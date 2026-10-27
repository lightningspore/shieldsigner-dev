//! Enabled single-color branches of complete AwbCalGainWpTypeLow.
use crate::{
    awb_gain::{self, Gains},
    awb_high_gain::{Light, LightResult},
    awb_low_gain, awb_single_color, awb_single_color_grid, InvalidInput,
};

#[derive(Clone, Debug, PartialEq)]
pub struct State<const CAP: usize> {
    pub low: awb_low_gain::State<CAP>,
    pub detection: awb_single_color_grid::Detection,
    pub single_weight: f32,
}
#[derive(Clone, Copy)]
pub struct Input<'a> {
    pub mode: i32,
    pub grid_valid: bool,
    pub grid: &'a [[f32; 3]; 225],
    pub classifier: &'a awb_single_color_grid::Calibration<'a>,
    pub confidence: &'a awb_single_color::Calibration,
    pub brightness_sample: f32,
    pub density: f32,
    pub acceptance_threshold: f32,
    pub estimated_gain: Gains,
    /// Native list at 0x3598; its first gain may become an extra candidate.
    pub high_history: &'a [Gains],
}
impl<const CAP: usize> State<CAP> {
    fn detect(&mut self, input: &Input<'_>, prior: Option<Gains>) -> Result<(), InvalidInput> {
        let mut state = awb_single_color_grid::State {
            history: self.low.color_history.clone(),
            result: self.detection.clone(),
        };
        state.process(input.grid, input.classifier, prior)?;
        self.single_weight = awb_single_color::confidence(
            input.confidence,
            input.brightness_sample,
            input.density,
            state.result.mean_distance,
            state.result.disagreements,
            state.result.gain,
            input.classifier.first,
            input.classifier.second,
        )?;
        self.low.color_history = state.history;
        self.detection = state.result;
        Ok(())
    }

    /// Single-color enable is true; the disabled profile uses the existing
    /// calculate_without_single_color API. All state/output commits are atomic.
    pub fn calculate(
        &mut self,
        lights: &[Light],
        output: &mut [LightResult],
        gain_history: &[Gains],
        settings: &awb_low_gain::Settings,
        input: &Input<'_>,
    ) -> Result<(), InvalidInput> {
        if output.len() > 255 {
            return Err(InvalidInput::Length);
        }
        let mut next = self.clone();
        let empty = LightResult {
            statistic: [0.; 4],
            spatial: [0.; 4],
            spatial_weight: 0.,
            extra_weight: 0.,
        };
        let mut staged = [empty; 255];
        let out = &mut staged[..output.len()];
        out.copy_from_slice(output);
        if settings.retained >= settings.count_threshold && input.mode != 2 {
            next.low
                .calculate_without_single_color(lights, out, gain_history, settings)?;
        } else {
            // Mode 2 bypasses the native sufficient-count early return.
            let effective = awb_low_gain::Settings {
                retained: 0,
                count_threshold: 1,
                ..*settings
            };
            if gain_history.is_empty() {
                next.low
                    .calculate_without_single_color(lights, out, gain_history, &effective)?;
                if settings.brightness > settings.low_brightness
                    && settings.brightness <= settings.high_brightness
                    && input.grid_valid
                {
                    if !input.acceptance_threshold.is_finite() {
                        return Err(InvalidInput::NonFinite);
                    }
                    next.detect(input, None)?;
                    if next.detection.valid && next.single_weight > input.acceptance_threshold {
                        next.low.current = next.detection.gain;
                        next.single_weight = 1.;
                        next.low.spatial_weight = self.low.spatial_weight;
                    } else {
                        next.single_weight = 0.;
                    }
                    next.low.low_result = next.low.current;
                }
            } else if !input.grid_valid || input.mode < 1 {
                next.low
                    .calculate_without_single_color(lights, out, gain_history, &effective)?;
            } else {
                if !input.acceptance_threshold.is_finite() {
                    return Err(InvalidInput::NonFinite);
                }
                next.detect(
                    input,
                    if input.mode == 2 {
                        None
                    } else {
                        input.high_history.first().copied()
                    },
                )?;
                if !next.detection.valid {
                    next.low.calculate_without_single_color(
                        lights,
                        out,
                        gain_history,
                        &effective,
                    )?;
                    next.single_weight = 0.;
                } else if input.mode == 1 && input.estimated_gain[0] as f64 > 0.00001 {
                    next.detection.gain = awb_gain::mixture(
                        next.detection.gain,
                        input.estimated_gain,
                        next.single_weight,
                    )?;
                    next.low.current = next.detection.gain;
                    next.low.low_result = next.low.current;
                } else if next.single_weight <= input.acceptance_threshold {
                    next.low.calculate_without_single_color(
                        lights,
                        out,
                        gain_history,
                        &effective,
                    )?;
                    next.single_weight = 0.;
                } else {
                    next.low.current = next.detection.gain;
                    next.low.low_result = next.low.current;
                    next.single_weight = 1.;
                }
            }
        }
        output.copy_from_slice(out);
        *self = next;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{
        awb_luma_history::History,
        awb_single_color::Line,
        awb_single_color_grid::{Candidate, Color, Detection},
    };
    #[test]
    fn confidence_failure_does_not_publish_classification_or_spatial_updates() {
        let mut state = State::<4> {
            low: awb_low_gain::State {
                current: [2.; 4],
                low_result: [3.; 4],
                temporal_result: [4.; 4],
                spatial_result: [5.; 4],
                temporal_source: [6.; 4],
                spatial_weight: 0.25,
                used_previous: false,
                color_history: History::from_values(&[]).unwrap(),
            },
            detection: Detection {
                selected: -1,
                color: -1,
                candidate_counts: [0; 14],
                color_counts: [0; 14],
                valid: false,
                disagreements: 0,
                votes: -1,
                mean_distance: 9999.,
                gain: [9.; 4],
            },
            single_weight: 0.75,
        };
        let before = state.clone();
        let light = Light {
            selected_gain: [0.; 4],
            selected_count: 0,
            extra_gain: [0.; 4],
            extra_count: 0,
            extra_enabled: false,
            low_threshold: 100,
            high_threshold: 200,
            low_gain: [2.; 4],
            high_gain: [3.; 4],
            spatial_percentage: 0,
            probability: 1.,
        };
        let settings = awb_low_gain::Settings {
            retained: 0,
            count_threshold: 100,
            brightness: 150,
            low_brightness: 100,
            high_brightness: 200,
            temporal_default: [1.; 4],
            color_history_value: 1,
            color_history_target: 0,
        };
        let candidates = [Candidate { red: 1., blue: 1. }];
        let colors = [Color {
            chroma: 0.,
            hue: 0.,
            cct_knots: [0., 1., 2.],
            distance_thresholds: [1000000.; 3],
        }];
        let line = Line {
            a: 0.,
            b: 0.,
            c: 0.,
            valid: false,
        };
        let classifier = awb_single_color_grid::Calibration {
            candidates: &candidates,
            colors: &colors,
            alpha: 0.5,
            history_target: 0,
            first: line,
            second: line,
        };
        let confidence = awb_single_color::Calibration {
            brightness_knots: core::array::from_fn(|i| i as f32),
            brightness_weights: [1.; 8],
            density_knots: core::array::from_fn(|i| i as f32),
            density_weights: [1.; 6],
            distance_knots: core::array::from_fn(|i| i as f32),
            cct_knots: [0., 1., 2.],
            distance_weights: [[1.; 6]; 3],
            disagreement_knots: core::array::from_fn(|i| i as f32),
            disagreement_weights: [1.; 6],
        };
        let input = Input {
            mode: 1,
            grid_valid: true,
            grid: &[[0.2; 3]; 225],
            classifier: &classifier,
            confidence: &confidence,
            brightness_sample: 1.,
            density: f32::NAN,
            acceptance_threshold: 0.5,
            estimated_gain: [0.; 4],
            high_history: &[],
        };
        let old = LightResult {
            statistic: [9.; 4],
            spatial: [8.; 4],
            spatial_weight: 0.5,
            extra_weight: 0.75,
        };
        let mut output = [old];
        assert_eq!(
            state.calculate(&[light], &mut output, &[], &settings, &input),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(state, before);
        assert_eq!(output, [old]);
    }
}

//! AwbCalGainByWbMode value composition: region -> probability -> high/low -> tail.
use crate::{
    awb_gain::{self, Gains},
    awb_gain_history::History,
    awb_high_gain, awb_low_gain, awb_low_single_color, awb_postprocess,
    awb_probability::{self, Probability},
    awb_single_color,
    awb_xy_selection::{self, Region},
    InvalidInput,
};
#[derive(Clone, Copy)]
pub struct Light<'a> {
    pub counts: [u32; 4],
    pub gains: [Gains; 4],
    pub probability: awb_probability::Light<'a>,
    pub calibration: awb_high_gain::Light,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct LightResult {
    pub probability: Probability,
    pub gain: awb_high_gain::LightResult,
}
pub struct Frame {
    pub complete: bool,
    pub fallback: Gains,
    pub exclusion_count: u32,
    pub exclusion_gain: Gains,
    pub divisors: [u32; 2],
}
#[derive(Clone, Copy)]
pub struct Settings<'a> {
    pub mode: i32,
    pub region: &'a awb_xy_selection::Settings,
    pub probability: awb_probability::Settings,
    pub high: &'a awb_high_gain::Settings,
    pub low: &'a awb_low_gain::Settings,
    pub single: Option<awb_low_single_color::Input<'a>>,
    pub post: &'a awb_postprocess::Settings<'a>,
    pub high_history_threshold: f32,
    pub estimated_density_threshold: f32,
    pub estimated_single_threshold: f32,
}
#[derive(Clone, Debug, PartialEq)]
pub struct State<const CAP: usize> {
    pub region: awb_xy_selection::State<CAP>,
    pub low: awb_low_single_color::State<CAP>,
    pub post: awb_postprocess::State<CAP>,
    pub high_history: History<CAP>,
    pub estimated_gain: Gains,
    pub high_gain: Gains,
    pub high_low_weight: f32,
    pub temporal_weight: f32,
    pub density: f32,
    pub selection_status: u8,
    pub strategy_flag: bool,
}
fn positive_product(gain: Gains) -> bool {
    ((((gain[0] * gain[1]) * gain[2]) * gain[3]) as f64) > 0.00001
}
impl<const CAP: usize> State<CAP> {
    pub fn process(
        &mut self,
        frame: &Frame,
        lights: &[Light<'_>],
        output: &mut [LightResult],
        settings: &Settings<'_>,
    ) -> Result<(), InvalidInput> {
        self.process_inner(frame, lights, output, settings, false)
    }

    /// Consume the three bounded measurement blocks in prepared native records.
    /// Calibration/prior fields come from `lights`; its explicit count/gain
    /// arrays are ignored. Exclusion in INITIAL mode uses `frame`'s aggregate.
    /// AUTO/ALWAYS Exclusion is rejected atomically: native reads past records.
    pub fn process_prepared(
        &mut self,
        frame: &Frame,
        records: &[crate::awb_preparation::LightRecord],
        lights: &[Light<'_>],
        output: &mut [LightResult],
        settings: &Settings<'_>,
    ) -> Result<(), InvalidInput> {
        let n = lights.len();
        if n < 4 || n > 255 || records.len() != n || output.len() != n {
            return Err(InvalidInput::Length);
        }
        let mut adapted = [lights[0]; 255];
        for i in 0..n {
            adapted[i] = lights[i];
            adapted[i].counts = [0; 4];
            adapted[i].gains = [[0.; 4]; 4];
            for region in 0..3 {
                adapted[i].counts[region] = records[i].count(region).unwrap();
                adapted[i].gains[region] = records[i].gain(region).unwrap();
            }
        }
        self.process_inner(frame, &adapted[..n], output, settings, true)
    }

    fn process_inner(
        &mut self,
        frame: &Frame,
        lights: &[Light<'_>],
        output: &mut [LightResult],
        settings: &Settings<'_>,
        prepared: bool,
    ) -> Result<(), InvalidInput> {
        let n = lights.len();
        if n < 4 || n > 255 || output.len() != n {
            return Err(InvalidInput::Length);
        }
        let mut next = self.clone();
        let zero = Probability {
            total: 0.,
            distance: 0.,
            luma: 0.,
            prior: 0.,
            white_points: 0.,
        };
        let empty = awb_high_gain::LightResult {
            statistic: [0.; 4],
            spatial: [0.; 4],
            spatial_weight: 0.,
            extra_weight: 0.,
        };
        let mut probabilities = [zero; 255];
        let mut gains = [empty; 255];
        for i in 0..n {
            probabilities[i] = output[i].probability;
            gains[i] = output[i].gain;
        }
        let mut candidate = next.post.current;
        if !frame.complete {
            if positive_product(frame.fallback) {
                candidate = frame.fallback;
            }
            candidate = awb_gain::normalize(candidate)?;
            next.density = 100000.;
        } else {
            next.selection_status = 0;
            if frame.divisors.contains(&0) {
                return Err(InvalidInput::DegenerateRange);
            }
            let normal: [u32; 255] =
                core::array::from_fn(|i| if i < n { lights[i].counts[0] } else { 0 });
            let big: [u32; 255] =
                core::array::from_fn(|i| if i < n { lights[i].counts[1] } else { 0 });
            let prior_kind = next.region.kind;
            next.region.select(
                &normal[..n],
                &big[..n],
                frame.exclusion_count,
                &mut probabilities[..n],
                settings.region,
            )?;
            if prepared && next.region.selected == Region::Exclusion && settings.mode >= 1 {
                return Err(InvalidInput::UnsupportedRegion);
            }
            next.density = ((next.region.retained as f32 / frame.divisors[0] as f32)
                / frame.divisors[1] as f32)
                * 100000.;
            if next.region.selected == Region::Exclusion && settings.mode < 1 {
                next.region.kind = prior_kind;
                if positive_product(frame.exclusion_gain) {
                    candidate = frame.exclusion_gain;
                }
            } else {
                next.strategy_flag = false;
                let reference_zero = awb_probability::Light {
                    reference_gain: [1.; 4],
                    statistic_gain: [0.; 4],
                    kind: 0,
                    white_points: 0,
                    prior: awb_probability::Curve {
                        knots: &[],
                        weights: &[],
                    },
                };
                let mut references = [reference_zero; 255];
                for i in 0..n {
                    references[i] = lights[i].probability;
                    gains[i].spatial_weight = 1.;
                }
                awb_probability::total_probabilities(
                    &references[..n],
                    &mut probabilities[..n],
                    awb_probability::Settings {
                        gain: candidate,
                        ..settings.probability
                    },
                )?;
                let high_zero = awb_high_gain::Light {
                    selected_gain: [0.; 4],
                    selected_count: 0,
                    extra_gain: [0.; 4],
                    extra_count: 0,
                    extra_enabled: false,
                    low_threshold: 0,
                    high_threshold: 0,
                    low_gain: [0.; 4],
                    high_gain: [0.; 4],
                    spatial_percentage: 0,
                    probability: 0.,
                };
                let mut high_lights = [high_zero; 255];
                let region = next.region.selected as usize;
                for i in 0..n {
                    let mut l = lights[i].calibration;
                    l.selected_gain = lights[i].gains[region];
                    l.selected_count = lights[i].counts[region];
                    l.extra_gain = lights[i].gains[2];
                    l.extra_count = lights[i].counts[2];
                    l.probability = probabilities[i].total;
                    high_lights[i] = l;
                }
                let high_settings = awb_high_gain::Settings {
                    fast: settings.probability.fast,
                    brightness: settings.probability.brightness,
                    ..*settings.high
                };
                let high =
                    awb_high_gain::calculate(&high_lights[..n], &mut gains[..n], &high_settings)?;
                next.high_gain = high.gain;
                next.temporal_weight = high.temporal_weight;
                next.low.low.current = high.gain;
                next.low.low.temporal_source = high.temporal;
                let low_settings = awb_low_gain::Settings {
                    retained: next.region.retained,
                    count_threshold: settings.region.count_thresholds[0],
                    brightness: settings.probability.brightness,
                    temporal_default: settings.high.temporal_default,
                    ..*settings.low
                };
                if let Some(single) = settings.single {
                    let input = awb_low_single_color::Input {
                        mode: settings.mode,
                        density: next.density,
                        estimated_gain: next.estimated_gain,
                        high_history: next.high_history.values(),
                        ..single
                    };
                    let low_settings = awb_low_gain::Settings {
                        color_history_value: single.classifier.candidates.len() as i32,
                        color_history_target: single.classifier.history_target,
                        ..low_settings
                    };
                    next.low.calculate(
                        &high_lights[..n],
                        &mut gains[..n],
                        next.post.raw_history.values(),
                        &low_settings,
                        &input,
                    )?;
                } else {
                    next.low.low.calculate_without_single_color(
                        &high_lights[..n],
                        &mut gains[..n],
                        next.post.raw_history.values(),
                        &low_settings,
                    )?;
                }
                next.high_low_weight = if settings.mode == 2 {
                    0.
                } else {
                    awb_single_color::curve(
                        &[
                            settings.region.count_thresholds[1] as f32,
                            settings.region.count_thresholds[0] as f32,
                        ],
                        &[0., 1.],
                        next.region.retained as f32,
                    )?
                };
                candidate = core::array::from_fn(|i| {
                    libm::fmaf(
                        high.gain[i],
                        next.high_low_weight,
                        (1. - next.high_low_weight) * next.low.low.current[i],
                    )
                });
                if settings.high_history_threshold < next.density {
                    next.high_history.update(high.gain, 1)?;
                }
                if settings.mode == 1 {
                    if next.density > settings.estimated_density_threshold {
                        next.estimated_gain = high.gain;
                    } else if next.low.single_weight > settings.estimated_single_threshold {
                        next.estimated_gain = candidate;
                    }
                }
            }
        }
        let metadata: [awb_postprocess::Light; 255] =
            core::array::from_fn(|i| awb_postprocess::Light {
                gain: gains[i].statistic,
                probability: probabilities[i].total,
            });
        next.post.finish(candidate, &metadata[..n], settings.post)?;
        next.low.low.current = next.post.current;
        for i in 0..n {
            output[i] = LightResult {
                probability: probabilities[i],
                gain: gains[i],
            };
        }
        *self = next;
        Ok(())
    }
}

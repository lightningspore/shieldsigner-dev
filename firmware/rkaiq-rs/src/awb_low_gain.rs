//! AwbCalGainWpTypeLow (ELF 0xc6a90), with single-color processing disabled.
//! The enabled single-color path remains required for the pinned SC3336 IQ.
use crate::{
    awb_gain::{self, Gains},
    awb_high_gain::{Light, LightResult},
    awb_luma_history::History,
    awb_probability, InvalidInput,
};

#[derive(Clone, Debug, PartialEq)]
pub struct State<const CAP: usize> {
    pub current: Gains,
    pub low_result: Gains,
    pub temporal_result: Gains,
    pub spatial_result: Gains,
    pub temporal_source: Gains,
    pub spatial_weight: f32,
    pub used_previous: bool,
    pub color_history: History<CAP>,
}

pub struct Settings {
    pub retained: u32,
    pub count_threshold: u32,
    pub brightness: u32,
    pub low_brightness: u32,
    pub high_brightness: u32,
    pub temporal_default: Gains,
    pub color_history_value: i32,
    pub color_history_target: u16,
}

impl<const CAP: usize> State<CAP> {
    /// Single-color-disabled branch only. Gain history is in native list order;
    /// fallback uses the last element. A sufficient count only updates color
    /// history and leaves gain fields/per-light outputs untouched.
    pub fn calculate_without_single_color(
        &mut self,
        lights: &[Light],
        output: &mut [LightResult],
        gain_history: &[Gains],
        settings: &Settings,
    ) -> Result<(), InvalidInput> {
        let mut next = self.clone();
        if settings.retained >= settings.count_threshold {
            next.color_history.update(
                settings.color_history_value,
                settings.color_history_target as i32,
            )?;
            *self = next;
            return Ok(());
        }
        if let Some(&previous) = gain_history.last() {
            if previous.iter().any(|v| !v.is_finite()) {
                return Err(InvalidInput::NonFinite);
            }
            next.current = previous;
            next.temporal_result = previous;
            next.used_previous = true;
        } else if settings.brightness <= settings.low_brightness {
            next.temporal_source = awb_gain::temporal_history(&[], &[], settings.temporal_default)?;
            next.current = next.temporal_source;
            next.temporal_result = next.current;
        } else {
            let n = lights.len();
            if n == 0 || n > 255 || output.len() != n {
                return Err(InvalidInput::Length);
            }
            let empty = LightResult {
                statistic: [0.; 4],
                spatial: [0.; 4],
                spatial_weight: 0.,
                extra_weight: 0.,
            };
            let mut staged = [empty; 255];
            staged[..n].copy_from_slice(output);
            let weight = if settings.brightness > settings.high_brightness {
                1.
            } else if settings.brightness as f32 <= settings.low_brightness as f32 {
                // Native interpolation clamps before checking span: distinct
                // u32 endpoints may collapse to the same f32 value.
                0.
            } else if settings.brightness as f32 >= settings.high_brightness as f32 {
                1.
            } else {
                crate::interpolate(
                    &[
                        settings.low_brightness as f32,
                        settings.high_brightness as f32,
                    ],
                    &[0., 1.],
                    settings.brightness as f32,
                )?
            };
            if settings.brightness <= settings.high_brightness {
                next.temporal_source =
                    awb_gain::temporal_history(&[], &[], settings.temporal_default)?;
                next.temporal_result = next.temporal_source;
            }
            for (light, result) in lights.iter().zip(&mut staged[..n]) {
                result.spatial = awb_gain::spatial(
                    settings.brightness,
                    light.low_threshold,
                    light.high_threshold,
                    light.low_gain,
                    light.high_gain,
                )?;
                result.statistic = result.spatial;
            }
            next.spatial_result = awb_probability::weighted_gain_values(
                lights
                    .iter()
                    .zip(&staged[..n])
                    .map(|(l, r)| (r.statistic, l.probability)),
            )?;
            next.current = if settings.brightness > settings.high_brightness {
                next.spatial_result
            } else {
                core::array::from_fn(|i| {
                    libm::fmaf(
                        next.spatial_result[i],
                        weight,
                        (1. - weight) * next.temporal_result[i],
                    )
                })
            };
            if next.current.iter().any(|v| !v.is_finite()) {
                return Err(InvalidInput::NonFinite);
            }
            next.spatial_weight = weight;
            next.low_result = next.current;
            output.copy_from_slice(&staged[..n]);
            *self = next;
            return Ok(());
        }
        next.low_result = next.current;
        *self = next;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn corrupting_singleton_update_is_rejected_without_changing_gain_state() {
        let mut state = State::<4> {
            current: [2.; 4],
            low_result: [3.; 4],
            temporal_result: [4.; 4],
            spatial_result: [5.; 4],
            temporal_source: [6.; 4],
            spatial_weight: 0.25,
            used_previous: false,
            color_history: History::from_values(&[42]).unwrap(),
        };
        let before = state.clone();
        let settings = Settings {
            retained: 100,
            count_threshold: 100,
            brightness: 0,
            low_brightness: 0,
            high_brightness: 0,
            temporal_default: [f32::NAN; 4],
            color_history_value: 43,
            color_history_target: 1,
        };
        assert_eq!(
            state.calculate_without_single_color(&[], &mut [], &[], &settings),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
        let settings = Settings {
            color_history_target: 0,
            ..settings
        };
        assert_eq!(
            state.calculate_without_single_color(&[], &mut [], &[], &settings),
            Ok(())
        );
        assert_eq!(state, before);
    }
}

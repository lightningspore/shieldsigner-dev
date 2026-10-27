//! Common AwbCalGainByWbMode tail after strategy gain selection.
use crate::{
    awb_gain::{self, Gains},
    awb_gain_adjust, awb_gain_clip,
    awb_gain_history::{self, History},
    awb_single_color::{self, ColorTemperature, Line},
    InvalidInput,
};

pub struct Light {
    pub gain: Gains,
    pub probability: f32,
}
#[derive(Clone, Copy)]
pub struct Adjustment<'a> {
    pub luts: &'a [awb_gain_adjust::Lut],
    pub settings: &'a awb_gain_adjust::Settings,
}
#[derive(Clone, Copy)]
pub struct Settings<'a> {
    pub history_target: i32,
    pub tolerance: f32,
    pub history_convergence: f32,
    pub damped_convergence: f32,
    pub damping_threshold: f32,
    pub brightness: u32,
    pub clipping: Option<&'a awb_gain_clip::Calibration<'a>>,
    pub adjustment: Option<Adjustment<'a>>,
    pub offsets: Option<Gains>,
    pub first: Line,
    pub second: Line,
}
#[derive(Clone, Debug, PartialEq)]
pub struct State<const CAP: usize> {
    pub raw_history: History<CAP>,
    pub output_history: History<CAP>,
    /// Caller advances this only after remaining outer AWB work.
    pub previous: Gains,
    pub coefficient: f32,
    pub effective_coefficient: f32,
    pub current: Gains,
    pub raw: Gains,
    pub clipped_gain: Gains,
    pub adjust_before: Gains,
    pub adjust_after: Gains,
    pub offset_gain: Gains,
    pub damped: Gains,
    pub adjust_coordinates_before: [f32; 2],
    pub adjust_coordinates_after: [f32; 2],
    pub clipped: bool,
    pub history_updated: bool,
    pub converged: bool,
    pub damping_stable: bool,
    pub temperature: ColorTemperature,
    pub top: [ColorTemperature; 4],
}
impl<const CAP: usize> State<CAP> {
    /// Atomic value-level common tail. Native always emits four ranked light
    /// records, so fewer than four lights is rejected before unsafe indexing.
    pub fn finish(
        &mut self,
        candidate: Gains,
        lights: &[Light],
        settings: &Settings<'_>,
    ) -> Result<(), InvalidInput> {
        if lights.len() < 4 || lights.len() > 255 {
            return Err(InvalidInput::Length);
        }
        if [
            settings.history_convergence,
            settings.damped_convergence,
            settings.damping_threshold,
        ]
        .iter()
        .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        let mut next = self.clone();
        next.raw = candidate;
        (next.current, next.history_updated) =
            next.raw_history
                .select(candidate, settings.history_target, settings.tolerance)?;
        next.converged = awb_gain_history::converged(
            next.raw_history.values(),
            None,
            settings.history_convergence + settings.history_convergence,
        )?;
        if let Some(cal) = settings.clipping {
            let output = awb_gain_clip::clip(next.current, next.clipped, settings.brightness, cal)?;
            next.current = output.gain;
            next.clipped = output.clipped;
            next.clipped_gain = next.current;
        }
        if let Some(adjust) = &settings.adjustment {
            next.adjust_before = next.current;
            let mut state = awb_gain_adjust::State {
                gain: next.current,
                before: next.adjust_coordinates_before,
                after: next.adjust_coordinates_after,
            };
            state.adjust(adjust.luts, adjust.settings)?;
            next.current = state.gain;
            next.adjust_coordinates_before = state.before;
            next.adjust_coordinates_after = state.after;
            next.adjust_after = next.current;
        }
        if let Some(offsets) = settings.offsets {
            next.current = awb_gain::offset(next.current, offsets)?;
            next.offset_gain = next.current;
        }
        let before = next.current;
        let damped = awb_gain::damp(next.previous, before, next.coefficient)?;
        next.current = damped.gain;
        next.damped = damped.gain;
        next.coefficient = damped.base_coefficient;
        next.effective_coefficient = damped.effective_coefficient;
        next.damping_stable = true;
        for i in 0..4 {
            let delta = libm::fabsf(next.current[i] - before[i]);
            if settings.damped_convergence <= delta {
                next.converged = false;
            }
            if settings.damping_threshold <= delta {
                next.damping_stable = false;
            }
        }
        next.output_history
            .update(next.current, settings.history_target)?;
        next.temperature =
            awb_single_color::color_temperature(next.current, settings.first, settings.second)?;
        let mut order: [usize; 255] = core::array::from_fn(|i| i);
        if lights.iter().any(|v| !v.probability.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        for end in (1..lights.len()).rev() {
            for i in 0..end {
                if lights[order[i]].probability < lights[order[i + 1]].probability {
                    order.swap(i, i + 1);
                }
            }
        }
        for i in 0..4 {
            next.top[i] = awb_single_color::color_temperature(
                lights[order[i]].gain,
                settings.first,
                settings.second,
            )?;
        }
        *self = next;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn late_metadata_failure_preserves_both_histories_and_gain_state() {
        let zero = ColorTemperature {
            valid: false,
            cct: 0.,
            ccri: 0.,
        };
        let mut state = State::<4> {
            raw_history: History::from_values(&[[1.; 4]]).unwrap(),
            output_history: History::from_values(&[]).unwrap(),
            previous: [1.; 4],
            coefficient: 0.9,
            effective_coefficient: 0.,
            current: [1.; 4],
            raw: [0.; 4],
            clipped_gain: [0.; 4],
            adjust_before: [0.; 4],
            adjust_after: [0.; 4],
            offset_gain: [0.; 4],
            damped: [0.; 4],
            adjust_coordinates_before: [0.; 2],
            adjust_coordinates_after: [0.; 2],
            clipped: false,
            history_updated: false,
            converged: false,
            damping_stable: false,
            temperature: zero,
            top: [zero; 4],
        };
        let before = state.clone();
        let lights: [Light; 4] = core::array::from_fn(|i| Light {
            gain: [1.; 4],
            probability: if i == 3 { f32::NAN } else { 1. },
        });
        let line = Line {
            a: 0.,
            b: 0.,
            c: 0.,
            valid: false,
        };
        let settings = Settings {
            history_target: 2,
            tolerance: 0.1,
            history_convergence: 0.1,
            damped_convergence: 0.1,
            damping_threshold: 0.1,
            brightness: 0,
            clipping: None,
            adjustment: None,
            offsets: None,
            first: line,
            second: line,
        };
        assert_eq!(
            state.finish([2.; 4], &lights, &settings),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(state, before);
    }
}

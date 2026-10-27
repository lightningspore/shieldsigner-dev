//! Numerical prefix of standard AwbPreProcV32 (ELF 0xc4698).
//! Returns the continuation decision before metadata/history/classification.
use crate::{interpolate, InvalidInput};
#[derive(Clone, Copy)]
pub struct Curve<'a> {
    pub knots: &'a [f32],
    pub values: &'a [f32],
}
impl Curve<'_> {
    fn at(&self, x: f32) -> Result<f32, InvalidInput> {
        interpolate(self.knots, self.values, x)
    }
}
pub struct Calibration<'a> {
    pub smart_knots: &'a [f32],
    pub smart: [&'a [f32]; 3],
    pub interval: Curve<'a>,
    pub point_knots: &'a [f32],
    pub points: [&'a [f32]; 2],
    pub region_knots: &'a [f32],
    pub regions: [&'a [f32]; 2],
}
pub struct Input {
    pub requested_mode: i32,
    pub previous_update: bool,
    pub smart_enabled: bool,
    pub countdown: i32,
    pub exposure_luma: Option<[f32; 2]>,
    pub frame_choice: u8,
    pub working_mode: i32,
    pub fallback: u32,
    pub override_enabled: bool,
    pub override_valid: bool,
    pub override_luma: f32,
    pub geometry: [u16; 2],
    pub block: [u8; 2],
    pub sample_scale: i32,
}
#[derive(Clone, Debug, PartialEq)]
pub struct State {
    pub mode: i32,
    pub update: bool,
    pub luma_integer: u32,
    pub luma: f32,
    pub smart: [f32; 3],
    pub interval: u32,
    pub points: [u32; 2],
    pub regions: [f32; 2],
    pub frame_counter: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Continuation {
    ModeBypass,
    IntervalSkip,
    Ready,
}
fn rounded(value: f32) -> u32 {
    ((value as f64) + 0.5) as u32
}
impl State {
    /// Validate into a copy so checked-input errors leave persistent state alone.
    /// Mode 1 bypasses numerics without reading calibration/exposure inputs.
    pub fn derive(
        &mut self,
        input: &Input,
        calibration: &Calibration<'_>,
    ) -> Result<Continuation, InvalidInput> {
        let mut next = self.clone();
        next.mode = input.requested_mode;
        next.update = input.previous_update;
        if next.mode == 1 {
            next.update = false;
            *self = next;
            return Ok(Continuation::ModeBypass);
        }
        next.update |= !input.smart_enabled || input.countdown > 0;
        if let Some(source) = input.exposure_luma {
            let index = if input.frame_choice < 2 {
                input.frame_choice as usize
            } else {
                usize::from(input.working_mode != 0)
            };
            if !source[index].is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            next.luma = source[index] * 1000.;
            if !next.luma.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            next.luma_integer = rounded(next.luma);
        } else {
            next.luma_integer = input.fallback;
            next.luma = input.fallback as f32;
        }
        if input.override_enabled && input.override_valid {
            if !input.override_luma.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            next.luma = input.override_luma;
            next.luma_integer = rounded(next.luma);
        }
        for i in 0..3 {
            next.smart[i] = interpolate(calibration.smart_knots, calibration.smart[i], next.luma)?;
        }
        next.interval = rounded(calibration.interval.at(next.luma_integer as f32)?);
        if next.interval == u32::MAX || input.block.contains(&0) {
            return Err(InvalidInput::Length);
        }
        let area = (((input.sample_scale as f32) * (input.geometry[0] as f32))
            / (input.block[0] as f32))
            * (input.geometry[1] as f32)
            / (input.block[1] as f32);
        for i in 0..2 {
            let point = interpolate(calibration.point_knots, calibration.points[i], next.luma)?;
            next.points[i] = rounded((area * point) / 100000.);
            let region = interpolate(calibration.region_knots, calibration.regions[i], next.luma)?;
            next.regions[i] = (area * region) / 100000.;
        }
        let decision = if next.frame_counter <= next.interval
            || next.frame_counter % (next.interval + 1) == 0
        {
            Continuation::Ready
        } else {
            next.frame_counter = next.frame_counter.wrapping_add(1);
            Continuation::IntervalSkip
        };
        *self = next;
        Ok(decision)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn mode_bypass_does_not_read_invalid_exposure_and_checked_failure_is_atomic() {
        let calibration = Calibration {
            smart_knots: &[0.],
            smart: [&[1.]; 3],
            interval: Curve {
                knots: &[0.],
                values: &[0.],
            },
            point_knots: &[0.],
            points: [&[1.]; 2],
            region_knots: &[0.],
            regions: [&[1.]; 2],
        };
        let mut input = Input {
            requested_mode: 1,
            previous_update: true,
            smart_enabled: false,
            countdown: 2,
            exposure_luma: Some([f32::NAN; 2]),
            frame_choice: 0,
            working_mode: 0,
            fallback: 0,
            override_enabled: false,
            override_valid: false,
            override_luma: f32::NAN,
            geometry: [2304, 1296],
            block: [0, 0],
            sample_scale: 1,
        };
        let mut state = State {
            mode: 7,
            update: true,
            luma_integer: 123,
            luma: 2.,
            smart: [3., 4., 5.],
            interval: 6,
            points: [7, 8],
            regions: [9., 10.],
            frame_counter: 17,
        };
        assert_eq!(
            state.derive(&input, &calibration),
            Ok(Continuation::ModeBypass)
        );
        assert_eq!(state.luma, 2.);
        assert!(!state.update);
        let before = state.clone();
        input.requested_mode = 0;
        input.exposure_luma = Some([1.; 2]);
        assert_eq!(
            state.derive(&input, &calibration),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
        input.block = [15, 15];
        let mut metadata = Metadata {
            history: crate::awb_luma_history::History::<4>::from_values(&[42]).unwrap(),
            level: 9,
            environment: -7,
            variance: 0.5,
            brightness_stable: true,
        };
        let environment = crate::awb_environment::Calibration {
            boundaries: &[0, 1000],
            thresholds: [110, 200, 65536, 65600],
        };
        assert_eq!(
            state.derive_measurements(
                &input,
                &calibration,
                &mut metadata,
                &environment,
                [true, true],
                1
            ),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
        assert_eq!(metadata.history.values(), &[42]);
        assert_eq!(metadata.environment, -7);
        assert_eq!(metadata.variance, 0.5);
    }
}

#[derive(Clone, Debug)]
pub struct Metadata<const CAP: usize> {
    pub history: crate::awb_luma_history::History<CAP>,
    pub level: u32,
    pub environment: i32,
    pub variance: f32,
    pub brightness_stable: bool,
}
impl State {
    /// Join numerical preprocessing to the environment/history update that
    /// precedes PrepareMeasureResult. Measurement classification remains external.
    pub fn derive_measurements<const CAP: usize>(
        &mut self,
        input: &Input,
        calibration: &Calibration<'_>,
        metadata: &mut Metadata<CAP>,
        environment: &crate::awb_environment::Calibration<'_>,
        convergence: [bool; 2],
        history_target: i32,
    ) -> Result<Continuation, InvalidInput> {
        let mut next = self.clone();
        let mut meta = metadata.clone();
        let decision = next.derive(input, calibration)?;
        if decision == Continuation::Ready {
            let classified =
                crate::awb_environment::classify(next.luma_integer, environment, meta.environment);
            meta.level = classified.level;
            meta.environment = classified.environment;
            meta.history
                .update(next.luma_integer as i32, history_target)?;
            meta.variance = meta.history.variance();
            // Native computes !(variance > threshold): unordered NaN is
            // therefore reported stable, unlike a Rust <= comparison.
            meta.brightness_stable =
                meta.variance.partial_cmp(&next.smart[0]) != Some(core::cmp::Ordering::Greater);
            next.update |= next.smart[0] < meta.variance || !(convergence[0] && convergence[1]);
        }
        *self = next;
        *metadata = meta;
        Ok(decision)
    }
}

impl State {
    /// Join the outer prefix through complete native-style measurement
    /// preparation. Gain selection and hardware reconfiguration follow later.
    /// Preparation may partially mutate borrowed buffers on arithmetic failure;
    /// discard the session after such an error, as with the underlying API.
    pub fn prepare_frame<const CAP: usize>(
        &mut self,
        input: &Input,
        calibration: &Calibration<'_>,
        metadata: &mut Metadata<CAP>,
        environment: &crate::awb_environment::Calibration<'_>,
        convergence: [bool; 2],
        history_target: i32,
        measurements: &mut crate::awb_preparation::State<'_>,
        frame: &crate::awb_preparation::Frame<'_>,
        settings: &crate::awb_preparation::Settings<'_>,
    ) -> Result<Continuation, InvalidInput> {
        let decision = self.derive_measurements(
            input,
            calibration,
            metadata,
            environment,
            convergence,
            history_target,
        )?;
        measurements.update = self.update;
        if decision == Continuation::Ready {
            let effective = crate::awb_preparation::Settings {
                groups: settings.groups,
                fast_light_count: settings.fast_light_count,
                stability_threshold: self.smart[2],
                exclusion_kind: settings.exclusion_kind,
                exclusion_weight: settings.exclusion_weight,
                prior_sample: self.luma,
            };
            crate::awb_preparation::prepare(measurements, frame, &effective)?;
            self.update = measurements.update;
        }
        Ok(decision)
    }
}

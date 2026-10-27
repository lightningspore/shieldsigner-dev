//! Standard linear error-history writes in AecPreProcess (ELF 0xb33d0).
use crate::InvalidInput;
pub fn record_error(
    history: &mut [f32; 10],
    frame: u32,
    run: bool,
    measured: f32,
    target: f32,
) -> Result<f32, InvalidInput> {
    if frame > i32::MAX as u32 - 9 {
        return Err(InvalidInput::Length);
    }
    if history.iter().any(|v| !v.is_finite())
        || (run && (!measured.is_finite() || !target.is_finite()))
    {
        return Err(InvalidInput::NonFinite);
    }
    if run && (measured < 0. || target <= 0.) {
        return Err(InvalidInput::Exposure);
    }
    let error = if run {
        (measured - target) / target
    } else {
        history[((frame + 9) % 10) as usize]
    };
    if !error.is_finite() {
        return Err(InvalidInput::Exposure);
    }
    history[(frame % 10) as usize] = error;
    Ok(error)
}

/// Side effects surrounding the standard linear target/history branch.
/// Exposure association and optional raw/luma/lux/flicker algorithms are external.
#[derive(Clone, Copy, Debug)]
pub struct Standard {
    pub frame: i32,
    pub exposure: crate::ae_publication::Record,
    pub measured: f32,
    pub auxiliary_mean: f32,
    pub normalized_brightness: f32,
    pub near_maximum: bool,
    pub near_minimum: bool,
    pub environment_level: f32,
    pub alternate_damping: bool,
}
impl Default for Standard {
    fn default() -> Self {
        Self {
            frame: -1,
            exposure: [0; 244],
            measured: 0.,
            auxiliary_mean: 0.,
            normalized_brightness: 0.,
            near_maximum: false,
            near_minimum: false,
            environment_level: 0.,
            alternate_damping: false,
        }
    }
}
impl Standard {
    pub fn update(
        &mut self,
        frame: i32,
        exposure: crate::ae_publication::Record,
        q8: [u16; 4],
        run: bool,
        bounds: [f32; 2],
        normalization_floor: f32,
    ) -> Result<f32, InvalidInput> {
        let f = |o| f32::from_le_bytes(exposure[o..o + 4].try_into().unwrap());
        let (time, gain, isp) = (f(0), f(4), f(12));
        if [time, gain, isp, bounds[0], bounds[1], normalization_floor]
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if time <= 0.
            || gain <= 0.
            || isp <= 0.
            || bounds[0] <= 0.
            || bounds[1] < bounds[0]
            || normalization_floor <= 0.
        {
            return Err(InvalidInput::Exposure);
        }
        let aggregate = (gain * time) * isp;
        if !aggregate.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        self.frame = frame;
        self.exposure = exposure;
        if run {
            self.measured = f32::from(q8[0]) / 256.;
            self.auxiliary_mean = f32::from(q8[3]) / 256.;
            self.normalized_brightness =
                self.measured / (aggregate * 1000.).max(normalization_floor);
            let near = |bound: f32| f64::from((bound - aggregate).abs() / bound) <= 0.05;
            self.near_minimum = near(bounds[0]);
            self.near_maximum = near(bounds[1]);
        }
        // AecGetEnvLgt runs in the processing caller even when control is skipped.
        // Preserve its distinct multiply order and float 5% threshold.
        let level = self.measured / (((gain * isp) * time) * 1000.);
        self.alternate_damping =
            (self.environment_level - level).abs() > self.environment_level * 0.05;
        self.environment_level = level;
        Ok(aggregate)
    }
}

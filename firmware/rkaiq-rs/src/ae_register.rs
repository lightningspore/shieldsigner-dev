//! Ordinary linear __AecRegConvertion (ELF 0xae8b0), SC3336 gain model.
use crate::{
    exposure::{self, Calibration, Codes, GainModel, Mode},
    InvalidInput,
};
#[derive(Clone, Copy, Debug)]
pub struct Policy {
    pub isp_range: [f32; 2],
    pub time_range: [f32; 2],
    pub gain_range: [f32; 2],
    pub analogue_minimum: f32,
    pub time_quantum: f32,
    pub flicker_enabled: bool,
    pub automatic: bool,
    /// Native context +0x23c0 bit 0x1000.
    pub suppress_isp_compensation: bool,
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub codes: Codes,
    pub seconds: f32,
    pub gain: f32,
    pub isp_gain: f32,
    pub mappings: u32,
}
pub fn linear(
    mut seconds: f32,
    mut gain: f32,
    isp: f32,
    dcg: i32,
    calibration: Calibration<'_>,
    policy: Policy,
) -> Result<Output, InvalidInput> {
    let p = policy;
    if [seconds, gain, isp, p.analogue_minimum, p.time_quantum]
        .iter()
        .chain(p.isp_range.iter())
        .chain(p.time_range.iter())
        .chain(p.gain_range.iter())
        .any(|x| !x.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if seconds <= 0.
        || gain <= 0.
        || isp <= 0.
        || p.analogue_minimum <= 0.
        || [p.isp_range, p.time_range, p.gain_range]
            .iter()
            .any(|r| r[0] <= 0. || r[1] < r[0])
    {
        return Err(InvalidInput::Exposure);
    }
    // This port qualifies the SC3336 ordinary linear band; do not silently
    // substitute the separately recovered camera-HAL conversion for other models.
    match calibration.gain {
        GainModel::Bands(b) if b.len() == 1 && b[0].exponent == 1. && b[0].scale > 0. => (),
        _ => return Err(InvalidInput::GainRange),
    }
    let mut codes = exposure::convert(seconds, gain, Mode::Linear, dcg, calibration)?;
    let mut mappings = 0;
    let mut gain_retries = 0;
    let mut time_retries = 0;
    let quantize = |x: f32, round: bool| {
        let scaled = x * 256.;
        let value = if round {
            libm::roundf(scaled)
        } else {
            libm::floorf(scaled)
        };
        (value * (1. / 256.))
            .max(p.isp_range[0])
            .min(p.isp_range[1])
    };
    loop {
        // Explicit resource bound for malformed/extreme inputs. Native ordinary
        // SC3336 paths terminate by code decrements or ten-retry limits.
        if mappings >= 1_000_000 {
            return Err(InvalidInput::Exposure);
        }
        let actual = exposure::decode_linear(codes, dcg, calibration)?;
        mappings += 1;
        let output = |isp| Output {
            codes,
            seconds: actual.seconds,
            gain: actual.gain,
            isp_gain: isp,
            mappings,
        };
        let gain_error = f64::from((gain - actual.gain).abs() / gain);
        let time_error = f64::from((seconds - actual.seconds).abs() / seconds);
        if !p.suppress_isp_compensation && p.isp_range[1] != 1. {
            if gain_error > 0.03 {
                let compensation = (gain * isp) / actual.gain;
                if compensation >= p.isp_range[0] {
                    return Ok(output(quantize(compensation, true)));
                }
                if gain <= p.analogue_minimum {
                    return Ok(output(isp));
                }
                codes.gain = codes.gain.checked_sub(1).ok_or(InvalidInput::GainRange)?;
                continue;
            }
            if time_error <= 0.03 {
                return Ok(output(quantize(isp, false)));
            }
            let compensation = (seconds * isp) / actual.seconds;
            if compensation >= p.isp_range[0] {
                return Ok(output(quantize(compensation, true)));
            }
        } else {
            if p.isp_range[1] != 1. || !p.automatic {
                return Ok(output(isp));
            }
            if gain_error > 0.05 && (actual.seconds < p.time_quantum || !p.flicker_enabled) {
                gain_retries += 1;
                if gain_retries > 10 {
                    return Ok(output(isp));
                }
                seconds = (seconds * (gain / actual.gain))
                    .max(p.time_range[0])
                    .min(p.time_range[1]);
                gain = actual.gain;
                // Native jumps directly to time-code conversion, preserving gain code.
                codes.integration_time =
                    exposure::convert(seconds, gain, Mode::Linear, dcg, calibration)?
                        .integration_time;
                continue;
            }
            if time_error <= 0.03 {
                return Ok(output(isp));
            }
            time_retries += 1;
            if time_retries > 10 {
                return Ok(output(isp));
            }
            let compensation = (seconds / actual.seconds) * gain;
            if compensation >= p.gain_range[0] {
                gain = compensation.min(p.gain_range[1]);
                seconds = actual.seconds;
                codes = exposure::convert(seconds, gain, Mode::Linear, dcg, calibration)?;
                continue;
            }
        }
        if codes.integration_time <= u32::from(calibration.linear.minimum) {
            return Ok(output(isp));
        }
        codes.integration_time = ((codes.integration_time as f32) - calibration.linear.step) as u32;
    }
}

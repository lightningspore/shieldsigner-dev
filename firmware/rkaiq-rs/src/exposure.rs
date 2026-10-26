//! Checked AeReal2RegConv reconstruction. Calibration is supplied explicitly;
//! no guessed sensor coefficients or live writes are introduced here.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct GainBand {
    pub lower: f32,
    pub upper: f32,
    pub scale: f32,
    pub offset: f32,
    pub exponent: f32,
    pub minimum: f32,
    pub maximum: f32,
}
#[derive(Clone, Copy, Debug)]
pub enum GainModel<'a> {
    Bands(&'a [GainBand]),
    Logarithmic,
}
#[derive(Clone, Copy, Debug)]
pub struct Timing {
    pub minimum: u16,
    pub step: f32,
    pub offset: f32,
}
#[derive(Clone, Copy, Debug)]
pub enum Mode {
    Linear,
    HdrTwo,
    HdrThree,
}
#[derive(Clone, Copy, Debug)]
pub struct Calibration<'a> {
    pub gain: GainModel<'a>,
    pub factors: [f32; 4],
    pub frame_length: f32,
    pub pixel_clock_mhz: f32,
    pub line_length_pixels: f32,
    pub linear: Timing,
    pub hdr: [Timing; 2],
    pub linear_dcg_ratio: f32,
    pub hdr_dcg_ratio: f32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Codes {
    pub integration_time: u32,
    pub gain: u32,
}
pub fn convert(
    seconds: f32,
    real_gain: f32,
    mode: Mode,
    dcg_mode: i32,
    calibration: Calibration<'_>,
) -> Result<Codes, InvalidInput> {
    let timing = match mode {
        Mode::Linear => calibration.linear,
        Mode::HdrTwo => calibration.hdr[0],
        Mode::HdrThree => calibration.hdr[1],
    };
    let ratio = if dcg_mode < 1 {
        1.
    } else {
        match mode {
            Mode::Linear => calibration.linear_dcg_ratio,
            _ => calibration.hdr_dcg_ratio,
        }
    };
    let values = [
        seconds,
        real_gain,
        ratio,
        timing.step,
        timing.offset,
        calibration.frame_length,
        calibration.pixel_clock_mhz,
        calibration.line_length_pixels,
    ];
    if values
        .iter()
        .chain(&calibration.factors)
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if seconds < 0.
        || real_gain <= 0.
        || ratio <= 0.
        || timing.step <= 0.
        || calibration.frame_length <= 0.
        || calibration.pixel_clock_mhz <= 0.
        || calibration.line_length_pixels <= 0.
    {
        return Err(InvalidInput::Exposure);
    }
    let normalized = real_gain / ratio;
    if normalized <= 0. || !normalized.is_finite() {
        return Err(InvalidInput::GainRange);
    }
    let gain = match calibration.gain {
        GainModel::Logarithmic => {
            let value = ((libm::log10f(normalized) * 20.) * 10.) / 3. + 0.5;
            (value as i32) as u32
        }
        GainModel::Bands(bands) => {
            for band in bands {
                if [
                    band.lower,
                    band.upper,
                    band.scale,
                    band.offset,
                    band.exponent,
                    band.minimum,
                    band.maximum,
                ]
                .iter()
                .any(|v| !v.is_finite())
                {
                    return Err(InvalidInput::NonFinite);
                }
                if band.lower > band.upper || band.minimum < 0. || band.maximum < band.minimum {
                    return Err(InvalidInput::GainRange);
                }
            }
            let fallback = GainBand {
                lower: 0.,
                upper: 0.,
                scale: 16.,
                offset: 0.,
                exponent: 1.,
                minimum: 16.,
                maximum: 255.,
            };
            let band = bands
                .iter()
                .find(|b| b.lower <= normalized && normalized <= b.upper)
                .filter(|b| b.scale != 0.)
                .unwrap_or(&fallback);
            let value = libm::fmaf(
                band.scale,
                libm::powf(normalized, band.exponent),
                -band.offset,
            ) + 0.5;
            let mut code = (value as i32) as u32;
            if (code as f32) < band.minimum {
                code = band.minimum as u32;
            }
            if (code as f32) > band.maximum {
                code = band.maximum as u32;
            }
            code
        }
    };
    let clock = ((seconds * calibration.pixel_clock_mhz) * 1_000_000.)
        / calibration.line_length_pixels
        + calibration.factors[3];
    let base = libm::fmaf(
        calibration.factors[0],
        calibration.frame_length,
        calibration.factors[1],
    );
    let coarse = (libm::fmaf(clock, calibration.factors[2], base) as i32) as u32;
    let steps = (((coarse as f32) - timing.offset) / timing.step) as i32;
    let aligned = libm::fmaf(steps as f32, timing.step, timing.offset) as u32;
    Ok(Codes {
        integration_time: aligned.max(timing.minimum as u32),
        gain,
    })
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_timing_rejected_and_unused_dcg_ratio_not_required() {
        let timing = Timing {
            minimum: 1,
            step: 1.,
            offset: 0.,
        };
        let mut cfg = Calibration {
            gain: GainModel::Bands(&[]),
            factors: [0., 0., 1., 0.],
            frame_length: 1600.,
            pixel_clock_mhz: 72.,
            line_length_pixels: 2400.,
            linear: timing,
            hdr: [timing; 2],
            linear_dcg_ratio: f32::NAN,
            hdr_dcg_ratio: f32::NAN,
        };
        assert!(convert(0.01, 1., Mode::Linear, 0, cfg).is_ok());
        assert!(convert(0.01, 1., Mode::Linear, 1, cfg).is_err());
        cfg.linear.step = 0.;
        assert!(convert(0.01, 1., Mode::Linear, 0, cfg).is_err());
    }
}

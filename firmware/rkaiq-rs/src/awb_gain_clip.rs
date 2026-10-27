//! AwbGainClip (ELF 0xca9c0), including native forward/inverse CCT helpers.
use crate::{
    awb_gain::Gains,
    awb_single_color::{self, Line},
    InvalidInput,
};
pub struct Bounds<'a> {
    pub cct: &'a [f32],
    /// Native lower tint boundary is the negative of this interpolated curve.
    pub negative_tint: &'a [f32],
    pub positive_tint: &'a [f32],
}
pub struct Calibration<'a> {
    pub first: Line,
    pub second: Line,
    pub daylight: bool,
    pub daylight_threshold: u32,
    pub daylight_minimum_cct: f32,
    pub bounds: Option<Bounds<'a>>,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Clipped {
    pub gain: Gains,
    pub clipped: bool,
}

/// Prior clipped flag is sticky. Even without an actual clamp, valid forward
/// CCT conversion is followed by inverse conversion and gain normalization.
pub fn clip(
    gain: Gains,
    was_clipped: bool,
    brightness: u32,
    cal: &Calibration<'_>,
) -> Result<Clipped, InvalidInput> {
    let mut temperature = awb_single_color::color_temperature(gain, cal.first, cal.second)?;
    let mut clipped = was_clipped;
    if !temperature.valid {
        return Ok(Clipped { gain, clipped });
    }
    if cal.daylight && brightness > cal.daylight_threshold {
        if !cal.daylight_minimum_cct.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if temperature.cct < cal.daylight_minimum_cct {
            temperature.cct = cal.daylight_minimum_cct;
            clipped = true;
        }
    }
    if let Some(bounds) = &cal.bounds {
        if bounds.cct.is_empty() {
            return Err(InvalidInput::Length);
        }
        if temperature.cct < bounds.cct[0] {
            temperature.cct = bounds.cct[0];
            clipped = true;
        } else if bounds.cct[bounds.cct.len() - 1] < temperature.cct {
            temperature.cct = bounds.cct[bounds.cct.len() - 1];
            clipped = true;
        }
        let lower = -awb_single_color::curve(bounds.cct, bounds.negative_tint, temperature.cct)?;
        let upper = awb_single_color::curve(bounds.cct, bounds.positive_tint, temperature.cct)?;
        if temperature.ccri < lower {
            temperature.ccri = lower;
            clipped = true;
        }
        if upper < temperature.ccri {
            temperature.ccri = upper;
            clipped = true;
        }
    }
    let (gain, _) =
        awb_single_color::gain_from_color_temperature(temperature, cal.first, cal.second, gain)?;
    Ok(Clipped { gain, clipped })
}

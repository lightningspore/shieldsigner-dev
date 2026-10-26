//! Incremental reconstruction of the pinned Luckfox RKAIQ binary.
//!
//! These are recovered numerical components, not a complete ISP library.
//! Function behavior is checked against original ARM machine code under Unicorn.
#![no_std]
pub mod ae;
pub mod ae_histogram;
pub mod discovery;
pub mod engine;
pub mod exposure;
pub mod gain;
pub mod isp32;
pub mod media;
pub mod sensor;
pub mod sensor_descriptor;
pub mod statistics;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum InvalidInput {
    Length,
    NonFinite,
    NonIncreasing,
    DegenerateRange,
    AlphaRange,
    FractionalBits,
    Exposure,
    GainRange,
}

/// Piecewise linear interpolation with the binary's endpoint clamping and
/// 0.001 *double-precision* minimum-span comparison.
/// Original symbol: `_Z13interpolationPKfS0_ifPf`, ELF address 0x20630 (Thumb).
pub fn interpolate(knots: &[f32], values: &[f32], sample: f32) -> Result<f32, InvalidInput> {
    if knots.is_empty() || knots.len() != values.len() {
        return Err(InvalidInput::Length);
    }
    if !sample.is_finite() || knots.iter().chain(values).any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if knots.windows(2).any(|p| p[0] >= p[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    if sample <= knots[0] {
        return Ok(values[0]);
    }
    let last = knots.len() - 1;
    if sample >= knots[last] {
        return Ok(values[last]);
    }
    let upper = knots.iter().position(|&x| sample < x).unwrap();
    let lower = upper - 1;
    let span = knots[upper] - knots[lower];
    if (span as f64) < 0.001 {
        return Ok(values[lower]);
    }
    let ratio = (sample - knots[lower]) / span;
    Ok(libm::fmaf(
        ratio,
        values[upper] - values[lower],
        values[lower],
    ))
}

/// Saturation-indexed color-correction profile. The original input record's
/// saturation is at byte 8, matrix at 12, and offsets at 48 (ARM32 layout).
#[derive(Clone, Copy, Debug)]
pub struct ColorProfile {
    pub saturation: f32,
    pub matrix: [f32; 9],
    pub offsets: [f32; 3],
}

fn profile_weight(
    value: f32,
    first: &ColorProfile,
    second: &ColorProfile,
) -> Result<f32, InvalidInput> {
    if !value.is_finite() || !first.saturation.is_finite() || !second.saturation.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if second.saturation == first.saturation {
        return Err(InvalidInput::DegenerateRange);
    }
    Ok((second.saturation - value) / (second.saturation - first.saturation))
}

/// Original `SatInterpolateMatrices`, ELF address 0xfd2e6 (Thumb).
/// Preserves the original operation order and extrapolation outside endpoints.
pub fn saturation_matrix(
    value: f32,
    first: &ColorProfile,
    second: &ColorProfile,
) -> Result<[f32; 9], InvalidInput> {
    let weight = profile_weight(value, first, second)?;
    let mut output = [0.; 9];
    for (i, out) in output.iter_mut().enumerate() {
        *out = libm::fmaf(first.matrix[i], weight, second.matrix[i] * (1.0 - weight));
    }
    Ok(output)
}

/// Original `SatInterpolateOffset`, ELF address 0xfd32e (Thumb).
pub fn saturation_offsets(
    value: f32,
    first: &ColorProfile,
    second: &ColorProfile,
) -> Result<[f32; 3], InvalidInput> {
    let weight = profile_weight(value, first, second)?;
    let mut output = [0.; 3];
    for (i, out) in output.iter_mut().enumerate() {
        *out = libm::fmaf(first.offsets[i], weight, (1.0 - weight) * second.offsets[i]);
    }
    Ok(output)
}

pub const LUT_ENTRIES: usize = 729; // 9 × 9 × 9
pub const LUT_VALUES: usize = LUT_ENTRIES * 3;

/// Original `InterpLutbyAlp`, ELF address 0xfc8bc (Thumb).
/// The coefficient is truncated to Q7, then each u16 value is blended with
/// integer arithmetic and a shift, without rounding-to-nearest.
pub fn blend_lut(
    alpha: f32,
    first: &[u16; LUT_VALUES],
    second: &[u16; LUT_VALUES],
    output: &mut [u16; LUT_VALUES],
) -> Result<(), InvalidInput> {
    if !alpha.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if !(0.0..=1.0).contains(&alpha) {
        return Err(InvalidInput::AlphaRange);
    }
    let weight = (alpha * 128.0) as u32;
    for i in 0..LUT_VALUES {
        output[i] = ((weight * second[i] as u32 + (128 - weight) * first[i] as u32) >> 7) as u16;
    }
    Ok(())
}

/// Original `_Z18AdpccInterpolationiPiS_`, ELF address 0x11a984 (Thumb).
/// Fixed 13-point integer calibration interpolation used by defect-pixel
/// correction. Reproduces its f32 computation and `+0.5`, truncating conversion.
pub fn defect_pixel_interpolate(
    sample: i32,
    knots: &[i32; 13],
    values: &[i32; 13],
) -> Result<i32, InvalidInput> {
    if knots.windows(2).any(|p| p[0] >= p[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let mut result = 1.0_f32;
    for i in 0..12 {
        if knots[i] <= sample && sample < knots[i + 1] {
            let lo = knots[i] as f32;
            let hi = knots[i + 1] as f32;
            let a = values[i] as f32;
            let b = values[i + 1] as f32;
            result = libm::fmaf((sample as f32) - lo, (a - b) / (lo - hi), a);
            break;
        }
    }
    if sample < knots[0] {
        result = values[0] as f32;
    }
    if sample >= knots[12] {
        result = values[12] as f32;
    }
    Ok(((result as f64) + 0.5) as i32)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn interpolation_bounds_and_tiny_span() {
        assert_eq!(interpolate(&[0., 1.], &[2., 4.], -1.), Ok(2.));
        assert_eq!(interpolate(&[0., 1.], &[2., 4.], 2.), Ok(4.));
        assert_eq!(interpolate(&[0., 1.], &[2., 4.], 0.5), Ok(3.));
        assert_eq!(
            interpolate(&[0., 0.0009, 1.], &[2., 4., 8.], 0.00045),
            Ok(2.)
        );
        assert_eq!(
            interpolate(&[1., 1.], &[2., 3.], 1.),
            Err(InvalidInput::NonIncreasing)
        );
    }
    #[test]
    fn lut_uses_truncation_not_rounding() {
        let first = [0; LUT_VALUES];
        let second = [129; LUT_VALUES];
        let mut output = [0; LUT_VALUES];
        blend_lut(0.5, &first, &second, &mut output).unwrap();
        assert_eq!(output, [64; LUT_VALUES]);
        blend_lut(1., &first, &second, &mut output).unwrap();
        assert_eq!(output, second);
        assert_eq!(
            blend_lut(-0.1, &first, &second, &mut output),
            Err(InvalidInput::AlphaRange)
        );
    }
}

/// Recovered multiplicative fixed-point branch of `gain_float_lim2_int`
/// (ELF 0xe79d8, Thumb), used by gain register packing with 6 fractional bits.
/// The ARM routine promotes the scaled f32 to f64 before adding ±0.5.
/// Supported bit counts are 0..=30; negative-shift/alternate-mode paths are
/// deliberately outside this checked API.
pub fn quantize_gain(value: f32, fractional_bits: u8) -> Result<i32, InvalidInput> {
    if !value.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if fractional_bits > 30 {
        return Err(InvalidInput::FractionalBits);
    }
    let scaled = value * ((1_i32 << fractional_bits) as f32);
    let rounded = (scaled as f64) + if scaled > 0.0 { 0.5 } else { -0.5 };
    Ok(rounded as i32)
}

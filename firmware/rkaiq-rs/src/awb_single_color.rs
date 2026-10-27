//! Native single-color confidence manager and gain-derived CCT/CCRI.
//! The grid/color classifier that produces manager statistics is not here yet.
use crate::{awb_gain::Gains, InvalidInput};

#[derive(Clone, Copy, Debug)]
pub struct Line {
    pub a: f32,
    pub b: f32,
    pub c: f32,
    pub valid: bool,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct ColorTemperature {
    pub valid: bool,
    pub cct: f32,
    pub ccri: f32,
}

/// AwbCalCCTandCCRIByGain (ELF 0xca840). Inactive/degenerate lines produce
/// the native invalid/zero result; positive Gr/Gb and |second.b| use a double
/// 1e-5 comparison after conversion from f32.
pub fn color_temperature(
    gain: Gains,
    first: Line,
    second: Line,
) -> Result<ColorTemperature, InvalidInput> {
    let invalid = ColorTemperature {
        valid: false,
        cct: 0.,
        ccri: 0.,
    };
    if !first.valid || !second.valid {
        return Ok(invalid);
    }
    if gain
        .iter()
        .chain([first.a, first.b, first.c, second.a, second.b, second.c].iter())
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if (gain[1] as f64) < 0.00001
        || (gain[2] as f64) < 0.00001
        || (libm::fabsf(second.b) as f64) < 0.00001
    {
        return Ok(invalid);
    }
    let red = gain[0] / gain[1];
    let blue = gain[3] / gain[2];
    let ccri = libm::fmaf(first.a, red, blue * first.b) - first.c;
    let projected = libm::fmaf(-ccri, first.a, red);
    let cct = libm::fmaf(-second.a, projected, second.c) / second.b;
    if !cct.is_finite() || !ccri.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    Ok(ColorTemperature {
        valid: true,
        cct,
        ccri,
    })
}

pub struct Calibration {
    pub brightness_knots: [f32; 8],
    pub brightness_weights: [f32; 8],
    pub density_knots: [f32; 6],
    pub density_weights: [f32; 6],
    pub distance_knots: [f32; 6],
    pub cct_knots: [f32; 3],
    /// Memory order at native config 0x74, 0x8c, 0xa4. Manager constructs
    /// its CCT interpolation values in the reverse order.
    pub distance_weights: [[f32; 6]; 3],
    pub disagreement_knots: [f32; 6],
    pub disagreement_weights: [f32; 6],
}

/// The pinned IQ has a repeated final density knot. Native interpolation
/// supports nondecreasing knots and chooses the last value at that endpoint.
fn curve<const N: usize>(
    knots: &[f32; N],
    values: &[f32; N],
    sample: f32,
) -> Result<f32, InvalidInput> {
    if N == 0 {
        return Err(InvalidInput::Length);
    }
    if !sample.is_finite() || knots.iter().chain(values).any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if knots.windows(2).any(|v| v[0] > v[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    if sample <= knots[0] {
        return Ok(values[0]);
    }
    if sample >= knots[N - 1] {
        return Ok(values[N - 1]);
    }
    let upper = knots.iter().position(|&v| sample < v).unwrap();
    let lower = upper - 1;
    let span = knots[upper] - knots[lower];
    if (span as f64) < 0.001 {
        return Ok(values[lower]);
    }
    Ok(libm::fmaf(
        (sample - knots[lower]) / span,
        values[upper] - values[lower],
        values[lower],
    ))
}

/// AwbSingleColorManager (ELF 0xcbaf0), including its original CCT helper.
/// `disagreements` is interpreted as signed i32, as in the native result word.
pub fn confidence(
    cal: &Calibration,
    brightness: f32,
    density: f32,
    mean_distance: f32,
    disagreements: i32,
    gain: Gains,
    first: Line,
    second: Line,
) -> Result<f32, InvalidInput> {
    let brightness_weight = curve(&cal.brightness_knots, &cal.brightness_weights, brightness)?;
    let density_weight = curve(&cal.density_knots, &cal.density_weights, density)?;
    let mut cct_weights = [0.; 3];
    for (value, table) in cct_weights.iter_mut().rev().zip(&cal.distance_weights) {
        *value = curve(&cal.distance_knots, table, mean_distance)?;
    }
    let temperature = color_temperature(gain, first, second)?;
    let color_weight = curve(&cal.cct_knots, &cct_weights, temperature.cct)?;
    let disagreement_weight = curve(
        &cal.disagreement_knots,
        &cal.disagreement_weights,
        disagreements as f32,
    )?;
    let weight = ((brightness_weight * density_weight) * color_weight) * disagreement_weight;
    if !weight.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    Ok(weight)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn decreasing_calibration_is_rejected_and_disabled_line_skips_invalid_gain() {
        assert_eq!(
            curve(&[1., 0.], &[0., 1.], 0.),
            Err(InvalidInput::NonIncreasing)
        );
        let line = Line {
            a: 0.,
            b: 0.,
            c: 0.,
            valid: false,
        };
        assert_eq!(
            color_temperature([f32::NAN; 4], line, line),
            Ok(ColorTemperature {
                valid: false,
                cct: 0.,
                ccri: 0.
            })
        );
    }
}

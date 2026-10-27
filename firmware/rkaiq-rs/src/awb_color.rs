//! Color transforms used by the original single-color grid classifier.
//! Float math imports in the pinned uClibc run double operations then round.
use crate::InvalidInput;

fn finite(values: &[f32]) -> Result<(), InvalidInput> {
    if values.iter().any(|v| !v.is_finite()) {
        Err(InvalidInput::NonFinite)
    } else {
        Ok(())
    }
}

/// rgb2xyz (ELF 0xcbce8), with native f64 coefficients and FMA order.
pub fn rgb_to_xyz(rgb: [f32; 3]) -> Result<[f32; 3], InvalidInput> {
    finite(&rgb)?;
    let [red, green, blue] = rgb.map(f64::from);
    let output = [
        [0.3576, 0.4124, 0.1805],
        [0.7152, 0.2126, 0.0722],
        [0.1192, 0.0193, 0.9505],
    ]
    .map(|[g, r, b]| libm::fma(blue, b, libm::fma(red, r, green * g)) as f32);
    finite(&output)?;
    Ok(output)
}

/// Internal f(float), ELF 0xcbda0. The exponent is the rounded f32 1/3,
/// promoted to double by the pinned powf wrapper; it is not a cube root.
pub fn lab_transfer(value: f32) -> Result<f32, InvalidInput> {
    finite(&[value])?;
    let output = if value as f64 > 0.008856451679035631 {
        libm::pow(value as f64, f32::from_bits(0x3eaaaaab) as f64) as f32
    } else {
        libm::fma(value as f64, 7.787037037037035, 0.13793103448275862) as f32
    };
    finite(&[output])?;
    Ok(output)
}

/// xyz2lab (ELF 0xcbdf0). White-point division rounds to f32 before the
/// transfer function. Y goes directly through that function.
pub fn xyz_to_lab(xyz: [f32; 3]) -> Result<[f32; 3], InvalidInput> {
    finite(&xyz)?;
    let x = lab_transfer((xyz[0] as f64 / 0.9504) as f32)?;
    let y = lab_transfer(xyz[1])?;
    let z = lab_transfer((xyz[2] as f64 / 1.0888) as f32)?;
    let output = [libm::fmaf(y, 116., -16.), (x - y) * 500., (y - z) * 200.];
    finite(&output)?;
    Ok(output)
}

/// lab2lch (ELF 0xcbeb4). Input is a*, b*. Hue retains atan2's signed
/// angle; native does not wrap negative degrees into [0, 360).
pub fn lab_to_lch(ab: [f32; 2]) -> Result<[f32; 2], InvalidInput> {
    finite(&ab)?;
    let [a, b] = ab;
    let squared = libm::fmaf(a, a, b * b);
    let chroma = libm::sqrt(squared as f64) as f32;
    let angle = libm::atan2(b as f64, a as f64) as f32;
    let hue = (angle / f32::from_bits(0x40490fda)) * 180.;
    let output = [chroma, hue];
    finite(&output)?;
    Ok(output)
}

//! CCM Saturationadjust (ELF 0xfd7e0), preserving mixed f32/f64 fused rounding.
use crate::InvalidInput;
pub fn apply(matrix: &mut [f32; 9], alpha: f32, saturation: f32) -> Result<(), InvalidInput> {
    if !alpha.is_finite() || !saturation.is_finite() || matrix.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if !(0. ..=1.).contains(&alpha) || !(0. ..=100.).contains(&saturation) {
        return Err(InvalidInput::AlphaRange);
    }
    if (alpha as f64) < 0.00001 {
        return Ok(());
    }
    let factor = (saturation - 50.) / 50. + 1.;
    let mut adjusted = *matrix;
    for (i, v) in adjusted.iter_mut().enumerate() {
        *v = if i % 4 == 0 {
            libm::fmaf(*v - 1., alpha, 1.)
        } else {
            *v * alpha
        };
    }
    let mut y = [0f32; 3];
    let mut cb = [0f32; 3];
    let mut cr = [0f32; 3];
    for col in 0..3 {
        let r = adjusted[col] as f64;
        let g = adjusted[3 + col] as f64;
        let b = adjusted[6 + col] as f64;
        y[col] = libm::fma(b, 0.114, libm::fma(r, 0.299, g * 0.587)) as f32;
        cb[col] = (libm::fma(b, 0.5, libm::fma(r, -0.1687, -(0.3313 * g))) as f32) * factor;
        cr[col] = (libm::fma(-b, 0.0813, libm::fma(r, 0.5, -(0.4187 * g))) as f32) * factor;
    }
    for col in 0..3 {
        adjusted[col] = libm::fma(
            cr[col] as f64,
            1.402,
            libm::fmaf(cb[col], 0., y[col]) as f64,
        ) as f32;
        adjusted[3 + col] = libm::fma(
            -(cr[col] as f64),
            0.71414,
            libm::fma(-(cb[col] as f64), 0.34414, y[col] as f64),
        ) as f32;
        adjusted[6 + col] =
            (libm::fma(cb[col] as f64, 1.772, y[col] as f64) + (cr[col] * 0.) as f64) as f32;
    }
    for (i, v) in adjusted.iter_mut().enumerate() {
        *v = if i % 4 == 0 {
            (*v - 1.) / alpha + 1.
        } else {
            *v / alpha
        };
    }
    *matrix = adjusted;
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_parameters_preserve_matrix() {
        let mut m = [1.; 9];
        for (a, s) in [(f32::NAN, 50.), (1., 101.), (-1., 50.)] {
            assert!(apply(&mut m, a, s).is_err());
            assert_eq!(m, [1.; 9]);
        }
    }
}

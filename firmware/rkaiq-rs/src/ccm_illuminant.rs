//! Nearest CCM illuminant selection (ELF 0xfd394).
use crate::InvalidInput;
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Estimate {
    /// Native initializes this to zero, even if no candidate is accepted.
    pub index: usize,
    pub matched: bool,
}
/// Native unweighted squared R/B gain distance, with first-candidate tie wins.
/// The native initial best distance is 9,999,999, not infinity.
pub fn estimate(calibrated_gains: &[[f32; 2]], gains: [f32; 2]) -> Result<Estimate, InvalidInput> {
    if gains
        .iter()
        .chain(calibrated_gains.iter().flatten())
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    let mut best = 9_999_999.;
    let mut result = Estimate {
        index: 0,
        matched: false,
    };
    for (index, candidate) in calibrated_gains.iter().enumerate() {
        let blue = gains[1] - candidate[1];
        let red = gains[0] - candidate[0];
        let distance = libm::fmaf(red, red, blue * blue);
        if distance < best {
            best = distance;
            result = Estimate {
                index,
                matched: true,
            };
        }
    }
    Ok(result)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn nonfinite_gains_are_rejected() {
        assert!(estimate(&[[1., f32::NAN]], [1., 1.]).is_err());
        assert!(estimate(&[[1., 1.]], [f32::INFINITY, 1.]).is_err());
    }
}

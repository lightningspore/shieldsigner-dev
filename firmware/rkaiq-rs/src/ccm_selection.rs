//! Saturation profile selection and interpolation (ELF 0xfd278/0xfd2e6/0xfd32e).
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Profile {
    pub saturation: f32,
    pub matrix: [f32; 9],
    pub offsets: [f32; 3],
}
#[derive(Clone, Copy, Debug)]
pub struct Selection {
    pub high: usize,
    pub low: usize,
    pub clamped: bool,
    pub matrix: [f32; 9],
    pub offsets: [f32; 3],
}
/// Profiles must be finite, strictly descending by saturation, and nonempty.
/// At exact interior knots native selection retains a two-profile bracket.
pub fn select(profiles: &[Profile], saturation: f32) -> Result<Selection, InvalidInput> {
    if profiles.is_empty() || profiles.len() > 65535 {
        return Err(InvalidInput::GainRange);
    }
    if !saturation.is_finite()
        || profiles.iter().any(|p| {
            !p.saturation.is_finite()
                || p.matrix
                    .iter()
                    .chain(p.offsets.iter())
                    .any(|v| !v.is_finite())
        })
    {
        return Err(InvalidInput::NonFinite);
    }
    if profiles
        .windows(2)
        .any(|p| p[0].saturation <= p[1].saturation)
    {
        return Err(InvalidInput::GainRange);
    }
    let last = profiles.len() - 1;
    let (high, low) = if saturation >= profiles[0].saturation {
        (0, 0)
    } else if saturation <= profiles[last].saturation {
        (last, last)
    } else {
        let low = profiles
            .iter()
            .position(|p| p.saturation < saturation)
            .unwrap();
        (low - 1, low)
    };
    let mut result = Selection {
        high,
        low,
        clamped: high == low,
        matrix: profiles[high].matrix,
        offsets: profiles[high].offsets,
    };
    if high != low {
        let a = profiles[high];
        let b = profiles[low];
        let weight = (b.saturation - saturation) / (b.saturation - a.saturation);
        let complement = 1. - weight;
        for i in 0..9 {
            result.matrix[i] = libm::fmaf(a.matrix[i], weight, b.matrix[i] * complement);
        }
        for i in 0..3 {
            result.offsets[i] = libm::fmaf(a.offsets[i], weight, complement * b.offsets[i]);
        }
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_profile_grids_are_rejected() {
        let p = Profile {
            saturation: 50.,
            matrix: [1.; 9],
            offsets: [0.; 3],
        };
        assert!(select(&[], 25.).is_err());
        assert!(select(&[p, p], 25.).is_err());
        assert!(select(&[p], f32::NAN).is_err());
        let mut invalid = p;
        invalid.matrix[8] = f32::INFINITY;
        assert!(select(&[invalid], 25.).is_err());
    }
}

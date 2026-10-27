//! CCM AE/AWB deadband, JudgeCcmRes3aConverge (ELF 0xfe1dc).
use crate::InvalidInput;
/// Records are [sensor gain, red WB gain, blue WB gain]. Small changes overwrite
/// current inputs with the baseline; significant changes advance the baseline.
/// Native gain comparison is absolute; WB uses squared R/B Euclidean distance.
pub fn filter(
    baseline: &mut [f32; 3],
    current: &mut [f32; 3],
    gain_tolerance: f32,
    wb_tolerance: f32,
) -> Result<bool, InvalidInput> {
    if baseline
        .iter()
        .chain(current.iter())
        .chain([&gain_tolerance, &wb_tolerance])
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if gain_tolerance < 0. || wb_tolerance < 0. {
        return Err(InvalidInput::GainRange);
    }
    let old = *current;
    let mut changed = false;
    if (baseline[0] - old[0]).abs() <= gain_tolerance {
        current[0] = baseline[0];
    } else {
        baseline[0] = old[0];
        changed = true;
    }
    let blue = baseline[2] - old[2];
    let red = baseline[1] - old[1];
    if libm::fmaf(red, red, blue * blue) > wb_tolerance * wb_tolerance {
        baseline[1] = old[1];
        baseline[2] = old[2];
        changed = true;
    } else {
        current[1] = baseline[1];
        current[2] = baseline[2];
    }
    Ok(changed)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_input_preserves_both_records() {
        let mut baseline = [1.; 3];
        let mut current = [2.; 3];
        for tolerance in [-1., f32::NAN] {
            assert!(filter(&mut baseline, &mut current, tolerance, 0.).is_err());
            assert_eq!(baseline, [1.; 3]);
            assert_eq!(current, [2.; 3]);
        }
    }
}

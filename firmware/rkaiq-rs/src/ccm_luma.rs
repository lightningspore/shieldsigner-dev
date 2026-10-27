//! Symmetric CCM YAlpSymAutoCfg (ELF 0xfe250).
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Row {
    pub iso: f32,
    pub curve: [f32; 17],
}
/// Caller owns previous bracket/weight, as in the native argument contract.
/// Update the full curve only when its summed absolute change exceeds one.
pub fn symmetric(
    rows: &[Row],
    iso: f32,
    previous_weight: f32,
    previous_upper: usize,
    force: bool,
    curve: &mut [f32; 17],
) -> Result<bool, InvalidInput> {
    if rows.len() < 2 {
        return Err(InvalidInput::Length);
    }
    if !iso.is_finite()
        || !previous_weight.is_finite()
        || curve.iter().any(|v| !v.is_finite())
        || rows
            .iter()
            .any(|r| !r.iso.is_finite() || r.curve.iter().any(|v| !v.is_finite()))
    {
        return Err(InvalidInput::NonFinite);
    }
    if rows.windows(2).any(|r| r[0].iso >= r[1].iso) {
        return Err(InvalidInput::NonIncreasing);
    }
    let last = rows.len() - 1;
    let (upper, weight) = if iso < rows[0].iso {
        (1, 0.)
    } else if iso > rows[last].iso {
        (last, 1.)
    } else {
        let upper = rows.iter().position(|r| iso < r.iso).unwrap_or(last);
        let span = rows[upper].iso - rows[upper - 1].iso;
        if (span as f64) < 0.00001 {
            return Err(InvalidInput::DegenerateRange);
        }
        (upper, (iso - rows[upper - 1].iso) / span)
    };
    if ((weight - previous_weight).abs() as f64) <= 0.01 && upper == previous_upper && !force {
        return Ok(false);
    }
    let mut next = [0.; 17];
    let mut change = 0.;
    for i in 0..17 {
        next[i] = libm::floorf(
            libm::fmaf(
                rows[upper].curve[i],
                weight,
                (1. - weight) * rows[upper - 1].curve[i],
            ) + 0.5,
        );
        change += (next[i] - curve[i]).abs();
    }
    if change > 1. {
        *curve = next;
        Ok(true)
    } else {
        Ok(false)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_grid_preserves_curve() {
        let row = Row {
            iso: 50.,
            curve: [10.; 17],
        };
        let mut curve = [5.; 17];
        assert!(symmetric(&[row, row], 50., 0., 0, true, &mut curve).is_err());
        assert_eq!(curve, [5.; 17]);
    }
}

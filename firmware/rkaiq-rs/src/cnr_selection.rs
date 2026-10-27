//! Complete cnr_select_params_by_ISO_V30 selected-record writes.
use crate::InvalidInput;
pub const ROW_BYTES: usize = 180;
pub const TABLE_BYTES: usize = 56 + 13 * ROW_BYTES;
fn f32_at(b: &[u8], p: usize) -> f32 {
    f32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
/// Retain SDK padding; out-of-table ISO extrapolates the first/last interval,
/// as native does. Reject malformed knots/nonfinite arithmetic transactionally.
pub fn select(
    table: &[u8; TABLE_BYTES],
    iso: i32,
    output: &mut [u8; ROW_BYTES],
) -> Result<[usize; 2], InvalidInput> {
    let mut knots = [0.; 13];
    for (i, knot) in knots.iter_mut().enumerate() {
        *knot = f32_at(table, 4 + i * 4);
        if !knot.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if *knot < 1. || *knot >= i32::MAX as f32 {
            return Err(InvalidInput::GainRange);
        }
    }
    if knots.windows(2).any(|p| p[0] as i32 >= p[1] as i32) {
        return Err(InvalidInput::NonIncreasing);
    }
    let sample = iso as f32;
    let mut bracket = [0, 1];
    for i in 0..12 {
        if sample >= knots[i] && sample <= knots[i + 1] {
            bracket = [i, i + 1];
        }
    }
    if sample > knots[12] {
        bracket = [11, 12];
    }
    let [low, high] = bracket;
    let a = knots[low] as i32;
    let b = knots[high] as i32;
    let lower_distance = iso.checked_sub(a).ok_or(InvalidInput::GainRange)?;
    let upper_distance = b.checked_sub(iso).ok_or(InvalidInput::GainRange)?;
    let ratio = lower_distance as f32 / (b - a) as f32;
    let lo = &table[56 + low * ROW_BYTES..56 + (low + 1) * ROW_BYTES];
    let hi = &table[56 + high * ROW_BYTES..56 + (high + 1) * ROW_BYTES];
    let near = if upper_distance < lower_distance {
        hi
    } else {
        lo
    };
    let mut next = *output;
    next[0] = u8::from(i32::from_le_bytes(table[..4].try_into().unwrap()) != 0);
    next[1..3].copy_from_slice(&near[1..3]);
    next[52] = near[52];
    next[140..180].copy_from_slice(&near[140..180]);
    for p in (4..52).step_by(4).chain((56..140).step_by(4)) {
        let x = f32_at(lo, p);
        let y = f32_at(hi, p);
        if !x.is_finite() || !y.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let value = libm::fmaf(y - x, ratio, x);
        if !value.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        next[p..p + 4].copy_from_slice(&value.to_le_bytes());
    }
    *output = next;
    Ok(bracket)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_invalid_calibration_without_output_mutation() {
        let mut table = [0; TABLE_BYTES];
        for i in 0..13 {
            table[4 + i * 4..8 + i * 4].copy_from_slice(&((i + 1) as f32 * 50.).to_le_bytes());
        }
        let mut output = [0xa5; ROW_BYTES];
        table[8..12].copy_from_slice(&50.5f32.to_le_bytes());
        assert_eq!(
            select(&table, 75, &mut output),
            Err(InvalidInput::NonIncreasing)
        );
        assert_eq!(output, [0xa5; ROW_BYTES]);
        table[8..12].copy_from_slice(&100f32.to_le_bytes());
        table[56 + 4..56 + 8].copy_from_slice(&f32::NAN.to_le_bytes());
        assert_eq!(
            select(&table, 75, &mut output),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(output, [0xa5; ROW_BYTES]);
    }
}

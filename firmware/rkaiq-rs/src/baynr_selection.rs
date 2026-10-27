//! Complete selected-record writes of bayer2dnr_select_params_by_ISO_V23.
use crate::InvalidInput;
pub const ROW_BYTES: usize = 252;
pub const TABLE_BYTES: usize = 60 + 13 * ROW_BYTES;
fn i32_at(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn f32_at(b: &[u8], p: usize) -> f32 {
    f32::from_bits(i32_at(b, p) as u32)
}
fn u16_at(b: &[u8], p: usize) -> u16 {
    u16::from_le_bytes(b[p..p + 2].try_into().unwrap())
}
/// Supported calibration has thirteen strictly increasing positive integer-gain
/// knots after truncating ISO/50. Outside their range is rejected: native leaves
/// zero bracket bounds there and can produce non-finite selected values.
/// Preserve every selected-record padding byte and commit only on success.
pub fn select(
    table: &[u8; TABLE_BYTES],
    iso: i32,
    output: &mut [u8; ROW_BYTES],
) -> Result<[usize; 2], InvalidInput> {
    let mut knots = [0; 13];
    for (i, knot) in knots.iter_mut().enumerate() {
        let raw = f32_at(table, 8 + i * 4) / 50.;
        if !raw.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if raw < 1. || raw > i32::MAX as f32 {
            return Err(InvalidInput::GainRange);
        }
        *knot = raw as i32;
    }
    if knots.windows(2).any(|p| p[0] >= p[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let gain = if iso < 50 { 1 } else { iso / 50 };
    let mut bracket = None;
    for i in 0..12 {
        if knots[i] <= gain && gain <= knots[i + 1] {
            bracket = Some([i, i + 1]);
        }
    }
    let [low, high] = bracket.ok_or(InvalidInput::GainRange)?;
    let ratio = (gain - knots[low]) as f32 / (knots[high] - knots[low]) as f32;
    let lo = &table[60 + low * ROW_BYTES..60 + (low + 1) * ROW_BYTES];
    let hi = &table[60 + high * ROW_BYTES..60 + (high + 1) * ROW_BYTES];
    let near = if knots[high] - gain < gain - knots[low] {
        hi
    } else {
        lo
    };
    let mut next = *output;
    next[0] = u8::from(i32_at(table, 0) != 0);
    next[240] = table[4];
    for p in [132, 156, 168] {
        next[p] = near[p];
    }
    for (p, n) in [(4, 64), (158, 4), (164, 4), (176, 32)] {
        next[p..p + n].copy_from_slice(&near[p..p + n]);
    }
    for p in [136, 140, 144, 148, 172, 244, 248] {
        let a = f32_at(lo, p);
        let b = f32_at(hi, p);
        if !a.is_finite() || !b.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let value = libm::fmaf(b - a, ratio, a);
        if !value.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        next[p..p + 4].copy_from_slice(&value.to_le_bytes());
    }
    for i in 0..16 {
        let p = 68 + i * 4;
        let a = i32_at(lo, p);
        let b = i32_at(hi, p);
        let value = libm::fmaf(b.wrapping_sub(a) as f32, ratio, a as f32) as i32;
        next[p..p + 4].copy_from_slice(&value.to_le_bytes());
    }
    for p in [152, 154].into_iter().chain((208..240).step_by(2)) {
        let a = i32::from(u16_at(lo, p));
        let b = i32::from(u16_at(hi, p));
        let value = libm::fmaf((b - a) as f32, ratio, a as f32) as u16;
        next[p..p + 2].copy_from_slice(&value.to_le_bytes());
    }
    *output = next;
    Ok([low, high])
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unsupported_calibration_or_iso_preserves_output() {
        let mut table = [0; TABLE_BYTES];
        for i in 0..13 {
            table[8 + i * 4..12 + i * 4].copy_from_slice(&(50. * (1u32 << i) as f32).to_le_bytes());
        }
        let mut output = [0xa5; ROW_BYTES];
        assert_eq!(
            select(&table, 204850, &mut output),
            Err(InvalidInput::GainRange)
        );
        assert_eq!(output, [0xa5; ROW_BYTES]);
        table[12..16].copy_from_slice(&50f32.to_le_bytes());
        assert_eq!(
            select(&table, 100, &mut output),
            Err(InvalidInput::NonIncreasing)
        );
        assert_eq!(output, [0xa5; ROW_BYTES]);
    }
}

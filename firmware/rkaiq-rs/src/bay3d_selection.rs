//! Complete normal table selection from bayertnr_select_params_by_ISO_V23.
use crate::InvalidInput;
pub const ROW_BYTES: usize = 400;
pub const TABLE_BYTES: usize = 56 + 13 * ROW_BYTES;
fn i(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn f(b: &[u8], p: usize) -> f32 {
    f32::from_bits(i(b, p) as u32)
}
pub fn select(
    table: &[u8; TABLE_BYTES],
    iso: i32,
    out: &mut [u8; ROW_BYTES],
) -> Result<[usize; 2], InvalidInput> {
    let mut knots = [0i32; 13];
    for (k, v) in knots.iter_mut().enumerate() {
        let raw = f(table, 4 + k * 4) / 50.;
        if !raw.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if raw < 1. || raw >= i32::MAX as f32 {
            return Err(InvalidInput::GainRange);
        }
        *v = raw as i32;
    }
    if knots.windows(2).any(|w| w[0] >= w[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let gain = if iso < 50 { 1 } else { iso / 50 };
    let mut bracket = None;
    for k in 0..12 {
        if knots[k] <= gain && gain <= knots[k + 1] {
            bracket = Some([k, k + 1]);
            break;
        }
    }
    if (iso as f32) < f(table, 4) {
        bracket = Some([0, 1]);
    }
    if (iso as f32) > f(table, 52) {
        bracket = Some([11, 12]);
    }
    let [lo, hi] = bracket.ok_or(InvalidInput::GainRange)?;
    let ratio = (gain - knots[lo]) as f32 / (knots[hi] - knots[lo]) as f32;
    let a = &table[56 + lo * 400..56 + (lo + 1) * 400];
    let b = &table[56 + hi * 400..56 + (hi + 1) * 400];
    let near = if knots[hi] - gain < gain - knots[lo] {
        b
    } else {
        a
    };
    let mut next = *out;
    next[0] = table[0];
    next[324..326].copy_from_slice(&a[324..326]);
    for p in [344, 348, 352] {
        let value = libm::fmaf(f(b, p) - f(a, p), ratio, f(a, p));
        if !value.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        next[p..p + 4].copy_from_slice(&value.to_le_bytes());
    }
    for p in (68..132)
        .step_by(4)
        .chain((196..324).step_by(4))
        .chain(core::iter::once(364))
    {
        let value = libm::fmaf(i(b, p).wrapping_sub(i(a, p)) as f32, ratio, i(a, p) as f32) as i32;
        next[p..p + 4].copy_from_slice(&value.to_le_bytes());
    }
    for (p, n) in [
        (4, 64),
        (132, 64),
        (340, 4),
        (356, 8),
        (368, 6),
        (380, 6),
        (388, 10),
    ] {
        next[p..p + n].copy_from_slice(&near[p..p + n]);
    }
    for p in [
        326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 374, 375, 376, 377,
    ] {
        next[p] = near[p];
    }
    *out = next;
    Ok([lo, hi])
}

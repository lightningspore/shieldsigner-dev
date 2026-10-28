//! ISO selection recovered from ynr_select_params_by_ISO_V22.
use crate::InvalidInput;
pub const ROW_BYTES: usize = 356;
pub const TABLE_BYTES: usize = 120 + 13 * ROW_BYTES;
fn f(b: &[u8], p: usize) -> f32 {
    f32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn u(b: &[u8], p: usize) -> u16 {
    u16::from_le_bytes(b[p..p + 2].try_into().unwrap())
}
/// Native nearest-row flags use float knots and truncated distances; interpolated
/// fields use the first inclusive integer-bound interval, clamping outer ISO.
pub fn select(
    table: &[u8; TABLE_BYTES],
    iso: i32,
    out: &mut [u8; ROW_BYTES],
) -> Result<[usize; 2], InvalidInput> {
    let knots: [f32; 13] = core::array::from_fn(|i| f(table, 68 + i * 4));
    if knots.iter().any(|x| !x.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if knots.windows(2).any(|p| p[0] as i32 >= p[1] as i32) {
        return Err(InvalidInput::NonIncreasing);
    }
    let mut near = 12;
    for i in 0..13 {
        if (iso as f32) < knots[i] {
            near = if i > 0
                && ((iso as f32 - knots[i - 1]) as i32) <= ((knots[i] - iso as f32) as i32)
            {
                i - 1
            } else {
                i
            };
            break;
        }
    }
    let (lo, hi, ratio) = if iso < knots[0] as i32 {
        (0, 1, 0.)
    } else if iso > knots[12] as i32 {
        (11, 12, 1.)
    } else {
        let low = (0..12)
            .find(|i| knots[*i] as i32 <= iso && iso <= knots[*i + 1] as i32)
            .ok_or(InvalidInput::GainRange)?;
        (
            low,
            low + 1,
            (iso - knots[low] as i32) as f32 / (knots[low + 1] as i32 - knots[low] as i32) as f32,
        )
    };
    let row = |i| &table[120 + i * ROW_BYTES..120 + (i + 1) * ROW_BYTES];
    let a = row(lo);
    let b = row(hi);
    let n = row(near);
    let mut next = *out;
    next[0] = u8::from(i32::from_le_bytes(table[..4].try_into().unwrap()) != 0);
    next[1..7].copy_from_slice(&n[1..7]);
    next[348..354].copy_from_slice(&n[348..354]);
    for p in (44..112)
        .step_by(4)
        .chain((124..148).step_by(4))
        .chain((160..348).step_by(4))
    {
        // 148..160 is the high-frequency luma u16 array; remaining fields are f32.
        let x = f(a, p);
        let y = f(b, p);
        if !x.is_finite() || !y.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let v = libm::fmaf(y - x, ratio, x);
        if !v.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        next[p..p + 4].copy_from_slice(&v.to_le_bytes());
    }
    for p in (8..42)
        .step_by(2)
        .chain((112..124).step_by(2))
        .chain((148..160).step_by(2))
    {
        let x = u(a, p);
        let y = u(b, p);
        let value = libm::fmaf(
            i32::from(y).wrapping_sub(i32::from(x)) as f32,
            ratio,
            f32::from(x),
        );
        let value = if p >= 112 {
            if value > 0. {
                (value as i32 as u16).wrapping_mul(4)
            } else {
                0
            }
        } else {
            value as i32 as u16
        };
        next[p..p + 2].copy_from_slice(&value.to_le_bytes());
    }
    *out = next;
    Ok([lo, hi])
}

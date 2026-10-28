//! Complete normal/HDR-slot SHARP V33 ISO selected-record writes.
pub use crate::sharp_calibration::{ROW_BYTES, TABLE_BYTES};
use crate::{
    sharp_calibration::{f32_at, i32_at, put_f32, put_u16, u16_at},
    InvalidInput,
};
fn interpolate(a: f32, b: f32, r: f32) -> f32 {
    libm::fmaf(b - a, r, a)
}
fn rounded(v: f32) -> i32 {
    (f64::from(v) + if v <= 0. { -0.5 } else { 0.5 }) as i32
}
/// Native uses the first inclusive ISO interval and clamps its outer endpoints.
/// Keep padding and unused fields unchanged; reject malformed calibration.
pub fn select(
    table: &[u8; TABLE_BYTES],
    iso: i32,
    out: &mut [u8; ROW_BYTES],
) -> Result<[usize; 2], InvalidInput> {
    let knots: [i32; 13] = core::array::from_fn(|i| i32_at(table, 88 + i * 4));
    if knots.windows(2).any(|a| a[0] >= a[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let (lo, hi, r) = if iso < knots[0] {
        (0, 1, 0.)
    } else if iso > knots[12] {
        (11, 12, 1.)
    } else {
        let i = (0..12)
            .find(|i| knots[*i] <= iso && iso <= knots[*i + 1])
            .ok_or(InvalidInput::GainRange)?;
        (
            i,
            i + 1,
            (iso - knots[i]) as f32 / (knots[i + 1] - knots[i]) as f32,
        )
    };
    let a = &table[140 + lo * ROW_BYTES..140 + (lo + 1) * ROW_BYTES];
    let b = &table[140 + hi * ROW_BYTES..140 + (hi + 1) * ROW_BYTES];
    let near = if iso - knots[lo] <= knots[hi] - iso {
        a
    } else {
        b
    };
    let mut next = *out;
    for (dst, src) in [(0, 0), (1, 4), (2, 8), (3, 76)] {
        next[dst] = u8::from(i32_at(table, src) != 0);
    }
    next[6..22].copy_from_slice(&a[6..22]);
    for j in 0..8 {
        let p = 22 + j * 2;
        let n = interpolate(u16_at(a, p) as f32, u16_at(b, p) as f32, r);
        put_u16(&mut next, p, if n > 0. { n as u16 } else { 0 });
        let p = 38 + j * 2;
        put_u16(
            &mut next,
            p,
            rounded(interpolate(u16_at(a, p) as f32, u16_at(b, p) as f32, r)) as u16,
        );
    }
    for p in [108, 117, 276, 288, 289] {
        next[p] = near[p];
    }
    for p in (56..108)
        .step_by(4)
        .chain([112])
        .chain((120..276).step_by(4))
        .chain([280, 284])
        .chain((292..388).step_by(4))
    {
        let x = f32_at(a, p);
        let y = f32_at(b, p);
        let n = interpolate(x, y, r);
        if !n.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        put_f32(&mut next, p, n);
    }
    next[4] = u8::from(interpolate(f32::from(a[4]), f32::from(b[4]), r) != 0.);
    let n = interpolate(f32::from(a[116]), f32::from(b[116]), r);
    next[116] = if n > 0. { n as u8 } else { 0 };
    let n = interpolate(u16_at(a, 118) as f32, u16_at(b, 118) as f32, r);
    put_u16(&mut next, 118, if n > 0. { n as u16 } else { 0 });
    *out = next;
    Ok([lo, hi])
}

//! Complete normal selected-result conversion recovered from ynr_fix_transfer_V22.
use crate::{ynr_selection::ROW_BYTES, InvalidInput};
pub const RESULT_BYTES: usize = 168;
fn f(b: &[u8], p: usize) -> f32 {
    f32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn u(b: &[u8], p: usize) -> u16 {
    u16::from_le_bytes(b[p..p + 2].try_into().unwrap())
}
fn i(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn clip(n: i32, max: i32) -> u16 {
    n.clamp(0, max) as u16
}
fn put(b: &mut [u8], p: usize, n: u16) {
    b[p..p + 2].copy_from_slice(&n.to_le_bytes())
}
fn q(x: f32, bits: i32, max: i32) -> u16 {
    clip((x * (1u32 << bits) as f32) as i32, max)
}
fn round(x: f32) -> i32 {
    (f64::from(x) + 0.5) as i32
}
fn curve(x: f32, points: &[f32; 6], values: &[f32; 6]) -> f32 {
    for n in 0..6 {
        if x <= points[n] {
            return if n == 0 {
                values[0]
            } else {
                libm::fmaf(
                    values[n] - values[n - 1],
                    (x - points[n - 1]) / (points[n] - points[n - 1]),
                    values[n - 1],
                )
            };
        }
    }
    values[5]
}
/// All SDK padding is retained. Input finite checks are transactional. Native
/// relies on positive raw dimensions; the public API rejects zero geometry.
pub fn quantize(
    s: &[u8; ROW_BYTES],
    strength: &[u8; 16],
    exp: &[u8; 88],
    out: &mut [u8; RESULT_BYTES],
) -> Result<(), InvalidInput> {
    for p in (44..112)
        .step_by(4)
        .chain((124..148).step_by(4))
        .chain((160..348).step_by(4))
    {
        if !f(s, p).is_finite() {
            return Err(InvalidInput::NonFinite);
        }
    }
    let mut factor = if strength[12] == 0 {
        1.
    } else {
        f(strength, 8)
    };
    if !factor.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if factor <= 0. {
        factor = f32::from_bits(0x358637bd)
    }
    let w = i(exp, 80);
    let h = i(exp, 84);
    if w <= 0 || h <= 0 {
        return Err(InvalidInput::Exposure);
    }
    let mut b = *out;
    put(&mut b, 0, 1);
    b[2] = s[6];
    b[3] = q(f(s, 192), 3, 8) as u8;
    put(&mut b, 4, q(f(s, 196), 4, 1023));
    b[6] = 0;
    b[7] = s[5];
    b[8] = s[4];
    b[9] = s[3];
    b[10] = s[2];
    b[11] = s[1];
    b[12] = s[0];
    let radius = 16. / w.wrapping_mul(w).wrapping_add(h.wrapping_mul(h)) as f32;
    let mantissa = (radius.to_bits() & 0x7fffff) as f32;
    let compressed = (126 - (radius.abs().to_bits() >> 23) as i32).wrapping_add(
        round(((mantissa * f32::from_bits(0x34000000) + 1.) * 0.5) * 256.).wrapping_mul(32),
    );
    put(&mut b, 14, clip(compressed, 16383));
    put(&mut b, 16, 128);
    put(&mut b, 18, (w / 2) as u16);
    put(&mut b, 20, (h / 2) as u16);
    for (dst, src, bits, max) in [
        (24, 204, 4, 255),
        (22, 200, 4, 1023),
        (34, 304, 2, 511),
        (36, 292, 0, 1023),
        (46, 296, 0, 1023),
    ] {
        let value = if dst == 46 {
            f(s, src) * 1023.
        } else {
            f(s, src)
        };
        put(&mut b, dst, q(value, bits, max))
    }
    put(&mut b, 26, q((1. / f(s, 280)) / factor, 9, 16383));
    put(&mut b, 28, q((1. / f(s, 276)) / factor, 9, 16383));
    put(&mut b, 30, q(f(s, 288) / factor, 7, 128));
    put(&mut b, 32, q(factor * f(s, 284), 6, 2047));
    put(&mut b, 38, q(factor * f(s, 320), 7, 128));
    put(&mut b, 40, q(factor * f(s, 308), 7, 128));
    put(&mut b, 42, q(f(s, 300) / factor, 10, 1024));
    put(&mut b, 44, 0);
    for (src, dst) in [(312, 48), (316, 54)] {
        let x = f(s, src);
        let e = libm::expf(-1. / ((x + x) * x));
        let denom = (e * 4. + 1.) + (e * e) * 4.;
        let a = round(((e * e) / denom) * 256.);
        let c = round((e / denom) * 256.);
        put(&mut b, dst, clip((64 - (a + c)) * 4, 511));
        put(&mut b, dst + 2, clip(c, 63));
        put(&mut b, dst + 4, clip(a, 63));
    }
    for n in 0..17 {
        put(&mut b, 60 + n * 2, u(s, 8 + n * 2).min(1024));
        put(&mut b, 94 + n * 2, q(f(s, 44 + n * 4) * f(s, 184), 3, 4095));
    }
    let points = core::array::from_fn(|n| u(s, 112 + n * 2) as f32);
    let ratios = core::array::from_fn(|n| f(s, 124 + n * 4));
    for n in 0..17 {
        let ratio = curve(u(&b, 60 + n * 2) as f32, &points, &ratios);
        let value = u(&b, 94 + n * 2) as f32 * ratio;
        put(&mut b, 94 + n * 2, clip(value as i32, 4095));
        b[128 + n] = q(f(s, 208 + n * 4), 4, 255) as u8;
    }
    put(&mut b, 146, q(f(s, 340), 11, 2047));
    b[148] = q(f(s, 328), 4, 31) as u8;
    put(&mut b, 150, q(factor * f(s, 324), 6, 1023));
    for n in 0..6 {
        b[152 + n] = s[348 + n].min(15)
    }
    b[160..164].copy_from_slice(&(q32(f(s, 332) / factor, 10, 262143)).to_le_bytes());
    put(&mut b, 164, q(f(s, 336), 10, 1023));
    put(&mut b, 166, q(factor * f(s, 344), 10, 1024));
    *out = b;
    Ok(())
}
fn q32(x: f32, bits: i32, max: i32) -> u32 {
    ((x * (1u32 << bits) as f32) as i32).clamp(0, max) as u32
}

//! Complete cnr_fix_transfer_V30 fixed-register conversion.
use crate::{cnr_selection::ROW_BYTES, isp_cnr::RESULT_BYTES, InvalidInput};
fn f32_at(b: &[u8], p: usize) -> f32 {
    f32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn clip(n: i32, max: i32) -> u16 {
    n.clamp(0, max) as u16
}
fn round(n: f32) -> i32 {
    (f64::from(n) + if n <= 0. { -0.5 } else { 0.5 }) as i32
}
fn put(b: &mut [u8], p: usize, n: u16) {
    b[p..p + 2].copy_from_slice(&n.to_le_bytes());
}
fn signed_q6(n: i32) -> i32 {
    let sign = if n < 1 { -1i32 } else { 1 };
    sign.wrapping_mul(n.wrapping_abs().wrapping_add(32) >> 6)
}
/// Preserve native SDK padding and all inputs. Exposure is a required native
/// pointer but this routine does not read its contents. Nonfinite selected
/// values are rejected before output publication.
pub fn quantize(
    selected: &[u8; ROW_BYTES],
    strength: &[u8; 16],
    _exposure: &[u8; 88],
    output: &mut [u8; RESULT_BYTES],
) -> Result<(), InvalidInput> {
    for p in (4..52).step_by(4).chain((56..180).step_by(4)) {
        if !f32_at(selected, p).is_finite() {
            return Err(InvalidInput::NonFinite);
        }
    }
    let mut factor = if strength[12] == 0 {
        1.
    } else {
        f32_at(strength, 8)
    };
    if !factor.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if factor <= 0. {
        factor = f32::from_bits(0x358637bd);
    }
    let f = |p| f32_at(selected, p);
    let mut next = *output;
    next[0] = selected[0];
    next[1] = 0;
    next[2] = 0;
    next[3] = match (selected[1], selected[2]) {
        (2, 2) => 0,
        (4, 4) => 1,
        _ => 2,
    };
    next[4] = selected[52];
    next[5] = clip((f(76) * 128.) as i32, 255) as u8;
    next[6] = clip((f(72) * 8.) as i32, 8) as u8;
    put(&mut next, 8, clip((f(68) * 16.) as i32, 1023));
    let uv = round(f(24) * 16.);
    let sigma = round((f(4) * 1023.) * factor) as f32;
    let reciprocal = (f32::from_bits(0x46d96bba) / sigma) as i32;
    put(
        &mut next,
        12,
        clip(
            signed_q6(
                reciprocal
                    .wrapping_mul(8i32.wrapping_sub(uv))
                    .wrapping_mul(2),
            ),
            16383,
        ),
    );
    put(
        &mut next,
        10,
        clip(signed_q6(reciprocal.wrapping_mul(uv)), 16383),
    );
    put(&mut next, 14, clip(round((f(8) * 1024.) * factor), 2047));
    for i in 0..4 {
        next[16 + i] = clip(round(f(140 + i * 4) * 128.), 255) as u8;
    }
    let slope = clip(round(f(28) * 128.), 1023);
    put(&mut next, 24, slope);
    let filter = (f(12) * 1023.) * factor;
    let product = i32::from(slope).wrapping_mul(round(f32::from_bits(0x4719bda5) / filter));
    // VCVT.F64.S32 converts the integer product directly; the decompiler
    // incorrectly suggests an intervening f32 rounding.
    let mut exponent = (libm::log(f64::from(product)) / core::f64::consts::LN_2 - 7.) as i32 as u32;
    exponent &= !((exponent as i32 >> 31) as u32);
    let mut shift = 15i32.wrapping_sub(exponent as i32);
    if shift < 0 {
        shift = (exponent as i32).wrapping_add(17);
    }
    next[22] = clip(shift, 63) as u8;
    let bits = exponent & 255;
    let divisor = if bits < 32 { (1u32 << bits) as i32 } else { 0 };
    next[21] = clip(round(product as f32 / divisor as f32), 255) as u8;
    next[20] = clip(uv, 15) as u8;
    next[26] = clip(round(f(20) * 64.), 63) as u8;
    next[27] = clip(round(f(16) * 8.), 127) as u8;
    for i in 0..6 {
        next[28 + i] = clip(f(176 - i * 4) as i32, 127) as u8;
    }
    put(&mut next, 34, clip(round(f(32) * 1024.), 2047));
    next[36] = clip(round(f(48) * 128.), 255) as u8;
    put(&mut next, 38, clip(round(f(56) * 1024.), 2047));
    next[40] = clip(round(f(40) * 16.), 127) as u8;
    put(
        &mut next,
        42,
        clip((13914. / ((f(36) * 1023.) * factor)) as i32, 1023),
    );
    next[44] = clip(round((f(44) * 128.) / factor), 255) as u8;
    put(&mut next, 46, clip(f(60) as i32, 511));
    put(&mut next, 48, clip(round(f(64) * 1024.), 32767));
    for i in 0..13 {
        next[50 + i] = clip(round(f(88 + i * 4) * 64.), 255) as u8;
    }
    next[63] = 8;
    next[64] = clip((f(80) * 64.) as i32, 255) as u8;
    *output = next;
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn nonfinite_input_preserves_output() {
        let mut selected = [0; ROW_BYTES];
        selected[176..180].copy_from_slice(&f32::NAN.to_le_bytes());
        let mut output = [0xa5; RESULT_BYTES];
        assert_eq!(
            quantize(&selected, &[0; 16], &[0; 88], &mut output),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(output, [0xa5; RESULT_BYTES]);
    }
}

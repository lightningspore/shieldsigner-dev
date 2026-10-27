//! Fixed-register quantization from complete bayer2dnr_fix_transfer_V23.
use crate::{baynr_selection::ROW_BYTES, isp_baynr::RESULT_BYTES, InvalidInput};
fn i32_at(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn f32_at(b: &[u8], p: usize) -> f32 {
    f32::from_bits(i32_at(b, p) as u32)
}
fn u16_at(b: &[u8], p: usize) -> u16 {
    u16::from_le_bytes(b[p..p + 2].try_into().unwrap())
}
fn put(b: &mut [u8], p: usize, n: u16) {
    b[p..p + 2].copy_from_slice(&n.to_le_bytes());
}
fn clipped(value: i32, max: i32) -> u16 {
    value.clamp(0, max) as u16
}
fn q10(value: f32) -> i32 {
    (value * 1024.) as i32
}
/// Selected SDK record, strength SDK record, exposure SDK record and previous
/// fixed output. Preserve padding and inactive HDR digital-gain slots. Invalid
/// metadata is rejected before changing output; no vendor dependency is loaded.
pub fn quantize(
    selected: &[u8; ROW_BYTES],
    strength: &[u8; 16],
    exposure: &[u8; 88],
    output: &mut [u8; RESULT_BYTES],
) -> Result<(), InvalidInput> {
    let mode = i32_at(exposure, 0);
    if !(0..=2).contains(&mode) {
        return Err(InvalidInput::Exposure);
    }
    for p in [136, 140, 144, 148, 172, 244, 248] {
        if !f32_at(selected, p).is_finite() {
            return Err(InvalidInput::NonFinite);
        }
    }
    let mut factor = if strength[12] == 0 {
        1.
    } else {
        f32_at(strength, 8)
    };
    if !factor.is_finite() || !f32_at(exposure, 64).is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if factor <= 0. {
        factor = f32::from_bits(0x358637bd);
    }
    let count = mode as usize + 1;
    let mut products = [0.; 3];
    for (i, out) in products[..count].iter_mut().enumerate() {
        let iso = i32_at(exposure, 68 + i * 4);
        let time = f32_at(exposure, 16 + i * 4);
        if iso <= 0 || !time.is_finite() || time <= 0. {
            return Err(InvalidInput::Exposure);
        }
        *out = iso as f32 * time;
        if !out.is_finite() || *out <= 0. {
            return Err(InvalidInput::Exposure);
        }
    }
    let mut next = *output;
    next[0] = if i32_at(exposure, 12) == 0 {
        0
    } else {
        selected[168] ^ 1
    };
    next[1] = selected[156];
    next[2] = selected[132];
    next[3] = 0;
    next[4] = if i32_at(exposure, 12) == 0 {
        selected[0]
    } else {
        1
    };
    for i in 0..count {
        let ratio = products[count - 1] / products[i];
        put(&mut next, 6 + i * 2, clipped(q10(ratio) / 4, 65535));
    }
    if count == 1 && f32_at(exposure, 64) > 0. {
        next[6..12].fill(0);
    }
    if selected[240] != 0 {
        if count >= 2 {
            let n = clipped(
                (f32::from(u16_at(&next, 6)) * f32_at(selected, 244)) as i32,
                65535,
            );
            put(&mut next, 6, n);
        }
        if count == 3 {
            let n = clipped(
                (f32::from(u16_at(&next, 8)) * f32_at(selected, 248)) as i32,
                65535,
            );
            put(&mut next, 8, n);
        }
    }
    put(&mut next, 12, u16_at(selected, 152).min(16383));
    put(&mut next, 14, u16_at(selected, 154).min(1023));
    put(
        &mut next,
        16,
        clipped(
            q10((f32_at(selected, 144) / f32_at(selected, 136)) / factor),
            1023,
        ),
    );
    put(&mut next, 18, 0);
    put(
        &mut next,
        20,
        clipped(q10(factor * f32_at(selected, 148)), 1023),
    );
    for i in 0..16 {
        put(
            &mut next,
            22 + i * 2,
            clipped(i32_at(selected, 4 + i * 4), 65535),
        );
        put(
            &mut next,
            54 + i * 2,
            clipped(
                (i32_at(selected, 68 + i * 4) as f32 * f32_at(selected, 136)) as i32,
                65535,
            ),
        );
    }
    let edge = (factor * f32_at(selected, 140)).min(16.);
    let denominator = (edge + edge) * edge;
    let distances = [32., 20., 16., 18., 10., 8., 4., 2.];
    let mut spatial = [0i32; 8];
    for (out, distance) in spatial.iter_mut().zip(distances) {
        *out = (libm::expf(-(distance / denominator)) * 1024.) as i32;
    }
    let indices = if i32_at(exposure, 8) == 0 {
        [5, 6, 7]
    } else {
        [4, 2, 3]
    };
    for (i, index) in indices.into_iter().enumerate() {
        put(&mut next, 86 + i * 2, clipped(spatial[index], 1023));
    }
    put(&mut next, 92, u16_at(selected, 160));
    put(&mut next, 94, u16_at(selected, 158).min(8191));
    next[96..100].copy_from_slice(&i32_at(selected, 164).clamp(0, 1048575).to_le_bytes());
    next[100..104].fill(0);
    for i in 0..16 {
        next[104 + i] = u16_at(selected, 176 + i * 2).min(255) as u8;
        let value = (f32::from(u16_at(selected, 208 + i * 2)) * f32_at(selected, 172)) * factor;
        put(&mut next, 120 + i * 2, clipped(value as i32, 4095));
    }
    *output = next;
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_exposure_preserves_prior_registers() {
        let selected = [0; ROW_BYTES];
        let strength = [0; 16];
        let mut exposure = [0; 88];
        let mut out = [0xa5; RESULT_BYTES];
        exposure[..4].copy_from_slice(&3i32.to_le_bytes());
        assert_eq!(
            quantize(&selected, &strength, &exposure, &mut out),
            Err(InvalidInput::Exposure)
        );
        assert_eq!(out, [0xa5; RESULT_BYTES]);
        exposure[..4].fill(0);
        exposure[68..72].copy_from_slice(&50i32.to_le_bytes());
        exposure[16..20].copy_from_slice(&(-1f32).to_le_bytes());
        assert_eq!(
            quantize(&selected, &strength, &exposure, &mut out),
            Err(InvalidInput::Exposure)
        );
        assert_eq!(out, [0xa5; RESULT_BYTES]);
    }
}

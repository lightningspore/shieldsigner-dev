//! Complete bayertnr_fix_transfer_V23 selected-to-fixed conversion.
use crate::{bay3d_selection::ROW_BYTES, isp_bay3d::RESULT_BYTES, InvalidInput};
fn i(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn f(b: &[u8], p: usize) -> f32 {
    f32::from_bits(i(b, p) as u32)
}
fn u(b: &[u8], p: usize) -> u16 {
    u16::from_le_bytes(b[p..p + 2].try_into().unwrap())
}
fn clip(n: i32, max: i32) -> u16 {
    n.clamp(0, max) as u16
}
fn put(b: &mut [u8], p: usize, n: u16) {
    b[p..p + 2].copy_from_slice(&n.to_le_bytes())
}
/// Native forces selected.lo_enable=1. Output padding, Lite-only wgtmin and
/// wgtmm fields remain untouched; the normal exposure pointer is not read.
pub fn quantize(
    selected: &mut [u8; ROW_BYTES],
    strength: &[u8; 16],
    _exposure: &[u8; 80],
    out: &mut [u8; RESULT_BYTES],
) -> Result<(), InvalidInput> {
    for p in [344, 348, 352, 356, 360, 368, 380, 388] {
        if !f(selected, p).is_finite() {
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
    let mut s = *selected;
    let mut n = *out;
    s[326] = 1;
    n[..2].fill(0);
    n[2] = s[0];
    n[3] = s[0] ^ 1;
    n[4] = s[327] ^ 1;
    n[5] = 0;
    for (dst, src) in [(6, 331), (7, 332), (10, 328), (11, 329), (12, 330)] {
        n[dst] = s[src] ^ 1;
    }
    n[8] = u8::from(s[374] > 1);
    n[9] = u8::from(s[375] > 1);
    n[13] = s[338];
    n[14] = 0;
    n[15] = s[333];
    put(&mut n, 16, clip((f(&s, 352) * 1024.) as i32, 1023));
    put(&mut n, 18, clip(i(&s, 364), 65535));
    n[20..24].copy_from_slice(&i(&s, 340).clamp(0, 268435455).to_le_bytes());
    n[24] = s[335];
    n[25] = u8::from(s[376] > 1);
    n[26] = 0;
    n[27] = 1;
    n[28] = 0;
    if s[324..326] == [4, 4] {
        n[27] = 0;
        n[28] = 1;
    } else if s[324..326] == [8, 8] {
        n[27] = 0;
    }
    n[29] = s[336];
    n[30] = s[337];
    n[31] = 1;
    n[32] = 0;
    n[33] = 0;
    n[34] = 0;
    match s[377] {
        1 => n[33] = 2,
        2 => n[33] = 1,
        3 => n[34] = 1,
        _ => {}
    }
    n[35] = s[334];
    put(&mut n, 38, clip(((1. - f(&s, 356)) * 1024.) as i32, 1023));
    put(
        &mut n,
        40,
        if s[327] == 0 {
            0
        } else {
            clip((f(&s, 360) * 1024.) as i32, 1023)
        },
    );
    for k in 0..16 {
        put(&mut n, 42 + k * 2, clip(i(&s, 4 + k * 4), 65535));
        put(&mut n, 74 + k * 2, clip(i(&s, 68 + k * 4), 16383));
        put(&mut n, 106 + k * 2, clip(i(&s, 132 + k * 4), 65535));
        put(
            &mut n,
            138 + k * 2,
            clip(
                ((i(&s, 260 + k * 4) as f32 * f(&s, 348)) * factor) as i32,
                16383,
            ),
        );
        put(
            &mut n,
            170 + k * 2,
            clip(
                ((i(&s, 196 + k * 4) as f32 * f(&s, 344)) * factor) as i32,
                1023,
            ),
        );
    }
    put(&mut n, 204, clip((f(&s, 380) * 256.) as i32, 4095));
    put(&mut n, 206, clip((f(&s, 388) * 256.) as i32, 4095));
    put(&mut n, 208, u(&s, 384).min(4095));
    put(&mut n, 210, u(&s, 392).min(4095));
    put(&mut n, 212, u(&s, 372).min(4095));
    put(&mut n, 214, clip((f(&s, 368) * 256.) as i32, 4095));
    n[216..220].fill(0);
    for k in 0..4 {
        n[220 + k] = s[394 + k].min(63);
    }
    *selected = s;
    *out = n;
    Ok(())
}

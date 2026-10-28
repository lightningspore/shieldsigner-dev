//! ISP32 temporal Bayer NR selected-result packing (ELF 0x2c686).
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 224;
pub const OFFSET: usize = 0x2869;
pub const BYTES: usize = 253;
pub const MODULE: u64 = 1 << 37;
pub fn apply(parameters: &mut [u8; PARAMETER_BYTES], result: &[u8; RESULT_BYTES]) {
    for (offset, mask) in [
        (0, MODULE | if result[2] != 0 { 1 << 36 } else { 0 }),
        (8, MODULE | if result[2] != 0 { 1 << 36 } else { 0 }),
        (16, MODULE),
    ] {
        let previous = u64::from_le_bytes(parameters[offset..offset + 8].try_into().unwrap());
        parameters[offset..offset + 8].copy_from_slice(&(previous | mask).to_le_bytes());
    }
    let out = &mut parameters[OFFSET..OFFSET + BYTES];
    for (dst, src, n) in [
        (0, 3, 13),
        (13, 24, 14),
        (27, 220, 4),
        (31, 16, 4),
        (35, 38, 4),
        (39, 42, 128),
        (199, 170, 32),
        (231, 202, 18),
        (249, 20, 4),
    ] {
        out[dst..dst + n].copy_from_slice(&result[src..src + n]);
    }
    // sig2_x at packed167..199 is intentionally retained, not zeroed.
}

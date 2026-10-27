//! ISP32 chroma NR serialization (ELF 0x2c982).
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 66;
pub const OFFSET: usize = 0x2a08;
pub const BYTES: usize = 59;
pub const MODULE: u64 = 1 << 39;

/// Native CNR always enables the hardware block. A disabled SDK result
/// bypasses its contribution by zeroing global alpha instead of the mask.
pub fn apply(parameters: &mut [u8; PARAMETER_BYTES], result: &[u8; RESULT_BYTES]) {
    for offset in [0, 8, 16] {
        let mask = u64::from_le_bytes(parameters[offset..offset + 8].try_into().unwrap());
        parameters[offset..offset + 8].copy_from_slice(&(mask | MODULE).to_le_bytes());
    }
    let out = &mut parameters[OFFSET..OFFSET + BYTES];
    // SDK alignment/padding and the native packed register ordering differ.
    for (dst, src, len) in [
        (0, 1, 4),
        (4, 16, 7),
        (11, 26, 8),
        (19, 36, 1),
        (20, 40, 1),
        (21, 44, 1),
        (22, 50, 15),
        (37, 5, 2),
        (39, 8, 8),
        (47, 24, 2),
        (49, 34, 2),
        (51, 38, 2),
        (53, 42, 2),
        (55, 46, 4),
    ] {
        out[dst..dst + len].copy_from_slice(&result[src..src + len]);
    }
    if result[0] == 0 {
        out[51..53].fill(0);
    }
}

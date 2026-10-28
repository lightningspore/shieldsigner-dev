//! ISP32 V33 sharpening result packing (native converter ELF 0x2d3f0).
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 178;
pub const OFFSET: usize = 0x2a43;
pub const BYTES: usize = 175;
pub const MODULE: u64 = 1 << 40;
/// Native keeps the module enabled; a disabled SDK result sets its bypass byte.
pub fn apply(params: &mut [u8; PARAMETER_BYTES], result: &[u8; RESULT_BYTES]) {
    for p in [0, 8, 16] {
        let n = u64::from_le_bytes(params[p..p + 8].try_into().unwrap());
        params[p..p + 8].copy_from_slice(&(n | MODULE).to_le_bytes());
    }
    let out = &mut params[OFFSET..OFFSET + BYTES];
    for (dst, src, n) in [
        (0, 4, 1),
        (1, 3, 1),
        (2, 2, 1),
        (3, 1, 1),
        (4, 0, 1),
        (5, 144, 2),
        (7, 9, 1),
        (8, 8, 1),
        (9, 7, 1),
        (10, 6, 1),
        (11, 10, 7),
        (18, 51, 1),
        (19, 50, 1),
        (20, 70, 1),
        (21, 69, 1),
        (22, 68, 1),
        (23, 73, 1),
        (24, 72, 1),
        (25, 71, 1),
        (26, 74, 6),
        (32, 82, 2),
        (34, 116, 22),
        (56, 140, 1),
        (57, 18, 16),
        (73, 34, 16),
        (89, 52, 16),
        (105, 80, 2),
        (107, 84, 28),
        (135, 112, 4),
        (139, 138, 2),
        (141, 142, 2),
        (143, 146, 32),
    ] {
        out[dst..dst + n].copy_from_slice(&result[src..src + n]);
    }
    if result[5] == 0 {
        out[0] = 1;
    }
}

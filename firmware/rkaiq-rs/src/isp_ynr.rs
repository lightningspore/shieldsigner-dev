//! ISP32 YNR result packing recovered from convertAiqYnrToIsp32Params.
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 168;
pub const OFFSET: usize = 0x2966;
pub const BYTES: usize = 162;
pub const MODULE: u64 = 1 << 38;
/// Hardware remains enabled; disabled tuning sets all five filter bypasses.
/// Packed frame_add4line has no corresponding SDK field and is preserved.
pub fn apply(p: &mut [u8; PARAMETER_BYTES], s: &[u8; RESULT_BYTES]) {
    for n in [0, 8, 16] {
        let v = u64::from_le_bytes(p[n..n + 8].try_into().unwrap());
        p[n..n + 8].copy_from_slice(&(v | MODULE).to_le_bytes());
    }
    let b = &mut p[OFFSET..OFFSET + BYTES];
    b[0] = s[0];
    b[1..3].copy_from_slice(&s[2..4]);
    b[3..9].copy_from_slice(&s[6..12]);
    if s[12] == 0 {
        b[4..9].fill(1)
    }
    b[9..26].copy_from_slice(&s[128..145]);
    b[26] = s[148];
    b[27..33].copy_from_slice(&s[152..158]);
    b[34..36].copy_from_slice(&s[4..6]);
    b[36..82].copy_from_slice(&s[14..60]);
    b[82..116].copy_from_slice(&s[60..94]);
    b[116..150].copy_from_slice(&s[94..128]);
    b[150..152].copy_from_slice(&s[146..148]);
    b[152..154].copy_from_slice(&s[150..152]);
    b[154..156].copy_from_slice(&s[166..168]);
    b[156..158].copy_from_slice(&s[164..166]);
    b[158..162].copy_from_slice(&s[160..164]);
}

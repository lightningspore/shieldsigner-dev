//! ISP32 Bayer spatial NR conversion (ELF 0x2c58e; dispatcher result type 12).
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 152;
pub const OFFSET: usize = 0x27d3;
pub const BYTES: usize = 150;
pub const MODULE: u64 = 1 << 36;
/// Pack native selected fields, preserving unrelated masks/data. Enable is any
/// nonzero SDK byte; unlike DPCC, zero clears an already enabled module.
pub fn apply(parameters: &mut [u8; PARAMETER_BYTES], result: &[u8; RESULT_BYTES]) {
    for offset in [0, 16] {
        let mask = u64::from_le_bytes(parameters[offset..offset + 8].try_into().unwrap());
        parameters[offset..offset + 8].copy_from_slice(&(mask | MODULE).to_le_bytes());
    }
    let enabled = u64::from_le_bytes(parameters[8..16].try_into().unwrap());
    parameters[8..16].copy_from_slice(
        &(if result[4] != 0 {
            enabled | MODULE
        } else {
            enabled & !MODULE
        })
        .to_le_bytes(),
    );
    let out = &mut parameters[OFFSET..OFFSET + BYTES];
    out[..4].copy_from_slice(&result[..4]);
    out[4..6].copy_from_slice(&result[8..10]);
    out[6..8].copy_from_slice(&result[6..8]);
    out[8..84].copy_from_slice(&result[10..86]);
    out[84..86].copy_from_slice(&result[90..92]);
    out[86..88].copy_from_slice(&result[88..90]);
    out[88..90].copy_from_slice(&result[86..88]);
    out[90..].copy_from_slice(&result[92..]);
}

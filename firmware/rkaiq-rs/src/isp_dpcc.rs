//! ISP32 DPCC selected-result branch in convert3aResultsToIspCfg (ELF 0x304c4).
//! Calibration selection and AdpccProcess are separate from this serializer.
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 192;
pub const OFFSET: usize = 0x7da;
pub const BYTES: usize = 186;

/// Serialize an explicitly supplied native-layout result. Skip its enable byte
/// and padding; preserve all unrelated parameter bytes and mask bits. Native
/// sets the module-enable bit for a nonzero result enable, but does not clear
/// an already-set bit for zero. This asymmetry is intentional.
pub fn apply(parameters: &mut [u8; PARAMETER_BYTES], result: &[u8; RESULT_BYTES]) {
    for offset in [0, 16] {
        let mask = u64::from_le_bytes(parameters[offset..offset + 8].try_into().unwrap());
        parameters[offset..offset + 8].copy_from_slice(&(mask | 1).to_le_bytes());
    }
    if result[2] != 0 {
        let mask = u64::from_le_bytes(parameters[8..16].try_into().unwrap());
        parameters[8..16].copy_from_slice(&(mask | 1).to_le_bytes());
    }
    let out = &mut parameters[OFFSET..OFFSET + BYTES];
    out[..2].copy_from_slice(&result[..2]);
    out[2..102].copy_from_slice(&result[3..103]);
    out[102..120].copy_from_slice(&result[104..122]);
    out[120..124].copy_from_slice(&result[124..128]);
    out[124..141].copy_from_slice(&result[128..145]);
    out[141..145].copy_from_slice(&result[146..150]);
    out[145..147].copy_from_slice(&(result[150] as u16).to_le_bytes());
    out[147..149].copy_from_slice(&(result[151] as u16).to_le_bytes());
    out[149..153].copy_from_slice(&result[152..156]);
    out[153..186].copy_from_slice(&result[156..189]);
}

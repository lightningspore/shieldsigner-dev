//! ISP32 LSC selected-result branch, result type 10, ELF 0x304c4 dispatcher.
use crate::isp32::PARAMETER_BYTES;
pub const RESULT_BYTES: usize = 2442;
pub const OFFSET: usize = 0x894;
pub const BYTES: usize = 2449;
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub enabled: bool,
}
/// Copy 289 SDK values per color plane, retaining the kernel's 290th entry.
/// When enabled, native clamps all 290 entries, including the retained one.
/// Disabled results still copy data/geometry and set sector_16x16 to one, while
/// clearing module enable/config-update bit 4. All unrelated bytes are retained.
pub fn apply(
    parameters: &mut [u8; PARAMETER_BYTES],
    result: &[u8; RESULT_BYTES],
    state: &mut State,
) {
    let enabled = result[0x988] != 0;
    for offset in [0, 8, 16] {
        let mask = u64::from_le_bytes(parameters[offset..offset + 8].try_into().unwrap());
        let mask = if offset == 0 || enabled {
            mask | (1 << 4)
        } else {
            mask & !(1 << 4)
        };
        parameters[offset..offset + 8].copy_from_slice(&mask.to_le_bytes());
    }
    let out = &mut parameters[OFFSET..OFFSET + BYTES];
    out[0] = 1;
    for channel in 0..4 {
        let start = 1 + channel * 580;
        out[start..start + 578].copy_from_slice(&result[channel * 578..(channel + 1) * 578]);
        if enabled {
            for entry in out[start..start + 580].chunks_exact_mut(2) {
                let value = u16::from_le_bytes(entry.try_into().unwrap()).min(8191);
                entry.copy_from_slice(&value.to_le_bytes());
            }
        }
    }
    out[2321..2449].copy_from_slice(&result[2312..2440]);
    state.enabled = enabled;
}

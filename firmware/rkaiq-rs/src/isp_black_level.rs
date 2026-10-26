//! Recovered ISP32 black-level parameter conversion, separate from calibration
//! selection and from live parameter queue submission.
use crate::{isp32::PARAMETER_BYTES, InvalidInput};
pub const OFFSET: usize = 0x7ae;
pub const BYTES: usize = 44;
pub const MODULE_MASK: u64 = 1 << 1;
#[derive(Clone, Copy, Debug)]
pub struct Configuration {
    pub enabled: bool,
    /// R, Gr, Gb, B signed channel offsets, copied without clipping.
    pub fixed: [i16; 4],
    pub stage1_enabled: bool,
    pub stage1: [i16; 4],
    /// The native input's optical-black enable flag is unused by this converter.
    pub optical_black_enabled: bool,
    pub optical_black_offset: i16,
    pub optical_black_predgain: f32,
    pub optical_black_maximum: i32,
}
fn put16(bytes: &mut [u8], offset: usize, value: u16) {
    bytes[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
}
/// Always updates the black-level masks/configuration and cache. Native
/// `enabled=false` leaves the existing module enable bit untouched; it does
/// not disable a previously enabled block. A nonfinite predgain is rejected
/// before any mutation rather than exposing the native conversion edge case.
pub fn apply(
    params: &mut [u8; PARAMETER_BYTES],
    cache: &mut [u8; BYTES],
    input: Configuration,
) -> Result<(), InvalidInput> {
    let gain = input.optical_black_predgain;
    if !gain.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let mut block = [0u8; BYTES];
    block[2] = input.stage1_enabled as u8;
    for i in 0..4 {
        put16(&mut block, 20 + i * 2, input.fixed[i] as u16);
        let stage1 = if gain == 0. {
            input.stage1[i] as u16
        } else {
            ((input.stage1[i] as f32 * gain) as i32).clamp(0, 32767) as u16
        };
        put16(&mut block, 28 + i * 2, stage1);
    }
    put16(
        &mut block,
        36,
        input.optical_black_offset.clamp(0, 511) as u16,
    );
    put16(
        &mut block,
        38,
        ((gain * 256.) as i32).clamp(0, 65535) as u16,
    );
    block[40..44].copy_from_slice(&input.optical_black_maximum.clamp(0, 0xfffff).to_le_bytes());
    for offset in [0usize, 16] {
        let mask = u64::from_le_bytes(params[offset..offset + 8].try_into().unwrap()) | MODULE_MASK;
        params[offset..offset + 8].copy_from_slice(&mask.to_le_bytes());
    }
    if input.enabled {
        let mask = u64::from_le_bytes(params[8..16].try_into().unwrap()) | MODULE_MASK;
        params[8..16].copy_from_slice(&mask.to_le_bytes());
    }
    params[OFFSET..OFFSET + BYTES].copy_from_slice(&block);
    *cache = block;
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    fn input() -> Configuration {
        Configuration {
            enabled: false,
            fixed: [-1, 64, 64, 32767],
            stage1_enabled: true,
            stage1: [-1, 1, 128, 32767],
            optical_black_enabled: false,
            optical_black_offset: -1,
            optical_black_predgain: 0.,
            optical_black_maximum: i32::MAX,
        }
    }
    #[test]
    fn zero_gain_preserves_signed_stage1_and_prior_enable() {
        let mut params = [0u8; PARAMETER_BYTES];
        params[8] = MODULE_MASK as u8;
        let mut cache = [0; BYTES];
        apply(&mut params, &mut cache, input()).unwrap();
        assert_eq!(&cache[28..30], &(-1i16).to_le_bytes());
        assert_eq!(params[8], MODULE_MASK as u8);
        assert_eq!(&cache[40..44], &0xfffffi32.to_le_bytes());
    }
    #[test]
    fn invalid_gain_leaves_record_and_cache_unchanged() {
        let mut params = [0x5a; PARAMETER_BYTES];
        let before = params;
        let mut cache = [0x33; BYTES];
        let mut config = input();
        config.optical_black_predgain = f32::NAN;
        assert_eq!(
            apply(&mut params, &mut cache, config),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(params, before);
        assert_eq!(cache, [0x33; BYTES]);
    }
}

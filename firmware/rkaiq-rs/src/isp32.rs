//! Pinned ISP32 parameter serialization. Not yet submitted to a live device.
//! Layout verified by cross-compiling the exact SDK kernel UAPI headers.
use crate::InvalidInput;
pub const PARAMETER_BYTES: usize = 11145;
pub const AWB_GAIN_OFFSET: usize = 0x1225;
pub const AWB_GAIN_BYTES: usize = 32;
pub const AWB_GAIN_MODULE_MASK: u64 = 1 << 5;
#[derive(Clone, Copy, Debug)]
pub enum ApplyPosition {
    Gain0,
    Gain1,
}
/// Initial apply-position selection in AwbPrepareV32 (ELF 0xc3a4c).
/// This is the prepare default; later automatic policy may reconfigure it.
pub fn awb_prepare_position(working_mode: i32) -> ApplyPosition {
    if working_mode == 0 {
        ApplyPosition::Gain1
    } else {
        ApplyPosition::Gain0
    }
}
#[derive(Clone, Copy, Debug)]
pub struct WhiteBalanceGain {
    pub red: f32,
    pub green_red: f32,
    pub green_blue: f32,
    pub blue: f32,
    pub position: ApplyPosition,
}
fn quantize(value: f32) -> Result<u16, InvalidInput> {
    if !value.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    // The binary narrows to u16 before its 11-bit clamp. Keep this checked API
    // below that wraparound regime; normal camera WB gains are well inside it.
    if !(0.0..=255.0).contains(&value) {
        return Err(InvalidInput::GainRange);
    }
    let raw = (((value * 256.0) as f64) + 0.5) as u32;
    Ok((raw as u16).min(2047))
}
/// Reconstruct convertAiqAwbGainToIsp32Params (ELF 0x2b590).
/// `update=false` is a complete no-op, not a request to disable AWB gains.
/// Uses explicit cached-record storage instead of the original C++ virtual-base
/// layout. Sets the AWB bit in all three update/enable masks and preserves all
/// unrelated fields. Both gain application positions are supported.
pub fn apply_awb_gain(
    params: &mut [u8; PARAMETER_BYTES],
    cached: &mut [u8; AWB_GAIN_BYTES],
    gain: WhiteBalanceGain,
    update: bool,
) -> Result<(), InvalidInput> {
    if !update {
        return Ok(());
    }
    let selected = [
        quantize(gain.green_blue)?,
        quantize(gain.green_red)?,
        quantize(gain.blue)?,
        quantize(gain.red)?,
    ];
    let mut words = [256u16; 16];
    match gain.position {
        ApplyPosition::Gain0 => {
            for i in 0..3 {
                words[4 + i * 4..8 + i * 4].copy_from_slice(&selected);
            }
        }
        ApplyPosition::Gain1 => words[..4].copy_from_slice(&selected),
    }
    for base in [0usize, 8, 16] {
        let mut value = u64::from_le_bytes(params[base..base + 8].try_into().unwrap());
        value |= AWB_GAIN_MODULE_MASK;
        params[base..base + 8].copy_from_slice(&value.to_le_bytes());
    }
    for (i, word) in words.iter().enumerate() {
        params[AWB_GAIN_OFFSET + i * 2..AWB_GAIN_OFFSET + i * 2 + 2]
            .copy_from_slice(&word.to_le_bytes());
    }
    cached.copy_from_slice(&params[AWB_GAIN_OFFSET..AWB_GAIN_OFFSET + AWB_GAIN_BYTES]);
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn update_preserves_unrelated_bytes() {
        let mut params = [0x5a; PARAMETER_BYTES];
        let original = params;
        let mut cached = [0; AWB_GAIN_BYTES];
        apply_awb_gain(
            &mut params,
            &mut cached,
            WhiteBalanceGain {
                red: 2.,
                green_red: 1.,
                green_blue: 1.,
                blue: 3.,
                position: ApplyPosition::Gain0,
            },
            true,
        )
        .unwrap();
        assert_eq!(&params[24..AWB_GAIN_OFFSET], &original[24..AWB_GAIN_OFFSET]);
        assert_eq!(
            &params[AWB_GAIN_OFFSET + AWB_GAIN_BYTES..],
            &original[AWB_GAIN_OFFSET + AWB_GAIN_BYTES..]
        );
        assert_eq!(u16::from_le_bytes([cached[14], cached[15]]), 512);
    }
    #[test]
    fn no_update_does_not_read_invalid_gains() {
        let mut params = [0x5a; PARAMETER_BYTES];
        let mut cache = [0x5a; 32];
        let original = params;
        apply_awb_gain(
            &mut params,
            &mut cache,
            WhiteBalanceGain {
                red: f32::NAN,
                green_red: 0.,
                green_blue: 0.,
                blue: 0.,
                position: ApplyPosition::Gain1,
            },
            false,
        )
        .unwrap();
        assert_eq!(params, original);
        assert_eq!(cache, [0x5a; 32]);
    }
}

/// Exposure digital gains: the binary uses three slots for any HDR mode.
#[derive(Clone, Copy, Debug)]
pub enum ExposureDigitalGain {
    Linear(f32),
    Hdr([f32; 3]),
}
/// Reconstruct convertAiqExpIspDgainToIsp32Params (ELF 0x2d860).
/// Scale the cached AWB-bank-0 gains, leaving bank 1 and the cache unchanged.
/// Only the AWB configuration-update mask is set, not either enable mask.
/// Finite linear gains <= 1 are a no-op; HDR gains are clamped to >= 1.
/// A unity request does not restore a previously scaled output buffer: callers
/// must supply the appropriate unscaled parameter state when rebuilding it.
pub fn apply_exposure_digital_gain(
    params: &mut [u8; PARAMETER_BYTES],
    cached: &[u8; AWB_GAIN_BYTES],
    gain: ExposureDigitalGain,
) -> Result<(), InvalidInput> {
    let gains = match gain {
        ExposureDigitalGain::Linear(value) => {
            if !value.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            if value <= 1.0 {
                return Ok(());
            }
            [value; 3]
        }
        ExposureDigitalGain::Hdr(values) => {
            if values.iter().any(|v| !v.is_finite()) {
                return Err(InvalidInput::NonFinite);
            }
            let values = values.map(|v| v.max(1.0));
            if values.iter().all(|v| *v == 1.0) {
                return Ok(());
            }
            values
        }
    };
    for (group, gain) in gains.iter().enumerate() {
        for channel in 0..4 {
            let offset = 8 + group * 8 + channel * 2;
            let base = u16::from_le_bytes(cached[offset..offset + 2].try_into().unwrap());
            let rounded = ((base as f32 * gain) as f64) + 0.5;
            let value = rounded.min(65535.0) as u16;
            params[AWB_GAIN_OFFSET + offset..AWB_GAIN_OFFSET + offset + 2]
                .copy_from_slice(&value.to_le_bytes());
        }
    }
    let value = u64::from_le_bytes(params[16..24].try_into().unwrap()) | AWB_GAIN_MODULE_MASK;
    params[16..24].copy_from_slice(&value.to_le_bytes());
    Ok(())
}

#[cfg(test)]
mod exposure_tests {
    use super::*;
    #[test]
    fn hdr_scales_from_cache_without_accumulating_and_preserves_enable_masks() {
        let mut params = [0xa5; PARAMETER_BYTES];
        let mut cache = [0; 32];
        for pair in cache.chunks_exact_mut(2) {
            pair.copy_from_slice(&1000u16.to_le_bytes());
        }
        let original = params;
        let gain = ExposureDigitalGain::Hdr([0.5, 2., 100.]);
        apply_exposure_digital_gain(&mut params, &cache, gain).unwrap();
        for (group, expected) in [1000u16, 2000, 65535].iter().enumerate() {
            for channel in 0..4 {
                let offset = AWB_GAIN_OFFSET + 8 + group * 8 + channel * 2;
                assert_eq!(
                    u16::from_le_bytes(params[offset..offset + 2].try_into().unwrap()),
                    *expected
                );
            }
        }
        assert_eq!(&params[..16], &original[..16]);
        assert_eq!(
            &params[24..AWB_GAIN_OFFSET + 8],
            &original[24..AWB_GAIN_OFFSET + 8]
        );
        assert_eq!(
            &params[AWB_GAIN_OFFSET + 32..],
            &original[AWB_GAIN_OFFSET + 32..]
        );
        let once = params;
        apply_exposure_digital_gain(&mut params, &cache, gain).unwrap();
        assert_eq!(params, once);
    }
    #[test]
    fn unity_is_noop_and_invalid_gain_is_atomic() {
        let mut params = [0xa5; PARAMETER_BYTES];
        let original = params;
        let cache = [0; 32];
        apply_exposure_digital_gain(&mut params, &cache, ExposureDigitalGain::Linear(1.)).unwrap();
        assert_eq!(params, original);
        assert!(apply_exposure_digital_gain(
            &mut params,
            &cache,
            ExposureDigitalGain::Hdr([2., f32::NAN, 1.])
        )
        .is_err());
        assert_eq!(params, original);
    }
}

/// Apply an ordered WB/exposure result pair, as in the native ISP result list.
/// `white_balance=None` preserves the previous cache and current output bytes.
/// `exposure=None` leaves exposure scaling untouched. This function does not
/// manage parameter-pool reuse, frame IDs, or decide whether WB is published.
/// Validate both inputs before changing the output or the unscaled cache.
pub fn apply_gain_results(
    params: &mut [u8; PARAMETER_BYTES],
    cached: &mut [u8; AWB_GAIN_BYTES],
    white_balance: Option<WhiteBalanceGain>,
    exposure: Option<ExposureDigitalGain>,
) -> Result<(), InvalidInput> {
    if let Some(gain) = white_balance {
        for value in [gain.red, gain.green_red, gain.green_blue, gain.blue] {
            quantize(value)?;
        }
    }
    if let Some(gain) = exposure {
        let finite = match gain {
            ExposureDigitalGain::Linear(v) => v.is_finite(),
            ExposureDigitalGain::Hdr(v) => v.iter().all(|v| v.is_finite()),
        };
        if !finite {
            return Err(InvalidInput::NonFinite);
        }
    }
    if let Some(gain) = white_balance {
        apply_awb_gain(params, cached, gain, true)?;
    }
    if let Some(gain) = exposure {
        apply_exposure_digital_gain(params, cached, gain)?;
    }
    Ok(())
}

#[cfg(test)]
mod ordered_gain_tests {
    use super::*;
    #[test]
    fn invalid_exposure_cannot_partially_publish_white_balance() {
        let mut params = [0x5a; PARAMETER_BYTES];
        let mut cache = [0x3c; AWB_GAIN_BYTES];
        let original = params;
        let original_cache = cache;
        assert_eq!(
            apply_gain_results(
                &mut params,
                &mut cache,
                Some(WhiteBalanceGain {
                    red: 2.,
                    green_red: 1.,
                    green_blue: 1.,
                    blue: 3.,
                    position: ApplyPosition::Gain1,
                }),
                Some(ExposureDigitalGain::Hdr([2., f32::NAN, 1.]))
            ),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(params, original);
        assert_eq!(cache, original_cache);
    }
}

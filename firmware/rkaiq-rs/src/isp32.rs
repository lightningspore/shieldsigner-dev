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

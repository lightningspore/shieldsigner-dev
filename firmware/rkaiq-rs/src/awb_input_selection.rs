//! AWB startup source selection and native 12-bit/shift flags.
use crate::{isp_awb_measurement::INPUT_BYTES, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub enum Source {
    RawFixed,
    RawAuto,
    BayerNr,
    Drc,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Flags {
    pub input_12bit: bool,
    pub shift_to_12bit: bool,
}
/// calcInputBitIs12Bit (ELF 0xc1214) and calcInputRightShift212Bit
/// (0xc124e). Keep their distinct ordered predicates, including NaN behavior.
pub fn flags(selector: u8, working_mode: u32, blc_pre_gain: Option<f32>) -> Flags {
    let input_12bit = if !blc_pre_gain.is_some_and(|g| g > 1.) {
        selector != 3 || working_mode == 0
    } else {
        selector != 3
    };
    let shift_to_12bit =
        selector == 3 && (blc_pre_gain.is_some_and(|g| g > 1.) || working_mode != 0);
    Flags {
        input_12bit,
        shift_to_12bit,
    }
}
/// Checked valid-mode startup path from AwbPrepareV32. RawAuto uses the
/// configured startup frame; later exposure-dependent automatic selection is
/// a separate reconfiguration decision. Other record bytes remain untouched.
pub fn configure(
    record: &mut [u8; INPUT_BYTES],
    source: Source,
    frame: u8,
    working_mode: u32,
    blc_pre_gain: Option<f32>,
) -> Result<(), InvalidInput> {
    if working_mode != 0 && working_mode < 16 {
        return Err(InvalidInput::Length);
    }
    let selector = match source {
        Source::BayerNr => 3,
        Source::Drc => 4,
        Source::RawFixed | Source::RawAuto => {
            if working_mode == 0 {
                0
            } else {
                let count = if working_mode < 32 { 2 } else { 3 };
                if frame >= count {
                    return Err(InvalidInput::Length);
                }
                frame
            }
        }
    };
    let bits = flags(selector, working_mode, blc_pre_gain);
    record[0x3e] = selector;
    record[2] = u8::from(bits.input_12bit);
    record[8] = u8::from(bits.shift_to_12bit);
    if selector == 4 {
        record[1] = 1;
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn separate_native_predicates_and_invalid_frame_preservation() {
        assert_eq!(
            flags(3, 0, Some(f32::NAN)),
            Flags {
                input_12bit: true,
                shift_to_12bit: false
            }
        );
        assert_eq!(
            flags(3, 0, Some(1.)),
            Flags {
                input_12bit: true,
                shift_to_12bit: false
            }
        );
        let mut record = [0xa5; INPUT_BYTES];
        assert!(configure(&mut record, Source::RawFixed, 2, 16, None).is_err());
        assert_eq!(record, [0xa5; INPUT_BYTES]);
    }
}

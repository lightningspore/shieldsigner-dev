//! ISP32 CCM register conversion (ELF 0x2d0cc), separate from calibration policy.
use crate::{isp32::PARAMETER_BYTES, InvalidInput};
pub const RESULT_BYTES: usize = 156;
pub const OFFSET: usize = 0x12bb;
pub const BYTES: usize = 79;

fn float(input: &[u8; RESULT_BYTES], offset: usize) -> f32 {
    f32::from_le_bytes(input[offset..offset + 4].try_into().unwrap())
}
fn signed(value: f32) -> u16 {
    let rounded = if value > 0. { value + 0.5 } else { value - 0.5 };
    (rounded as i32) as u16
}
fn positive(value: f32) -> u16 {
    if value > 0. {
        (value as i32) as u16
    } else {
        0
    }
}
/// Convert the explicit SDK-layout result, preserving native narrowing and mask
/// behavior. Finite bounded input is required; invalid input changes no bytes.
/// This does not choose a calibrated matrix or enable a live CCM controller.
pub fn apply(
    parameters: &mut [u8; PARAMETER_BYTES],
    input: &[u8; RESULT_BYTES],
) -> Result<(), InvalidInput> {
    // Native float-to-integer behavior outside this bounded domain is excluded.
    for offset in (8..=144).step_by(4).chain(core::iter::once(152)) {
        let value = float(input, offset);
        if !value.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if value.abs() > 1_000_000. {
            return Err(InvalidInput::GainRange);
        }
    }
    let out = &mut parameters[OFFSET..OFFSET + BYTES];
    out[0] = input[4] ^ 1;
    out[1] = input[2];
    out[2] = input[1];
    out[3] = positive(float(input, 132)) as u8;
    out[4] = positive(float(input, 128)) as u8;
    let put = |out: &mut [u8], index: usize, value: u16| {
        out[index..index + 2].copy_from_slice(&value.to_le_bytes());
    };
    for row in 0..3 {
        for col in 0..3 {
            let v = float(input, 8 + (row * 3 + col) * 4) - if row == col { 1. } else { 0. };
            put(out, 5 + row * 8 + col * 2, signed(v * 128.));
        }
        put(out, 11 + row * 8, signed(float(input, 44 + row * 4)));
    }
    for index in 0..3 {
        put(out, 29 + index * 2, positive(float(input, 136 + index * 4)));
    }
    for index in 0..18 {
        put(out, 35 + index * 2, positive(float(input, 56 + index * 4)));
    }
    for index in 0..3 {
        put(out, 71 + index * 2, u16::from(input[148 + index]));
    }
    put(out, 77, positive(float(input, 152) * 1024.));
    for offset in [0, 16] {
        let mask = u64::from_le_bytes(parameters[offset..offset + 8].try_into().unwrap());
        parameters[offset..offset + 8].copy_from_slice(&(mask | (1 << 8)).to_le_bytes());
    }
    if input[0] != 0 {
        let mask = u64::from_le_bytes(parameters[8..16].try_into().unwrap());
        parameters[8..16].copy_from_slice(&(mask | (1 << 8)).to_le_bytes());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_input_preserves_complete_parameter_buffer() {
        let mut parameters = [0xa5; PARAMETER_BYTES];
        let before = parameters;
        for value in [f32::NAN, f32::INFINITY, 1_000_001.] {
            let mut result = [0u8; RESULT_BYTES];
            result[152..156].copy_from_slice(&value.to_le_bytes());
            assert!(apply(&mut parameters, &result).is_err());
            assert_eq!(parameters, before);
        }
    }
}

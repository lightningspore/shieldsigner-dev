//! Native AWB RGB-to-XY and rotated-YUV measurement transforms.
use crate::InvalidInput;
fn validate(values: &[f32]) -> Result<(), InvalidInput> {
    if values.iter().all(|v| v.is_finite()) {
        Ok(())
    } else {
        Err(InvalidInput::NonFinite)
    }
}
fn signed(value: f32, scale: f32) -> Result<i16, InvalidInput> {
    let n = value * scale;
    if !n.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    Ok((if value > 0. { n + 0.5 } else { n - 0.5 }) as i32 as i16)
}
/// JsonXyParaFixed1, ELF 0xc8210. Native U0012 masks to 12 bits;
/// it does not saturate a weight of 1.0 to the largest representable fraction.
pub fn xy(
    weights: &[f32; 3],
    rotation: &[f32; 9],
    output: &mut [u8; 24],
) -> Result<(), InvalidInput> {
    validate(weights)?;
    validate(rotation)?;
    let mut next = [0; 24];
    for i in 0..3 {
        let n = weights[i] * 4096. + 0.5;
        if !n.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let value = if n > 0. {
            (n as i32 as u32 & 0xfff) as u16
        } else {
            0
        };
        next[i * 2..i * 2 + 2].copy_from_slice(&value.to_le_bytes());
    }
    for i in 0..9 {
        next[6 + i * 2..8 + i * 2].copy_from_slice(&signed(rotation[i], 4096.)?.to_le_bytes());
    }
    *output = next;
    Ok(())
}
/// JsonRtYuvParaFixed1, ELF 0xc9050. The last matrix row is not consumed.
pub fn rotated_yuv(matrix: &[f32; 16], output: &mut [u8; 24]) -> Result<(), InvalidInput> {
    validate(&matrix[..12])?;
    let mut next = [0; 24];
    for i in 0..12 {
        let scale = if i % 4 == 3 { 16. } else { 512. };
        next[i * 2..i * 2 + 2].copy_from_slice(&signed(matrix[i], scale)?.to_le_bytes());
    }
    *output = next;
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn late_invalid_values_are_atomic_and_unused_row_is_not_read() {
        let mut output = [0xa5; 24];
        let mut rotation = [0.; 9];
        rotation[8] = f32::NAN;
        assert!(xy(&[0.3; 3], &rotation, &mut output).is_err());
        assert_eq!(output, [0xa5; 24]);
        let mut matrix = [0.; 16];
        matrix[12..].fill(f32::NAN);
        assert!(rotated_yuv(&matrix, &mut output).is_ok());
        assert_eq!(output, [0; 24]);
        matrix[11] = f32::MAX;
        let before = output;
        assert!(rotated_yuv(&matrix, &mut output).is_err());
        assert_eq!(output, before);
    }
}

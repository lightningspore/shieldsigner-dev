//! Native calibrated UV/XY/rotated-YUV region quantization for ISP32 AWB.
use crate::InvalidInput;
fn finite(values: &[f32]) -> Result<(), InvalidInput> {
    if values.iter().all(|x| x.is_finite()) {
        Ok(())
    } else {
        Err(InvalidInput::NonFinite)
    }
}
/// JsonXyParaFixed3, ELF 0xc8254. The two small-region ranges are untouched.
pub fn xy(values: &[f32; 8], output: &mut [u8; 48]) -> Result<(), InvalidInput> {
    finite(values)?;
    let mut next = *output;
    for (i, v) in values.iter().enumerate() {
        let scaled = *v * 1024.;
        if !scaled.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let rounded = if scaled > 0. {
            scaled + 0.5
        } else {
            scaled - 0.5
        };
        let value = (rounded as i32 as i16) as i32;
        next[i * 4..i * 4 + 4].copy_from_slice(&value.to_le_bytes());
    }
    *output = next;
    Ok(())
}
pub struct RotatedYuv {
    pub u: [f32; 6],
    pub threshold: [f32; 6],
    pub line: [f32; 6],
    pub distance: u8,
}
fn positive_q4(value: f32) -> u16 {
    let n = value * 16. + 0.5;
    if n > 0. {
        n as i32 as u16
    } else {
        0
    }
}
/// JsonRtYuvParaFixed2, ELF 0xc90d4. The final padding byte is untouched.
pub fn rotated_yuv(input: &RotatedYuv, output: &mut [u8; 32]) -> Result<(), InvalidInput> {
    finite(&input.u)?;
    finite(&input.threshold)?;
    finite(&input.line)?;
    if input
        .threshold
        .iter()
        .chain(input.line.iter())
        .any(|x| !(*x * 16. + 0.5).is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    let mut next = *output;
    for i in 0..6 {
        next[i] = if input.u[i] > 0. {
            input.u[i] as i32 as u8
        } else {
            0
        };
        next[6 + i * 2..8 + i * 2].copy_from_slice(&positive_q4(input.threshold[i]).to_le_bytes());
    }
    for i in 0..3 {
        let a = positive_q4(input.line[i]);
        let b = positive_q4(input.line[i + 3]);
        next[18 + i * 2..20 + i * 2].copy_from_slice(&a.to_le_bytes());
        next[24 + i * 2..26 + i * 2].copy_from_slice(&b.wrapping_sub(a).to_le_bytes());
    }
    next[30] = input.distance;
    *output = next;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_values_preserve_both_record_types() {
        let mut xy_record = [0xa5; 48];
        let mut values = [1.; 8];
        values[7] = f32::MAX;
        assert!(xy(&values, &mut xy_record).is_err());
        assert_eq!(xy_record, [0xa5; 48]);
        let mut rt_record = [0xa5; 32];
        let mut input = RotatedYuv {
            u: [1.; 6],
            threshold: [1.; 6],
            line: [1.; 6],
            distance: 3,
        };
        input.line[5] = f32::NAN;
        assert!(rotated_yuv(&input, &mut rt_record).is_err());
        assert_eq!(rt_record, [0xa5; 32]);
    }
}

/// Inline UV polygon conversion in UpdateAwbCalibV2Para, ELF 0xc240e–0xc24d2.
/// Native promotes Q4 rounding and the final signed slope rounding to f64.
/// A horizontal edge uses the native 0x3ffff inverse-slope sentinel.
pub fn uv(u: &[f32; 4], v: &[f32; 4], output: &mut [u8; 36]) -> Result<(), InvalidInput> {
    finite(u)?;
    finite(v)?;
    let mut pu = [0u16; 5];
    let mut pv = [0u16; 5];
    for i in 0..4 {
        let x = u[i] * 16.;
        let y = v[i] * 16.;
        if !x.is_finite() || !y.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        pu[i] = ((x as f64 + 0.5) as u32) as u16;
        pv[i] = ((y as f64 + 0.5) as u32) as u16;
    }
    pu[4] = pu[0];
    pv[4] = pv[0];
    let mut next = [0; 36];
    for i in 0..5 {
        next[i * 2..i * 2 + 2].copy_from_slice(&pu[i].to_le_bytes());
        next[10 + i * 2..12 + i * 2].copy_from_slice(&pv[i].to_le_bytes());
    }
    for i in 1..5 {
        let dx = pu[i] as i32 - pu[i - 1] as i32;
        let dy = pv[i] as i32 - pv[i - 1] as i32;
        let inverse = if dy == 0 {
            0x3ffff
        } else {
            let ratio = dx as f32 / dy as f32;
            let scaled = (ratio * 1024.) as f64;
            (if ratio > 0. {
                scaled + 0.5
            } else {
                scaled - 0.5
            }) as i32
        };
        next[20 + (i - 1) * 4..24 + (i - 1) * 4].copy_from_slice(&inverse.to_le_bytes());
    }
    *output = next;
    Ok(())
}

#[cfg(test)]
mod uv_tests {
    use super::*;
    #[test]
    fn horizontal_edges_close_polygon_and_invalid_input_is_atomic() {
        let mut output = [0xa5; 36];
        uv(&[0., 1., 2., 3.], &[1.; 4], &mut output).unwrap();
        assert_eq!(&output[..2], &output[8..10]);
        assert_eq!(&output[10..12], &output[18..20]);
        for slope in output[20..].chunks_exact(4) {
            assert_eq!(i32::from_le_bytes(slope.try_into().unwrap()), 0x3ffff);
        }
        let before = output;
        assert!(uv(&[0., 1., 2., f32::MAX], &[1.; 4], &mut output).is_err());
        assert_eq!(output, before);
    }
}

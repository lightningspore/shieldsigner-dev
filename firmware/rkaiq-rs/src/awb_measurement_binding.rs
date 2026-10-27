//! Post-initialization AWB measurement binding for the live linear BayerNR,
//! Gain1 path. Other input/position/OTP branches remain separate.
use crate::{isp_awb_measurement::INPUT_BYTES, isp_black_level::Configuration, InvalidInput};
pub struct Input {
    pub black_level: Option<Configuration>,
    /// AWB-specific offsets already selected at ISO × optical-black pre-gain.
    pub awb_offsets: [f32; 4],
    pub digital_gain: f32,
    pub remosaic_inverse: Option<[f32; 4]>,
    pub software_pre_gain: Option<[f32; 4]>,
}
fn q8(value: f32) -> Result<u16, InvalidInput> {
    if !value.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    Ok(((value as f64 + 0.5) as u32) as u16)
}
pub fn bind_gain1_linear(
    record: &mut [u8; INPUT_BYTES],
    input: &Input,
) -> Result<(), InvalidInput> {
    if record[0x3e] != 3 {
        return Err(InvalidInput::UnsupportedRegion);
    }
    if !input.digital_gain.is_finite() || input.awb_offsets.iter().any(|x| !x.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    let mut next = *record;
    let mut inverse = [256; 3];
    if let Some(gains) = input.remosaic_inverse {
        for (i, j) in [0, 1, 3].iter().enumerate() {
            if !gains[*j].is_finite() || (gains[*j] as f64) < 1e-5 {
                return Err(InvalidInput::GainRange);
            }
            inverse[i] = q8(256. / gains[*j])?;
        }
    }
    let software = input.software_pre_gain.unwrap_or([1.; 4]);
    if let Some(gains) = input.software_pre_gain {
        if gains.iter().any(|x| !x.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        for (i, j) in [0, 1, 3].iter().enumerate() {
            if (gains[*j] as f64) < 1e-5 {
                return Err(InvalidInput::GainRange);
            }
            inverse[i] = q8(gains[*j] * 256.)?;
        }
    }
    for (i, n) in inverse.iter().enumerate() {
        next[0x5a + i * 2..0x5c + i * 2].copy_from_slice(&n.to_le_bytes());
    }
    for (i, n) in software.iter().enumerate() {
        next[0x4a4 + i * 4..0x4a8 + i * 4].copy_from_slice(&n.to_le_bytes());
    }
    let pre = input.black_level.map_or(1., |b| b.optical_black_predgain);
    if !pre.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let pre = pre.max(1.);
    let offset = input.black_level.map_or(0, |b| b.optical_black_offset);
    let mut blc = [0i32; 4];
    for i in 0..4 {
        let stage1 = input
            .black_level
            .filter(|b| b.stage1_enabled)
            .map_or(0, |b| b.stage1[i]);
        let value = libm::fmaf(input.digital_gain, input.awb_offsets[i], stage1 as f32) * pre;
        if !value.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        blc[i] = (value as f64 + 0.5) as i32;
    }
    next[0xc] = 1;
    for (i, n) in blc.iter().enumerate() {
        next[0x10 + i * 4..0x14 + i * 4].copy_from_slice(&n.to_le_bytes());
    }
    let mut maximum = 0i16;
    for i in 0..4 {
        let raw = input.black_level.filter(|b| b.enabled).map_or(0i16, |b| {
            libm::fmaf(pre, b.fixed[i] as f32, -(offset as f32)) as i32 as i16
        });
        let value = raw.max(0).wrapping_add(blc[i] as i16).wrapping_add(offset);
        maximum = maximum.max(value);
    }
    let threshold = libm::fmaf(pre, 254., -((maximum as i32 >> 4) as f32));
    if !threshold.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    next[0x60..0x64].copy_from_slice(&(threshold as i32).to_le_bytes());
    *record = next;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn late_black_level_overflow_preserves_all_measurement_metadata() {
        let mut record = [0xa5; INPUT_BYTES];
        record[0x3e] = 3;
        let before = record;
        let input = Input {
            black_level: None,
            awb_offsets: [f32::MAX; 4],
            digital_gain: 2.,
            remosaic_inverse: None,
            software_pre_gain: Some([1.25; 4]),
        };
        assert!(bind_gain1_linear(&mut record, &input).is_err());
        assert_eq!(record, before);
    }
}

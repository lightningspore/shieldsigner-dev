//! Selected-result branches of ISP32 convert3aResultsToIspCfg (ELF 0x304c4).
//! These serialize selected settings; automatic calibration selection is separate.
use crate::{isp32::PARAMETER_BYTES, InvalidInput};

fn masks(params: &mut [u8; PARAMETER_BYTES], bit: u32, enabled: bool, clear_cfg: bool) {
    let mask = 1u64 << bit;
    for offset in [0, 8, 16] {
        let old = u64::from_le_bytes(params[offset..offset + 8].try_into().unwrap());
        let value = match offset {
            0 => old | mask,
            8 if !enabled => old & !mask,
            16 if clear_cfg => old & !mask,
            16 if !enabled => old,
            _ => old | mask,
        };
        params[offset..offset + 8].copy_from_slice(&value.to_le_bytes());
    }
}

pub fn gamma(
    params: &mut [u8; PARAMETER_BYTES],
    enabled: bool,
    mode: u8,
    dense: bool,
    offset: u16,
    curve: &[u16; 49],
) {
    masks(params, 9, enabled, false);
    if !enabled {
        return;
    }
    let block = &mut params[0x130a..0x1370];
    block[0] = mode;
    block[1] = dense as u8;
    block[2..4].copy_from_slice(&offset.to_le_bytes());
    for (i, value) in curve.iter().enumerate() {
        block[4 + i * 2..6 + i * 2].copy_from_slice(&value.to_le_bytes());
    }
}

pub fn csm(
    params: &mut [u8; PARAMETER_BYTES],
    mode: i32,
    full_range: u8,
    y_offset: u8,
    c_offset: u8,
    coefficients: &[f32; 9],
) -> Result<(), InvalidInput> {
    let enabled = mode == 1 || mode == 2;
    if enabled
        && coefficients
            .iter()
            .any(|v| !v.is_finite() || v.abs() > 255.)
    {
        return Err(InvalidInput::GainRange);
    }
    masks(params, 43, enabled, !enabled);
    if !enabled {
        return Ok(());
    }
    let block = &mut params[0x2b54..0x2b7d];
    block[0] = full_range;
    block[1..3].copy_from_slice(&(y_offset as u16).to_le_bytes());
    block[3..5].copy_from_slice(&(c_offset as u16).to_le_bytes());
    for (i, value) in coefficients.iter().enumerate() {
        let scaled = value * 128.;
        let rounded = (scaled as f64 + if *value > 0. { 0.5 } else { -0.5 }) as i32;
        block[5 + i * 4..9 + i * 4].copy_from_slice(&((rounded as i16) as i32).to_le_bytes());
    }
    Ok(())
}

pub fn cgc(params: &mut [u8; PARAMETER_BYTES], mode: i32, ratio: u8, limit: u8) {
    let enabled = mode == 1 || mode == 2;
    masks(params, 44, enabled, !enabled);
    if enabled {
        params[0x2b7d..0x2b7f].copy_from_slice(&[limit, ratio]);
    }
}

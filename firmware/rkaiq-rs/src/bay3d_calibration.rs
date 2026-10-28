//! Native Temporal Bayer NR calibration preparation.
extern crate alloc;
use crate::bay3d_selection::TABLE_BYTES;
use alloc::{format, string::String};
use serde_json::Value;
fn list<'a>(v: &'a Value, key: &str) -> Result<&'a [Value], String> {
    let a = v[key]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 64)
        .ok_or_else(|| format!("Invalid BAY3D {key} array"))?;
    if let Some(n) = v.get(format!("{key}_len")) {
        if n.as_u64() != Some(a.len() as u64) {
            return Err(format!("BAY3D {key} count mismatch"));
        }
    }
    Ok(a)
}
fn flag(v: &Value) -> Result<u8, String> {
    if let Some(b) = v.as_bool() {
        return Ok(u8::from(b));
    };
    v.as_u64()
        .filter(|n| *n <= 1)
        .map(|n| n as u8)
        .ok_or_else(|| "Expected BAY3D boolean".into())
}
fn float(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|n| n as f32)
        .filter(|n| n.is_finite())
        .ok_or_else(|| "Expected finite BAY3D number".into())
}
fn signed(v: &Value) -> Result<i32, String> {
    v.as_i64()
        .and_then(|n| i32::try_from(n).ok())
        .ok_or_else(|| "Expected BAY3D i32".into())
}
fn unsigned(v: &Value, max: u64) -> Result<u32, String> {
    v.as_u64()
        .filter(|n| *n <= max)
        .map(|n| n as u32)
        .ok_or_else(|| "Expected bounded BAY3D unsigned integer".into())
}
fn put_float(b: &mut [u8], p: usize, v: &Value) -> Result<(), String> {
    b[p..p + 4].copy_from_slice(&float(v)?.to_le_bytes());
    Ok(())
}
fn put_u16(b: &mut [u8], p: usize, v: &Value) -> Result<(), String> {
    b[p..p + 2].copy_from_slice(&(unsigned(v, 65535)? as u16).to_le_bytes());
    Ok(())
}
fn sixteen<'a>(v: &'a Value) -> Result<&'a [Value], String> {
    v.as_array()
        .filter(|a| a.len() == 16)
        .map(|a| a.as_slice())
        .ok_or_else(|| "BAY3D requires sixteen curve entries".into())
}
fn setting<'a>(v: &'a Value, noise: &str) -> Result<(&'a Value, usize), String> {
    let settings = list(v, "Setting")?;
    for row in settings {
        if row["SNR_Mode"]
            .as_str()
            .filter(|s| s.is_ascii() && !s.as_bytes().contains(&0))
            .is_none()
        {
            return Err("Invalid BAY3D SNR mode name".into());
        }
    }
    let index = settings
        .iter()
        .position(|s| s["SNR_Mode"].as_str().unwrap().starts_with(noise))
        .unwrap_or(0);
    Ok((&settings[index], index))
}

pub fn prepare(
    calibration: &Value,
    noise: &str,
    output: &mut [u8; TABLE_BYTES],
) -> Result<[usize; 2], String> {
    if !noise.is_ascii() || noise.len() > 63 || noise.as_bytes().contains(&0) {
        return Err("Invalid BAY3D SNR name".into());
    }
    let (cal, ci) = setting(&calibration["CalibPara"], noise)?;
    let (tune, ti) = setting(&calibration["TuningPara"], noise)?;
    let mut next = *output;
    next[0] = flag(&calibration["TuningPara"]["enable"])?;
    for (i, row) in list(cal, "Calib_ISO")?.iter().take(13).enumerate() {
        put_float(&mut next, 4 + i * 4, &row["iso"])?;
        let p = 56 + i * 400;
        for (key, offset) in [
            ("lumapoint", 4),
            ("sigma", 68),
            ("lumapoint2", 132),
            ("lo_sigma", 196),
            ("hi_sigma", 260),
        ] {
            for (j, v) in sixteen(&row[key])?.iter().enumerate() {
                next[p + offset + j * 4..p + offset + j * 4 + 4]
                    .copy_from_slice(&signed(v)?.to_le_bytes());
            }
        }
    }
    for (i, row) in list(tune, "Tuning_ISO")?.iter().take(13).enumerate() {
        put_float(&mut next, 4 + i * 4, &row["iso"])?;
        let p = 56 + i * 400;
        for (key, offset, max) in [("thumbds_w", 324, 255), ("thumbds_h", 325, 255)] {
            next[p + offset] = unsigned(&calibration["TuningPara"][key], max)? as u8;
        }
        for (key, offset) in [("lo_enable", 326), ("trans_en", 333)] {
            next[p + offset] = flag(&calibration["TuningPara"][key])?;
        }
        for (key, offset) in [
            ("hi_enable", 327),
            ("lo_med_en", 328),
            ("lo_gsbay_en", 329),
            ("lo_gslum_en", 330),
            ("hi_med_en", 331),
            ("hi_gslum_en", 332),
            ("wgt_use_mode", 334),
            ("wgt_mge_mode", 335),
            ("hi_guass", 336),
            ("kl_guass", 337),
            ("global_pk_en", 338),
        ] {
            next[p + offset] = flag(&row[key])?;
        }
        for (key, offset) in [("global_pksq", 340), ("hidif_th", 364)] {
            next[p + offset..p + offset + 4].copy_from_slice(&signed(&row[key])?.to_le_bytes());
        }
        for (key, offset) in [
            ("lo_filter_strength", 344),
            ("hi_filter_strength", 348),
            ("soft_threshold_ratio", 352),
            ("lo_clipwgt", 356),
            ("hi_wgt_comp", 360),
            ("lo_filter_rat0", 368),
            ("hi_filter_rat0", 380),
            ("hi_filter_rat1", 388),
        ] {
            put_float(&mut next, p + offset, &row[key])?;
        }
        for (key, offset) in [
            ("lo_filter_thed0", 372),
            ("hi_filter_thed0", 384),
            ("hi_filter_thed1", 392),
        ] {
            put_u16(&mut next, p + offset, &row[key])?;
        }
        for (key, offset) in [
            ("hi_filter_abs_ctrl", 374),
            ("hi_filter_filt_bay", 375),
            ("hi_filter_filt_avg", 376),
            ("hi_filter_filt_mode", 377),
            ("guass_guide_coeff0", 394),
            ("guass_guide_coeff1", 395),
            ("guass_guide_coeff2", 396),
            ("guass_guide_coeff3", 397),
        ] {
            next[p + offset] = unsigned(&row[key], 255)? as u8;
        }
    }
    *output = next;
    Ok([ci, ti])
}

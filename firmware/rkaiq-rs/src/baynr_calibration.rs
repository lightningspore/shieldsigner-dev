//! Native Bayer spatial NR setting lookup and calibration/tuning table merge.
extern crate alloc;
use crate::baynr_selection::TABLE_BYTES;
use alloc::{format, string::String};
use serde_json::Value;
fn list<'a>(v: &'a Value, key: &str) -> Result<&'a [Value], String> {
    let a = v[key]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 64)
        .ok_or_else(|| format!("Invalid BAYNR {key} array"))?;
    if let Some(n) = v.get(format!("{key}_len")) {
        if n.as_u64() != Some(a.len() as u64) {
            return Err(format!("BAYNR {key} count mismatch"));
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
        .ok_or_else(|| "Expected BAYNR boolean".into())
}
fn float(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|n| n as f32)
        .filter(|n| n.is_finite())
        .ok_or_else(|| "Expected finite BAYNR number".into())
}
fn signed(v: &Value) -> Result<i32, String> {
    v.as_i64()
        .and_then(|n| i32::try_from(n).ok())
        .ok_or_else(|| "Expected BAYNR i32".into())
}
fn unsigned(v: &Value, max: u64) -> Result<u32, String> {
    v.as_u64()
        .filter(|n| *n <= max)
        .map(|n| n as u32)
        .ok_or_else(|| "Expected bounded BAYNR unsigned integer".into())
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
        .ok_or_else(|| "BAYNR requires sixteen curve entries".into())
}
fn setting<'a>(v: &'a Value, noise: &str) -> Result<(&'a Value, usize), String> {
    let settings = list(v, "Setting")?;
    for row in settings {
        if row["SNR_Mode"]
            .as_str()
            .filter(|s| s.is_ascii() && !s.as_bytes().contains(&0))
            .is_none()
        {
            return Err("Invalid BAYNR SNR mode name".into());
        }
    }
    let index = settings
        .iter()
        .position(|s| s["SNR_Mode"].as_str().unwrap().starts_with(noise))
        .unwrap_or(0);
    Ok((&settings[index], index))
}
/// First prefix match in calibration and tuning is selected independently;
/// absent matches use setting zero. Sensor_Mode and BLC reference rows are not
/// read by this native preparation path. Retain all untouched table bytes.
pub fn prepare(
    calibration: &Value,
    noise: &str,
    output: &mut [u8; TABLE_BYTES],
) -> Result<[usize; 2], String> {
    if !noise.is_ascii() || noise.len() > 63 || noise.as_bytes().contains(&0) {
        return Err("Invalid BAYNR requested SNR name".into());
    }
    let (cal, ci) = setting(&calibration["CalibPara"], noise)?;
    let (tuning, ti) = setting(&calibration["TuningPara"], noise)?;
    let mut next = *output;
    next[..4]
        .copy_from_slice(&u32::from(flag(&calibration["TuningPara"]["enable"])?).to_le_bytes());
    next[4] = flag(&calibration["TuningPara"]["hdrdgain_ctrl_en"])?;
    for (i, row) in list(cal, "Calib_ISO")?.iter().take(13).enumerate() {
        put_float(&mut next, 8 + i * 4, &row["iso"])?;
        let p = 60 + i * 252;
        for (key, offset) in [("lumapoint", 4), ("sigma", 68)] {
            for (j, v) in sixteen(&row[key])?.iter().enumerate() {
                next[p + offset + j * 4..p + offset + j * 4 + 4]
                    .copy_from_slice(&signed(v)?.to_le_bytes());
            }
        }
    }
    for (i, row) in list(tuning, "Tuning_ISO")?.iter().take(13).enumerate() {
        put_float(&mut next, 8 + i * 4, &row["iso"])?;
        let p = 60 + i * 252;
        for (key, offset) in [("gauss_guide", 132), ("gain_bypass", 168)] {
            next[p + offset] = flag(&row[key])?;
        }
        for (key, offset) in [
            ("filter_strength", 136),
            ("edgesofts", 140),
            ("ratio", 144),
            ("weight", 148),
            ("gain_scale", 172),
            ("hdr_dgain_scale_s", 244),
            ("hdr_dgain_scale_m", 248),
        ] {
            put_float(&mut next, p + offset, &row[key])?;
        }
        for (key, offset) in [
            ("pix_diff", 152),
            ("diff_thld", 154),
            ("trans_offset", 158),
            ("itrans_offset", 160),
        ] {
            put_u16(&mut next, p + offset, &row[key])?;
        }
        next[p + 156] = unsigned(&row["trans_mode"], 255)? as u8;
        next[p + 164..p + 168]
            .copy_from_slice(&unsigned(&row["trans_datmax"], u64::from(u32::MAX))?.to_le_bytes());
        for (key, offset) in [("gain_lumapoint", 176), ("gain_adj", 208)] {
            for (j, v) in sixteen(&row["gain_adj"][key])?.iter().enumerate() {
                put_u16(&mut next, p + offset + j * 2, v)?;
            }
        }
    }
    *output = next;
    Ok([ci, ti])
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn late_invalid_curve_preserves_prepared_table() {
        let mut row = serde_json::json!({"iso":50,"lumapoint":[],"sigma":[]});
        // Construct arrays explicitly; the JSON macro does not use repeat syntax.
        row["lumapoint"] = serde_json::json!(alloc::vec![0;16]);
        row["sigma"] = serde_json::json!(alloc::vec![0;16]);
        let mut tune = serde_json::json!({"iso":50,"gauss_guide":true,"filter_strength":1,"edgesofts":1,"ratio":1,"weight":1,"gain_bypass":true,"gain_scale":1,"pix_diff":1,"diff_thld":1,"trans_mode":0,"trans_offset":0,"itrans_offset":0,"trans_datmax":1,"hdr_dgain_scale_s":1,"hdr_dgain_scale_m":1,"gain_adj":{}});
        tune["gain_adj"]["gain_lumapoint"] = serde_json::json!(alloc::vec![0;16]);
        tune["gain_adj"]["gain_adj"] = serde_json::json!(alloc::vec![0;15]);
        let cal = serde_json::json!({"CalibPara":{"Setting":[{"SNR_Mode":"LSNR","Calib_ISO":[row]}]},"TuningPara":{"enable":true,"hdrdgain_ctrl_en":false,"Setting":[{"SNR_Mode":"LSNR","Tuning_ISO":[tune]}]}});
        let mut table = [0xa5; TABLE_BYTES];
        assert!(prepare(&cal, "LSNR", &mut table).is_err());
        assert_eq!(table, [0xa5; TABLE_BYTES]);
    }
}

//! Native Chroma NR setting lookup and calibration table preparation.
extern crate alloc;
use crate::cnr_selection::TABLE_BYTES;
use alloc::{format, string::String};
use serde_json::Value;
fn list<'a>(v: &'a Value, key: &str) -> Result<&'a [Value], String> {
    let a = v[key]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 64)
        .ok_or_else(|| format!("Invalid CNR {key} array"))?;
    if let Some(n) = v.get(format!("{key}_len")) {
        if n.as_u64() != Some(a.len() as u64) {
            return Err(format!("CNR {key} count mismatch"));
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
        .ok_or_else(|| "Expected CNR boolean".into())
}
fn float(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|n| n as f32)
        .filter(|n| n.is_finite())
        .ok_or_else(|| "Expected finite CNR number".into())
}
fn put_float(b: &mut [u8], p: usize, v: &Value) -> Result<(), String> {
    b[p..p + 4].copy_from_slice(&float(v)?.to_le_bytes());
    Ok(())
}
fn setting<'a>(v: &'a Value, noise: &str) -> Result<(&'a Value, usize), String> {
    let settings = list(v, "Setting")?;
    for row in settings {
        if row["SNR_Mode"]
            .as_str()
            .filter(|s| s.is_ascii() && !s.as_bytes().contains(&0))
            .is_none()
        {
            return Err("Invalid CNR SNR mode name".into());
        }
    }
    let index = settings
        .iter()
        .position(|s| s["SNR_Mode"].as_str().unwrap().starts_with(noise))
        .unwrap_or(0);
    Ok((&settings[index], index))
}

/// First SNR prefix match, or setting zero. At most thirteen tuning rows are
/// copied; missing rows, row padding and unrelated table bytes are retained.
pub fn prepare(
    calibration: &Value,
    noise: &str,
    output: &mut [u8; TABLE_BYTES],
) -> Result<usize, String> {
    if !noise.is_ascii() || noise.len() > 63 || noise.as_bytes().contains(&0) {
        return Err("Invalid CNR requested SNR name".into());
    }
    let (tuning, index) = setting(&calibration["TuningPara"], noise)?;
    let enabled = flag(&calibration["TuningPara"]["enable"])?;
    let mut next = *output;
    next[..4].copy_from_slice(&u32::from(enabled).to_le_bytes());
    for (i, row) in list(tuning, "Tuning_ISO")?.iter().take(13).enumerate() {
        put_float(&mut next, 4 + i * 4, &row["iso"])?;
        let p = 56 + i * 180;
        next[p] = enabled;
        for (j, key) in ["down_scale_x", "down_scale_y"].iter().enumerate() {
            next[p + 1 + j] = row[key]
                .as_u64()
                .filter(|n| *n <= 255)
                .ok_or("Invalid CNR downscale byte")? as u8;
        }
        next[p + 52] = flag(&row["bf_wgt0_sel"])?;
        for (offset, keys) in [
            (
                4,
                &[
                    "thumb_sigma",
                    "thumb_bf_ratio",
                    "chroma_filter_strength",
                    "chroma_filter_wgt_clip",
                    "anti_chroma_ghost",
                    "chroma_filter_uv_gain",
                    "wgt_slope",
                    "gaus_ratio",
                    "bf_sigmaR",
                    "bf_uvgain",
                    "bf_ratio",
                    "hbf_wgt_clip",
                ][..],
            ),
            (
                56,
                &[
                    "global_alpha",
                    "saturation_adj_offset",
                    "saturation_adj_ratio",
                    "global_gain",
                    "global_gain_alpha",
                    "local_gain_scale",
                    "global_gain_thumb",
                    "global_gain_alpha_thumb",
                ][..],
            ),
        ] {
            for (j, key) in keys.iter().enumerate() {
                put_float(&mut next, p + offset + j * 4, &row[key])?;
            }
        }
        for (key, offset, n) in [
            ("gain_adj_strength_ratio", 88, 13),
            ("thumb_filter_wgt_coeff", 140, 4),
            ("gaus_coeff", 156, 6),
        ] {
            let values = row[key]
                .as_array()
                .filter(|a| a.len() == n)
                .ok_or_else(|| format!("Invalid CNR {key} curve"))?;
            for (j, value) in values.iter().enumerate() {
                put_float(&mut next, p + offset + j * 4, value)?;
            }
        }
    }
    *output = next;
    Ok(index)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_late_field_preserves_table() {
        let row =
            serde_json::json!({"iso":50,"down_scale_x":4,"down_scale_y":4,"bf_wgt0_sel":false});
        let cal = serde_json::json!({"TuningPara":{"enable":true,"Setting":[{"SNR_Mode":"LSNR","Tuning_ISO":[row]}]}});
        let mut table = [0xa5; TABLE_BYTES];
        assert!(prepare(&cal, "LSNR", &mut table).is_err());
        assert_eq!(table, [0xa5; TABLE_BYTES]);
    }
}

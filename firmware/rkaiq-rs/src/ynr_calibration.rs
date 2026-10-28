//! Native YNR v22 SNR lookup, sigma polynomial expansion and tuning preparation.
extern crate alloc;
use crate::ynr_selection::{ROW_BYTES, TABLE_BYTES};
use alloc::{format, string::String};
use serde_json::Value;
const FLAGS: [&str; 6] = [
    "ynr_bft3x3_bypass",
    "ynr_lbft5x5_bypass",
    "ynr_lgft3x3_bypass",
    "ynr_flt1x1_bypass",
    "ynr_nlm11x11_bypass",
    "ynr_thumb_mix_cur_en",
];
const GLOBAL: [&str; 4] = [
    "ynr_global_gain_alpha",
    "ynr_global_gain",
    "ynr_adjust_thresh",
    "ynr_adjust_scale",
];
const FILTER: [&str; 18] = [
    "low_bf1",
    "low_bf2",
    "low_thred_adj",
    "low_peak_supress",
    "low_edge_adj_thresh",
    "low_lbf_weight_thresh",
    "low_center_weight",
    "low_dist_adj",
    "low_weight",
    "low_filt1_strength",
    "low_filt2_strength",
    "low_bi_weight",
    "hi_bf_scale",
    "hi_gain_alpha",
    "hi_center_weight",
    "hi_weight_offset",
    "hi_min_sigma",
    "hi_nr_weight",
];
const COEFF: [&str; 6] = [
    "hi_filter_coeff1_1",
    "hi_filter_coeff1_2",
    "hi_filter_coeff1_3",
    "hi_filter_coeff2_1",
    "hi_filter_coeff2_2",
    "hi_filter_coeff2_3",
];
fn list<'a>(v: &'a Value, k: &str) -> Result<&'a [Value], String> {
    let a = v[k]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 64)
        .ok_or_else(|| format!("Invalid YNR {k}"))?;
    if let Some(n) = v.get(format!("{k}_len")) {
        if n.as_u64() != Some(a.len() as u64) {
            return Err(format!("YNR {k} count mismatch"));
        }
    }
    Ok(a)
}
fn number(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|n| n as f32)
        .filter(|n| n.is_finite())
        .ok_or_else(|| "Invalid finite YNR number".into())
}
fn flag(v: &Value) -> Result<u8, String> {
    if let Some(v) = v.as_bool() {
        return Ok(v as u8);
    }
    v.as_u64()
        .filter(|n| *n <= 1)
        .map(|n| n as u8)
        .ok_or_else(|| "Invalid YNR flag".into())
}
fn put(b: &mut [u8], p: usize, v: f32) {
    b[p..p + 4].copy_from_slice(&v.to_le_bytes())
}
fn setting(v: &Value, noise: &str) -> Result<usize, String> {
    let a = list(v, "Setting")?;
    for s in a {
        let n = s["SNR_Mode"].as_str().ok_or("Invalid YNR SNR string")?;
        if !n.is_ascii() || n.as_bytes().contains(&0) {
            return Err("Invalid YNR SNR string".into());
        }
    }
    Ok(a.iter()
        .position(|s| s["SNR_Mode"].as_str().unwrap().starts_with(noise))
        .unwrap_or(0))
}
/// Native initializer uses the tuning index for both lists, despite the lookup
/// publishing independent indices. Preserve that behavior and validate bounds.
pub fn prepare(
    cal: &Value,
    noise: &str,
    out: &mut [u8; TABLE_BYTES],
) -> Result<[usize; 2], String> {
    if !noise.is_ascii() || noise.len() > 63 || noise.as_bytes().contains(&0) {
        return Err("Invalid YNR SNR request".into());
    }
    let ci = setting(&cal["CalibPara"], noise)?;
    let ti = setting(&cal["TuningPara"], noise)?;
    let cs = list(&cal["CalibPara"], "Setting")?;
    let ts = list(&cal["TuningPara"], "Setting")?;
    let c = cs.get(ti).ok_or("YNR native shared-index out of bounds")?;
    let t = &ts[ti];
    let mut b = *out;
    let enabled = flag(&cal["TuningPara"]["enable"])?;
    b[..4].copy_from_slice(&u32::from(enabled).to_le_bytes());
    for (n, r) in list(c, "Calib_ISO")?.iter().take(13).enumerate() {
        put(&mut b, 68 + n * 4, number(&r["iso"])?);
        let p = 120 + n * ROW_BYTES;
        let coefficients = r["sigma_curve"]
            .as_array()
            .filter(|a| a.len() == 5)
            .ok_or("YNR needs five polynomial coefficients")?;
        let mut coeff = [0.; 5];
        for (i, v) in coefficients.iter().enumerate() {
            coeff[i] = v
                .as_f64()
                .filter(|v| v.is_finite())
                .ok_or("Invalid YNR sigma coefficient")?;
        }
        for i in 0..17 {
            let x = (i * 256) as f32;
            let x3 = (x * x) * x;
            let x4 = x * x3;
            let sigma = ((((coeff[1] * f64::from(x3) + coeff[0] * f64::from(x4))
                + coeff[2] * f64::from(x * x))
                + coeff[3] * f64::from(x))
                + coeff[4]) as f32;
            put(&mut b, p + 44 + i * 4, sigma.max(0.));
            b[p + 8 + i * 2..p + 10 + i * 2].copy_from_slice(&((i * 64) as u16).to_le_bytes());
        }
        put(&mut b, p + 184, number(&r["ynr_lci"])?);
        put(&mut b, p + 188, number(&r["ynr_hci"])?);
    }
    for (n, r) in list(t, "Tuning_ISO")?.iter().take(13).enumerate() {
        let p = 120 + n * ROW_BYTES;
        for (i, key) in FLAGS.iter().enumerate() {
            b[p + 1 + i] = flag(&r[key])?
        }
        for (i, key) in GLOBAL.iter().enumerate() {
            put(&mut b, p + 192 + i * 4, number(&r[key])?)
        }
        for (i, key) in FILTER.iter().enumerate() {
            put(&mut b, p + 276 + i * 4, number(&r[key])?)
        }
        for (i, key) in COEFF.iter().enumerate() {
            b[p + 348 + i] = r[key]
                .as_u64()
                .filter(|n| *n <= 255)
                .ok_or("Invalid YNR coefficient byte")? as u8;
        }
        for (key, offset, n) in [("lo_lumaPoint", 112, 6), ("hi_lumaPoint", 148, 6)] {
            let a = r["lumaPara"][key]
                .as_array()
                .filter(|a| a.len() == n)
                .ok_or("Invalid YNR luma curve")?;
            for (i, v) in a.iter().enumerate() {
                let v = v
                    .as_u64()
                    .filter(|n| *n <= 65535)
                    .ok_or("Invalid YNR luma value")? as u16;
                b[p + offset + i * 2..p + offset + i * 2 + 2].copy_from_slice(&v.to_le_bytes());
            }
        }
        for (values, key, offset, n) in [
            (&r["lumaPara"], "lo_ratio", 124, 6),
            (&r["lumaPara"], "hi_ratio", 160, 6),
            (r, "rnr_strength", 208, 17),
        ] {
            let a = values[key]
                .as_array()
                .filter(|a| a.len() == n)
                .ok_or("Invalid YNR ratio curve")?;
            for (i, v) in a.iter().enumerate() {
                put(&mut b, p + offset + i * 4, number(v)?);
            }
        }
    }
    *out = b;
    Ok([ci, ti])
}

//! Sharpening V33 SNR setting preparation into the native persistent table.
extern crate alloc;
use alloc::{format, string::String};
use serde_json::Value;
pub const ROW_BYTES: usize = 388;
pub const TABLE_BYTES: usize = 140 + 13 * ROW_BYTES;
pub(crate) fn f32_at(b: &[u8], p: usize) -> f32 {
    f32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
pub(crate) fn i32_at(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
pub(crate) fn u16_at(b: &[u8], p: usize) -> u16 {
    u16::from_le_bytes(b[p..p + 2].try_into().unwrap())
}
pub(crate) fn put_f32(b: &mut [u8], p: usize, n: f32) {
    b[p..p + 4].copy_from_slice(&n.to_le_bytes());
}
pub(crate) fn put_i32(b: &mut [u8], p: usize, n: i32) {
    b[p..p + 4].copy_from_slice(&n.to_le_bytes());
}
pub(crate) fn put_u16(b: &mut [u8], p: usize, n: u16) {
    b[p..p + 2].copy_from_slice(&n.to_le_bytes());
}
fn float(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|v| v as f32)
        .filter(|v| v.is_finite())
        .ok_or_else(|| "Invalid SHARP finite number".into())
}
fn byte(v: &Value) -> Result<u8, String> {
    if let Some(v) = v.as_bool() {
        return Ok(u8::from(v));
    }
    v.as_u64()
        .and_then(|v| u8::try_from(v).ok())
        .ok_or_else(|| "Invalid SHARP byte".into())
}
fn flag(v: &Value) -> Result<u8, String> {
    let v = byte(v)?;
    if v > 1 {
        return Err("Invalid SHARP boolean".into());
    }
    Ok(v)
}
fn array<'a>(v: &'a Value, n: usize) -> Result<&'a [Value], String> {
    v.as_array()
        .filter(|v| v.len() == n)
        .map(|v| v.as_slice())
        .ok_or_else(|| format!("SHARP array requires {n} elements"))
}
/// Copy no more than thirteen tuning rows, preserving untouched rows and padding.
/// Match the first SNR prefix, falling back to setting zero. Sensor_Mode is unused.
pub fn prepare(cal: &Value, noise: &str, output: &mut [u8; TABLE_BYTES]) -> Result<usize, String> {
    if !noise.is_ascii() || noise.len() > 63 || noise.as_bytes().contains(&0) {
        return Err("Invalid SHARP SNR name".into());
    }
    let tune = &cal["TuningPara"];
    let settings = tune["Setting"]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 64)
        .ok_or("Invalid SHARP settings")?;
    if let Some(n) = tune.get("Setting_len") {
        if n.as_u64() != Some(settings.len() as u64) {
            return Err("SHARP setting count mismatch".into());
        }
    }
    for s in settings {
        let n = s["SNR_Mode"].as_str().ok_or("Invalid SHARP SNR setting")?;
        if !n.is_ascii() || n.as_bytes().contains(&0) {
            return Err("Invalid SHARP SNR setting".into());
        }
    }
    let index = settings
        .iter()
        .position(|s| s["SNR_Mode"].as_str().unwrap().starts_with(noise))
        .unwrap_or(0);
    let setting = &settings[index];
    let rows = setting["Tuning_ISO"]
        .as_array()
        .filter(|a| !a.is_empty() && a.len() <= 64)
        .ok_or("Invalid SHARP ISO table")?;
    if let Some(n) = setting.get("Tuning_ISO_len") {
        if n.as_u64() != Some(rows.len() as u64) {
            return Err("SHARP ISO count mismatch".into());
        }
    }
    let mut next = *output;
    for (name, p) in [
        ("enable", 0),
        ("sharp_ratio_seperate_en", 4),
        ("kernel_sigma_enable", 8),
        ("Center_Mode", 76),
    ] {
        put_i32(&mut next, p, i32::from(flag(&tune[name])?));
    }
    for (i, row) in rows.iter().take(13).enumerate() {
        put_i32(&mut next, 88 + i * 4, float(&row["iso"])? as i32);
        let p = 140 + i * ROW_BYTES;
        next[p + 4] = flag(&row["exgain_bypass"])?;
        for (j, key) in [
            "pbf_gain",
            "pbf_ratio",
            "pbf_add",
            "gaus_ratio",
            "sharp_ratio",
            "sharp_ratio_0",
            "sharp_ratio_1",
            "bf_gain",
            "bf_ratio",
            "bf_add",
            "global_gain",
            "global_gain_alpha",
            "local_gainscale",
        ]
        .iter()
        .enumerate()
        {
            put_f32(&mut next, p + 56 + j * 4, float(&row[key])?);
        }
        next[p + 108] = byte(&row["global_hf_clip_pos"])?;
        put_f32(&mut next, p + 112, float(&row["noiseclip_strength"])?);
        next[p + 116] = byte(&row["enhance_bit"])?;
        next[p + 117] = flag(&row["noiseclip_mode"])?;
        put_u16(
            &mut next,
            p + 118,
            row["noise_sigma_clip"]
                .as_u64()
                .and_then(|n| u16::try_from(n).ok())
                .ok_or("Invalid SHARP noise sigma")?,
        );
        for (key, offset) in [("luma_point", 6), ("luma_sigma", 22), ("hf_clip", 38)] {
            for (j, v) in array(&row["luma_para"][key], 8)?.iter().enumerate() {
                put_u16(
                    &mut next,
                    p + offset + j * 2,
                    v.as_u64()
                        .and_then(|n| u16::try_from(n).ok())
                        .ok_or("Invalid SHARP luma entry")?,
                );
            }
        }
        for (key, offset, n) in [
            ("gain_adj_sharp_strength", 120, 14),
            ("dis_adj_sharp_strength", 176, 22),
        ] {
            for (j, v) in array(&row[key], n)?.iter().enumerate() {
                put_f32(&mut next, p + offset + j * 4, float(v)?);
            }
        }
        let k = &row["kernel_sigma"];
        for (key, offset) in [
            ("prefilter_sigma", 264),
            ("hfBilateralFilter_sigma", 268),
            ("GaussianFilter_sigma", 272),
            ("GaussianFilter_sigma_0", 280),
            ("GaussianFilter_sigma_1", 284),
        ] {
            put_f32(&mut next, p + offset, float(&k[key])?);
        }
        for (key, offset) in [
            ("GaussianFilter_radius", 276),
            ("GaussianFilter_radius_0", 288),
            ("GaussianFilter_radius_1", 289),
        ] {
            next[p + offset] = byte(&k[key])?;
        }
        for (key, offset, n) in [
            ("prefilter_coeff", 292, 3),
            ("GaussianFilter_coeff", 304, 6),
            ("hfBilateralFilter_coeff", 328, 3),
            ("GaussianFilter_coeff_0", 340, 6),
            ("GaussianFilter_coeff_1", 364, 6),
        ] {
            for (j, v) in array(&row["kernel_para"][key], n)?.iter().enumerate() {
                put_f32(&mut next, p + offset + j * 4, float(v)?);
            }
        }
    }
    *output = next;
    Ok(index)
}

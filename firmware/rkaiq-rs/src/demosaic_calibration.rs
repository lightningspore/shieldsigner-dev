//! Load the explicitly selected debayer_v2.param JSON object, not a full IQ DB.
extern crate alloc;
use crate::demosaic_selection::*;
use alloc::{format, string::String};
use serde_json::Value;
fn array<const N: usize>(value: &Value, key: &str, kind: &str) -> Result<[f64; N], String> {
    let source = value
        .get(key)
        .and_then(Value::as_array)
        .ok_or_else(|| format!("Expected array at {key}"))?;
    if source.len() != N {
        return Err(format!("Expected {N} values at {key}"));
    }
    let mut out = [0.; N];
    for (i, slot) in out.iter_mut().enumerate() {
        let n = source[i]
            .as_f64()
            .ok_or_else(|| format!("Expected number at {key}/{i}"))?;
        let valid = match kind {
            "f32" => (n as f32).is_finite(),
            "u8" => n >= 0. && n <= 255. && n.fract() == 0.,
            "u16" => n >= 0. && n <= 65535. && n.fract() == 0.,
            _ => n >= i32::MIN as f64 && n <= i32::MAX as f64 && n.fract() == 0.,
        };
        if !valid {
            return Err(format!("Out-of-range {kind} at {key}/{i}"));
        }
        *slot = n;
    }
    Ok(out)
}
impl Calibration {
    /// Input is one explicit scene's debayer_v2.param object. Scene selection
    /// and provenance belong to the caller; no fallback/default table is invented.
    pub fn from_value(value: &Value) -> Result<Self, String> {
        let enable = value
            .get("debayer_en")
            .ok_or_else(|| format!("Missing debayer_en"))?;
        let debayer_en = if let Some(v) = enable.as_bool() {
            v
        } else {
            match enable.as_i64() {
                Some(0) => false,
                Some(1) => true,
                _ => return Err(format!("Expected boolean or 0/1 at debayer_en")),
            }
        };

        let g_interp = value
            .get("g_interp")
            .ok_or_else(|| format!("Missing g_interp"))?;
        let g_drctwgt = value
            .get("g_drctwgt")
            .ok_or_else(|| format!("Missing g_drctwgt"))?;
        let g_filter = value
            .get("g_filter")
            .ok_or_else(|| format!("Missing g_filter"))?;
        let c_filter = value
            .get("c_filter")
            .ok_or_else(|| format!("Missing c_filter"))?;
        let out = Self {
            debayer_en,
            lowfreq_filter1: array::<4>(value, "lowfreq_filter1", "i32")?.map(|v| v as i32),
            highfreq_filter2: array::<4>(value, "highfreq_filter2", "i32")?.map(|v| v as i32),
            c_alpha_gaus_coe: array::<3>(value, "c_alpha_gaus_coe", "i32")?.map(|v| v as i32),
            c_guid_gaus_coe: array::<3>(value, "c_guid_gaus_coe", "i32")?.map(|v| v as i32),
            c_ce_gaus_coe: array::<3>(value, "c_ce_gaus_coe", "i32")?.map(|v| v as i32),
            g_interp: GreenInterpolation {
                iso: array::<13>(g_interp, "iso", "f32")?.map(|v| v as f32),
                debayer_clip_en: array::<13>(g_interp, "debayer_clip_en", "u8")?.map(|v| v as u8),
                debayer_gain_offset: array::<13>(g_interp, "debayer_gain_offset", "u16")?
                    .map(|v| v as u16),
                debayer_max_ratio: array::<13>(g_interp, "debayer_max_ratio", "u8")?
                    .map(|v| v as u8),
            },
            g_drctwgt: GreenDirection {
                iso: array::<13>(g_drctwgt, "iso", "f32")?.map(|v| v as f32),
                debayer_hf_offset: array::<13>(g_drctwgt, "debayer_hf_offset", "u16")?
                    .map(|v| v as u16),
                debayer_thed0: array::<13>(g_drctwgt, "debayer_thed0", "u8")?.map(|v| v as u8),
                debayer_thed1: array::<13>(g_drctwgt, "debayer_thed1", "u8")?.map(|v| v as u8),
                debayer_dist_scale: array::<13>(g_drctwgt, "debayer_dist_scale", "u8")?
                    .map(|v| v as u8),
                debayer_select_thed: array::<13>(g_drctwgt, "debayer_select_thed", "u8")?
                    .map(|v| v as u8),
            },
            g_filter: GreenFilter {
                iso: array::<13>(g_filter, "iso", "f32")?.map(|v| v as f32),
                debayer_gfilter_en: array::<13>(g_filter, "debayer_gfilter_en", "u8")?
                    .map(|v| v as u8),
                debayer_gfilter_offset: array::<13>(g_filter, "debayer_gfilter_offset", "u16")?
                    .map(|v| v as u16),
            },
            c_filter: ColorFilter {
                iso: array::<13>(c_filter, "iso", "f32")?.map(|v| v as f32),
                debayer_cfilter_en: array::<13>(c_filter, "debayer_cfilter_en", "u8")?
                    .map(|v| v as u8),
                debayer_loggd_offset: array::<13>(c_filter, "debayer_loggd_offset", "u16")?
                    .map(|v| v as u16),
                debayer_cfilter_str: array::<13>(c_filter, "debayer_cfilter_str", "f32")?
                    .map(|v| v as f32),
                debayer_wet_clip: array::<13>(c_filter, "debayer_wet_clip", "f32")?
                    .map(|v| v as f32),
                debayer_wet_ghost: array::<13>(c_filter, "debayer_wet_ghost", "f32")?
                    .map(|v| v as f32),
                debayer_wgtslope: array::<13>(c_filter, "debayer_wgtslope", "f32")?
                    .map(|v| v as f32),
                debayer_bf_sgm: array::<13>(c_filter, "debayer_bf_sgm", "f32")?.map(|v| v as f32),
                debayer_bf_clip: array::<13>(c_filter, "debayer_bf_clip", "u8")?.map(|v| v as u8),
                debayer_bf_curwgt: array::<13>(c_filter, "debayer_bf_curwgt", "u8")?
                    .map(|v| v as u8),
                debayer_loghf_offset: array::<13>(c_filter, "debayer_loghf_offset", "u16")?
                    .map(|v| v as u16),
                debayer_alpha_offset: array::<13>(c_filter, "debayer_alpha_offset", "u16")?
                    .map(|v| v as u16),
                debayer_alpha_scale: array::<13>(c_filter, "debayer_alpha_scale", "f32")?
                    .map(|v| v as f32),
                debayer_edge_offset: array::<13>(c_filter, "debayer_edge_offset", "u16")?
                    .map(|v| v as u16),
                debayer_edge_scale: array::<13>(c_filter, "debayer_edge_scale", "f32")?
                    .map(|v| v as f32),
            },
        };
        out.validate()
            .map_err(|v| format!("Invalid demosaic calibration: {v:?}"))?;
        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloc::vec;
    use serde_json::json;
    fn value() -> Value {
        let mut v = json!({"debayer_en":1,"lowfreq_filter1":[-2,2,-4,4],"highfreq_filter2":[-1,2,-2,4],"c_alpha_gaus_coe":[64,32,16],"c_guid_gaus_coe":[64,32,16],"c_ce_gaus_coe":[64,32,16]});
        for (group, fields) in [
            (
                "g_interp",
                &[
                    "debayer_clip_en",
                    "debayer_gain_offset",
                    "debayer_max_ratio",
                ][..],
            ),
            (
                "g_drctwgt",
                &[
                    "debayer_hf_offset",
                    "debayer_thed0",
                    "debayer_thed1",
                    "debayer_dist_scale",
                    "debayer_select_thed",
                ][..],
            ),
            (
                "g_filter",
                &["debayer_gfilter_en", "debayer_gfilter_offset"][..],
            ),
            (
                "c_filter",
                &[
                    "debayer_cfilter_en",
                    "debayer_loggd_offset",
                    "debayer_cfilter_str",
                    "debayer_wet_clip",
                    "debayer_wet_ghost",
                    "debayer_wgtslope",
                    "debayer_bf_sgm",
                    "debayer_bf_clip",
                    "debayer_bf_curwgt",
                    "debayer_loghf_offset",
                    "debayer_alpha_offset",
                    "debayer_alpha_scale",
                    "debayer_edge_offset",
                    "debayer_edge_scale",
                ][..],
            ),
        ] {
            v[group] = json!({"iso":[1,2,3,4,5,6,7,8,9,10,11,12,13]});
            for field in fields {
                v[group][*field] = json!(vec![1; 13]);
            }
        }
        v
    }
    #[test]
    fn fractional_knots_use_truncated_integer_weighting() {
        let mut v = value();
        v["g_interp"]["iso"] = json!([1.9, 4.9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]);
        v["g_interp"]["debayer_max_ratio"][0] = json!(0);
        v["g_interp"]["debayer_max_ratio"][1] = json!(6);
        let selected = Calibration::from_value(&v).unwrap().select(3).unwrap();
        assert_eq!(selected.debayer_max_ratio, 4);
        assert_eq!(selected.lowfreq_filter1, [-2, 2, -4, 4]);
    }
    #[test]
    fn reject_knots_that_collapse_after_integer_conversion() {
        let mut v = value();
        v["g_interp"]["iso"][0] = json!(1.1);
        v["g_interp"]["iso"][1] = json!(1.2);
        assert!(Calibration::from_value(&v).is_err());
    }
    #[test]
    fn reject_missing_or_truncated_tables_without_defaults() {
        let mut v = value();
        v["g_filter"]
            .as_object_mut()
            .unwrap()
            .remove("debayer_gfilter_en");
        assert!(Calibration::from_value(&v).is_err());
        let mut v = value();
        v["c_filter"]["iso"] = json!([1, 2, 3]);
        assert!(Calibration::from_value(&v).is_err());
    }
    #[test]
    fn reject_fractional_unsigned_and_overflowing_values() {
        let mut v = value();
        v["g_interp"]["debayer_clip_en"][0] = json!(1.5);
        assert!(Calibration::from_value(&v).is_err());
        let mut v = value();
        v["g_interp"]["debayer_gain_offset"][0] = json!(65536);
        assert!(Calibration::from_value(&v).is_err());
        let mut v = value();
        v["c_filter"]["debayer_alpha_scale"][0] = json!(1e100);
        assert!(Calibration::from_value(&v).is_err());
    }
}

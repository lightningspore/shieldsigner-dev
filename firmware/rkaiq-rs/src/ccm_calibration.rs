//! Explicit CCM JSON-to-static-result fields, matching ConfigHwbyCalib.
extern crate alloc;
use crate::isp_ccm::RESULT_BYTES;
use alloc::{format, string::String};
use serde_json::Value;
fn flag(v: &Value) -> Result<u8, String> {
    if let Some(v) = v.as_bool() {
        return Ok(u8::from(v));
    }
    v.as_u64()
        .filter(|v| *v <= 1)
        .map(|v| v as u8)
        .ok_or_else(|| "Expected CCM boolean".into())
}
fn number(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|v| v as f32)
        .filter(|v| v.is_finite())
        .ok_or_else(|| "Expected finite CCM number".into())
}
/// Apply only the fields written by native ConfigHwbyCalib. Preserve enable,
/// matrix, curve (except symmetric final point), ratio and all padding.
/// Supports both bound layouts; this alone does not enable asymmetric processing.
pub fn static_fields(calibration: &Value, result: &mut [u8; RESULT_BYTES]) -> Result<(), String> {
    let luma = &calibration["lumaCCM"];
    let asym = flag(&luma["asym_enable"])?;
    let (highy, bound, right) = if asym == 0 {
        let sym = &luma["y_alp_sym"];
        let bound = number(&sym["bound_pos_bit"])?;
        (flag(&sym["highy_adj_en"])?, bound, bound)
    } else {
        let asym = &luma["y_alp_asym"];
        (
            1,
            number(&asym["bound_pos_bit"])?,
            number(&asym["right_pos_bit"])?,
        )
    };
    let rgb = luma["rgb2y_para"]
        .as_array()
        .filter(|v| v.len() == 3)
        .ok_or_else(|| format!("Expected three CCM luma coefficients"))?;
    let mut coeffs = [0.; 3];
    for i in 0..3 {
        coeffs[i] = number(&rgb[i])?;
    }
    let enhance = calibration["enhCCM"]["enh_rgb2y_para"]
        .as_array()
        .filter(|v| v.len() == 3)
        .ok_or_else(|| format!("Expected three CCM enhancement coefficients"))?;
    let mut bytes = [0u8; 3];
    for i in 0..3 {
        bytes[i] = enhance[i]
            .as_u64()
            .filter(|v| *v <= 255)
            .ok_or_else(|| "Expected CCM u8 enhancement coefficient")? as u8;
    }
    result[1] = asym;
    result[4] = highy;
    if asym == 0 {
        result[124..128].copy_from_slice(&1024f32.to_le_bytes());
    }
    result[128..132].copy_from_slice(&right.to_le_bytes());
    result[132..136].copy_from_slice(&bound.to_le_bytes());
    for i in 0..3 {
        result[136 + i * 4..140 + i * 4].copy_from_slice(&coeffs[i].to_le_bytes());
    }
    result[148..151].copy_from_slice(&bytes);
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_json_preserves_result() {
        let mut out = [0xa5; RESULT_BYTES];
        assert!(
            static_fields(&serde_json::json!({"lumaCCM":{"asym_enable":0}}), &mut out).is_err()
        );
        assert_eq!(out, [0xa5; RESULT_BYTES]);
    }
}

use crate::{
    ccm_luma::Row,
    ccm_runtime::{Illuminant, NamedProfile},
    ccm_selection::Profile,
};
use alloc::vec::Vec;
pub struct OwnedIlluminant {
    pub gains: [f32; 2],
    pub sensor_gains: [f32; 4],
    pub saturations: [f32; 4],
    pub profiles: Vec<NamedProfile>,
}
pub struct Automatic {
    pub enabled: bool,
    pub damping_enabled: bool,
    pub enhancement_enabled: bool,
    pub wb_tolerance: f32,
    pub gain_tolerance: f32,
    pub illuminants: Vec<OwnedIlluminant>,
    pub luma: [Row; 13],
    pub alpha_gains: [f32; 9],
    pub alpha_scales: [f32; 9],
    pub enhancement_gains: [f32; 9],
    pub enhancement_ratios: [f32; 9],
    pub static_result: [u8; RESULT_BYTES],
}
fn array<const N: usize>(v: &Value) -> Result<[f32; N], String> {
    let a = v
        .as_array()
        .filter(|a| a.len() == N)
        .ok_or_else(|| format!("Expected CCM array length {N}"))?;
    let mut result = [0.; N];
    for i in 0..N {
        result[i] = number(&a[i])?;
    }
    Ok(result)
}
fn increasing(v: &[f32]) -> Result<(), String> {
    if v.windows(2).any(|v| v[0] >= v[1]) {
        Err("CCM grid must increase strictly".into())
    } else {
        Ok(())
    }
}
fn name(v: &Value) -> Result<[u8; 25], String> {
    let s = v
        .as_str()
        .filter(|s| !s.is_empty() && s.len() < 25 && !s.as_bytes().contains(&0))
        .ok_or_else(|| String::from("Expected CCM name of 1..24 bytes"))?;
    let mut out = [0; 25];
    out[..s.len()].copy_from_slice(s.as_bytes());
    Ok(out)
}
impl Automatic {
    /// Load an explicit symmetric/non-blended profile. Unsupported modes fail.
    /// This resolves names and stable descending profile order as native init does.
    pub fn from_value(v: &Value) -> Result<Self, String> {
        let luma = &v["lumaCCM"];
        let tuning = &v["TuningPara"];
        let enhance = &v["enhCCM"];
        if flag(&luma["asym_enable"])? != 0 || flag(&tuning["illu_estim"]["interp_enable"])? != 0 {
            return Err("CCM loader requires symmetric, non-blended mode".into());
        }
        let matrices = tuning["matrixAll"]
            .as_array()
            .ok_or_else(|| "Expected CCM matrices")?;
        if tuning["matrixAll_len"].as_u64() != Some(matrices.len() as u64) {
            return Err("CCM matrix count mismatch".into());
        }
        let mut parsed = Vec::new();
        for m in matrices {
            let n = name(&m["name"])?;
            if parsed.iter().any(|(other, _)| *other == n) {
                return Err("Duplicate CCM matrix name".into());
            }
            parsed.push((
                n,
                Profile {
                    saturation: number(&m["saturation"])?,
                    matrix: array(&m["ccMatrix"])?,
                    offsets: array(&m["ccOffsets"])?,
                },
            ));
        }
        let source = tuning["aCcmCof"]
            .as_array()
            .filter(|a| !a.is_empty() && a.len() <= 9)
            .ok_or_else(|| "Expected 1..9 CCM illuminants")?;
        if tuning["aCcmCof_len"].as_u64() != Some(source.len() as u64) {
            return Err("CCM illuminant count mismatch".into());
        }
        let mut illuminants = Vec::new();
        for ill in source {
            let names = ill["matrixUsed"]
                .as_array()
                .filter(|a| !a.is_empty() && a.len() <= 5)
                .ok_or_else(|| "Expected 1..5 CCM profile names")?;
            if ill["matrixUsed_len"].as_u64() != Some(names.len() as u64) {
                return Err("CCM profile count mismatch".into());
            }
            let mut profiles = Vec::new();
            for n in names {
                let n = name(n)?;
                let p = parsed
                    .iter()
                    .find(|(other, _)| *other == n)
                    .ok_or_else(|| "Unresolved CCM profile name")?;
                profiles.push(NamedProfile {
                    name: n,
                    profile: p.1,
                });
            }
            profiles.sort_by(|a, b| {
                b.profile
                    .saturation
                    .partial_cmp(&a.profile.saturation)
                    .unwrap()
            });
            if profiles
                .windows(2)
                .any(|p| p[0].profile.saturation <= p[1].profile.saturation)
            {
                return Err("CCM profile saturation must decrease strictly".into());
            }
            let sensor_gains = array(&ill["gain_sat_curve"]["gains"])?;
            increasing(&sensor_gains)?;
            illuminants.push(OwnedIlluminant {
                gains: array(&ill["awbGain"])?,
                sensor_gains,
                saturations: array(&ill["gain_sat_curve"]["sat"])?,
                profiles,
            });
        }
        let rows = luma["y_alp_sym"]["gain_yalp_curve"]
            .as_array()
            .filter(|a| a.len() == 13)
            .ok_or_else(|| "Expected 13 CCM luma rows")?;
        let mut curves = [Row {
            iso: 0.,
            curve: [0.; 17],
        }; 13];
        for (out, row) in curves.iter_mut().zip(rows) {
            *out = Row {
                iso: number(&row["iso"])?,
                curve: array(&row["y_alpha_curve"])?,
            };
        }
        if curves.windows(2).any(|r| r[0].iso >= r[1].iso) {
            return Err("CCM luma ISO grid must increase strictly".into());
        }
        let alpha_gains = array(&luma["gain_alphaScale_curve"]["gain"])?;
        increasing(&alpha_gains)?;
        let enhancement_gains = array(&enhance["enh_rat"]["gains"])?;
        increasing(&enhancement_gains)?;
        let mut static_result = [0; RESULT_BYTES];
        static_fields(v, &mut static_result)?;
        Ok(Self {
            enabled: flag(&v["control"]["enable"])? != 0,
            damping_enabled: flag(&tuning["damp_enable"])? != 0,
            enhancement_enabled: flag(&enhance["enh_adj_en"])? != 0,
            wb_tolerance: number(&v["control"]["wbgain_tolerance"])?,
            gain_tolerance: number(&v["control"]["gain_tolerance"])?,
            illuminants,
            luma: curves,
            alpha_gains,
            alpha_scales: array(&luma["gain_alphaScale_curve"]["scale"])?,
            enhancement_gains,
            enhancement_ratios: array(&enhance["enh_rat"]["enh_rat_max"])?,
            static_result,
        })
    }
    pub fn views(&self) -> Vec<Illuminant<'_>> {
        self.illuminants
            .iter()
            .map(|i| Illuminant {
                gains: i.gains,
                sensor_gains: i.sensor_gains,
                saturations: i.saturations,
                profiles: &i.profiles,
            })
            .collect()
    }
}

#[cfg(test)]
mod table_tests {
    use super::*;
    #[test]
    fn unsupported_modes_and_bad_references_are_rejected() {
        let mut v = serde_json::json!({"lumaCCM":{"asym_enable":1},"TuningPara":{"illu_estim":{"interp_enable":0}}});
        assert!(Automatic::from_value(&v)
            .err()
            .unwrap()
            .contains("symmetric"));
        v["lumaCCM"]["asym_enable"] = 0.into();
        v["TuningPara"]["matrixAll"] = serde_json::json!([]);
        v["TuningPara"]["matrixAll_len"] = 0.into();
        v["TuningPara"]["aCcmCof"] =
            serde_json::json!([{"matrixUsed":["missing"],"matrixUsed_len":1}]);
        v["TuningPara"]["aCcmCof_len"] = 1.into();
        assert!(Automatic::from_value(&v)
            .err()
            .unwrap()
            .contains("Unresolved"));
        v["TuningPara"]["matrixAll_len"] = 1.into();
        assert!(Automatic::from_value(&v)
            .err()
            .unwrap()
            .contains("count mismatch"));
    }
}

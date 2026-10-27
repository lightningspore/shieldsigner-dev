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

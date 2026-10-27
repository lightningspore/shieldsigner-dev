//! Explicitly selected singleColorProces IQ object; not a full AWB IQ database.
extern crate alloc;
use crate::{
    awb_single_color::{self, Line},
    awb_single_color_grid::{self, Candidate, Color},
};
use alloc::{
    format,
    string::{String, ToString},
    vec::Vec,
};
use serde_json::Value;
fn at<'a>(v: &'a Value, p: &str) -> Result<&'a Value, String> {
    v.pointer(p).ok_or_else(|| format!("Missing AWB field {p}"))
}
fn number(v: &Value, p: &str) -> Result<f32, String> {
    let n = at(v, p)?
        .as_f64()
        .ok_or_else(|| format!("Expected number at {p}"))? as f32;
    if !n.is_finite() {
        return Err(format!("Nonfinite/out-of-range number at {p}"));
    }
    Ok(n)
}
fn integer(v: &Value, p: &str, lo: i64, hi: i64) -> Result<i64, String> {
    let n = at(v, p)?
        .as_f64()
        .ok_or_else(|| format!("Expected integer at {p}"))?;
    if n < lo as f64 || n > hi as f64 || n.fract() != 0. {
        return Err(format!("Integer out of range at {p}"));
    }
    Ok(n as i64)
}
fn flag(v: &Value, p: &str) -> Result<bool, String> {
    if let Some(x) = at(v, p)?.as_bool() {
        Ok(x)
    } else {
        Ok(integer(v, p, 0, 1)? != 0)
    }
}
fn array<const N: usize>(v: &Value, p: &str) -> Result<[f32; N], String> {
    if at(v, p)?
        .as_array()
        .ok_or_else(|| format!("Expected array at {p}"))?
        .len()
        != N
    {
        return Err(format!("Expected {N} values at {p}"));
    }
    let mut out = [0.; N];
    for (i, x) in out.iter_mut().enumerate() {
        *x = number(v, &format!("{p}/{i}"))?;
    }
    Ok(out)
}
fn ordered(v: &[f32], p: &str) -> Result<(), String> {
    if v.windows(2).any(|x| x[0] > x[1]) {
        Err(format!("Descending knots at {p}"))
    } else {
        Ok(())
    }
}
fn list<'a>(v: &'a Value, p: &str) -> Result<&'a [Value], String> {
    let a = at(v, p)?
        .as_array()
        .ok_or_else(|| format!("Expected array at {p}"))?;
    let n = integer(v, &format!("{p}_len"), 1, 14)? as usize;
    if a.len() != n {
        return Err(format!("Length mismatch at {p}"));
    }
    Ok(a)
}
/// Owned settings for the existing bounded classifier and confidence manager.
/// Scene selection and calibrated line construction remain the caller's job.
pub struct SingleColor {
    pub enabled: bool,
    pub mode: i32,
    pub colors: Vec<Color>,
    pub color_indices: Vec<i32>,
    pub candidates: Vec<Candidate>,
    pub candidate_names: Vec<String>,
    pub history_target: u16,
    pub alpha: f32,
    pub diagnostic_candidate: i32,
    pub acceptance_threshold: f32,
    pub estimated_density_threshold: f32,
    pub estimated_single_threshold: f32,
    pub high_history_threshold: f32,
    pub confidence: awb_single_color::Calibration,
}
impl SingleColor {
    /// Parse one explicitly selected autoExtPara.singleColorProces object.
    /// No scene, enable flag, mode, count or numerical table is defaulted.
    pub fn from_value(v: &Value) -> Result<Self, String> {
        let mode = match at(v, "/mode")?.as_str() {
            Some("AWB_SGC_CALL_INITIAL") => 0,
            Some("AWB_SGC_CALL_AUTO") => 1,
            Some("AWB_SGC_CALL_ALWAYS") => 2,
            _ => return Err(format!("Unsupported single-color mode")),
        };
        let mut colors = Vec::new();
        let mut color_indices = Vec::new();
        for c in list(v, "/colorBlock")? {
            let knots = array(c, "/ct")?;
            ordered(&knots, "colorBlock/ct")?;
            colors.push(Color {
                chroma: number(c, "/meanC")?,
                hue: number(c, "/meanH")?,
                cct_knots: knots,
                distance_thresholds: array(c, "/disTh")?,
            });
            color_indices.push(integer(c, "/index", i32::MIN as i64, i32::MAX as i64)? as i32);
        }
        let mut candidates = Vec::new();
        let mut candidate_names = Vec::new();
        for c in list(v, "/lsUsedForEstimation")? {
            let name = at(c, "/name")?
                .as_str()
                .ok_or_else(|| format!("Expected candidate name"))?;
            if name.as_bytes().contains(&0) || name.len() > 19 {
                return Err(format!("Invalid candidate name"));
            }
            candidate_names.push(name.to_string());
            candidates.push(Candidate {
                red: number(c, "/RGain")?,
                blue: number(c, "/BGain")?,
            });
        }
        let confidence = awb_single_color::Calibration {
            brightness_knots: array(v, "/wgtLvX")?,
            brightness_weights: array(v, "/wgtLvY")?,
            density_knots: array(v, "/wgtWpNumthX")?,
            density_weights: array(v, "/wgtWpNumthY")?,
            distance_knots: array(v, "/wgtDisX")?,
            cct_knots: array(v, "/wgtDisCt")?,
            distance_weights: [
                array(v, "/wgtDisHCtY")?,
                array(v, "/wgtDisMCtY")?,
                array(v, "/wgtDisLCtY")?,
            ],
            disagreement_knots: array(v, "/wgtClrGradX")?,
            disagreement_weights: array(v, "/wgtClrGradY")?,
        };
        for (knots, name) in [
            (&confidence.brightness_knots[..], "wgtLvX"),
            (&confidence.density_knots[..], "wgtWpNumthX"),
            (&confidence.distance_knots[..], "wgtDisX"),
            (&confidence.cct_knots[..], "wgtDisCt"),
            (&confidence.disagreement_knots[..], "wgtClrGradX"),
        ] {
            ordered(knots, name)?;
        }
        let alpha = number(v, "/alpha")?;
        if !(0. ..=1.).contains(&alpha) {
            return Err(format!("Alpha out of range"));
        }
        Ok(Self {
            enabled: flag(v, "/enable")?,
            mode,
            colors,
            color_indices,
            candidates,
            candidate_names,
            history_target: integer(v, "/illuEstListSize", 0, u16::MAX as i64)? as u16,
            alpha,
            diagnostic_candidate: integer(v, "/illuMchPrt", i32::MIN as i64, i32::MAX as i64)?
                as i32,
            acceptance_threshold: number(v, "/useSgcResth")?,
            estimated_density_threshold: number(v, "/updateDpWbgnTh")?,
            estimated_single_threshold: number(v, "/updateDpWbgnTh2")?,
            high_history_threshold: number(v, "/updateEstWbgnTh")?,
            confidence,
        })
    }
    pub fn classifier(&self, first: Line, second: Line) -> awb_single_color_grid::Calibration<'_> {
        awb_single_color_grid::Calibration {
            candidates: &self.candidates,
            colors: &self.colors,
            alpha: self.alpha,
            history_target: self.history_target,
            first,
            second,
        }
    }
}

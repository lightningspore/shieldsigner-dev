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

/// An owned prior curve; numerical adapters borrow its slices.
pub struct Prior {
    pub knots: Vec<f32>,
    pub weights: Vec<f32>,
}
pub struct Illumination {
    pub name: String,
    pub kind: i32,
    pub reference_gain: [f32; 4],
    pub spatial_percentages: [u8; 16],
    /// JSON order [low, high]; native strategy stores [high, low].
    pub day_thresholds: [u32; 2],
    pub low_gain: [f32; 4],
    pub high_gain: [f32; 4],
    pub prior: Prior,
    pub uv: [[f32; 4]; 2],
    pub xy: [[f32; 4]; 2],
    pub yuv_knots: [f32; 6],
    pub yuv_thresholds: [f32; 6],
    pub yuv_line: [f32; 6],
    pub yuv_distance: f32,
}
pub struct Lights {
    pub entries: Vec<Illumination>,
    pub first_frame: usize,
}
impl Lights {
    /// Parse one explicitly selected wb_v32 scene's light table and first-frame
    /// name. Other autoPara/autoExtPara settings are not defaulted or loaded.
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let auto = at(wb, "/autoPara")?;
        let values = at(auto, "/lightSources")?
            .as_array()
            .ok_or_else(|| format!("Expected lightSources array"))?;
        let count = integer(auto, "/lightSources_len", 1, 255)? as usize;
        if count != values.len() {
            return Err(format!("Light count mismatch"));
        }
        let mut entries: Vec<Illumination> = Vec::new();
        for v in values {
            let name = at(v, "/name")?
                .as_str()
                .ok_or_else(|| format!("Expected light name"))?;
            if name.is_empty()
                || name.as_bytes().contains(&0)
                || name.len() > 19
                || entries.iter().any(|l| l.name == name)
            {
                return Err(format!("Invalid/duplicate light name"));
            }
            let kind = match at(v, "/doorType")?.as_str() {
                Some("CALIB_AWB_DOOR_TYPE_INDOOR") => 1,
                Some("CALIB_AWB_DOOR_TYPE_AMBIGUITY") => 2,
                Some("CALIB_AWB_DOOR_TYPE_OUTDOOR") => 3,
                _ => return Err(format!("Unknown doorType")),
            };
            let mut percentages = [0u8; 16];
            if at(v, "/staWeight")?.as_array().map(|a| a.len()) != Some(16) {
                return Err(format!("Expected 16 spatial weights"));
            }
            for (i, p) in percentages.iter_mut().enumerate() {
                *p = integer(v, &format!("/staWeight/{i}"), 0, 255)? as u8;
            }
            if at(v, "/dayGainLvThSet")?.as_array().map(|a| a.len()) != Some(2) {
                return Err(format!("Expected two daylight thresholds"));
            }
            let day_thresholds = [
                integer(v, "/dayGainLvThSet/0", 0, u32::MAX as i64)? as u32,
                integer(v, "/dayGainLvThSet/1", 0, u32::MAX as i64)? as u32,
            ];
            let weight = at(v, "/weight")?;
            let count = integer(weight, "/lumaValue_len", 1, i32::MAX as i64)? as usize;
            if integer(weight, "/weight_len", 1, i32::MAX as i64)? as usize != count {
                return Err(format!("Prior length mismatch"));
            }
            let mut knots = Vec::new();
            let mut weights = Vec::new();
            for (key, out) in [("lumaValue", &mut knots), ("weight", &mut weights)] {
                if at(weight, &format!("/{key}"))?.as_array().map(|a| a.len()) != Some(count) {
                    return Err(format!("Prior array length mismatch"));
                }
                for i in 0..count {
                    out.push(number(weight, &format!("/{key}/{i}"))?);
                }
            }
            if knots.windows(2).any(|x| x[0] >= x[1]) {
                return Err(format!("Prior knots must increase"));
            }
            entries.push(Illumination {
                name: name.to_string(),
                kind,
                reference_gain: array(v, "/standardGainValue")?,
                spatial_percentages: percentages,
                day_thresholds,
                low_gain: array(v, "/defaultDayGainLow")?,
                high_gain: array(v, "/defaultDayGainHigh")?,
                prior: Prior { knots, weights },
                uv: [array(v, "/uvRegion/u")?, array(v, "/uvRegion/v")?],
                xy: [array(v, "/xyRegion/normal")?, array(v, "/xyRegion/big")?],
                yuv_knots: array(v, "/rtYuvRegion/thcurve_u")?,
                yuv_thresholds: array(v, "/rtYuvRegion/thcure_th")?,
                yuv_line: array(v, "/rtYuvRegion/lineVector")?,
                yuv_distance: number(v, "/rtYuvRegion/disP1P2")?,
            });
        }
        let first = at(wb, "/autoExtPara/lightSourceForFirstFrame")?
            .as_str()
            .ok_or_else(|| format!("Expected first-frame light name"))?;
        let first_frame = entries
            .iter()
            .position(|l| l.name == first)
            .ok_or_else(|| format!("First-frame light not found"))?;
        Ok(Self {
            entries,
            first_frame,
        })
    }
}
impl Illumination {
    pub fn probability(
        &self,
        statistic_gain: [f32; 4],
        white_points: u32,
    ) -> crate::awb_probability::Light<'_> {
        crate::awb_probability::Light {
            reference_gain: self.reference_gain,
            statistic_gain,
            kind: self.kind,
            white_points,
            prior: crate::awb_probability::Curve {
                knots: &self.prior.knots,
                weights: &self.prior.weights,
            },
        }
    }
    /// Runtime selects the environment index and extra-region flag; these are
    /// deliberately not inferred from static JSON or its detection geometry.
    pub fn controller_light(
        &self,
        environment: usize,
        extra_enabled: bool,
    ) -> Result<crate::awb_gain_controller::Light<'_>, crate::InvalidInput> {
        let percentage = *self
            .spatial_percentages
            .get(environment)
            .ok_or(crate::InvalidInput::Length)?;
        Ok(crate::awb_gain_controller::Light {
            counts: [0; 4],
            gains: [[0.; 4]; 4],
            probability: self.probability([0.; 4], 0),
            calibration: crate::awb_high_gain::Light {
                selected_gain: [0.; 4],
                selected_count: 0,
                extra_gain: [0.; 4],
                extra_count: 0,
                extra_enabled,
                low_threshold: self.day_thresholds[0],
                high_threshold: self.day_thresholds[1],
                low_gain: self.low_gain,
                high_gain: self.high_gain,
                spatial_percentage: percentage,
                probability: 0.,
            },
        })
    }
}

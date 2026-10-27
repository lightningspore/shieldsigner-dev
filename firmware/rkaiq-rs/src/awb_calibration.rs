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

/// Shared strategy settings copied by JsonPara2SwParaCom (ELF 0xc8450).
/// Dynamic preprocessor curves, clipping/adjustment enable flags and saved-site
/// initialization are separate parts of the full calibration update.
pub struct Common {
    pub night_gain: [f32; 4],
    pub lines: [Line; 2],
    pub daylight_cct_minimum: f32,
    pub clip_tables: [Vec<f32>; 3],
    pub remosaic_enabled: bool,
    pub remosaic_inverse: bool,
    pub sensor_gain: [f32; 4],
    pub history_weights: Vec<u8>,
    pub brightness_knots: [u32; 16],
    /// Copied by the enclosing calibration update before the common helper.
    pub night_percentages: [u8; 16],
    pub environment_thresholds: [u32; 4],
    /// Native declares 16 intervals over its 16 knots and the adjacent first
    /// division-threshold word. Keep that final boundary explicit and bounded.
    pub environment_boundaries: [u32; 17],
    pub distance_thresholds: [f32; 2],
    pub probability_thresholds: [u32; 4],
    pub relative_count_threshold: f32,
    pub damping: crate::awb_gain::DampingParameters,
    pub luma_history_target: i32,
    pub history_convergence: f32,
    pub damped_convergence: f32,
    pub stabilization: bool,
    pub region_history_target: i32,
    pub region_variance_threshold: f32,
    pub initial_smart: [f32; 3],
    pub initial_countdown: i32,
}
impl Common {
    /// Input is the explicit autoExtPara object, not an implicitly chosen scene.
    pub fn from_value(v: &Value) -> Result<Self, String> {
        // Native requires a nonempty adjustment LUT even when adjustment is off.
        let lut_count = integer(v, "/wbGainAdjust/lutAll_len", 1, i32::MAX as i64)? as usize;
        if at(v, "/wbGainAdjust/lutAll")?.as_array().map(|a| a.len()) != Some(lut_count) {
            return Err(format!("Adjustment LUT count mismatch"));
        }
        let clip = at(v, "/wbGainClip")?;
        let n = integer(clip, "/cct_len", 1, i32::MAX as i64)? as usize;
        let mut tables = [Vec::new(), Vec::new(), Vec::new()];
        for (key, table) in ["cct", "cri_bound_up", "cri_bound_low"]
            .iter()
            .zip(&mut tables)
        {
            if integer(clip, &format!("/{key}_len"), 1, i32::MAX as i64)? as usize != n
                || at(clip, &format!("/{key}"))?.as_array().map(|a| a.len()) != Some(n)
            {
                return Err(format!("Clip table count mismatch"));
            }
            for i in 0..n {
                table.push(number(clip, &format!("/{key}/{i}"))?);
            }
        }
        ordered(&tables[0], "wbGainClip/cct")?;
        let n = integer(v, "/weightForNightGainCalc_len", 1, 255)? as usize;
        if at(v, "/weightForNightGainCalc")?
            .as_array()
            .map(|a| a.len())
            != Some(n)
        {
            return Err(format!("History weight count mismatch"));
        }
        let mut history_weights = Vec::new();
        for i in 0..n {
            history_weights
                .push(integer(v, &format!("/weightForNightGainCalc/{i}"), 0, 255)? as u8);
        }
        let mut brightness_knots = [0; 16];
        let mut night_percentages = [0; 16];
        for key in ["lumaValueMatrix", "defaultNightGainWeight"] {
            if at(v, &format!("/{key}"))?.as_array().map(|a| a.len()) != Some(16) {
                return Err(format!("Expected 16 {key} values"));
            }
        }
        for i in 0..16 {
            brightness_knots[i] =
                integer(v, &format!("/lumaValueMatrix/{i}"), 0, u32::MAX as i64)? as u32;
            night_percentages[i] =
                integer(v, &format!("/defaultNightGainWeight/{i}"), 0, 255)? as u8;
        }
        if brightness_knots.windows(2).any(|x| x[0] >= x[1]) {
            return Err(format!("Brightness knots must increase"));
        }
        let line = |key: &str| -> Result<Line, String> {
            let a: [f32; 3] = array(v, &format!("/{key}"))?;
            Ok(Line {
                a: a[0],
                b: a[1],
                c: a[2],
                valid: true,
            })
        };
        let mut environment_thresholds = [0; 4];
        for (i, key) in [
            "lumaValThLow",
            "lumaValThLow2",
            "lumaValThHigh",
            "lumaValThHigh2",
        ]
        .iter()
        .enumerate()
        {
            environment_thresholds[i] =
                integer(v, &format!("/division/{key}"), 0, u32::MAX as i64)? as u32;
        }
        Ok(Self {
            night_gain: array(v, "/defaultNightGain")?,
            lines: [line("lineRgBg")?, line("lineRgProjCCT")?],
            daylight_cct_minimum: number(v, "/wbGainDaylightClip/outdoor_cct_min")?,
            clip_tables: tables,
            remosaic_enabled: flag(v, "/remosaicCfg/enable")?,
            remosaic_inverse: flag(v, "/remosaicCfg/applyInvWbGainEnable")?,
            sensor_gain: array(v, "/remosaicCfg/sensorWbGain")?,
            history_weights,
            brightness_knots,
            night_percentages,
            environment_boundaries: core::array::from_fn(|i| {
                if i < 16 {
                    brightness_knots[i]
                } else {
                    environment_thresholds[0]
                }
            }),
            environment_thresholds,
            distance_thresholds: [
                number(v, "/probCalcDis/proDis_THL")?,
                number(v, "/probCalcDis/proDis_THH")?,
            ],
            probability_thresholds: [
                0,
                0,
                integer(v, "/probCalcLv/outdoorLumaValThLow", 0, u32::MAX as i64)? as u32,
                integer(v, "/probCalcLv/outdoorLumaValThHigh", 0, u32::MAX as i64)? as u32,
            ],
            relative_count_threshold: number(v, "/probCalcWp/wpNumPercTh2")?,
            damping: crate::awb_gain::DampingParameters {
                step: number(v, "/dampFactor/dFStep")?,
                minimum: number(v, "/dampFactor/dFMin")?,
                maximum: number(v, "/dampFactor/dFMax")?,
                variance_threshold: number(v, "/dampFactor/lvVarTh")?,
            },
            luma_history_target: integer(v, "/dampFactor/lvIIRsize", 0, i32::MAX as i64)? as i32,
            history_convergence: number(v, "/converged/varThforUnDamp")?,
            damped_convergence: number(v, "/converged/varThforDamp")?,
            stabilization: flag(v, "/xyRegionStableSelection/enable")?,
            region_history_target: integer(
                v,
                "/xyRegionStableSelection/xyTypeListSize",
                0,
                i32::MAX as i64,
            )? as i32,
            region_variance_threshold: number(v, "/xyRegionStableSelection/varianceLumaTh")?,
            initial_smart: [
                f32::from_bits(0x3a83126f),
                f32::from_bits(0x3ba3d70a),
                f32::from_bits(0x3d4ccccd),
            ],
            initial_countdown: 20,
        })
    }
    /// Native missing-exposure fallback reads strategy +0x188, knot index 8.
    pub fn fallback_brightness(&self) -> u32 {
        self.brightness_knots[8]
    }
    pub fn environment(&self) -> crate::awb_environment::Calibration<'_> {
        crate::awb_environment::Calibration {
            boundaries: &self.environment_boundaries,
            thresholds: self.environment_thresholds,
        }
    }
    pub fn high(&self, fast: bool, brightness: u32) -> crate::awb_high_gain::Settings {
        crate::awb_high_gain::Settings {
            fast,
            brightness,
            temporal_default: self.night_gain,
            temporal_knots: self.brightness_knots,
            temporal_percentages: self.night_percentages,
        }
    }
}

pub struct Curves<const N: usize> {
    pub knots: Vec<f32>,
    pub values: [Vec<f32>; N],
}
impl<const N: usize> Curves<N> {
    fn parse(v: &Value, keys: [&str; N]) -> Result<Self, String> {
        let n = integer(v, "/lumaValue_len", 1, i32::MAX as i64)? as usize;
        let read = |key: &str| -> Result<Vec<f32>, String> {
            if integer(v, &format!("/{key}_len"), 1, i32::MAX as i64)? as usize != n
                || at(v, &format!("/{key}"))?.as_array().map(|a| a.len()) != Some(n)
            {
                return Err(format!("Curve length mismatch at {key}"));
            }
            (0..n).map(|i| number(v, &format!("/{key}/{i}"))).collect()
        };
        let knots = read("lumaValue")?;
        if knots.windows(2).any(|x| x[0] >= x[1]) {
            return Err(format!("Curve knots must increase"));
        }
        let mut values = core::array::from_fn(|_| Vec::new());
        for (out, key) in values.iter_mut().zip(keys) {
            *out = read(key)?;
        }
        Ok(Self { knots, values })
    }
}
pub struct Preprocessing {
    pub smart_enabled: bool,
    pub smart: Curves<3>,
    pub interval: Curves<1>,
    pub tolerance: Curves<1>,
    /// Native strategy order high then low, not JSON field declaration order.
    pub points: Curves<2>,
    pub regions: Curves<2>,
}
impl Preprocessing {
    pub fn from_value(v: &Value) -> Result<Self, String> {
        let smart = at(v, "/smartRun")?;
        let interval = Curves::parse(at(v, "/runInterval")?, ["intervalValue"])?;
        let tolerance = Curves::parse(at(v, "/tolerance")?, ["toleranceValue"])?;
        if interval.knots.len() > 8 || tolerance.knots.len() > 8 {
            return Err(format!(
                "Inline interval/tolerance tables exceed eight entries"
            ));
        }
        Ok(Self {
            smart_enabled: flag(smart, "/enable")?,
            smart: Curves::parse(
                at(smart, "/cfg")?,
                ["lvVarTh", "wbgainAlgDiffTh", "wbgainHwDiffTh"],
            )?,
            interval,
            tolerance,
            points: Curves::parse(at(v, "/division/wpNumTh")?, ["high", "low"])?,
            regions: Curves::parse(
                at(v, "/xyRegionStableSelection/wpNumTh")?,
                ["forBigType", "forExtraType"],
            )?,
        })
    }
    pub fn calibration(&self) -> crate::awb_preprocess::Calibration<'_> {
        crate::awb_preprocess::Calibration {
            smart_knots: &self.smart.knots,
            smart: core::array::from_fn(|i| &self.smart.values[i][..]),
            interval: crate::awb_preprocess::Curve {
                knots: &self.interval.knots,
                values: &self.interval.values[0],
            },
            point_knots: &self.points.knots,
            points: core::array::from_fn(|i| &self.points.values[i][..]),
            region_knots: &self.regions.knots,
            regions: core::array::from_fn(|i| &self.regions.values[i][..]),
        }
    }
    pub fn tolerance(&self, brightness: u32) -> Result<f32, crate::InvalidInput> {
        crate::interpolate(
            &self.tolerance.knots,
            &self.tolerance.values[0],
            brightness as f32,
        )
    }
}

pub struct OptionalProcessing {
    pub bounds_enabled: bool,
    pub daylight_enabled: bool,
    pub adjustment_enabled: bool,
    pub temperature_mode: bool,
    pub sample_from_luma: bool,
    pub luts: Vec<crate::awb_gain_adjust::Lut>,
    pub offsets: Option<[f32; 4]>,
}
impl OptionalProcessing {
    pub fn from_value(v: &Value) -> Result<Self, String> {
        let a = at(v, "/wbGainAdjust")?;
        let temperature_mode = match at(a, "/adjDataSelt")?.as_str() {
            Some("AWB_GAIN_ADJ_DATA_GAIN") => false,
            Some("AWB_GAIN_ADJ_DATA_CT") => true,
            _ => return Err(format!("Unknown adjustment data selector")),
        };
        let sample_from_luma = match at(a, "/ctrlDataSelt")?.as_str() {
            Some("AWB_CTRL_DATA_LV") => true,
            Some("AWB_CTRL_DATA_ISO") => false,
            _ => return Err(format!("Unknown adjustment control selector")),
        };
        let n = integer(a, "/lutAll_len", 1, 8)? as usize;
        let values = at(a, "/lutAll")?
            .as_array()
            .ok_or_else(|| format!("Expected adjustment LUT array"))?;
        if values.len() != n {
            return Err(format!("Adjustment LUT length mismatch"));
        }
        let mut luts = Vec::new();
        for v in values {
            let lut = crate::awb_gain_adjust::Lut {
                sample: number(v, "/ctlData")?,
                x: array(v, "/rgct_in_ds")?,
                y: array(v, "/bgcri_in_ds")?,
                mapped_x: array(v, "/rgct_lut_out")?,
                mapped_y: array(v, "/bgcri_lut_out")?,
            };
            for axis in [&lut.x[..], &lut.y[..]] {
                let descending = axis[axis.len() - 1] < axis[0];
                if axis.windows(2).any(|p| {
                    if descending {
                        p[0] <= p[1]
                    } else {
                        p[0] >= p[1]
                    }
                }) {
                    return Err(format!("Adjustment axis must be strictly monotone"));
                }
            }
            luts.push(lut);
        }
        if luts.windows(2).any(|p| p[0].sample > p[1].sample) {
            return Err(format!("Adjustment sample levels must not descend"));
        }
        let offsets = array(v, "/wbGainOffset/offset")?;
        Ok(Self {
            bounds_enabled: flag(v, "/wbGainClip/enable")?,
            daylight_enabled: flag(v, "/wbGainDaylightClip/enable")?,
            adjustment_enabled: flag(a, "/enable")?,
            temperature_mode,
            sample_from_luma,
            luts,
            offsets: if flag(v, "/wbGainOffset/enable")? {
                Some(offsets)
            } else {
                None
            },
        })
    }
}
/// One explicitly selected wb_v32 scene. File I/O and initial persistent state
/// remain external; this owns the numerical settings rather than picking scenes.
pub struct Scene {
    pub lights: Lights,
    pub single: SingleColor,
    pub common: Common,
    pub preprocessing: Preprocessing,
    pub optional: OptionalProcessing,
    pub site: crate::awb_site::Settings,
    pub site_path: String,
}
impl Scene {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let ext = at(wb, "/autoExtPara")?;
        let site = at(ext, "/avaSiteRec")?;
        let path = at(site, "/fullFileName")?
            .as_str()
            .ok_or_else(|| format!("Expected saved-site path"))?;
        if path.as_bytes().contains(&0) {
            return Err(format!("Saved-site path contains NUL"));
        }
        Ok(Self {
            lights: Lights::from_value(wb)?,
            single: SingleColor::from_value(at(ext, "/singleColorProces")?)?,
            common: Common::from_value(ext)?,
            preprocessing: Preprocessing::from_value(ext)?,
            optional: OptionalProcessing::from_value(ext)?,
            site: crate::awb_site::Settings {
                enabled: flag(site, "/enable")?,
                frame_limit: integer(site, "/frameNum", 0, u32::MAX as i64)? as u32,
                reuse_enabled: flag(site, "/avaEnable")?,
                gain_threshold: number(site, "/wbgainTh")?,
                sample_threshold: number(site, "/lvValueTh")?,
            },
            site_path: path.to_string(),
        })
    }
    /// Build borrowed postprocessing settings inside their valid lifetime.
    /// The wrapper supplies the current smart-run damping threshold and samples.
    pub fn with_post_settings<R>(
        &self,
        brightness: u32,
        luma_sample: f32,
        iso: f32,
        damping_threshold: f32,
        run: impl FnOnce(&crate::awb_postprocess::Settings<'_>) -> R,
    ) -> Result<R, crate::InvalidInput> {
        let clip = crate::awb_gain_clip::Calibration {
            first: self.common.lines[0],
            second: self.common.lines[1],
            daylight: self.optional.daylight_enabled,
            daylight_threshold: self.common.probability_thresholds[3],
            daylight_minimum_cct: self.common.daylight_cct_minimum,
            bounds: if self.optional.bounds_enabled {
                Some(crate::awb_gain_clip::Bounds {
                    cct: &self.common.clip_tables[0],
                    negative_tint: &self.common.clip_tables[1],
                    positive_tint: &self.common.clip_tables[2],
                })
            } else {
                None
            },
        };
        let adjustment = crate::awb_gain_adjust::Settings {
            temperature_mode: self.optional.temperature_mode,
            sample: if self.optional.sample_from_luma {
                luma_sample
            } else {
                iso
            },
            first: self.common.lines[0],
            second: self.common.lines[1],
        };
        let post = crate::awb_postprocess::Settings {
            history_target: self.common.history_weights.len() as i32,
            tolerance: self.preprocessing.tolerance(brightness)?,
            history_convergence: self.common.history_convergence,
            damped_convergence: self.common.damped_convergence,
            damping_threshold,
            brightness,
            clipping: if self.optional.daylight_enabled || self.optional.bounds_enabled {
                Some(&clip)
            } else {
                None
            },
            adjustment: if self.optional.adjustment_enabled {
                Some(crate::awb_postprocess::Adjustment {
                    luts: &self.optional.luts,
                    settings: &adjustment,
                })
            } else {
                None
            },
            offsets: self.optional.offsets,
            first: self.common.lines[0],
            second: self.common.lines[1],
        };
        Ok(run(&post))
    }
}

/// Values produced by preprocessing or held in the live session, not IQ tuning.
#[derive(Clone, Copy)]
pub struct GainRuntime<'a> {
    pub active_lights: usize,
    pub numeric: &'a crate::awb_preprocess::State,
    pub variance: f32,
    pub environment: usize,
    pub fast: bool,
    pub absolute_count_threshold: f32,
    pub extra_enabled: &'a [bool],
    pub grid_valid: bool,
    pub grid: &'a [[f32; 3]; 225],
    pub site_input: &'a crate::awb_site::Input,
    pub iso: f32,
    pub scale: Option<[f32; 2]>,
}
impl Scene {
    /// Configure the complete joined gain-frame path from owned scene data.
    /// Measurement geometry/count thresholds and runtime flags remain explicit.
    pub fn process_gain_frame<const CAP: usize>(
        &self,
        state: &mut crate::awb_gain_frame::State<CAP>,
        update: bool,
        frame: &crate::awb_gain_controller::Frame,
        records: &[crate::awb_preparation::LightRecord],
        output: &mut [crate::awb_gain_controller::LightResult],
        runtime: &GainRuntime<'_>,
    ) -> Result<crate::awb_dispatch::Action, crate::InvalidInput> {
        if !update || !frame.complete {
            return state.dispatch.process(
                update,
                false,
                &mut state.controller.post.current,
                runtime.scale,
                |_| unreachable!(),
            );
        }
        let n = runtime.active_lights;
        if n < 4
            || n > self.lights.entries.len()
            || records.len() < n
            || output.len() != n
            || runtime.extra_enabled.len() < n
        {
            return Err(crate::InvalidInput::Length);
        }
        let lights: Vec<_> = self.lights.entries[..n]
            .iter()
            .zip(&runtime.extra_enabled[..n])
            .map(|(light, &extra)| light.controller_light(runtime.environment, extra))
            .collect::<Result<_, _>>()?;
        let numeric = runtime.numeric;
        let region = crate::awb_xy_selection::Settings {
            absolute: runtime.absolute_count_threshold,
            relative: self.common.relative_count_threshold,
            region_thresholds: numeric.regions,
            count_thresholds: numeric.points,
            stabilization: self.common.stabilization,
            target: self.common.region_history_target,
            variance: runtime.variance,
            variance_threshold: self.common.region_variance_threshold,
        };
        let probability = crate::awb_probability::Settings {
            gain: state.controller.post.current,
            frame: state.dispatch.frame,
            fast: runtime.fast,
            near_distance_squared: self.common.distance_thresholds[0],
            far_distance_squared: self.common.distance_thresholds[1],
            brightness: numeric.luma_integer,
            brightness_thresholds: self.common.probability_thresholds,
            prior_sample: numeric.luma,
            absolute_count_threshold: region.absolute,
            relative_count_threshold: region.relative,
        };
        let high = self.common.high(runtime.fast, numeric.luma_integer);
        let low = crate::awb_low_gain::Settings {
            retained: 0,
            count_threshold: numeric.points[0],
            brightness: numeric.luma_integer,
            low_brightness: self.common.environment_thresholds[0],
            high_brightness: self.common.environment_thresholds[3],
            temporal_default: self.common.night_gain,
            color_history_value: self.single.candidates.len() as i32,
            color_history_target: self.single.history_target,
        };
        let classifier = self
            .single
            .classifier(self.common.lines[0], self.common.lines[1]);
        let single = if self.single.enabled {
            Some(crate::awb_low_single_color::Input {
                mode: self.single.mode,
                grid_valid: runtime.grid_valid,
                grid: runtime.grid,
                classifier: &classifier,
                confidence: &self.single.confidence,
                brightness_sample: numeric.luma,
                density: 0.,
                acceptance_threshold: self.single.acceptance_threshold,
                estimated_gain: [0.; 4],
                high_history: &[],
            })
        } else {
            None
        };
        self.with_post_settings(
            numeric.luma_integer,
            numeric.luma,
            runtime.iso,
            numeric.smart[1],
            |post| {
                let settings = crate::awb_gain_controller::Settings {
                    mode: self.single.mode,
                    region: &region,
                    probability,
                    high: &high,
                    low: &low,
                    single,
                    post,
                    high_history_threshold: self.single.high_history_threshold,
                    estimated_density_threshold: self.single.estimated_density_threshold,
                    estimated_single_threshold: self.single.estimated_single_threshold,
                };
                let controls = crate::awb_wrapper::Controls {
                    damping: self.common.damping,
                    variance: runtime.variance,
                    tolerance_knots: &self.preprocessing.tolerance.knots,
                    tolerance_values: &self.preprocessing.tolerance.values[0],
                    site: &self.site,
                    site_input: runtime.site_input,
                };
                state.process(
                    update,
                    frame,
                    &records[..n],
                    &lights,
                    output,
                    &settings,
                    &controls,
                    runtime.scale,
                )
            },
        )?
    }
}

impl Scene {
    /// Prepare raw SDK measurements and process their caches as one transition.
    /// Borrowed buffers are copied into staging, including inactive cache data;
    /// any preparation/gain/scaling error discards all changes.
    pub fn prepare_gain_frame<const CAP: usize>(
        &self,
        state: &mut crate::awb_gain_frame::State<CAP>,
        measurements: &mut crate::awb_preparation::State<'_>,
        raw: &crate::awb_preparation::Frame<'_>,
        preparation: &crate::awb_preparation::Settings<'_>,
        divisors: [u32; 2],
        output: &mut [crate::awb_gain_controller::LightResult],
        runtime: &GainRuntime<'_>,
    ) -> Result<crate::awb_dispatch::Action, crate::InvalidInput> {
        if measurements.lights.len() != self.lights.entries.len() {
            return Err(crate::InvalidInput::Length);
        }
        let mut seen = measurements.seen.to_vec();
        let mut lights = measurements.lights.to_vec();
        let mut second = measurements.second_counts.to_vec();
        let mut totals = measurements.total_counts.to_vec();
        let mut grid = *measurements.grid;
        let mut staged = crate::awb_preparation::State {
            update: measurements.update,
            stability_mask: measurements.stability_mask,
            history: measurements.history,
            mode_names: measurements.mode_names,
            seen: &mut seen,
            active_lights: measurements.active_lights,
            complete: measurements.complete,
            lights: &mut lights,
            second_counts: &mut second,
            total_counts: &mut totals,
            previous_pre_gain: measurements.previous_pre_gain,
            grid_valid: measurements.grid_valid,
            second_grid_valid: measurements.second_grid_valid,
            grid: &mut grid,
            exclusions_valid: measurements.exclusions_valid,
            exclusions: measurements.exclusions,
            exclusion_aggregate: measurements.exclusion_aggregate,
            histogram_cache: measurements.histogram_cache,
            histogram_aggregate: measurements.histogram_aggregate,
        };
        staged.update = runtime.numeric.update;
        let preparation = crate::awb_preparation::Settings {
            stability_threshold: runtime.numeric.smart[2],
            prior_sample: runtime.numeric.luma,
            ..*preparation
        };
        crate::awb_preparation::prepare(&mut staged, raw, &preparation)?;
        let active = staged.active_lights as usize;
        let frame = staged.gain_frame(divisors);
        let effective = GainRuntime {
            active_lights: active,
            fast: raw.fast()?,
            grid_valid: staged.grid_valid,
            grid: &*staged.grid,
            scale: runtime
                .scale
                .map(|_| [staged.previous_pre_gain[0], staged.previous_pre_gain[3]]),
            ..*runtime
        };
        let active_output = output
            .get_mut(..active)
            .ok_or(crate::InvalidInput::Length)?;
        let action = self.process_gain_frame(
            state,
            staged.update,
            &frame,
            staged.lights,
            active_output,
            &effective,
        )?;
        measurements.update = staged.update;
        measurements.stability_mask = staged.stability_mask;
        measurements.history = staged.history;
        measurements.mode_names = staged.mode_names;
        measurements.active_lights = staged.active_lights;
        measurements.complete = staged.complete;
        measurements.seen.copy_from_slice(staged.seen);
        measurements.lights.copy_from_slice(staged.lights);
        measurements
            .second_counts
            .copy_from_slice(staged.second_counts);
        measurements
            .total_counts
            .copy_from_slice(staged.total_counts);
        measurements.previous_pre_gain = staged.previous_pre_gain;
        measurements.grid_valid = staged.grid_valid;
        measurements.second_grid_valid = staged.second_grid_valid;
        measurements.grid.copy_from_slice(staged.grid);
        measurements.exclusions_valid = staged.exclusions_valid;
        measurements.exclusions = staged.exclusions;
        measurements.exclusion_aggregate = staged.exclusion_aggregate;
        measurements.histogram_cache = staged.histogram_cache;
        measurements.histogram_aggregate = staged.histogram_aggregate;
        Ok(action)
    }
}

/// Calibrated UV, XY and rotated-YUV detection records for each scene light.
/// Complete hardware-record assembly remains separate initialization.
pub struct MeasurementRegions {
    pub uv: Vec<[u8; 36]>,
    pub xy: Vec<[u8; 48]>,
    pub rotated_yuv: Vec<[u8; 32]>,
}
impl MeasurementRegions {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let lights = at(wb, "/autoPara/lightSources")?
            .as_array()
            .ok_or_else(|| format!("Expected lightSources array"))?;
        if integer(wb, "/autoPara/lightSources_len", 1, 255)? as usize != lights.len() {
            return Err(format!("Light count mismatch"));
        }
        let array = |v: &Value, path: &str, count: usize| -> Result<Vec<f32>, String> {
            if at(v, path)?.as_array().map(Vec::len) != Some(count) {
                return Err(format!("Invalid detection region array {path}"));
            }
            (0..count)
                .map(|i| number(v, &format!("{path}/{i}")))
                .collect()
        };
        let mut xy = Vec::new();
        let mut rotated_yuv = Vec::new();
        let mut uv = Vec::new();
        for light in lights {
            let mut polygon = [0; 36];
            crate::awb_measurement_regions::uv(
                &array(light, "/uvRegion/u", 4)?.try_into().unwrap(),
                &array(light, "/uvRegion/v", 4)?.try_into().unwrap(),
                &mut polygon,
            )
            .map_err(|e| format!("UV detection region: {e:?}"))?;
            uv.push(polygon);
            let mut values = array(light, "/xyRegion/normal", 4)?;
            values.extend(array(light, "/xyRegion/big", 4)?);
            let mut record = [0; 48];
            crate::awb_measurement_regions::xy(&values.try_into().unwrap(), &mut record)
                .map_err(|e| format!("XY detection region: {e:?}"))?;
            xy.push(record);
            let input = crate::awb_measurement_regions::RotatedYuv {
                u: array(light, "/rtYuvRegion/thcurve_u", 6)?
                    .try_into()
                    .unwrap(),
                threshold: array(light, "/rtYuvRegion/thcure_th", 6)?
                    .try_into()
                    .unwrap(),
                line: array(light, "/rtYuvRegion/lineVector", 6)?
                    .try_into()
                    .unwrap(),
                distance: integer(light, "/rtYuvRegion/disP1P2", 0, 255)? as u8,
            };
            let mut record = [0; 32];
            crate::awb_measurement_regions::rotated_yuv(&input, &mut record)
                .map_err(|e| format!("Rotated-YUV detection region: {e:?}"))?;
            rotated_yuv.push(record);
        }
        Ok(Self {
            uv,
            xy,
            rotated_yuv,
        })
    }
}

pub struct MeasurementTransforms {
    pub xy: [u8; 24],
    pub rotated_yuv: [u8; 24],
}
impl MeasurementTransforms {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let array = |path: &str, count: usize| -> Result<Vec<f32>, String> {
            if at(wb, path)?.as_array().map(Vec::len) != Some(count) {
                return Err(format!("Invalid measurement transform {path}"));
            }
            (0..count)
                .map(|i| number(wb, &format!("{path}/{i}")))
                .collect()
        };
        let weights = array("/autoPara/rgb2TcsPara/pseudoLuminanceWeight", 3)?;
        let rotation = array("/autoPara/rgb2TcsPara/rotationMat", 9)?;
        let matrix = array("/autoPara/rgb2RotationYuvMat", 16)?;
        let mut xy = [0; 24];
        let mut rotated_yuv = [0; 24];
        crate::awb_measurement_transforms::xy(
            &weights.try_into().unwrap(),
            &rotation.try_into().unwrap(),
            &mut xy,
        )
        .map_err(|e| format!("XY transform: {e:?}"))?;
        crate::awb_measurement_transforms::rotated_yuv(
            &matrix.try_into().unwrap(),
            &mut rotated_yuv,
        )
        .map_err(|e| format!("Rotated-YUV transform: {e:?}"))?;
        Ok(Self { xy, rotated_yuv })
    }
}

pub struct MeasurementGeometry {
    pub manual_window: Option<[f32; 4]>,
    pub downsample: u32,
    pub count_fraction: f32,
    pub luma_weight_fraction: f32,
}
impl MeasurementGeometry {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let main = at(wb, "/autoPara/mainWindow")?;
        let manual_window = match at(main, "/mode")?.as_str() {
            Some("CALIB_AWB_WINDOW_CFG_AUTO") => None,
            Some("CALIB_AWB_WINDOW_CFG_FIXED") => {
                if at(main, "/window")?.as_array().map(Vec::len) != Some(4) {
                    return Err(format!("Expected four window coordinates"));
                }
                let mut window = [0.; 4];
                for (i, out) in window.iter_mut().enumerate() {
                    *out = number(main, &format!("/window/{i}"))?;
                }
                Some(window)
            }
            _ => return Err(format!("Unknown AWB window mode")),
        };
        let downsample = match at(wb, "/autoPara/downScaleMode")?.as_str() {
            Some("CALIB_AWB_DS_4X4") => 0,
            Some("CALIB_AWB_DS_8X8") => 1,
            _ => return Err(format!("Unknown AWB downscale mode")),
        };
        Ok(Self {
            manual_window,
            downsample,
            count_fraction: number(wb, "/autoExtPara/probCalcWp/wpNumPercTh")?,
            luma_weight_fraction: number(
                wb,
                "/autoPara/wpDiffLumaWeight/wpDiffWeiEnableTh/wpDiffWeiNoTh",
            )?,
        })
    }
    /// Multiwindow inputs remain explicit; the v32 scene has no multiWindow field.
    pub fn derive(
        &self,
        dimensions: [u32; 2],
        sample_scale: u32,
        multiwindow: Option<[[f32; 4]; 4]>,
    ) -> Result<crate::awb_measurement_geometry::Geometry, crate::InvalidInput> {
        crate::awb_measurement_geometry::derive(&crate::awb_measurement_geometry::Input {
            dimensions,
            sample_scale,
            multiwindow,
            manual_window: self.manual_window,
            downsample: self.downsample,
            count_fraction: self.count_fraction,
            luma_weight_fraction: self.luma_weight_fraction,
        })
    }
}

pub struct MeasurementLimits {
    pub knots: Vec<f32>,
    pub values: [Vec<f32>; 8],
}
impl MeasurementLimits {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let v = at(wb, "/autoPara/limitRange")?;
        let count = integer(v, "/lumaValue_len", 1, i32::MAX as i64)? as usize;
        let read = |name: &str| -> Result<Vec<f32>, String> {
            if integer(v, &format!("/{name}_len"), 1, i32::MAX as i64)? as usize != count
                || at(v, &format!("/{name}"))?.as_array().map(Vec::len) != Some(count)
            {
                return Err(format!("Limit table length mismatch: {name}"));
            }
            (0..count)
                .map(|i| number(v, &format!("/{name}/{i}")))
                .collect()
        };
        let knots = read("lumaValue")?;
        if knots.windows(2).any(|p| p[0] >= p[1]) {
            return Err(format!("Limit knots must increase"));
        }
        let mut values: [Vec<f32>; 8] = core::array::from_fn(|_| Vec::new());
        for (i, key) in [
            "maxR", "minR", "maxG", "minG", "maxB", "minB", "maxY", "minY",
        ]
        .iter()
        .enumerate()
        {
            values[i] = read(key)?;
            for n in &mut values[i] {
                *n *= 16.;
                if !n.is_finite() {
                    return Err(format!("Limit Q4 conversion overflow"));
                }
            }
        }
        Ok(Self { knots, values })
    }
    pub fn apply(
        &self,
        brightness: u32,
        record: &mut [u8; crate::isp_awb_measurement::INPUT_BYTES],
    ) -> Result<bool, crate::InvalidInput> {
        crate::awb_measurement_limits::Limits {
            knots: &self.knots,
            values: core::array::from_fn(|i| &self.values[i][..]),
        }
        .apply(brightness, record)
    }
}

pub struct MeasurementInput {
    pub source: crate::awb_input_selection::Source,
    pub frame: u8,
}
impl MeasurementInput {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        use crate::awb_input_selection::Source;
        let v = at(wb, "/autoPara/rawSelectPara")?;
        let source = match at(v, "/frameChooseMode")?.as_str() {
            Some("CALIB_AWB_INPUT_RAW_FIXED") => Source::RawFixed,
            Some("CALIB_AWB_INPUT_RAW_AUTO") => Source::RawAuto,
            Some("CALIB_AWB_INPUT_BAYERNR") => Source::BayerNr,
            Some("CALIB_AWB_INPUT_DRC") => Source::Drc,
            _ => return Err(format!("Unknown AWB input source")),
        };
        Ok(Self {
            source,
            frame: integer(v, "/frameChoose", 0, 255)? as u8,
        })
    }
    pub fn apply(
        &self,
        record: &mut [u8; crate::isp_awb_measurement::INPUT_BYTES],
        working_mode: u32,
        blc_pre_gain: Option<f32>,
    ) -> Result<(), crate::InvalidInput> {
        crate::awb_input_selection::configure(
            record,
            self.source,
            self.frame,
            working_mode,
            blc_pre_gain,
        )
    }
}

pub struct WeightingLevel {
    pub brightness: f32,
    pub ratios: Vec<f32>,
    pub weights: Vec<[f32; 9]>,
}
pub struct MeasurementWeighting {
    pub enabled: bool,
    pub block_enabled: bool,
    pub block: [u8; 225],
    pub y: [u8; 9],
    pub perfect: [bool; 8],
    pub minimum_brightness: u32,
    pub levels: Vec<WeightingLevel>,
}
impl MeasurementWeighting {
    pub fn from_value(wb: &Value) -> Result<Self, String> {
        let auto = at(wb, "/autoPara")?;
        let v = at(auto, "/wpDiffLumaWeight")?;
        let exact = |v: &Value, path: &str, n: usize| -> Result<(), String> {
            if at(v, path)?.as_array().map(Vec::len) == Some(n) {
                Ok(())
            } else {
                Err(format!("Invalid weight array {path}"))
            }
        };
        exact(auto, "/wpDiffBlkWeight", 225)?;
        exact(v, "/wpDiffwei_y", 9)?;
        exact(v, "/perfectBin", 8)?;
        let mut block = [0; 225];
        for (i, n) in block.iter_mut().enumerate() {
            *n = integer(auto, &format!("/wpDiffBlkWeight/{i}"), 0, 65535)? as u8;
        }
        let mut y = [0; 9];
        for (i, n) in y.iter_mut().enumerate() {
            *n = integer(v, &format!("/wpDiffwei_y/{i}"), 0, 255)? as u8;
        }
        let mut perfect = [false; 8];
        for (i, n) in perfect.iter_mut().enumerate() {
            *n = flag(v, &format!("/perfectBin/{i}"))?;
        }
        let count = integer(v, "/wpDiffWeightLvSet_len", 1, i32::MAX as i64)? as usize;
        exact(v, "/wpDiffWeightLvSet", count)?;
        let mut levels: Vec<WeightingLevel> = Vec::new();
        for i in 0..count {
            let level = at(v, &format!("/wpDiffWeightLvSet/{i}"))?;
            let brightness = number(level, "/LvValue")?;
            if levels.last().is_some_and(|p| p.brightness >= brightness) {
                return Err(format!("Weight brightness knots must increase"));
            }
            let n = integer(level, "/ratioSet_len", 1, i32::MAX as i64)? as usize;
            exact(level, "/ratioSet", n)?;
            let mut ratios: Vec<f32> = Vec::new();
            let mut weights = Vec::new();
            for j in 0..n {
                let ratio = at(level, &format!("/ratioSet/{j}"))?;
                let value = number(ratio, "/ratioValue")?;
                if ratios.last().is_some_and(|p| *p >= value) {
                    return Err(format!("Weight ratio knots must increase"));
                }
                exact(ratio, "/weight", 9)?;
                let mut row = [0.; 9];
                for (k, n) in row.iter_mut().enumerate() {
                    *n = number(ratio, &format!("/weight/{k}"))?;
                }
                ratios.push(value);
                weights.push(row);
            }
            levels.push(WeightingLevel {
                brightness,
                ratios,
                weights,
            });
        }
        Ok(Self {
            enabled: flag(v, "/enable")?,
            block_enabled: flag(auto, "/wpDiffBlkWeiEnable")?,
            block,
            y,
            perfect,
            minimum_brightness: integer(
                v,
                "/wpDiffWeiEnableTh/wpDiffWeiLvValueTh",
                0,
                u32::MAX as i64,
            )? as u32,
            levels,
        })
    }
    pub fn apply(
        &self,
        record: &mut [u8; crate::isp_awb_measurement::INPUT_BYTES],
        previous: &mut [f32; 9],
        input: &crate::awb_measurement_weights::Input,
    ) -> Result<bool, crate::InvalidInput> {
        let rows: Vec<_> = self
            .levels
            .iter()
            .map(|r| crate::awb_measurement_weights::Row {
                brightness: r.brightness,
                ratios: &r.ratios,
                weights: &r.weights,
            })
            .collect();
        crate::awb_measurement_weights::apply(
            record,
            previous,
            &rows,
            &crate::awb_measurement_weights::Input {
                perfect: self.perfect,
                minimum_brightness: self.minimum_brightness,
                ..*input
            },
        )
    }
}

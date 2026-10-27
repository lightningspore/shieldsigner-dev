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

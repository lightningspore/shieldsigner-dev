//! The exposure subset of SDK IQ JSON. Other ISP/3A tuning remains unparsed.
extern crate alloc;
use crate::exposure::{self, Calibration, GainBand, GainModel, Timing};
use alloc::{
    format,
    string::{String, ToString},
    vec::Vec,
};
use serde_json::Value;
#[derive(Clone, Debug)]
pub struct SensorCalibration {
    pub width: u32,
    pub height: u32,
    pub logarithmic_gain: bool,
    pub bands: Vec<GainBand>,
    pub factors: [f32; 4],
    pub linear: Timing,
    pub hdr: [Timing; 2],
    pub linear_max_factors: [f32; 2],
    pub linear_dcg_supported: bool,
    pub hdr_dcg_supported: bool,
    pub linear_dcg_ratio: f32,
    pub hdr_dcg_ratio: f32,
    pub analogue_range: [f32; 2],
    pub digital_range: [f32; 2],
    pub isp_gain_range: [f32; 2],
    pub linear_update_delays: [u32; 3],
}
#[derive(Clone, Copy, Debug)]
pub struct RuntimeTiming {
    pub frame_length: u32,
    pub pixel_clock_mhz: f32,
    pub line_length_pixels: u32,
}
fn at<'a>(value: &'a Value, path: &str) -> Result<&'a Value, String> {
    value
        .pointer(path)
        .ok_or_else(|| format!("Missing IQ field {path}"))
}
fn number(value: &Value, path: &str) -> Result<f32, String> {
    let n = at(value, path)?
        .as_f64()
        .ok_or_else(|| format!("Expected number at {path}"))? as f32;
    if !n.is_finite() {
        return Err(format!("Nonfinite/out-of-range number at {path}"));
    }
    Ok(n)
}
fn integer(value: &Value, path: &str, maximum: u32) -> Result<u32, String> {
    let n = at(value, path)?
        .as_f64()
        .ok_or_else(|| format!("Expected integer at {path}"))?;
    if n < 0. || n > maximum as f64 || n.fract() != 0. {
        return Err(format!("Integer out of range at {path}"));
    }
    Ok(n as u32)
}
fn flag(value: &Value, path: &str) -> Result<bool, String> {
    if let Some(v) = at(value, path)?.as_bool() {
        Ok(v)
    } else {
        Ok(integer(value, path, 1)? != 0)
    }
}
fn array<const N: usize>(value: &Value, path: &str) -> Result<[f32; N], String> {
    let values = at(value, path)?
        .as_array()
        .ok_or_else(|| format!("Expected array at {path}"))?;
    if values.len() != N {
        return Err(format!("Expected {N} values at {path}"));
    }
    let mut out = [0.; N];
    for (i, item) in out.iter_mut().enumerate() {
        *item = number(value, &format!("{path}/{i}"))?;
    }
    Ok(out)
}
fn timing(value: &Value, path: &str) -> Result<Timing, String> {
    let coefficients = array::<2>(value, &format!("{path}/CISTimeRegOdevity/fCoeff"))?;
    Ok(Timing {
        minimum: integer(value, &format!("{path}/CISTimeRegMin"), u16::MAX as u32)? as u16,
        step: coefficients[0],
        offset: coefficients[1],
    })
}
fn range(value: &Value, path: &str) -> Result<[f32; 2], String> {
    let limits = [
        number(value, &format!("{path}/Min"))?,
        number(value, &format!("{path}/Max"))?,
    ];
    if limits[0] < 0. || limits[0] > limits[1] {
        return Err(format!("Invalid gain range at {path}"));
    }
    Ok(limits)
}
impl SensorCalibration {
    pub fn from_json(text: &str) -> Result<Self, String> {
        let value: Value = serde_json::from_str(text).map_err(|e| e.to_string())?;
        Self::from_value(&value)
    }
    pub fn from_value(value: &Value) -> Result<Self, String> {
        let value = at(value, "/sensor_calib")?;
        let logarithmic_gain = match at(value, "/Gain2Reg/GainMode")?.as_str() {
            Some("EXPGAIN_MODE_LINEAR") => false,
            Some("EXPGAIN_MODE_NONLINEAR_DB") => true,
            _ => return Err("Unsupported IQ Gain2Reg/GainMode".into()),
        };
        let entries = at(value, "/Gain2Reg/GainRange")?
            .as_array()
            .ok_or("Expected GainRange array")?;
        if integer(value, "/Gain2Reg/GainRange_len", 100000)? as usize != entries.len()
            || entries.len() % 7 != 0
        {
            return Err("GainRange length must match its declaration and contain complete seven-value bands".into());
        }
        let mut bands = Vec::new();
        for i in (0..entries.len()).step_by(7) {
            let mut row = [0.; 7];
            for (j, item) in row.iter_mut().enumerate() {
                *item = number(value, &format!("/Gain2Reg/GainRange/{}", i + j))?;
            }
            if row[0] > row[1] || row[5] < 0. || row[5] > row[6] {
                return Err("Invalid gain-band bounds".into());
            }
            bands.push(GainBand {
                lower: row[0],
                upper: row[1],
                scale: row[2],
                offset: row[3],
                exponent: row[4],
                minimum: row[5],
                maximum: row[6],
            });
        }
        let width = integer(value, "/resolution/width", u32::MAX)?;
        let height = integer(value, "/resolution/height", u32::MAX)?;
        if width == 0 || height == 0 {
            return Err("IQ sensor resolution must be nonzero".into());
        }
        let linear = timing(value, "/CISTimeSet/Linear")?;
        if linear.step <= 0. {
            return Err("Linear time-register step must be positive".into());
        }
        if at(value, "/CISTimeSet/Hdr/0/name")?.as_str() != Some("HDR_TWO_FRAME")
            || at(value, "/CISTimeSet/Hdr/1/name")?.as_str() != Some("HDR_THREE_FRAME")
        {
            return Err("Unexpected HDR timing record order".into());
        }
        let hdr = [
            timing(value, "/CISTimeSet/Hdr/0")?,
            timing(value, "/CISTimeSet/Hdr/1")?,
        ];
        let linear_dcg_supported = flag(value, "/CISDcgSet/Linear/support_en")?;
        let hdr_dcg_supported = flag(value, "/CISDcgSet/Hdr/support_en")?;
        let linear_dcg_ratio = number(value, "/CISDcgSet/Linear/dcg_ratio")?;
        let hdr_dcg_ratio = number(value, "/CISDcgSet/Hdr/dcg_ratio")?;
        if (linear_dcg_supported && linear_dcg_ratio <= 0.)
            || (hdr_dcg_supported && hdr_dcg_ratio <= 0.)
        {
            return Err("Supported DCG mode requires a positive ratio".into());
        }
        Ok(Self {
            width,
            height,
            logarithmic_gain,
            bands,
            factors: array(value, "/Time2Reg/fCoeff")?,
            linear,
            hdr,
            linear_max_factors: array(value, "/CISTimeSet/Linear/CISLinTimeRegMaxFac/fCoeff")?,
            linear_dcg_supported,
            hdr_dcg_supported,
            linear_dcg_ratio,
            hdr_dcg_ratio,
            analogue_range: range(value, "/CISGainSet/CISAgainRange")?,
            digital_range: range(value, "/CISGainSet/CISDgainRange")?,
            isp_gain_range: range(value, "/CISGainSet/CISIspDgainRange")?,
            linear_update_delays: [
                integer(value, "/CISExpUpdate/Linear/time_update", u32::MAX)?,
                integer(value, "/CISExpUpdate/Linear/gain_update", u32::MAX)?,
                integer(value, "/CISExpUpdate/Linear/dcg_update", u32::MAX)?,
            ],
        })
    }
    pub fn conversion(&self, timing: RuntimeTiming) -> Calibration<'_> {
        Calibration {
            gain: if self.logarithmic_gain {
                GainModel::Logarithmic
            } else {
                GainModel::Bands(&self.bands)
            },
            factors: self.factors,
            frame_length: timing.frame_length as f32,
            pixel_clock_mhz: timing.pixel_clock_mhz,
            line_length_pixels: timing.line_length_pixels as f32,
            linear: self.linear,
            hdr: self.hdr,
            linear_dcg_ratio: self.linear_dcg_ratio,
            hdr_dcg_ratio: self.hdr_dcg_ratio,
        }
    }
    pub fn linear_codes(
        &self,
        seconds: f32,
        gain: f32,
        timing: RuntimeTiming,
    ) -> Result<exposure::Codes, String> {
        exposure::convert(
            seconds,
            gain,
            exposure::Mode::Linear,
            if self.linear_dcg_supported { 0 } else { -1 },
            self.conversion(timing),
        )
        .map_err(|e| format!("Exposure conversion: {e:?}"))
    }
}

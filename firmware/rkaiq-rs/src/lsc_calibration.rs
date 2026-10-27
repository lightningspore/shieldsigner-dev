//! Owned selected single-resolution, normal-case LSC calibration.
extern crate alloc;
use crate::{lsc_geometry, lsc_tables::SAMPLES};
use alloc::{format, string::String, vec::Vec};
use serde_json::Value;
#[derive(Clone, Debug)]
pub struct Table {
    pub name: [u8; 32],
    pub vignetting: f32,
    pub samples: [u16; SAMPLES],
}
#[derive(Clone, Debug)]
pub struct Illuminant {
    pub wb: [f32; 2],
    pub gains: Vec<f32>,
    pub vig: Vec<f32>,
    pub tables: Vec<Table>,
}
#[derive(Clone, Debug)]
pub struct Automatic {
    pub enabled: bool,
    pub damping_enabled: bool,
    pub resolution: [u8; 32],
    pub sectors: [[u16; 16]; 2],
    pub gradients: [[u16; 16]; 2],
    pub illuminants: Vec<Illuminant>,
}
fn number(v: &Value) -> Result<f32, String> {
    v.as_f64()
        .map(|n| n as f32)
        .filter(|n| n.is_finite())
        .ok_or_else(|| "Expected finite LSC number".into())
}
fn flag(v: &Value) -> Result<bool, String> {
    if let Some(b) = v.as_bool() {
        return Ok(b);
    };
    v.as_u64()
        .filter(|n| *n <= 1)
        .map(|n| n == 1)
        .ok_or_else(|| "Expected LSC boolean".into())
}
fn name(v: &Value) -> Result<[u8; 32], String> {
    let s = v
        .as_str()
        .filter(|s| !s.is_empty() && s.len() < 32 && s.is_ascii() && !s.as_bytes().contains(&0))
        .ok_or("Expected 1..31 ASCII LSC name")?;
    let mut out = [0; 32];
    out[..s.len()].copy_from_slice(s.as_bytes());
    Ok(out)
}
fn array<'a>(v: &'a Value, count: &Value, max: usize) -> Result<&'a [Value], String> {
    v.as_array()
        .filter(|a| !a.is_empty() && a.len() <= max && count.as_u64() == Some(a.len() as u64))
        .map(|a| a.as_slice())
        .ok_or_else(|| "Invalid LSC array/count".into())
}
fn words<const N: usize>(v: &Value) -> Result<[u16; N], String> {
    let a = v
        .as_array()
        .filter(|a| a.len() == N)
        .ok_or("Wrong LSC grid/sector size")?;
    let mut out = [0; N];
    for (o, v) in out.iter_mut().zip(a) {
        *o = v
            .as_u64()
            .and_then(|n| u16::try_from(n).ok())
            .ok_or("Expected LSC u16")?;
    }
    Ok(out)
}
impl Automatic {
    /// Reject unsupported calibration cases rather than silently omitting them.
    /// Full resolution switching/OTP/manual mode are handled separately.
    pub fn from_value(v: &Value) -> Result<Self, String> {
        let common = &v["common"];
        let coefficient = &v["alscCoef"];
        let table = &v["tbl"];
        let resolution = &array(&common["resolutionAll"], &common["resolutionAll_len"], 1)?[0];
        let resolution_name = name(&resolution["name"])?;
        let sectors = [
            words(&resolution["lsc_sect_size_x"])?,
            words(&resolution["lsc_sect_size_y"])?,
        ];
        let (x, y) = lsc_geometry::gradients(&sectors[0], &sectors[1])
            .map_err(|e| format!("LSC geometry: {e:?}"))?;
        let all_tables = array(&table["tableAll"], &table["tableAll_len"], 35)?;
        let mut illuminants = Vec::new();
        for ill in array(&coefficient["illAll"], &coefficient["illAll_len"], 7)? {
            if ill["usedForCase"].as_u64() != Some(0) {
                return Err("Only normal-case LSC calibration is supported".into());
            }
            let ill_name = name(&ill["name"])?;
            let wb = ill["wbGain"]
                .as_array()
                .filter(|a| a.len() == 2)
                .ok_or("Expected LSC WB pair")?;
            let gains = array(&ill["gains"], &ill["gains_len"], 64)?
                .iter()
                .map(number)
                .collect::<Result<Vec<_>, _>>()?;
            let vig = array(&ill["vig"], &ill["vig_len"], 64)?
                .iter()
                .map(number)
                .collect::<Result<Vec<_>, _>>()?;
            crate::interpolate(&gains, &vig, 1.).map_err(|e| format!("LSC gain curve: {e:?}"))?;
            let mut tables = Vec::new();
            for used in array(&ill["tableUsed"], &ill["tableUsed_len"], 5)? {
                let suffix = used
                    .as_str()
                    .or_else(|| used["name"].as_str())
                    .ok_or("Expected LSC table name")?;
                let key = format!("{}_{}", resolution["name"].as_str().unwrap(), suffix);
                let matches = all_tables
                    .iter()
                    .filter(|t| t["name"].as_str() == Some(&key))
                    .collect::<Vec<_>>();
                if matches.len() != 1 {
                    return Err("Missing/ambiguous LSC table".into());
                }
                let t = matches[0];
                if name(&t["resolution"])? != resolution_name
                    || name(&t["illumination"])? != ill_name
                {
                    return Err("LSC table metadata mismatch".into());
                }
                let mut samples = [0; SAMPLES];
                for (i, key) in [
                    "lsc_samples_red",
                    "lsc_samples_greenR",
                    "lsc_samples_greenB",
                    "lsc_samples_blue",
                ]
                .iter()
                .enumerate()
                {
                    samples[i * 289..(i + 1) * 289]
                        .copy_from_slice(&words::<289>(&t[key]["uCoeff"])?);
                }
                let table = Table {
                    name: name(&t["name"])?,
                    vignetting: number(&t["vignetting"])?,
                    samples,
                };
                if tables.iter().any(|p: &Table| p.name == table.name) {
                    return Err("Duplicate LSC table reference".into());
                }
                tables.push(table);
            }
            illuminants.push(Illuminant {
                wb: [number(&wb[0])?, number(&wb[1])?],
                gains,
                vig,
                tables,
            });
        }
        Ok(Self {
            enabled: flag(&common["enable"])?,
            damping_enabled: flag(&coefficient["damp_enable"])?,
            resolution: resolution_name,
            sectors,
            gradients: [x, y],
            illuminants,
        })
    }
    pub fn result(
        &self,
        samples: &[u16; SAMPLES],
        enabled: bool,
    ) -> [u8; crate::isp_lsc::RESULT_BYTES] {
        let mut out = [0; crate::isp_lsc::RESULT_BYTES];
        for (i, n) in samples.iter().enumerate() {
            out[i * 2..i * 2 + 2].copy_from_slice(&n.to_le_bytes());
        }
        for (i, plane) in self.gradients.iter().chain(self.sectors.iter()).enumerate() {
            for (j, n) in plane.iter().enumerate() {
                let p = 2312 + i * 32 + j * 2;
                out[p..p + 2].copy_from_slice(&n.to_le_bytes());
            }
        }
        out[2440] = u8::from(enabled);
        out
    }
}

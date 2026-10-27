//! Linear selected-measurement prefix of AecUpdateConfig, ending after initial
//! weight publication. This is not the full configuration/exposure controller.
extern crate alloc;
use crate::{
    ae_geometry::{self, Geometry, RECORD_BYTES},
    InvalidInput,
};
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Policy {
    pub histogram_mode: i32,
    pub raw_mode: i32,
    pub y_range: i32,
    pub channel_mask: u8,
}
pub fn linear(
    geometry: Geometry,
    weights: &[u8; 225],
    histogram_mode: i32,
    raw_mode: i32,
    y_range: i32,
    calibration_channel_mask: u8,
) -> Result<([u8; RECORD_BYTES], Policy), InvalidInput> {
    // The outer native method supplies a built-in fallback for all-zero grids;
    // this checked checkpoint rejects that unsupported case rather than guessing.
    if weights.iter().all(|v| *v == 0) {
        return Err(InvalidInput::DegenerateRange);
    }
    let mut record = ae_geometry::defaults();
    ae_geometry::configure(&mut record, geometry, 0)?;
    let histogram_mode = if (1..=5).contains(&histogram_mode) {
        histogram_mode
    } else {
        5
    };
    let raw_mode = if (1..=4).contains(&raw_mode) {
        raw_mode
    } else {
        4
    };
    let y_range = if (1..=2).contains(&y_range) {
        y_range
    } else {
        1
    };
    let channel_mask = calibration_channel_mask
        | match raw_mode {
            1 => 2,
            2 => 4,
            3 => 8,
            _ => 1,
        };
    let (offset, blue, green, red) = if y_range == 1 {
        (0, 29, 75, 77)
    } else {
        (16, 28, 64, 64)
    };
    // Header offsets within the independently checked SDK selected records.
    for (o, b, g, r) in [
        (112, 113, 114, 115),
        (154, 155, 156, 157),
        (396, 397, 398, 399),
    ] {
        record[o] = offset;
        record[b] = blue;
        record[g] = green;
        record[r] = red;
    }
    // Linear source 1 publishes the full software grid into histogram 1.
    record[166..391].copy_from_slice(weights);
    Ok((
        record,
        Policy {
            histogram_mode,
            raw_mode,
            y_range,
            channel_mask,
        },
    ))
}
#[cfg(feature = "diagnostics")]
pub fn from_comm(
    comm: &serde_json::Value,
    width: u32,
    height: u32,
) -> Result<([u8; RECORD_BYTES], Policy), alloc::string::String> {
    extern crate alloc;
    use alloc::string::String;
    if comm["Enable"].as_u64() != Some(1)
        || comm["AecOpType"].as_str() != Some("RK_AIQ_OP_MODE_AUTO")
    {
        return Err("AE profile checkpoint requires enabled automatic mode".into());
    }
    let window = |name: &str| -> Result<[f32; 4], String> {
        let value = &comm["AecWinScale"][name];
        let mut out = [0.; 4];
        for (i, key) in ["h_offs", "v_offs", "h_size", "v_size"].iter().enumerate() {
            let f = value[key].as_f64().ok_or("Missing AE window fraction")? as f32;
            if !f.is_finite() || !(0.0..=1.0).contains(&f) {
                return Err("AE window fraction outside checked domain".into());
            }
            out[i] = f;
        }
        if out[0] + out[2] > 1. || out[1] + out[3] > 1. {
            return Err(
                "AE window requires native calibration correction before this checkpoint".into(),
            );
        }
        Ok(out)
    };
    let geometry = Geometry {
        width,
        height,
        input: window("InRawWinScale")?,
        tone_mapped: window("TmoRawWinScale")?,
    };
    let grid = comm["AecGridWeight"]
        .as_array()
        .ok_or("Missing AE weight grid")?;
    if grid.len() != 225 {
        return Err("AE weight grid requires 225 cells".into());
    }
    let mut weights = [0; 225];
    for (i, v) in grid.iter().enumerate() {
        weights[i] = u8::try_from(v.as_u64().ok_or("Invalid AE grid weight")?)
            .map_err(|_| "AE grid weight exceeds byte")?;
    }
    let hist = match comm["HistStatsMode"].as_str() {
        Some("CAM_HISTV2_MODE_Y") => 5,
        _ => return Err("Profile checkpoint currently supports histogram Y mode".into()),
    };
    let raw = match comm["RawStatsMode"].as_str() {
        Some("CAM_RAWSTATSV2_MODE_Y") => 4,
        _ => return Err("Profile checkpoint currently supports raw Y statistics".into()),
    };
    let range = match comm["YRangeMode"].as_str() {
        Some("CAM_YRANGEV2_MODE_FULL") => 1,
        _ => return Err("Unsupported AE Y range".into()),
    };
    linear(geometry, &weights, hist, raw, range, 0)
        .map_err(|_| "AE profile outside checked linear checkpoint".into())
}

#[cfg(all(test, feature = "diagnostics"))]
mod tests {
    use super::*;
    #[test]
    fn profile_rejects_incomplete_or_unsupported_configuration() {
        let win = serde_json::json!({"h_offs":0,"v_offs":0,"h_size":1,"v_size":1});
        let mut comm = serde_json::json!({"Enable":1,"AecOpType":"RK_AIQ_OP_MODE_AUTO","HistStatsMode":"CAM_HISTV2_MODE_Y","RawStatsMode":"CAM_RAWSTATSV2_MODE_Y","YRangeMode":"CAM_YRANGEV2_MODE_FULL","AecGridWeight":alloc::vec![1u8;225],"AecWinScale":{"InRawWinScale":win,"TmoRawWinScale":win}});
        assert!(from_comm(&comm, 2304, 1296).is_ok());
        comm["AecGridWeight"] = serde_json::json!(alloc::vec![0u8;225]);
        assert!(from_comm(&comm, 2304, 1296).is_err());
        comm["AecGridWeight"] = serde_json::json!(alloc::vec![1u8;224]);
        assert!(from_comm(&comm, 2304, 1296).is_err());
        comm["AecGridWeight"] = serde_json::json!(alloc::vec![1u8;225]);
        comm["Enable"] = serde_json::json!(0);
        assert!(from_comm(&comm, 2304, 1296).is_err());
    }
}

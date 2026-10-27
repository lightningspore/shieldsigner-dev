//! Offline replay through the same owned session used by camera integration.
//! No camera devices or ISP submission occur in this fixture.
use serde_json::{json, Value};
use shieldsigner_rkaiq::{
    awb_preparation::FRAME_BYTES,
    awb_session::{Input, Session},
};

pub fn run(v: &Value) -> Result<Value, String> {
    let dimensions = [
        u32::try_from(v["dimensions"][0].as_u64().ok_or("width")?).map_err(|_| "width overflow")?,
        u32::try_from(v["dimensions"][1].as_u64().ok_or("height")?)
            .map_err(|_| "height overflow")?,
    ];
    let scale = u32::try_from(v["sample_scale"].as_u64().ok_or("sample_scale")?)
        .map_err(|_| "scale overflow")?;
    let iso = v["iso"].as_f64().ok_or("explicit ISO required")? as f32;
    let text = v["raw"].as_str().ok_or("translated frame required")?;
    if text.len() != FRAME_BYTES * 2 {
        return Err("translated frame length".into());
    }
    let bytes = (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).map_err(|e| e.to_string()))
        .collect::<Result<Vec<_>, _>>()?;
    let raw: [u8; FRAME_BYTES] = bytes.try_into().map_err(|_| "translated frame length")?;
    let mut session = Session::new(&v["iq"], dimensions, scale)?;
    let repeat = v.get("repeat").and_then(Value::as_u64).unwrap_or(1);
    if repeat == 0 || repeat > 256 {
        return Err("repeat must be 1..256".into());
    }
    let check_rollback = v
        .get("check_rollback")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    let mut reference = if check_rollback {
        Some(Session::new(&v["iq"], dimensions, scale)?)
    } else {
        None
    };
    let mut results = Vec::new();
    for i in 0..repeat {
        if check_rollback {
            let mut bad = raw;
            bad[0x1dcc..0x1dd0].copy_from_slice(&f32::NAN.to_bits().to_le_bytes());
            let result = session.process(
                &bad,
                &Input {
                    requested_update: true,
                    exposure_luma: Some([123.456; 2]),
                    iso,
                    site_reference: None,
                },
            );
            if result.is_ok() {
                return Err("Corrupt pre-gain was accepted".into());
            }
        }
        let r = session
            .process(
                &raw,
                &Input {
                    requested_update: i == 0,
                    exposure_luma: None,
                    iso,
                    site_reference: None,
                },
            )
            .map_err(|e| format!("session: {e:?}"))?;
        if let Some(reference) = reference.as_mut() {
            let expected = reference
                .process(
                    &raw,
                    &Input {
                        requested_update: i == 0,
                        exposure_luma: None,
                        iso,
                        site_reference: None,
                    },
                )
                .map_err(|e| format!("reference: {e:?}"))?;
            if r != expected {
                return Err("Rejected frame altered subsequent session behavior".into());
            }
        }
        let geometry = session.geometry();
        results.push(json!({"kind":"offline-captured-awb-gain","hardwareWrites":false,"automaticWhiteBalance":false,
            "inputAssumptions":{"sampleScale":scale,"iso":iso,"exposureMetadata":"missing; calibrated fallback","savedSiteReference":"absent","softwarePreGainOverride":false},
            "numeric":{"brightness":r.numeric.luma,"points":r.numeric.points,"regions":r.numeric.regions,"smart":r.numeric.smart,"variance":r.variance,"environment":r.environment},
            "geometry":{"window":geometry.window,"block":geometry.block,"sampled":geometry.sampled_dimensions,"absoluteCountThreshold":geometry.count_threshold},
            "prepared":{"complete":r.complete,"activeLights":r.active_lights,"totalCounts":r.total_counts,"gridValid":r.grid_valid},
            "action":{"calculated":r.action.calculated,"reconfigureRequested":r.action.reconfigure},
            "gain":{"initial":r.initial_gain,"current":r.current_gain,"previous":r.previous_gain,"region":r.region,"retained":r.retained,"density":r.density},
            "probabilities":r.probabilities,
            "session":{"frame":r.controller_frame,"countdown":r.countdown,"continuation":format!("{:?}",r.continuation)}
        }));
    }
    if repeat == 1 {
        Ok(results.remove(0))
    } else {
        Ok(
            json!({"kind":"repeated-capture-awb-session-replay","hardwareWrites":false,"repeat":repeat,"rollbackChecks":if check_rollback {repeat} else {0},"frames":results}),
        )
    }
}

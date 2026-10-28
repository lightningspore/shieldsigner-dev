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

/// Controlled multi-frame replay through one production Session. Input records
/// may be captured or deliberately transformed; no hardware writes occur.
pub fn run_sequence(v: &Value) -> Result<Value, String> {
    let width = u32::try_from(v["dimensions"][0].as_u64().ok_or("width")?).map_err(|_| "width")?;
    let height =
        u32::try_from(v["dimensions"][1].as_u64().ok_or("height")?).map_err(|_| "height")?;
    let scale = u32::try_from(v["sample_scale"].as_u64().ok_or("sample_scale")?)
        .map_err(|_| "sample_scale")?;
    let stages = v["stages"].as_array().ok_or("stages")?;
    if stages.is_empty() || stages.len() > 32 {
        return Err("stages must be 1..32".into());
    }
    let mut session = Session::new(&v["iq"], [width, height], scale)?;
    // Optional measurement replay follows the same post-processing handoff as
    // the camera owner. Seed bytes are explicit; never invent SDK state.
    fn decode<const N: usize>(value: &Value) -> Result<[u8; N], String> {
        let text = value.as_str().ok_or("measurement hex required")?;
        if text.len() != N * 2 {
            return Err("measurement hex length".into());
        }
        let bytes = text.as_bytes().chunks_exact(2).map(|pair| {
            let text = core::str::from_utf8(pair).map_err(|_| "non-ASCII measurement hex")?;
            u8::from_str_radix(text, 16).map_err(|_| "invalid measurement hex")
        }).collect::<Result<Vec<_>, _>>()?;
        bytes.try_into().map_err(|_| "measurement length".into())
    }
    let mut measurement = v.get("initial_measurement")
        .map(decode::<{shieldsigner_rkaiq::isp_awb_measurement::INPUT_BYTES}>)
        .transpose()?;
    let signature = if measurement.is_some() {
        decode::<64>(v.get("measurement_signature").ok_or("measurement signature required")?)?
    } else { [0; 64] };
    let mut results = Vec::new();
    for (stage_index, stage) in stages.iter().enumerate() {
        let records = stage["raw"].as_array().ok_or("stage raw records")?;
        let cycles = stage["cycles"].as_u64().ok_or("cycles")?;
        if records.is_empty()
            || records.len() > 4
            || !(1..=128).contains(&cycles)
            || results.len() + cycles as usize * records.len() > 512
        {
            return Err("sequence exceeds bounded size".into());
        }
        let iso = stage
            .get("iso")
            .unwrap_or(&v["iso"])
            .as_f64()
            .ok_or("iso")? as f32;
        let luma = stage
            .get("normalized_brightness")
            .or_else(|| v.get("normalized_brightness"))
            .map(|value| value.as_f64().ok_or("normalized brightness"))
            .transpose()?
            .map(|x| [x as f32, 0.]);
        let requested_update = stage.get("requested_update")
            .map(|value| value.as_bool().ok_or("requested update must be boolean"))
            .transpose()?;
        let mut frames = Vec::new();
        for record in records {
            let text = record.as_str().ok_or("translated frame hex")?;
            if text.len() != FRAME_BYTES * 2 {
                return Err("translated frame length".into());
            }
            let bytes = text
                .as_bytes()
                .chunks_exact(2)
                .map(|pair| {
                    let text = core::str::from_utf8(pair)
                        .map_err(|_| "non-ASCII frame hex".to_string())?;
                    u8::from_str_radix(text, 16).map_err(|_| "invalid frame hex".to_string())
                })
                .collect::<Result<Vec<_>, String>>()?;
            frames.push(<[u8; FRAME_BYTES]>::try_from(bytes).map_err(|_| "frame length")?);
        }
        for cycle in 0..cycles {
            for (record, raw) in frames.iter().enumerate() {
                let output = session
                    .process(
                        raw,
                        &Input {
                            requested_update: requested_update.unwrap_or(results.is_empty()),
                            exposure_luma: luma,
                            iso,
                            site_reference: None,
                        },
                    )
                    .map_err(|e| format!("session stage {stage_index} cycle {cycle}: {e:?}"))?;
                let mut row = json!({"stage":stage_index,"cycle":cycle,"record":record,
                "calculated":output.action.calculated,"reconfigure":output.action.reconfigure,
                "gain":output.current_gain,"controllerFrame":output.controller_frame,"countdown":output.countdown,
                "complete":output.complete,"activeLights":output.active_lights,"continuation":format!("{:?}",output.continuation),
                "preparationRequested":output.preparation_requested,"updateAfterGate":output.numeric.update,
                "stabilityThreshold":output.numeric.smart[2],"stabilityMask":output.stability_mask,
                "region":output.region,"density":output.density,"probabilities":output.probabilities,"dampingCoefficient":session.ccm_damping(),
                "historyBits":output.measurement_history.map(|row|row.map(f32::to_bits))});
                if let Some(record) = measurement.as_mut() {
                    if output.action.reconfigure {
                        session.next_measurement(record, &signature)
                            .map_err(|e| format!("next measurement: {e:?}"))?;
                    }
                    row["measurement"] = Value::String(record.iter()
                        .map(|b| format!("{b:02x}")).collect());
                }
                results.push(row);
            }
        }
    }
    Ok(
        json!({"kind":"controlled-awb-session-sequence-replay","hardwareWrites":false,
        "forcedStageUpdates":false,"frames":results}),
    )
}

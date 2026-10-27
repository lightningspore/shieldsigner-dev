use crate::{ae_session_fixture::snapshot, sensor_submission_fixture::Backend};
use serde_json::{json, Value};
use shieldsigner_rkaiq::*;
fn decode(text: &str) -> Vec<u8> {
    (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap())
        .collect()
}
fn hex(record: &[u8]) -> String {
    record.iter().map(|b| format!("{b:02x}")).collect()
}
fn sensor(runtime: &ae_runtime::Runtime) -> Value {
    json!({"pending":runtime.sensor.pending().map(|e|json!({"first":e.first,"record":hex(&e.exposure)})).collect::<Vec<_>>(),"current":hex(&runtime.sensor.current),"effective":runtime.sensor.effective().map(|e|json!({"frame":e.frame,"record":hex(&e.exposure)})).collect::<Vec<_>>()})
}
pub fn run(v: &Value) -> String {
    let session = ae_session::Session::from_profile(
        &v["profile"],
        calibration::RuntimeTiming {
            frame_length: 1360,
            line_length_pixels: 2800,
            pixel_clock_mhz: 114.24,
        },
        2304,
        1296,
    )
    .unwrap();
    let initial = decode(v["initial"].as_str().unwrap()).try_into().unwrap();
    let mut runtime = ae_runtime::Runtime::new(
        session,
        initial,
        sensor_scheduler::EffectPolicy {
            shorten_enabled: false,
            designated_frame: 0,
            shorten_all: false,
        },
    )
    .unwrap();
    let owned = v["parameters"]
        .as_array()
        .unwrap()
        .iter()
        .map(|p| {
            (
                p["id"].as_u64().unwrap() as u32,
                decode(p["bytes"].as_str().unwrap()).try_into().unwrap(),
            )
        })
        .collect::<Vec<(u32, [u8; isp32::PARAMETER_BYTES])>>();
    let parameters = owned
        .iter()
        .map(|(id, bytes)| ae_session::ParameterSnapshot { id: *id, bytes })
        .collect::<Vec<_>>();
    let mut isp_parameters = owned[0].1;
    let mut wb_cache: [u8; 32] = isp_parameters
        [isp32::AWB_GAIN_OFFSET..isp32::AWB_GAIN_OFFSET + 32]
        .try_into()
        .unwrap();
    let mut error = 0.;
    let mut results = vec![
        json!({"kind":"initial","state":snapshot(&runtime.session,error),"sensor":sensor(&runtime)}),
    ];
    for event in v["events"].as_array().unwrap() {
        if event["kind"] == "isp" {
            isp_parameters[..24].fill(0);
            let wb = event.get("wb").map(|v| isp32::WhiteBalanceGain {
                red: v[0].as_f64().unwrap() as f32,
                green_red: v[1].as_f64().unwrap() as f32,
                green_blue: v[2].as_f64().unwrap() as f32,
                blue: v[3].as_f64().unwrap() as f32,
                position: isp32::ApplyPosition::Gain1,
            });
            let out = runtime
                .apply_isp_gain_results(
                    event["frame"].as_u64().unwrap() as u32,
                    &mut isp_parameters,
                    &mut wb_cache,
                    wb,
                )
                .unwrap();
            results.push(json!({"kind":"isp","selected_frame":out.exposure_frame,"exact":out.exact_exposure,"parameters":hex(&isp_parameters),"cache":hex(&wb_cache),"state":snapshot(&runtime.session,error),"sensor":sensor(&runtime)}));
        } else if event["kind"] == "sof" {
            let mut backend = Backend {
                trace: vec!["descriptor".into()],
                operations: 0,
                fail: event["fail"].as_u64().unwrap() as usize,
            };
            let out = runtime.on_sof(event["frame"].as_u64().unwrap() as u32, &mut backend);
            let mut state = sensor(&runtime);
            state["status"] = json!(out.scheduled.status);
            state["written"] = json!(out.scheduled.written.map(|r| hex(&r)));
            state["trace"] = json!(out.scheduled.written.map(|_| format!(
                "{}|{}|-",
                backend.trace.join(";"),
                out.scheduled.status
            )));
            results.push(
                json!({"kind":"sof","sensor":state,"state":snapshot(&runtime.session,error)}),
            );
        } else {
            let raw = decode(event["raw"].as_str().unwrap());
            let mut record = match runtime.step_statistics(&raw, &parameters) {
                Ok(Some(out)) => {
                    error = out
                        .control
                        .frame
                        .control
                        .map_or(out.control.frame.preprocessing_error, |c| c.relative_error);
                    json!({"kind":"stats","status":"processed","selected_frame":out.exposure_frame,"exact":out.exact_exposure,"mean":out.mean_q8})
                }
                Ok(None) => json!({"kind":"stats","status":"no-measurement"}),
                Err(e) => json!({"kind":"stats","status":"error","error":e}),
            };
            record["state"] = snapshot(&runtime.session, error);
            record["sensor"] = sensor(&runtime);
            results.push(record);
        }
    }
    serde_json::to_string(&results).unwrap()
}

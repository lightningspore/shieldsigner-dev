//! Line protocol used by the ARM-original differential harness.
use shieldsigner_rkaiq::*;
use std::io::{self, BufRead};
#[path = "../ae_pipeline_fixture.rs"]
mod ae_pipeline_fixture;
#[path = "../ae_result_fixture.rs"]
mod ae_result_fixture;
#[path = "../ae_runtime_fixture.rs"]
mod ae_runtime_fixture;
#[path = "../ae_session_fixture.rs"]
mod ae_session_fixture;
#[path = "../awb_gain_adjust_fixture.rs"]
mod awb_gain_adjust_fixture;
#[path = "../awb_gain_controller_fixture.rs"]
mod awb_gain_controller_fixture;
#[path = "../awb_prepared_gain_fixture.rs"]
mod awb_prepared_gain_fixture;
#[path = "../awb_site_fixture.rs"]
mod awb_site_fixture;
#[path = "../awb_dispatch_fixture.rs"]
mod awb_dispatch_fixture;
#[path = "../awb_common_fixture.rs"]
mod awb_common_fixture;
#[path = "../awb_low_single_color_fixture.rs"]
mod awb_low_single_color_fixture;
#[path = "../awb_postprocess_fixture.rs"]
mod awb_postprocess_fixture;
#[path = "../awb_preparation_fixture.rs"]
mod awb_preparation_fixture;
#[path = "../awb_translation_fixture.rs"]
mod awb_translation_fixture;
#[path = "../sensor_submission_fixture.rs"]
mod sensor_submission_fixture;
#[path = "../awb_capture_replay_fixture.rs"]
mod awb_capture_replay_fixture;
fn f(s: &str) -> f32 {
    f32::from_bits(u32::from_str_radix(s, 16).unwrap())
}
fn floats(s: &str) -> Vec<f32> {
    s.split(',').map(f).collect()
}
fn emit(values: &[f32]) {
    println!(
        "{}",
        values
            .iter()
            .map(|v| format!("{:08x}", v.to_bits()))
            .collect::<Vec<_>>()
            .join(",")
    );
}
#[path = "../awb_measurement_schedule_fixture.rs"]
mod awb_measurement_schedule_fixture;
#[path = "../awb_measurement_regions_fixture.rs"]
mod awb_measurement_regions_fixture;
#[path = "../awb_measurement_transforms_fixture.rs"]
mod awb_measurement_transforms_fixture;
#[path = "../awb_measurement_geometry_fixture.rs"]
mod awb_measurement_geometry_fixture;
#[path = "../awb_measurement_limits_fixture.rs"]
mod awb_measurement_limits_fixture;
#[path = "../awb_input_selection_fixture.rs"]
mod awb_input_selection_fixture;
#[path = "../awb_measurement_weights_fixture.rs"]
mod awb_measurement_weights_fixture;
#[path = "../awb_measurement_exclusions_fixture.rs"]
mod awb_measurement_exclusions_fixture;
#[path = "../awb_fast_configuration_fixture.rs"]
mod awb_fast_configuration_fixture;
#[path = "../awb_measurement_binding_fixture.rs"]
mod awb_measurement_binding_fixture;
fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let a: Vec<_> = line.split_whitespace().collect();
        match a[0] {
            "ae-runtime" => println!(
                "{}",
                ae_runtime_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "sensor-submission" => println!(
                "{}",
                sensor_submission_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "ae-raw-session" => println!(
                "{}",
                ae_session_fixture::run_raw(&serde_json::from_str(a[1]).unwrap())
            ),
            "ae-session" => println!(
                "{}",
                ae_session_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "ae-preparation" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let out = ae_startup::profile::linear(
                    &v["profile"],
                    calibration::RuntimeTiming {
                        frame_length: v["frame"].as_u64().unwrap() as u32,
                        line_length_pixels: v["line"].as_u64().unwrap() as u32,
                        pixel_clock_mhz: v["clock"].as_f64().unwrap() as f32,
                    },
                )
                .unwrap();
                let p = out.register_policy;
                let s = out.startup;
                let mut words = vec![
                    out.timing.frame_length,
                    out.fps.to_bits(),
                    p.time_range[0].to_bits(),
                    p.time_range[1].to_bits(),
                    p.gain_range[0].to_bits(),
                    p.gain_range[1].to_bits(),
                    p.isp_range[0].to_bits(),
                    p.isp_range[1].to_bits(),
                    p.time_quantum.to_bits(),
                    s.requested_aggregate.to_bits(),
                    s.held_aggregate.to_bits(),
                    s.current.gain.to_bits(),
                    s.current.isp_gain.to_bits(),
                    u32::MAX,
                    s.current.seconds.to_bits(),
                    s.current.codes.integration_time,
                    s.current.codes.gain,
                    s.intermediate_count as u32,
                ];
                // Native structure of arrays, including both iris metadata arrays.
                for field in 0..9 {
                    for h in s.history {
                        words.push(match field {
                            0 => h.aggregate.to_bits(),
                            1 => h.iris_gain as u32,
                            8 => h.iris_step as u32,
                            2 => h.isp_gain.to_bits(),
                            3 => h.gain.to_bits(),
                            4 => h.seconds.to_bits(),
                            5 => h.dcg as u32,
                            6 => h.time_code,
                            7 => h.gain_code,
                            _ => unreachable!(),
                        });
                    }
                }
                println!(
                    "{}",
                    words
                        .iter()
                        .map(|w| format!("{w:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-lifecycle" => {
                let mut state = ae_lifecycle::State(u32::from_str_radix(a[1], 16).unwrap());
                let mut output = Vec::new();
                for op in a[3].bytes() {
                    let context = if a[2] == "1" { Some(&mut state) } else { None };
                    let status = match op {
                        b's' => ae_lifecycle::State::start(context),
                        b't' => ae_lifecycle::State::stop(context),
                        _ => panic!("invalid lifecycle operation"),
                    };
                    output.push(format!("{:02x}:{:08x}", status, state.0));
                }
                println!("{}", output.join(","));
            }
            "awb-measurement-binding" => println!("{}", awb_measurement_binding_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-fast-configuration" => println!("{}", awb_fast_configuration_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-exclusions" => println!("{}", awb_measurement_exclusions_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-weights" => println!("{}", awb_measurement_weights_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-input-selection" => println!("{}", awb_input_selection_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-limits" => println!("{}", awb_measurement_limits_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-geometry" => println!("{}", awb_measurement_geometry_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-transforms" => println!("{}", awb_measurement_transforms_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-iq-transforms" => println!("{}", awb_measurement_transforms_fixture::iq(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-uv" => println!("{}", awb_measurement_regions_fixture::uv(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-iq-uv" => println!("{}", awb_measurement_regions_fixture::iq_uv(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-iq-regions" => println!("{}", awb_measurement_regions_fixture::iq(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-regions" => println!("{}", awb_measurement_regions_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-measurement-schedule" => println!("{}", awb_measurement_schedule_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-translation" => println!(
                "{}",
                awb_translation_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "awb-dispatch" => println!("{}", awb_dispatch_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-site" => println!("{}", awb_site_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-gain-controller" => println!(
                "{}",
                awb_gain_controller_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "awb-postprocess" => println!(
                "{}",
                awb_postprocess_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "awb-gain-adjust" => println!(
                "{}",
                awb_gain_adjust_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "awb-gain-clip" => {
                use shieldsigner_rkaiq::{
                    awb_gain_clip::*,
                    awb_single_color::{self, ColorTemperature, Line},
                };
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let gain = core::array::from_fn(|i| v["gain"][i].as_f64().unwrap() as f32);
                let line = |key: &str| Line {
                    a: v[key][0].as_f64().unwrap() as f32,
                    b: v[key][1].as_f64().unwrap() as f32,
                    c: v[key][2].as_f64().unwrap() as f32,
                    valid: v[key][3].as_bool().unwrap(),
                };
                if v["kind"].as_str().unwrap() == "inverse" {
                    let temperature = ColorTemperature {
                        valid: v["valid"].as_bool().unwrap(),
                        cct: v["cct"].as_f64().unwrap() as f32,
                        ccri: v["ccri"].as_f64().unwrap() as f32,
                    };
                    let (gain, converted) = awb_single_color::gain_from_color_temperature(
                        temperature,
                        line("first"),
                        line("second"),
                        gain,
                    )
                    .unwrap();
                    println!(
                        "{}",
                        serde_json::json!({"gain":gain.map(f32::to_bits),"converted":converted})
                    );
                } else {
                    let floats = |key: &str| {
                        v[key]
                            .as_array()
                            .unwrap()
                            .iter()
                            .map(|v| v.as_f64().unwrap() as f32)
                            .collect::<Vec<_>>()
                    };
                    let knots = floats("knots");
                    let lower = floats("lower");
                    let upper = floats("upper");
                    let cal = Calibration {
                        first: line("first"),
                        second: line("second"),
                        daylight: v["daylight"].as_bool().unwrap(),
                        daylight_threshold: v["daylight_threshold"].as_u64().unwrap() as u32,
                        daylight_minimum_cct: v["daylight_minimum"].as_f64().unwrap() as f32,
                        bounds: if v["bounds"].as_bool().unwrap() {
                            Some(Bounds {
                                cct: &knots,
                                negative_tint: &lower,
                                positive_tint: &upper,
                            })
                        } else {
                            None
                        },
                    };
                    let r = clip(
                        gain,
                        v["clipped"].as_bool().unwrap(),
                        v["brightness"].as_u64().unwrap() as u32,
                        &cal,
                    )
                    .unwrap();
                    println!(
                        "{}",
                        serde_json::json!({"gain":r.gain.map(f32::to_bits),"clipped":r.clipped})
                    );
                }
            }
            "awb-gain-history" => {
                use shieldsigner_rkaiq::awb_gain_history::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let gain = |v: &serde_json::Value| -> [f32; 4] {
                    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
                };
                let initial: Vec<_> = v["history"].as_array().unwrap().iter().map(gain).collect();
                let mut history = History::<32>::from_values(&initial).unwrap();
                let mut output = Vec::new();
                for step in v["steps"].as_array().unwrap() {
                    let (selected, updated) = history
                        .select(
                            gain(&step["gain"]),
                            step["target"].as_i64().unwrap() as i32,
                            step["tolerance"].as_f64().unwrap() as f32,
                        )
                        .unwrap();
                    let converged = converged(
                        history.values(),
                        None,
                        (step["convergence"].as_f64().unwrap() as f32) * 2.,
                    )
                    .unwrap();
                    let values: Vec<_> = history
                        .values()
                        .iter()
                        .map(|g| g.map(f32::to_bits))
                        .collect();
                    output.push(serde_json::json!({"gain":selected.map(f32::to_bits),"updated":updated,"converged":converged,"history":values}));
                }
                println!("{}", serde_json::json!(output));
            }
            "awb-single-camera-scale" => println!("{}",awb_session::SINGLE_CAMERA_SAMPLE_SCALE),
            "awb-schedule-init" => {
                let n:u8=a[1].parse().unwrap(); let capacity:u8=a[2].parse().unwrap();
                match awb_measurement_schedule::initialize(n,capacity) {
                    Err(error)=>println!("error:{error:?}"),
                    Ok(s)=>{
                        let mut bytes=[0u8;164];
                        bytes[1]=(n>capacity) as u8;
                        bytes[4..8].copy_from_slice(&(s.count as u32).to_le_bytes());
                        for (i,g) in s.groups.iter().enumerate() {
                            bytes[148+i*4..152+i*4].copy_from_slice(&(g.count as u32).to_le_bytes());
                            for j in 0..7 {
                                bytes[8+(i*7+j)*4..12+(i*7+j)*4].copy_from_slice(&g.indices[j].to_le_bytes());
                                bytes[120+i*7+j]=g.rt_yuv[j] as u8;
                            }
                        }
                        println!("{}",bytes.iter().map(|b|format!("{b:02x}")).collect::<String>());
                    }
                }
            }
            "awb-linear-iso" => {
                let v=floats(a[1]);
                match awb_exposure::linear_iso(v.try_into().unwrap()) {
                    Ok(iso)=>emit(&[iso]), Err(error)=>println!("error:{error:?}"),
                }
            }
            "awb-captured-sequence" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                println!("{}", match awb_capture_replay_fixture::run_sequence(&v) { Ok(value)=>value, Err(error)=>serde_json::json!({"error":error}) });
            }
            "awb-captured-gain" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                println!("{}", match awb_capture_replay_fixture::run(&v) { Ok(value)=>value, Err(error)=>serde_json::json!({"error":error}) });
            }
            "awb-fresh-preparation" => {
                use awb_preparation::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = v["n"].as_u64().unwrap() as usize;
                let mut seen = vec![0xA5; n];
                let mut records = vec![LightRecord([0xA5; LIGHT_BYTES]); n];
                let mut second = vec![u32::MAX; n];
                let mut total = vec![u32::MAX; n.max(2)];
                let mut grid = [[f32::NAN; 3]; 225];
                let mut state = State::fresh(&mut seen, &mut records, &mut second, &mut total, &mut grid, n).unwrap();
                let before = awb_preparation_fixture::render(&state);
                let text = v["raw"].as_str().unwrap();
                let bytes: Vec<u8> = (0..text.len()).step_by(2).map(|i|u8::from_str_radix(&text[i..i+2],16).unwrap()).collect();
                let bytes: [u8; FRAME_BYTES] = bytes.try_into().unwrap();
                let curve = awb_probability::Curve { knots: &[0.], weights: &[0.] };
                prepare(&mut state, &Frame(&bytes), &Settings {
                    groups:v["groups"].as_u64().unwrap() as usize,
                    fast_light_count:v["fast_count"].as_u64().unwrap() as u32,
                    stability_threshold:v["threshold"].as_f64().unwrap() as f32,
                    prior_sample:0., exclusion_kind:[1;4], exclusion_weight:[curve;4],
                }).unwrap();
                println!("{}",serde_json::json!({"before":before,"after":awb_preparation_fixture::render(&state)}));
            }
            "awb-initial-gain-state" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut c = shieldsigner_rkaiq::awb_calibration::Scene::from_value(&v["iq"]).unwrap();
                c.lights.first_frame = v["first"].as_u64().unwrap() as usize;
                let s = c.initial_gain_state::<64>().unwrap();
                let p = &s.controller.post;
                println!("{}", serde_json::json!({
                    "current":p.current.map(f32::to_bits),
                    "previous":p.previous.map(f32::to_bits),
                    "low_current":s.controller.low.low.current.map(f32::to_bits),
                    "temperature":[p.temperature.valid as u32,p.temperature.cct.to_bits(),p.temperature.ccri.to_bits()],
                    "frame":s.dispatch.frame,"countdown":s.dispatch.countdown,
                    "history_lengths":[p.raw_history.values().len(),p.output_history.values().len(),s.controller.high_history.values().len()],
                    "diagnostics":[p.coefficient.to_bits(),p.effective_coefficient.to_bits(),s.controller.density.to_bits(),s.controller.temporal_weight.to_bits(),s.controller.high_low_weight.to_bits()],
                    "lines":c.common.lines.map(|l|serde_json::json!([l.a.to_bits(),l.b.to_bits(),l.c.to_bits(),l.valid as u32])),
                    "gains":c.lights.entries.iter().map(|l|l.reference_gain.map(f32::to_bits)).collect::<Vec<_>>()
                }));
            }
            "awb-scene-parse" => {
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                println!("{}",match shieldsigner_rkaiq::awb_calibration::Scene::from_value(&v){
                    Ok(c)=>serde_json::json!({"lights":c.lights.entries.len(),"first":c.lights.first_frame,"candidates":c.single.candidates.len(),"mode":c.single.mode,"optional":[c.optional.bounds_enabled,c.optional.daylight_enabled,c.optional.adjustment_enabled,c.optional.offsets.is_some()],"temperature":c.optional.temperature_mode,"luma":c.optional.sample_from_luma,"luts":c.optional.luts.len(),"site":[c.site.enabled,c.site.reuse_enabled],"site_frames":c.site.frame_limit,"site_thresholds":[c.site.gain_threshold.to_bits(),c.site.sample_threshold.to_bits()],"site_path":c.site_path}),
                    Err(e)=>serde_json::json!({"error":e}),
                });
            }
            "awb-iq-environment" => {
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                let c=shieldsigner_rkaiq::awb_calibration::Common::from_value(&v["iq"]).unwrap();
                let r=shieldsigner_rkaiq::awb_environment::classify(v["luma"].as_u64().unwrap() as u32,&c.environment(),v["previous"].as_i64().unwrap() as i32);
                println!("{}",serde_json::json!({"level":r.level,"environment":r.environment,"boundaries":c.environment_boundaries}));
            }
            "awb-preprocess-parse" => {
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                println!("{}", match shieldsigner_rkaiq::awb_calibration::Preprocessing::from_value(&v["iq"]) {
                    Ok(c)=>serde_json::json!({"enabled":c.smart_enabled,"lengths":[c.smart.knots.len(),c.interval.knots.len(),c.points.knots.len(),c.regions.knots.len(),c.tolerance.knots.len()],"tolerance":c.tolerance(v["brightness"].as_u64().unwrap() as u32).unwrap().to_bits()}),
                    Err(e)=>serde_json::json!({"error":e}),
                });
            }
            "awb-common-iq" => println!("{}",awb_common_fixture::run(&serde_json::from_str(a[1]).unwrap())),
            "awb-lights-parse" => {
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                println!("{}",match shieldsigner_rkaiq::awb_calibration::Lights::from_value(&v){
                    Ok(c)=>serde_json::json!({"first":c.first_frame,"lights":c.entries.iter().map(|l|serde_json::json!({"name":l.name,"kind":l.kind,"reference":l.reference_gain.map(f32::to_bits),"uv":l.uv.map(|a|a.map(f32::to_bits)),"xy":l.xy.map(|a|a.map(f32::to_bits)),"yuv_knots":l.yuv_knots.map(f32::to_bits),"yuv_thresholds":l.yuv_thresholds.map(f32::to_bits),"yuv_line":l.yuv_line.map(f32::to_bits),"yuv_distance":l.yuv_distance.to_bits()})).collect::<Vec<_>>()}),
                    Err(e)=>serde_json::json!({"error":e}),
                });
            }
            "awb-sgc-parse" => {
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                println!("{}", match shieldsigner_rkaiq::awb_calibration::SingleColor::from_value(&v) {
                    Ok(c)=>serde_json::json!({"enabled":c.enabled,"mode":c.mode,"colors":c.colors.len(),"candidates":c.candidates.len(),"names":c.candidate_names,"indices":c.color_indices,"target":c.history_target,"alpha":c.alpha.to_bits(),"diagnostic":c.diagnostic_candidate,"thresholds":([c.acceptance_threshold,c.estimated_density_threshold,c.estimated_single_threshold,c.high_history_threshold].map(f32::to_bits))}),
                    Err(e)=>serde_json::json!({"error":e}),
                });
            }
            "awb-single-color-grid" => {
                use shieldsigner_rkaiq::{
                    awb_luma_history::History, awb_single_color::Line, awb_single_color_grid::*,
                };
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let line = |key: &str| Line {
                    a: v[key][0].as_f64().unwrap() as f32,
                    b: v[key][1].as_f64().unwrap() as f32,
                    c: v[key][2].as_f64().unwrap() as f32,
                    valid: v[key][3].as_bool().unwrap(),
                };
                let candidates: Vec<_> = v["candidates"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| Candidate {
                        red: v[0].as_f64().unwrap() as f32,
                        blue: v[1].as_f64().unwrap() as f32,
                    })
                    .collect();
                let colors: Vec<_> = v["colors"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| Color {
                        chroma: v["chroma"].as_f64().unwrap() as f32,
                        hue: v["hue"].as_f64().unwrap() as f32,
                        cct_knots: core::array::from_fn(|i| v["knots"][i].as_f64().unwrap() as f32),
                        distance_thresholds: core::array::from_fn(|i| {
                            v["thresholds"][i].as_f64().unwrap() as f32
                        }),
                    })
                    .collect();
                let grid = core::array::from_fn(|i| {
                    core::array::from_fn(|j| v["grid"][i][j].as_f64().unwrap() as f32)
                });
                let history: Vec<_> = v["history"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| v.as_u64().unwrap() as u32)
                    .collect();
                let mut state = State {
                    history: History::<32>::from_values(&history).unwrap(),
                    result: Detection {
                        selected: 0,
                        color: 0,
                        candidate_counts: [0x5a5a5a5a; 14],
                        color_counts: [0x5a5a5a5a; 14],
                        valid: false,
                        disagreements: 0,
                        votes: 0,
                        mean_distance: 0.,
                        gain: [0.; 4],
                    },
                };
                let prior = if v["prior"].is_null() {
                    None
                } else {
                    Some(core::array::from_fn(|i| {
                        v["prior"][i].as_f64().unwrap() as f32
                    }))
                };
                let loaded = v.get("sgc").map(shieldsigner_rkaiq::awb_calibration::SingleColor::from_value).transpose().unwrap();
                let manual = Calibration { candidates:&candidates,colors:&colors,alpha:v["alpha"].as_f64().unwrap() as f32,history_target:v["target"].as_u64().unwrap() as u16,first:line("first"),second:line("second") };
                let calibration=loaded.as_ref().map(|c|c.classifier(line("first"),line("second"))).unwrap_or(manual);
                state
                    .process(
                        &grid,
                        &calibration,
                        prior,
                    )
                    .unwrap();
                let r = state.result;
                println!(
                    "{}",
                    serde_json::json!({"selected":r.selected,"color":r.color,"candidate_counts":r.candidate_counts,"color_counts":r.color_counts,"valid":r.valid,"disagreements":r.disagreements,"votes":r.votes,"mean":r.mean_distance.to_bits(),"gain":r.gain.map(f32::to_bits),"history":state.history.values()})
                );
            }
            "awb-color" => {
                use shieldsigner_rkaiq::awb_color::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let input: [f32; 3] =
                    core::array::from_fn(|i| v["input"][i].as_f64().unwrap() as f32);
                let result: Vec<u32> = match v["kind"].as_str().unwrap() {
                    "transfer" => vec![lab_transfer(input[0]).unwrap().to_bits()],
                    "xyz" => rgb_to_xyz(input).unwrap().map(f32::to_bits).to_vec(),
                    "lab" => xyz_to_lab(input).unwrap().map(f32::to_bits).to_vec(),
                    "lch" => lab_to_lch([input[0], input[1]])
                        .unwrap()
                        .map(f32::to_bits)
                        .to_vec(),
                    "pipeline" => {
                        let xyz = rgb_to_xyz(input).unwrap();
                        let lab = xyz_to_lab(xyz).unwrap();
                        let lch = lab_to_lch([lab[1], lab[2]]).unwrap();
                        xyz.into_iter()
                            .chain(lab)
                            .chain(lch)
                            .map(f32::to_bits)
                            .collect()
                    }
                    _ => panic!("unknown color stage"),
                };
                println!("{}", serde_json::json!(result));
            }
            "awb-single-color" => {
                use shieldsigner_rkaiq::awb_single_color::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let line = |key: &str| Line {
                    a: v[key][0].as_f64().unwrap() as f32,
                    b: v[key][1].as_f64().unwrap() as f32,
                    c: v[key][2].as_f64().unwrap() as f32,
                    valid: v[key][3].as_bool().unwrap(),
                };
                let gain = core::array::from_fn(|i| v["gain"][i].as_f64().unwrap() as f32);
                if v["kind"].as_str().unwrap() == "temperature" {
                    let r = color_temperature(gain, line("first"), line("second")).unwrap();
                    println!(
                        "{}",
                        serde_json::json!({"valid":r.valid,"cct":r.cct.to_bits(),"ccri":r.ccri.to_bits()})
                    );
                } else {
                    let c = &v["calibration"];
                    let cal = Calibration {
                        brightness_knots: core::array::from_fn(|i| {
                            c["brightness_knots"][i].as_f64().unwrap() as f32
                        }),
                        brightness_weights: core::array::from_fn(|i| {
                            c["brightness_weights"][i].as_f64().unwrap() as f32
                        }),
                        density_knots: core::array::from_fn(|i| {
                            c["density_knots"][i].as_f64().unwrap() as f32
                        }),
                        density_weights: core::array::from_fn(|i| {
                            c["density_weights"][i].as_f64().unwrap() as f32
                        }),
                        distance_knots: core::array::from_fn(|i| {
                            c["distance_knots"][i].as_f64().unwrap() as f32
                        }),
                        cct_knots: core::array::from_fn(|i| {
                            c["cct_knots"][i].as_f64().unwrap() as f32
                        }),
                        distance_weights: core::array::from_fn(|j| {
                            core::array::from_fn(|i| {
                                c["distance_weights"][j][i].as_f64().unwrap() as f32
                            })
                        }),
                        disagreement_knots: core::array::from_fn(|i| {
                            c["disagreement_knots"][i].as_f64().unwrap() as f32
                        }),
                        disagreement_weights: core::array::from_fn(|i| {
                            c["disagreement_weights"][i].as_f64().unwrap() as f32
                        }),
                    };
                    let loaded = v.get("sgc").map(shieldsigner_rkaiq::awb_calibration::SingleColor::from_value).transpose().unwrap();
                    let calibration = loaded.as_ref().map(|c| &c.confidence).unwrap_or(&cal);
                    let r = confidence(
                        calibration,
                        v["brightness"].as_f64().unwrap() as f32,
                        v["density"].as_f64().unwrap() as f32,
                        v["distance"].as_f64().unwrap() as f32,
                        v["disagreements"].as_i64().unwrap() as i32,
                        gain,
                        line("first"),
                        line("second"),
                    )
                    .unwrap();
                    println!("{}", serde_json::json!({"weight":r.to_bits()}));
                }
            }
            "awb-low-gain" | "awb-low-single-color" => {
                use shieldsigner_rkaiq::{
                    awb_high_gain::{Light, LightResult},
                    awb_low_gain::*,
                    awb_luma_history::History,
                };
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let gains = |v: &serde_json::Value| -> [f32; 4] {
                    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
                };
                let colors: Vec<_> = v["colors"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| v.as_u64().unwrap() as u32)
                    .collect();
                let history: Vec<_> = v["history"].as_array().unwrap().iter().map(gains).collect();
                let mut state = State {
                    current: [2.; 4],
                    low_result: [3.; 4],
                    temporal_result: [4.; 4],
                    spatial_result: [5.; 4],
                    temporal_source: [6.; 4],
                    spatial_weight: 0.25,
                    used_previous: v["used_previous"].as_bool().unwrap(),
                    color_history: History::<32>::from_values(&colors).unwrap(),
                };
                let settings = Settings {
                    retained: v["retained"].as_u64().unwrap() as u32,
                    count_threshold: v["threshold"].as_u64().unwrap() as u32,
                    brightness: v["brightness"].as_u64().unwrap() as u32,
                    low_brightness: v["low"].as_u64().unwrap() as u32,
                    high_brightness: v["high"].as_u64().unwrap() as u32,
                    temporal_default: gains(&v["default"]),
                    color_history_value: v["color_value"].as_i64().unwrap() as i32,
                    color_history_target: v["target"].as_u64().unwrap() as u16,
                };
                let lights: Vec<_> = v["lights"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|l| Light {
                        selected_gain: [0.; 4],
                        selected_count: 0,
                        extra_gain: [0.; 4],
                        extra_count: 0,
                        extra_enabled: false,
                        low_threshold: l["low"].as_u64().unwrap() as u32,
                        high_threshold: l["high"].as_u64().unwrap() as u32,
                        low_gain: gains(&l["low_gain"]),
                        high_gain: gains(&l["high_gain"]),
                        spatial_percentage: 0,
                        probability: l["probability"].as_f64().unwrap() as f32,
                    })
                    .collect();
                let mut output = vec![
                    LightResult {
                        statistic: [7.; 4],
                        spatial: [8.; 4],
                        spatial_weight: 0.5,
                        extra_weight: 0.75
                    };
                    lights.len()
                ];
                let single = if a[0] == "awb-low-single-color" {
                    let (low, single) = awb_low_single_color_fixture::run(
                        state,
                        &lights,
                        &mut output,
                        &history,
                        &settings,
                        &v,
                    );
                    state = low;
                    Some(single)
                } else {
                    state
                        .calculate_without_single_color(&lights, &mut output, &history, &settings)
                        .unwrap();
                    None
                };
                let lights: Vec<_> = output.iter().map(|r| serde_json::json!({"statistic": r.statistic.map(f32::to_bits), "spatial": r.spatial.map(f32::to_bits), "spatial_weight": r.spatial_weight.to_bits(), "extra_weight": r.extra_weight.to_bits()})).collect();
                let mut result = serde_json::json!({"current": state.current.map(f32::to_bits), "low_result": state.low_result.map(f32::to_bits), "temporal_result": state.temporal_result.map(f32::to_bits), "spatial_result": state.spatial_result.map(f32::to_bits), "temporal_source": state.temporal_source.map(f32::to_bits), "weight": state.spatial_weight.to_bits(), "used_previous": state.used_previous, "colors": state.color_history.values(), "lights": lights});
                if let Some(single) = single {
                    result["single"] = single;
                }
                println!("{}", result);
            }
            "awb-high-gain" => {
                use shieldsigner_rkaiq::awb_high_gain::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let gains = |v: &serde_json::Value| -> [f32; 4] {
                    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
                };
                let mut lights: Vec<_> = v["lights"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|l| Light {
                        selected_gain: gains(&l["selected_gain"]),
                        selected_count: l["selected_count"].as_u64().unwrap() as u32,
                        extra_gain: gains(&l["extra_gain"]),
                        extra_count: l["extra_count"].as_u64().unwrap() as u32,
                        extra_enabled: l["extra_enabled"].as_bool().unwrap(),
                        low_threshold: l["low"].as_u64().unwrap() as u32,
                        high_threshold: l["high"].as_u64().unwrap() as u32,
                        low_gain: gains(&l["low_gain"]),
                        high_gain: gains(&l["high_gain"]),
                        spatial_percentage: l["percentage"].as_u64().unwrap() as u8,
                        probability: l["probability"].as_f64().unwrap() as f32,
                    })
                    .collect();
                let loaded=v.get("light_iq").map(shieldsigner_rkaiq::awb_calibration::Lights::from_value).transpose().unwrap();
                if let Some(iq)=&loaded {
                    assert_eq!(lights.len(),iq.entries.len());
                    for (light,cal) in lights.iter_mut().zip(&iq.entries){
                        let c=cal.controller_light(v["group"].as_u64().unwrap() as usize, light.extra_enabled).unwrap().calibration;
                        light.low_threshold=c.low_threshold;light.high_threshold=c.high_threshold;
                        light.low_gain=c.low_gain;light.high_gain=c.high_gain;light.spatial_percentage=c.spatial_percentage;
                    }
                }
                let mut output = vec![
                    LightResult {
                        statistic: [0.; 4],
                        spatial: [0.; 4],
                        spatial_weight: 0.25,
                        extra_weight: 0.75
                    };
                    lights.len()
                ];
                let settings = Settings {
                    fast: v["fast"].as_bool().unwrap(),
                    brightness: v["brightness"].as_u64().unwrap() as u32,
                    temporal_default: gains(&v["default"]),
                    temporal_knots: core::array::from_fn(|i| {
                        v["knots"][i].as_u64().unwrap() as u32
                    }),
                    temporal_percentages: core::array::from_fn(|i| {
                        v["percentages"][i].as_u64().unwrap() as u8
                    }),
                };
                let result = calculate(&lights, &mut output, &settings).unwrap();
                let lights: Vec<_> = output.iter().map(|r| serde_json::json!({"statistic": r.statistic.map(f32::to_bits), "spatial": r.spatial.map(f32::to_bits), "spatial_weight": r.spatial_weight.to_bits(), "extra_weight": r.extra_weight.to_bits()})).collect();
                println!(
                    "{}",
                    serde_json::json!({"lights": lights, "gain": result.gain.map(f32::to_bits), "temporal": result.temporal.map(f32::to_bits), "weight": result.temporal_weight.to_bits()})
                );
            }
            "awb-temporal" => {
                use shieldsigner_rkaiq::awb_gain;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let gains = |v: &serde_json::Value| -> [f32; 4] {
                    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
                };
                let history: Vec<_> = v["history"].as_array().unwrap().iter().map(gains).collect();
                let weights: Vec<_> = v["weights"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| v.as_u64().unwrap() as u8)
                    .collect();
                let default = gains(&v["default"]);
                let temporal = if v["direct"].as_bool().unwrap() {
                    default
                } else {
                    awb_gain::temporal_history(&history, &weights, default).unwrap()
                };
                let knots = core::array::from_fn(|i| v["knots"][i].as_u64().unwrap() as u32);
                let percentages =
                    core::array::from_fn(|i| v["percentages"][i].as_u64().unwrap() as u8);
                let (gain, weight) = awb_gain::temporal_blend(
                    gains(&v["current"]),
                    temporal,
                    v["brightness"].as_u64().unwrap() as u32,
                    &knots,
                    &percentages,
                )
                .unwrap();
                println!(
                    "{}",
                    serde_json::json!({"temporal": temporal.map(f32::to_bits), "gain": gain.map(f32::to_bits), "weight": weight.to_bits()})
                );
            }
            "awb-spatial" => {
                use shieldsigner_rkaiq::awb_gain;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let gains = |v: &serde_json::Value| -> [f32; 4] {
                    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
                };
                let mut output = Vec::new();
                for light in v["lights"].as_array().unwrap() {
                    let spatial = awb_gain::spatial(
                        v["brightness"].as_u64().unwrap() as u32,
                        light["low"].as_u64().unwrap() as u32,
                        light["high"].as_u64().unwrap() as u32,
                        gains(&light["low_gain"]),
                        gains(&light["high_gain"]),
                    )
                    .unwrap();
                    let (mixed, weight) = awb_gain::spatial_statistics(
                        gains(&light["statistics"]),
                        spatial,
                        light["percentage"].as_u64().unwrap() as u8,
                    )
                    .unwrap();
                    output.push(serde_json::json!({
                        "spatial": spatial.map(f32::to_bits),
                        "mixed": mixed.map(f32::to_bits),
                        "weight": weight.to_bits(),
                    }));
                }
                println!("{}", serde_json::json!(output));
            }
            "awb-xy-selection" => {
                use shieldsigner_rkaiq::{
                    awb_luma_history, awb_probability::Probability, awb_xy_selection::*,
                };
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let values = |key: &str| {
                    v[key]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|v| v.as_u64().unwrap() as u32)
                        .collect::<Vec<_>>()
                };
                let history = values("history");
                let normal = values("normal");
                let big = values("big");
                let mut state = State {
                    history: awb_luma_history::History::<32>::from_values(&history).unwrap(),
                    selected: match v["previous"].as_u64().unwrap() {
                        0 => Region::Normal,
                        1 => Region::Big,
                        3 => Region::Exclusion,
                        _ => panic!(),
                    },
                    retained: 0,
                    kind: 9,
                };
                let mut output = vec![
                    Probability {
                        total: 0.25,
                        distance: 0.5,
                        luma: 0.75,
                        prior: 1.,
                        white_points: 1.25
                    };
                    normal.len()
                ];
                let settings = Settings {
                    absolute: v["absolute"].as_f64().unwrap() as f32,
                    relative: v["relative"].as_f64().unwrap() as f32,
                    region_thresholds: core::array::from_fn(|i| {
                        v["region_thresholds"][i].as_f64().unwrap() as f32
                    }),
                    count_thresholds: core::array::from_fn(|i| {
                        v["count_thresholds"][i].as_u64().unwrap() as u32
                    }),
                    stabilization: v["enabled"].as_bool().unwrap(),
                    target: v["target"].as_i64().unwrap() as i32,
                    variance: f32::from_bits(v["variance"].as_u64().unwrap() as u32),
                    variance_threshold: v["variance_threshold"].as_f64().unwrap() as f32,
                };
                state
                    .select(
                        &normal,
                        &big,
                        v["exclusion"].as_u64().unwrap() as u32,
                        &mut output,
                        &settings,
                    )
                    .unwrap();
                println!(
                    "{}",
                    serde_json::json!({"selected":state.selected as u8,"retained":state.retained,"kind":state.kind,"history":state.history.values(),"probabilities":output.iter().map(|p|[p.total,p.distance,p.luma,p.prior,p.white_points].map(f32::to_bits)).collect::<Vec<_>>()})
                );
            }
            "awb-prepared-frame" => println!(
                "{}",
                awb_preparation_fixture::run_with_preprocess(
                    &serde_json::from_str(a[1]).unwrap(),
                    true
                )
            ),
            "awb-preparation" => println!(
                "{}",
                awb_preparation_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "interp" => emit(&[interpolate(&floats(a[2]), &floats(a[3]), f(a[1])).unwrap()]),
            "matrix" | "offset" => {
                let x = floats(a[4]);
                let y = floats(a[5]);
                let first = ColorProfile {
                    saturation: f(a[2]),
                    matrix: x[..9].try_into().unwrap(),
                    offsets: x[9..].try_into().unwrap(),
                };
                let second = ColorProfile {
                    saturation: f(a[3]),
                    matrix: y[..9].try_into().unwrap(),
                    offsets: y[9..].try_into().unwrap(),
                };
                if a[0] == "matrix" {
                    emit(&saturation_matrix(f(a[1]), &first, &second).unwrap());
                } else {
                    emit(&saturation_offsets(f(a[1]), &first, &second).unwrap());
                }
            }
            "defect" => {
                let x: Vec<i32> = a[2].split(',').map(|v| v.parse().unwrap()).collect();
                let y: Vec<i32> = a[3].split(',').map(|v| v.parse().unwrap()).collect();
                println!(
                    "{}",
                    defect_pixel_interpolate(
                        a[1].parse().unwrap(),
                        x.as_slice().try_into().unwrap(),
                        y.as_slice().try_into().unwrap()
                    )
                    .unwrap()
                );
            }
            "iso" => {
                use shieldsigner_rkaiq::gain::*;
                let knots: Vec<i32> = a[3].split(',').map(|v| v.parse().unwrap()).collect();
                let table = GainTable {
                    enabled: a[2] == "1",
                    iso: knots.try_into().unwrap(),
                    short: floats(a[4]).try_into().unwrap(),
                    middle: floats(a[5]).try_into().unwrap(),
                };
                let mut e = ExposureSet {
                    mode: HdrMode::Linear,
                    time: [1.; 3],
                    analog_gain: [1.; 3],
                    digital_gain: [1.; 3],
                    iso: [0; 3],
                };
                e.iso[0] = a[1].parse().unwrap();
                let out = select_gain_scales(&table, &e).unwrap();
                println!(
                    "{} {} {} {:08x} {:08x}",
                    out.low,
                    out.high,
                    out.scales.enabled as u8,
                    out.scales.short.to_bits(),
                    out.scales.middle.to_bits()
                );
            }
            "awb" => {
                use shieldsigner_rkaiq::isp32::*;
                let mut state: u32 = a[1].parse().unwrap();
                let mut params = [0u8; PARAMETER_BYTES];
                for value in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *value = (state >> 24) as u8;
                }
                let mut cache = [0u8; 32];
                let values = floats(a[4]);
                let gain = WhiteBalanceGain {
                    red: values[0],
                    green_red: values[1],
                    green_blue: values[2],
                    blue: values[3],
                    position: if a[3] == "0" {
                        ApplyPosition::Gain0
                    } else {
                        ApplyPosition::Gain1
                    },
                };
                apply_awb_gain(&mut params, &mut cache, gain, a[2] == "1").unwrap();
                let hex = |data: &[u8]| {
                    data.iter()
                        .map(|v| format!("{:02x}", v))
                        .collect::<String>()
                };
                println!(
                    "{}:{}:{}",
                    hex(&params[..24]),
                    hex(&params[AWB_GAIN_OFFSET..AWB_GAIN_OFFSET + 32]),
                    hex(&cache)
                );
            }
            "isp-effective" => {
                use shieldsigner_rkaiq::isp_effective::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut record = [0x5a; RECORD_BYTES];
                let ae = [v["ae"].as_u64().unwrap() as u8; AE_CACHE_BYTES];
                let blc = [v["blc"].as_u64().unwrap() as u8; BLC_CACHE_BYTES];
                let wb = [v["wb"].as_u64().unwrap() as u8; WB_CACHE_BYTES];
                let cfg = [v["cfg"].as_u64().unwrap() as u8; AWB_CONFIGURATION_BYTES];
                copy_metadata(
                    &mut record,
                    &ae,
                    &blc,
                    &wb,
                    if v["present"].as_bool().unwrap() {
                        Some(&cfg)
                    } else {
                        None
                    },
                );
                println!(
                    "{}",
                    record
                        .iter()
                        .map(|v| format!("{v:02x}"))
                        .collect::<String>()
                );
            }
            "awb-preprocess" => {
                use shieldsigner_rkaiq::awb_preprocess::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let array = |key: &str| {
                    v[key]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|v| v.as_f64().unwrap() as f32)
                        .collect::<Vec<_>>()
                };
                let knots = array("knots");
                let smart = [array("smart0"), array("smart1"), array("smart2")];
                let intervals = array("intervals");
                let points = [array("points0"), array("points1")];
                let regions = [array("regions0"), array("regions1")];
                let calibration = Calibration {
                    smart_knots: &knots,
                    smart: [&smart[0], &smart[1], &smart[2]],
                    interval: Curve {
                        knots: &knots,
                        values: &intervals,
                    },
                    point_knots: &knots,
                    points: [&points[0], &points[1]],
                    region_knots: &knots,
                    regions: [&regions[0], &regions[1]],
                };
                let loaded=v.get("preprocess_iq").map(shieldsigner_rkaiq::awb_calibration::Preprocessing::from_value).transpose().unwrap();
                let calibration=loaded.as_ref().map(|c|c.calibration()).unwrap_or(calibration);
                let common=v.get("common_iq").map(shieldsigner_rkaiq::awb_calibration::Common::from_value).transpose().unwrap();
                let input = Input {
                    requested_mode: v["mode"].as_i64().unwrap() as i32,
                    previous_update: v["update"].as_bool().unwrap(),
                    smart_enabled: loaded.as_ref().map(|c|c.smart_enabled).unwrap_or(v["enabled"].as_bool().unwrap()),
                    countdown: v["countdown"].as_i64().unwrap() as i32,
                    exposure_luma: if v["source"].is_null() {
                        None
                    } else {
                        Some([
                            v["source"][0].as_f64().unwrap() as f32,
                            v["source"][1].as_f64().unwrap() as f32,
                        ])
                    },
                    frame_choice: v["choice"].as_u64().unwrap() as u8,
                    working_mode: v["working"].as_i64().unwrap() as i32,
                    fallback: common.as_ref().map(|c|c.fallback_brightness()).unwrap_or(v["fallback"].as_u64().unwrap() as u32),
                    override_enabled: v["override_enabled"].as_bool().unwrap(),
                    override_valid: v["override_valid"].as_bool().unwrap(),
                    override_luma: v["override"].as_f64().unwrap() as f32,
                    geometry: [2304, 1296],
                    block: [
                        v["block"][0].as_u64().unwrap() as u8,
                        v["block"][1].as_u64().unwrap() as u8,
                    ],
                    sample_scale: v["scale"].as_i64().unwrap() as i32,
                };
                let mut state = State {
                    mode: 7,
                    update: false,
                    luma_integer: 123,
                    luma: 2.,
                    smart: [3., 4., 5.],
                    interval: 6,
                    points: [7, 8],
                    regions: [9., 10.],
                    frame_counter: v["frame"].as_u64().unwrap() as u32,
                };
                let mut extra = serde_json::Value::Null;
                let decision = if let Some(m) = v.get("metadata") {
                    let values = m["history"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|v| v.as_u64().unwrap() as u32)
                        .collect::<Vec<_>>();
                    let mut metadata = Metadata {
                        history: awb_luma_history::History::<32>::from_values(&values).unwrap(),
                        level: 9,
                        environment: -7,
                        variance: 0.5,
                        brightness_stable: true,
                    };
                    let boundaries = m["boundaries"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|v| v.as_u64().unwrap() as u32)
                        .collect::<Vec<_>>();
                    let manual_environment = awb_environment::Calibration {
                        boundaries: &boundaries,
                        thresholds: core::array::from_fn(|i| {
                            m["thresholds"][i].as_u64().unwrap() as u32
                        }),
                    };
                    let environment=common.as_ref().map(|c|c.environment()).unwrap_or(manual_environment);
                    let decision = state
                        .derive_measurements(
                            &input,
                            &calibration,
                            &mut metadata,
                            &environment,
                            [
                                m["convergence"][0].as_bool().unwrap(),
                                m["convergence"][1].as_bool().unwrap(),
                            ],
                            m["target"].as_i64().unwrap() as i32,
                        )
                        .unwrap();
                    extra = serde_json::json!({"history":metadata.history.values(),"level":metadata.level,"environment":metadata.environment,"variance":metadata.variance.to_bits(),"stable":metadata.brightness_stable});
                    decision
                } else {
                    state.derive(&input, &calibration).unwrap()
                };
                let mut output = serde_json::json!({"mode":state.mode,"update":state.update,"integer":state.luma_integer,"luma":state.luma.to_bits(),"smart":state.smart.map(f32::to_bits),"interval":state.interval,"points":state.points,"regions":state.regions.map(f32::to_bits),"frame":state.frame_counter,"decision":match decision {Continuation::ModeBypass=>0,Continuation::IntervalSkip=>1,Continuation::Ready=>2}});
                if !extra.is_null() {
                    output["metadata"] = extra;
                }
                println!("{}", output);
            }
            "awb-luma-history" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let initial = v["initial"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| v.as_u64().unwrap() as u32)
                    .collect::<Vec<_>>();
                let mut history = awb_luma_history::History::<32>::from_values(&initial).unwrap();
                let mut results = vec![
                    serde_json::json!({"values":history.values(),"variance":history.variance().to_bits(),"grew":false}),
                ];
                for event in v["events"].as_array().unwrap() {
                    let length = history.values().len();
                    history
                        .update(
                            event["value"].as_i64().unwrap() as i32,
                            event["target"].as_i64().unwrap() as i32,
                        )
                        .unwrap();
                    results.push(serde_json::json!({"values":history.values(),"variance":history.variance().to_bits(),"grew":history.values().len()>length}));
                }
                println!("{}", serde_json::json!(results));
            }
            "awb-stability" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut state = awb_stability::State {
                    matched: 0xa5,
                    update: v["update"].as_bool().unwrap(),
                    history: core::array::from_fn(|i| {
                        core::array::from_fn(|j| v["history"][i][j].as_f64().unwrap() as f32)
                    }),
                };
                let sums = core::array::from_fn(|i| v["sums"][i].as_i64().unwrap());
                state
                    .measure(
                        sums,
                        v["count"].as_u64().unwrap() as usize,
                        v["slot"].as_i64().unwrap() as i32,
                        v["threshold"].as_f64().unwrap() as f32,
                    )
                    .unwrap();
                println!(
                    "{}",
                    serde_json::json!({"matched":state.matched,"update":state.update,"history":state.history.map(|a|a.map(f32::to_bits))})
                );
            }
            "awb-publication" => {
                use shieldsigner_rkaiq::awb_publication::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let word = |key: &str| v[key].as_u64().unwrap() as u32;
                let make_gain = |fill: u8| Gain {
                    frame: 99,
                    sync: word("item_sync"),
                    updated: true,
                    data: [fill; 20],
                };
                let make_config = |fill: u8| Configuration {
                    frame: 99,
                    sync: word("item_sync"),
                    updated: true,
                    data: [fill; 1204],
                };
                let mut state = State {
                    gain_sync: word("gain_sync"),
                    configuration_sync: word("config_sync"),
                    latest_gain: if v["latest_gain"].as_bool().unwrap() {
                        Some(make_gain(0x33))
                    } else {
                        None
                    },
                    latest_configuration: if v["latest_config"].as_bool().unwrap() {
                        Some(make_config(0x44))
                    } else {
                        None
                    },
                };
                let mut gain = make_gain(0x11);
                gain.sync = word("gain_item_sync");
                let mut configuration = make_config(0x22);
                let flags = publish(
                    &mut state,
                    &mut gain,
                    &mut configuration,
                    Input {
                        frame: word("frame"),
                        initial: v["initial"].as_bool().unwrap(),
                        bypass: v["bypass"].as_bool().unwrap(),
                        algorithm_id: v["algorithm_id"].as_i64().unwrap() as i32,
                        gain_changed: v["gain_changed"].as_bool().unwrap(),
                        configuration_changed: v["config_changed"].as_bool().unwrap(),
                    },
                );
                let hex =
                    |bytes: &[u8]| bytes.iter().map(|b| format!("{b:02x}")).collect::<String>();
                println!(
                    "{}",
                    serde_json::json!({"gain_sync":state.gain_sync,"config_sync":state.configuration_sync,"gain_frame":gain.frame,"config_frame":configuration.frame,"gain_item_sync":gain.sync,"config_item_sync":configuration.sync,"gain_updated":gain.updated,"config_updated":configuration.updated,"gain_data":hex(&gain.data),"config_data":hex(&configuration.data),"gain_changed":flags.0,"config_changed":flags.1,"latest_gain":state.latest_gain.map(|v| hex(&v.data)),"latest_config":state.latest_configuration.map(|v| hex(&v.data))})
                );
            }
            "gain-results" => {
                use shieldsigner_rkaiq::isp32::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut params = [0x5a; PARAMETER_BYTES];
                let mut cache = [0; AWB_GAIN_BYTES];
                let mut outputs = Vec::new();
                for event in v.as_array().unwrap() {
                    let wb = event.get("wb").map(|v| {
                        let g = v.as_array().unwrap();
                        WhiteBalanceGain {
                            red: g[0].as_f64().unwrap() as f32,
                            green_red: g[1].as_f64().unwrap() as f32,
                            green_blue: g[2].as_f64().unwrap() as f32,
                            blue: g[3].as_f64().unwrap() as f32,
                            position: if g[4].as_u64().unwrap() == 0 {
                                ApplyPosition::Gain0
                            } else {
                                ApplyPosition::Gain1
                            },
                        }
                    });
                    let exposure = event.get("gain").map(|v| {
                        let g = v.as_array().unwrap();
                        if event["mode"].as_u64().unwrap() == 0 {
                            ExposureDigitalGain::Linear(g[0].as_f64().unwrap() as f32)
                        } else {
                            ExposureDigitalGain::Hdr(core::array::from_fn(|i| {
                                g[i].as_f64().unwrap() as f32
                            }))
                        }
                    });
                    apply_gain_results(&mut params, &mut cache, wb, exposure).unwrap();
                    let hex =
                        |bytes: &[u8]| bytes.iter().map(|b| format!("{b:02x}")).collect::<String>();
                    outputs
                        .push(serde_json::json!({"parameters":hex(&params),"cache":hex(&cache)}));
                }
                println!("{}", serde_json::json!(outputs));
            }
            "dgain" => {
                use shieldsigner_rkaiq::isp32::*;
                let mut state: u32 = a[1].parse().unwrap();
                let mut params = [0u8; PARAMETER_BYTES];
                for value in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *value = (state >> 24) as u8;
                }
                let mut cache = [0u8; AWB_GAIN_BYTES];
                for (i, value) in a[4].split(',').enumerate() {
                    cache[i * 2..i * 2 + 2]
                        .copy_from_slice(&value.parse::<u16>().unwrap().to_le_bytes());
                }
                let values = floats(a[3]);
                let gain = if a[2] == "0" {
                    ExposureDigitalGain::Linear(values[0])
                } else {
                    ExposureDigitalGain::Hdr(values.try_into().unwrap())
                };
                apply_exposure_digital_gain(&mut params, &cache, gain).unwrap();
                let hex = |data: &[u8]| {
                    data.iter()
                        .map(|v| format!("{:02x}", v))
                        .collect::<String>()
                };
                println!(
                    "{}:{}",
                    hex(&params[..24]),
                    hex(&params[AWB_GAIN_OFFSET..AWB_GAIN_OFFSET + 32])
                );
            }
            "aehist" => {
                use shieldsigner_rkaiq::{ae::Bls, ae_histogram::*};
                let mut state: u32 = a[1].parse().unwrap();
                let count: usize = a[2].parse().unwrap();
                let input: Vec<u32> = (0..count)
                    .map(|_| {
                        state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                        state
                    })
                    .collect();
                let read = |s: &str| {
                    let v: Vec<i16> = s.split(',').map(|v| v.parse().unwrap()).collect();
                    Bls {
                        red: v[0],
                        green_red: v[1],
                        green_blue: v[2],
                        blue: v[3],
                    }
                };
                let mode = match a[3] {
                    "2" => Mode::Red,
                    "3" => Mode::Green,
                    "4" => Mode::Blue,
                    _ => Mode::Luma,
                };
                let config = Config {
                    mode,
                    optical_black_rb: a[4].parse().unwrap(),
                    optical_black_green: a[5].parse().unwrap(),
                    black: read(a[6]),
                    gain: read(a[7]),
                    bypass: a[8] == "1",
                };
                let mut output = vec![0xa5a5a5a5; count];
                correct(&input, &mut output, config).unwrap();
                println!(
                    "{}",
                    output
                        .iter()
                        .map(|v| format!("{v:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "awb-probability" => {
                use shieldsigner_rkaiq::awb_probability::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let number = |name: &str| v[name].as_f64().unwrap() as f32;
                let source = v["lights"].as_array().unwrap();
                let knots: Vec<Vec<f32>> = source
                    .iter()
                    .map(|l| {
                        l["knots"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .map(|n| n.as_f64().unwrap() as f32)
                            .collect()
                    })
                    .collect();
                let weights: Vec<Vec<f32>> = source
                    .iter()
                    .map(|l| {
                        l["weights"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .map(|n| n.as_f64().unwrap() as f32)
                            .collect()
                    })
                    .collect();
                let mut lights: Vec<_> = source
                    .iter()
                    .enumerate()
                    .map(|(i, l)| Light {
                        reference_gain: core::array::from_fn(|j| {
                            l["gain"][j].as_f64().unwrap() as f32
                        }),
                        statistic_gain: core::array::from_fn(|j| {
                            l["statisticGain"][j].as_f64().unwrap() as f32
                        }),
                        kind: l["kind"].as_i64().unwrap() as i32,
                        white_points: l["count"].as_u64().unwrap() as u32,
                        prior: Curve {
                            knots: &knots[i],
                            weights: &weights[i],
                        },
                    })
                    .collect();
                let loaded=v.get("light_iq").map(shieldsigner_rkaiq::awb_calibration::Lights::from_value).transpose().unwrap();
                if let Some(iq)=&loaded{
                    assert_eq!(lights.len(),iq.entries.len());
                    for (light,cal) in lights.iter_mut().zip(&iq.entries){*light=cal.probability(light.statistic_gain,light.white_points);}
                }
                let mut output: Vec<_> = source
                    .iter()
                    .map(|l| Probability {
                        total: 0.,
                        distance: 0.,
                        luma: l["oldLuma"].as_f64().unwrap() as f32,
                        prior: 0.,
                        white_points: 0.,
                    })
                    .collect();
                let count = calculate(
                    &lights,
                    &mut output,
                    Settings {
                        gain: core::array::from_fn(|i| v["gain"][i].as_f64().unwrap() as f32),
                        frame: v["frame"].as_u64().unwrap() as u32,
                        fast: v["fast"].as_bool().unwrap(),
                        near_distance_squared: number("near"),
                        far_distance_squared: number("far"),
                        brightness: v["brightness"].as_u64().unwrap() as u32,
                        brightness_thresholds: core::array::from_fn(|i| {
                            v["thresholds"][i].as_u64().unwrap() as u32
                        }),
                        prior_sample: number("sample"),
                        absolute_count_threshold: number("absolute"),
                        relative_count_threshold: number("relative"),
                    },
                )
                .unwrap();
                let values = output
                    .iter()
                    .map(|p| {
                        [p.total, p.distance, p.luma, p.prior, p.white_points]
                            .iter()
                            .map(|x| format!("{:08x}", x.to_bits()))
                            .collect::<Vec<_>>()
                            .join(":")
                    })
                    .collect::<Vec<_>>()
                    .join(",");
                let gain = weighted_gain(&lights, &output)
                    .unwrap()
                    .iter()
                    .map(|x| format!("{:08x}", x.to_bits()))
                    .collect::<Vec<_>>()
                    .join(":");
                println!("{count:08x}:{values}|{gain}");
            }
            "awb-gain" => {
                use shieldsigner_rkaiq::awb_gain::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let value = |name: &str| v[name].as_f64().unwrap() as f32;
                let gains =
                    |name: &str| core::array::from_fn(|i| v[name][i].as_f64().unwrap() as f32);
                if matches!(v["kind"].as_str().unwrap(), "ratios" | "statistics") {
                    let count = v["count"].as_i64().unwrap();
                    let red = v["red"].as_i64().unwrap();
                    let blue = v["blue"].as_i64().unwrap();
                    let (gain, rounded) = if v["kind"] == "statistics" {
                        statistics_gain(count, red, blue).unwrap()
                    } else {
                        (ratios(count, red, blue), count)
                    };
                    println!(
                        "{}:{:016x}",
                        gain.iter()
                            .map(|v| format!("{:08x}", v.to_bits()))
                            .collect::<Vec<_>>()
                            .join(":"),
                        rounded as u64
                    );
                    continue;
                }
                let result = match v["kind"].as_str().unwrap() {
                    "normalize" => normalize(gains("first")).unwrap().to_vec(),
                    "mixture" => mixture(gains("first"), gains("second"), value("weight"))
                        .unwrap()
                        .to_vec(),
                    "factor" => vec![DampingParameters {
                        variance_threshold: value("threshold"),
                        step: value("step"),
                        minimum: value("minimum"),
                        maximum: value("maximum"),
                    }
                    .adapt(value("coefficient"), value("variance"))
                    .unwrap()],
                    "damp" => {
                        let result =
                            damp(gains("first"), gains("second"), value("coefficient")).unwrap();
                        let mut out = vec![result.base_coefficient, result.effective_coefficient];
                        out.extend(result.gain);
                        out
                    }
                    _ => panic!("unknown AWB gain operation"),
                };
                println!(
                    "{}",
                    result
                        .iter()
                        .map(|v| format!("{:08x}", v.to_bits()))
                        .collect::<Vec<_>>()
                        .join(":")
                );
            }
            "awb-measurement" => {
                use shieldsigner_rkaiq::{isp32::PARAMETER_BYTES, isp_awb_measurement::*};
                fn hex_bytes(b: &[u8]) -> String {
                    b.iter().map(|v| format!("{v:02x}")).collect()
                }
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut state = v["seed"].as_u64().unwrap() as u32;
                let mut params = [0u8; PARAMETER_BYTES];
                for b in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *b = (state >> 24) as u8;
                }
                let original = params;
                let source = v["record"].as_str().unwrap();
                let record = (0..source.len())
                    .step_by(2)
                    .map(|i| u8::from_str_radix(&source[i..i + 2], 16).unwrap())
                    .collect::<Vec<_>>();
                Measurement(record.try_into().unwrap())
                    .apply(&mut params, v["update"].as_bool().unwrap());
                assert_eq!(&params[24..OFFSET], &original[24..OFFSET]);
                assert_eq!(&params[OFFSET + BYTES..], &original[OFFSET + BYTES..]);
                println!(
                    "{}:{}",
                    hex_bytes(&params[..24]),
                    hex_bytes(&params[OFFSET..OFFSET + BYTES])
                );
            }
            "ae-zero-config" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let scene = &v["profile"]["main_scene"][0]["sub_scene"][0]["scene_isp32"];
                let sensor = &v["profile"]["sensor_calib"];
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let baseline = ae_fps::refresh_baseline(0, f("frame"), f("line"), f("clock"))
                    .unwrap()
                    .unwrap();
                let mut fps_state = ae_fps::State {
                    baseline_frame: baseline.frame,
                    baseline_fps: baseline.fps,
                    variable_frame: 2222.,
                    fixed_rate: 7.,
                    variable_rate: 8.,
                };
                let fps = ae_fps::Calibration::from_scene(scene)
                    .unwrap()
                    .select(
                        &mut fps_state,
                        f("frame"),
                        f("line"),
                        f("clock"),
                        sensor["CISMinFps"].as_f64().unwrap() as f32,
                    )
                    .unwrap();
                let policy = ae_policy::Calibration::from_scene(scene).unwrap();
                let delay = ae_delay_calibration::Calibration::from_scene(scene)
                    .unwrap()
                    .counts(fps.frame, f("line"), f("clock"))
                    .unwrap();
                let smooth = ae_smoothing::from_profile(scene, sensor).unwrap();
                let dynamic = ae_dynamic_calibration::Calibration::from_scene(scene).unwrap();
                let init = &scene["ae_calib"]["LinearAeCtrl"]["InitExp"];
                let t = init["InitTimeValue"].as_f64().unwrap() as f32;
                let g = init["InitGainValue"].as_f64().unwrap() as f32;
                let isp = init["InitIspDGainValue"].as_f64().unwrap() as f32;
                let mut words = vec![
                    baseline.frame.to_bits(),
                    baseline.clock_mhz.to_bits(),
                    baseline.line.to_bits(),
                    baseline.fps.to_bits(),
                    fps.frame.to_bits(),
                    fps.fps.to_bits(),
                    policy.tolerance_in.to_bits(),
                    policy.tolerance_out.to_bits(),
                    policy.damp_over.to_bits(),
                    policy.damp_under.to_bits(),
                    policy.damp_dark_to_bright.to_bits(),
                    policy.damp_bright_to_dark.to_bits(),
                    delay[0] as u32,
                    delay[1] as u32,
                    smooth.linear as u32,
                    smooth.hdr as u32,
                    g.to_bits(),
                    isp.to_bits(),
                    t.to_bits(),
                    ((g * t) * isp).to_bits(),
                    u32::MAX,
                    0,
                    dynamic.call_enabled as u32,
                    match dynamic.mode {
                        ae_damping::Mode::Default => 1,
                        _ => 2,
                    },
                ];
                words.extend([0u32; 55]);
                println!(
                    "{}",
                    words
                        .iter()
                        .map(|w| format!("{w:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-fps" | "ae-fps-refresh" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let mut state = ae_fps::State {
                    baseline_frame: f("baseline_frame"),
                    baseline_fps: f("baseline_fps"),
                    variable_frame: 2222.,
                    fixed_rate: 7.,
                    variable_rate: 8.,
                };
                let mut baseline = ae_fps::Baseline {
                    frame: state.baseline_frame,
                    clock_mhz: 114.24,
                    line: 2800.,
                    fps: state.baseline_fps,
                };
                if a[0] == "ae-fps-refresh" {
                    if let Some(new) = ae_fps::refresh_baseline(
                        v["mask"].as_u64().unwrap() as u32,
                        f("frame"),
                        f("line"),
                        f("clock"),
                    )
                    .unwrap()
                    {
                        baseline = new;
                        state.baseline_frame = new.frame;
                        state.baseline_fps = new.fps;
                    }
                }
                let out = ae_fps::Calibration::from_scene(&v["scene"])
                    .unwrap()
                    .select(
                        &mut state,
                        f("frame"),
                        f("line"),
                        f("clock"),
                        f("minimum_fps"),
                    )
                    .unwrap();
                let mut values = Vec::new();
                if a[0] == "ae-fps-refresh" {
                    values.extend([
                        baseline.frame,
                        baseline.clock_mhz,
                        baseline.line,
                        baseline.fps,
                    ]);
                }
                values.extend([
                    out.frame,
                    out.fps,
                    state.variable_frame,
                    state.fixed_rate,
                    state.variable_rate,
                ]);
                emit(&values);
            }
            "ae-delay-calibration" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let c = ae_delay_calibration::Calibration::from_scene(&v["scene"]).unwrap();
                let n = c
                    .counts(
                        v["frame"].as_f64().unwrap() as f32,
                        v["line"].as_f64().unwrap() as f32,
                        v["clock"].as_f64().unwrap() as f32,
                    )
                    .unwrap();
                println!("{},{}", n[0], n[1]);
            }
            "ae-pipeline-sequence" => println!(
                "{}",
                ae_pipeline_fixture::sequence(&serde_json::from_str(a[1]).unwrap())
            ),
            "ae-pipeline" => println!(
                "{}",
                ae_pipeline_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "ae-result" => println!(
                "{}",
                ae_result_fixture::run(&serde_json::from_str(a[1]).unwrap())
            ),
            "ae-publication" | "ae-publication-state" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let record = |value: &serde_json::Value| -> ae_publication::Record {
                    let text = value.as_str().unwrap();
                    core::array::from_fn(|i| {
                        u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()
                    })
                };
                let proposed: Vec<_> = v["proposed"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(record)
                    .collect();
                let published: Vec<_> = v["published"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(record)
                    .collect();
                let mut state = ae_publication::State {
                    empty_reference: v.get("empty_reference").map(record).unwrap_or([0; 244]),
                    previous_final: record(&v["previous"]),
                    published: core::array::from_fn(|i| {
                        published.get(i).copied().unwrap_or([0; 244])
                    }),
                    published_count: published.len(),
                    synchronized_frame: v["sync"].as_i64().unwrap() as i32,
                    last_result_frame: 0,
                };
                let mut convergence = ae_convergence::State {
                    dynamic_enabled: v["dynamic"].as_u64().unwrap_or(0) as u8,
                    gating_enabled: v["gating"].as_u64().unwrap_or(0) as u8,
                };
                let mut history = core::array::from_fn(|i| ae_environment::Record {
                    frame: i as i32,
                    current_exposure: 0.003,
                    published_exposure: 0.006,
                    error: 0.2,
                    queued: [0.001, 0.002, 0.003, 0.004, 0.005, 0.006],
                    queued_count: 2,
                });
                let state_mode = a[0] == "ae-publication-state";
                let out = if state_mode {
                    ae_publication::finish(
                        &mut state,
                        &mut convergence,
                        &mut history,
                        v["index"].as_u64().unwrap() as u32,
                        v["aggregate"].as_f64().unwrap() as f32,
                        ae_convergence::Exposure {
                            time_code: v["effective"][0].as_u64().unwrap() as u32,
                            gain_code: v["effective"][1].as_u64().unwrap() as u32,
                            isp_gain: v["effective"][2].as_f64().unwrap() as f32,
                        },
                        &proposed,
                        v["frame"].as_i64().unwrap() as i32,
                    )
                    .unwrap()
                } else {
                    ae_publication::select(
                        &proposed,
                        &state.previous_final,
                        &published,
                        v["frame"].as_i64().unwrap() as i32,
                        state.synchronized_frame,
                    )
                    .unwrap()
                };
                let hex =
                    |bytes: &[u8]| bytes.iter().map(|b| format!("{b:02x}")).collect::<String>();
                print!(
                    "{}:{}:{}:{}",
                    out.count,
                    out.synchronized_frame,
                    hex(&out.records.concat()),
                    hex(&out.final_record)
                );
                if state_mode {
                    let mut words = Vec::new();
                    for r in history {
                        words.extend([
                            r.frame as u32,
                            r.current_exposure.to_bits(),
                            r.published_exposure.to_bits(),
                            r.error.to_bits(),
                        ]);
                        words.extend(r.queued.map(f32::to_bits));
                        words.push(r.queued_count);
                    }
                    let bytes: Vec<u8> = words.into_iter().flat_map(u32::to_le_bytes).collect();
                    print!(
                        ":{}:{}:{}:{}:{}:{}:{}",
                        state.published_count,
                        state.last_result_frame,
                        convergence.dynamic_enabled,
                        convergence.gating_enabled,
                        hex(&state.published.concat()),
                        hex(&state.previous_final),
                        hex(&bytes)
                    );
                }
                println!();
            }
            "ae-conversion-queue" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let profile = calibration::SensorCalibration::from_value(&v["profile"]).unwrap();
                let calibration = profile.conversion(calibration::RuntimeTiming {
                    frame_length: 1360,
                    pixel_clock_mhz: 114.24,
                    line_length_pixels: 2800,
                });
                let number = |k: &str| v[k].as_f64().unwrap() as f32;
                let point = |x: &serde_json::Value| ae_route::Point {
                    time: x[0].as_f64().unwrap() as f32,
                    gain: x[1].as_f64().unwrap() as f32,
                    isp_gain: x[2].as_f64().unwrap() as f32,
                };
                let mut route: Vec<_> = v["route"].as_array().unwrap().iter().map(point).collect();
                let published: Vec<_> = v["published"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(point)
                    .collect();
                let limits = ae_route::Limits {
                    minimum_time: 0.00005,
                    maximum_time: 0.03,
                    minimum_gain: 1.,
                    maximum_gain: 512.,
                    time_quantum: 0.01,
                    floor_tolerance_coefficient: 8.,
                    line_length: 2800.,
                    pixel_clock_mhz: 114.24,
                };
                let out = ae_conversion_queue::linear(
                    point(&v["proposed"]),
                    number("target"),
                    number("held"),
                    &published,
                    v["frame_id"].as_i64().unwrap() as i32,
                    v["sync"].as_i64().unwrap() as i32,
                    v["count"].as_u64().unwrap() as usize,
                    &mut route,
                    limits,
                    calibration,
                    ae_register::Policy {
                        isp_range: [1., 32.],
                        time_range: [0.00005, 0.03],
                        gain_range: [1., 512.],
                        analogue_minimum: 1.,
                        time_quantum: 0.01,
                        flicker_enabled: true,
                        automatic: true,
                        suppress_isp_compensation: false,
                    },
                )
                .unwrap();
                let mut words = vec![
                    out.current.gain.to_bits(),
                    out.current.isp_gain.to_bits(),
                    out.current.seconds.to_bits(),
                    out.current.codes.integration_time,
                    out.current.codes.gain,
                ];
                for entry in out.intermediate.into_iter().flatten() {
                    let c = entry.converted;
                    words.extend([
                        entry.aggregate.to_bits(),
                        c.gain.to_bits(),
                        c.isp_gain.to_bits(),
                        c.seconds.to_bits(),
                        u32::MAX,
                        c.codes.integration_time,
                        c.codes.gain,
                        0,
                    ]);
                }
                words.extend(route.iter().map(|p| p.time.to_bits()));
                println!(
                    "{}",
                    words
                        .iter()
                        .map(|w| format!("{w:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-register" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let profile = calibration::SensorCalibration::from_value(&v["profile"]).unwrap();
                let c = profile.conversion(calibration::RuntimeTiming {
                    frame_length: v["frame"].as_u64().unwrap() as u32,
                    pixel_clock_mhz: v["clock"].as_f64().unwrap() as f32,
                    line_length_pixels: v["line"].as_u64().unwrap() as u32,
                });
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let range = |k: &str| core::array::from_fn(|i| v[k][i].as_f64().unwrap() as f32);
                let out = ae_register::linear(
                    f("seconds"),
                    f("gain"),
                    f("isp"),
                    v["dcg"].as_i64().unwrap() as i32,
                    c,
                    ae_register::Policy {
                        isp_range: range("isp_range"),
                        time_range: range("time_range"),
                        gain_range: range("gain_range"),
                        analogue_minimum: f("analogue_minimum"),
                        time_quantum: f("quantum"),
                        flicker_enabled: v["flicker"].as_bool().unwrap(),
                        automatic: v["automatic"].as_bool().unwrap(),
                        suppress_isp_compensation: v["suppress"].as_bool().unwrap(),
                    },
                )
                .unwrap();
                let words = [
                    out.codes.integration_time,
                    out.codes.gain,
                    out.gain.to_bits(),
                    out.seconds.to_bits(),
                    out.isp_gain.to_bits(),
                    out.mappings,
                ];
                println!(
                    "{}",
                    words
                        .iter()
                        .map(|w| format!("{w:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "exposure-decode" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let profile = calibration::SensorCalibration::from_value(&v["profile"]).unwrap();
                let c = profile.conversion(calibration::RuntimeTiming {
                    frame_length: v["frame"].as_u64().unwrap() as u32,
                    pixel_clock_mhz: v["clock"].as_f64().unwrap() as f32,
                    line_length_pixels: v["line"].as_u64().unwrap() as u32,
                });
                let result = exposure::decode_linear(
                    exposure::Codes {
                        integration_time: v["time_code"].as_u64().unwrap() as u32,
                        gain: v["gain_code"].as_u64().unwrap() as u32,
                    },
                    v["dcg"].as_i64().unwrap() as i32,
                    c,
                )
                .unwrap();
                emit(&[result.gain, result.seconds]);
            }
            "ae-convergence" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let exposure = |key: &str| ae_convergence::Exposure {
                    time_code: v[key][0].as_u64().unwrap() as u32,
                    gain_code: v[key][1].as_u64().unwrap() as u32,
                    isp_gain: v[key][2].as_f64().unwrap() as f32,
                };
                let mut state = ae_convergence::State {
                    dynamic_enabled: v["dynamic"].as_u64().unwrap() as u8,
                    gating_enabled: v["gating"].as_u64().unwrap() as u8,
                };
                ae_convergence::linear(
                    &mut state,
                    exposure("effective"),
                    exposure("proposed"),
                    exposure("published"),
                )
                .unwrap();
                println!("{},{}", state.dynamic_enabled, state.gating_enabled);
            }
            "ae-run-flag" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let previous: Vec<u16> = v["previous"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_u64().unwrap() as u16)
                    .collect();
                let current: Vec<u16> = v["current"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_u64().unwrap() as u16)
                    .collect();
                let overrides: Vec<u8> = v["overrides"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_u64().unwrap() as u8)
                    .collect();
                println!(
                    "{}",
                    ae_run_flag::select(
                        ae_run_flag::Policy {
                            enabled_4fb9: v["enabled"].as_u64().unwrap() as u8,
                            channel_mode_23cd: v["mode"].as_u64().unwrap() as u8,
                            unchanged_23cf: core::array::from_fn(|i| v["unchanged"][i]
                                .as_u64()
                                .unwrap()
                                as u8),
                            overrides_3d3c: overrides.try_into().unwrap(),
                        },
                        &previous,
                        &current
                    )
                    .unwrap()
                );
            }
            "ae-preprocess-history" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut history =
                    core::array::from_fn(|i| v["history"][i].as_f64().unwrap() as f32);
                let mut run = v["run"].as_bool().unwrap();
                if v["native_run"].as_bool().unwrap_or(false) {
                    let measured = (v["measured"].as_f64().unwrap() * 256.) as u16;
                    let previous = if !run {
                        measured
                    } else if measured == 0 {
                        65535
                    } else {
                        0
                    };
                    run = ae_run_flag::select(
                        ae_run_flag::Policy {
                            enabled_4fb9: 1,
                            channel_mode_23cd: 0,
                            unchanged_23cf: [0; 3],
                            overrides_3d3c: [0; 3],
                        },
                        &[previous],
                        &[measured],
                    )
                    .unwrap()
                        != 0;
                }
                let error = ae_preprocess::record_error(
                    &mut history,
                    v["frame"].as_u64().unwrap() as u32,
                    run,
                    v["measured"].as_f64().unwrap() as f32,
                    45.,
                )
                .unwrap();
                emit(&history.into_iter().chain([error]).collect::<Vec<_>>());
            }
            "awb-prepare-position" => {
                let mode = a[1].parse::<i32>().unwrap();
                println!(
                    "{}",
                    match isp32::awb_prepare_position(mode) {
                        isp32::ApplyPosition::Gain0 => 0,
                        isp32::ApplyPosition::Gain1 => 1,
                    }
                );
            }
            "sensor-sof" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let delay = v["delay"].as_i64().unwrap() as i32;
                let mut d = sensor_timing::Delays {
                    time: 0,
                    gain: 0,
                    dcg: 0,
                    split_gain: false,
                    split_dcg: false,
                    dcg_with_time: false,
                };
                assert_eq!(d.configure(delay, delay, 0), 0);
                let mut scheduler = sensor_scheduler::Scheduler::new(
                    1u32,
                    d,
                    sensor_scheduler::EffectPolicy {
                        shorten_enabled: v["shorten"].as_bool().unwrap(),
                        designated_frame: v["designated"].as_u64().unwrap() as u32,
                        shorten_all: v["all"].as_bool().unwrap(),
                    },
                )
                .unwrap();
                for n in v["requests"].as_array().unwrap() {
                    scheduler.enqueue(n.as_u64().unwrap() as u32).unwrap();
                }
                let fail = v["fail"].as_u64().unwrap() as u32;
                let out = v["frames"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|f| {
                        let o = scheduler.on_sof(f.as_u64().unwrap() as u32, |id| {
                            if id == fail {
                                -5
                            } else {
                                0
                            }
                        });
                        let map = scheduler
                            .effective()
                            .map(|e| format!("{}={}", e.frame, e.exposure))
                            .collect::<Vec<_>>()
                            .join(";");
                        format!(
                            "{},{},{},{}:{}",
                            o.status,
                            scheduler.last_sof,
                            scheduler.current,
                            o.written.unwrap_or(0),
                            map
                        )
                    })
                    .collect::<Vec<_>>();
                println!("{}", out.join("|"));
            }
            "sensor-delays" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut d = sensor_timing::Delays {
                    time: 10,
                    gain: 11,
                    dcg: 12,
                    split_gain: v["flags"][0].as_bool().unwrap(),
                    split_dcg: v["flags"][1].as_bool().unwrap(),
                    dcg_with_time: v["flags"][2].as_bool().unwrap(),
                };
                let status = d.configure(
                    v["time"].as_i64().unwrap() as i32,
                    v["gain"].as_i64().unwrap() as i32,
                    v["dcg"].as_i64().unwrap() as i32,
                );
                println!(
                    "{},{},{},{},{},{},{}",
                    status,
                    d.time,
                    d.gain,
                    d.dcg,
                    d.split_gain as u8,
                    d.split_dcg as u8,
                    d.dcg_with_time as u8
                );
            }
            "exposure-association" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let frames = v["frames"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|n| n.as_u64().unwrap() as u32)
                    .collect::<Vec<_>>();
                match exposure_association::effective_index(
                    &frames,
                    v["requested"].as_u64().unwrap() as u32,
                )
                .unwrap()
                {
                    Some(m) => println!("{},{}", if m.exact { 0 } else { 1 }, m.index + 10),
                    None => println!("-2,0"),
                }
            }
            "ae-controller" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let b = |k: &str| v[k].as_bool().unwrap();
                let point = ae_route::Point {
                    time: 0.003,
                    gain: 1.,
                    isp_gain: 1.,
                };
                let mut state = ae_controller::State {
                    history: core::array::from_fn(|i| ae_environment::Record {
                        frame: i as i32,
                        current_exposure: 0.003,
                        published_exposure: 0.003,
                        error: if i % 2 == 0 { 0.2 } else { -0.2 },
                        queued: [0.003, 0.006, 0.009, 0.012, 0.015, 0.018],
                        queued_count: 2,
                    }),
                    index: v["index"].as_u64().unwrap() as u32,
                    environment: ae_environment::State {
                        priming: b("priming"),
                        queued_count: 2,
                        held_exposure: 0.003,
                    },
                    delay: Default::default(),
                    cache: ae_route::Cache {
                        exposure: 0.003,
                        relative_threshold: 0.01,
                        force: b("force"),
                        point,
                    },
                    previous_error: f("previous"),
                    reference_error: f("reference"),
                    saturated: b("saturated"),
                };
                let mut route = vec![
                    (0., 1.),
                    (0.01, 1.),
                    (0.01, 4.),
                    (0.02, 8.),
                    (0.03, 15.5),
                    (0.03, 512.),
                ]
                .into_iter()
                .map(|(time, gain)| ae_route::Point {
                    time,
                    gain,
                    isp_gain: 1.,
                })
                .collect::<Vec<_>>();
                let h = v["histogram"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_u64().unwrap() as u32)
                    .collect::<Vec<_>>();
                let mut preprocessing_history =
                    core::array::from_fn(|i| v["damping_history"][i].as_f64().unwrap() as f32);
                let mut runtime = ae_run::State {
                    previous_q8: [100, 200, 300],
                    previous_mean: 11.,
                    previous_hdr_means: [12., 13., 14.],
                };
                let mut execute = |state: &mut ae_controller::State,
                                   route: &mut [ae_route::Point],
                                   histogram: &[u32],
                                   input: ae_decision::Input,
                                   policy: ae_controller::Policy,
                                   limits: ae_route::Limits,
                                   frame: i32,
                                   synchronized_frame: i32| {
                    if v["full_frame"].as_bool().unwrap_or(false) {
                        let mut frame_state = ae_frame::State {
                            error_history: preprocessing_history,
                            target: 45.,
                            current_error: 0.,
                            convergence: ae_convergence::State {
                                gating_enabled: b("enabled") as u8,
                                dynamic_enabled: b("dynamic_enabled") as u8,
                            },
                        };
                        let output = ae_frame::linear(
                            &mut frame_state,
                            &mut runtime,
                            state,
                            route,
                            histogram,
                            input,
                            policy,
                            limits,
                            ae_frame::Target {
                                levels: &[0., 1.],
                                points: &[45., 45.],
                                bias_percent: 0.,
                            },
                            frame,
                            synchronized_frame,
                            0.009,
                            [(input.measured * 256.) as u16, 512, 768],
                            [2., 3., 4.],
                        )?;
                        preprocessing_history = frame_state.error_history;
                        Ok(output.control.unwrap_or(ae_controller::Output {
                            point: ae_route::Point {
                                gain: 2.,
                                isp_gain: 1.,
                                time: 0.0045,
                            },
                            aggregate_exposure: 0.009,
                            relative_error: output.preprocessing_error,
                            held: false,
                            damping_diagnostics: None,
                        }))
                    } else if v["run_wrapper"].as_bool().unwrap_or(false) {
                        let output = ae_run::linear(
                            &mut runtime,
                            state,
                            route,
                            histogram,
                            input,
                            policy,
                            limits,
                            frame,
                            synchronized_frame,
                            v["run"].as_bool().unwrap(),
                            0.009,
                            [(input.measured * 256.) as u16, 512, 768],
                            [2., 3., 4.],
                        )?;
                        Ok(output.unwrap_or(ae_controller::Output {
                            point: ae_route::Point {
                                gain: 2.,
                                isp_gain: 1.,
                                time: 0.0045,
                            },
                            aggregate_exposure: 0.009,
                            relative_error: 0.,
                            held: false,
                            damping_diagnostics: None,
                        }))
                    } else if v["preprocess"].as_bool().unwrap_or(false) {
                        ae_controller::step_with_history(
                            state,
                            route,
                            histogram,
                            input,
                            policy,
                            limits,
                            frame,
                            synchronized_frame,
                            &mut preprocessing_history,
                        )
                    } else {
                        ae_controller::step(
                            state,
                            route,
                            histogram,
                            input,
                            policy,
                            limits,
                            frame,
                            synchronized_frame,
                        )
                    }
                };
                let selected = if let Some(scene) = v.get("policy_scene") {
                    ae_policy::Calibration::from_scene(scene)
                        .unwrap()
                        .select(b("enabled"), v["alternate"].as_bool().unwrap())
                        .unwrap()
                } else {
                    ae_policy::Selected {
                        tolerance_percent: 10.,
                        damping_under: 0.5,
                        damping_over: 0.4,
                    }
                };
                let out = execute(
                    &mut state,
                    &mut route,
                    &h,
                    ae_decision::Input {
                        target: 45.,
                        measured: f("measured"),
                        current_exposure: f("exposure"),
                        tolerance_percent: selected.tolerance_percent,
                        minimum_exposure: 0.00005,
                        maximum_exposure: 15.36,
                        saturated: false,
                    },
                    ae_controller::Policy {
                        dynamic: if v["bind_dynamic"].as_bool().unwrap_or(false) {
                            ae_dynamic_calibration::Calibration::from_scene(&v["policy_scene"])
                                .unwrap()
                                .dynamic(
                                    b("dynamic_enabled"),
                                    core::array::from_fn(|i| {
                                        v["damping_history"][i].as_f64().unwrap() as f32
                                    }),
                                )
                        } else if v["dynamic"].as_bool().unwrap_or(false) {
                            Some(ae_brightness::Dynamic {
                                enabled: b("dynamic_enabled"),
                                mode: if b("custom") {
                                    ae_damping::Mode::Custom {
                                        scale: 10.,
                                        middle: 0.95,
                                    }
                                } else {
                                    ae_damping::Mode::Default
                                },
                                history: core::array::from_fn(|i| {
                                    v["damping_history"][i].as_f64().unwrap() as f32
                                }),
                            })
                        } else {
                            None
                        },
                        damping_under: selected.damping_under,
                        damping_over: selected.damping_over,
                        fps: f("fps"),
                        delay_enabled: b("enabled"),
                        same_mode: b("same_mode"),
                        negative_delay: 3,
                        positive_delay: 2,
                    },
                    ae_route::Limits {
                        minimum_time: 0.00005,
                        maximum_time: 0.03,
                        minimum_gain: 1.,
                        maximum_gain: 512.,
                        time_quantum: 0.01,
                        floor_tolerance_coefficient: 8.,
                        line_length: 2800.,
                        pixel_clock_mhz: 114.24,
                    },
                    v["frame"].as_i64().unwrap() as i32,
                    v["sync"].as_i64().unwrap() as i32,
                )
                .unwrap();
                let mut words = vec![
                    out.aggregate_exposure.to_bits(),
                    out.point.gain.to_bits(),
                    out.point.isp_gain.to_bits(),
                    out.point.time.to_bits(),
                    out.relative_error.to_bits(),
                    state.previous_error.to_bits(),
                    state.reference_error.to_bits(),
                    state.environment.held_exposure.to_bits(),
                    state.environment.queued_count,
                    state.environment.priming as u32,
                    state.delay.negative_start as u32,
                    state.delay.positive_start as u32,
                    state.delay.negative_count as u32,
                    state.delay.positive_count as u32,
                    state.delay.changed as u32,
                    state.cache.exposure.to_bits(),
                    state.cache.point.gain.to_bits(),
                    state.cache.point.isp_gain.to_bits(),
                    state.cache.point.time.to_bits(),
                    state.cache.force as u32,
                    state.saturated as u32,
                ];
                for r in state.history {
                    words.extend([
                        r.frame as u32,
                        r.current_exposure.to_bits(),
                        r.published_exposure.to_bits(),
                        r.error.to_bits(),
                    ]);
                    words.extend(r.queued.map(f32::to_bits));
                    words.push(r.queued_count);
                }
                words.extend(route.iter().map(|p| p.time.to_bits()));
                if let Some(d) = out.damping_diagnostics {
                    words.extend([
                        d.slot as u32,
                        d.trend.to_bits(),
                        d.normalized_trend.to_bits(),
                        d.normalized_current.to_bits(),
                    ]);
                } else {
                    words.extend([u32::MAX, 0, 0, 0]);
                }

                words.extend(preprocessing_history.map(f32::to_bits));
                if v["run_wrapper"].as_bool().unwrap_or(false) {
                    words.push(state.index);
                    words.extend(runtime.previous_q8.map(u32::from));
                    words.push(runtime.previous_mean.to_bits());
                    words.extend(runtime.previous_hdr_means.map(f32::to_bits));
                }
                println!(
                    "{}",
                    words
                        .iter()
                        .map(|w| format!("{w:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-history" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let mut history: [ae_environment::Record; 5] = core::array::from_fn(|i| {
                    let r = &v["history"][i];
                    ae_environment::Record {
                        frame: r["frame"].as_i64().unwrap() as i32,
                        current_exposure: r["current"].as_f64().unwrap() as f32,
                        error: r["error"].as_f64().unwrap() as f32,
                        published_exposure: r["published"].as_f64().unwrap() as f32,
                        queued: core::array::from_fn(|j| r["queued"][j].as_f64().unwrap() as f32),
                        queued_count: r["count"].as_u64().unwrap() as u32,
                    }
                });
                let queue = v["queue"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|p| ae_route::Point {
                        time: p[0].as_f64().unwrap() as f32,
                        gain: p[1].as_f64().unwrap() as f32,
                        isp_gain: p[2].as_f64().unwrap() as f32,
                    })
                    .collect::<Vec<_>>();
                let index = v["index"].as_u64().unwrap() as u32;
                ae_environment::record_current(
                    &mut history,
                    index,
                    v["frame"].as_i64().unwrap() as i32,
                    f("current"),
                    f("error"),
                )
                .unwrap();
                ae_environment::publish(&mut history, index, f("published"), &queue).unwrap();
                let words = history
                    .iter()
                    .flat_map(|r| {
                        [
                            r.frame as u32,
                            r.current_exposure.to_bits(),
                            r.published_exposure.to_bits(),
                            r.error.to_bits(),
                        ]
                        .into_iter()
                        .chain(r.queued.iter().map(|v| v.to_bits()))
                        .chain([r.queued_count])
                    })
                    .collect::<Vec<_>>();
                println!(
                    "{}",
                    words
                        .iter()
                        .map(|w| format!("{w:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-environment" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let n = |k: &str| v[k].as_i64().unwrap();
                let history = core::array::from_fn(|i| {
                    let r = &v["history"][i];
                    ae_environment::Record {
                        error: r["error"].as_f64().unwrap() as f32,
                        published_exposure: r["published"].as_f64().unwrap() as f32,
                        queued: core::array::from_fn(|j| r["queued"][j].as_f64().unwrap() as f32),
                        ..Default::default()
                    }
                });
                let mut state = ae_environment::State {
                    priming: v["priming"].as_bool().unwrap(),
                    queued_count: n("count") as u32,
                    held_exposure: f("held"),
                };
                let out = ae_environment::adjust(
                    &mut state,
                    &history,
                    n("index") as u32,
                    n("frame") as i32,
                    n("sync") as i32,
                    f("current"),
                    f("candidate"),
                )
                .unwrap();
                println!(
                    "{:08x},{:08x},{},{}",
                    out.to_bits(),
                    state.held_exposure.to_bits(),
                    state.queued_count,
                    state.priming as u8
                );
            }
            "ae-brightness" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let h = v["histogram"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|v| v.as_u64().unwrap() as u32)
                    .collect::<Vec<_>>();
                let o = ae_brightness::standard(
                    &h,
                    ae_decision::Input {
                        target: f("target"),
                        measured: f("measured"),
                        current_exposure: f("exposure"),
                        tolerance_percent: f("tolerance"),
                        minimum_exposure: f("minimum"),
                        maximum_exposure: f("maximum"),
                        saturated: v["saturated"].as_bool().unwrap(),
                    },
                    f("under"),
                    f("over"),
                    f("fps"),
                )
                .unwrap();
                println!(
                    "{:08x},{:08x},{}",
                    o.exposure.to_bits(),
                    o.relative_error.to_bits(),
                    o.saturated as u8
                );
            }
            "ae-delay" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let f = |k: &str| v[k].as_f64().unwrap() as f32;
                let n = |k: &str| v[k].as_i64().unwrap();
                let mut state = ae_delay::State {
                    negative_start: n("negative_start") as i32,
                    positive_start: n("positive_start") as i32,
                    negative_count: n("negative_count") as u8,
                    positive_count: n("positive_count") as u8,
                    changed: v["changed"].as_bool().unwrap(),
                };
                let blocked = ae_delay::linear(
                    &mut state,
                    ae_delay::Input {
                        enabled: v["enabled"].as_bool().unwrap(),
                        same_mode: v["same_mode"].as_bool().unwrap(),
                        frame: n("frame") as i32,
                        previous_error: f("previous"),
                        current_error: f("current"),
                        reference_error: f("reference"),
                        negative_delay: n("negative_delay") as u8,
                        positive_delay: n("positive_delay") as u8,
                    },
                )
                .unwrap();
                println!(
                    "{},{},{},{},{},{}",
                    blocked as u8,
                    state.changed as u8,
                    state.negative_start,
                    state.positive_start,
                    state.negative_count,
                    state.positive_count
                );
            }
            "ae-gain-limits" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let pair =
                    |name: &str| core::array::from_fn(|i| v[name][i].as_f64().unwrap() as f32);
                let out = ae_gain_limits::linear(ae_gain_limits::Input {
                    analogue: pair("analogue"),
                    digital: pair("digital"),
                    isp: pair("isp"),
                    route_gain: pair("route_gain"),
                    route_isp: pair("route_isp"),
                    overrides: if v["override"].as_bool().unwrap() {
                        Some(core::array::from_fn(|i| {
                            v["gain_overrides"][i].as_f64().unwrap() as f32
                        }))
                    } else {
                        None
                    },
                })
                .unwrap();
                emit(&[
                    out.physical_gain[0],
                    out.physical_gain[1],
                    out.gain[0],
                    out.gain[1],
                    out.isp[0],
                    out.isp[1],
                ]);
            }
            "ae-shutter" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |s: &str| v[s].as_f64().unwrap() as f32;
                let b = if let Some(iq) = v.get("profile") {
                    let sensor = calibration::SensorCalibration::from_value(iq).unwrap();
                    let route = ae_route::from_profile(
                        &iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["ae_calib"]
                            ["LinearAeCtrl"]["Route"],
                    )
                    .unwrap();
                    ae_shutter::from_calibration(
                        &sensor,
                        calibration::RuntimeTiming {
                            frame_length: n("frame") as u32,
                            line_length_pixels: n("line") as u32,
                            pixel_clock_mhz: n("clock"),
                        },
                        &route,
                        None,
                        Some((0.01, false)),
                    )
                    .unwrap()
                } else {
                    ae_shutter::fixed_frame(ae_shutter::Input {
                        frame_length: n("frame"),
                        line_length: n("line"),
                        pixel_clock_mhz: n("clock"),
                        factors: core::array::from_fn(|i| v["factors"][i].as_f64().unwrap() as f32),
                        minimum_register: v["minimum"].as_u64().unwrap() as u16,
                        maximum_register_factors: core::array::from_fn(|i| {
                            v["maxfactors"][i].as_f64().unwrap() as f32
                        }),
                        route_minimum: n("route_min"),
                        route_maximum: n("route_max"),
                        overrides: if v["override"].as_bool().unwrap() {
                            Some([n("override_min"), n("override_max")])
                        } else {
                            None
                        },
                        flicker: if v["enabled"].as_bool().unwrap() {
                            Some((0.01, v["mode"].as_i64().unwrap() == 1))
                        } else {
                            None
                        },
                    })
                    .unwrap()
                };
                println!(
                    "{}",
                    [b.physical_minimum, b.physical_maximum, b.minimum, b.maximum]
                        .iter()
                        .map(|v| format!("{:08x}", v.to_bits()))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-flicker" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |s: &str| v[s].as_f64().unwrap() as f32;
                let result = ae_flicker::select(
                    ae_flicker::State {
                        quantum: n("prior"),
                        alternate: n("alternate"),
                        frequency_selector: 0,
                    },
                    v["enabled"].as_bool().unwrap(),
                    v["frequency"].as_i64().unwrap() as i32,
                    n("detected"),
                    Some(ae_flicker::LineTiming {
                        line_length: n("line"),
                        pixel_clock_mhz: n("clock"),
                        coefficient: n("coefficient"),
                    }),
                )
                .unwrap();
                println!(
                    "{}:{:08x}:{:08x}",
                    result.frequency_selector,
                    result.quantum.to_bits(),
                    result.alternate.to_bits()
                );
            }
            "ae-route" | "ae-route-profile" | "ae-route-cached" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |key: &str| v[key].as_f64().unwrap() as f32;
                let mut route = if a[0] == "ae-route-profile" {
                    ae_route::from_profile(&v["profile"]).unwrap()
                } else {
                    v["route"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|p| ae_route::Point {
                            time: p[0].as_f64().unwrap() as f32,
                            gain: p[1].as_f64().unwrap() as f32,
                            isp_gain: p[2].as_f64().unwrap() as f32,
                        })
                        .collect::<Vec<_>>()
                };
                let limits = ae_route::Limits {
                    minimum_time: n("tmin"),
                    maximum_time: n("tmax"),
                    minimum_gain: n("gmin"),
                    maximum_gain: n("gmax"),
                    time_quantum: n("quantum"),
                    floor_tolerance_coefficient: n("coefficient"),
                    line_length: n("line"),
                    pixel_clock_mhz: n("clock"),
                };
                let mut cache = ae_route::Cache {
                    exposure: v["prior"].as_f64().unwrap_or(0.) as f32,
                    relative_threshold: v["threshold"].as_f64().unwrap_or(0.) as f32,
                    force: v["force"].as_bool().unwrap_or(false),
                    point: ae_route::Point {
                        time: 0.004,
                        gain: 2.,
                        isp_gain: 1.5,
                    },
                };
                let result = if a[0] == "ae-route-cached" {
                    ae_route::split_cached(&mut route, n("exposure"), limits, &mut cache)
                } else {
                    ae_route::split(&mut route, n("exposure"), limits)
                }
                .unwrap();
                if a[0] == "ae-route-cached" {
                    emit(
                        &[result.gain, result.isp_gain, result.time]
                            .into_iter()
                            .chain(route.iter().map(|p| p.time))
                            .chain([cache.exposure, if cache.force { 1. } else { 0. }])
                            .collect::<Vec<_>>(),
                    );
                    continue;
                }
                println!(
                    "{}",
                    [result.gain, result.isp_gain, result.time]
                        .into_iter()
                        .chain(route.iter().map(|p| p.time))
                        .map(|v| format!("{:08x}", v.to_bits()))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-initial-target" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                println!(
                    "{:08x}",
                    ae_target::initial_from_scene(&v).unwrap().to_bits()
                );
            }
            "ae-target" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let array = |name: &str| {
                    v[name]
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|v| v.as_f64().unwrap() as f32)
                        .collect::<Vec<_>>()
                };
                let result = ae_target::select(
                    &array("levels"),
                    &array("points"),
                    v["exposure"].as_f64().unwrap() as f32,
                    v["bias"].as_f64().unwrap() as f32,
                )
                .unwrap();
                println!("{:08x}", result.to_bits());
            }
            "ae-linear-translation" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |s: &str| -> Vec<u8> {
                    (0..s.len())
                        .step_by(2)
                        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
                        .collect()
                };
                let raw = decode(v["raw"].as_str().unwrap());
                let params = decode(v["parameters"].as_str().unwrap());
                match ae_translation::measure_linear(&raw, params.as_slice().try_into().unwrap())
                    .unwrap()
                {
                    None => println!("invalid"),
                    Some(m) => println!(
                        "{}:{}:{}",
                        m.mean,
                        m.grid
                            .bytes()
                            .iter()
                            .map(|b| format!("{b:02x}"))
                            .collect::<String>(),
                        m.histogram
                            .iter()
                            .flat_map(|v| v.to_le_bytes())
                            .map(|b| format!("{b:02x}"))
                            .collect::<String>()
                    ),
                }
            }
            "ae-profile" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let (record, p) = ae_configuration::from_comm(
                    &v["comm"],
                    v["width"].as_u64().unwrap() as u32,
                    v["height"].as_u64().unwrap() as u32,
                )
                .unwrap();
                println!(
                    "{}:{}:{}:{}:{}",
                    p.histogram_mode,
                    p.raw_mode,
                    p.y_range,
                    p.channel_mask,
                    record
                        .iter()
                        .map(|b| format!("{b:02x}"))
                        .collect::<String>()
                );
            }
            "ae-configuration" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let geometry = ae_geometry::Geometry {
                    width: v["width"].as_u64().unwrap() as u32,
                    height: v["height"].as_u64().unwrap() as u32,
                    input: core::array::from_fn(|i| v["input"][i].as_f64().unwrap() as f32),
                    tone_mapped: core::array::from_fn(|i| v["tone"][i].as_f64().unwrap() as f32),
                };
                let weights = core::array::from_fn(|i| v["weights"][i].as_u64().unwrap() as u8);
                let (record, p) = ae_configuration::linear(
                    geometry,
                    &weights,
                    v["hist"].as_i64().unwrap() as i32,
                    v["raw"].as_i64().unwrap() as i32,
                    v["range"].as_i64().unwrap() as i32,
                    v["mask"].as_u64().unwrap() as u8,
                )
                .unwrap();
                println!(
                    "{}:{}:{}:{}:{}",
                    p.histogram_mode,
                    p.raw_mode,
                    p.y_range,
                    p.channel_mask,
                    record
                        .iter()
                        .map(|b| format!("{b:02x}"))
                        .collect::<String>()
                );
            }
            "ae-weights" => {
                let source: [u8; 225] = core::array::from_fn(|i| {
                    u8::from_str_radix(&a[2][i * 2..i * 2 + 2], 16).unwrap()
                });
                let mut output = [0xa5; 225];
                ae_weights::select(&mut output, &source, a[1].parse().unwrap()).unwrap();
                println!(
                    "{}",
                    output
                        .iter()
                        .map(|v| format!("{v:02x}"))
                        .collect::<String>()
                );
            }
            "ae-defaults" => println!(
                "{}",
                ae_geometry::defaults()
                    .iter()
                    .map(|v| format!("{v:02x}"))
                    .collect::<String>()
            ),
            "ae-geometry" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut record = if v["defaults"].as_bool().unwrap_or(false) {
                    ae_geometry::defaults()
                } else {
                    [0x5au8; ae_geometry::RECORD_BYTES]
                };
                let geometry = ae_geometry::Geometry {
                    width: v["width"].as_u64().unwrap() as u32,
                    height: v["height"].as_u64().unwrap() as u32,
                    input: core::array::from_fn(|i| v["input"][i].as_f64().unwrap() as f32),
                    tone_mapped: core::array::from_fn(|i| v["tone"][i].as_f64().unwrap() as f32),
                };
                let selected = ae_geometry::configure(
                    &mut record,
                    geometry,
                    v["mode"].as_i64().unwrap() as i32,
                )
                .unwrap();
                println!(
                    "{}:{}:{}",
                    selected[0],
                    selected[1],
                    record
                        .iter()
                        .map(|v| format!("{v:02x}"))
                        .collect::<String>()
                );
            }
            "isp-color" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut params = [0x5au8; isp32::PARAMETER_BYTES];
                let mode = v["mode"].as_i64().unwrap() as i32;
                match v["kind"].as_str().unwrap() {
                    "gamma" => {
                        let curve: [u16; 49] =
                            core::array::from_fn(|i| v["curve"][i].as_u64().unwrap() as u16);
                        isp_color::gamma(
                            &mut params,
                            mode != 0,
                            v["segment"].as_u64().unwrap() as u8,
                            v["dense"].as_bool().unwrap(),
                            v["offset"].as_u64().unwrap() as u16,
                            &curve,
                        );
                    }
                    "csm" => {
                        let coefficients =
                            core::array::from_fn(|i| v["coefficients"][i].as_f64().unwrap() as f32);
                        isp_color::csm(&mut params, mode, 1, 2, 3, &coefficients).unwrap();
                    }
                    "cgc" => isp_color::cgc(&mut params, mode, 1, 0),
                    _ => panic!("kind"),
                }
                println!(
                    "{}",
                    params
                        .iter()
                        .map(|x| format!("{x:02x}"))
                        .collect::<String>()
                );
            }
            "ae-measurement" => {
                use shieldsigner_rkaiq::{isp32::PARAMETER_BYTES, isp_ae_measurement::*};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut state = v["seed"].as_u64().unwrap() as u32;
                let mut next = || {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    (state >> 24) as u8
                };
                let mut params = [0u8; PARAMETER_BYTES];
                for b in &mut params {
                    *b = next();
                }
                let mut ae = [0u8; AE_BYTES];
                for b in &mut ae {
                    *b = next();
                }
                let mut histogram = [0u8; HISTOGRAM_BYTES];
                for b in &mut histogram {
                    *b = next();
                }
                let original = params;
                let source = v["record"].as_str().unwrap();
                let record = (0..source.len())
                    .step_by(2)
                    .map(|i| u8::from_str_radix(&source[i..i + 2], 16).unwrap())
                    .collect::<Vec<_>>();
                if v["kind"].as_str().unwrap() == "ae" {
                    apply_ae(
                        &mut params,
                        &mut ae,
                        &AeMeasurement::from_record(&record.try_into().unwrap()).unwrap(),
                    );
                } else {
                    apply_histogram(
                        &mut params,
                        &mut histogram,
                        &HistogramMeasurement::from_record(&record.try_into().unwrap()).unwrap(),
                    );
                }
                assert_eq!(&params[24..AE_OFFSET], &original[24..AE_OFFSET]);
                assert_eq!(
                    &params[HISTOGRAM_OFFSET + HISTOGRAM_BYTES..],
                    &original[HISTOGRAM_OFFSET + HISTOGRAM_BYTES..]
                );
                let hex = |b: &[u8]| b.iter().map(|v| format!("{v:02x}")).collect::<String>();
                println!(
                    "{}:{}:{}:{}:{}",
                    hex(&params[..24]),
                    hex(&params[AE_OFFSET..AE_OFFSET + AE_BYTES]),
                    hex(&params[HISTOGRAM_OFFSET..HISTOGRAM_OFFSET + HISTOGRAM_BYTES]),
                    hex(&ae),
                    hex(&histogram)
                );
            }
            "parameter-queue" => {
                use shieldsigner_rkaiq::parameter_queue::*;
                fn hex(b: &[u8]) -> String {
                    b.iter().map(|v| format!("{v:02x}")).collect()
                }
                fn decode(v: &serde_json::Value) -> BufferRecord {
                    let s = v.as_str().unwrap();
                    (0..s.len())
                        .step_by(2)
                        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
                        .collect::<Vec<_>>()
                        .try_into()
                        .unwrap()
                }
                struct Mock {
                    v: serde_json::Value,
                    trace: Vec<String>,
                    requested: u32,
                }
                impl Mock {
                    fn n(&self, key: &str) -> i32 {
                        self.v[key].as_i64().unwrap() as i32
                    }
                }
                impl Backend for Mock {
                    fn request_buffers(&mut self) -> i32 {
                        let mut request = [0u8; 20];
                        put(&mut request, 0, self.requested);
                        put(&mut request, 4, META_OUTPUT);
                        put(&mut request, 8, self.n("memory") as u32);
                        self.trace.push(format!("req:{}", hex(&request)));
                        if self.n("request_result") < 0 {
                            -9
                        } else {
                            self.requested = self.n("returned_count") as u32;
                            0
                        }
                    }
                    fn initialize_pool(&mut self) -> i32 {
                        self.trace.push("init".into());
                        self.n("init_result")
                    }
                    fn stream_on(&mut self) -> i32 {
                        self.trace.push("on:14".into());
                        self.n("stream_result")
                    }
                    fn stream_off(&mut self) -> i32 {
                        self.trace.push("off:14".into());
                        self.n("stream_result")
                    }
                    fn close(&mut self) {
                        self.trace.push("close".into());
                    }
                    fn finalize_pool(&mut self) {
                        self.trace.push("finalize".into());
                    }
                    fn lock(&mut self) {
                        self.trace.push("lock".into());
                    }
                    fn unlock(&mut self) {
                        self.trace.push("unlock".into());
                    }
                    fn queue(&mut self, r: &mut BufferRecord) -> i32 {
                        self.trace.push(format!("qbuf:{}", hex(r)));
                        let result = self.n("io_result");
                        if result >= 0 {
                            *r = decode(&self.v["mutation"]);
                        }
                        result
                    }
                    fn dequeue(&mut self, r: &mut BufferRecord) -> i32 {
                        self.trace.push(format!("dqbuf:{}", hex(r)));
                        let result = self.n("io_result");
                        if result >= 0 {
                            *r = decode(&self.v["response"]);
                        }
                        result
                    }
                }
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut buffers = v["records"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .enumerate()
                    .map(|(i, r)| {
                        let mut b = BufferState::from_record(decode(r)).unwrap();
                        b.queued = v
                            .get("busy")
                            .map_or(v["buffer_queued"].as_bool().unwrap(), |v| {
                                v[i].as_bool().unwrap()
                            });
                        b.returned_length = v["initial_length"].as_u64().unwrap() as u32;
                        b
                    })
                    .collect::<Vec<_>>();
                let mut q = Queue {
                    queued_count: v["queued"].as_u64().unwrap() as u32,
                    active: v["active"].as_bool().unwrap(),
                };
                let mut backend = Mock {
                    requested: v["count"].as_u64().unwrap() as u32,
                    v: v.clone(),
                    trace: vec![],
                };
                let mut index = None;
                let status = match v["op"].as_str().unwrap() {
                    "get" => {
                        let preferred = v["preferred"].as_i64().unwrap();
                        let count = if v["has_pool"].as_bool().unwrap() {
                            buffers.len()
                        } else {
                            0
                        };
                        match q.get_buffer(
                            &mut backend,
                            &mut buffers[..count],
                            if preferred < 0 {
                                None
                            } else {
                                Some(preferred as usize)
                            },
                        ) {
                            Ok(i) => {
                                index = Some(i);
                                0
                            }
                            Err(e) => e,
                        }
                    }
                    "prepare" => q.prepare(&mut backend),
                    "start" => q.start(&mut backend, v["prepared"].as_bool().unwrap()),
                    "queue" => q.queue(
                        &mut backend,
                        &mut buffers[0],
                        v["locked"].as_bool().unwrap(),
                        v["cache_sync"].as_bool().unwrap(),
                    ),
                    "dequeue" => match q.dequeue(
                        &mut backend,
                        &mut buffers,
                        v["memory"].as_u64().unwrap() as u32,
                        v["cache_sync"].as_bool().unwrap(),
                    ) {
                        Ok(i) => {
                            index = Some(i);
                            0
                        }
                        Err(e) => e,
                    },
                    "return" => {
                        q.return_to_pool(&mut backend, &mut buffers[0]);
                        0
                    }
                    "stop" => {
                        q.stop(&mut backend, v["has_pool"].as_bool().unwrap());
                        0
                    }
                    _ => panic!("unsupported queue fixture"),
                };
                println!(
                    "{}",
                    serde_json::json!({"status":status,"index":index,"queued":q.queued_count,"active":q.active,"requested":backend.requested,"trace":backend.trace,"buffers":buffers.iter().map(|b|serde_json::json!({"record":hex(&b.record),"queued":b.queued,"length":b.returned_length})).collect::<Vec<_>>()})
                );
            }
            "demosaic-frames" => {
                use shieldsigner_rkaiq::{demosaic_selection::Calibration, demosaic_runtime::State};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let calibration = Calibration::from_value(&v["calibration"]).unwrap();
                let raw = v["hardware"].as_str().unwrap();
                let hardware = (0..raw.len()).step_by(2).map(|i| u8::from_str_radix(&raw[i..i+2],16).unwrap()).collect::<Vec<_>>().try_into().unwrap();
                let mut state = State { iso: 50, reconfigure: true, hardware };
                let mut results = Vec::new();
                for frame in v["frames"].as_array().unwrap() {
                    state.reconfigure |= frame["reconfigure"].as_bool().unwrap();
                    let gains = frame["gains"].as_array().map(|g| core::array::from_fn(|i| g[i].as_f64().unwrap() as f32));
                    let result = state.process(&calibration, gains).unwrap();
                    let hex = |b: &[u8]| b.iter().map(|v| format!("{v:02x}")).collect::<String>();
                    results.push(serde_json::json!({"iso":state.iso,"reconfigure":state.reconfigure,"hardware":result.map(|r|hex(&r)),"cache":hex(&state.hardware)}));
                }
                println!("{}",serde_json::to_string(&results).unwrap());
            }
            "demosaic-select" => {
                use shieldsigner_rkaiq::{
                    demosaic_selection::Calibration, isp32::PARAMETER_BYTES, isp_demosaic::*,
                };
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |key: &str| {
                    let s = v[key].as_str().unwrap();
                    (0..s.len())
                        .step_by(2)
                        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
                        .collect::<Vec<_>>()
                };
                let hex = |b: &[u8]| b.iter().map(|v| format!("{v:02x}")).collect::<String>();
                let calibration = Calibration::from_value(&v["calibration"]).unwrap();
                let mut record: [u8; SELECTED_BYTES] = decode("previous").try_into().unwrap();
                let selected = calibration
                    .select(v["iso"].as_i64().unwrap() as i32)
                    .unwrap();
                selected.write_record(&mut record);
                let mut cached: HardwareRecord = decode("hardware").try_into().unwrap();
                let hardware = quantize(&mut cached, selected).unwrap();
                let mut state = v["seed"].as_u64().unwrap() as u32;
                let mut params = [0u8; PARAMETER_BYTES];
                for b in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *b = (state >> 24) as u8;
                }
                let before = params;
                apply(&mut params, &hardware);
                assert_eq!(&params[24..OFFSET], &before[24..OFFSET]);
                assert_eq!(&params[OFFSET + BYTES..], &before[OFFSET + BYTES..]);
                println!(
                    "{}:{}:{}:{}:{}",
                    hex(&record),
                    hex(&params[..24]),
                    hex(&params[OFFSET..OFFSET + BYTES]),
                    hex(&hardware),
                    hex(&cached)
                );
            }
            "dpcc-frames" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let calibration = shieldsigner_rkaiq::dpcc_calibration::Automatic::from_value(&v["calibration"]).unwrap();
                let mut state = shieldsigner_rkaiq::dpcc_runtime::State::default();
                let mut result = [0u8;192];
                let mut outputs = Vec::new();
                for frame in v["frames"].as_array().unwrap() {
                    state.reconfigure |= frame["reconfigure"].as_bool().unwrap();
                    let gains = frame["gains"].as_array().map(|g| core::array::from_fn(|i| g[i].as_f64().unwrap() as f32));
                    let update = state.process(&calibration,gains,&mut result).unwrap();
                    outputs.push(serde_json::json!({"iso":state.iso,"reconfigure":state.reconfigure,"updated":update,"result":result.iter().map(|v|format!("{v:02x}")).collect::<String>()}));
                }
                println!("{}",serde_json::to_string(&outputs).unwrap());
            }
            "dpcc-auto" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let calibration = shieldsigner_rkaiq::dpcc_calibration::Automatic::from_value(&v["calibration"]).unwrap();
                let s = v["result"].as_str().unwrap();
                let mut result = (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>().try_into().unwrap();
                calibration.process(v["iso"].as_i64().unwrap() as i32,&mut result).unwrap();
                println!("{}",result.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "dpcc-expert-init" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let table = shieldsigner_rkaiq::dpcc_calibration::expert_table(&v).unwrap();
                println!("{}",table.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "dpcc-select" => {
                use shieldsigner_rkaiq::dpcc_selection;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |key: &str| {
                    let s = v[key].as_str().unwrap();
                    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>()
                };
                let table = decode("table").try_into().unwrap();
                let mut result = decode("result").try_into().unwrap();
                dpcc_selection::select(&table,v["iso"].as_i64().unwrap() as i32,&mut result).unwrap();
                println!("{}",result.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "ccm-frames" => {
                use shieldsigner_rkaiq::{ccm_frame,isp_ccm::RESULT_BYTES};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let cal=shieldsigner_rkaiq::ccm_calibration::Automatic::from_value(&v["calibration"]).unwrap();
                let mut state=ccm_frame::State::new(&cal);let mut output=Vec::new();
                let hex=|b: &[u8]|b.iter().map(|v|format!("{v:02x}")).collect::<String>();
                let mut result=[0xa5;RESULT_BYTES];
                for frame in v["frames"].as_array().unwrap() {
                    state.active=frame["active"].as_bool().unwrap();state.attributes_changed=frame["attributes"].as_bool().unwrap();
                    state.reconfigure|=frame["reconfigure"].as_bool().unwrap();
                    let current=frame["current"].as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>().try_into().unwrap();
                    let mut info=ccm_frame::Information{current,damping:frame["damping"].as_f64().unwrap() as f32,gray:frame["gray"].as_bool().unwrap(),software_gray:frame["softwareGray"].as_bool().unwrap(),converged:false};
                    let updated=state.process(&cal,&mut info,&mut result).unwrap();
                    let auto=&state.automatic;
                    let mut selection=auto.selection.saturation.to_le_bytes().to_vec();selection.extend((auto.selection.illuminant as u32).to_le_bytes());selection.extend(auto.selection.high_name);selection.extend(auto.selection.low_name);selection.extend(auto.selection.matrix.iter().chain(auto.selection.offsets.iter()).flat_map(|v|v.to_le_bytes()));
                    let inputs=auto.baseline.iter().chain(auto.current.iter()).flat_map(|v|v.to_le_bytes()).collect::<Vec<_>>();
                    output.push(serde_json::json!({"updated":updated,"output":hex(&result),"softwareGray":info.software_gray,"informationConverged":info.converged,"result":hex(&auto.result),"selection":hex(&selection),"inputs":hex(&inputs),"alpha":auto.alpha.to_bits(),"saturation":auto.saturation.to_bits(),"converged":auto.converged,"frames":auto.frames,"inputsChanged":auto.inputs_changed,"published":auto.published}));
                }
                println!("{}",serde_json::json!(output));
            }
            "ccm-automatic" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let cal=shieldsigner_rkaiq::ccm_calibration::Automatic::from_value(&v["calibration"]).unwrap();
                let mut state=shieldsigner_rkaiq::ccm_automatic::State::new(&cal);let mut output=Vec::new();
                let hex=|b: &[u8]|b.iter().map(|v|format!("{v:02x}")).collect::<String>();
                let serialize=|state: &shieldsigner_rkaiq::ccm_automatic::State| {
                    let mut selection=state.selection.saturation.to_le_bytes().to_vec();selection.extend((state.selection.illuminant as u32).to_le_bytes());selection.extend(state.selection.high_name);selection.extend(state.selection.low_name);selection.extend(state.selection.matrix.iter().chain(state.selection.offsets.iter()).flat_map(|v|v.to_le_bytes()));
                    let inputs=state.baseline.iter().chain(state.current.iter()).flat_map(|v|v.to_le_bytes()).collect::<Vec<_>>();
                    serde_json::json!({"result":hex(&state.result),"selection":hex(&selection),"inputs":hex(&inputs),"alpha":state.alpha.to_bits(),"saturation":state.saturation.to_bits(),"converged":state.converged,"frames":state.frames,"inputsChanged":state.inputs_changed,"published":state.published})
                };
                if v["includeInitial"].as_bool().unwrap_or(false) {output.push(serialize(&state));}
                for frame in v["frames"].as_array().unwrap() {
                    let current=frame["current"].as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>().try_into().unwrap();
                    state.process(&cal,current,frame["damping"].as_f64().unwrap() as f32,frame["active"].as_bool().unwrap(),frame["attributes"].as_bool().unwrap(),frame["reconfigure"].as_bool().unwrap(),frame["gray"].as_bool().unwrap(),frame["publish"].as_bool().unwrap()).unwrap();
                    output.push(serialize(&state));
                }
                println!("{}",serde_json::json!(output));
            }
            "ccm-input" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let array=|p: &serde_json::Value|p.as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>().try_into().unwrap();
                let mut baseline=array(&v["baseline"]);let mut output=Vec::new();
                for frame in v["frames"].as_array().unwrap() {
                    let mut current=array(&frame["current"]);
                    let changed=shieldsigner_rkaiq::ccm_input::filter(&mut baseline,&mut current,frame["gainTolerance"].as_f64().unwrap() as f32,frame["wbTolerance"].as_f64().unwrap() as f32).unwrap();
                    let hex=baseline.iter().chain(current.iter()).flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>();
                    output.push(serde_json::json!({"records":hex,"changed":changed}));
                }
                println!("{}",serde_json::json!(output));
            }
            "ccm-tables" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let cal=shieldsigner_rkaiq::ccm_calibration::Automatic::from_value(&v).unwrap();
                let hex=|b: &[u8]|b.iter().map(|v|format!("{v:02x}")).collect::<String>();
                let floats=|v: &[f32]|hex(&v.iter().flat_map(|v|v.to_le_bytes()).collect::<Vec<_>>());
                let illuminants=cal.illuminants.iter().map(|ill| {
                    let values=ill.gains.iter().chain(ill.sensor_gains.iter()).chain(ill.saturations.iter()).copied().collect::<Vec<_>>();
                    let profiles=ill.profiles.iter().map(|p|serde_json::json!({"name":hex(&p.name),"values":floats(&std::iter::once(p.profile.saturation).chain(p.profile.matrix).chain(p.profile.offsets).collect::<Vec<_>>())})).collect::<Vec<_>>();
                    serde_json::json!({"values":floats(&values),"profiles":profiles})
                }).collect::<Vec<_>>();
                let luma=cal.luma.iter().flat_map(|r|std::iter::once(r.iso).chain(r.curve)).collect::<Vec<_>>();
                println!("{}",serde_json::json!({"flags":[cal.enabled,cal.damping_enabled,cal.enhancement_enabled],"tolerances":floats(&[cal.wb_tolerance,cal.gain_tolerance]),"illuminants":illuminants,"luma":floats(&luma),"alphaGains":floats(&cal.alpha_gains),"alphaScales":floats(&cal.alpha_scales),"enhancementGains":floats(&cal.enhancement_gains),"enhancementRatios":floats(&cal.enhancement_ratios),"staticResult":hex(&cal.static_result)}));
            }
            "ccm-calibration" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let s=v["result"].as_str().unwrap();
                let mut result=(0..s.len()).step_by(2).map(|i|u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>().try_into().unwrap();
                shieldsigner_rkaiq::ccm_calibration::static_fields(&v["calibration"],&mut result).unwrap();
                println!("{}",result.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "ccm-luma" => {
                use shieldsigner_rkaiq::ccm_luma::{Row,symmetric};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let array=|p: &serde_json::Value| p.as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>();
                let rows=v["rows"].as_array().unwrap().iter().map(|r|Row{iso:r["iso"].as_f64().unwrap() as f32,curve:array(&r["curve"]).try_into().unwrap()}).collect::<Vec<_>>();
                let mut curve=array(&v["curve"]).try_into().unwrap();
                let updated=symmetric(&rows,v["iso"].as_f64().unwrap() as f32,v["previousWeight"].as_f64().unwrap() as f32,v["previousUpper"].as_u64().unwrap() as usize,v["force"].as_bool().unwrap(),&mut curve).unwrap();
                let hex=curve.iter().flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>();
                println!("{}",serde_json::json!({"updated":updated,"curve":hex}));
            }
            "ccm-saturation" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut matrix=v["matrix"].as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>().try_into().unwrap();
                shieldsigner_rkaiq::ccm_saturation::apply(&mut matrix,v["alpha"].as_f64().unwrap() as f32,v["saturation"].as_f64().unwrap() as f32).unwrap();
                println!("{}",matrix.iter().flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>());
            }
            "ccm-damping" => {
                use shieldsigner_rkaiq::ccm_damping::State;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let state=|p: &serde_json::Value| { let x=p.as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>();State{matrix:x[..9].try_into().unwrap(),offsets:x[9..].try_into().unwrap()} };
                let mut cache=state(&v["initial"]);let mut output=Vec::new();
                for frame in v["frames"].as_array().unwrap() {
                    let converged=cache.process(&state(&frame["target"]),frame["damping"].as_f64().unwrap() as f32).unwrap();
                    let hex=cache.matrix.iter().chain(cache.offsets.iter()).flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>();
                    output.push(serde_json::json!({"result":hex,"converged":converged}));
                }
                println!("{}",serde_json::json!(output));
            }
            "ccm-runtime" => {
                use shieldsigner_rkaiq::{ccm_runtime::*,ccm_selection::Profile};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let floats=|p: &serde_json::Value| p.as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>();
                let mut all=Vec::new();
                for cal in v["calibration"].as_array().unwrap() {
                    all.push(cal["profiles"].as_array().unwrap().iter().map(|p| {
                        let mut name=[0u8;25];let bytes=p["name"].as_str().unwrap().as_bytes();name[..bytes.len()].copy_from_slice(bytes);
                        NamedProfile{name,profile:Profile{saturation:p["saturation"].as_f64().unwrap() as f32,matrix:floats(&p["matrix"]).try_into().unwrap(),offsets:floats(&p["offsets"]).try_into().unwrap()}}
                    }).collect::<Vec<_>>());
                }
                let calibration=v["calibration"].as_array().unwrap().iter().zip(&all).map(|(cal,profiles)|Illuminant{gains:floats(&cal["gains"]).try_into().unwrap(),sensor_gains:floats(&cal["sensorGains"]).try_into().unwrap(),saturations:floats(&cal["saturations"]).try_into().unwrap(),profiles}).collect::<Vec<_>>();
                let mut state=State{illuminant:0,saturation:0.,high_name:[0xa5;25],low_name:[0xa5;25],matrix:[0.;9],offsets:[0.;3]};
                let mut output=Vec::new();
                for frame in v["frames"].as_array().unwrap() {
                    let mut updated=frame["updated"].as_bool().unwrap();
                    let status=state.process(&calibration,frame["sensorGain"].as_f64().unwrap() as f32,floats(&frame["gains"]).try_into().unwrap(),frame["force"].as_bool().unwrap(),frame["pending"].as_bool().unwrap(),&mut updated).unwrap();
                    let hex=|b: &[u8]|b.iter().map(|v|format!("{v:02x}")).collect::<String>();
                    let bytes=state.matrix.iter().chain(state.offsets.iter()).flat_map(|v|v.to_le_bytes()).collect::<Vec<_>>();
                    output.push(serde_json::json!({"status":status,"illuminant":state.illuminant,"saturation":state.saturation.to_bits(),"high":hex(&state.high_name),"low":hex(&state.low_name),"result":hex(&bytes),"updated":updated}));
                }
                println!("{}",serde_json::json!(output));
            }
            "ccm-illuminant" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let pair = |p: &serde_json::Value| [p[0].as_f64().unwrap() as f32,p[1].as_f64().unwrap() as f32];
                let candidates=v["candidates"].as_array().unwrap().iter().map(pair).collect::<Vec<_>>();
                let out=shieldsigner_rkaiq::ccm_illuminant::estimate(&candidates,pair(&v["gains"])).unwrap();
                println!("{}",serde_json::json!({"index":out.index,"matched":out.matched}));
            }
            "ccm-selection" => {
                use shieldsigner_rkaiq::ccm_selection::{Profile,select};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let array = |x: &serde_json::Value| x.as_array().unwrap().iter().map(|n|n.as_f64().unwrap() as f32).collect::<Vec<_>>();
                let profiles = v["profiles"].as_array().unwrap().iter().map(|p|Profile { saturation:p["saturation"].as_f64().unwrap() as f32,matrix:array(&p["matrix"]).try_into().unwrap(),offsets:array(&p["offsets"]).try_into().unwrap() }).collect::<Vec<_>>();
                let out=select(&profiles,v["saturation"].as_f64().unwrap() as f32).unwrap();
                let hex=out.matrix.iter().chain(out.offsets.iter()).flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>();
                println!("{}",serde_json::json!({"high":out.high,"low":out.low,"clamped":out.clamped,"result":hex}));
            }
            "isp-ccm" => {
                use shieldsigner_rkaiq::{isp_ccm, isp32::PARAMETER_BYTES};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |key: &str| {
                    let s = v[key].as_str().unwrap();
                    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>()
                };
                let result = decode("result").try_into().unwrap();
                let mut parameters: [u8; PARAMETER_BYTES] = decode("parameters").try_into().unwrap();
                isp_ccm::apply(&mut parameters, &result).unwrap();
                println!("{}",parameters.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "lsc-frames" => {
                use shieldsigner_rkaiq::{lsc_frame,lsc_calibration::Automatic,isp_lsc::RESULT_BYTES};
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();let cal=Automatic::from_value(&v["calibration"]).unwrap();
                let mut state=lsc_frame::State::default();let mut output=[0xa5;RESULT_BYTES];let mut frames=Vec::new();
                for f in v["frames"].as_array().unwrap(){
                    if let Some(n)=f["seedFrameCount"].as_u64(){state.frame_count=n as u32;}
                    let current=core::array::from_fn(|i|f["current"][i].as_f64().unwrap() as f32);
                    let updated=state.process(&cal,lsc_frame::Information{current,damping:f["damping"].as_f64().unwrap() as f32,force:f["force"].as_bool().unwrap(),bypass:f["bypass"].as_bool().unwrap()},&mut output).unwrap();
                    let hex=|b:&[u8]|b.iter().map(|v|format!("{v:02x}")).collect::<String>();
                    let name=|b:&[u8]|String::from_utf8(b.iter().take_while(|b|**b!=0).copied().collect()).unwrap();
                    frames.push(serde_json::json!({"updated":updated,"result":hex(&output),"target":state.target.iter().flat_map(|n|n.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>(),"converged":state.converged,"inputChanged":state.input_changed,"frameCount":state.frame_count,"vignetting":format!("{:08x}",state.vignetting.to_bits()),"illuminant":state.illuminant,"high":name(&state.high),"low":name(&state.low),"last":core::iter::once(state.last_gain).chain(state.last_wb).map(|f|format!("{:08x}",f.to_bits())).collect::<Vec<_>>(),"history":&state.history.history[..state.history.len]}));
                }
                println!("{}",serde_json::json!(frames));
            }
            "lsc-damping" => {
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                let array=|key:&str|v[key].as_array().unwrap().iter().map(|v|u16::try_from(v.as_u64().unwrap()).unwrap()).collect::<Vec<_>>().try_into().unwrap();
                let mut previous=array("previous");let target=array("target");
                let converged=shieldsigner_rkaiq::lsc_damping::process(&mut previous,&target,v["factor"].as_f64().unwrap() as f32,v["enabled"].as_bool().unwrap(),v["frame"].as_u64().unwrap() as u32).unwrap();
                let samples=previous.iter().flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>();
                println!("{}",serde_json::json!({"samples":samples,"converged":converged}));
            }
            "lsc-tables" => {
                use shieldsigner_rkaiq::{lsc_tables,interpolate};
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                let floats=|key:&str|v[key].as_array().unwrap().iter().map(|v|v.as_f64().unwrap() as f32).collect::<Vec<_>>();
                let grids=v["profiles"].as_array().unwrap().iter().map(|p|p["samples"].as_array().unwrap().iter().map(|s|u16::try_from(s.as_u64().unwrap()).unwrap()).collect::<Vec<_>>().try_into().unwrap()).collect::<Vec<[u16;lsc_tables::SAMPLES]>>();
                let profiles=v["profiles"].as_array().unwrap().iter().zip(grids.iter()).map(|(p,samples)|lsc_tables::Profile{vignetting:p["vignetting"].as_f64().unwrap() as f32,samples}).collect::<Vec<_>>();
                let vig=interpolate(&floats("gains"),&floats("vig"),v["gain"].as_f64().unwrap() as f32).unwrap();
                let result=lsc_tables::select(&profiles,vig).unwrap();
                let bytes=result.samples.iter().flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>();
                println!("{}",serde_json::json!({"high":result.high,"low":result.low,"vignetting":format!("{:08x}",vig.to_bits()),"samples":bytes}));
            }
            "lsc-illuminant" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let pair=|p: &serde_json::Value|[p[0].as_f64().unwrap() as f32,p[1].as_f64().unwrap() as f32];
                let calibrated=v["calibrated"].as_array().unwrap().iter().map(pair).collect::<Vec<_>>();
                let mut state=shieldsigner_rkaiq::lsc_illuminant::State::default();let mut output=Vec::new();
                for frame in v["frames"].as_array().unwrap() {
                    let estimate=state.process(&calibrated,pair(frame)).unwrap();
                    output.push(match estimate {Some(e)=>serde_json::json!({"nearest":e.nearest,"selected":e.selected,"stable":e.stable_window,"history":&state.history[..state.len]}),None=>serde_json::json!({"nearest":null,"selected":null,"stable":false,"history":&state.history[..state.len]})});
                }
                println!("{}",serde_json::json!(output));
            }
            "lsc-gradients" => {
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let array=|key: &str|v[key].as_array().unwrap().iter().map(|v|u16::try_from(v.as_u64().unwrap()).unwrap()).collect::<Vec<_>>().try_into().unwrap();
                let (x,y)=shieldsigner_rkaiq::lsc_geometry::gradients(&array("x"),&array("y")).unwrap();
                println!("{}",x.iter().chain(y.iter()).flat_map(|v|v.to_le_bytes()).map(|v|format!("{v:02x}")).collect::<String>());
            }
            "isp-baynr" => {
                use shieldsigner_rkaiq::{isp_baynr,isp32::PARAMETER_BYTES};
                let v:serde_json::Value=serde_json::from_str(a[1]).unwrap();
                let decode=|key:&str|{let s=v[key].as_str().unwrap();(0..s.len()).step_by(2).map(|i|u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>()};
                let result=decode("result").try_into().unwrap();let mut parameters:[u8;PARAMETER_BYTES]=decode("parameters").try_into().unwrap();
                isp_baynr::apply(&mut parameters,&result);
                println!("{}",parameters.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "isp-lsc" => {
                use shieldsigner_rkaiq::{isp_lsc,isp32::PARAMETER_BYTES};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode=|key: &str| {let s=v[key].as_str().unwrap();(0..s.len()).step_by(2).map(|i|u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>()};
                let result=decode("result").try_into().unwrap();let mut parameters:[u8;PARAMETER_BYTES]=decode("parameters").try_into().unwrap();
                let mut state=isp_lsc::State{enabled:v["enabled"].as_bool().unwrap()};
                isp_lsc::apply(&mut parameters,&result,&mut state);
                println!("{}",serde_json::json!({"parameters":parameters.iter().map(|v|format!("{v:02x}")).collect::<String>(),"enabled":state.enabled}));
            }
            "isp-dpcc" => {
                use shieldsigner_rkaiq::{isp_dpcc, isp32::PARAMETER_BYTES};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |key: &str| {
                    let s = v[key].as_str().unwrap();
                    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>()
                };
                let result = decode("result").try_into().unwrap();
                let mut parameters: [u8; PARAMETER_BYTES] = decode("parameters").try_into().unwrap();
                isp_dpcc::apply(&mut parameters, &result);
                println!("{}",parameters.iter().map(|v|format!("{v:02x}")).collect::<String>());
            }
            "isp-demosaic" => {
                use shieldsigner_rkaiq::{isp32::PARAMETER_BYTES, isp_demosaic::*};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |key: &str| {
                    let s = v[key].as_str().unwrap();
                    (0..s.len())
                        .step_by(2)
                        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
                        .collect::<Vec<_>>()
                };
                let hex = |b: &[u8]| b.iter().map(|v| format!("{v:02x}")).collect::<String>();
                let mut cached: HardwareRecord = decode("hardware").try_into().unwrap();
                let hardware = if v["kind"].as_str().unwrap() == "quantize" {
                    let selected =
                        SelectedParameters::from_record(&decode("selected").try_into().unwrap())
                            .unwrap();
                    quantize(&mut cached, selected).unwrap()
                } else {
                    cached
                };
                let mut state = v["seed"].as_u64().unwrap() as u32;
                let mut params = [0u8; PARAMETER_BYTES];
                for b in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *b = (state >> 24) as u8;
                }
                let before = params;
                apply(&mut params, &hardware);
                assert_eq!(&params[24..OFFSET], &before[24..OFFSET]);
                assert_eq!(&params[OFFSET + BYTES..], &before[OFFSET + BYTES..]);
                println!(
                    "{}:{}:{}:{}",
                    hex(&params[..24]),
                    hex(&params[OFFSET..OFFSET + BYTES]),
                    hex(&hardware),
                    hex(&cached)
                );
            }
            "isp-black-level" => {
                use shieldsigner_rkaiq::{isp32::PARAMETER_BYTES, isp_black_level::*};
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let mut state = v["seed"].as_u64().unwrap() as u32;
                let mut params = [0u8; PARAMETER_BYTES];
                for b in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *b = (state >> 24) as u8;
                }
                let before = params;
                let mut cache = [0x77; BYTES];
                let channels = |k: &str| -> [i16; 4] {
                    v[k].as_array()
                        .unwrap()
                        .iter()
                        .map(|x| x.as_i64().unwrap() as i16)
                        .collect::<Vec<_>>()
                        .try_into()
                        .unwrap()
                };
                let config = Configuration {
                    enabled: v["enabled"].as_bool().unwrap(),
                    fixed: channels("fixed"),
                    stage1_enabled: v["stage1_enabled"].as_bool().unwrap(),
                    stage1: channels("stage1"),
                    optical_black_enabled: v["ob_enabled"].as_bool().unwrap(),
                    optical_black_offset: v["offset"].as_i64().unwrap() as i16,
                    optical_black_predgain: v["gain"].as_f64().unwrap() as f32,
                    optical_black_maximum: v["maximum"].as_i64().unwrap() as i32,
                };
                apply(&mut params, &mut cache, config).unwrap();
                assert_eq!(&params[24..OFFSET], &before[24..OFFSET]);
                assert_eq!(&params[OFFSET + BYTES..], &before[OFFSET + BYTES..]);
                let hex = |b: &[u8]| b.iter().map(|v| format!("{v:02x}")).collect::<String>();
                println!(
                    "{}:{}:{}",
                    hex(&params[..24]),
                    hex(&params[OFFSET..OFFSET + BYTES]),
                    hex(&cache)
                );
            }
            "isp-pipeline" | "isp-pad-cif" => {
                use shieldsigner_rkaiq::isp_pipeline::*;
                fn hex(v: &[u8]) -> String {
                    v.iter().map(|b| format!("{b:02x}")).collect()
                }
                struct Trace {
                    calls: Vec<String>,
                    operations: i32,
                    fail: i32,
                    error: i32,
                    formats: [Format; 2],
                    bits: i8,
                    adjust: bool,
                }
                impl Trace {
                    fn status(&mut self) -> i32 {
                        self.operations += 1;
                        if self.operations == self.fail {
                            self.error
                        } else {
                            0
                        }
                    }
                }
                impl Backend for Trace {
                    fn set_tx_format(&mut self, f: &Format, p: u32) {
                        self.calls.push(format!("tx:{p}:{}", hex(f)));
                    }
                    fn set_rx_format(&mut self, f: &Format, p: u32) {
                        self.calls.push(format!("rx:{p}:{}", hex(f)));
                    }
                    fn bits_per_pixel(&mut self, p: u32) -> i8 {
                        self.calls.push(format!("bpp:{p}"));
                        self.bits
                    }
                    fn set_scaler_format(&mut self, s: &Selection, p: u32, b: i8) {
                        self.calls.push(format!("scaler:{p}:{b}:{}", hex(s)));
                    }
                    fn get_format(&mut self, w: u32, p: u32, out: &mut Format) -> i32 {
                        self.calls.push(format!("get:{w}:{p}"));
                        let status = self.status();
                        if status == 0 {
                            *out = self.formats[(p == 2) as usize];
                        }
                        status
                    }
                    fn set_format(&mut self, f: &mut Format) -> i32 {
                        self.calls.push(format!("format:{}", hex(f)));
                        self.status()
                    }
                    fn set_selection(&mut self, s: &mut Selection) -> i32 {
                        self.calls.push(format!("selection:{}", hex(s)));
                        let status = self.status();
                        if status == 0 && self.adjust {
                            for (offset, mask) in [(8, 0x1234u32), (12, 0x8000)] {
                                let n =
                                    u32::from_le_bytes(s[offset..offset + 4].try_into().unwrap())
                                        ^ mask;
                                s[offset..offset + 4].copy_from_slice(&n.to_le_bytes());
                            }
                            for (offset, delta) in [(16, 1i32), (20, 2), (24, -2), (28, -4)] {
                                let n =
                                    u32::from_le_bytes(s[offset..offset + 4].try_into().unwrap())
                                        .wrapping_add(delta as u32);
                                s[offset..offset + 4].copy_from_slice(&n.to_le_bytes());
                            }
                            for b in &mut s[32..] {
                                *b ^= 0x5a;
                            }
                        }
                        status
                    }
                }
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let decode = |k: &str| {
                    let s = v[k].as_str().unwrap();
                    (0..s.len())
                        .step_by(2)
                        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
                        .collect::<Vec<_>>()
                };
                let mut trace = Trace {
                    calls: vec![],
                    operations: 0,
                    fail: v["fail"].as_i64().unwrap() as i32,
                    error: v["error"].as_i64().unwrap() as i32,
                    bits: v["bits"].as_i64().unwrap() as i8,
                    adjust: v["adjust"].as_bool().unwrap(),
                    formats: [
                        decode("sink").try_into().unwrap(),
                        decode("source").try_into().unwrap(),
                    ],
                };
                let config = Configuration {
                    shared_cif: v["shared"].as_bool().unwrap(),
                    shared_capture_first: v["first"].as_bool().unwrap(),
                    scaler: v["scaler"].as_bool().unwrap(),
                    pixel_format: v["pixel"].as_u64().unwrap() as u32,
                };
                let result = if a[0] == "isp-pad-cif" {
                    configure_pads(
                        &mut trace,
                        &decode("sensor").try_into().unwrap(),
                        &decode("crop").try_into().unwrap(),
                        InputRoute::Cif,
                    )
                } else {
                    setup(
                        &mut trace,
                        config,
                        &decode("sensor").try_into().unwrap(),
                        &decode("crop").try_into().unwrap(),
                    )
                };
                trace.calls.push(format!("return:{result}"));
                println!("{}", trace.calls.join(";"));
            }
            "ae-damping" => {
                use shieldsigner_rkaiq::ae_damping::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |key: &str| v[key].as_f64().unwrap() as f32;
                let history: [f32; 10] = v["history"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_f64().unwrap() as f32)
                    .collect::<Vec<_>>()
                    .try_into()
                    .unwrap();
                let mode = if v["custom"].as_bool().unwrap() {
                    Mode::Custom {
                        scale: n("custom_scale"),
                        middle: n("middle"),
                    }
                } else {
                    Mode::Default
                };
                let result = calculate(
                    n("coefficient"),
                    n("scale"),
                    v["enabled"].as_bool().unwrap(),
                    mode,
                    v["frame"].as_u64().unwrap() as u32,
                    &history,
                )
                .unwrap();
                if let Some(d) = result.diagnostics {
                    println!(
                        "{:08x}:{}:{:08x}:{:08x}:{:08x}",
                        result.coefficient.to_bits(),
                        d.slot,
                        d.trend.to_bits(),
                        d.normalized_trend.to_bits(),
                        d.normalized_current.to_bits()
                    );
                } else {
                    println!("{:08x}:none", result.coefficient.to_bits());
                }
            }
            "ae-decision" => {
                use shieldsigner_rkaiq::ae_decision::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |key: &str| v[key].as_f64().unwrap() as f32;
                let histogram = v["histogram"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_u64().unwrap() as u32)
                    .collect::<Vec<_>>();
                let input = Input {
                    target: n("target"),
                    measured: n("measured"),
                    current_exposure: n("exposure"),
                    tolerance_percent: n("tolerance"),
                    minimum_exposure: n("minimum"),
                    maximum_exposure: n("maximum"),
                    saturated: v["saturated"].as_bool().unwrap(),
                };
                let result = solve(&histogram, input).unwrap();
                println!(
                    "{:08x}:{}",
                    result.exposure.to_bits(),
                    result.saturated as u8
                );
            }
            "iq-exposure" => {
                use shieldsigner_rkaiq::calibration::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let profile = SensorCalibration::from_value(&v["profile"]).unwrap();
                let timing = RuntimeTiming {
                    frame_length: v["frame"].as_u64().unwrap() as u32,
                    pixel_clock_mhz: v["clock"].as_f64().unwrap() as f32,
                    line_length_pixels: v["line"].as_u64().unwrap() as u32,
                };
                let codes = profile
                    .linear_codes(
                        v["time"].as_f64().unwrap() as f32,
                        v["gain"].as_f64().unwrap() as f32,
                        timing,
                    )
                    .unwrap();
                println!("{}:{}", codes.integration_time, codes.gain);
            }
            "sensor-descriptor" => {
                use shieldsigner_rkaiq::sensor_descriptor::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                struct Trace {
                    v: serde_json::Value,
                    trace: Vec<String>,
                }
                impl Trace {
                    fn operation(&mut self, name: &str) -> Result<(), ()> {
                        self.trace.push(name.into());
                        if self.v["fail"]
                            .as_str()
                            .unwrap()
                            .split('+')
                            .any(|v| v == name)
                        {
                            Err(())
                        } else {
                            Ok(())
                        }
                    }
                    fn n(&self, key: &str) -> u32 {
                        self.v[key].as_u64().unwrap() as u32
                    }
                }
                impl Backend for Trace {
                    type Error = ();
                    fn format(&mut self) -> Result<Format, ()> {
                        self.operation("format")?;
                        Ok(Format {
                            width: self.n("width"),
                            height: self.n("height"),
                            media_bus_code: self.n("bus"),
                        })
                    }
                    fn minimum(&mut self, id: u32) -> Result<i32, ()> {
                        let name = match id {
                            HBLANK => "hblank",
                            VBLANK => "vblank",
                            _ => "exposure",
                        };
                        self.operation(name)?;
                        Ok(self.v[name].as_i64().unwrap() as i32)
                    }
                    fn frame_interval(&mut self) -> Result<(u32, u32), ()> {
                        self.operation("interval")?;
                        if self.v["fps_fail"] == true {
                            return Err(());
                        }
                        Ok((self.n("numerator"), self.n("denominator")))
                    }
                    fn pixel_rate(&mut self) -> Result<i64, ()> {
                        self.operation("pixel_rate")?;
                        Ok(self.v["pixel_rate"].as_i64().unwrap())
                    }
                    fn nr_switch(&mut self) -> Result<[u32; 4], ()> {
                        self.operation("nr")?;
                        Ok(core::array::from_fn(|i| {
                            self.v["nr"][i].as_u64().unwrap() as u32
                        }))
                    }
                    fn dcg_ratio(&mut self) -> Result<[u32; 3], ()> {
                        self.operation("dcg")?;
                        Ok(core::array::from_fn(|i| {
                            self.v["dcg"][i].as_u64().unwrap() as u32
                        }))
                    }
                }
                let mut backend = Trace {
                    v,
                    trace: Vec::new(),
                };
                let result = read(&mut backend);
                let (status, data) = match result {
                    Ok(d) => (
                        0,
                        d.bytes()
                            .iter()
                            .map(|v| format!("{v:02x}"))
                            .collect::<String>(),
                    ),
                    Err(_) => (-9, "-".into()),
                };
                println!("{}|{status}|{data}", backend.trace.join(";"));
            }
            "exposure" => {
                use shieldsigner_rkaiq::exposure::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |name: &str| v[name].as_f64().unwrap() as f32;
                let timing = |key: &str| {
                    let t = &v[key];
                    Timing {
                        minimum: t["minimum"].as_u64().unwrap() as u16,
                        step: t["step"].as_f64().unwrap() as f32,
                        offset: t["offset"].as_f64().unwrap() as f32,
                    }
                };
                let bands: Vec<_> = v["bands"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|b| {
                        let f = |i: usize| b[i].as_f64().unwrap() as f32;
                        GainBand {
                            lower: f(0),
                            upper: f(1),
                            scale: f(2),
                            offset: f(3),
                            exponent: f(4),
                            minimum: f(5),
                            maximum: f(6),
                        }
                    })
                    .collect();
                let cfg = Calibration {
                    gain: if v["model"] == 0 {
                        GainModel::Bands(&bands)
                    } else {
                        GainModel::Logarithmic
                    },
                    factors: core::array::from_fn(|i| v["factors"][i].as_f64().unwrap() as f32),
                    frame_length: n("frame_length"),
                    pixel_clock_mhz: n("pixel_clock"),
                    line_length_pixels: n("line_length"),
                    linear: timing("linear"),
                    hdr: [timing("hdr2"), timing("hdr3")],
                    linear_dcg_ratio: n("linear_ratio"),
                    hdr_dcg_ratio: n("hdr_ratio"),
                };
                let mode = match v["mode"].as_u64().unwrap() {
                    0 => Mode::Linear,
                    1 => Mode::HdrTwo,
                    _ => Mode::HdrThree,
                };
                let result = convert(
                    n("time"),
                    n("gain"),
                    mode,
                    v["dcg"].as_i64().unwrap() as i32,
                    cfg,
                )
                .unwrap();
                println!("{}:{}", result.integration_time, result.gain);
            }
            "sensor-linear" => {
                use shieldsigner_rkaiq::sensor::*;
                struct Trace {
                    descriptor: Descriptor,
                    trace: Vec<String>,
                    fail: usize,
                    calls: usize,
                }
                impl Trace {
                    fn operation(&mut self, text: String) -> Result<(), ()> {
                        self.trace.push(text);
                        self.calls += 1;
                        if self.fail == self.calls {
                            Err(())
                        } else {
                            Ok(())
                        }
                    }
                }
                impl Backend for Trace {
                    type Error = ();
                    fn descriptor(&mut self) -> Result<Descriptor, ()> {
                        self.trace.push("descriptor".into());
                        Ok(self.descriptor)
                    }
                    fn control(&mut self, id: u32, value: i32) -> Result<(), ()> {
                        self.operation(format!("control:{id:08x}:{value}"))
                    }
                    fn conversion_gain(&mut self, value: u32) -> Result<(), ()> {
                        self.operation(format!("dcg:{value}"))
                    }
                }
                let mut backend = Trace {
                    descriptor: Descriptor {
                        line_periods_per_field: a[1].parse().unwrap(),
                        output_height: a[2].parse().unwrap(),
                    },
                    trace: Vec::new(),
                    fail: a[10].parse().unwrap(),
                    calls: 0,
                };
                let exposure = LinearExposure {
                    frame_length_lines: a[3].parse().unwrap(),
                    dcg_mode: a[4].parse().unwrap(),
                    analogue_gain_code: a[5].parse().unwrap(),
                    digital_gain_code: a[6].parse().unwrap(),
                    coarse_integration_time: a[7].parse().unwrap(),
                };
                let mut mirror = if a[8] == "1" {
                    Some(a[9].parse().unwrap())
                } else {
                    None
                };
                let status = if program_linear(&mut backend, exposure, &mut mirror).is_ok() {
                    0
                } else {
                    -9
                };
                println!(
                    "{}|{status}|{}",
                    backend.trace.join(";"),
                    mirror.map(|v| v.to_string()).unwrap_or_else(|| "-".into())
                );
            }
            "aebig" => {
                use shieldsigner_rkaiq::ae::*;
                let mut state: u32 = a[1].parse().unwrap();
                fn next(s: &mut u32) -> u32 {
                    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                    *s
                }
                let input = core::array::from_fn(|_| next(&mut state));
                let raw_sums = RawSums {
                    red: core::array::from_fn(|_| next(&mut state)),
                    green: core::array::from_fn(|_| next(&mut state)),
                    blue: core::array::from_fn(|_| next(&mut state)),
                };
                let initial = core::array::from_fn(|_| (next(&mut state) >> 24) as u8);
                let mut output = BigGrid::from_bytes(&initial);
                let weights = core::array::from_fn(|_| (next(&mut state) >> 24) as u8);
                let read = |s: &str| {
                    let v: Vec<i16> = s.split(',').map(|v| v.parse().unwrap()).collect();
                    Bls {
                        red: v[0],
                        green_red: v[1],
                        green_blue: v[2],
                        blue: v[3],
                    }
                };
                let selection = match a[2] {
                    "1" => Selection::Luma,
                    "2" => Selection::Red,
                    "4" => Selection::Green,
                    "8" => Selection::Blue,
                    "14" => Selection::Rgb,
                    _ => Selection::RgbAndLuma,
                };
                let range = if a[3] == "0" {
                    LumaRange::Full
                } else {
                    LumaRange::Limited
                };
                let mut mean = a[7].parse().unwrap();
                let pixels = a[6]
                    .split(',')
                    .map(|v| v.parse().unwrap())
                    .collect::<Vec<u32>>()
                    .try_into()
                    .unwrap();
                correct_big_grid(
                    &input,
                    raw_sums,
                    &mut output,
                    &mut mean,
                    &weights,
                    selection,
                    range,
                    read(a[4]),
                    read(a[5]),
                    pixels,
                )
                .unwrap();
                println!(
                    "{}:{mean}",
                    output
                        .bytes()
                        .iter()
                        .map(|v| format!("{v:02x}"))
                        .collect::<String>()
                );
            }
            "aegrid" => {
                use shieldsigner_rkaiq::ae::*;
                let mut state: u32 = a[1].parse().unwrap();
                fn next(s: &mut u32) -> u32 {
                    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                    *s
                }
                let input = core::array::from_fn(|_| next(&mut state));
                let mut output =
                    Grid::from_words(core::array::from_fn(|_| (next(&mut state) >> 16) as u16));
                let weights = core::array::from_fn(|_| (next(&mut state) >> 24) as u8);
                let read_bls = |s: &str| {
                    let v: Vec<i16> = s.split(',').map(|v| v.parse().unwrap()).collect();
                    Bls {
                        red: v[0],
                        green_red: v[1],
                        green_blue: v[2],
                        blue: v[3],
                    }
                };
                let mut mean = a[6].parse().unwrap();
                let selection = match a[2] {
                    "1" => Selection::Luma,
                    "2" => Selection::Red,
                    "4" => Selection::Green,
                    "8" => Selection::Blue,
                    "14" => Selection::Rgb,
                    _ => Selection::RgbAndLuma,
                };
                let range = if a[3] == "0" {
                    LumaRange::Full
                } else {
                    LumaRange::Limited
                };
                correct_lite_grid(
                    &input,
                    &mut output,
                    &mut mean,
                    &weights,
                    selection,
                    range,
                    read_bls(a[4]),
                    read_bls(a[5]),
                )
                .unwrap();
                println!(
                    "{}:{mean}",
                    output
                        .words()
                        .iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "statistics" => {
                use shieldsigner_rkaiq::statistics::*;
                let mut state: u32 = a[1].parse().unwrap();
                let mut bytes = [0u8; BUFFER_BYTES];
                for b in &mut bytes {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *b = (state >> 24) as u8;
                }
                bytes[MEASUREMENT_OFFSET..MEASUREMENT_OFFSET + 4]
                    .copy_from_slice(&0x20u32.to_le_bytes());
                let stats = Statistics::parse(&bytes).unwrap();
                let grid = stats
                    .awb()
                    .unwrap()
                    .map(|v| format!("{},{},{},{}", v.red, v.green, v.blue, v.white_points))
                    .collect::<Vec<_>>()
                    .join(",");
                let sums = stats
                    .awb_sums()
                    .unwrap()
                    .map(|v| {
                        format!(
                            "{},{},{},{},{},{},{}",
                            v.red_normal,
                            v.blue_normal,
                            v.points_normal,
                            v.points_second,
                            v.red_big,
                            v.blue_big,
                            v.points_big
                        )
                    })
                    .collect::<Vec<_>>()
                    .join(",");
                let hist = stats
                    .awb_luma_histogram()
                    .unwrap()
                    .map(|v| v.to_string())
                    .collect::<Vec<_>>()
                    .join(",");
                println!("{}:{grid}:{sums}:{hist}", stats.frame_id());
            }
            "binding" => {
                use shieldsigner_rkaiq::discovery::*;
                let input: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let sensors: Vec<_> = input["sensors"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|s| {
                        let paths = |key: &str| {
                            s[key]
                                .as_array()
                                .unwrap()
                                .iter()
                                .map(|v| v.as_str().unwrap())
                                .collect::<Vec<_>>()
                        };
                        Sensor {
                            name: s["name"].as_str().unwrap(),
                            has_isp: s["isp"].as_bool().unwrap(),
                            isp_paths: paths("paths").try_into().unwrap(),
                            cif_paths: if s["cif"].is_null() {
                                None
                            } else {
                                Some(paths("cif").try_into().unwrap())
                            },
                            media: match s["media"].as_i64().unwrap() {
                                -1 => MediaStatus::Missing,
                                -2 => MediaStatus::OpenFailed,
                                -3 => MediaStatus::EntityUnavailable,
                                -4 => MediaStatus::NoLinks,
                                n => MediaStatus::FirstLinkFlags(n as u32),
                            },
                        }
                    })
                    .collect();
                println!(
                    "{}",
                    serde_json::to_string(&bound_sensor(&sensors, input["query"].as_str()))
                        .unwrap()
                );
            }
            "engine" => {
                use shieldsigner_rkaiq::engine::*;
                struct Trace(Vec<String>);
                impl Backend for Trace {
                    type Error = ();
                    fn initialize(&mut self, sensor: &str, iq: &str) -> Result<(), ()> {
                        self.0.push(format!("init:{sensor}:{iq}"));
                        Ok(())
                    }
                    fn listen_in_library(&mut self, enabled: bool) -> Result<(), ()> {
                        self.0.push(format!("listen:{}", enabled as u8));
                        Ok(())
                    }
                    fn multiple_cameras(&mut self) -> Result<(), ()> {
                        self.0.push("multicam:1".into());
                        Ok(())
                    }
                    fn prepare_linear(&mut self, w: u32, h: u32) -> Result<(), ()> {
                        self.0.push(format!("prepare:{w}:{h}:0"));
                        Ok(())
                    }
                    fn subscribe(&mut self, e: u32) -> Result<(), ()> {
                        self.0.push(format!("subscribe:{e}"));
                        Ok(())
                    }
                    fn start(&mut self) -> Result<(), ()> {
                        self.0.push("start".into());
                        Ok(())
                    }
                    fn stop(&mut self, keep: bool) -> Result<(), ()> {
                        self.0.push(format!("stop:{}", keep as u8));
                        Ok(())
                    }
                }
                let config = Config {
                    sensor: a[4],
                    iq_directory: a[5],
                    width: a[2].parse().unwrap(),
                    height: a[3].parse().unwrap(),
                    multiple_cameras: a[1] == "1",
                };
                let mut engine = Engine::prepare(Trace(Vec::new()), config).unwrap();
                if a[6] != "-" {
                    for e in a[6].split(',') {
                        engine.on_event(e.parse().unwrap()).unwrap();
                    }
                }
                println!("{}", engine.backend().0.join(";"));
            }
            "gain" => {
                use shieldsigner_rkaiq::gain::*;
                let mode = match a[1] {
                    "0" => HdrMode::Linear,
                    "1" => HdrMode::TwoFrame,
                    "2" => HdrMode::ThreeFrame,
                    _ => panic!("invalid HDR mode"),
                };
                let e = ExposureSet {
                    mode,
                    time: floats(a[5]).try_into().unwrap(),
                    analog_gain: floats(a[6]).try_into().unwrap(),
                    digital_gain: floats(a[7]).try_into().unwrap(),
                    iso: a[8]
                        .split(',')
                        .map(|v| v.parse().unwrap())
                        .collect::<Vec<_>>()
                        .try_into()
                        .unwrap(),
                };
                let scales = GainScales {
                    enabled: a[2] == "1",
                    short: f(a[3]),
                    middle: f(a[4]),
                };
                let out = pack_gain_registers(scales, e)
                    .unwrap()
                    .little_endian_bytes();
                println!(
                    "{}",
                    out.iter().map(|v| format!("{:02x}", v)).collect::<String>()
                );
            }
            "quant" => println!("{}", quantize_gain(f(a[1]), a[2].parse().unwrap()).unwrap()),
            "lut" => {
                let mut state: u32 = a[2].parse().unwrap();
                fn next(s: &mut u32) -> u16 {
                    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                    (*s >> 16) as u16
                }
                let mut first = [0; LUT_VALUES];
                let mut second = [0; LUT_VALUES];
                let mut out = [0; LUT_VALUES];
                for v in &mut first {
                    *v = next(&mut state);
                }
                for v in &mut second {
                    *v = next(&mut state);
                }
                blend_lut(f(a[1]), &first, &second, &mut out).unwrap();
                println!(
                    "{}",
                    out.iter()
                        .map(|v| format!("{:04x}", v))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            _ => panic!("unknown fixture operation"),
        }
    }
}

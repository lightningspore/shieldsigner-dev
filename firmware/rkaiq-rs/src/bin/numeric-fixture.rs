//! Line protocol used by the ARM-original differential harness.
use shieldsigner_rkaiq::*;
use std::io::{self, BufRead};
#[path = "../awb_preparation_fixture.rs"]
mod awb_preparation_fixture;
#[path = "../awb_translation_fixture.rs"]
mod awb_translation_fixture;
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
fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let a: Vec<_> = line.split_whitespace().collect();
        match a[0] {
            "awb-translation" => println!(
                "{}",
                awb_translation_fixture::run(&serde_json::from_str(a[1]).unwrap())
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
                let lights: Vec<_> = source
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
                let out = execute(
                    &mut state,
                    &mut route,
                    &h,
                    ae_decision::Input {
                        target: 45.,
                        measured: f("measured"),
                        current_exposure: f("exposure"),
                        tolerance_percent: 10.,
                        minimum_exposure: 0.00005,
                        maximum_exposure: 15.36,
                        saturated: false,
                    },
                    ae_controller::Policy {
                        dynamic: if v["dynamic"].as_bool().unwrap_or(false) {
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
                        damping_under: 0.5,
                        damping_over: 0.4,
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
                    .map(|r| {
                        let mut b = BufferState::from_record(decode(r)).unwrap();
                        b.queued = v["buffer_queued"].as_bool().unwrap();
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

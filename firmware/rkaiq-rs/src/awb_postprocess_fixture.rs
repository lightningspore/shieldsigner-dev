use crate::{
    awb_gain, awb_gain_adjust, awb_gain_clip,
    awb_gain_history::History,
    awb_postprocess::*,
    awb_single_color::{ColorTemperature, Line},
};
use serde_json::{json, Value};
fn array<const N: usize>(v: &Value) -> [f32; N] {
    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
}
fn temperature(t: ColorTemperature) -> Value {
    json!({"valid":t.valid,"cct":t.cct.to_bits(),"ccri":t.ccri.to_bits()})
}
pub fn initial(v: &Value) -> State<32> {
    initial_with_capacity(v)
}
pub fn initial_with_capacity<const CAP: usize>(v: &Value) -> State<CAP> {
    let values = |key: &str| {
        v[key]
            .as_array()
            .unwrap()
            .iter()
            .map(array)
            .collect::<Vec<[f32; 4]>>()
    };
    let raw = values("raw_history");
    let out = values("output_history");
    let zero = ColorTemperature {
        valid: false,
        cct: 0.,
        ccri: 0.,
    };
    State::<CAP> {
        raw_history: History::from_values(&raw).unwrap(),
        output_history: History::from_values(&out).unwrap(),
        previous: array(&v["previous"]),
        coefficient: v["coefficient"].as_f64().unwrap() as f32,
        effective_coefficient: 0.9,
        current: array(&v["candidate"]),
        raw: [2.; 4],
        clipped_gain: [3.; 4],
        adjust_before: [4.; 4],
        adjust_after: [5.; 4],
        offset_gain: [6.; 4],
        damped: [7.; 4],
        adjust_coordinates_before: [12., 13.],
        adjust_coordinates_after: [14., 15.],
        clipped: v["clipped"].as_bool().unwrap(),
        history_updated: false,
        converged: false,
        damping_stable: false,
        temperature: zero,
        top: [zero; 4],
    }
}
pub fn run(v: &Value) -> Value {
    let line = |key: &str| Line {
        a: v[key][0].as_f64().unwrap() as f32,
        b: v[key][1].as_f64().unwrap() as f32,
        c: v[key][2].as_f64().unwrap() as f32,
        valid: v[key][3].as_bool().unwrap(),
    };
    let mut state = initial(v);
    let clip_knots = [2000., 5000., 8000.];
    let lower = [0.2; 3];
    let upper = [0.2; 3];
    let clip = awb_gain_clip::Calibration {
        first: line("first"),
        second: line("second"),
        daylight: v["daylight"].as_bool().unwrap(),
        daylight_threshold: 100,
        daylight_minimum_cct: 5000.,
        bounds: Some(awb_gain_clip::Bounds {
            cct: &clip_knots,
            negative_tint: &lower,
            positive_tint: &upper,
        }),
    };
    let lut = &v["lut"];
    let luts = [awb_gain_adjust::Lut {
        sample: lut["sample"].as_f64().unwrap() as f32,
        x: array(&lut["x"]),
        y: array(&lut["y"]),
        mapped_x: array(&lut["mapped_x"]),
        mapped_y: array(&lut["mapped_y"]),
    }];
    let adjustment = awb_gain_adjust::Settings {
        temperature_mode: true,
        sample: 0.,
        first: line("first"),
        second: line("second"),
    };
    let settings = Settings {
        history_target: v["target"].as_i64().unwrap() as i32,
        tolerance: v["tolerance"].as_f64().unwrap() as f32,
        history_convergence: v["history_convergence"].as_f64().unwrap() as f32,
        damped_convergence: v["damped_convergence"].as_f64().unwrap() as f32,
        damping_threshold: v["damping_threshold"].as_f64().unwrap() as f32,
        brightness: v["brightness"].as_u64().unwrap() as u32,
        clipping: if v["clip"].as_bool().unwrap() {
            Some(&clip)
        } else {
            None
        },
        adjustment: if v["adjust"].as_bool().unwrap() {
            Some(Adjustment {
                luts: &luts,
                settings: &adjustment,
            })
        } else {
            None
        },
        offsets: if v["offset_enabled"].as_bool().unwrap() {
            Some(array(&v["offsets"]))
        } else {
            None
        },
        first: line("first"),
        second: line("second"),
    };
    let lights: Vec<_> = v["lights"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| Light {
            gain: array(&v["gain"]),
            probability: v["probability"].as_f64().unwrap() as f32,
        })
        .collect();
    if let Some(wb) = v.get("scene_iq") {
        let scene = crate::awb_calibration::Scene::from_value(wb).unwrap();
        scene
            .with_post_settings(
                settings.brightness,
                v["sample"].as_f64().unwrap() as f32,
                v["iso"].as_f64().unwrap() as f32,
                settings.damping_threshold,
                |post| {
                    state.finish(
                        awb_gain::normalize(array(&v["candidate"])).unwrap(),
                        &lights,
                        post,
                    )
                },
            )
            .unwrap()
            .unwrap();
    } else {
        state
            .finish(
                awb_gain::normalize(array(&v["candidate"])).unwrap(),
                &lights,
                &settings,
            )
            .unwrap();
    }
    output(&state)
}
pub fn output<const CAP: usize>(state: &State<CAP>) -> Value {
    let raw: Vec<_> = state
        .raw_history
        .values()
        .iter()
        .map(|v| v.map(f32::to_bits))
        .collect();
    let out: Vec<_> = state
        .output_history
        .values()
        .iter()
        .map(|v| v.map(f32::to_bits))
        .collect();
    json!({"current":state.current.map(f32::to_bits),"previous":state.previous.map(f32::to_bits),"raw":state.raw.map(f32::to_bits),"clipped_gain":state.clipped_gain.map(f32::to_bits),"adjust_before":state.adjust_before.map(f32::to_bits),"adjust_after":state.adjust_after.map(f32::to_bits),"offset_gain":state.offset_gain.map(f32::to_bits),"damped":state.damped.map(f32::to_bits),"coordinates_before":state.adjust_coordinates_before.map(f32::to_bits),"coordinates_after":state.adjust_coordinates_after.map(f32::to_bits),"coefficient":state.coefficient.to_bits(),"effective":state.effective_coefficient.to_bits(),"clipped":state.clipped,"updated":state.history_updated,"converged":state.converged,"damping_stable":state.damping_stable,"raw_history":raw,"output_history":out,"temperature":temperature(state.temperature),"top":state.top.map(temperature)})
}

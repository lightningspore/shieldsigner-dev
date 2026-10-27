use crate::awb_site::*;
use serde_json::{json, Value};
pub fn run(v: &Value) -> Value {
    let gain = |key: &str| core::array::from_fn(|i| v[key][i].as_f64().unwrap() as f32);
    let mut current = gain("gain");
    let mut state = State {
        matched: v["matched"].as_bool().unwrap(),
        frames: v["frames"].as_u64().unwrap() as u32,
    };
    state
        .apply(
            &mut current,
            &Input {
                frame: v["frame"].as_u64().unwrap() as u32,
                application_flag: v["application_flag"].as_bool().unwrap(),
                application_mode: v["application_mode"].as_i64().unwrap() as i32,
                reference_valid: v["reference_valid"].as_bool().unwrap(),
                reference_gain: gain("reference_gain"),
                reference_sample: v["reference_sample"].as_f64().unwrap() as f32,
                sample: v["sample"].as_f64().unwrap() as f32,
            },
            &Settings {
                enabled: v["enabled"].as_bool().unwrap(),
                frame_limit: v["frame_limit"].as_u64().unwrap() as u32,
                reuse_enabled: v["reuse_enabled"].as_bool().unwrap(),
                gain_threshold: v["gain_threshold"].as_f64().unwrap() as f32,
                sample_threshold: v["sample_threshold"].as_f64().unwrap() as f32,
            },
        )
        .unwrap();
    json!({"gain":current.map(f32::to_bits),"matched":state.matched,"frames":state.frames})
}

use crate::{awb_gain_adjust::*, awb_single_color::Line};
use serde_json::{json, Value};
fn array<const N: usize>(v: &Value) -> [f32; N] {
    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
}
pub fn run(v: &Value) -> Value {
    let luts: Vec<_> = v["luts"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| Lut {
            sample: v["sample"].as_f64().unwrap() as f32,
            x: array(&v["x"]),
            y: array(&v["y"]),
            mapped_x: array(&v["mapped_x"]),
            mapped_y: array(&v["mapped_y"]),
        })
        .collect();
    if v["kind"].as_str().unwrap() == "shift" {
        return match shift(&luts[0], array(&v["input"])) {
            Ok(values) => json!(values.map(f32::to_bits)),
            Err(_) => json!({"rejected":true}),
        };
    }
    let line = |key: &str| Line {
        a: v[key][0].as_f64().unwrap() as f32,
        b: v[key][1].as_f64().unwrap() as f32,
        c: v[key][2].as_f64().unwrap() as f32,
        valid: v[key][3].as_bool().unwrap(),
    };
    let mut state = State {
        gain: array(&v["gain"]),
        before: [12., 13.],
        after: [14., 15.],
    };
    let settings = Settings {
        temperature_mode: v["mode"].as_i64().unwrap() == 1,
        sample: if v["selector"].as_i64().unwrap() == 1 {
            &v["sample"]
        } else {
            &v["alternate_sample"]
        }
        .as_f64()
        .unwrap() as f32,
        first: line("first"),
        second: line("second"),
    };
    if state.adjust(&luts, &settings).is_err() {
        return json!({"rejected":true});
    }
    json!({"gain":state.gain.map(f32::to_bits),"before":state.before.map(f32::to_bits),"after":state.after.map(f32::to_bits)})
}

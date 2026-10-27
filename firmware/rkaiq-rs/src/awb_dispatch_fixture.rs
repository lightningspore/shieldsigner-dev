use crate::awb_dispatch::State;
use serde_json::{json, Value};
pub fn run(v: &Value) -> Value {
    let gain = |key: &str| core::array::from_fn(|i| v[key][i].as_f64().unwrap() as f32);
    let mut current = gain("current");
    let mut previous = gain("previous");
    let mut state = State {
        countdown: v["countdown"].as_i64().unwrap() as i32,
        frame: v["frame"].as_u64().unwrap() as u32,
    };
    let scale = v["scale"]
        .as_array()
        .map(|s| [s[0].as_f64().unwrap() as f32, s[1].as_f64().unwrap() as f32]);
    let action = state
        .process(
            v["update"].as_bool().unwrap(),
            v["complete"].as_bool().unwrap(),
            &mut current,
            scale,
            |g| {
                *g = gain("computed");
                previous = *g;
                Ok(())
            },
        )
        .unwrap();
    json!({"gain":current.map(f32::to_bits),"previous":previous.map(f32::to_bits),"countdown":state.countdown,"frame":state.frame,"calculated":action.calculated,"reconfigure":action.reconfigure})
}

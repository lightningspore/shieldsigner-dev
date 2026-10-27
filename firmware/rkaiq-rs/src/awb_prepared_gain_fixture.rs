use serde_json::{json, Value};
use shieldsigner_rkaiq::{
    awb_calibration::{GainRuntime, Scene},
    awb_dispatch::Action,
    awb_gain_controller::LightResult,
    awb_gain_frame,
    awb_preparation::*,
    awb_probability::Curve,
    InvalidInput,
};
fn put(b: &mut [u8], o: usize, n: u32) {
    b[o..o + 4].copy_from_slice(&n.to_le_bytes());
}
fn gain(b: &mut [u8], o: usize, g: [f32; 4]) {
    for (i, n) in g.iter().enumerate() {
        put(b, o + i * 4, n.to_bits());
    }
}
pub fn run(
    v: &Value,
    scene: &Scene,
    state: &mut awb_gain_frame::State<64>,
    output: &mut [LightResult],
    runtime: &GainRuntime<'_>,
) -> Result<(Action, Value), InvalidInput> {
    let s = &v["controller"];
    let m = &s["measurement"];
    let n = scene.lights.entries.len();
    let text = m["raw"].as_str().unwrap();
    let raw: Vec<u8> = (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap())
        .collect();
    let raw: [u8; FRAME_BYTES] = raw.try_into().unwrap();
    let mut lights = vec![LightRecord([0; LIGHT_BYTES]); n];
    for light in &mut lights {
        for r in 0..2 {
            put(
                &mut light.0,
                r * REGION_BYTES,
                m["cache_count"].as_u64().unwrap() as u32,
            );
            gain(&mut light.0, r * REGION_BYTES + 4, [2., 1., 1., 3.]);
        }
        gain(&mut light.0, 0x9c, [1.; 4]);
    }
    let mut seen = vec![if m["seen"].as_bool().unwrap() { 1 } else { 0 }; n];
    let mut second = vec![0; n];
    let mut total = vec![0; n];
    let mut grid = *runtime.grid;
    let mode = if m["rename"].as_bool().unwrap() {
        b"old".as_slice()
    } else {
        &raw[0x1d70 + 28..0x1d70 + 92]
            .split(|b| *b == 0)
            .next()
            .unwrap()
    };
    let mut name = [0u8; 64];
    name[..mode.len()].copy_from_slice(mode);
    let mut measurements = State {
        update: !runtime.numeric.update,
        stability_mask: 0,
        history: [[1.; 4]; 4],
        mode_names: [ModeName(name); 4],
        seen: &mut seen,
        active_lights: n as u8,
        complete: s["complete"].as_bool().unwrap(),
        lights: &mut lights,
        second_counts: &mut second,
        total_counts: &mut total,
        previous_pre_gain: runtime
            .scale
            .map(|s| [s[0], 1., 1., s[1]])
            .unwrap_or([1.; 4]),
        grid_valid: runtime.grid_valid,
        second_grid_valid: false,
        grid: &mut grid,
        exclusions_valid: false,
        exclusions: [[0; REGION_BYTES]; 7],
        exclusion_aggregate: [0; REGION_BYTES],
        histogram_cache: [[0; 8]; 4],
        histogram_aggregate: [0; 8],
    };
    let before = crate::awb_preparation_fixture::render(&measurements);
    let knots = [0., 1000., 10000.];
    let weights = [0.5, 0.5, 0.5];
    let settings = Settings {
        groups: 1,
        fast_light_count: 4,
        stability_threshold: f32::NAN,
        prior_sample: f32::NAN,
        exclusion_kind: core::array::from_fn(|i| m["kinds"][i].as_i64().unwrap() as i32),
        exclusion_weight: [Curve {
            knots: &knots,
            weights: &weights,
        }; 4],
    };
    let ignored_grid = [[f32::NAN; 3]; 225];
    let poisoned_runtime = GainRuntime {
        active_lights: 0,
        fast: !runtime.fast,
        grid_valid: !runtime.grid_valid,
        grid: &ignored_grid,
        ..*runtime
    };
    let result = scene.prepare_gain_frame(
        state,
        &mut measurements,
        &Frame(&raw),
        &settings,
        [10, 20],
        output,
        &poisoned_runtime,
    );
    if result.is_err() {
        assert_eq!(
            crate::awb_preparation_fixture::render(&measurements),
            before
        );
    }
    result.map(|a|(a,json!({"update":measurements.update,"complete":measurements.complete,"active":measurements.active_lights,"cache":crate::awb_preparation_fixture::render(&measurements)})))
}

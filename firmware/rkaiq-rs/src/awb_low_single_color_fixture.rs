use crate::{
    awb_high_gain::{Light, LightResult},
    awb_low_gain, awb_low_single_color,
    awb_single_color::{self, Line},
    awb_single_color_grid::{self, Candidate, Color},
};
use serde_json::{json, Value};
fn array<const N: usize>(v: &Value) -> [f32; N] {
    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
}
fn line(v: &Value) -> Line {
    Line {
        a: v[0].as_f64().unwrap() as f32,
        b: v[1].as_f64().unwrap() as f32,
        c: v[2].as_f64().unwrap() as f32,
        valid: v[3].as_bool().unwrap(),
    }
}
pub fn confidence(c: &Value) -> awb_single_color::Calibration {
    awb_single_color::Calibration {
        brightness_knots: array(&c["brightness_knots"]),
        brightness_weights: array(&c["brightness_weights"]),
        density_knots: array(&c["density_knots"]),
        density_weights: array(&c["density_weights"]),
        distance_knots: array(&c["distance_knots"]),
        cct_knots: array(&c["cct_knots"]),
        distance_weights: core::array::from_fn(|i| array(&c["distance_weights"][i])),
        disagreement_knots: array(&c["disagreement_knots"]),
        disagreement_weights: array(&c["disagreement_weights"]),
    }
}
pub fn run(
    low: awb_low_gain::State<32>,
    lights: &[Light],
    output: &mut [LightResult],
    history: &[[f32; 4]],
    settings: &awb_low_gain::Settings,
    v: &Value,
) -> (awb_low_gain::State<32>, Value) {
    let s = &v["single"];
    let candidates: Vec<_> = s["candidates"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| Candidate {
            red: v[0].as_f64().unwrap() as f32,
            blue: v[1].as_f64().unwrap() as f32,
        })
        .collect();
    let colors: Vec<_> = s["colors"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| Color {
            chroma: v["chroma"].as_f64().unwrap() as f32,
            hue: v["hue"].as_f64().unwrap() as f32,
            cct_knots: array(&v["knots"]),
            distance_thresholds: array(&v["thresholds"]),
        })
        .collect();
    let classifier = awb_single_color_grid::Calibration {
        candidates: &candidates,
        colors: &colors,
        alpha: s["alpha"].as_f64().unwrap() as f32,
        history_target: v["target"].as_u64().unwrap() as u16,
        first: line(&s["first"]),
        second: line(&s["second"]),
    };
    let confidence = confidence(&s["confidence"]);
    let grid = core::array::from_fn(|i| array(&s["grid"][i]));
    let high: Vec<_> = s["high_history"]
        .as_array()
        .unwrap()
        .iter()
        .map(array)
        .collect();
    let input = awb_low_single_color::Input {
        mode: s["mode"].as_i64().unwrap() as i32,
        grid_valid: s["grid_valid"].as_bool().unwrap(),
        grid: &grid,
        classifier: &classifier,
        confidence: &confidence,
        brightness_sample: s["brightness_sample"].as_f64().unwrap() as f32,
        density: s["density"].as_f64().unwrap() as f32,
        acceptance_threshold: s["threshold"].as_f64().unwrap() as f32,
        estimated_gain: array(&s["estimated"]),
        high_history: &high,
    };
    let mut state = awb_low_single_color::State {
        low,
        detection: awb_single_color_grid::Detection {
            selected: 0x5a5a5a5a,
            color: 0x5a5a5a5a,
            candidate_counts: [0x5a5a5a5a; 14],
            color_counts: [0x5a5a5a5a; 14],
            valid: true,
            disagreements: 0x5a5a5a5a,
            votes: 0x5a5a5a5a,
            mean_distance: f32::from_bits(0x5a5a5a5a),
            gain: [9.; 4],
        },
        single_weight: 0.75,
    };
    state
        .calculate(lights, output, history, settings, &input)
        .unwrap();
    let r = state.detection;
    (
        state.low,
        json!({"selected":r.selected,"color":r.color,"candidate_counts":r.candidate_counts,"color_counts":r.color_counts,"valid":r.valid,"disagreements":r.disagreements,"votes":r.votes,"mean":r.mean_distance.to_bits(),"gain":r.gain.map(f32::to_bits),"weight":state.single_weight.to_bits()}),
    )
}

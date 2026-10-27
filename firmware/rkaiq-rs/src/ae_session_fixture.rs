use serde_json::{json, Value};
use shieldsigner_rkaiq::*;
fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}
fn snapshot(s: &ae_session::Session, error: f32) -> Value {
    let state = &s.state;
    let c = &state.controller;
    let p = &state.publication;
    let r = &state.retained_records[state.retained_count - 1];
    let w = |o| u32::from_le_bytes(r[o..o + 4].try_into().unwrap());
    let mut words = vec![
        state.last_aggregate.to_bits(),
        w(4),
        w(12),
        w(0),
        w(32),
        w(36),
        error.to_bits(),
        state.frame.target.to_bits(),
        c.previous_error.to_bits(),
        c.reference_error.to_bits(),
        c.environment.held_exposure.to_bits(),
        p.published_count as u32,
        c.index,
        p.synchronized_frame as u32,
        p.last_result_frame as u32,
        state.frame.convergence.dynamic_enabled as u32,
        state.frame.convergence.gating_enabled as u32,
        c.environment.priming as u32,
        c.saturated as u32,
        c.delay.changed as u32,
        c.cache.force as u32,
        c.delay.negative_start as u32,
        c.delay.positive_start as u32,
        c.delay.negative_count as u32,
        c.delay.positive_count as u32,
        c.cache.exposure.to_bits(),
        c.cache.relative_threshold.to_bits(),
        c.cache.point.gain.to_bits(),
        c.cache.point.isp_gain.to_bits(),
        c.cache.point.time.to_bits(),
    ];
    words.extend(state.frame.error_history.map(f32::to_bits));
    words.extend(state.runtime.previous_q8.map(u32::from));
    words.push(state.runtime.previous_mean.to_bits());
    words.extend(state.runtime.previous_hdr_means.map(f32::to_bits));
    let mut history = Vec::new();
    for r in c.history {
        let mut words = vec![
            r.frame as u32,
            r.current_exposure.to_bits(),
            r.published_exposure.to_bits(),
            r.error.to_bits(),
        ];
        words.extend(r.queued.map(f32::to_bits));
        words.push(r.queued_count);
        for w in words {
            history.extend(w.to_le_bytes());
        }
    }
    let pre = &s.preprocessing;
    json!({"words":words,"pre":[pre.frame as u32,pre.measured.to_bits(),pre.auxiliary_mean.to_bits(),pre.normalized_brightness.to_bits(),pre.near_maximum as u32,pre.near_minimum as u32,pre.environment_level.to_bits(),pre.alternate_damping as u32],"history":hex(&history),"published":hex(&p.published.concat()),"previous":hex(&p.previous_final),"empty":hex(&p.empty_reference),"exposure":hex(&pre.exposure),"route":s.route.iter().map(|p|p.time.to_bits()).collect::<Vec<_>>()})
}
pub fn run(v: &Value) -> String {
    let mut session = ae_session::Session::from_profile(
        &v["profile"],
        calibration::RuntimeTiming {
            frame_length: v["frame"].as_u64().unwrap() as u32,
            line_length_pixels: 2800,
            pixel_clock_mhz: 114.24,
        },
        v["width"].as_u64().unwrap() as u32,
        v["height"].as_u64().unwrap() as u32,
    )
    .unwrap();
    let mut results = vec![snapshot(&session, 0.)];
    for frame in v["frames"].as_array().unwrap() {
        let text = frame["effective"].as_str().unwrap();
        let effective = (0..text.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap())
            .collect::<Vec<_>>()
            .try_into()
            .unwrap();
        let q = core::array::from_fn(|i| frame["q8"][i].as_u64().unwrap() as u16);
        let histogram = frame["histogram"]
            .as_array()
            .unwrap()
            .iter()
            .map(|n| n.as_u64().unwrap() as u32)
            .collect::<Vec<_>>();
        let out = session
            .step(
                frame["id"].as_i64().unwrap() as i32,
                q,
                &histogram,
                effective,
            )
            .unwrap();
        let error = out
            .frame
            .control
            .map_or(out.frame.preprocessing_error, |v| v.relative_error);
        results.push(snapshot(&session, error));
    }
    serde_json::to_string(&results).unwrap()
}

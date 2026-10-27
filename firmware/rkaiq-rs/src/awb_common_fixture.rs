use serde_json::{json, Value};
pub fn run(v: &Value) -> Value {
    let c = match crate::awb_calibration::Common::from_value(v) {
        Ok(c) => c,
        Err(e) => return json!({"error":e}),
    };
    let line = |l: crate::awb_single_color::Line| json!({"coefficients":[l.a.to_bits(),l.b.to_bits(),l.c.to_bits()],"valid":l.valid});
    json!({"night_gain":c.night_gain.map(f32::to_bits),"lines":c.lines.map(line),"daylight_min":c.daylight_cct_minimum.to_bits(),
        "clip":c.clip_tables.iter().map(|v|v.iter().map(|n|n.to_bits()).collect::<Vec<_>>()).collect::<Vec<_>>(),
        "remosaic":[c.remosaic_enabled,c.remosaic_inverse],"sensor_gain":c.sensor_gain.map(f32::to_bits),"weights":c.history_weights,
        "knots":c.brightness_knots,"percentages":c.night_percentages,"environment":c.environment_thresholds,"distance":c.distance_thresholds.map(f32::to_bits),"probability":c.probability_thresholds,
        "relative":c.relative_count_threshold.to_bits(),"damping":[c.damping.step.to_bits(),c.damping.minimum.to_bits(),c.damping.maximum.to_bits(),c.luma_history_target as u32,c.damping.variance_threshold.to_bits()],
        "convergence":[c.history_convergence.to_bits(),c.damped_convergence.to_bits()],"stable":c.stabilization,"target":c.region_history_target,"variance":c.region_variance_threshold.to_bits(),"smart":c.initial_smart.map(f32::to_bits),"countdown":c.initial_countdown})
}

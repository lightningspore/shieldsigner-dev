use serde_json::{json, Value};
use shieldsigner_rkaiq::awb_measurement_weights::*;
pub fn run(v: &Value) -> String {
    let data = v["rows"].as_array().unwrap();
    let ratios: Vec<Vec<f32>> = data
        .iter()
        .map(|r| {
            r["ratios"]
                .as_array()
                .unwrap()
                .iter()
                .map(|x| x.as_f64().unwrap() as f32)
                .collect()
        })
        .collect();
    let weights: Vec<Vec<[f32; 9]>> = data
        .iter()
        .map(|r| {
            r["weights"]
                .as_array()
                .unwrap()
                .iter()
                .map(|a| core::array::from_fn(|i| a[i].as_f64().unwrap() as f32))
                .collect()
        })
        .collect();
    let rows: Vec<_> = data
        .iter()
        .enumerate()
        .map(|(i, r)| Row {
            brightness: r["brightness"].as_f64().unwrap() as f32,
            ratios: &ratios[i],
            weights: &weights[i],
        })
        .collect();
    let mut record = [0xa5; 1204];
    record[0x2e] = v["enable"][0].as_bool().unwrap() as u8;
    record[0x2f] = v["enable"][1].as_bool().unwrap() as u8;
    let mut cache = core::array::from_fn(|i| v["previous"][i].as_f64().unwrap() as f32);
    let input = Input {
        frame_counter: v["frame"].as_u64().unwrap() as u32,
        brightness: v["brightness"].as_u64().unwrap() as u32,
        histogram: core::array::from_fn(|i| v["histogram"][i].as_i64().unwrap() as i32),
        perfect: core::array::from_fn(|i| v["perfect"][i].as_bool().unwrap()),
        minimum_count: v["minimum_count"].as_f64().unwrap() as f32,
        minimum_brightness: v["minimum_brightness"].as_u64().unwrap() as u32,
        damping: v["damping"].as_f64().unwrap() as f32,
    };
    let reached = if let Some(iq) = v.get("iq") {
        shieldsigner_rkaiq::awb_calibration::MeasurementWeighting::from_value(iq)
            .unwrap()
            .apply(&mut record, &mut cache, &input)
    } else {
        apply(&mut record, &mut cache, &rows, &input)
    }
    .unwrap();
    json!({"reached":reached,"cache":cache.map(f32::to_bits),"record":record.iter().map(|b|format!("{b:02x}")).collect::<String>()}).to_string()
}

use serde_json::{json, Value};
pub fn run(v: &Value) -> String {
    let mut record = [v["fill"].as_u64().unwrap() as u8; 1204];
    if let Some(initial) = v.get("initial") {
        for (i, n) in initial.as_array().unwrap().iter().enumerate() {
            record[0x4a + i * 2..0x4c + i * 2]
                .copy_from_slice(&(n.as_u64().unwrap() as u16).to_le_bytes());
        }
    }
    let brightness = v["brightness"].as_u64().unwrap() as u32;
    let changed = if let Some(iq) = v.get("iq") {
        shieldsigner_rkaiq::awb_calibration::MeasurementLimits::from_value(iq)
            .unwrap()
            .apply(brightness, &mut record)
            .unwrap()
    } else {
        let floats = |v: &Value| -> Vec<f32> {
            v.as_array()
                .unwrap()
                .iter()
                .map(|x| x.as_f64().unwrap() as f32)
                .collect()
        };
        let knots = floats(&v["knots"]);
        let values: [Vec<f32>; 8] = core::array::from_fn(|i| floats(&v["values"][i]));
        shieldsigner_rkaiq::awb_measurement_limits::Limits {
            knots: &knots,
            values: core::array::from_fn(|i| &values[i][..]),
        }
        .apply(brightness, &mut record)
        .unwrap()
    };
    json!({"changed":changed,"record":record.iter().map(|b|format!("{b:02x}")).collect::<String>()})
        .to_string()
}

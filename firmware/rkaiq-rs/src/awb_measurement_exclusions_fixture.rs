use serde_json::Value;
use shieldsigner_rkaiq::{awb_measurement_exclusions::*, awb_probability::Curve};
pub fn run(v: &Value) -> String {
    let mut record = [0xa5; 1204];
    let brightness = v["brightness"].as_f64().unwrap() as f32;
    if let Some(iq) = v.get("iq") {
        shieldsigner_rkaiq::awb_calibration::MeasurementExclusions::from_value(iq)
            .unwrap()
            .apply_weights(&mut record, brightness)
            .unwrap();
    } else {
        let floats = |v: &Value| -> Vec<f32> {
            v.as_array()
                .unwrap()
                .iter()
                .map(|x| x.as_f64().unwrap() as f32)
                .collect()
        };
        let knots: Vec<_> = v["regions"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| floats(&r["knots"]))
            .collect();
        let values: Vec<_> = v["regions"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| floats(&r["weights"]))
            .collect();
        let regions = core::array::from_fn(|i| Region {
            mode: v["regions"][i]["mode"].as_u64().unwrap() as u32,
            domain: 0,
            coordinates: [0; 4],
            weight: Curve {
                knots: &knots[i],
                weights: &values[i],
            },
        });
        apply_weights(&mut record, &regions, brightness).unwrap();
    }
    record.iter().map(|b| format!("{b:02x}")).collect()
}

use serde_json::{json, Value};
use shieldsigner_rkaiq::awb_fast_configuration::*;
pub fn run(v: &Value) -> String {
    let lights: Vec<[u8; 48]> = v["lights"]
        .as_array()
        .unwrap()
        .iter()
        .map(|row| {
            let mut record = [0; 48];
            for i in 0..12 {
                record[i * 4..i * 4 + 4]
                    .copy_from_slice(&(row[i].as_i64().unwrap() as i32).to_le_bytes());
            }
            record
        })
        .collect();
    let manual: [[i32; 8]; 4] = core::array::from_fn(|i| {
        core::array::from_fn(|j| v["manual"][i][j].as_i64().unwrap_or(0) as i32)
    });
    let mode = if v["manual"].is_null() {
        Mode::Automatic
    } else {
        Mode::Manual(&manual)
    };
    let mut record = [0xa5; 1204];
    let selected = if let Some(iq) = v.get("iq") {
        let regions =
            shieldsigner_rkaiq::awb_calibration::MeasurementRegions::from_value(iq).unwrap();
        shieldsigner_rkaiq::awb_calibration::FastStart::from_value(iq)
            .unwrap()
            .apply(&mut record, &regions, v["valid"].as_u64().unwrap() as usize)
    } else {
        configure(
            &mut record,
            &lights,
            v["valid"].as_u64().unwrap() as usize,
            mode,
        )
    }
    .unwrap();
    json!({"groups":selected.groups,"record":record.iter().map(|b|format!("{b:02x}")).collect::<String>()}).to_string()
}

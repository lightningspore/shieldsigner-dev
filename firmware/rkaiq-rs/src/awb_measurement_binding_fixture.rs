use serde_json::Value;
use shieldsigner_rkaiq::{awb_measurement_binding::*, isp_black_level::Configuration};
pub fn run(v: &Value) -> String {
    let floats = |key: &str| -> Option<[f32; 4]> {
        if v[key].is_null() {
            None
        } else {
            Some(core::array::from_fn(|i| v[key][i].as_f64().unwrap() as f32))
        }
    };
    let black = if v["blc"].is_null() {
        None
    } else {
        let b = &v["blc"];
        Some(Configuration {
            enabled: b["enabled"].as_bool().unwrap(),
            fixed: core::array::from_fn(|i| b["fixed"][i].as_i64().unwrap() as i16),
            stage1_enabled: b["stage1_enabled"].as_bool().unwrap(),
            stage1: core::array::from_fn(|i| b["stage1"][i].as_i64().unwrap() as i16),
            optical_black_enabled: true,
            optical_black_offset: b["offset"].as_i64().unwrap() as i16,
            optical_black_predgain: b["gain"].as_f64().unwrap() as f32,
            optical_black_maximum: 0,
        })
    };
    let mut record = [0xa5; 1204];
    record[0x3e] = 3;
    bind_gain1_linear(
        &mut record,
        &Input {
            black_level: black,
            awb_offsets: floats("offsets").unwrap(),
            digital_gain: v["digital_gain"].as_f64().unwrap() as f32,
            remosaic_inverse: floats("remosaic"),
            software_pre_gain: floats("software"),
        },
    )
    .unwrap();
    record.iter().map(|b| format!("{b:02x}")).collect()
}

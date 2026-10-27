use serde_json::Value;
use shieldsigner_rkaiq::awb_measurement_schedule::*;
fn decode(s: &str) -> Vec<u8> {
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
        .collect()
}
pub fn run(v: &Value) -> String {
    let mut record = decode(v["record"].as_str().unwrap()).try_into().unwrap();
    let groups: Vec<_> = v["groups"]
        .as_array()
        .unwrap()
        .iter()
        .map(|g| Group {
            count: g["count"].as_u64().unwrap() as u8,
            indices: core::array::from_fn(|i| g["indices"][i].as_u64().unwrap() as u32),
            rt_yuv: core::array::from_fn(|i| g["rt_yuv"][i].as_bool().unwrap()),
        })
        .collect();
    let uv: Vec<[u8; 32]> = decode(v["rt_yuv"].as_str().unwrap())
        .chunks_exact(32)
        .map(|x| x.try_into().unwrap())
        .collect();
    let xy: Vec<[u8; 36]> = decode(v["uv"].as_str().unwrap())
        .chunks_exact(36)
        .map(|x| x.try_into().unwrap())
        .collect();
    let yuv: Vec<[u8; 48]> = decode(v["xy"].as_str().unwrap())
        .chunks_exact(48)
        .map(|x| x.try_into().unwrap())
        .collect();
    let signature: [u8; 64] = decode(v["signature"].as_str().unwrap()).try_into().unwrap();
    configure(
        &mut record,
        &Calibration {
            uv_enabled: v["uv_enabled"].as_u64().unwrap() as u16,
            yuv_enabled: v["yuv_enabled"].as_u64().unwrap() as u16,
            capacity: v["capacity"].as_u64().unwrap() as u8,
            rt_yuv: &uv,
            uv: &xy,
            xy: &yuv,
        },
        &Strategy {
            groups: &groups,
            signature: &signature,
            xy_detection: v["xy_detection"].as_bool(),
        },
    )
    .unwrap();
    record.iter().map(|b| format!("{b:02x}")).collect()
}

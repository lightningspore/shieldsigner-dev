use serde_json::Value;
use shieldsigner_rkaiq::awb_measurement_regions::*;
pub fn run(v: &Value) -> String {
    let floats = |key: &str| -> Vec<f32> {
        v[key]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| f32::from_bits(u32::from_str_radix(x.as_str().unwrap(), 16).unwrap()))
            .collect()
    };
    let mut xy_record = [v["fill"].as_u64().unwrap() as u8; 48];
    xy(&floats("xy").try_into().unwrap(), &mut xy_record).unwrap();
    let mut rt_record = [v["fill"].as_u64().unwrap() as u8; 32];
    rotated_yuv(
        &RotatedYuv {
            u: floats("u").try_into().unwrap(),
            threshold: floats("threshold").try_into().unwrap(),
            line: floats("line").try_into().unwrap(),
            distance: v["distance"].as_u64().unwrap() as u8,
        },
        &mut rt_record,
    )
    .unwrap();
    xy_record
        .iter()
        .chain(rt_record.iter())
        .map(|b| format!("{b:02x}"))
        .collect()
}
pub fn iq(v: &Value) -> String {
    let records = shieldsigner_rkaiq::awb_calibration::MeasurementRegions::from_value(v).unwrap();
    records
        .xy
        .iter()
        .zip(records.rotated_yuv.iter())
        .flat_map(|(x, y)| x.iter().chain(y.iter()))
        .map(|b| format!("{b:02x}"))
        .collect()
}

pub fn uv(v: &Value) -> String {
    let array = |key: &str| -> [f32; 4] {
        core::array::from_fn(|i| {
            f32::from_bits(u32::from_str_radix(v[key][i].as_str().unwrap(), 16).unwrap())
        })
    };
    let mut record = [0xa5; 36];
    shieldsigner_rkaiq::awb_measurement_regions::uv(&array("u"), &array("v"), &mut record).unwrap();
    record.iter().map(|b| format!("{b:02x}")).collect()
}
pub fn iq_uv(v: &Value) -> String {
    shieldsigner_rkaiq::awb_calibration::MeasurementRegions::from_value(v)
        .unwrap()
        .uv
        .iter()
        .flatten()
        .map(|b| format!("{b:02x}"))
        .collect()
}

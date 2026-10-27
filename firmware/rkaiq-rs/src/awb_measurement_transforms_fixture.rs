use serde_json::Value;
use shieldsigner_rkaiq::awb_measurement_transforms::*;
pub fn run(v: &Value) -> String {
    let values = |key: &str| -> Vec<f32> {
        v[key]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| f32::from_bits(u32::from_str_radix(x.as_str().unwrap(), 16).unwrap()))
            .collect()
    };
    let mut x = [0xa5; 24];
    let mut y = [0xa5; 24];
    xy(
        &values("weights").try_into().unwrap(),
        &values("rotation").try_into().unwrap(),
        &mut x,
    )
    .unwrap();
    rotated_yuv(&values("matrix").try_into().unwrap(), &mut y).unwrap();
    x.iter()
        .chain(y.iter())
        .map(|b| format!("{b:02x}"))
        .collect()
}
pub fn iq(v: &Value) -> String {
    let t = shieldsigner_rkaiq::awb_calibration::MeasurementTransforms::from_value(v).unwrap();
    t.xy.iter()
        .chain(t.rotated_yuv.iter())
        .map(|b| format!("{b:02x}"))
        .collect()
}

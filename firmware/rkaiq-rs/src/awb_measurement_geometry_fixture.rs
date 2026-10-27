use serde_json::{json, Value};
use shieldsigner_rkaiq::awb_measurement_geometry::*;
pub fn run(v: &Value) -> String {
    let array = |v: &Value| -> [f32; 4] { core::array::from_fn(|i| v[i].as_f64().unwrap() as f32) };
    let input = Input {
        dimensions: [
            v["width"].as_u64().unwrap() as u32,
            v["height"].as_u64().unwrap() as u32,
        ],
        manual_window: if v["manual"].is_null() {
            None
        } else {
            Some(array(&v["manual"]))
        },
        downsample: v["downsample"].as_u64().unwrap() as u32,
        multiwindow: if v["multi"].is_null() {
            None
        } else {
            Some(core::array::from_fn(|i| array(&v["multi"][i])))
        },
        sample_scale: v["scale"].as_u64().unwrap() as u32,
        count_fraction: v["count"].as_f64().unwrap() as f32,
        luma_weight_fraction: v["absolute"].as_f64().unwrap() as f32,
    };
    let result = if let Some(iq) = v.get("iq") {
        shieldsigner_rkaiq::awb_calibration::MeasurementGeometry::from_value(iq)
            .unwrap()
            .derive(input.dimensions, input.sample_scale, input.multiwindow)
    } else {
        derive(&input)
    };
    match result {
        Ok(g)=>json!({"status":0,"window":g.window,"downsample":g.downsample,"block":g.block,"dimensions":g.sampled_dimensions,"multi":g.multiwindow,"count":g.count_threshold.to_bits(),"absolute":g.luma_weight_threshold.to_bits()}).to_string(),
        Err(_)=>json!({"status":-2}).to_string(),
    }
}

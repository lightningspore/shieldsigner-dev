use serde_json::{json, Value};
use shieldsigner_rkaiq::awb_input_selection::*;
pub fn run(v: &Value) -> String {
    let pre = v["gain"]
        .as_str()
        .map(|s| f32::from_bits(u32::from_str_radix(s, 16).unwrap()));
    let mode = v["mode"].as_u64().unwrap() as u32;
    let bits = flags(v["selector"].as_u64().unwrap() as u8, mode, pre);
    let mut record = [0xa5; 1204];
    let result = if let Some(iq) = v.get("iq") {
        shieldsigner_rkaiq::awb_calibration::MeasurementInput::from_value(iq)
            .unwrap()
            .apply(&mut record, mode, pre)
    } else {
        let source = match v["source"].as_u64().unwrap() {
            0 => Source::RawFixed,
            1 => Source::RawAuto,
            3 => Source::BayerNr,
            4 => Source::Drc,
            _ => panic!("source"),
        };
        configure(
            &mut record,
            source,
            v["frame"].as_u64().unwrap() as u8,
            mode,
            pre,
        )
    };
    json!({"flags":[bits.input_12bit,bits.shift_to_12bit],"success":result.is_ok(),"record":record.iter().map(|b|format!("{b:02x}")).collect::<String>()}).to_string()
}

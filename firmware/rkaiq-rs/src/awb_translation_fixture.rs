//! Original-reference line protocol for complete AWB translation.
use serde_json::Value;
use shieldsigner_rkaiq::{
    awb_preparation::FRAME_BYTES, awb_translation::*, statistics::Statistics,
};
fn data(mut seed: u32, n: usize) -> Vec<u8> {
    (0..n)
        .map(|_| {
            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
            (seed >> 24) as u8
        })
        .collect()
}
fn word(b: &[u8], o: usize) -> u32 {
    u32::from_le_bytes(b[o..o + 4].try_into().unwrap())
}
fn put(b: &mut [u8], o: usize, v: u32) {
    b[o..o + 4].copy_from_slice(&v.to_le_bytes());
}
pub fn run(v: &Value) -> String {
    let seed = v["seed"].as_u64().unwrap() as u32;
    let mut raw = data(
        seed ^ 0x31,
        if v["payload"].as_bool().unwrap() {
            13036
        } else {
            13040
        },
    );
    let flags = (word(&raw, 0x32e0) & !0x20)
        | if v["valid"].as_bool().unwrap() {
            0x20
        } else {
            0
        };
    put(&mut raw, 0x32e0, flags);
    put(&mut raw, 0x2af8, v["debug"].as_u64().unwrap() as u32);
    let mut record: [u8; 1204] = data(seed ^ 0x32, 1204).try_into().unwrap();
    record[0x48] = v["lights"].as_u64().unwrap() as u8;
    let initial = data(seed ^ 0x21, 0x2300);
    let mut frame: [u8; FRAME_BYTES] = initial[8..0x1e08].try_into().unwrap();
    let mut destination = Destination {
        frame: &mut frame,
        valid: seed & 1 != 0,
        frame_info_valid: seed & 2 != 0,
        frame_id: word(&initial, 0x22f4),
        proxy_sequence: word(&data(seed ^ 0x22, 0x100), 0x50),
    };
    let statistics = Statistics::parse(&raw).unwrap();
    let configuration = Configuration::from_measurement(&record).unwrap();
    let result = translate(
        if v["missing"].as_bool().unwrap() {
            None
        } else {
            Some(&statistics)
        },
        &configuration,
        &mut destination,
    );
    format!(
        "{}:{}:{}:{:08x}:{:08x}:{}",
        result.native_status(),
        destination.valid as u8,
        destination.frame_info_valid as u8,
        destination.frame_id,
        destination.proxy_sequence,
        destination
            .frame
            .iter()
            .map(|v| format!("{v:02x}"))
            .collect::<String>()
    )
}

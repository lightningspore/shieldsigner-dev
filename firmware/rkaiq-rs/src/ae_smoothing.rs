//! Intermediate queue counts selected by AecUpdateConfig SmoothEn.
#[derive(Clone, Copy, Debug)]
pub struct Counts {
    pub linear: u8,
    pub hdr: u8,
}
pub fn counts(enabled: bool, linear: [u8; 2], hdr: [u8; 2]) -> Counts {
    let count = |v: [u8; 2]| v[0].max(v[1]).wrapping_add(2).min(5);
    if enabled {
        Counts {
            linear: count(linear),
            hdr: count(hdr),
        }
    } else {
        Counts { linear: 0, hdr: 0 }
    }
}
#[cfg(feature = "diagnostics")]
pub fn from_profile(
    scene: &serde_json::Value,
    sensor: &serde_json::Value,
) -> Result<Counts, alloc::string::String> {
    let e = &scene["ae_calib"]["CommCtrl"]["AecSpeed"]["SmoothEn"];
    let enabled = match (e.as_bool(), e.as_u64()) {
        (Some(v), _) => v,
        (_, Some(0)) => false,
        (_, Some(1)) => true,
        _ => return Err(alloc::string::String::from("Invalid SmoothEn")),
    };
    let pair = |key: &str| -> Result<[u8; 2], alloc::string::String> {
        let p = &sensor["CISExpUpdate"][key];
        let n = |field: &str| {
            p[field]
                .as_u64()
                .filter(|v| *v <= 10)
                .map(|v| v as u8)
                .ok_or_else(|| alloc::format!("Invalid sensor update delay {key}/{field}"))
        };
        Ok([n("time_update")?, n("gain_update")?])
    };
    Ok(counts(enabled, pair("Linear")?, pair("Hdr")?))
}
#[cfg(feature = "diagnostics")]
extern crate alloc;

//! AecUpdateConfig transition-delay binding, not sensor application latency.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub enum Mode {
    Frames,
    Time,
}
#[derive(Clone, Copy, Debug)]
pub struct Calibration {
    pub mode: Mode,
    pub black: u8,
    pub white: u8,
}
impl Calibration {
    pub fn counts(self, frame: f32, line: f32, clock_mhz: f32) -> Result<[u8; 2], InvalidInput> {
        if matches!(self.mode, Mode::Frames) {
            return Ok([self.black, self.white]);
        }
        if [frame, line, clock_mhz].iter().any(|x| !x.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        if frame <= 0. || line <= 0. || clock_mhz <= 0. {
            return Err(InvalidInput::Exposure);
        }
        let period = ((frame * line) / clock_mhz) / 1_000_000.;
        if !period.is_finite() || period <= 0. {
            return Err(InvalidInput::Exposure);
        }
        let convert = |value: u8| {
            let n = ((f32::from(value) / 30.) / period) + 0.5;
            if !n.is_finite() || n >= i32::MAX as f32 {
                return Err(InvalidInput::Exposure);
            }
            // Native writes a byte after conversion; values above 255 wrap, not clamp.
            Ok(if n > 0. { (n as i32) as u8 } else { 0 })
        };
        Ok([convert(self.black)?, convert(self.white)?])
    }
    #[cfg(feature = "diagnostics")]
    pub fn from_scene(scene: &serde_json::Value) -> Result<Self, alloc::string::String> {
        let d = &scene["ae_calib"]["CommCtrl"]["AecDelay"];
        let mode = match d["DelayType"].as_str() {
            Some("DELAY_TYPE_FRAME") => Mode::Frames,
            Some("DELAY_TYPE_TIME") => Mode::Time,
            _ => return Err(alloc::string::String::from("Unsupported AE delay type")),
        };
        let number = |key: &str| {
            d[key]
                .as_u64()
                .filter(|n| *n <= 255)
                .map(|n| n as u8)
                .ok_or_else(|| alloc::format!("Invalid AE delay byte {key}"))
        };
        Ok(Self {
            mode,
            black: number("BlackDelay")?,
            white: number("WhiteDelay")?,
        })
    }
}
#[cfg(feature = "diagnostics")]
extern crate alloc;

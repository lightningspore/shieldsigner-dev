//! Standard linear tolerance and damping selection in AecClmExecute.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Calibration {
    pub tolerance_in: f32,
    pub tolerance_out: f32,
    pub damp_over: f32,
    pub damp_under: f32,
    pub damp_dark_to_bright: f32,
    pub damp_bright_to_dark: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Selected {
    pub tolerance_percent: f32,
    pub damping_under: f32,
    pub damping_over: f32,
}
impl Calibration {
    /// `alternate` is native context +0x23ce; its state producer is external.
    pub fn select(self, gating: bool, alternate: bool) -> Result<Selected, InvalidInput> {
        let s = self;
        if [
            s.tolerance_in,
            s.tolerance_out,
            s.damp_over,
            s.damp_under,
            s.damp_dark_to_bright,
            s.damp_bright_to_dark,
        ]
        .iter()
        .any(|x| !x.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if s.tolerance_in < 0.
            || s.tolerance_out < 0.
            || [
                s.damp_over,
                s.damp_under,
                s.damp_dark_to_bright,
                s.damp_bright_to_dark,
            ]
            .iter()
            .any(|x| !(0. ..=1.).contains(x))
        {
            return Err(InvalidInput::Exposure);
        }
        Ok(Selected {
            tolerance_percent: if gating {
                s.tolerance_out
            } else {
                s.tolerance_in
            },
            damping_under: if alternate {
                s.damp_bright_to_dark
            } else {
                s.damp_under
            },
            damping_over: if alternate {
                s.damp_dark_to_bright
            } else {
                s.damp_over
            },
        })
    }
    #[cfg(feature = "diagnostics")]
    pub fn from_scene(scene: &serde_json::Value) -> Result<Self, alloc::string::String> {
        let root = &scene["ae_calib"];
        let linear = &root["LinearAeCtrl"];
        let speed = &root["CommCtrl"]["AecSpeed"];
        let number = |v: &serde_json::Value, key: &str| {
            v[key]
                .as_f64()
                .map(|x| x as f32)
                .ok_or_else(|| alloc::format!("Missing AE policy number {key}"))
        };
        let out = Self {
            tolerance_in: number(linear, "ToleranceIn")?,
            tolerance_out: number(linear, "ToleranceOut")?,
            damp_over: number(speed, "DampOver")?,
            damp_under: number(speed, "DampUnder")?,
            damp_dark_to_bright: number(speed, "DampDark2Bright")?,
            damp_bright_to_dark: number(speed, "DampBright2Dark")?,
        };
        out.select(false, false)
            .map_err(|_| alloc::string::String::from("Invalid AE damping/tolerance calibration"))?;
        Ok(out)
    }
}
#[cfg(feature = "diagnostics")]
extern crate alloc;

//! Profile binding for the recovered native dynamic-damping controller.
use crate::{ae_brightness::Dynamic, ae_damping::Mode};
#[derive(Clone, Copy, Debug)]
pub struct Calibration {
    pub call_enabled: bool,
    pub mode: Mode,
}
impl Calibration {
    pub fn dynamic(self, runtime_enabled: bool, history: [f32; 10]) -> Option<Dynamic> {
        self.call_enabled.then_some(Dynamic {
            enabled: runtime_enabled,
            mode: self.mode,
            history,
        })
    }
    #[cfg(feature = "diagnostics")]
    pub fn from_scene(scene: &serde_json::Value) -> Result<Self, alloc::string::String> {
        let d = &scene["ae_calib"]["CommCtrl"]["AecSpeed"]["DyDamp"];
        let enabled = match (d["DyDampEn"].as_bool(), d["DyDampEn"].as_u64()) {
            (Some(v), _) => v,
            (_, Some(0)) => false,
            (_, Some(1)) => true,
            _ => return Err(alloc::string::String::from("Invalid DyDampEn")),
        };
        let number = |key: &str| {
            d[key]
                .as_f64()
                .map(|x| x as f32)
                .filter(|x| x.is_finite())
                .ok_or_else(|| alloc::format!("Invalid dynamic damping number {key}"))
        };
        let scale = number("SlowRange")?;
        let middle = number("SlowDamp")?;
        if !(0. ..=100.).contains(&scale) || !(0. ..=1.).contains(&middle) {
            return Err(alloc::string::String::from(
                "Dynamic damping value outside profile range",
            ));
        }
        let mode = match d["SlowOPType"].as_str() {
            Some("RK_AIQ_OP_MODE_AUTO") => Mode::Default,
            Some("RK_AIQ_OP_MODE_MANUAL") if scale > 0. => Mode::Custom { scale, middle },
            _ => {
                return Err(alloc::string::String::from(
                    "Unsupported dynamic damping mode/range",
                ))
            }
        };
        Ok(Self {
            call_enabled: enabled,
            mode,
        })
    }
}
#[cfg(feature = "diagnostics")]
extern crate alloc;

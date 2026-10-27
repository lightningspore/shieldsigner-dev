//! FPS selection in AecUpdateConfig with an explicit cached baseline.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub baseline_frame: f32,
    pub baseline_fps: f32,
    pub variable_frame: f32,
    pub fixed_rate: f32,
    pub variable_rate: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Calibration {
    pub fixed: bool,
    pub requested: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Selected {
    pub frame: f32,
    pub fps: f32,
}
impl Calibration {
    pub fn select(
        self,
        state: &mut State,
        current_frame: f32,
        line: f32,
        clock_mhz: f32,
        minimum_fps: f32,
    ) -> Result<Selected, InvalidInput> {
        if [
            self.requested,
            current_frame,
            line,
            clock_mhz,
            minimum_fps,
            state.baseline_frame,
            state.baseline_fps,
            state.variable_frame,
            state.fixed_rate,
            state.variable_rate,
        ]
        .iter()
        .any(|x| !x.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if self.requested < 0.
            || [
                current_frame,
                line,
                clock_mhz,
                minimum_fps,
                state.baseline_frame,
                state.baseline_fps,
            ]
            .iter()
            .any(|x| *x <= 0.)
        {
            return Err(InvalidInput::Exposure);
        }
        let mut frame = current_frame;
        let requested = if self.requested != 0. && self.requested <= state.baseline_fps {
            self.requested.max(minimum_fps)
        } else if self.requested > state.baseline_fps {
            state.baseline_fps
        } else {
            0.
        };
        let selected_frame = if self.requested != 0. && self.requested <= state.baseline_fps {
            libm::roundf(((clock_mhz * 1_000_000.) / line) / requested)
        } else {
            state.baseline_frame
        };
        if !selected_frame.is_finite() || selected_frame <= 0. {
            return Err(InvalidInput::Exposure);
        }
        if self.fixed {
            state.fixed_rate = requested;
            frame = selected_frame;
        } else {
            state.variable_rate = requested;
            state.variable_frame = selected_frame;
        }
        let fps = ((clock_mhz * 1_000_000.) / frame) / line;
        if !fps.is_finite() || fps <= 0. {
            return Err(InvalidInput::Exposure);
        }
        Ok(Selected { frame, fps })
    }
    #[cfg(feature = "diagnostics")]
    pub fn from_scene(scene: &serde_json::Value) -> Result<Self, alloc::string::String> {
        let d = &scene["ae_calib"]["CommCtrl"]["AecFrameRateMode"];
        let fixed = match (d["isFpsFix"].as_bool(), d["isFpsFix"].as_u64()) {
            (Some(v), _) => v,
            (_, Some(0)) => false,
            (_, Some(1)) => true,
            _ => return Err(alloc::string::String::from("Invalid isFpsFix")),
        };
        let requested = d["FpsValue"]
            .as_f64()
            .map(|n| n as f32)
            .filter(|n| n.is_finite() && (0. ..=1024.).contains(n))
            .ok_or_else(|| alloc::string::String::from("Invalid FpsValue"))?;
        Ok(Self { fixed, requested })
    }
}
#[cfg(feature = "diagnostics")]
extern crate alloc;

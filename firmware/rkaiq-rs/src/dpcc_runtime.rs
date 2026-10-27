//! Automatic linear color DPCC frame gate (ELF 0x11a67c).
use crate::{dpcc_calibration::Automatic, isp_dpcc::RESULT_BYTES, InvalidInput};
#[derive(Clone, Copy, Debug, Default)]
pub struct State {
    pub iso: i32,
    pub reconfigure: bool,
}
impl State {
    /// Native combines sensor-digital/ISP gains first, then analogue and 50.
    /// Fresh context ISO is zero; missing exposure falls back to ISO 50.
    pub fn process(
        &mut self,
        calibration: &Automatic,
        gains: Option<[f32; 3]>,
        result: &mut [u8; RESULT_BYTES],
    ) -> Result<bool, InvalidInput> {
        let iso = if let Some(g) = gains {
            if g.iter().any(|v| !v.is_finite() || *v < 0.) {
                return Err(InvalidInput::GainRange);
            }
            let value = (g[0] * (g[1] * g[2])) * 50.;
            if !value.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            value as i32
        } else {
            50
        };
        if self.iso == iso && !self.reconfigure {
            return Ok(false);
        }
        let mut next = *result;
        calibration.process(iso, &mut next)?;
        *result = next;
        self.iso = iso;
        self.reconfigure = false;
        Ok(true)
    }
}

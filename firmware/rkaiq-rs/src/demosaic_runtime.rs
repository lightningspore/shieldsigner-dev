//! Linear color-frame branch of the demosaic processing callback (ELF 0x114a2c).
//! Own the ISO/reconfiguration gate and cached converter state. HDR, monochrome
//! and manual processing remain outside this explicit automatic-color API.
use crate::{
    demosaic_selection::Calibration,
    isp_demosaic::{self, HardwareRecord},
    InvalidInput,
};

#[derive(Clone, Copy, Debug)]
pub struct State {
    pub iso: i32,
    pub reconfigure: bool,
    pub hardware: HardwareRecord,
}
impl State {
    /// Missing exposure uses native ISO 50. Unlike AWB, this callback does not
    /// clamp individual gains to unity. Intermediate products are f32 in order.
    /// State commits only after successful selection and quantization.
    pub fn process(
        &mut self,
        calibration: &Calibration,
        gains: Option<[f32; 3]>,
    ) -> Result<Option<HardwareRecord>, InvalidInput> {
        let iso = if let Some(g) = gains {
            if g.iter().any(|x| !x.is_finite() || *x < 0.) {
                return Err(InvalidInput::GainRange);
            }
            let value = ((g[0] * g[1]) * g[2]) * 50.;
            if !value.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            value as i32
        } else {
            50
        };
        let mut next = *self;
        if next.iso != iso {
            next.iso = iso;
            next.hardware[0] = 1;
        }
        if next.reconfigure {
            next.reconfigure = false;
            next.hardware[0] = 1;
        }
        let result = if next.hardware[0] != 0 {
            let selected = calibration.select(iso)?;
            Some(isp_demosaic::quantize(&mut next.hardware, selected)?)
        } else {
            None
        };
        *self = next;
        Ok(result)
    }
}

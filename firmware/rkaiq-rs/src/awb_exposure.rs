//! Linear exposure-to-ISO binding in awbProcessing (ELF 0x10f848).
use crate::InvalidInput;
/// Native accepts each real gain only when >= 1, multiplies in analogue,
/// sensor-digital, ISP order, then scales by 50. Reject nonfinite input/output
/// rather than carrying unchecked NaN/Inf into calibrated interpolation.
pub fn linear_iso(gains: [f32; 3]) -> Result<f32, InvalidInput> {
    if gains.iter().any(|g| !g.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    let accepted = gains.map(|g| if g >= 1. { g } else { 1. });
    let iso = ((accepted[0] * accepted[1]) * accepted[2]) * 50.;
    if !iso.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    Ok(iso)
}

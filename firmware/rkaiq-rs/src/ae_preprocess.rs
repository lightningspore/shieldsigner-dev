//! Standard linear error-history writes in AecPreProcess (ELF 0xb33d0).
use crate::InvalidInput;
pub fn record_error(
    history: &mut [f32; 10],
    frame: u32,
    run: bool,
    measured: f32,
    target: f32,
) -> Result<f32, InvalidInput> {
    if frame > i32::MAX as u32 - 9 {
        return Err(InvalidInput::Length);
    }
    if history.iter().any(|v| !v.is_finite())
        || (run && (!measured.is_finite() || !target.is_finite()))
    {
        return Err(InvalidInput::NonFinite);
    }
    if run && (measured < 0. || target <= 0.) {
        return Err(InvalidInput::Exposure);
    }
    let error = if run {
        (measured - target) / target
    } else {
        history[((frame + 9) % 10) as usize]
    };
    if !error.is_finite() {
        return Err(InvalidInput::Exposure);
    }
    history[(frame % 10) as usize] = error;
    Ok(error)
}

//! No-OTP temporal grid damping inside native AlscAutoConfig.
use crate::{lsc_tables::SAMPLES, InvalidInput};
/// Updates all planes. Native convergence deliberately observes only the first
/// and last samples; once both relative errors are below 0.015 it snaps all
/// samples to the target. `previous` must represent accepted prior state.
pub fn process(
    previous: &mut [u16; SAMPLES],
    target: &[u16; SAMPLES],
    damping: f32,
    enabled: bool,
    frame_count: u32,
) -> Result<bool, InvalidInput> {
    if !damping.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if !(0. ..=1.).contains(&damping) {
        return Err(InvalidInput::Length);
    }
    let close = |index: usize| {
        let before = i32::from(previous[index]);
        let after = i32::from(target[index]);
        ((before - after) as f32 / (before + after) as f32).abs() < 0.015
    };
    let converged = close(0) && close(SAMPLES - 1);
    let factor = if enabled && frame_count >= 2 {
        damping
    } else {
        0.
    };
    let old_weight = if converged {
        0
    } else {
        (factor * 65536.) as u32
    };
    let new_weight = 65536 - old_weight;
    for (old, new) in previous.iter_mut().zip(target) {
        *old = old_weight
            .wrapping_mul(u32::from(*old))
            .wrapping_add(new_weight.wrapping_mul(u32::from(*new)))
            .wrapping_add(32768)
            .wrapping_shr(16) as u16;
    }
    Ok(converged)
}

//! Linear AecClmExpChkForEnv (ELF 0xa379c), with explicit history inputs.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug, Default)]
pub struct Record {
    pub frame: i32,
    pub current_exposure: f32,
    pub queued_count: u32,
    pub error: f32,
    pub published_exposure: f32,
    pub queued: [f32; 6],
}
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub priming: bool,
    pub queued_count: u32,
    pub held_exposure: f32,
}
pub fn adjust(
    state: &mut State,
    history: &[Record; 5],
    index: u32,
    frame: i32,
    synchronized_frame: i32,
    current_exposure: f32,
    candidate: f32,
) -> Result<f32, InvalidInput> {
    if index > i32::MAX as u32 - 4 || state.queued_count > 6 {
        return Err(InvalidInput::Length);
    }
    if !candidate.is_finite()
        || !current_exposure.is_finite()
        || !state.held_exposure.is_finite()
        || history.iter().any(|r| {
            !r.error.is_finite()
                || !r.published_exposure.is_finite()
                || r.queued.iter().any(|v| !v.is_finite())
        })
    {
        return Err(InvalidInput::NonFinite);
    }
    if state.priming {
        state.priming = false;
        state.queued_count = 0;
        state.held_exposure = current_exposure;
        return Ok(candidate);
    }
    let previous = history[((index + 4) % 5) as usize];
    let current = history[(index % 5) as usize];
    let delta = frame.wrapping_sub(synchronized_frame).max(1) as u32;
    let reference = if delta < state.queued_count {
        previous.queued[delta as usize]
    } else {
        previous.published_exposure
    };
    if current.error * previous.error > 0. || previous.error == 0. {
        if current.error < 0. {
            Ok(candidate.max(reference))
        } else if current.error > 0. {
            Ok(candidate.min(reference))
        } else {
            Ok(reference)
        }
    } else {
        Ok(candidate)
    }
}

/// Native AecCurInfoSetForEnv, linear branch (ELF 0xa0f2c).
/// The caller owns ring advancement; this function only writes the chosen slot.
pub fn record_current(
    history: &mut [Record; 5],
    index: u32,
    frame: i32,
    exposure: f32,
    error: f32,
) -> Result<(), InvalidInput> {
    if index > i32::MAX as u32 {
        return Err(InvalidInput::Length);
    }
    if !exposure.is_finite() || !error.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let record = &mut history[(index % 5) as usize];
    record.frame = frame;
    record.current_exposure = exposure;
    record.error = error;
    Ok(())
}
/// Native AecClmExpSetForEnv, non-iris linear branch (ELF 0xae428).
/// Queue points are real exposure values, not register codes; unused tail slots
/// retain their previous values, as in the native record.
pub fn publish(
    history: &mut [Record; 5],
    index: u32,
    exposure: f32,
    queued: &[crate::ae_route::Point],
) -> Result<(), InvalidInput> {
    if index > i32::MAX as u32 || queued.len() > 6 {
        return Err(InvalidInput::Length);
    }
    if !exposure.is_finite()
        || queued
            .iter()
            .any(|p| ![p.time, p.gain, p.isp_gain].iter().all(|v| v.is_finite()))
    {
        return Err(InvalidInput::NonFinite);
    }
    let mut totals = [0.; 6];
    for (i, p) in queued.iter().enumerate() {
        totals[i] = (p.gain * p.time) * p.isp_gain;
        if !totals[i].is_finite() {
            return Err(InvalidInput::Exposure);
        }
    }
    let record = &mut history[(index % 5) as usize];
    record.published_exposure = exposure;
    record.queued_count = queued.len() as u32;
    record.queued[..queued.len()].copy_from_slice(&totals[..queued.len()]);
    Ok(())
}

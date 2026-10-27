//! Linear AecClmExpChkForEnv (ELF 0xa379c), with explicit history inputs.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Record {
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

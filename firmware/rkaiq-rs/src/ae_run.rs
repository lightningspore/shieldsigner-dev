//! Ordinary linear AecRun bookkeeping around AecClmExecute (ELF 0xb0d1c).
//! Register/DCG conversion and missing-statistics/manual modes are external.
use crate::{ae_controller, ae_decision, ae_route, InvalidInput};

#[derive(Clone, Copy, Debug)]
pub struct State {
    pub previous_q8: [u16; 3],
    pub previous_mean: f32,
    pub previous_hdr_means: [f32; 3],
}

/// Statistics and exposure have already passed preprocessing. Skipped runs
/// preserve the control index and previous samples, but still copy the last
/// aggregate output into the environment's held-exposure field.
/// Callers must not publish partially updated state if any stage fails.
pub fn linear(
    runtime: &mut State,
    controller: &mut ae_controller::State,
    route: &mut [ae_route::Point],
    histogram: &[u32],
    input: ae_decision::Input,
    policy: ae_controller::Policy,
    limits: ae_route::Limits,
    frame: i32,
    synchronized_frame: i32,
    run: bool,
    last_aggregate_output: f32,
    q8: [u16; 3],
    hdr_means: [f32; 3],
) -> Result<Option<ae_controller::Output>, InvalidInput> {
    if !last_aggregate_output.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    controller.environment.held_exposure = last_aggregate_output;
    if !run {
        return Ok(None);
    }
    // Restrict the successful numerical domain to that accepted by the
    // subordinate ring helpers rather than emulate signed index overflow.
    if controller.index >= i32::MAX as u32 - 4 {
        return Err(InvalidInput::Length);
    }
    controller.index += 1;
    let output = ae_controller::step(
        controller,
        route,
        histogram,
        input,
        policy,
        limits,
        frame,
        synchronized_frame,
    )?;
    runtime.previous_mean = input.measured;
    runtime.previous_hdr_means = hdr_means;
    runtime.previous_q8 = q8;
    Ok(Some(output))
}

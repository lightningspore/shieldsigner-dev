//! Connected standard linear AecClmExecute (ELF 0xa40c8) success path.
//! Runtime policy/limits and applied exposure history remain explicit inputs.
use crate::{ae_brightness, ae_decision, ae_delay, ae_environment, ae_route, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub history: [ae_environment::Record; 5],
    pub index: u32,
    pub environment: ae_environment::State,
    pub delay: ae_delay::State,
    pub cache: ae_route::Cache,
    pub previous_error: f32,
    pub reference_error: f32,
    pub saturated: bool,
}
#[derive(Clone, Copy, Debug)]
pub struct Policy {
    pub dynamic: Option<ae_brightness::Dynamic>,
    pub damping_under: f32,
    pub damping_over: f32,
    pub fps: f32,
    pub delay_enabled: bool,
    pub same_mode: bool,
    pub negative_delay: u8,
    pub positive_delay: u8,
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub point: ae_route::Point,
    pub aggregate_exposure: f32,
    pub relative_error: f32,
    pub held: bool,
    pub damping_diagnostics: Option<crate::ae_damping::Diagnostics>,
}
pub fn step(
    state: &mut State,
    route: &mut [ae_route::Point],
    histogram: &[u32],
    mut input: ae_decision::Input,
    policy: Policy,
    limits: ae_route::Limits,
    frame: i32,
    synchronized_frame: i32,
) -> Result<Output, InvalidInput> {
    input.saturated = state.saturated;
    let brightness = ae_brightness::controlled(
        histogram,
        input,
        policy.damping_under,
        policy.damping_over,
        policy.fps,
        policy.dynamic.as_ref(),
        frame as u32,
    )?;
    ae_environment::record_current(
        &mut state.history,
        state.index,
        frame,
        input.current_exposure,
        brightness.relative_error,
    )?;
    let mut candidate = ae_environment::adjust(
        &mut state.environment,
        &state.history,
        state.index,
        frame,
        synchronized_frame,
        input.current_exposure,
        brightness.exposure,
    )?;
    let held = ae_delay::linear(
        &mut state.delay,
        ae_delay::Input {
            enabled: policy.delay_enabled,
            same_mode: policy.same_mode,
            frame,
            previous_error: state.previous_error,
            current_error: brightness.relative_error,
            reference_error: state.reference_error,
            negative_delay: policy.negative_delay,
            positive_delay: policy.positive_delay,
        },
    )?;
    if held {
        candidate = state.environment.held_exposure;
    } else {
        if (brightness.relative_error * state.previous_error < 0.
            || (state.previous_error != 0. && brightness.relative_error == 0.))
            && input.current_exposure != state.environment.held_exposure
        {
            candidate = state.environment.held_exposure;
        }
        state.previous_error = brightness.relative_error;
    }
    state.reference_error = brightness.relative_error;
    let point = ae_route::split_cached(route, candidate, limits, &mut state.cache)?;
    state.saturated = brightness.saturated;
    Ok(Output {
        point,
        aggregate_exposure: (point.gain * point.time) * point.isp_gain,
        relative_error: brightness.relative_error,
        held,
        damping_diagnostics: brightness.damping_diagnostics,
    })
}

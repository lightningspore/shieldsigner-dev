//! Connected ordinary linear preprocessing checkpoint and automatic caller.
//! Exposure association, conversion, and result publication remain external.
use crate::{
    ae_controller, ae_convergence, ae_decision, ae_preprocess, ae_route, ae_run, ae_run_flag,
    ae_target, InvalidInput,
};

#[derive(Clone, Copy, Debug)]
pub struct State {
    pub error_history: [f32; 10],
    pub target: f32,
    pub current_error: f32,
    pub convergence: ae_convergence::State,
}
#[derive(Clone, Copy, Debug)]
pub struct Target<'a> {
    pub levels: &'a [f32],
    pub points: &'a [f32],
    pub bias_percent: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub run: bool,
    pub preprocessing_error: f32,
    pub control: Option<ae_controller::Output>,
}
/// Applies the standard mean/target/history branch followed by the recovered
/// automatic caller. Current exposure must already be associated with stats.
/// Caller retains the last output when control is None. Failed partial state
/// must not be published, just as for the subordinate controller API.
pub fn linear(
    state: &mut State,
    runtime: &mut ae_run::State,
    controller: &mut ae_controller::State,
    route: &mut [ae_route::Point],
    histogram: &[u32],
    mut input: ae_decision::Input,
    mut policy: ae_controller::Policy,
    limits: ae_route::Limits,
    target: Target<'_>,
    frame: i32,
    synchronized_frame: i32,
    last_aggregate_output: f32,
    q8: [u16; 3],
    hdr_means: [f32; 3],
) -> Result<Output, InvalidInput> {
    let run = should_run(state, runtime, controller, q8)?;
    if run {
        input.measured = f32::from(q8[0]) / 256.;
        state.target = ae_target::select(
            target.levels,
            target.points,
            input.current_exposure,
            target.bias_percent,
        )?;
    }
    input.target = state.target;
    state.current_error = ae_preprocess::record_error(
        &mut state.error_history,
        frame as u32,
        run,
        input.measured,
        state.target,
    )?;
    policy.delay_enabled = state.convergence.gating_enabled != 0;
    if let Some(dynamic) = policy.dynamic.as_mut() {
        dynamic.enabled = state.convergence.dynamic_enabled != 0;
        dynamic.history = state.error_history;
    }
    let control = ae_run::linear(
        runtime,
        controller,
        route,
        histogram,
        input,
        policy,
        limits,
        frame,
        synchronized_frame,
        run,
        last_aggregate_output,
        q8,
        hdr_means,
    )?;
    Ok(Output {
        run,
        preprocessing_error: state.current_error,
        control,
    })
}
/// Native run/skip predicate shared with the full standard preprocessing path.
pub fn should_run(
    state: &State,
    runtime: &ae_run::State,
    controller: &ae_controller::State,
    q8: [u16; 3],
) -> Result<bool, InvalidInput> {
    Ok(ae_run_flag::select(
        ae_run_flag::Policy {
            enabled_4fb9: state.convergence.gating_enabled,
            channel_mode_23cd: 0,
            unchanged_23cf: [controller.delay.changed as u8, 0, 0],
            overrides_3d3c: [controller.cache.force as u8, 0, 0],
        },
        &runtime.previous_q8[..1],
        &q8[..1],
    )? != 0)
}

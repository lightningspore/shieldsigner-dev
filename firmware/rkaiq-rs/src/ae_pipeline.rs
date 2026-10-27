//! Joined standard linear frame policy, conversion and exposure publication.
//! Runtime/profile binding and real statistics/exposure association are external.
use crate::{
    ae_controller, ae_convergence, ae_conversion_queue, ae_decision, ae_frame, ae_publication,
    ae_register, ae_result, ae_route, ae_run, exposure::Calibration, InvalidInput,
};
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub frame: ae_frame::State,
    pub runtime: ae_run::State,
    pub controller: ae_controller::State,
    pub publication: ae_publication::State,
    /// Last proposed converted records, including timing metadata before selection.
    pub retained_records: [ae_publication::Record; 6],
    pub retained_count: usize,
    /// Native requested aggregate remains separate from its converted real point.
    pub last_aggregate: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub frame: ae_frame::Output,
    pub conversion: Option<ae_conversion_queue::Output>,
    pub publication: ae_publication::Output,
}
/// No hardware writes. A caller must discard partially updated state on errors.
pub fn linear(
    state: &mut State,
    route: &mut [ae_route::Point],
    histogram: &[u32],
    input: ae_decision::Input,
    policy: ae_controller::Policy,
    limits: ae_route::Limits,
    target: ae_frame::Target<'_>,
    calibration: Calibration<'_>,
    register_policy: ae_register::Policy,
    frame: i32,
    q8: [u16; 3],
    hdr_means: [f32; 3],
    effective: ae_convergence::Exposure,
    intermediate_count: usize,
) -> Result<Output, InvalidInput> {
    if intermediate_count > 5 || state.retained_count > 6 {
        return Err(InvalidInput::Length);
    }
    state.controller.environment.queued_count = state.publication.published_count as u32;
    let frame_output = ae_frame::linear(
        &mut state.frame,
        &mut state.runtime,
        &mut state.controller,
        route,
        histogram,
        input,
        policy,
        limits,
        target,
        frame,
        state.publication.synchronized_frame,
        state.last_aggregate,
        q8,
        hdr_means,
    )?;
    state.publication.published_count = state.controller.environment.queued_count as usize;
    if let Some(control) = frame_output.control {
        state.last_aggregate = control.aggregate_exposure;
        let result = ae_result::linear(
            &mut state.publication,
            &mut state.frame.convergence,
            &mut state.controller.history,
            state.controller.index,
            control.point,
            control.aggregate_exposure,
            state.controller.environment.held_exposure,
            effective,
            frame,
            intermediate_count,
            route,
            limits,
            calibration,
            register_policy,
        )?;
        state.retained_records = result.proposed_records;
        state.retained_count = result.proposed_count;
        state.controller.environment.queued_count = state.publication.published_count as u32;
        Ok(Output {
            frame: frame_output,
            conversion: Some(result.conversion),
            publication: result.publication,
        })
    } else {
        if state.retained_count != intermediate_count + 1 {
            return Err(InvalidInput::Length);
        }
        let publication = ae_publication::finish(
            &mut state.publication,
            &mut state.frame.convergence,
            &mut state.controller.history,
            state.controller.index,
            state.last_aggregate,
            effective,
            &state.retained_records[..state.retained_count],
            frame,
        )?;
        state.controller.environment.queued_count = state.publication.published_count as u32;
        Ok(Output {
            frame: frame_output,
            conversion: None,
            publication,
        })
    }
}

//! Standard linear histogram/damping prefix of AecClmExecute (ELF 0xa40c8).
//! Stops before environment-history adjustment, delay gate and route dispatch.
use crate::{ae_decision, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub exposure: f32,
    pub relative_error: f32,
    pub saturated: bool,
}
pub fn standard(
    histogram: &[u32],
    input: ae_decision::Input,
    damping_under: f32,
    damping_over: f32,
    fps: f32,
) -> Result<Output, InvalidInput> {
    if [damping_under, damping_over, fps]
        .iter()
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if !(0. ..=1.).contains(&damping_under) || !(0. ..=1.).contains(&damping_over) || fps <= 0. {
        return Err(InvalidInput::Exposure);
    }
    let decision = ae_decision::solve(histogram, input)?;
    let mut relative_error = (input.measured - input.target) / input.target;
    if (input.measured - input.target).abs() / input.target <= input.tolerance_percent / 100. {
        relative_error = 0.;
    }
    let mut damping = if input.measured <= input.target {
        damping_under
    } else {
        damping_over
    };
    if input.measured > input.target && decision.saturated {
        damping = damping.min((fps / 30.).min(1.) * 0.05_f32);
    }
    let exposure = libm::fmaf(
        1. - damping,
        decision.exposure,
        damping * input.current_exposure,
    )
    .clamp(input.minimum_exposure, input.maximum_exposure);
    Ok(Output {
        exposure,
        relative_error,
        saturated: decision.saturated,
    })
}

//! Ordinary linear AecRegValueConvertion (ELF 0xaf0b0), non-iris/DCG disabled.
use crate::{ae_register, ae_route, exposure::Calibration, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub struct Entry {
    pub converted: ae_register::Output,
    pub aggregate: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub current: ae_register::Output,
    pub intermediate: [Option<Entry>; 5],
}
pub fn linear(
    proposed: ae_route::Point,
    target_aggregate: f32,
    held_aggregate: f32,
    published: &[ae_route::Point],
    frame: i32,
    synchronized_frame: i32,
    count: usize,
    route: &mut [ae_route::Point],
    limits: ae_route::Limits,
    calibration: Calibration<'_>,
    policy: ae_register::Policy,
) -> Result<Output, InvalidInput> {
    if count > 5 || published.len() > 6 || !policy.automatic {
        return Err(InvalidInput::Length);
    }
    let current = ae_register::linear(
        proposed.time,
        proposed.gain,
        proposed.isp_gain,
        -1,
        calibration,
        policy,
    )?;
    let delta = frame.wrapping_sub(synchronized_frame).max(1) as usize;
    let base = if delta < published.len() {
        let p = published[delta];
        (p.gain * p.isp_gain) * p.time
    } else {
        held_aggregate
    };
    let mut intermediate = [None; 5];
    if count != 0
        && (!base.is_finite()
            || base <= 0.
            || !target_aggregate.is_finite()
            || target_aggregate <= 0.)
    {
        return Err(InvalidInput::Exposure);
    }
    for (i, slot) in intermediate.iter_mut().enumerate().take(count) {
        // Preserve native float evaluation before promotion into double pow.
        let exponent = ((libm::log10f(target_aggregate) - libm::log10f(base)) * ((i + 1) as f32))
            / ((count + 1) as f32)
            + libm::log10f(base);
        let aggregate = libm::pow(10., f64::from(exponent)) as f32;
        let p = ae_route::split(route, aggregate, limits)?;
        let converted = ae_register::linear(p.time, p.gain, p.isp_gain, -1, calibration, policy)?;
        let aggregate = (converted.gain * converted.seconds) * converted.isp_gain;
        *slot = Some(Entry {
            converted,
            aggregate,
        });
    }
    Ok(Output {
        current,
        intermediate,
    })
}

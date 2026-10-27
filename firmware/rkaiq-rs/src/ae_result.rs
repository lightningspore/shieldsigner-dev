//! Joined ordinary linear conversion, record assembly and exposure publication.
use crate::{
    ae_convergence, ae_conversion_queue, ae_environment, ae_publication, ae_register, ae_route,
    exposure::Calibration, InvalidInput,
};
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub conversion: ae_conversion_queue::Output,
    pub publication: ae_publication::Output,
    pub proposed_records: [ae_publication::Record; 6],
    pub proposed_count: usize,
}
pub fn linear(
    state: &mut ae_publication::State,
    convergence: &mut ae_convergence::State,
    history: &mut [ae_environment::Record; 5],
    index: u32,
    proposed: ae_route::Point,
    target_aggregate: f32,
    held_aggregate: f32,
    effective: ae_convergence::Exposure,
    frame: i32,
    count: usize,
    route: &mut [ae_route::Point],
    limits: ae_route::Limits,
    calibration: Calibration<'_>,
    policy: ae_register::Policy,
) -> Result<Output, InvalidInput> {
    if state.published_count > 6 {
        return Err(InvalidInput::Length);
    }
    let points = state.published.map(|r| {
        let f = |o| f32::from_le_bytes(r[o..o + 4].try_into().unwrap());
        ae_route::Point {
            time: f(0),
            gain: f(4),
            isp_gain: f(12),
        }
    });
    let conversion = ae_conversion_queue::linear(
        proposed,
        target_aggregate,
        held_aggregate,
        &points[..state.published_count],
        frame,
        state.synchronized_frame,
        count,
        route,
        limits,
        calibration,
        policy,
    )?;
    if !calibration.frame_length.is_finite()
        || calibration.frame_length <= 0.
        || calibration.frame_length >= i32::MAX as f32
        || !calibration.line_length_pixels.is_finite()
        || calibration.line_length_pixels <= 0.
        || calibration.line_length_pixels > u16::MAX as f32
    {
        return Err(InvalidInput::Exposure);
    }
    let timing = ae_publication::Timing {
        frame_length: calibration.frame_length as u32,
        line_length: calibration.line_length_pixels as u16,
        pixel_clock_mhz: calibration.pixel_clock_mhz,
    };
    let pack = |c: ae_register::Output| {
        ae_publication::pack(
            ae_route::Point {
                time: c.seconds,
                gain: c.gain,
                isp_gain: c.isp_gain,
            },
            c.codes,
            -1,
            timing,
        )
    };
    let mut records = [[0; 244]; 6];
    for (i, entry) in conversion.intermediate.iter().enumerate().take(count) {
        records[i] = pack(entry.ok_or(InvalidInput::Length)?.converted);
    }
    records[count] = pack(conversion.current);
    let publication = ae_publication::finish(
        state,
        convergence,
        history,
        index,
        target_aggregate,
        effective,
        &records[..count + 1],
        frame,
    )?;
    Ok(Output {
        conversion,
        publication,
        proposed_records: records,
        proposed_count: count + 1,
    })
}

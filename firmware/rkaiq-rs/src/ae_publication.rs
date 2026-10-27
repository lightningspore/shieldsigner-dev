//! Linear AecGetProcResults queue selection; result metadata/history elsewhere.
use crate::{ae_route::Point, exposure::Codes, InvalidInput};
pub type Record = [u8; 244];
#[derive(Clone, Copy, Debug)]
pub struct Timing {
    pub frame_length: u32,
    pub line_length: u16,
    pub pixel_clock_mhz: f32,
}
pub fn pack(point: Point, codes: Codes, dcg: i32, timing: Timing) -> Record {
    let mut r = [0; 244];
    for (o, x) in [
        (0, point.time.to_bits()),
        (4, point.gain.to_bits()),
        (8, 1f32.to_bits()),
        (12, point.isp_gain.to_bits()),
        (20, dcg as u32),
        (32, codes.integration_time),
        (36, codes.gain),
        (232, timing.frame_length),
        (236, timing.pixel_clock_mhz.to_bits()),
    ] {
        r[o..o + 4].copy_from_slice(&x.to_le_bytes());
    }
    r[228..230].copy_from_slice(&timing.line_length.to_le_bytes());
    r
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    pub count: usize,
    pub records: [Record; 6],
    pub synchronized_frame: i32,
    pub final_record: Record,
}
fn selected(r: &Record) -> Record {
    // Native copies these ranges into its zeroed result scratch records.
    // In particular line length and pixel clock are not retained here.
    let mut out = [0; 244];
    out[..48].copy_from_slice(&r[..48]);
    out[192..228].copy_from_slice(&r[192..228]);
    out[232..236].copy_from_slice(&r[232..236]);
    out
}
pub fn select(
    proposed: &[Record],
    previous_final: &Record,
    published: &[Record],
    frame: i32,
    synchronized_frame: i32,
) -> Result<Output, InvalidInput> {
    select_with_reference(
        proposed,
        previous_final,
        published,
        frame,
        synchronized_frame,
        None,
    )
}
fn select_with_reference(
    proposed: &[Record],
    previous_final: &Record,
    published: &[Record],
    frame: i32,
    mut synchronized_frame: i32,
    empty_reference: Option<&Record>,
) -> Result<Output, InvalidInput> {
    if proposed.is_empty() || proposed.len() > 6 || published.len() > 6 {
        return Err(InvalidInput::Length);
    }
    let final_record = &proposed[proposed.len() - 1];
    let mut records = [[0; 244]; 6];
    let mut count;
    let mut use_previous_fallback = false;
    if final_record[..48] == previous_final[..48] {
        count = usize::from(final_record[232..236] != previous_final[232..236]);
        if count != 0 {
            records[0] = selected(final_record);
        }
        if final_record[196..200] != previous_final[196..200] {
            count = 1;
            records[0] = selected(final_record);
            records[0][192] = 1;
            synchronized_frame = frame;
        } else {
            records[0][192] = 0;
        }
        use_previous_fallback = count == 0;
    } else {
        let delta = frame.wrapping_sub(synchronized_frame).max(1) as usize;
        let reference = if published.is_empty() {
            empty_reference.ok_or(InvalidInput::Length)?
        } else {
            &published[delta.min(published.len()) - 1]
        };
        let first = proposed.iter().position(|r| r[..48] != reference[..48]);
        if let Some(first) = first {
            count = 1;
            records[0] = selected(&proposed[first]);
            for r in &proposed[first + 1..] {
                if records[count - 1][..48] != r[..48] {
                    records[count] = selected(r);
                    count += 1;
                }
            }
            synchronized_frame = frame;
            records[count - 1][192] = u8::from(final_record[196..200] != previous_final[196..200]);
        } else {
            // No remaining transition: the native result has count zero
            // and zeroed scratch records in this branch.
            count = 0;
        }
    }
    if use_previous_fallback {
        records[0] = *previous_final;
    }
    let final_record = records[count.saturating_sub(1)];
    Ok(Output {
        count,
        records,
        synchronized_frame,
        final_record,
    })
}

#[derive(Clone, Copy, Debug)]
pub struct State {
    pub previous_final: Record,
    /// Native empty-queue selection reads the 244-byte region immediately
    /// preceding the queue (context +0x4ec8); caller supplies its defined bytes.
    pub empty_reference: Record,
    pub published: [Record; 6],
    pub published_count: usize,
    pub synchronized_frame: i32,
    pub last_result_frame: i32,
}
fn word(r: &Record, offset: usize) -> u32 {
    u32::from_le_bytes(r[offset..offset + 4].try_into().unwrap())
}
fn point(r: &Record) -> Point {
    Point {
        time: f32::from_bits(word(r, 0)),
        gain: f32::from_bits(word(r, 4)),
        isp_gain: f32::from_bits(word(r, 12)),
    }
}
fn convergence_exposure(r: &Record) -> crate::ae_convergence::Exposure {
    crate::ae_convergence::Exposure {
        time_code: word(r, 32),
        gain_code: word(r, 36),
        isp_gain: f32::from_bits(word(r, 12)),
    }
}
/// Publish ordinary linear exposure state. Other result fields/CIS flags remain
/// external. Do not publish partially updated state after an error.
pub fn finish(
    state: &mut State,
    convergence: &mut crate::ae_convergence::State,
    history: &mut [crate::ae_environment::Record; 5],
    index: u32,
    aggregate: f32,
    effective: crate::ae_convergence::Exposure,
    proposed: &[Record],
    frame: i32,
) -> Result<Output, InvalidInput> {
    if proposed.is_empty() || state.published_count > 6 {
        return Err(InvalidInput::Length);
    }
    crate::ae_convergence::linear(
        convergence,
        effective,
        convergence_exposure(&proposed[proposed.len() - 1]),
        convergence_exposure(&state.previous_final),
    )?;
    let output = select_with_reference(
        proposed,
        &state.previous_final,
        &state.published[..state.published_count],
        frame,
        state.synchronized_frame,
        Some(&state.empty_reference),
    )?;
    state.synchronized_frame = output.synchronized_frame;
    if state.synchronized_frame == frame {
        state.published_count = output.count;
        state.published = output.records;
    }
    let points = state.published.map(|r| point(&r));
    crate::ae_environment::publish(history, index, aggregate, &points[..state.published_count])?;
    state.previous_final = output.final_record;
    state.last_result_frame = frame;
    Ok(output)
}

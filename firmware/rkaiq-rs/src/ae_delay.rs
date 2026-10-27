//! Linear AecCheckDelay (ELF 0xa13b8), not sensor application latency.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug, Default)]
pub struct State {
    pub negative_start: i32,
    pub positive_start: i32,
    pub negative_count: u8,
    pub positive_count: u8,
    pub changed: bool,
}
#[derive(Clone, Copy, Debug)]
pub struct Input {
    pub enabled: bool,
    pub same_mode: bool,
    pub frame: i32,
    pub previous_error: f32,
    pub current_error: f32,
    pub reference_error: f32,
    pub negative_delay: u8,
    pub positive_delay: u8,
}
pub fn linear(state: &mut State, input: Input) -> Result<bool, InvalidInput> {
    let i = input;
    if [i.previous_error, i.current_error, i.reference_error]
        .iter()
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    let reset = |s: &mut State, changed| {
        *s = State {
            changed,
            ..State::default()
        };
    };
    if !i.enabled || !i.same_mode {
        reset(state, true);
        return Ok(false);
    }
    if (i.previous_error != 0. || i.current_error == 0.) && 0. <= i.previous_error * i.current_error
    {
        reset(state, false);
        return Ok(false);
    }
    state.changed = true;
    let count = |start: i32| {
        let n = i.frame.wrapping_add(1).wrapping_sub(start);
        if n > 254 {
            255
        } else {
            n as u8
        }
    };
    let reference = i.reference_error * 0.98_f32;
    if 0. < i.current_error {
        if state.positive_start == 0 {
            state.positive_start = i.frame;
        }
        if i.current_error <= reference {
            state.positive_count = 0;
            state.positive_start = 0;
        } else {
            state.positive_count = count(state.positive_start);
        }
        state.negative_start = 0;
        state.negative_count = 0;
        if state.positive_count < i.positive_delay {
            return Ok(true);
        }
    }
    if 0. <= i.current_error {
        return Ok(false);
    }
    if state.negative_start == 0 {
        state.negative_start = i.frame;
    }
    if reference <= i.current_error {
        state.negative_count = 0;
        state.negative_start = 0;
    } else {
        state.negative_count = count(state.negative_start);
    }
    state.positive_start = 0;
    state.positive_count = 0;
    Ok(state.negative_count < i.negative_delay)
}

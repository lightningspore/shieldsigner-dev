//! Native AecStart/AecStop state transitions (ELF 0xa7618/0xa76a4).
//! This controls algorithm activation only; it does not start a camera stream.

/// Preserve native numeric states, including unknown values accepted by the
/// original. The initialized state is 1, stopped is 2 and running is 3.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct State(pub u32);

impl State {
    pub const INITIALIZED: Self = Self(1);

    /// Native return codes: 0 success, 3 invalid state, 8 null context.
    pub fn start(context: Option<&mut Self>) -> u8 {
        let Some(state) = context else {
            return 8;
        };
        if state.0.wrapping_sub(3) < 2 {
            return 3;
        }
        state.0 = 3;
        0
    }

    pub fn stop(context: Option<&mut Self>) -> u8 {
        let Some(state) = context else {
            return 8;
        };
        if state.0 == 4 {
            return 3;
        }
        state.0 = 2;
        0
    }
}

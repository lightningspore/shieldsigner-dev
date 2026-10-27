//! AwbPreProcV32 continuation after PrepareMeasureResult (ELF 0xc4ae0).
use crate::{awb_gain::Gains, InvalidInput};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct State {
    pub countdown: i32,
    pub frame: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Action {
    pub calculated: bool,
    pub reconfigure: bool,
}
impl State {
    /// Run gain calculation only for a pending update with complete data.
    /// The callback performs the gain-wrapper transition, including previous
    /// gain carry-forward. Red/blue scaling follows it and never changes that
    /// unscaled previous gain. Reconfiguration itself belongs to the caller.
    /// State/current gain commit on success; callback-owned state is the
    /// caller's responsibility if a later scale validation can fail.
    pub fn process(
        &mut self,
        update: bool,
        complete: bool,
        gain: &mut Gains,
        scale: Option<[f32; 2]>,
        calculate: impl FnOnce(&mut Gains) -> Result<(), InvalidInput>,
    ) -> Result<Action, InvalidInput> {
        if !update {
            return Ok(Action {
                calculated: false,
                reconfigure: false,
            });
        }
        let mut next = *self;
        if next.countdown > 0 {
            next.countdown -= 1;
        }
        let mut current = *gain;
        if complete {
            // Validate scale before a callback can commit its own state.
            if scale.is_some_and(|s| !s.iter().all(|x| x.is_finite())) {
                return Err(InvalidInput::NonFinite);
            }
            calculate(&mut current)?;
            if let Some(scale) = scale {
                current[0] *= scale[0];
                current[3] *= scale[1];
                if !current[0].is_finite() || !current[3].is_finite() {
                    return Err(InvalidInput::NonFinite);
                }
            }
            next.frame = next.frame.wrapping_add(1);
        }
        *self = next;
        *gain = current;
        Ok(Action {
            calculated: complete,
            reconfigure: true,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_scale_is_rejected_before_gain_callback_commits_state() {
        let mut state = State {
            countdown: 3,
            frame: 7,
        };
        let before = state;
        let mut gain = [1.; 4];
        let mut called = false;
        let result = state.process(true, true, &mut gain, Some([f32::NAN, 1.]), |_| {
            called = true;
            Ok(())
        });
        assert_eq!(result, Err(InvalidInput::NonFinite));
        assert!(!called);
        assert_eq!(state, before);
        assert_eq!(gain, [1.; 4]);
    }
}

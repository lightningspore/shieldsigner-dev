//! Saved-site gain reuse after AwbCalGainByWbMode (runAvaSiteRec, ELF 0xc7e70).
use crate::{awb_gain::Gains, InvalidInput};
#[derive(Clone, Copy)]
pub struct Settings {
    pub enabled: bool,
    pub frame_limit: u32,
    pub reuse_enabled: bool,
    pub gain_threshold: f32,
    pub sample_threshold: f32,
}
pub struct Input {
    pub frame: u32,
    /// Context +4; its application-level meaning is not yet established.
    pub application_flag: bool,
    /// Context +8; reuse requires the stored value to equal 1.
    pub application_mode: i32,
    pub reference_valid: bool,
    pub reference_gain: Gains,
    pub reference_sample: f32,
    pub sample: f32,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct State {
    pub matched: bool,
    pub frames: u32,
}
impl State {
    /// Preserve the original startup-only match test and post-match override.
    /// No filesystem I/O occurs in this helper; reference loading belongs to
    /// initialization. Invalid active arithmetic leaves state and gain intact.
    pub fn apply(
        &mut self,
        gain: &mut Gains,
        input: &Input,
        settings: &Settings,
    ) -> Result<(), InvalidInput> {
        if !settings.enabled || self.frames >= settings.frame_limit {
            return Ok(());
        }
        let mut next = self.clone();
        if settings.reuse_enabled && input.frame == 0 {
            if ![
                input.reference_sample,
                input.sample,
                settings.sample_threshold,
                settings.gain_threshold,
            ]
            .iter()
            .all(|x| x.is_finite())
            {
                return Err(InvalidInput::NonFinite);
            }
            let mean = (input.reference_sample + input.sample) * 0.5;
            let sample_distance = if (mean as f64) > 0.00001 {
                (input.reference_sample - input.sample).abs() / mean
            } else {
                0.
            };
            if !mean.is_finite() || !sample_distance.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            if sample_distance < settings.sample_threshold {
                let distance = if !input.reference_valid || ((gain[1] * gain[2]) as f64) <= 0.00001
                {
                    10.
                } else {
                    if !gain
                        .iter()
                        .chain(input.reference_gain.iter())
                        .all(|x| x.is_finite())
                    {
                        return Err(InvalidInput::NonFinite);
                    }
                    (input.reference_gain[0] / input.reference_gain[1] - gain[0] / gain[1]).abs()
                        + (input.reference_gain[3] / input.reference_gain[2] - gain[3] / gain[2])
                            .abs()
                };
                if !distance.is_finite() {
                    return Err(InvalidInput::NonFinite);
                }
                if distance < settings.gain_threshold {
                    next.matched = true;
                }
            }
        }
        if (!settings.reuse_enabled || next.matched)
            && !input.application_flag
            && input.application_mode == 1
            && input.reference_valid
        {
            if !input.reference_gain.iter().all(|x| x.is_finite()) {
                return Err(InvalidInput::NonFinite);
            }
            *gain = input.reference_gain;
        }
        next.frames = next.frames.wrapping_add(1);
        *self = next;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn nonfinite_ratio_leaves_match_counter_and_gain_unchanged() {
        let mut state = State {
            matched: false,
            frames: 0,
        };
        let mut gain = [2., 1., 1., 3.];
        let before = gain;
        let input = Input {
            frame: 0,
            application_flag: false,
            application_mode: 1,
            reference_valid: true,
            reference_gain: [2., 0., 1., 3.],
            reference_sample: 1.,
            sample: 1.,
        };
        let settings = Settings {
            enabled: true,
            frame_limit: 3,
            reuse_enabled: true,
            gain_threshold: 0.2,
            sample_threshold: 2.,
        };
        assert_eq!(
            state.apply(&mut gain, &input, &settings),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(
            state,
            State {
                matched: false,
                frames: 0
            }
        );
        assert_eq!(gain, before);
    }
    #[test]
    fn disabled_policy_does_not_read_inactive_nonfinite_fields() {
        let mut state = State {
            matched: true,
            frames: 1,
        };
        let mut gain = [1.; 4];
        let input = Input {
            frame: 0,
            application_flag: false,
            application_mode: 1,
            reference_valid: true,
            reference_gain: [f32::NAN; 4],
            reference_sample: f32::NAN,
            sample: f32::NAN,
        };
        let settings = Settings {
            enabled: false,
            frame_limit: 3,
            reuse_enabled: true,
            gain_threshold: f32::NAN,
            sample_threshold: f32::NAN,
        };
        assert_eq!(state.apply(&mut gain, &input, &settings), Ok(()));
        assert_eq!(
            state,
            State {
                matched: true,
                frames: 1
            }
        );
        assert_eq!(gain, [1.; 4]);
    }
}

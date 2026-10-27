//! Persistent non-blended selectCCM path (ELF 0xfe000).
use crate::{ccm_illuminant, ccm_selection, interpolate, InvalidInput};
#[derive(Clone, Copy)]
pub struct NamedProfile {
    pub name: [u8; 25],
    pub profile: ccm_selection::Profile,
}
pub struct Illuminant<'a> {
    pub gains: [f32; 2],
    pub sensor_gains: [f32; 4],
    pub saturations: [f32; 4],
    pub profiles: &'a [NamedProfile],
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub illuminant: usize,
    pub saturation: f32,
    pub high_name: [u8; 25],
    pub low_name: [u8; 25],
    pub matrix: [f32; 9],
    pub offsets: [f32; 3],
}
impl State {
    /// Preserve the caller's update flag on native early exits. `force` and
    /// `pending` are the explicit native context bytes at 0x55f and 0x560.
    /// Return native status, including -21 for an unpublished clamped pair;
    /// callers must preserve its automatic-controller early-exit behavior.
    pub fn process(
        &mut self,
        calibration: &[Illuminant<'_>],
        sensor_gain: f32,
        gains: [f32; 2],
        force: bool,
        pending: bool,
        updated: &mut bool,
    ) -> Result<i32, InvalidInput> {
        if calibration.len() > 9 {
            return Err(InvalidInput::Length);
        }
        let mut pairs = [[0.; 2]; 9];
        for (i, cal) in calibration.iter().enumerate() {
            pairs[i] = cal.gains;
        }
        let estimate = ccm_illuminant::estimate(&pairs[..calibration.len()], gains)?;
        if !estimate.matched {
            return Ok(-1);
        }
        let cal = &calibration[estimate.index];
        if cal.profiles.is_empty()
            || cal.profiles.len() > 5
            || cal.profiles.iter().any(|p| !p.name.contains(&0))
        {
            return Err(InvalidInput::Length);
        }
        let saturation = interpolate(&cal.sensor_gains, &cal.saturations, sensor_gain)?;
        let delta = (saturation - self.saturation).abs();
        if !pending && !force && self.illuminant == estimate.index && (delta as f64) <= 0.00001 {
            return Ok(0);
        }
        let mut profiles = [ccm_selection::Profile {
            saturation: 0.,
            matrix: [0.; 9],
            offsets: [0.; 3],
        }; 5];
        for (i, p) in cal.profiles.iter().enumerate() {
            profiles[i] = p.profile;
        }
        let selection = ccm_selection::select(&profiles[..cal.profiles.len()], saturation)?;
        let high = cal.profiles[selection.high].name;
        let low = cal.profiles[selection.low].name;
        let c_string_equal = |a: &[u8; 25], b: &[u8; 25]| {
            a.iter()
                .take_while(|v| **v != 0)
                .eq(b.iter().take_while(|v| **v != 0))
        };
        let publish = force
            || delta > 0.
            || !c_string_equal(&high, &self.high_name)
            || !c_string_equal(&low, &self.low_name);
        self.illuminant = estimate.index;
        self.saturation = saturation;
        for (destination, source) in [(&mut self.high_name, high), (&mut self.low_name, low)] {
            for (out, value) in destination.iter_mut().zip(source) {
                *out = value;
                if value == 0 {
                    break;
                }
            }
        }
        if publish {
            self.matrix = selection.matrix;
            self.offsets = selection.offsets;
        }
        *updated = publish;
        Ok(if !publish && selection.clamped {
            -21
        } else {
            0
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_calibration_does_not_commit_state_or_flag() {
        let mut state = State {
            illuminant: 3,
            saturation: 50.,
            high_name: [7; 25],
            low_name: [9; 25],
            matrix: [2.; 9],
            offsets: [3.; 3],
        };
        let original = state;
        let cal = Illuminant {
            gains: [1., 1.],
            sensor_gains: [1., 1., 4., 8.],
            saturations: [100., 75., 50., 25.],
            profiles: &[],
        };
        let mut updated = true;
        assert!(state
            .process(&[cal], 2., [1., 1.], true, false, &mut updated)
            .is_err());
        assert_eq!(state.illuminant, original.illuminant);
        assert_eq!(state.saturation, original.saturation);
        assert_eq!(state.high_name, original.high_name);
        assert_eq!(state.low_name, original.low_name);
        assert_eq!(state.matrix, original.matrix);
        assert_eq!(state.offsets, original.offsets);
        assert!(updated);
    }
}

#[cfg(test)]
mod status_tests {
    use super::*;
    #[test]
    fn pending_unchanged_clamp_preserves_native_minus_21_status() {
        let mut name = [0; 25];
        name[0] = b'p';
        let profiles = [NamedProfile {
            name,
            profile: ccm_selection::Profile {
                saturation: 100.,
                matrix: [1.; 9],
                offsets: [0.; 3],
            },
        }];
        let calibration = [Illuminant {
            gains: [1., 1.],
            sensor_gains: [1., 2., 4., 8.],
            saturations: [100.; 4],
            profiles: &profiles,
        }];
        let mut state = State {
            illuminant: 0,
            saturation: 0.,
            high_name: [0; 25],
            low_name: [0; 25],
            matrix: [0.; 9],
            offsets: [0.; 3],
        };
        let mut updated = false;
        assert_eq!(
            state.process(&calibration, 2., [1., 1.], true, false, &mut updated),
            Ok(0)
        );
        assert!(updated);
        let before = state;
        assert_eq!(
            state.process(&calibration, 1., [1., 1.], false, true, &mut updated),
            Ok(-21)
        );
        assert!(!updated);
        assert_eq!(state, before);
    }
}

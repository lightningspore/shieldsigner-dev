//! Region selection at the start of AwbCalGainByWbMode (ELF 0xc72b8).
use crate::{
    awb_luma_history::History,
    awb_probability::{self, Probability},
    InvalidInput,
};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Region {
    Normal = 0,
    Big = 1,
    Exclusion = 3,
}
/// StableXytpeSelection (ELF 0xc71cc). Short/disabled history preserves the
/// proposed value. Stable variance retains the previous value. NaN follows
/// the native unsigned-condition branch into voting. For
/// changing scenes, votes favor Big on a Normal/Big tie; Exclusion must win
/// strictly over both. Unrecognized history entries do not receive votes.
pub fn stabilize(
    values: &[u32],
    target: i32,
    variance: f32,
    threshold: f32,
    previous: Region,
    proposed: Region,
) -> Result<Region, InvalidInput> {
    if target < 0 {
        return Err(InvalidInput::Length);
    }
    if !threshold.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if target == 0 || values.len() < target as usize {
        return Ok(proposed);
    }
    if variance.is_nan() || variance > threshold {
        let counts = [0, 1, 3].map(|r| values.iter().filter(|&&v| v == r).count());
        if counts[2] > counts[0].max(counts[1]) {
            Ok(Region::Exclusion)
        } else if counts[0] > counts[1] {
            Ok(Region::Normal)
        } else {
            Ok(Region::Big)
        }
    } else {
        Ok(previous)
    }
}
/// AwbCalWPType (ELF 0xca000) uses signed i32 comparisons of stored u32 words.
pub fn white_point_kind(retained: u32, thresholds: [u32; 2]) -> u32 {
    if (retained as i32) <= (thresholds[1] as i32) {
        1
    } else if (retained as i32) <= (thresholds[0] as i32) {
        2
    } else {
        3
    }
}
pub struct Settings {
    pub absolute: f32,
    pub relative: f32,
    pub region_thresholds: [f32; 2],
    pub count_thresholds: [u32; 2],
    pub stabilization: bool,
    pub target: i32,
    pub variance: f32,
    pub variance_threshold: f32,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct State<const CAP: usize> {
    pub history: History<CAP>,
    pub selected: Region,
    pub retained: u32,
    pub kind: u32,
}
impl<const CAP: usize> State<CAP> {
    /// Join count filtering, fallback and stabilization. Exclusion selection
    /// replaces the retained count only when stabilization changes the proposed
    /// region to Exclusion. It preserves the last per-light count distribution.
    /// An unchanged Exclusion proposal retains the Big filtered count instead.
    pub fn select(
        &mut self,
        normal: &[u32],
        big: &[u32],
        exclusion: u32,
        output: &mut [Probability],
        settings: &Settings,
    ) -> Result<(), InvalidInput> {
        let n = normal.len();
        if n == 0 || n > 255 || big.len() != n || output.len() != n {
            return Err(InvalidInput::Length);
        }
        if settings.region_thresholds.iter().any(|v| !v.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        let mut next = self.clone();
        let zero = Probability {
            white_points: 0.,
            distance: 0.,
            luma: 0.,
            prior: 0.,
            total: 0.,
        };
        let mut staged = [zero; 255];
        staged[..n].copy_from_slice(output);
        let out = &mut staged[..n];
        let filter = |counts: &[u32], out: &mut [Probability]| {
            awb_probability::count_probabilities(
                counts.iter().copied(),
                out,
                settings.absolute,
                settings.relative,
            )
        };
        let mut retained = filter(normal, out)?;
        let mut proposed = Region::Normal;
        if retained as f32 <= settings.region_thresholds[0] {
            proposed = Region::Big;
            retained = filter(big, out)?;
            if retained as f32 <= settings.region_thresholds[1] && exclusion != 0 {
                proposed = Region::Exclusion;
            }
        }
        let mut selected = proposed;
        if settings.stabilization {
            next.history.update(proposed as i32, settings.target)?;
            selected = stabilize(
                next.history.values(),
                settings.target,
                settings.variance,
                settings.variance_threshold,
                self.selected,
                proposed,
            )?;
        }
        if selected != proposed {
            retained = if selected == Region::Exclusion {
                exclusion
            } else {
                filter(
                    if selected == Region::Normal {
                        normal
                    } else {
                        big
                    },
                    out,
                )?
            };
        }
        next.selected = selected;
        next.retained = retained;
        next.kind = white_point_kind(retained, settings.count_thresholds);
        *self = next;
        output.copy_from_slice(out);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejected_singleton_rotation_preserves_selection_and_probabilities() {
        let mut state = State::<4> {
            history: History::from_values(&[0]).unwrap(),
            selected: Region::Big,
            retained: 42,
            kind: 2,
        };
        let before = state.clone();
        let mut output = [Probability {
            white_points: 0.5,
            total: 1.,
            distance: 1.,
            luma: 1.,
            prior: 1.,
        }];
        let previous = output;
        let settings = Settings {
            absolute: 0.,
            relative: 0.,
            region_thresholds: [0.; 2],
            count_thresholds: [100, 10],
            stabilization: true,
            target: 1,
            variance: 0.,
            variance_threshold: 0.,
        };
        assert_eq!(
            state.select(&[100], &[100], 0, &mut output, &settings),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
        assert_eq!(output, previous);
    }
}

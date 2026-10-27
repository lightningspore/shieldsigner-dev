//! LSC nearest illuminant and rolling stability window (ELF 0x118498/0x118528/0x118576).
use crate::InvalidInput;
pub const WINDOW: usize = 15;
#[derive(Clone, Copy, Debug, PartialEq, Default)]
pub struct State {
    pub history: [u8; WINDOW],
    pub len: usize,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Estimate {
    pub nearest: usize,
    pub selected: usize,
    pub stable_window: bool,
}
impl State {
    /// SDK-supported groups contain at most seven illuminants. Before fifteen
    /// samples native keeps nearest selection; afterward it uses window mode,
    /// breaking count ties toward the lowest calibration index.
    pub fn process(
        &mut self,
        calibrated: &[[f32; 2]],
        current: [f32; 2],
    ) -> Result<Option<Estimate>, InvalidInput> {
        if calibrated.len() > 7
            || self.len > WINDOW
            || self.history[..self.len]
                .iter()
                .any(|id| usize::from(*id) >= calibrated.len())
        {
            return Err(InvalidInput::Length);
        }
        if current
            .iter()
            .chain(calibrated.iter().flatten())
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        let mut best = 9_999_999.;
        let mut nearest = None;
        for (index, gain) in calibrated.iter().enumerate() {
            let red = current[0] - gain[0];
            let blue = current[1] - gain[1];
            let distance = libm::sqrtf(libm::fmaf(red, red, blue * blue));
            if distance < best {
                best = distance;
                nearest = Some(index);
            }
        }
        let Some(nearest) = nearest else {
            return Ok(None);
        };
        if self.len == WINDOW {
            self.history.copy_within(1..WINDOW, 0);
            self.history[WINDOW - 1] = nearest as u8;
        } else {
            self.history[self.len] = nearest as u8;
            self.len += 1;
        }
        let mut selected = nearest;
        if self.len == WINDOW {
            let mut best_count = 0;
            for index in 0..calibrated.len() {
                let count = self
                    .history
                    .iter()
                    .filter(|id| usize::from(**id) == index)
                    .count();
                if count > best_count {
                    best_count = count;
                    selected = index;
                }
            }
        }
        Ok(Some(Estimate {
            nearest,
            selected,
            stable_window: self.len == WINDOW,
        }))
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_inputs_do_not_advance_history() {
        let mut state = State::default();
        let before = state;
        assert!(state.process(&[[1., 1.]], [f32::NAN, 1.]).is_err());
        assert_eq!(state, before);
        assert_eq!(state.process(&[], [1., 1.]), Ok(None));
        assert_eq!(state, before);
    }
}

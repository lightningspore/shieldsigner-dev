//! Standard AWB measurement-history gate (IsMeasureResultStable4, ELF 0xc2f90).
//! Outer preprocessor initialization and illumination selection remain separate.
use crate::InvalidInput;
#[derive(Clone, Debug, PartialEq)]
pub struct State {
    pub matched: u8,
    pub update: bool,
    pub history: [[f32; 4]; 8],
}
impl State {
    /// Compare red/blue ratios for `count` history records, preserving the
    /// incoming update request when all records match. Only requested updates
    /// replace a history slot. Native slot -1 aliases slot zero.
    /// `sums` is signed [red, green, blue], not per-illumination WP gain sums.
    pub fn measure(
        &mut self,
        sums: [i64; 3],
        count: usize,
        slot: i32,
        threshold: f32,
    ) -> Result<(), InvalidInput> {
        if count > 8 || !(-1..8).contains(&slot) {
            return Err(InvalidInput::Length);
        }
        if !threshold.is_finite()
            || self.history[..count]
                .iter()
                .flatten()
                .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        let current = if sums[0] > 0 && sums[2] > 0 {
            let green = sums[1] as f32;
            [green / (sums[0] as f32), 1., 1., green / (sums[2] as f32)]
        } else {
            [0.; 4]
        };
        let mut matched = 0u8;
        for (i, previous) in self.history[..count].iter().enumerate() {
            if (current[0] - previous[0]).abs() <= threshold
                && (current[3] - previous[3]).abs() <= threshold
            {
                matched |= 1 << i;
            }
        }
        self.matched = matched;
        if matched as u16 != (1u16 << count) - 1 {
            self.update = true;
        }
        if self.update {
            self.history[slot.max(0) as usize] = current;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_storage_boundary_does_not_change_history_or_flags() {
        let mut state = State {
            matched: 0xa5,
            update: false,
            history: [[1.; 4]; 8],
        };
        let before = state.clone();
        assert_eq!(
            state.measure([1, 1, 1], 9, 0, 0.1),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
        assert_eq!(
            state.measure([1, 1, 1], 8, 8, 0.1),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
    }
}

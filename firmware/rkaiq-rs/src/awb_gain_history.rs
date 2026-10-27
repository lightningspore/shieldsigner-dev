//! UpdateWbGainList / IsWbGainConverged / IsUpdateWbGain.
use crate::{awb_gain::Gains, InvalidInput};

fn finite(gain: &Gains) -> Result<(), InvalidInput> {
    if gain.iter().any(|v| !v.is_finite()) {
        Err(InvalidInput::NonFinite)
    } else {
        Ok(())
    }
}

/// Native convergence counts the optional proposal in the mean/denominator,
/// but only existing history entries contribute absolute deviations.
pub fn converged(
    history: &[Gains],
    proposal: Option<Gains>,
    threshold: f32,
) -> Result<bool, InvalidInput> {
    if !threshold.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let mut sum = [0.; 4];
    for gain in history.iter().chain(proposal.iter()) {
        finite(gain)?;
        for i in 0..4 {
            sum[i] += gain[i];
        }
    }
    let count = history.len() + usize::from(proposal.is_some());
    if count < 3 {
        return Ok(false);
    }
    let divisor = count as f32;
    let mean = sum.map(|v| v / divisor);
    finite(&mean)?;
    let mut deviation = [0.; 4];
    for gain in history {
        for i in 0..4 {
            deviation[i] += libm::fabsf(gain[i] - mean[i]);
        }
    }
    let deviation = deviation.map(|v| v / divisor);
    finite(&deviation)?;
    Ok(!deviation.iter().any(|&v| threshold <= v))
}

#[derive(Clone, Debug, PartialEq)]
pub struct History<const CAP: usize> {
    values: [Gains; CAP],
    len: usize,
}
impl<const CAP: usize> History<CAP> {
    pub fn from_values(values: &[Gains]) -> Result<Self, InvalidInput> {
        if values.len() > CAP {
            return Err(InvalidInput::Length);
        }
        for gain in values {
            finite(gain)?;
        }
        let mut result = Self {
            values: [[0.; 4]; CAP],
            len: values.len(),
        };
        result.values[..values.len()].copy_from_slice(values);
        Ok(result)
    }
    pub fn values(&self) -> &[Gains] {
        &self.values[..self.len]
    }
    /// A lower target rotates once without shrinking. Unlike the scalar-luma
    /// list helper, the native gain list handles target-1 singleton replacement.
    pub fn update(&mut self, gain: Gains, target: i32) -> Result<(), InvalidInput> {
        if target < 0 || target as usize > CAP {
            return Err(InvalidInput::Length);
        }
        if target == 0 {
            return Ok(());
        }
        finite(&gain)?;
        if self.len < target as usize {
            self.values[self.len] = gain;
            self.len += 1;
        } else {
            self.values[..self.len].rotate_left(1);
            self.values[self.len - 1] = gain;
        }
        Ok(())
    }
    pub fn should_update(
        &self,
        gain: Gains,
        target: i32,
        threshold: f32,
    ) -> Result<bool, InvalidInput> {
        if target < 0 {
            return Err(InvalidInput::Length);
        }
        if self.len < target as usize {
            return Ok(true);
        }
        Ok(!converged(self.values(), Some(gain), threshold)?)
    }
    /// Caller gate: append/rotate on update; otherwise use the previous tail.
    /// Gain/list are committed only after all checked numerical work succeeds.
    pub fn select(
        &mut self,
        gain: Gains,
        target: i32,
        threshold: f32,
    ) -> Result<(Gains, bool), InvalidInput> {
        let update = self.should_update(gain, target, threshold)?;
        if update {
            self.update(gain, target)?;
            Ok((gain, true))
        } else {
            Ok((*self.values().last().ok_or(InvalidInput::Length)?, false))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bad_target_preserves_history_and_singleton_replacement_is_supported() {
        let mut history = History::<4>::from_values(&[[1.; 4]]).unwrap();
        let before = history.clone();
        assert_eq!(history.update([2.; 4], 5), Err(InvalidInput::Length));
        assert_eq!(history, before);
        history.update([2.; 4], 1).unwrap();
        assert_eq!(history.values(), &[[2.; 4]]);
    }
}

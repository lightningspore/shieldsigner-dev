//! UpdateLvValueList / CalculateVarianceLuma (ELF 0xc9e54 / 0xc9ea4).
//! Native intrusive allocation is replaced by explicit bounded owned storage.
use crate::InvalidInput;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct History<const CAP: usize> {
    values: [u32; CAP],
    len: usize,
}
impl<const CAP: usize> History<CAP> {
    pub fn from_values(values: &[u32]) -> Result<Self, InvalidInput> {
        if values.len() > CAP {
            return Err(InvalidInput::Length);
        }
        let mut out = Self {
            values: [0; CAP],
            len: values.len(),
        };
        out.values[..values.len()].copy_from_slice(values);
        Ok(out)
    }
    pub fn values(&self) -> &[u32] {
        &self.values[..self.len]
    }
    /// Zero length is a no-op. A reduced nonzero target rotates one oldest
    /// entry; it does not truncate an already longer native list.
    /// Native stores the signed input's bits, then reads them as unsigned luma.
    /// Reject its corrupting singleton/target-1 case before changing storage.
    pub fn update(&mut self, value: i32, target: i32) -> Result<(), InvalidInput> {
        if target < 0 || target as usize > CAP || (target == 1 && self.len == 1) {
            return Err(InvalidInput::Length);
        }
        if target == 0 {
            return Ok(());
        }
        if self.len < (target as usize) {
            self.values[self.len] = value as u32;
            self.len += 1;
        } else {
            self.values[..self.len].rotate_left(1);
            self.values[self.len - 1] = value as u32;
        }
        Ok(())
    }
    /// Population mean of squared relative deviations, using native f32/FMA
    /// ordering. Empty history returns zero. Nonempty all-zero history produces
    /// the native ARM quiet NaN (0x7fc00000), not a fabricated zero variance.
    pub fn variance(&self) -> f32 {
        let mut sum = 0f32;
        for &value in self.values() {
            sum += value as f32;
        }
        if self.len == 0 {
            return 0.;
        }
        if sum == 0. {
            return f32::from_bits(0x7fc00000);
        }
        let mean = sum / (self.len as f32);
        let mut squared = 0f32;
        for &value in self.values() {
            let delta = (value as f32) / mean - 1.;
            squared = libm::fmaf(delta, delta, squared);
        }
        if squared == 0. {
            0.
        } else {
            squared / (self.len as f32)
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_capacity_request_preserves_history() {
        let mut history = History::<4>::from_values(&[1, 2, 3]).unwrap();
        let original = history.clone();
        assert_eq!(history.update(5, -1), Err(InvalidInput::Length));
        assert_eq!(history, original);
        assert_eq!(history.update(5, 5), Err(InvalidInput::Length));
        assert_eq!(history, original);
        let mut singleton = History::<4>::from_values(&[42]).unwrap();
        let before = singleton.clone();
        assert_eq!(singleton.update(43, 1), Err(InvalidInput::Length));
        assert_eq!(singleton, before);
    }
}

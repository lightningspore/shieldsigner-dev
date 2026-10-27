//! CCM Damping (ELF 0xfd6f8), distinct from the same-named LUT3D routine.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub matrix: [f32; 9],
    pub offsets: [f32; 3],
}
impl State {
    /// Blend every value and report native convergence without snapping to target.
    /// Validated unit-interval damping; invalid input does not change the cache.
    pub fn process(&mut self, target: &State, damping: f32) -> Result<bool, InvalidInput> {
        if !damping.is_finite()
            || self
                .matrix
                .iter()
                .chain(self.offsets.iter())
                .chain(target.matrix.iter())
                .chain(target.offsets.iter())
                .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if !(0. ..=1.).contains(&damping) {
            return Err(InvalidInput::AlphaRange);
        }
        let complement = 1. - damping;
        let mut converged = true;
        for (value, target) in self
            .matrix
            .iter_mut()
            .chain(self.offsets.iter_mut())
            .zip(target.matrix.iter().chain(target.offsets.iter()))
        {
            *value = libm::fmaf(*value, damping, *target * complement);
            if ((*value - *target).abs() as f64) > 0.00001 {
                converged = false;
            }
        }
        Ok(converged)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_inputs_preserve_cache() {
        let mut cache = State {
            matrix: [1.; 9],
            offsets: [2.; 3],
        };
        let target = cache;
        for weight in [f32::NAN, -0.1, 1.1] {
            assert!(cache.process(&target, weight).is_err());
            assert_eq!(cache.matrix, [1.; 9]);
            assert_eq!(cache.offsets, [2.; 3]);
        }
    }
}

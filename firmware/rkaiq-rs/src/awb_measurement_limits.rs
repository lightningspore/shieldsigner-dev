//! Brightness-dependent channel limits in ReconfigHwParaV32.
//! The caller owns the group-boundary/update gate and effective configuration.
use crate::{interpolate, isp_awb_measurement::INPUT_BYTES, InvalidInput};
pub struct Limits<'a> {
    pub knots: &'a [f32],
    /// Native order: R max/min, G max/min, B max/min, Y max/min, in Q4 units.
    pub values: [&'a [f32]; 8],
}
impl Limits<'_> {
    /// Return whether any channel limit changed. Native rounds after promoting
    /// interpolation output to f64, then narrows the unsigned result to u16.
    /// Errors leave the complete SDK record unchanged.
    pub fn apply(
        &self,
        brightness: u32,
        record: &mut [u8; INPUT_BYTES],
    ) -> Result<bool, InvalidInput> {
        if self.knots.is_empty() || self.knots.windows(2).any(|p| p[0] >= p[1]) {
            return Err(InvalidInput::Length);
        }
        let mut next = [0u8; 16];
        for i in 0..8 {
            let value = interpolate(self.knots, self.values[i], brightness as f32)?;
            if !value.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            let rounded = ((value as f64 + 0.5) as u32) as u16;
            next[i * 2..i * 2 + 2].copy_from_slice(&rounded.to_le_bytes());
        }
        let changed = record[0x4a..0x5a] != next;
        record[0x4a..0x5a].copy_from_slice(&next);
        Ok(changed)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn late_bad_table_is_atomic_and_repeated_application_is_unchanged() {
        let mut record = [0xa5; INPUT_BYTES];
        let mut values = [&[48.][..]; 8];
        values[7] = &[];
        let mut limits = Limits {
            knots: &[0.],
            values,
        };
        assert!(limits.apply(0, &mut record).is_err());
        assert_eq!(record, [0xa5; INPUT_BYTES]);
        limits.values[7] = &[48.];
        assert_eq!(limits.apply(0, &mut record), Ok(true));
        assert_eq!(limits.apply(0, &mut record), Ok(false));
        for (i, b) in record.iter().enumerate() {
            if !(0x4a..0x5a).contains(&i) {
                assert_eq!(*b, 0xa5);
            }
        }
    }
}

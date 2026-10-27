//! Normal-exposure sensor SNR flag from AecCISFeature / AeCISFeature.
use crate::{ae_publication::Record, InvalidInput};
pub const SNR_OFFSET: usize = 240;
/// Optional kernel NR switch fields: direction, upper, lower, divisor. Inside
/// the hysteresis band retain the caller's prior flag. Without switch metadata,
/// native derives the flag from signed DCG > 0. Only the flag byte is changed.
pub fn normal(record: &mut Record, noise_switch: Option<[u32; 4]>) -> Result<u8, InvalidInput> {
    let mut flag = record[SNR_OFFSET];
    if let Some([direction, upper, lower, divisor]) = noise_switch {
        if divisor == 0 {
            return Err(InvalidInput::DegenerateRange);
        }
        let gain = f32::from_le_bytes(record[4..8].try_into().unwrap());
        if !gain.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let high = upper as f32 / divisor as f32;
        let low = lower as f32 / divisor as f32;
        if high <= gain {
            flag = u8::from(direction == 0);
        }
        // Native's second comparison can overwrite the first for overlapping
        // thresholds. Equality at the lower threshold retains the prior value.
        if gain < low {
            flag = u8::from(direction != 0);
        }
    } else {
        flag = u8::from(i32::from_le_bytes(record[20..24].try_into().unwrap()) > 0);
    }
    record[SNR_OFFSET] = flag;
    Ok(flag)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_switch_preserves_exposure_record() {
        let mut record = [0xa5; 244];
        let before = record;
        assert_eq!(
            normal(&mut record, Some([0, 10, 5, 0])),
            Err(InvalidInput::DegenerateRange)
        );
        assert_eq!(record, before);
    }
}

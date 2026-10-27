//! AecGetRunFlag (ELF 0xb31f0). Field names retain context offsets where
//! the surrounding calibration/state lifecycle has not yet been recovered.
use crate::InvalidInput;

#[derive(Clone, Copy, Debug)]
pub struct Policy {
    pub enabled_4fb9: u8,
    pub channel_mode_23cd: u8,
    pub unchanged_23cf: [u8; 3],
    pub overrides_3d3c: [u8; 3],
}

/// Compare previous/current Q8 means. Returns the native byte, not a normalized
/// boolean. Single-channel mode requires one pair; channel mode accepts 0..=3.
/// Populating the previous samples and override flags remains caller work.
pub fn select(policy: Policy, previous: &[u16], current: &[u16]) -> Result<u8, InvalidInput> {
    if previous.len() != current.len()
        || previous.len() > 3
        || (policy.channel_mode_23cd == 0 && previous.len() != 1)
    {
        return Err(InvalidInput::Length);
    }
    if policy.enabled_4fb9 == 0 {
        return Ok(1);
    }
    let mut result = 0;
    for (i, (&old, &new)) in previous.iter().zip(current).enumerate() {
        // ARM performs division in double, rounds to float, then compares
        // the promoted float against the double literal 0.03.
        let difference = (i32::from(old) - i32::from(new)).unsigned_abs();
        let relative = (f64::from(difference) / f64::from(old.max(1))) as f32;
        let unchanged = f64::from(relative) <= 0.03;
        let candidate = if policy.channel_mode_23cd == 0 {
            if unchanged {
                policy.unchanged_23cf[i]
            } else {
                policy.enabled_4fb9
            }
        } else if unchanged {
            if policy.unchanged_23cf[i] == 0 {
                result
            } else {
                policy.unchanged_23cf[i]
            }
        } else {
            policy.channel_mode_23cd
        };
        result = if policy.overrides_3d3c[i] == 0 {
            candidate
        } else {
            policy.overrides_3d3c[i]
        };
    }
    Ok(result)
}

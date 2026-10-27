//! LSC stable profile ordering, endpoint selection and Q16 four-plane blending.
use crate::InvalidInput;
pub const SAMPLES: usize = 4 * 17 * 17;
pub const MAX_PROFILES: usize = 5;
pub struct Profile<'a> {
    pub vignetting: f32,
    pub samples: &'a [u16; SAMPLES],
}
#[derive(Debug, PartialEq)]
pub struct Selection {
    /// Original input indices, preserving native stable ordering for equal keys.
    pub high: usize,
    pub low: usize,
    pub samples: [u16; SAMPLES],
}
pub fn select(profiles: &[Profile<'_>], vignetting: f32) -> Result<Selection, InvalidInput> {
    if profiles.is_empty() || profiles.len() > MAX_PROFILES {
        return Err(InvalidInput::Length);
    }
    if !vignetting.is_finite() || profiles.iter().any(|p| !p.vignetting.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    let mut order = [0, 1, 2, 3, 4];
    for end in (1..profiles.len()).rev() {
        for i in 0..end {
            if profiles[order[i]].vignetting < profiles[order[i + 1]].vignetting {
                order.swap(i, i + 1);
            }
        }
    }
    let first = order[0];
    let last = order[profiles.len() - 1];
    let (high, low) = if vignetting >= profiles[first].vignetting {
        (first, first)
    } else if vignetting <= profiles[last].vignetting {
        (last, last)
    } else {
        let lower = (1..profiles.len())
            .find(|i| profiles[order[*i]].vignetting < vignetting)
            .ok_or(InvalidInput::Length)?;
        (order[lower - 1], order[lower])
    };
    let mut samples = *profiles[high].samples;
    if high != low {
        let high_v = profiles[high].vignetting;
        let low_v = profiles[low].vignetting;
        let weight = (low_v - vignetting) / (low_v - high_v);
        // Native truncates these independently; integer weights need not sum to 65536.
        let high_weight = (weight * 65536.) as u32;
        let low_weight = ((1. - weight) * 65536.) as u32;
        for (i, out) in samples.iter_mut().enumerate() {
            *out = high_weight
                .wrapping_mul(u32::from(profiles[high].samples[i]))
                .wrapping_add(low_weight.wrapping_mul(u32::from(profiles[low].samples[i])))
                .wrapping_add(0x8000)
                .wrapping_shr(16) as u16;
        }
    }
    Ok(Selection { high, low, samples })
}

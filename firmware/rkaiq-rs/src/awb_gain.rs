//! Native AWB weighted-statistics gains, normalization, mixture and damping.
//! These are stages of the original algorithm, not a standalone AWB controller.
use crate::InvalidInput;

/// Channel order throughout this module is R, Gr, Gb, B.
pub type Gains = [f32; 4];

/// AwbGainOffset (ELF 0xca658). Apply all channel offsets only when every
/// resulting channel is nonnegative; otherwise preserve the complete gain.
pub fn offset(gain: Gains, offsets: Gains) -> Result<Gains, InvalidInput> {
    finite(&gain)?;
    finite(&offsets)?;
    let output = core::array::from_fn(|i| gain[i] + offsets[i]);
    finite(&output)?;
    Ok(if output.iter().all(|&v| v >= 0.) {
        output
    } else {
        gain
    })
}
fn finite(values: &[f32]) -> Result<(), InvalidInput> {
    if values.iter().all(|v| v.is_finite()) {
        Ok(())
    } else {
        Err(InvalidInput::NonFinite)
    }
}

/// AwbGainNormal (ELF 0xca030): the divisor starts at 5, rather than infinity.
/// Nonpositive or very small minima leave the values unchanged.
pub fn normalize(mut gain: Gains) -> Result<Gains, InvalidInput> {
    finite(&gain)?;
    let mut divisor = 5.;
    for value in gain {
        if value <= divisor {
            divisor = value;
        }
    }
    if (divisor as f64) > 0.00001 {
        for value in &mut gain {
            *value /= divisor;
        }
    }
    finite(&gain)?;
    Ok(gain)
}

/// AwbGainMixture (ELF 0xca080): blend with weight on the first input, then
/// normalize. The native blend uses a rounded product followed by an FMA.
pub fn mixture(first: Gains, second: Gains, weight: f32) -> Result<Gains, InvalidInput> {
    finite(&first)?;
    finite(&second)?;
    finite(&[weight])?;
    let complement = 1. - weight;
    normalize(core::array::from_fn(|i| {
        libm::fmaf(first[i], weight, complement * second[i])
    }))
}

/// AwbCalGainInSpatial (ELF 0xc66d0), for one illumination. Endpoints are
/// copied verbatim; only interpolation calls the normalizing gain mixture.
/// Threshold order is intentionally not changed or validated as ascending.
pub fn spatial(
    brightness: u32,
    low_threshold: u32,
    high_threshold: u32,
    low_gain: Gains,
    high_gain: Gains,
) -> Result<Gains, InvalidInput> {
    if brightness < low_threshold {
        finite(&low_gain)?;
        return Ok(low_gain);
    }
    if brightness > high_threshold {
        finite(&high_gain)?;
        return Ok(high_gain);
    }
    let low = low_threshold as f32;
    let width = high_threshold as f32 - low;
    let ratio = if width as f64 >= 0.0001 {
        (brightness as f32 - low) / width
    } else {
        1.
    };
    mixture(low_gain, high_gain, 1. - ratio)
}

/// AwbCalGainBySpatialMulStatistics (ELF 0xc67a8), for one illumination.
/// The stored byte is a percentage, including values above 100; no clamp.
pub fn spatial_statistics(
    statistics: Gains,
    spatial: Gains,
    percentage: u8,
) -> Result<(Gains, f32), InvalidInput> {
    let weight = percentage as f32 / 100.;
    Ok((mixture(statistics, spatial, weight)?, weight))
}

/// AwbCalGainInTemporalGain (ELF 0xc5d5c): list-order weighted history,
/// without normalization. Empty history copies the configured default, as
/// AwbCalGainInTemporalGain2 (ELF 0xc5d3c) does unconditionally.
pub fn temporal_history(
    history: &[Gains],
    weights: &[u8],
    default: Gains,
) -> Result<Gains, InvalidInput> {
    if history.is_empty() {
        finite(&default)?;
        return Ok(default);
    }
    if weights.len() < history.len() {
        return Err(InvalidInput::Length);
    }
    let mut sum = [0.; 4];
    let mut total = 0i32;
    for (gain, &weight) in history.iter().zip(weights) {
        finite(gain)?;
        total = total.wrapping_add(weight as i32);
        for i in 0..4 {
            sum[i] = libm::fmaf(gain[i], weight as f32, sum[i]);
        }
    }
    for value in &mut sum {
        *value /= total as f32;
    }
    finite(&sum)?;
    Ok(sum)
}

/// AwbCalGainTotalMulTemp (ELF 0xc6860). The 16-point percentage curve uses
/// unsigned integer comparisons before f32 interpolation. Returned weight is
/// the raw percentage, not a fraction. No clamp or sorting is applied.
pub fn temporal_blend(
    current: Gains,
    temporal: Gains,
    brightness: u32,
    knots: &[u32; 16],
    percentages: &[u8; 16],
) -> Result<(Gains, f32), InvalidInput> {
    finite(&current)?;
    finite(&temporal)?;
    let weight = if brightness <= knots[0] {
        percentages[0] as f32
    } else if brightness >= knots[15] {
        percentages[15] as f32
    } else {
        let index = knots
            .iter()
            .position(|&v| brightness < v)
            .map_or(14, |i| i - 1);
        let low = knots[index] as f32;
        let width = knots[index + 1] as f32 - low;
        let base = percentages[index] as f32;
        if width as f64 >= 0.001 {
            let ratio = (brightness as f32 - low) / width;
            libm::fmaf(ratio, percentages[index + 1] as f32 - base, base)
        } else {
            base
        }
    };
    let complement = 100. - weight;
    let gain = normalize(core::array::from_fn(|i| {
        libm::fmaf(temporal[i], weight, complement * current[i]) / 100.
    }))?;
    Ok((gain, weight))
}

#[cfg(test)]
mod temporal_tests {
    use super::*;

    #[test]
    fn history_rejects_missing_or_zero_weights_but_empty_uses_default() {
        assert_eq!(
            temporal_history(&[[1.; 4]], &[], [2.; 4]),
            Err(InvalidInput::Length)
        );
        assert_eq!(
            temporal_history(&[[1.; 4]], &[0], [2.; 4]),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(temporal_history(&[], &[], [2.; 4]), Ok([2.; 4]));
    }
}

/// AwbGainCalbyRgainBgain (ELF 0xca7cc). Inputs are accumulated gain statistics,
/// not raw R/G/B pixel sums. Each signed total rounds to f32 before division.
pub fn ratios(weighted_count: i64, red_total: i64, blue_total: i64) -> Gains {
    if weighted_count == 0 {
        [0.; 4]
    } else {
        let divisor = weighted_count as f32;
        [
            red_total as f32 / divisor,
            1.,
            1.,
            blue_total as f32 / divisor,
        ]
    }
}

/// AwbCalGainForDiffIllumAndDiffXYType2 (ELF 0xc99d8): normalize one
/// illumination/XY-region result and round its weighted count from Q10.
pub fn statistics_gain(
    weighted_count: i64,
    red_total: i64,
    blue_total: i64,
) -> Result<(Gains, i64), InvalidInput> {
    Ok((
        normalize(ratios(weighted_count, red_total, blue_total))?,
        weighted_count.wrapping_add(512) >> 10,
    ))
}

#[derive(Clone, Copy, Debug)]
pub struct DampingParameters {
    pub variance_threshold: f32,
    pub step: f32,
    pub minimum: f32,
    pub maximum: f32,
}
impl DampingParameters {
    /// AwbCalDampFactor (ELF 0xc9f2c): adapt the prior coefficient up/down by
    /// one step. Preserve the native ordered lower/upper-bound comparisons.
    pub fn adapt(self, prior: f32, variance: f32) -> Result<f32, InvalidInput> {
        finite(&[
            self.variance_threshold,
            self.step,
            self.minimum,
            self.maximum,
            prior,
            variance,
        ])?;
        let candidate = if self.variance_threshold < variance {
            prior - self.step
        } else {
            prior + self.step
        };
        let value = if candidate < self.minimum {
            self.minimum
        } else if self.maximum < candidate {
            self.maximum
        } else {
            candidate
        };
        finite(&[value])?;
        Ok(value)
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Damped {
    pub gain: Gains,
    /// Base coefficient is reset to zero when previous R is below 1e-5.
    pub base_coefficient: f32,
    pub effective_coefficient: f32,
}

/// AwbCalDampGain (ELF 0xca0e0). Does not modify the previous-frame gains;
/// the outer native caller advances that history after the remaining stages.
pub fn damp(previous: Gains, candidate: Gains, coefficient: f32) -> Result<Damped, InvalidInput> {
    finite(&previous)?;
    finite(&candidate)?;
    finite(&[coefficient])?;
    if (previous[0] as f64) < 0.00001 {
        return Ok(Damped {
            gain: candidate,
            base_coefficient: 0.,
            effective_coefficient: 0.,
        });
    }
    let mut difference = 0.;
    for i in 0..4 {
        let delta = libm::fabsf(candidate[i] - previous[i]);
        if difference < delta {
            difference = delta;
        }
    }
    let adjustment = if (difference as f64) < 0.3 {
        crate::interpolate(
            &[0.01, 0.05, 0.1, 0.15, 0.3],
            &[0., 0.5, 0.7, 0.9, 1.],
            difference,
        )?
    } else {
        1.
    };
    let effective = adjustment * coefficient;
    let complement = 1. - effective;
    let gain =
        core::array::from_fn(|i| libm::fmaf(previous[i], effective, complement * candidate[i]));
    finite(&gain)?;
    finite(&[effective])?;
    Ok(Damped {
        gain,
        base_coefficient: coefficient,
        effective_coefficient: effective,
    })
}

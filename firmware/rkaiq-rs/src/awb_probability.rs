//! Original AWB white-point filtering and total illumination probability path.
//! Consumes selected-region counts and calibrated tables, not raw RGB averages.
use crate::{awb_gain::Gains, InvalidInput};

#[derive(Clone, Copy, Debug)]
pub struct Curve<'a> {
    pub knots: &'a [f32],
    pub weights: &'a [f32],
}
#[derive(Clone, Copy, Debug)]
pub struct Light<'a> {
    pub reference_gain: Gains,
    /// Selected-region gain after upstream per-illumination processing.
    pub statistic_gain: Gains,
    pub kind: i32,
    pub white_points: u32,
    pub prior: Curve<'a>,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Probability {
    pub total: f32,
    pub distance: f32,
    pub luma: f32,
    pub prior: f32,
    pub white_points: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Settings {
    pub gain: Gains,
    pub frame: u32,
    /// Native context mode string equals FASTAWBACT.
    pub fast: bool,
    pub near_distance_squared: f32,
    pub far_distance_squared: f32,
    pub brightness: u32,
    pub brightness_thresholds: [u32; 4],
    pub prior_sample: f32,
    pub absolute_count_threshold: f32,
    pub relative_count_threshold: f32,
}
fn finite(values: &[f32]) -> Result<(), InvalidInput> {
    if values.iter().all(|v| v.is_finite()) {
        Ok(())
    } else {
        Err(InvalidInput::NonFinite)
    }
}

/// AwbCalGainTotal (ELF 0xc696c): accumulate each channel in light order with
/// the original FMA instructions, then apply native gain normalization.
pub fn weighted_gain(
    lights: &[Light<'_>],
    probabilities: &[Probability],
) -> Result<Gains, InvalidInput> {
    if lights.len() != probabilities.len() {
        return Err(InvalidInput::Length);
    }
    weighted_gain_values(
        lights
            .iter()
            .zip(probabilities)
            .map(|(l, p)| (l.statistic_gain, p.total)),
    )
}

/// Value-level accumulator shared with the gain strategies after they replace
/// per-light statistic gains. Same light order and normalization as above.
pub fn weighted_gain_values(
    values: impl ExactSizeIterator<Item = (Gains, f32)>,
) -> Result<Gains, InvalidInput> {
    if values.len() == 0 || values.len() > 255 {
        return Err(InvalidInput::Length);
    }
    let mut gain = [0.; 4];
    for (channels, probability) in values {
        finite(&channels)?;
        finite(&[probability])?;
        for (value, channel) in gain.iter_mut().zip(channels) {
            *value = libm::fmaf(probability, channel, *value);
        }
    }
    crate::awb_gain::normalize(gain)
}

/// Calls corresponding to AwbCalWpNoProbablity then AwbCalTotalProbablity.
/// The latter calls the original distance, brightness and source-prior stages.
/// Existing luma probabilities matter for unrecognized light kinds, because
/// the native brightness stage leaves their raw values untouched.
pub fn calculate(
    lights: &[Light<'_>],
    output: &mut [Probability],
    settings: Settings,
) -> Result<u32, InvalidInput> {
    calculate_impl(lights, output, settings, true)
}

/// AwbCalTotalProbablity alone, preserving count probabilities selected by
/// the region controller. Does not repeat AwbCalWpNoProbablity.
pub fn total_probabilities(
    lights: &[Light<'_>],
    output: &mut [Probability],
    settings: Settings,
) -> Result<(), InvalidInput> {
    calculate_impl(lights, output, settings, false).map(|_| ())
}

fn calculate_impl(
    lights: &[Light<'_>],
    output: &mut [Probability],
    settings: Settings,
    filter_counts: bool,
) -> Result<u32, InvalidInput> {
    let n = lights.len();
    if n == 0 || n > 255 || output.len() != n {
        return Err(InvalidInput::Length);
    }
    finite(&settings.gain)?;
    finite(&[
        settings.near_distance_squared,
        settings.far_distance_squared,
        settings.prior_sample,
    ])?;
    if filter_counts {
        finite(&[
            settings.absolute_count_threshold,
            settings.relative_count_threshold,
        ])?;
    }
    for (light, probability) in lights.iter().zip(output.iter()) {
        finite(&light.reference_gain)?;
        finite(&[probability.luma])?;
        if !filter_counts {
            finite(&[probability.white_points])?;
        }
        // Validate all tables before changing outputs. The scalar interpolation
        // helper independently checks length, monotonic knots and finite values.
        crate::interpolate(
            light.prior.knots,
            light.prior.weights,
            settings.prior_sample,
        )?;
        if light.reference_gain[1] == 0. || light.reference_gain[2] == 0. {
            return Err(InvalidInput::GainRange);
        }
    }
    let uniform = 1. / n as f32;
    let retained_count = if filter_counts {
        count_probabilities(
            lights.iter().map(|l| l.white_points),
            output,
            settings.absolute_count_threshold,
            settings.relative_count_threshold,
        )?
    } else {
        0
    };
    let mut sum;

    let [red, green_red, green_blue, blue] = settings.gain;
    let product = ((red * blue) * green_red) * green_blue;
    if (product as f64) <= 0.00001 || settings.frame == 0 || settings.fast {
        for probability in output.iter_mut() {
            probability.distance = uniform;
        }
    } else {
        let current_red = red / green_red;
        let current_blue = blue / green_blue;
        sum = 0.;
        for (light, probability) in lights.iter().zip(output.iter_mut()) {
            let [r, gr, gb, b] = light.reference_gain;
            let dr = r / gr - current_red;
            let db = b / gb - current_blue;
            let distance = libm::fmaf(dr, dr, db * db);
            probability.distance = if distance <= settings.near_distance_squared {
                1.
            } else if distance < settings.far_distance_squared {
                (settings.far_distance_squared - distance)
                    / (settings.far_distance_squared - settings.near_distance_squared)
            } else {
                0.
            };
            sum += probability.distance;
        }
        for probability in output.iter_mut() {
            probability.distance = if (sum as f64) >= 0.00001 {
                probability.distance / sum
            } else {
                uniform
            };
        }
    }

    if settings.fast {
        for probability in output.iter_mut() {
            probability.luma = uniform;
            probability.prior = 1.;
        }
    } else {
        let [a, b, c, d] = settings.brightness_thresholds;
        let lv = settings.brightness;
        let ramp = if lv < a || lv < b {
            0.5
        } else if d < lv {
            0.99
        } else if c < lv {
            // Native differences round to f32 first, then the ramp uses
            // double multiplication/division/addition and narrows once.
            (((lv as f32 - c as f32) as f64 * 0.5) / (d as f32 - c as f32) as f64 + 0.5) as f32
        } else {
            0.5
        };
        let middle = if ramp < 0.5 { 1. - ramp } else { ramp };
        sum = 0.;
        for (light, probability) in lights.iter().zip(output.iter_mut()) {
            let value = match light.kind {
                3 => Some(ramp),
                1 => Some(1. - ramp),
                2 => Some(middle),
                _ => None,
            };
            if let Some(value) = value {
                probability.luma = value;
                sum += value;
            }
        }
        for probability in output.iter_mut() {
            probability.luma = if (sum as f64) >= 0.00001 {
                probability.luma / sum
            } else {
                uniform
            };
        }
        sum = 0.;
        for (light, probability) in lights.iter().zip(output.iter_mut()) {
            probability.prior = crate::interpolate(
                light.prior.knots,
                light.prior.weights,
                settings.prior_sample,
            )?;
            sum += probability.prior;
        }
        for probability in output.iter_mut() {
            // Preserve native integer quotient, not floating-point uniform.
            probability.prior = if (sum as f64) > 0.00001 {
                probability.prior / sum
            } else {
                (1 / n) as f32
            };
        }
    }

    sum = 0.;
    for probability in output.iter_mut() {
        probability.total = ((probability.luma * probability.distance) * probability.white_points)
            * probability.prior;
        sum += probability.total;
    }
    if (sum as f64) <= 0.00001 {
        let count_sum = output.iter().fold(0., |sum, p| sum + p.white_points);
        for probability in output.iter_mut() {
            probability.total = if (count_sum as f64) <= 0.00001 {
                uniform
            } else {
                probability.white_points / count_sum
            };
        }
    } else {
        for probability in output.iter_mut() {
            probability.total /= sum;
        }
    }
    for probability in output.iter() {
        finite(&[
            probability.total,
            probability.distance,
            probability.luma,
            probability.prior,
            probability.white_points,
        ])?;
    }
    Ok(retained_count as u32)
}

/// AwbCalWpNoProbablity count filtering. Writes only white-point probability;
/// other output fields remain available for later stages. Returns retained sum's
/// low u32 word, while probability division uses the full 64-bit sum.
pub fn count_probabilities<I: Iterator<Item = u32> + Clone>(
    counts: I,
    output: &mut [Probability],
    absolute: f32,
    relative: f32,
) -> Result<u32, InvalidInput> {
    let n = output.len();
    if n == 0 || n > 255 || counts.clone().count() != n {
        return Err(InvalidInput::Length);
    }
    finite(&[absolute, relative])?;
    let total: u64 = counts.clone().map(u64::from).sum();
    let cutoff = absolute as u32;
    let keep =
        |value: u32| total != 0 && !((value as f32 / total as f32) <= relative && value <= cutoff);
    let retained: u64 = counts.clone().filter(|v| keep(*v)).map(u64::from).sum();
    let mut sum = 0.;
    for (value, p) in counts.zip(output.iter_mut()) {
        p.white_points = if keep(value) {
            value as f32 / retained as f32
        } else {
            0.
        };
        sum += p.white_points;
    }
    if sum as f64 <= 0.00001 {
        for p in output {
            p.white_points = 1. / n as f32;
        }
    }
    Ok(retained as u32)
}

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
    if lights.is_empty() || lights.len() > 255 || lights.len() != probabilities.len() {
        return Err(InvalidInput::Length);
    }
    let mut gain = [0.; 4];
    for (light, probability) in lights.iter().zip(probabilities) {
        finite(&light.statistic_gain)?;
        finite(&[probability.total])?;
        for (value, channel) in gain.iter_mut().zip(light.statistic_gain) {
            *value = libm::fmaf(probability.total, channel, *value);
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
    let n = lights.len();
    if n == 0 || n > 255 || output.len() != n {
        return Err(InvalidInput::Length);
    }
    finite(&settings.gain)?;
    finite(&[
        settings.near_distance_squared,
        settings.far_distance_squared,
        settings.prior_sample,
        settings.absolute_count_threshold,
        settings.relative_count_threshold,
    ])?;
    for (light, probability) in lights.iter().zip(output.iter()) {
        finite(&light.reference_gain)?;
        finite(&[probability.luma])?;
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
    let total_count: u64 = lights.iter().map(|l| l.white_points as u64).sum();
    let cutoff = settings.absolute_count_threshold as u32;
    let retained = |light: &Light<'_>| {
        total_count != 0
            && !((light.white_points as f32 / total_count as f32)
                <= settings.relative_count_threshold
                && light.white_points <= cutoff)
    };
    let retained_count: u64 = lights
        .iter()
        .filter(|l| retained(l))
        .map(|l| l.white_points as u64)
        .sum();
    let mut sum = 0.;
    for (light, probability) in lights.iter().zip(output.iter_mut()) {
        probability.white_points = if retained(light) {
            light.white_points as f32 / retained_count as f32
        } else {
            0.
        };
        sum += probability.white_points;
    }
    if (sum as f64) <= 0.00001 {
        for probability in output.iter_mut() {
            probability.white_points = uniform;
        }
    }

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

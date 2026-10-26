//! Recovered ClmExecute histogram exposure solver. Outer AE damping, routing,
//! exposure/gain splitting and sensor scheduling are separate unfinished stages.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
/// Exposure values are the native aggregate scalar, not shutter seconds.
/// Route/gain splitting and outer state/limits must be applied by the caller.
pub struct Input {
    pub target: f32,
    pub measured: f32,
    pub current_exposure: f32,
    pub tolerance_percent: f32,
    pub minimum_exposure: f32,
    pub maximum_exposure: f32,
    pub saturated: bool,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Decision {
    pub exposure: f32,
    pub saturated: bool,
}
pub fn solve(histogram: &[u32], input: Input) -> Result<Decision, InvalidInput> {
    let count = histogram.len();
    if !matches!(count, 64 | 256) {
        return Err(InvalidInput::Length);
    }
    let v = [
        input.target,
        input.measured,
        input.current_exposure,
        input.tolerance_percent,
        input.minimum_exposure,
        input.maximum_exposure,
    ];
    if v.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if input.target <= 0.
        || input.measured < 0.
        || input.current_exposure <= 0.
        || input.tolerance_percent < 0.
        || input.minimum_exposure < 0.
        || input.maximum_exposure < input.minimum_exposure
    {
        return Err(InvalidInput::Exposure);
    }
    if ((input.measured - input.target).abs() / input.target) <= input.tolerance_percent / 100. {
        return Ok(Decision {
            exposure: input.current_exposure,
            saturated: input.saturated,
        });
    }
    let mut work = [0u32; 768];
    let mut sum = 0u32;
    for i in 0..count - 1 {
        work[i] = histogram[i];
        sum = sum.wrapping_add(histogram[i]);
    }
    let previous = histogram[count - 2];
    let last = histogram[count - 1];
    let length;
    if previous < last {
        let maximum = 770 - count;
        let width = if previous == 0 {
            if sum == 0 {
                maximum
            } else {
                (last.wrapping_mul(2) as usize).min(maximum)
            }
        } else {
            ((last.wrapping_mul(2) / previous).wrapping_add(1) as usize).min(maximum)
        };
        if width < 2 {
            return Err(InvalidInput::DegenerateRange);
        }
        let step = last.wrapping_mul(2) / (width as u32);
        let mut running = step;
        for i in 0..width - 1 {
            let value = running / ((width - 1) as u32);
            work[count - 1 + i] = value;
            sum = sum.wrapping_add(value);
            running = running.wrapping_add(step);
        }
        length = count + width - 2;
    } else {
        work[count - 1] = last;
        length = count;
    }
    // The original denominator excludes the source last bin; it adds only the
    // replacement triangle's counts when extrapolating that bin.
    if sum == 0 {
        sum = 1;
    }
    let scale = 256. / count as f32;
    let maximum_center = count as f32 - 0.5;
    let mut mean = 0.;
    for (i, value) in work[..length].iter().enumerate() {
        let weight = (*value as f32 * scale) / (sum as f32);
        mean = libm::fmaf(weight, (i as f32 + 0.5).min(maximum_center), mean);
    }
    if mean <= 0. {
        mean = 1.;
    }
    let measured_ratio = ((input.measured.max(0.5) as f64) / (mean as f64)) as f32;
    let mut error = (input.target - mean).abs() / input.target;
    let mut exposure = input.current_exposure;
    for _ in 0..51 {
        if error <= 0.01 {
            break;
        }
        let factor = (measured_ratio * exposure) / input.current_exposure;
        let mut predicted = 0.;
        for (i, value) in work[..length].iter().enumerate() {
            let center = ((i as f32 + 0.5) * factor).min(maximum_center);
            let weight = (*value as f32 * scale) / (sum as f32);
            predicted = libm::fmaf(weight, center, predicted);
        }
        exposure = (input.target / predicted) * exposure;
        if exposure < input.minimum_exposure || exposure > input.maximum_exposure {
            break;
        }
        error = (input.target - predicted).abs() / input.target;
    }
    Ok(Decision {
        exposure: exposure.min(input.current_exposure * 40.),
        saturated: (sum as f64) * 0.95 < (last as f64),
    })
}
#[cfg(test)]
mod tests {
    use super::*;
    fn input() -> Input {
        Input {
            target: 128.,
            measured: 64.,
            current_exposure: 0.01,
            tolerance_percent: 10.,
            minimum_exposure: 0.0001,
            maximum_exposure: 100.,
            saturated: true,
        }
    }
    #[test]
    fn tolerance_preserves_exposure_and_previous_flag() {
        let mut v = input();
        v.measured = v.target;
        assert_eq!(
            solve(&[0; 256], v),
            Ok(Decision {
                exposure: v.current_exposure,
                saturated: true
            })
        );
    }
    #[test]
    fn dark_histogram_obeys_native_relative_growth_cap() {
        let v = input();
        assert_eq!(
            solve(&[0; 256], v).unwrap().exposure,
            v.current_exposure * 40.
        );
    }
    #[test]
    fn rejects_invalid_active_inputs() {
        let mut v = input();
        v.target = 0.;
        assert!(solve(&[0; 256], v).is_err());
        assert!(solve(&[0; 10], input()).is_err());
    }
    #[test]
    fn native_bound_is_a_stop_condition_not_a_clamp() {
        let mut v = input();
        v.measured = 1.;
        v.maximum_exposure = 0.02;
        let mut histogram = [0; 256];
        histogram[0] = 1000;
        let result = solve(&histogram, v).unwrap();
        assert!(result.exposure > v.maximum_exposure);
        assert_eq!(result.exposure, v.current_exposure * 40.);
    }
}

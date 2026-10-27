//! Non-iris linear EcmExecuteAuto (ELF 0xb5bcc) and EcmExecuteBrief2
//! (0xb57a4). Limit selection and the outer cached EcmExecute are separate.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Point {
    pub time: f32,
    pub gain: f32,
    pub isp_gain: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct Limits {
    pub minimum_time: f32,
    pub maximum_time: f32,
    pub minimum_gain: f32,
    pub maximum_gain: f32,
    pub time_quantum: f32,
    /// Native context 0x680: maximum-register factor[1] (8 for pinned SC3336).
    pub floor_tolerance_coefficient: f32,
    pub line_length: f32,
    pub pixel_clock_mhz: f32,
}
fn quantize(time: f32, gain: f32, upper_time: f32, maximum_gain: f32, quantum: f32) -> (f32, f32) {
    if time <= quantum {
        return (time, gain);
    }
    let ratio = time / quantum;
    let conserved = gain * time;
    let mut selected = (quantum * libm::roundf(ratio)).min(upper_time);
    let mut adjusted = conserved / selected;
    if adjusted < gain {
        selected = quantum * libm::floorf(ratio);
        adjusted = conserved / selected;
        if adjusted > maximum_gain {
            return (time, gain);
        }
    } else if adjusted > maximum_gain {
        selected = quantum * libm::ceilf(ratio);
        adjusted = conserved / selected;
        if adjusted < gain {
            return (time, gain);
        }
    }
    (selected, adjusted)
}
fn segment(route: &[Point], index: usize, exposure: f32, quantum: f32) -> Point {
    let previous = route[index - 1];
    let next = route[index];
    let mut out = next;
    if previous.time == next.time {
        if previous.gain == next.gain {
            out.isp_gain = exposure / (next.time * next.gain);
        } else if previous.isp_gain == next.isp_gain {
            out.gain = exposure / (next.time * next.isp_gain);
        } else {
            out.gain = next.gain.min(exposure / next.time);
            out.isp_gain = exposure / (next.time * out.gain);
            if out.isp_gain < previous.isp_gain {
                out.gain = exposure / (next.time * previous.isp_gain);
                out.isp_gain = previous.isp_gain;
            }
        }
    } else if previous.gain != next.gain {
        out.gain = previous.gain;
        out.time = exposure / (out.gain * out.isp_gain);
        (out.time, out.gain) = quantize(
            out.time,
            out.gain,
            next.time,
            route.last().unwrap().gain,
            quantum,
        );
    } else {
        out.isp_gain = previous.isp_gain;
        out.time = exposure / (out.isp_gain * out.gain);
        (out.time, out.isp_gain) = quantize(
            out.time,
            out.isp_gain,
            next.time,
            route.last().unwrap().isp_gain,
            quantum,
        );
    }
    out.isp_gain = out
        .isp_gain
        .clamp(route[0].isp_gain, route.last().unwrap().isp_gain);
    out
}
/// The native routine adjusts route time knots in-place before selecting the
/// first knot whose total exposure is strictly greater than the request.
/// The checked domain excludes iris and intervals changing all three variables,
/// which the original interpolation helper rejects. Runtime limits are explicit.
pub fn split(route: &mut [Point], exposure: f32, limits: Limits) -> Result<Point, InvalidInput> {
    if route.is_empty() || route.len() > 64 {
        return Err(InvalidInput::Length);
    }
    let cfg = [
        limits.minimum_time,
        limits.maximum_time,
        limits.minimum_gain,
        limits.maximum_gain,
        limits.time_quantum,
        limits.floor_tolerance_coefficient,
        limits.line_length,
        limits.pixel_clock_mhz,
    ];
    if !exposure.is_finite()
        || cfg.iter().any(|v| !v.is_finite())
        || route
            .iter()
            .any(|p| ![p.time, p.gain, p.isp_gain].iter().all(|v| v.is_finite()))
    {
        return Err(InvalidInput::NonFinite);
    }
    if exposure < 0.
        || limits.minimum_time <= 0.
        || limits.maximum_time < limits.minimum_time
        || limits.minimum_gain <= 0.
        || limits.maximum_gain < limits.minimum_gain
        || limits.time_quantum <= 0.
        || limits.floor_tolerance_coefficient < 0.
        || limits.line_length <= 0.
        || limits.pixel_clock_mhz <= 0.
        || route
            .iter()
            .any(|p| p.time < 0. || p.gain <= 0. || p.isp_gain <= 0.)
        || route[0].isp_gain > route.last().unwrap().isp_gain
    {
        return Err(InvalidInput::Exposure);
    }
    if route
        .windows(2)
        .any(|w| w[0].time != w[1].time && w[0].gain != w[1].gain && w[0].isp_gain != w[1].isp_gain)
    {
        return Err(InvalidInput::DegenerateRange);
    }
    let tolerance = ((limits.floor_tolerance_coefficient as f64 * 1.5) * limits.line_length as f64)
        / (limits.pixel_clock_mhz * 1_000_000.) as f64;
    for point in route.iter_mut() {
        if point.time > limits.time_quantum {
            let ratio = point.time / limits.time_quantum;
            let residual = libm::fmaf(limits.time_quantum, libm::ceilf(ratio), -point.time);
            if residual as f64 >= tolerance {
                point.time = limits.time_quantum * libm::floorf(ratio);
            }
        }
    }
    let index = route
        .iter()
        .position(|p| (p.time * p.gain) * p.isp_gain > exposure)
        .unwrap_or(route.len());
    let mut out = if index == 0 || index == route.len() {
        route[if index == route.len() { index - 1 } else { 0 }]
    } else {
        segment(route, index, exposure, limits.time_quantum)
    };
    if out.gain < limits.minimum_gain {
        out.gain = limits.minimum_gain;
        out.time = exposure / out.gain;
    } else if out.gain > limits.maximum_gain {
        out.isp_gain = (out.gain / limits.maximum_gain).min(route.last().unwrap().isp_gain);
        out.gain = limits.maximum_gain;
        out.time = exposure / (out.gain * out.isp_gain);
    }
    out.time = out.time.clamp(limits.minimum_time, limits.maximum_time);
    Ok(out)
}

/// Non-iris successful-path EcmExecute (ELF 0xb65cc) cache state.
#[derive(Clone, Copy, Debug)]
pub struct Cache {
    pub exposure: f32,
    pub relative_threshold: f32,
    pub force: bool,
    pub point: Point,
}
/// Run automatic route splitting only when the native relative-change test or
/// force flag requires it. Manual/iris modes and native error-state publication
/// are outside this checked successful-path API.
pub fn split_cached(
    route: &mut [Point],
    exposure: f32,
    limits: Limits,
    cache: &mut Cache,
) -> Result<Point, InvalidInput> {
    if !exposure.is_finite()
        || !cache.exposure.is_finite()
        || !cache.relative_threshold.is_finite()
        || [cache.point.time, cache.point.gain, cache.point.isp_gain]
            .iter()
            .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if exposure < 0. || cache.exposure < 0. || cache.relative_threshold < 0. {
        return Err(InvalidInput::Exposure);
    }
    let difference = if exposure < cache.exposure {
        cache.exposure - exposure
    } else {
        exposure - cache.exposure
    };
    // Native unordered comparison also recomputes: zero/zero must not take
    // the cache-hit path. Keep the negated strict comparison.
    if !(difference / cache.exposure < cache.relative_threshold) || cache.force {
        let point = split(route, exposure, limits)?;
        cache.exposure = exposure;
        cache.point = point;
        cache.force = false;
    }
    Ok(cache.point)
}

#[cfg(feature = "diagnostics")]
pub fn from_profile(
    value: &serde_json::Value,
) -> Result<alloc::vec::Vec<Point>, alloc::string::String> {
    extern crate alloc;
    use alloc::{string::String, vec::Vec};
    let array = |name: &str| -> Result<Vec<f32>, String> {
        let entries = value[name].as_array().ok_or("Missing AE route array")?;
        if value[alloc::format!("{name}_len")].as_u64() != Some(entries.len() as u64)
            || entries.is_empty()
            || entries.len() > 64
        {
            return Err("Invalid AE route array length".into());
        }
        entries
            .iter()
            .map(|v| {
                v.as_f64()
                    .map(|v| v as f32)
                    .filter(|v| v.is_finite())
                    .ok_or("Invalid AE route value".into())
            })
            .collect()
    };
    let times = array("TimeDot")?;
    let gains = array("GainDot")?;
    let isp = array("IspDGainDot")?;
    if times.len() != gains.len() || times.len() != isp.len() {
        return Err("AE route arrays have different lengths".into());
    }
    Ok((0..times.len())
        .map(|i| Point {
            time: times[i],
            gain: gains[i],
            isp_gain: isp[i],
        })
        .collect())
}
#[cfg(feature = "diagnostics")]
extern crate alloc;
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_requests_are_rejected_before_time_knot_mutation() {
        let mut route = [
            Point {
                time: 0.0199,
                gain: 1.,
                isp_gain: 1.,
            },
            Point {
                time: 0.03,
                gain: 2.,
                isp_gain: 2.,
            },
        ];
        let limits = Limits {
            minimum_time: 0.0001,
            maximum_time: 0.03,
            minimum_gain: 1.,
            maximum_gain: 16.,
            time_quantum: 0.01,
            floor_tolerance_coefficient: 1.,
            line_length: 2500.,
            pixel_clock_mhz: 72.,
        };
        assert!(split(&mut route, -1., limits).is_err());
        assert_eq!(route[0].time, 0.0199);
        assert!(split(&mut route, 0.1, limits).is_err());
        assert_eq!(route[0].time, 0.0199);
    }
}

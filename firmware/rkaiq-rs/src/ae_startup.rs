//! Ordinary linear, non-iris/DCG-disabled AecInitEcm startup (ELF 0xafe0c).
//! Fresh preparation only (update mask zero); no sensor or ISP writes.
use crate::{ae_register, ae_route, exposure::Calibration, InvalidInput};

#[derive(Clone, Copy, Debug)]
pub struct History {
    /// Native startup history excludes ISP gain from this product.
    pub aggregate: f32,
    pub iris_gain: i32,
    pub iris_step: i32,
    pub isp_gain: f32,
    pub gain: f32,
    pub seconds: f32,
    pub dcg: i32,
    pub time_code: u32,
    pub gain_code: u32,
}
impl History {
    const ZERO: Self = Self {
        aggregate: 0.,
        iris_gain: 0,
        iris_step: 0,
        isp_gain: 0.,
        gain: 0.,
        seconds: 0.,
        dcg: 0,
        time_code: 0,
        gain_code: 0,
    };
}
#[derive(Clone, Copy, Debug)]
pub struct Output {
    /// Retained before register conversion, including requested ISP gain.
    pub requested_aggregate: f32,
    pub held_aggregate: f32,
    pub current: ae_register::Output,
    pub intermediate_count: usize,
    pub history: [History; 5],
}
/// Construct fresh smoothing history. Existing history and reprepare mask 8
/// require a different entry path and must not be passed through this API.
pub fn linear(
    requested: ae_route::Point,
    count: usize,
    iris: [i32; 2],
    calibration: Calibration<'_>,
    policy: ae_register::Policy,
) -> Result<Output, InvalidInput> {
    if count > 5 {
        return Err(InvalidInput::Length);
    }
    let aggregate = (requested.gain * requested.time) * requested.isp_gain;
    if !aggregate.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let current = ae_register::linear(
        requested.time,
        requested.gain,
        requested.isp_gain,
        -1,
        calibration,
        policy,
    )?;
    let mut history = [History::ZERO; 5];
    for entry in history.iter_mut().take(count) {
        *entry = History {
            aggregate: current.gain * current.seconds,
            iris_gain: iris[0],
            iris_step: iris[1],
            isp_gain: current.isp_gain,
            gain: current.gain,
            seconds: current.seconds,
            dcg: -1,
            time_code: current.codes.integration_time,
            gain_code: current.codes.gain,
        };
    }
    Ok(Output {
        requested_aggregate: aggregate,
        held_aggregate: aggregate,
        current,
        intermediate_count: count,
        history,
    })
}

#[cfg(feature = "diagnostics")]
pub mod profile {
    extern crate alloc;
    use super::*;
    use crate::{
        ae_flicker, ae_fps, ae_gain_limits, ae_shutter, ae_smoothing,
        calibration::{RuntimeTiming, SensorCalibration},
    };
    use alloc::{format, string::String, vec::Vec};
    use serde_json::Value;
    #[derive(Clone, Copy, Debug)]
    pub struct Prepared {
        pub startup: Output,
        pub timing: RuntimeTiming,
        pub fps: f32,
        pub register_policy: ae_register::Policy,
    }
    fn number(v: &Value, key: &str) -> Result<f32, String> {
        let n = v[key]
            .as_f64()
            .ok_or_else(|| format!("Missing number {key}"))? as f32;
        if !n.is_finite() {
            return Err(format!("Nonfinite {key}"));
        }
        Ok(n)
    }
    fn flag(v: &Value) -> Result<bool, String> {
        match (v.as_bool(), v.as_u64()) {
            (Some(b), _) => Ok(b),
            (_, Some(0)) => Ok(false),
            (_, Some(1)) => Ok(true),
            _ => Err("Invalid boolean".into()),
        }
    }
    /// Fresh ordinary auto/linear preparation using profile timing and route
    /// endpoints. Runtime geometry is configured separately. HDR, iris, DCG,
    /// overrides and variable-rate preparation are not admitted by this binder.
    pub fn linear(profile: &Value, timing: RuntimeTiming) -> Result<Prepared, String> {
        let sensor = SensorCalibration::from_value(profile)?;
        let scene = profile
            .pointer("/main_scene/0/sub_scene/0/scene_isp32")
            .ok_or("Missing linear scene")?;
        let sensor_json = &profile["sensor_calib"];
        let ae = &scene["ae_calib"];
        if sensor.linear_dcg_supported
            || ae["CommCtrl"]["AecOpType"].as_str() != Some("RK_AIQ_OP_MODE_AUTO")
            || flag(&ae["IrisCtrl"]["Enable"])?
        {
            return Err("Startup requires ordinary auto mode with iris/DCG disabled".into());
        }
        if !flag(&ae["CommCtrl"]["AecFrameRateMode"]["isFpsFix"])? {
            return Err("Variable-rate startup is not qualified".into());
        }
        let baseline = ae_fps::refresh_baseline(
            0,
            timing.frame_length as f32,
            timing.line_length_pixels as f32,
            timing.pixel_clock_mhz,
        )
        .map_err(|e| format!("{e:?}"))?
        .ok_or("Missing baseline")?;
        let mut state = ae_fps::State {
            baseline_frame: baseline.frame,
            baseline_fps: baseline.fps,
            variable_frame: 0.,
            fixed_rate: 0.,
            variable_rate: 0.,
        };
        // The minimum FPS is supplied by the sensor record, not inferred from timing.
        let fps = ae_fps::Calibration::from_scene(scene)?
            .select(
                &mut state,
                baseline.frame,
                baseline.line,
                baseline.clock_mhz,
                number(sensor_json, "CISMinFps")?,
            )
            .map_err(|e| format!("{e:?}"))?;
        let active = RuntimeTiming {
            frame_length: fps.frame as u32,
            ..timing
        };
        let flicker = &ae["CommCtrl"]["AecAntiFlicker"];
        let enabled = flag(&flicker["enable"])?;
        let frequency = match flicker["Frequency"].as_str() {
            Some("AECV2_FLICKER_FREQUENCY_OFF") => 0,
            Some("AECV2_FLICKER_FREQUENCY_50HZ") => 1,
            Some("AECV2_FLICKER_FREQUENCY_60HZ") => 2,
            Some("AECV2_FLICKER_FREQUENCY_AUTO") => 3,
            _ => return Err("Unsupported flicker frequency".into()),
        };
        let strict = match flicker["Mode"].as_str() {
            Some("AECV2_ANTIFLICKER_AUTO_MODE") => false,
            Some("AECV2_ANTIFLICKER_NORMAL_MODE") => true,
            _ => return Err("Unsupported flicker mode".into()),
        };
        let quantum = ae_flicker::select(
            ae_flicker::State {
                quantum: 0.,
                alternate: 0.,
                frequency_selector: 0,
            },
            enabled,
            frequency,
            0.,
            Some(ae_flicker::LineTiming {
                line_length: baseline.line,
                pixel_clock_mhz: baseline.clock_mhz,
                coefficient: sensor.factors[2],
            }),
        )
        .map_err(|e| format!("{e:?}"))?
        .quantum;
        let route = &ae["LinearAeCtrl"]["Route"];
        let times = route["TimeDot"].as_array().ok_or("Missing route")?;
        if times.len() < 2 {
            return Err("Startup route needs at least two points".into());
        }
        let mut points = Vec::new();
        for i in 0..times.len() {
            let at = |k: &str| {
                route[k][i]
                    .as_f64()
                    .map(|n| n as f32)
                    .ok_or_else(|| format!("Invalid route {k}[{i}]"))
            };
            points.push(ae_route::Point {
                time: at("TimeDot")?,
                gain: at("GainDot")?,
                isp_gain: at("IspDGainDot")?,
            });
        }
        let shutter = ae_shutter::from_calibration(
            &sensor,
            active,
            &points,
            None,
            enabled.then_some((quantum, strict)),
        )
        .map_err(|e| format!("{e:?}"))?;
        let gains = ae_gain_limits::linear(ae_gain_limits::Input {
            analogue: sensor.analogue_range,
            digital: sensor.digital_range,
            isp: sensor.isp_gain_range,
            route_gain: [points[0].gain, points[points.len() - 1].gain],
            route_isp: [points[0].isp_gain, points[points.len() - 1].isp_gain],
            overrides: None,
        })
        .map_err(|e| format!("{e:?}"))?;
        let policy = ae_register::Policy {
            isp_range: sensor.isp_gain_range,
            time_range: [shutter.minimum, shutter.maximum],
            gain_range: gains.gain,
            analogue_minimum: sensor.analogue_range[0],
            time_quantum: quantum,
            flicker_enabled: enabled,
            automatic: true,
            suppress_isp_compensation: false,
        };
        let init = &ae["LinearAeCtrl"]["InitExp"];
        let initial_gain = number(init, "InitGainValue")?;
        if initial_gain <= 0. {
            return Err("Initial gain must be positive".into());
        }
        let requested = ae_route::Point {
            time: number(init, "InitTimeValue")?.clamp(shutter.minimum, shutter.maximum),
            gain: initial_gain.clamp(gains.gain[0], gains.gain[1]),
            // Native fresh auto configuration forces unity here, despite the
            // InitIspDGainValue field present in the SDK profile.
            isp_gain: 1.,
        };
        let count = ae_smoothing::from_profile(scene, sensor_json)?.linear as usize;
        // Configuration preserves the PIris seed even when iris control is off.
        let iris = &ae["IrisCtrl"];
        let table = &iris["PIrisAttr"]["StepTable"];
        let step = |index: usize| -> Result<i32, String> {
            table[index]
                .as_i64()
                .filter(|n| (0..=u16::MAX as i64).contains(n))
                .map(|n| n as i32)
                .ok_or("Invalid iris table entry".into())
        };
        let index = |key: &str| -> Result<usize, String> {
            iris["PIrisAttr"][key]
                .as_u64()
                .filter(|n| *n > 0 && *n <= table.as_array().map_or(0, |v| v.len()) as u64)
                .map(|n| n as usize - 1)
                .ok_or("Invalid iris table index".into())
        };
        let maximum = step(0)?;
        let total = step(index("TotalStep")?)?;
        let minimum = step(index("EffcStep")?)?.max(total);
        let mut iris_gain = if flag(&iris["PIrisAttr"]["ZeroIsMax"])? {
            maximum
        } else {
            total
        };
        let requested_iris = iris["InitAttr"]["PIrisGainValue"]
            .as_i64()
            .filter(|n| i32::try_from(*n).is_ok())
            .ok_or("Invalid initial iris gain")? as i32;
        if requested_iris != 0 {
            iris_gain = requested_iris;
        }
        if iris_gain < minimum || iris_gain > maximum {
            iris_gain = maximum;
        }
        // The native configuration quantizes this metadata even with iris off.
        let total_count = index("TotalStep")? + 1;
        let (mut lower, mut upper, mut middle) = (0, total_count - 1, 0);
        let mut selected = None;
        for _ in 0..=total_count {
            if lower >= upper || step(middle)? == iris_gain {
                selected = Some(middle);
                break;
            }
            middle = (lower + upper) / 2;
            if iris_gain < step(middle + 1)? {
                lower = middle;
                continue;
            }
            if iris_gain > step(middle)? {
                upper = middle;
                continue;
            }
            if iris_gain * 2 < step(middle)? + step(middle + 1)? {
                middle += 1;
            }
            selected = Some(middle);
            break;
        }
        let selected = selected.ok_or("Iris seed search did not converge")?;
        // Configuration computes the table index into a stack temporary. With
        // iris disabled it does not store that index in context +0x2024, which
        // remains calloc-zero and is what startup copies into history.
        let iris = [step(selected)?, 0];
        let startup = super::linear(requested, count, iris, sensor.conversion(active), policy)
            .map_err(|e| format!("{e:?}"))?;
        Ok(Prepared {
            startup,
            timing: active,
            fps: fps.fps,
            register_policy: policy,
        })
    }
}

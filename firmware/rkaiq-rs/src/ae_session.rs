//! Profile-bound fresh ordinary linear AE session. Associated exposure records
//! and translated statistics are inputs; no sensor/ISP programming is performed.
extern crate alloc;
use crate::{
    ae_configuration, ae_controller, ae_convergence, ae_decision, ae_delay_calibration,
    ae_dynamic_calibration, ae_frame, ae_pipeline, ae_policy, ae_preprocess, ae_publication,
    ae_route, ae_startup,
    calibration::{RuntimeTiming, SensorCalibration},
};
use alloc::{format, string::String, vec::Vec};
use serde_json::Value;

pub struct Session {
    pub state: ae_pipeline::State,
    pub preprocessing: ae_preprocess::Standard,
    pub route: Vec<ae_route::Point>,
    pub prepared: ae_startup::profile::Prepared,
    result_buffer: [ae_publication::Record; 6],
    sensor: SensorCalibration,
    policy: ae_policy::Calibration,
    dynamic: ae_dynamic_calibration::Calibration,
    delays: [u8; 2],
    levels: Vec<f32>,
    targets: Vec<f32>,
    bias: f32,
    limits: ae_route::Limits,
    bounds: [f32; 2],
}
fn number(v: &Value, key: &str) -> Result<f32, String> {
    v[key]
        .as_f64()
        .map(|v| v as f32)
        .filter(|v| v.is_finite())
        .ok_or_else(|| format!("Invalid number {key}"))
}
fn array(v: &Value, key: &str) -> Result<Vec<f32>, String> {
    let a = v[key]
        .as_array()
        .ok_or_else(|| format!("Missing array {key}"))?;
    if v[format!("{key}_len")].as_u64() != Some(a.len() as u64) {
        return Err(format!("Invalid length {key}"));
    }
    a.iter()
        .map(|n| {
            n.as_f64()
                .map(|v| v as f32)
                .filter(|v| v.is_finite())
                .ok_or("Nonfinite array value".into())
        })
        .collect()
}
impl Session {
    pub(crate) fn sensor_update_delays(&self) -> [u32; 3] {
        self.sensor.linear_update_delays
    }

    pub fn from_profile(
        profile: &Value,
        timing: RuntimeTiming,
        width: u32,
        height: u32,
    ) -> Result<Self, String> {
        let scene = profile
            .pointer("/main_scene/0/sub_scene/0/scene_isp32")
            .ok_or("Missing scene")?;
        let ae = &scene["ae_calib"];
        let comm = &ae["CommCtrl"];
        let linear = &ae["LinearAeCtrl"];
        for v in [
            &linear["BackLightCtrl"]["Enable"],
            &linear["OverExpCtrl"]["Enable"],
            &comm["AecEnvLvCalib"]["Enable"],
        ] {
            if v.as_u64() != Some(0) && v.as_bool() != Some(false) {
                return Err("Optional raw/luma/lux preprocessing is not yet supported".into());
            }
        }
        if linear["RawStatsEn"].as_u64() != Some(1) && linear["RawStatsEn"].as_bool() != Some(true)
        {
            return Err("Session requires the translated raw-statistics mean".into());
        }
        if comm["AecRunInterval"].as_u64() != Some(0) {
            return Err("Nonzero algorithm run intervals remain unported".into());
        }
        if (comm["AecAntiFlicker"]["enable"].as_u64() == Some(1)
            || comm["AecAntiFlicker"]["enable"].as_bool() == Some(true))
            && comm["AecAntiFlicker"]["Frequency"].as_str() == Some("AECV2_FLICKER_FREQUENCY_AUTO")
        {
            return Err("Automatic flicker estimator remains unported".into());
        }
        let prepared = ae_startup::profile::linear(profile, timing)?;
        let sensor = SensorCalibration::from_value(profile)?;
        let p = prepared.register_policy;
        let source = &linear["Route"];
        let times = array(source, "TimeDot")?;
        let gains = array(source, "GainDot")?;
        let isp = array(source, "IspDGainDot")?;
        if times.len() != gains.len() || times.len() != isp.len() {
            return Err("Mismatched route lengths".into());
        }
        let route = times
            .iter()
            .zip(&gains)
            .zip(&isp)
            .map(|((&t, &g), &i)| ae_route::Point {
                time: t.clamp(p.time_range[0], p.time_range[1]),
                gain: g.clamp(p.gain_range[0], p.gain_range[1]),
                isp_gain: i.clamp(sensor.isp_gain_range[0], sensor.isp_gain_range[1]),
            })
            .collect::<Vec<_>>();
        let (measurement, _) = ae_configuration::from_comm(comm, width, height)?;
        let state = ae_startup::publish_initial(
            prepared.startup,
            ae_publication::Timing {
                frame_length: prepared.timing.frame_length,
                line_length: prepared.timing.line_length_pixels as u16,
                pixel_clock_mhz: prepared.timing.pixel_clock_mhz,
            },
            &measurement,
        )
        .map_err(|e| format!("{e:?}"))?;
        let targets = &linear["DySetpoint"];
        let levels = array(targets, "ExpLevel")?;
        let points = array(targets, "DySetpoint")?;
        let minimum_isp = route.first().ok_or("Empty route")?.isp_gain;
        let maximum_isp = route.last().ok_or("Empty route")?.isp_gain;
        let bounds = [
            (p.time_range[0] * p.gain_range[0]) * minimum_isp,
            (p.time_range[1] * p.gain_range[1]) * maximum_isp,
        ];
        let limits = ae_route::Limits {
            minimum_time: p.time_range[0],
            maximum_time: p.time_range[1],
            minimum_gain: p.gain_range[0],
            maximum_gain: p.gain_range[1],
            time_quantum: p.time_quantum,
            floor_tolerance_coefficient: sensor.linear_max_factors[1],
            line_length: prepared.timing.line_length_pixels as f32,
            pixel_clock_mhz: prepared.timing.pixel_clock_mhz,
        };
        Ok(Self {
            result_buffer: state.publication.published,
            state,
            preprocessing: Default::default(),
            route,
            prepared,
            sensor,
            policy: ae_policy::Calibration::from_scene(scene)?,
            dynamic: ae_dynamic_calibration::Calibration::from_scene(scene)?,
            delays: ae_delay_calibration::Calibration::from_scene(scene)?
                .counts(
                    prepared.timing.frame_length as f32,
                    prepared.timing.line_length_pixels as f32,
                    prepared.timing.pixel_clock_mhz,
                )
                .map_err(|e| format!("{e:?}"))?,
            levels,
            targets: points,
            bias: number(linear, "Evbias")?,
            limits,
            bounds,
        })
    }
    /// Exposure must already be associated with this frame's statistics.
    /// Discard the session after an error; updates are not transactional.
    pub fn step(
        &mut self,
        frame: i32,
        q8: [u16; 4],
        histogram: &[u32],
        effective: ae_publication::Record,
    ) -> Result<ae_pipeline::Output, String> {
        let line = u16::from_le_bytes(effective[228..230].try_into().unwrap()) as u32;
        let frame_length = u32::from_le_bytes(effective[232..236].try_into().unwrap());
        let clock = u32::from_le_bytes(effective[236..240].try_into().unwrap());
        // Native publication may leave cached line length / clock zero. AE
        // retains its prepare-time timing; only nonzero conflicts are rejected.
        if (line != 0 && line != self.prepared.timing.line_length_pixels)
            || frame_length != self.prepared.timing.frame_length
            || (clock != 0 && clock != self.prepared.timing.pixel_clock_mhz.to_bits())
        {
            return Err("Incomplete or changed exposure timing; reconfigure the session".into());
        }
        let q = [q8[0], q8[1], q8[2]];
        let run = ae_frame::should_run(
            &self.state.frame,
            &self.state.runtime,
            &self.state.controller,
            q,
        )
        .map_err(|e| format!("{e:?}"))?;
        let aggregate = self
            .preprocessing
            .update(
                frame,
                effective,
                q8,
                run,
                self.bounds,
                self.state.controller.cache.relative_threshold,
            )
            .map_err(|e| format!("{e:?}"))?;
        let selected = self
            .policy
            .select(
                self.state.frame.convergence.gating_enabled != 0,
                self.preprocessing.alternate_damping,
            )
            .map_err(|e| format!("{e:?}"))?;
        let word = |o| u32::from_le_bytes(effective[o..o + 4].try_into().unwrap());
        let dynamic = self.dynamic.dynamic(
            self.state.frame.convergence.dynamic_enabled != 0,
            self.state.frame.error_history,
        );
        let mut output = ae_pipeline::linear(
            &mut self.state,
            &mut self.route,
            histogram,
            ae_decision::Input {
                target: 1.,
                measured: self.preprocessing.measured,
                current_exposure: aggregate,
                tolerance_percent: selected.tolerance_percent,
                minimum_exposure: self.bounds[0],
                maximum_exposure: self.bounds[1],
                saturated: false,
            },
            ae_controller::Policy {
                dynamic,
                damping_under: selected.damping_under,
                damping_over: selected.damping_over,
                fps: self.prepared.fps,
                delay_enabled: false,
                same_mode: true,
                negative_delay: self.delays[0],
                positive_delay: self.delays[1],
            },
            self.limits,
            ae_frame::Target {
                levels: &self.levels,
                points: &self.targets,
                bias_percent: self.bias,
            },
            self.sensor.conversion(self.prepared.timing),
            self.prepared.register_policy,
            frame,
            q,
            [0.; 3],
            ae_convergence::Exposure {
                time_code: word(32),
                gain_code: word(36),
                isp_gain: f32::from_bits(word(12)),
            },
            self.prepared.startup.intermediate_count,
        )
        .map_err(|e| format!("{e:?}"))?;
        // Native GetProcResults overwrites only max(count,1) caller records;
        // a persistent SDK output buffer retains the unused tail across calls.
        let written = output.publication.count.max(1);
        self.result_buffer[..written].copy_from_slice(&output.publication.records[..written]);
        output.publication.records = self.result_buffer;
        if self.state.publication.synchronized_frame == frame {
            self.state.publication.published = self.result_buffer;
        }
        // The empty-reference region overlaps the live convergence/limit flags
        // in the native context; selection reads only its exposure-key prefix.
        self.state.publication.empty_reference[240..244].copy_from_slice(&[
            self.state.frame.convergence.dynamic_enabled,
            self.state.frame.convergence.gating_enabled,
            self.preprocessing.near_maximum as u8,
            self.preprocessing.near_minimum as u8,
        ]);
        Ok(output)
    }
}

/// Caller-owned complete parameter state identified by the driver's params ID.
/// Partial ISP update buffers must be accumulated before being supplied here.
pub struct ParameterSnapshot<'a> {
    pub id: u32,
    pub bytes: &'a [u8; crate::isp32::PARAMETER_BYTES],
}
pub struct StatisticsOutput {
    pub frame: u32,
    pub parameters: u32,
    pub exposure_frame: u32,
    pub exact_exposure: bool,
    pub mean_q8: u16,
    pub control: ae_pipeline::Output,
}
impl Session {
    /// Join raw ISP32 translation, explicit snapshot IDs and native effective-
    /// exposure lookup. The supplied map reports scheduling state, not measured
    /// physical application. Missing measurements leave the session untouched.
    pub fn step_statistics(
        &mut self,
        bytes: &[u8],
        parameters: &[ParameterSnapshot<'_>],
        effective: &[crate::sensor_scheduler::Entry<ae_publication::Record>],
    ) -> Result<Option<StatisticsOutput>, String> {
        let stats = crate::statistics::Statistics::parse(bytes)
            .map_err(|_| String::from("Invalid ISP32 statistics length"))?;
        let frame = stats.frame_id();
        let parameter_id = stats.parameters_id();
        if stats.measurements() & ((1 << 8) | (1 << 12)) != ((1 << 8) | (1 << 12)) {
            return Ok(None);
        }
        if frame > i32::MAX as u32 - 9 {
            return Err("Frame ID outside qualified AE history range".into());
        }
        if parameters.windows(2).any(|v| v[0].id >= v[1].id) {
            return Err("Parameter snapshots must have unique increasing IDs".into());
        }
        let p = parameters
            .binary_search_by_key(&parameter_id, |p| p.id)
            .ok()
            .map(|i| parameters[i].bytes)
            .ok_or_else(|| format!("Missing parameter snapshot {parameter_id}"))?;
        let frames = effective.iter().map(|v| v.frame).collect::<Vec<_>>();
        let selected = crate::exposure_association::effective_index(&frames, frame)
            .map_err(|e| format!("Effective exposure map: {e:?}"))?
            .ok_or("No effective exposure records")?;
        let record = effective[selected.index];
        let m = crate::ae_translation::measure_linear(bytes, p)
            .map_err(|e| format!("AE translation: {e:?}"))?
            .ok_or("Missing primary AE measurements")?;
        // This qualified source routing produces only channel zero. Optional
        // channels are not synthesized from an uncorrected raw mean.
        let control = self.step(
            frame as i32,
            [m.mean, 0, 0, 0],
            &m.histogram,
            record.exposure,
        )?;
        Ok(Some(StatisticsOutput {
            frame,
            parameters: parameter_id,
            exposure_frame: record.frame,
            exact_exposure: selected.exact,
            mean_q8: m.mean,
            control,
        }))
    }
}

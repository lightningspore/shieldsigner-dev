//! Owned experimental FAST/normal linear AWB session. No devices or publication here.
//! Complete state is staged so rejected statistics cannot advance histories.
extern crate alloc;
use crate::{
    awb_calibration::{GainRuntime, MeasurementExclusions, MeasurementGeometry, Scene},
    awb_gain_controller::LightResult,
    awb_gain_frame,
    awb_preparation::{
        self, LightRecord, ModeName, State as Measurements, FRAME_BYTES, LIGHT_BYTES, REGION_BYTES,
    },
    awb_preprocess, awb_probability, awb_site, InvalidInput,
};
use alloc::{format, string::String, vec, vec::Vec};
use serde_json::Value;

/// The original single-camera create_context (ELF 0xbd5f4) writes 1 to
/// context +0x369c; its camera-group creator uses a separate configured value.
pub const SINGLE_CAMERA_SAMPLE_SCALE: u32 = 1;

#[derive(Clone)]
struct Header {
    update: bool,
    stability_mask: u8,
    history: [[f32; 4]; 4],
    mode_names: [ModeName; 4],
    active_lights: u8,
    complete: bool,
    previous_pre_gain: [f32; 4],
    grid_valid: bool,
    second_grid_valid: bool,
    exclusions_valid: bool,
    exclusions: [[u8; REGION_BYTES]; 7],
    exclusion_aggregate: [u8; REGION_BYTES],
    histogram_cache: [[u32; 8]; 4],
    histogram_aggregate: [u32; 8],
}
impl Header {
    fn read(s: &Measurements<'_>) -> Self {
        Self {
            update: s.update,
            stability_mask: s.stability_mask,
            history: s.history,
            mode_names: s.mode_names,
            active_lights: s.active_lights,
            complete: s.complete,
            previous_pre_gain: s.previous_pre_gain,
            grid_valid: s.grid_valid,
            second_grid_valid: s.second_grid_valid,
            exclusions_valid: s.exclusions_valid,
            exclusions: s.exclusions,
            exclusion_aggregate: s.exclusion_aggregate,
            histogram_cache: s.histogram_cache,
            histogram_aggregate: s.histogram_aggregate,
        }
    }
}
#[derive(Clone)]
struct Cache {
    header: Header,
    seen: Vec<u8>,
    lights: Vec<LightRecord>,
    second_counts: Vec<u32>,
    total_counts: Vec<u32>,
    grid: [[f32; 3]; 225],
}
impl Cache {
    fn fresh(n: usize) -> Result<Self, InvalidInput> {
        let mut seen = vec![0; n];
        let mut lights = vec![LightRecord([0; LIGHT_BYTES]); n];
        let mut second_counts = vec![0; n];
        let mut total_counts = vec![0; n.max(2)];
        let mut grid = [[0.; 3]; 225];
        let header = Header::read(&Measurements::fresh(
            &mut seen,
            &mut lights,
            &mut second_counts,
            &mut total_counts,
            &mut grid,
            n,
        )?);
        Ok(Self {
            header,
            seen,
            lights,
            second_counts,
            total_counts,
            grid,
        })
    }
    fn with_mut<R>(
        &mut self,
        run: impl FnOnce(&mut Measurements<'_>) -> Result<R, InvalidInput>,
    ) -> Result<R, InvalidInput> {
        let mut s = Measurements {
            update: self.header.update,
            stability_mask: self.header.stability_mask,
            history: self.header.history,
            mode_names: self.header.mode_names,
            active_lights: self.header.active_lights,
            complete: self.header.complete,
            previous_pre_gain: self.header.previous_pre_gain,
            grid_valid: self.header.grid_valid,
            second_grid_valid: self.header.second_grid_valid,
            exclusions_valid: self.header.exclusions_valid,
            exclusions: self.header.exclusions,
            exclusion_aggregate: self.header.exclusion_aggregate,
            histogram_cache: self.header.histogram_cache,
            histogram_aggregate: self.header.histogram_aggregate,
            seen: &mut self.seen,
            lights: &mut self.lights,
            second_counts: &mut self.second_counts,
            total_counts: &mut self.total_counts,
            grid: &mut self.grid,
        };
        let result = run(&mut s);
        self.header = Header::read(&s);
        result
    }
}
#[derive(Clone)]
struct State {
    gain: awb_gain_frame::State<64>,
    numeric: awb_preprocess::State,
    metadata: awb_preprocess::Metadata<64>,
    cache: Cache,
    results: Vec<LightResult>,
}
/// Caller supplies runtime bindings explicitly. Missing exposure takes the
/// recovered calibrated fallback branch; ISO is never inferred from RGB data.
pub struct Input {
    pub requested_update: bool,
    pub exposure_luma: Option<[f32; 2]>,
    pub iso: f32,
    pub site_reference: Option<awb_site::Input>,
}
#[derive(Debug, PartialEq)]
pub struct Output {
    pub action: crate::awb_dispatch::Action,
    pub continuation: awb_preprocess::Continuation,
    pub initial_gain: [f32; 4],
    pub current_gain: [f32; 4],
    pub previous_gain: [f32; 4],
    pub numeric: awb_preprocess::State,
    pub variance: f32,
    pub environment: i32,
    pub complete: bool,
    pub active_lights: u8,
    pub total_counts: Vec<u32>,
    pub grid_valid: bool,
    pub region: i32,
    pub retained: u32,
    pub density: f32,
    pub probabilities: Vec<f32>,
    pub controller_frame: u32,
    pub countdown: i32,
    pub preparation_requested: bool,
    pub stability_mask: u8,
    pub measurement_history: [[f32; 4]; 4],
}
pub struct Session {
    scene: Scene,
    geometry: crate::awb_measurement_geometry::Geometry,
    extra: MeasurementExclusions,
    sample_scale: i32,
    schedule: crate::awb_measurement_schedule::Schedule,
    regions: crate::awb_calibration::MeasurementRegions,
    uv_enabled: u16,
    yuv_enabled: u16,
    state: State,
}
impl Session {
    pub fn new(wb: &Value, dimensions: [u32; 2], sample_scale: u32) -> Result<Self, String> {
        if sample_scale == 0 || sample_scale > i32::MAX as u32 {
            return Err(String::from("Invalid sample scale"));
        }
        let scene = Scene::from_value(wb)?;
        let geometry = MeasurementGeometry::from_value(wb)?
            .derive(dimensions, sample_scale, None)
            .map_err(|e| format!("geometry: {e:?}"))?;
        let extra = MeasurementExclusions::from_value(wb)?;
        let gain = scene
            .initial_gain_state::<64>()
            .map_err(|e| format!("gain initialization: {e:?}"))?;
        let numeric = awb_preprocess::State {
            mode: 2,
            update: true,
            luma_integer: 0,
            luma: 0.,
            smart: scene.common.initial_smart,
            interval: 0,
            points: [0; 2],
            regions: [0.; 2],
            frame_counter: 0,
        };
        let metadata = awb_preprocess::Metadata {
            history: crate::awb_luma_history::History::from_values(&[])
                .map_err(|e| format!("history initialization: {e:?}"))?,
            level: 0,
            environment: 0,
            variance: 0.,
            brightness_stable: false,
        };
        let n = scene.lights.entries.len();
        let zero = LightResult {
            probability: awb_probability::Probability {
                total: 0.,
                distance: 0.,
                luma: 0.,
                prior: 0.,
                white_points: 0.,
            },
            gain: crate::awb_high_gain::LightResult {
                statistic: [0.; 4],
                spatial: [0.; 4],
                spatial_weight: 0.,
                extra_weight: 0.,
            },
        };
        let schedule = crate::awb_measurement_schedule::initialize(n as u8, 4)
            .map_err(|e| format!("schedule initialization: {e:?}"))?;
        let regions = crate::awb_calibration::MeasurementRegions::from_value(wb)?;
        let enabled = |key: &str| match wb["autoPara"][key].as_u64() {
            Some(0) => Ok(0u16),
            Some(1) => Ok(1u16),
            _ => Err(format!("Invalid detection flag: {key}")),
        };
        let uv_enabled = enabled("uvDetectionEnable")?;
        let yuv_enabled = enabled("yuvDetectionEnable")?;
        let state = State {
            gain,
            numeric,
            metadata,
            cache: Cache::fresh(n).map_err(|e| format!("cache initialization: {e:?}"))?,
            results: vec![zero; n],
        };
        Ok(Self {
            scene,
            geometry,
            extra,
            sample_scale: sample_scale as i32,
            schedule,
            regions,
            uv_enabled,
            yuv_enabled,
            state,
        })
    }
    /// Normal zero-reserved time-share record after a successful gain/preparation
    /// transition. Caller owns signature epochs and commits only after enqueue.
    pub fn next_measurement(
        &self,
        record: &mut [u8; crate::isp_awb_measurement::INPUT_BYTES],
        signature: &[u8; 64],
    ) -> Result<(), InvalidInput> {
        crate::awb_measurement_schedule::configure(
            record,
            &crate::awb_measurement_schedule::Calibration {
                uv_enabled: self.uv_enabled,
                yuv_enabled: self.yuv_enabled,
                capacity: 4,
                rt_yuv: &self.regions.rotated_yuv,
                uv: &self.regions.uv,
                xy: &self.regions.xy,
            },
            &crate::awb_measurement_schedule::Strategy {
                groups: &self.schedule.groups[..self.schedule.count],
                signature,
                xy_detection: None,
            },
        )?;
        record[0x444..0x448]
            .copy_from_slice(&(self.state.gain.controller.region.selected as u32).to_le_bytes());
        Ok(())
    }
    pub fn geometry(&self) -> &crate::awb_measurement_geometry::Geometry {
        &self.geometry
    }
    pub fn gain(&self) -> [f32; 4] {
        self.state.gain.controller.post.current
    }
    /// One translated, correctly snapshot-associated frame. Session supports
    /// FAST and normal zero-reserved linear records; HDR remains separate.
    pub fn process(
        &mut self,
        raw: &[u8; FRAME_BYTES],
        input: &Input,
    ) -> Result<Output, InvalidInput> {
        let frame = awb_preparation::Frame(raw);
        if raw[0x1d74] > 4 || (frame.fast()? && raw[0x1d74] != 4) {
            return Err(InvalidInput::Length);
        }
        if !input.iso.is_finite() || input.iso <= 0. {
            return Err(InvalidInput::GainRange);
        }
        let initial_gain = self.gain();
        let mut next = self.state.clone();
        next.numeric.frame_counter = next.gain.dispatch.frame;
        let continuation = next.numeric.derive_measurements(
            &awb_preprocess::Input {
                requested_mode: 2,
                previous_update: input.requested_update,
                smart_enabled: self.scene.preprocessing.smart_enabled,
                countdown: next.gain.dispatch.countdown,
                exposure_luma: input.exposure_luma,
                frame_choice: 0,
                working_mode: 0,
                fallback: self.scene.common.fallback_brightness(),
                override_enabled: false,
                override_valid: false,
                override_luma: 0.,
                geometry: [self.geometry.window[2], self.geometry.window[3]],
                block: self.geometry.block,
                sample_scale: self.sample_scale,
            },
            &self.scene.preprocessing.calibration(),
            &mut next.metadata,
            &self.scene.common.environment(),
            [
                next.gain.controller.post.converged,
                next.gain.controller.post.damping_stable,
            ],
            self.scene.common.luma_history_target,
        )?;
        let mut action = crate::awb_dispatch::Action {
            calculated: false,
            reconfigure: false,
        };
        let preparation_requested = next.numeric.update;
        if continuation == awb_preprocess::Continuation::Ready {
            let settings = awb_preparation::Settings {
                groups: self.schedule.count,
                fast_light_count: 4,
                stability_threshold: next.numeric.smart[2],
                prior_sample: next.numeric.luma,
                exclusion_kind: core::array::from_fn(|i| self.extra.regions[i].mode as i32),
                exclusion_weight: core::array::from_fn(|i| awb_probability::Curve {
                    knots: &self.extra.regions[i].knots,
                    weights: &self.extra.regions[i].weights,
                }),
            };
            let mut site = input.site_reference.unwrap_or(awb_site::Input {
                frame: 0,
                application_flag: false,
                application_mode: 1,
                reference_valid: false,
                reference_gain: [0.; 4],
                reference_sample: 0.,
                sample: 0.,
            });
            site.frame = next.gain.dispatch.frame;
            site.sample = next.numeric.luma;
            let extra_enabled = vec![false; self.scene.lights.entries.len()];
            let grid = [[0.; 3]; 225];
            let runtime = GainRuntime {
                active_lights: self.scene.lights.entries.len(),
                numeric: &next.numeric,
                variance: next.metadata.variance,
                environment: usize::try_from(next.metadata.environment)
                    .map_err(|_| InvalidInput::Length)?,
                fast: true,
                absolute_count_threshold: self.geometry.count_threshold,
                extra_enabled: &extra_enabled,
                grid_valid: false,
                grid: &grid,
                site_input: &site,
                iso: input.iso,
                scale: None,
            };
            action = next.cache.with_mut(|measurements| {
                self.scene.prepare_gain_frame(
                    &mut next.gain,
                    measurements,
                    &frame,
                    &settings,
                    self.geometry.sampled_dimensions,
                    &mut next.results,
                    &runtime,
                )
            })?;
            next.numeric.update = next.cache.header.update;
        } else {
            next.gain.dispatch.frame = next.numeric.frame_counter;
        }
        next.numeric.frame_counter = next.gain.dispatch.frame;
        let output = Output {
            action,
            continuation,
            initial_gain,
            current_gain: next.gain.controller.post.current,
            previous_gain: next.gain.controller.post.previous,
            numeric: next.numeric.clone(),
            variance: next.metadata.variance,
            environment: next.metadata.environment,
            complete: next.cache.header.complete,
            active_lights: next.cache.header.active_lights,
            total_counts: next.cache.total_counts.clone(),
            grid_valid: next.cache.header.grid_valid,
            region: next.gain.controller.region.selected as i32,
            retained: next.gain.controller.region.retained,
            density: next.gain.controller.density,
            probabilities: next.results[..next.cache.header.active_lights as usize]
                .iter()
                .map(|r| r.probability.total)
                .collect(),
            controller_frame: next.gain.dispatch.frame,
            countdown: next.gain.dispatch.countdown,
            preparation_requested,
            stability_mask: next.cache.header.stability_mask,
            measurement_history: next.cache.header.history,
        };
        self.state = next;
        Ok(output)
    }
}

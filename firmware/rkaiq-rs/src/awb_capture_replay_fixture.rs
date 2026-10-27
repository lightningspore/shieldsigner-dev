//! Offline first-frame replay. Runtime assumptions are explicit JSON inputs;
//! this command never opens a device or publishes computed gains.
use serde_json::{json, Value};
use shieldsigner_rkaiq::{
    awb_calibration::{GainRuntime, MeasurementExclusions, MeasurementGeometry, Scene},
    awb_gain_controller::LightResult,
    awb_preparation::{self, LightRecord, FRAME_BYTES, LIGHT_BYTES},
    awb_preprocess, awb_probability, awb_site, InvalidInput,
};

pub fn run(v: &Value) -> Result<Value, String> {
    let scene = Scene::from_value(&v["iq"])?;
    let geometry = MeasurementGeometry::from_value(&v["iq"])?;
    let extra = MeasurementExclusions::from_value(&v["iq"])?;
    let dimensions = [
        v["dimensions"][0].as_u64().ok_or("width")? as u32,
        v["dimensions"][1].as_u64().ok_or("height")? as u32,
    ];
    let sample_scale = v["sample_scale"].as_u64().ok_or("sample_scale")?;
    if sample_scale == 0 || sample_scale > i32::MAX as u64 {
        return Err("sample_scale outside checked range".into());
    }
    let geometry = geometry
        .derive(dimensions, sample_scale as u32, None)
        .map_err(|e| format!("geometry: {e:?}"))?;
    let iso = v["iso"].as_f64().ok_or("explicit ISO required")? as f32;
    if !iso.is_finite() || iso <= 0. {
        return Err("invalid ISO".into());
    }
    let text = v["raw"].as_str().ok_or("translated frame required")?;
    if text.len() != FRAME_BYTES * 2 {
        return Err("translated frame length".into());
    }
    let bytes = (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).map_err(|e| e.to_string()))
        .collect::<Result<Vec<_>, _>>()?;
    let raw: [u8; FRAME_BYTES] = bytes.try_into().map_err(|_| "translated frame length")?;
    let frame = awb_preparation::Frame(&raw);
    if !frame.fast().map_err(|e| format!("metadata: {e:?}"))? || raw[0x1d74] != 4 {
        return Err("Only the four-window FAST startup capture is supported".into());
    }
    // Initial software result owns the controller state; no synthetic history.
    let mut gain = scene
        .initial_gain_state::<64>()
        .map_err(|e| format!("gain init: {e:?}"))?;
    let mut numeric = awb_preprocess::State {
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
    let mut metadata = awb_preprocess::Metadata::<64> {
        history: shieldsigner_rkaiq::awb_luma_history::History::from_values(&[])
            .map_err(|e| format!("history: {e:?}"))?,
        level: 0,
        environment: 0,
        variance: 0.,
        brightness_stable: false,
    };
    let decision = numeric
        .derive_measurements(
            &awb_preprocess::Input {
                requested_mode: 2,
                previous_update: true,
                smart_enabled: scene.preprocessing.smart_enabled,
                countdown: gain.dispatch.countdown,
                exposure_luma: None,
                frame_choice: 0,
                working_mode: 0,
                fallback: scene.common.fallback_brightness(),
                override_enabled: false,
                override_valid: false,
                override_luma: 0.,
                geometry: [geometry.window[2], geometry.window[3]],
                block: geometry.block,
                sample_scale: sample_scale as i32,
            },
            &scene.preprocessing.calibration(),
            &mut metadata,
            &scene.common.environment(),
            [false; 2],
            scene.common.luma_history_target,
        )
        .map_err(|e| format!("numeric: {e:?}"))?;
    if decision != awb_preprocess::Continuation::Ready {
        return Err(format!("unexpected continuation: {decision:?}"));
    }
    let n = scene.lights.entries.len();
    let mut seen = vec![0; n];
    let mut records = vec![LightRecord([0; LIGHT_BYTES]); n];
    let mut second = vec![0; n];
    let mut totals = vec![0; n.max(2)];
    let mut grid = [[0.; 3]; 225];
    let mut measurements = awb_preparation::State::fresh(
        &mut seen,
        &mut records,
        &mut second,
        &mut totals,
        &mut grid,
        n,
    )
    .map_err(|e| format!("measurements: {e:?}"))?;
    let settings = awb_preparation::Settings {
        groups: 4,
        fast_light_count: 4,
        stability_threshold: numeric.smart[2],
        prior_sample: numeric.luma,
        exclusion_kind: core::array::from_fn(|i| extra.regions[i].mode as i32),
        exclusion_weight: core::array::from_fn(|i| awb_probability::Curve {
            knots: &extra.regions[i].knots,
            weights: &extra.regions[i].weights,
        }),
    };
    let site = awb_site::Input {
        frame: 0,
        application_flag: false,
        application_mode: 1,
        reference_valid: false,
        reference_gain: [0.; 4],
        reference_sample: 0.,
        sample: numeric.luma,
    };
    let extra_enabled = vec![false; n];
    let ignored_grid = [[0.; 3]; 225];
    let runtime = GainRuntime {
        active_lights: n,
        numeric: &numeric,
        variance: metadata.variance,
        environment: usize::try_from(metadata.environment).map_err(|_| "invalid environment")?,
        fast: true,
        absolute_count_threshold: geometry.count_threshold,
        extra_enabled: &extra_enabled,
        grid_valid: false,
        grid: &ignored_grid,
        site_input: &site,
        iso,
        scale: None,
    };
    let zero = LightResult {
        probability: awb_probability::Probability {
            total: 0.,
            distance: 0.,
            luma: 0.,
            prior: 0.,
            white_points: 0.,
        },
        gain: shieldsigner_rkaiq::awb_high_gain::LightResult {
            statistic: [0.; 4],
            spatial: [0.; 4],
            spatial_weight: 0.,
            extra_weight: 0.,
        },
    };
    let mut output = vec![zero; n];
    let start = gain.controller.post.current;
    let action = scene
        .prepare_gain_frame(
            &mut gain,
            &mut measurements,
            &frame,
            &settings,
            geometry.sampled_dimensions,
            &mut output,
            &runtime,
        )
        .map_err(|e: InvalidInput| format!("gain: {e:?}"))?;
    Ok(
        json!({"kind":"offline-captured-awb-gain","hardwareWrites":false,"automaticWhiteBalance":false,
        "inputAssumptions":{"sampleScale":sample_scale,"iso":iso,"exposureMetadata":"missing; calibrated fallback","savedSiteReference":"absent","softwarePreGainOverride":false},
        "numeric":{"brightness":numeric.luma,"points":numeric.points,"regions":numeric.regions,"smart":numeric.smart,"variance":metadata.variance,"environment":metadata.environment},
        "geometry":{"window":geometry.window,"block":geometry.block,"sampled":geometry.sampled_dimensions,"absoluteCountThreshold":geometry.count_threshold},
        "prepared":{"complete":measurements.complete,"activeLights":measurements.active_lights,"totalCounts":measurements.total_counts,"gridValid":measurements.grid_valid},
        "action":{"calculated":action.calculated,"reconfigureRequested":action.reconfigure},
        "gain":{"initial":start,"current":gain.controller.post.current,"previous":gain.controller.post.previous,"region":gain.controller.region.selected as i32,"retained":gain.controller.region.retained,"density":gain.controller.density},
        "probabilities":output[..measurements.active_lights as usize].iter().map(|r|r.probability.total).collect::<Vec<_>>() }),
    )
}

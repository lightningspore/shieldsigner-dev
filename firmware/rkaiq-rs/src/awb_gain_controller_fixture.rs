use crate::{
    awb_gain_controller::*, awb_gain_history, awb_high_gain, awb_low_gain, awb_low_single_color,
    awb_luma_history, awb_postprocess, awb_postprocess_fixture, awb_probability,
    awb_single_color::Line, awb_single_color_grid, awb_xy_selection,
};
use serde_json::{json, Value};
fn array<const N: usize>(v: &Value) -> [f32; N] {
    core::array::from_fn(|i| v[i].as_f64().unwrap() as f32)
}
fn scalar(v: &Value) -> f32 {
    v.as_f64().unwrap() as f32
}
pub fn run(v: &Value) -> Value {
    let s = &v["controller"];
    let u32s = |key: &str| {
        s[key]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_u64().unwrap() as u32)
            .collect::<Vec<_>>()
    };
    let xy = u32s("xy_history");
    let colors = u32s("color_history");
    let high_history: Vec<_> = s["high_history"]
        .as_array()
        .unwrap()
        .iter()
        .map(array)
        .collect();
    let initial_post = awb_postprocess_fixture::initial_with_capacity(v);
    let low = awb_low_gain::State {
        current: initial_post.current,
        low_result: [8.; 4],
        temporal_result: [9.; 4],
        spatial_result: [10.; 4],
        temporal_source: [11.; 4],
        spatial_weight: 0.25,
        used_previous: s["used_previous"].as_bool().unwrap(),
        color_history: awb_luma_history::History::from_values(&colors).unwrap(),
    };
    let detection = awb_single_color_grid::Detection {
        selected: 0x5a5a5a5a,
        color: 0x5a5a5a5a,
        candidate_counts: [0x5a5a5a5a; 14],
        color_counts: [0x5a5a5a5a; 14],
        valid: true,
        disagreements: 0x5a5a5a5a,
        votes: 0x5a5a5a5a,
        mean_distance: f32::from_bits(0x5a5a5a5a),
        gain: [12.; 4],
    };
    let mut state = State::<64> {
        region: awb_xy_selection::State {
            history: awb_luma_history::History::from_values(&xy).unwrap(),
            selected: if s["previous_region"].as_u64().unwrap() == 3 {
                awb_xy_selection::Region::Exclusion
            } else if s["previous_region"].as_u64().unwrap() == 1 {
                awb_xy_selection::Region::Big
            } else {
                awb_xy_selection::Region::Normal
            },
            retained: 42,
            kind: 2,
        },
        low: awb_low_single_color::State {
            low,
            detection,
            single_weight: 0.75,
        },
        post: initial_post,
        high_history: awb_gain_history::History::from_values(&high_history).unwrap(),
        estimated_gain: array(&s["estimated"]),
        high_gain: [13.; 4],
        high_low_weight: 0.5,
        temporal_weight: 0.75,
        density: 0.25,
        selection_status: 255,
        strategy_flag: true,
    };
    let line = |key: &str| Line {
        a: scalar(&v[key][0]),
        b: scalar(&v[key][1]),
        c: scalar(&v[key][2]),
        valid: v[key][3].as_bool().unwrap(),
    };
    let post = awb_postprocess::Settings {
        history_target: v["target"].as_i64().unwrap() as i32,
        tolerance: scalar(&v["tolerance"]),
        history_convergence: scalar(&v["history_convergence"]),
        damped_convergence: scalar(&v["damped_convergence"]),
        damping_threshold: scalar(&v["damping_threshold"]),
        brightness: v["brightness"].as_u64().unwrap() as u32,
        clipping: None,
        adjustment: None,
        offsets: if v["offset_enabled"].as_bool().unwrap() {
            Some(array(&v["offsets"]))
        } else {
            None
        },
        first: line("first"),
        second: line("second"),
    };
    let region = awb_xy_selection::Settings {
        absolute: scalar(&s["absolute"]),
        relative: scalar(&s["relative"]),
        region_thresholds: array(&s["region_thresholds"]),
        count_thresholds: core::array::from_fn(|i| {
            s["count_thresholds"][i].as_u64().unwrap() as u32
        }),
        stabilization: s["stabilization"].as_bool().unwrap(),
        target: s["xy_target"].as_i64().unwrap() as i32,
        variance: scalar(&s["variance"]),
        variance_threshold: 0.5,
    };
    let probability = awb_probability::Settings {
        gain: state.post.current,
        frame: s["frame"].as_u64().unwrap() as u32,
        fast: s["fast"].as_bool().unwrap(),
        near_distance_squared: 0.01,
        far_distance_squared: 2.,
        brightness: v["brightness"].as_u64().unwrap() as u32,
        brightness_thresholds: [100, 200, 400, 800],
        prior_sample: scalar(&s["prior_sample"]),
        absolute_count_threshold: region.absolute,
        relative_count_threshold: region.relative,
    };
    let high = awb_high_gain::Settings {
        fast: probability.fast,
        brightness: probability.brightness,
        temporal_default: [2., 1., 1., 3.],
        temporal_knots: core::array::from_fn(|i| 100 * i as u32),
        temporal_percentages: core::array::from_fn(|i| ((i % 6) * 20) as u8),
    };
    let low = awb_low_gain::Settings {
        retained: 0,
        count_threshold: region.count_thresholds[0],
        brightness: probability.brightness,
        low_brightness: 100,
        high_brightness: 200,
        temporal_default: high.temporal_default,
        color_history_value: 2,
        color_history_target: s["color_target"].as_u64().unwrap() as u16,
    };
    let single = s.get("single");
    let candidates: Vec<_> = single
        .map(|s| {
            s["candidates"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| awb_single_color_grid::Candidate {
                    red: scalar(&v[0]),
                    blue: scalar(&v[1]),
                })
                .collect()
        })
        .unwrap_or_default();
    let colors: Vec<_> = single
        .map(|s| {
            s["colors"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| awb_single_color_grid::Color {
                    chroma: scalar(&v["chroma"]),
                    hue: scalar(&v["hue"]),
                    cct_knots: array(&v["knots"]),
                    distance_thresholds: array(&v["thresholds"]),
                })
                .collect()
        })
        .unwrap_or_default();
    let grid: [[f32; 3]; 225] = single
        .map(|s| core::array::from_fn(|i| array(&s["grid"][i])))
        .unwrap_or([[0.; 3]; 225]);
    let confidence =
        single.map(|s| crate::awb_low_single_color_fixture::confidence(&s["confidence"]));
    let classifier = awb_single_color_grid::Calibration {
        candidates: &candidates,
        colors: &colors,
        alpha: single.map(|s| scalar(&s["alpha"])).unwrap_or(0.),
        history_target: low.color_history_target,
        first: line("first"),
        second: line("second"),
    };
    let single = single.map(|s| awb_low_single_color::Input {
        mode: 0,
        grid_valid: s["grid_valid"].as_bool().unwrap(),
        grid: &grid,
        classifier: &classifier,
        confidence: confidence.as_ref().unwrap(),
        brightness_sample: probability.prior_sample,
        density: 0.,
        acceptance_threshold: scalar(&s["threshold"]),
        estimated_gain: [0.; 4],
        high_history: &[],
    });
    let settings = Settings {
        mode: s["mode"].as_i64().unwrap() as i32,
        region: &region,
        probability,
        high: &high,
        low: &low,
        single,
        post: &post,
        high_history_threshold: scalar(&s["high_threshold"]),
        estimated_density_threshold: scalar(&s["estimated_threshold"]),
        estimated_single_threshold: 0.5,
    };
    let source = s["lights"].as_array().unwrap();
    let prior_knots = [0., 1., 2., 3.];
    let priors: Vec<[f32; 4]> = source.iter().map(|v| array(&v["prior"])).collect();
    let lights: Vec<_> = source
        .iter()
        .enumerate()
        .map(|(i, l)| Light {
            counts: core::array::from_fn(|j| l["counts"][j].as_u64().unwrap() as u32),
            gains: core::array::from_fn(|j| array(&l["gains"][j])),
            probability: awb_probability::Light {
                reference_gain: array(&l["reference"]),
                statistic_gain: [0.; 4],
                kind: l["kind"].as_i64().unwrap() as i32,
                white_points: 0,
                prior: awb_probability::Curve {
                    knots: &prior_knots,
                    weights: &priors[i],
                },
            },
            calibration: awb_high_gain::Light {
                selected_gain: [0.; 4],
                selected_count: 0,
                extra_gain: [0.; 4],
                extra_count: 0,
                extra_enabled: l["extra"].as_bool().unwrap(),
                low_threshold: 100,
                high_threshold: 200,
                low_gain: [2., 1., 1., 4.],
                high_gain: [3., 1., 1., 2.],
                spatial_percentage: l["percentage"].as_u64().unwrap() as u8,
                probability: 0.,
            },
        })
        .collect();
    let mut results: Vec<_> = v["lights"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| LightResult {
            probability: awb_probability::Probability {
                total: scalar(&v["probability"]),
                distance: 0.5,
                luma: 0.75,
                prior: 1.,
                white_points: 1.25,
            },
            gain: awb_high_gain::LightResult {
                statistic: array(&v["gain"]),
                spatial: [14.; 4],
                spatial_weight: 0.25,
                extra_weight: 0.75,
            },
        })
        .collect();
    let frame = Frame {
        complete: s["complete"].as_bool().unwrap(),
        fallback: array(&v["candidate"]),
        exclusion_count: s["exclusion_count"].as_u64().unwrap() as u32,
        exclusion_gain: [2., 1., 1., 3.],
        divisors: [10, 20],
    };
    let outer = s.get("outer");
    let mut site = crate::awb_site::State {
        matched: outer
            .map(|o| o["matched"].as_bool().unwrap())
            .unwrap_or(false),
        frames: outer
            .map(|o| o["frames"].as_u64().unwrap() as u32)
            .unwrap_or(0),
    };
    let dispatch = s.get("dispatch");
    let mut dispatch_state = crate::awb_dispatch::State {
        countdown: dispatch
            .map(|d| d["countdown"].as_i64().unwrap() as i32)
            .unwrap_or(0),
        frame: settings.probability.frame,
    };
    let before_dispatch = dispatch_state;
    let mut action = crate::awb_dispatch::Action {
        calculated: false,
        reconfigure: false,
    };
    let before_site = site.clone();
    let before = state.clone();
    let before_results = results.clone();
    let result = if s["prepared"].as_bool().unwrap_or(false) {
        let mut records: Vec<_> = lights
            .iter()
            .map(|light| {
                let mut bytes = [0u8; crate::awb_preparation::LIGHT_BYTES];
                for region in 0..3 {
                    let at = region * crate::awb_preparation::REGION_BYTES;
                    bytes[at..at + 4].copy_from_slice(&light.counts[region].to_le_bytes());
                    for channel in 0..4 {
                        let offset = at + 4 + channel * 4;
                        bytes[offset..offset + 4]
                            .copy_from_slice(&light.gains[region][channel].to_le_bytes());
                    }
                }
                crate::awb_preparation::LightRecord(bytes)
            })
            .collect();
        if s.get("scene_iq").is_some() && records.len() == 4 {
            records.extend(
                [crate::awb_preparation::LightRecord([0xff; crate::awb_preparation::LIGHT_BYTES]);
                    3],
            );
        }
        // Poison the unused explicit fields: the adapter must read records.
        let mut calibration = lights.clone();
        for light in &mut calibration {
            light.counts = [u32::MAX; 4];
            light.gains = [[f32::NAN; 4]; 4];
        }
        if let Some(o) = outer {
            let site_settings = crate::awb_site::Settings {
                enabled: o["enabled"].as_bool().unwrap(),
                frame_limit: o["frame_limit"].as_u64().unwrap() as u32,
                reuse_enabled: o["reuse_enabled"].as_bool().unwrap(),
                gain_threshold: scalar(&o["gain_threshold"]),
                sample_threshold: scalar(&o["sample_threshold"]),
            };
            let site_input = crate::awb_site::Input {
                frame: settings.probability.frame,
                application_flag: o["application_flag"].as_bool().unwrap(),
                application_mode: o["application_mode"].as_i64().unwrap() as i32,
                reference_valid: o["reference_valid"].as_bool().unwrap(),
                reference_gain: array(&o["reference_gain"]),
                reference_sample: scalar(&o["reference_sample"]),
                sample: settings.probability.prior_sample,
            };
            let controls = crate::awb_wrapper::Controls {
                damping: crate::awb_gain::DampingParameters {
                    variance_threshold: 0.5,
                    step: scalar(&o["step"]),
                    minimum: 0.,
                    maximum: 0.9,
                },
                variance: region.variance,
                tolerance_knots: &[0., 100., 1000.],
                tolerance_values: &[0.01, 0.1, 0.2],
                site: &site_settings,
                site_input: &site_input,
            };
            if let Some(d) = dispatch {
                let mut joined = crate::awb_gain_frame::State {
                    dispatch: dispatch_state,
                    controller: state.clone(),
                    site: site.clone(),
                };
                let scale = d["scale"]
                    .as_array()
                    .map(|v| [v[0].as_f64().unwrap() as f32, v[1].as_f64().unwrap() as f32]);
                let result = if let Some(wb) = s.get("scene_iq") {
                    let scene = crate::awb_calibration::Scene::from_value(wb).unwrap();
                    let numeric = crate::awb_preprocess::State {
                        mode: 0,
                        update: d["update"].as_bool().unwrap(),
                        luma_integer: probability.brightness,
                        luma: probability.prior_sample,
                        smart: [0.001, 0.005, 0.05],
                        interval: 0,
                        points: region.count_thresholds,
                        regions: region.region_thresholds,
                        frame_counter: dispatch_state.frame,
                    };
                    let extra: Vec<_> =
                        lights.iter().map(|l| l.calibration.extra_enabled).collect();
                    scene.process_gain_frame(
                        &mut joined,
                        numeric.update,
                        &frame,
                        &records,
                        &mut results,
                        &crate::awb_calibration::GainRuntime {
                            active_lights: lights.len(),
                            numeric: &numeric,
                            variance: region.variance,
                            environment: s["environment"].as_u64().unwrap() as usize,
                            fast: probability.fast,
                            absolute_count_threshold: region.absolute,
                            extra_enabled: &extra,
                            grid_valid: s["single"]["grid_valid"].as_bool().unwrap(),
                            grid: &grid,
                            site_input: &site_input,
                            iso: 100.,
                            scale,
                        },
                    )
                } else {
                    joined.process(
                        d["update"].as_bool().unwrap(),
                        &frame,
                        &records,
                        &calibration,
                        &mut results,
                        &settings,
                        &controls,
                        scale,
                    )
                };
                if let Ok(value) = result {
                    action = value;
                }
                dispatch_state = joined.dispatch;
                state = joined.controller;
                site = joined.site;
                result.map(|_| ())
            } else {
                crate::awb_wrapper::process(
                    &mut state,
                    &mut site,
                    &frame,
                    &records,
                    &calibration,
                    &mut results,
                    &settings,
                    &controls,
                )
            }
        } else {
            state.process_prepared(&frame, &records, &calibration, &mut results, &settings)
        }
    } else {
        state.process(&frame, &lights, &mut results, &settings)
    };
    if s["expect_prepared_error"].as_bool().unwrap_or(false) {
        let error = if s["late_site_error"].as_bool().unwrap_or(false)
            || s["late_scale_error"].as_bool().unwrap_or(false)
        {
            crate::InvalidInput::NonFinite
        } else {
            crate::InvalidInput::UnsupportedRegion
        };
        assert_eq!(result, Err(error));
        assert_eq!(dispatch_state, before_dispatch);
        assert_eq!(site, before_site);
        assert_eq!(state, before);
        assert_eq!(results, before_results);
        return json!({"error":format!("{:?}", error), "unchanged":true});
    }
    result.unwrap();
    let lights:Vec<_>=results.iter().map(|v|json!({"probability":([v.probability.total,v.probability.distance,v.probability.luma,v.probability.prior,v.probability.white_points].map(f32::to_bits)),"statistic":v.gain.statistic.map(f32::to_bits),"spatial":v.gain.spatial.map(f32::to_bits),"spatial_weight":v.gain.spatial_weight.to_bits(),"extra_weight":v.gain.extra_weight.to_bits()})).collect();
    let high: Vec<_> = state
        .high_history
        .values()
        .iter()
        .map(|v| v.map(f32::to_bits))
        .collect();
    let mut output = awb_postprocess_fixture::output(&state.post);
    output["controller"] = json!({"selected":state.region.selected as u8,"retained":state.region.retained,"kind":state.region.kind,"density":state.density.to_bits(),"high_gain":state.high_gain.map(f32::to_bits),"high_low_weight":state.high_low_weight.to_bits(),"temporal_weight":state.temporal_weight.to_bits(),"estimated":state.estimated_gain.map(f32::to_bits),"low_result":state.low.low.low_result.map(f32::to_bits),"temporal_result":state.low.low.temporal_result.map(f32::to_bits),"spatial_result":state.low.low.spatial_result.map(f32::to_bits),"temporal_source":state.low.low.temporal_source.map(f32::to_bits),"spatial_weight":state.low.low.spatial_weight.to_bits(),"used_previous":state.low.low.used_previous,"single_weight":state.low.single_weight.to_bits(),"selection_status":state.selection_status,"strategy_flag":state.strategy_flag,"xy_history":state.region.history.values(),"color_history":state.low.low.color_history.values(),"high_history":high,"lights":lights});
    if dispatch.is_some() {
        output["dispatch"] = json!({"frame":dispatch_state.frame,"countdown":dispatch_state.countdown,"calculated":action.calculated,"reconfigure":action.reconfigure});
    }
    if let Some(wb) = s.get("scene_iq") {
        if action.calculated {
            let scene = crate::awb_calibration::Scene::from_value(wb).unwrap();
            output["_scene_tolerance"] = json!(scene
                .preprocessing
                .tolerance(settings.probability.brightness)
                .unwrap()
                .to_bits());
        }
    }
    if outer.is_some() {
        output["outer"] = json!({"matched":site.matched,"frames":site.frames,"tolerance":if dispatch.is_some() && !action.calculated { post.tolerance.to_bits() } else { crate::interpolate(&[0.,100.,1000.], &[0.01,0.1,0.2], settings.probability.brightness as f32).unwrap().to_bits() }});
    }
    if let Some(tolerance) = output.as_object_mut().unwrap().remove("_scene_tolerance") {
        output["outer"]["tolerance"] = tolerance;
    }
    if s.get("single").is_some() || outer.is_some() {
        let r = &state.low.detection;
        output["controller"]["single"] = json!({"selected":r.selected,"color":r.color,"candidate_counts":r.candidate_counts,"color_counts":r.color_counts,"valid":r.valid,"disagreements":r.disagreements,"votes":r.votes,"mean":r.mean_distance.to_bits(),"gain":r.gain.map(f32::to_bits)});
    }
    output
}

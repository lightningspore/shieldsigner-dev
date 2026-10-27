use shieldsigner_rkaiq::*;
fn initialize(v: &serde_json::Value) -> (ae_pipeline::State, Vec<ae_route::Point>) {
    let f = |k: &str| v[k].as_f64().unwrap() as f32;
    let b = |k: &str| v[k].as_bool().unwrap();
    let initial = ae_route::Point {
        time: 0.0045,
        gain: 2.,
        isp_gain: 1.,
    };
    let timing = ae_publication::Timing {
        frame_length: 1360,
        line_length: 2800,
        pixel_clock_mhz: 114.24,
    };
    let mut retained = [[0; 244]; 6];
    let count = v["count"].as_u64().unwrap() as usize;
    for r in retained.iter_mut().take(count) {
        *r = ae_publication::pack(
            ae_route::Point {
                time: 0.,
                gain: 0.,
                isp_gain: 0.,
            },
            exposure::Codes {
                integration_time: 0,
                gain: 0,
            },
            0,
            timing,
        );
    }
    retained[count] = ae_publication::pack(
        initial,
        exposure::Codes {
            integration_time: 184,
            gain: 256,
        },
        -1,
        timing,
    );
    let previous = ae_publication::pack(
        ae_route::Point {
            time: 0.003,
            gain: 1.,
            isp_gain: 1.,
        },
        exposure::Codes {
            integration_time: 122,
            gain: 128,
        },
        -1,
        timing,
    );
    let mut published = [[0; 244]; 6];
    for (i, time) in [0.003f32, 0.006].into_iter().enumerate() {
        for (o, x) in [(0, time), (4, 1.), (8, 1.), (12, 1.)] {
            published[i][o..o + 4].copy_from_slice(&x.to_le_bytes());
        }
    }
    let state = ae_pipeline::State {
        frame: ae_frame::State {
            error_history: core::array::from_fn(|i| {
                v["damping_history"][i].as_f64().unwrap() as f32
            }),
            target: 45.,
            current_error: 0.,
            convergence: ae_convergence::State {
                gating_enabled: b("enabled") as u8,
                dynamic_enabled: b("dynamic_enabled") as u8,
            },
        },
        runtime: ae_run::State {
            previous_q8: [100, 200, 300],
            previous_mean: 11.,
            previous_hdr_means: [12., 13., 14.],
        },
        controller: ae_controller::State {
            history: core::array::from_fn(|i| ae_environment::Record {
                frame: i as i32,
                current_exposure: 0.003,
                published_exposure: 0.003,
                error: if i % 2 == 0 { 0.2 } else { -0.2 },
                queued: [0.003, 0.006, 0.009, 0.012, 0.015, 0.018],
                queued_count: 2,
            }),
            index: v["index"].as_u64().unwrap() as u32,
            environment: ae_environment::State {
                priming: b("priming"),
                queued_count: 2,
                held_exposure: 0.003,
            },
            delay: Default::default(),
            cache: ae_route::Cache {
                exposure: 0.003,
                relative_threshold: 0.01,
                force: b("force"),
                point: ae_route::Point {
                    time: 0.003,
                    gain: 1.,
                    isp_gain: 1.,
                },
            },
            previous_error: f("previous"),
            reference_error: f("reference"),
            saturated: b("saturated"),
        },
        publication: ae_publication::State {
            previous_final: previous,
            empty_reference: [0; 244],
            published,
            published_count: 2,
            synchronized_frame: v["sync"].as_i64().unwrap() as i32,
            last_result_frame: 0,
        },
        retained_records: retained,
        retained_count: count + 1,
        last_aggregate: 0.009,
    };
    let route: Vec<_> = [
        (0., 1.),
        (0.01, 1.),
        (0.01, 4.),
        (0.02, 8.),
        (0.03, 15.5),
        (0.03, 512.),
    ]
    .into_iter()
    .map(|(time, gain)| ae_route::Point {
        time,
        gain,
        isp_gain: 1.,
    })
    .collect();
    (state, route)
}
fn step(
    v: &serde_json::Value,
    mut state: &mut ae_pipeline::State,
    mut route: &mut Vec<ae_route::Point>,
) -> String {
    let f = |k: &str| v[k].as_f64().unwrap() as f32;
    let b = |k: &str| v[k].as_bool().unwrap();
    let count = v["count"].as_u64().unwrap() as usize;
    let h: Vec<_> = v["histogram"]
        .as_array()
        .unwrap()
        .iter()
        .map(|n| n.as_u64().unwrap() as u32)
        .collect();
    let calibration = calibration::SensorCalibration::from_value(&v["profile"]).unwrap();
    let q8 = [(f("measured") * 256.) as u16, 512, 768];
    let (current_exposure, effective) = if v["effective_from_previous"].as_bool().unwrap_or(false) {
        let r = &state.retained_records[state.retained_count - 1];
        let word = |o| u32::from_le_bytes(r[o..o + 4].try_into().unwrap());
        (
            (f32::from_bits(word(4)) * f32::from_bits(word(0))) * f32::from_bits(word(12)),
            ae_convergence::Exposure {
                time_code: word(32),
                gain_code: word(36),
                isp_gain: f32::from_bits(word(12)),
            },
        )
    } else {
        (
            f("exposure"),
            ae_convergence::Exposure {
                time_code: 0,
                gain_code: 0,
                isp_gain: 1.,
            },
        )
    };
    let selected = if let Some(scene) = v.get("policy_scene") {
        ae_policy::Calibration::from_scene(scene)
            .unwrap()
            .select(
                state.frame.convergence.gating_enabled != 0,
                v["alternate"].as_bool().unwrap(),
            )
            .unwrap()
    } else {
        ae_policy::Selected {
            tolerance_percent: 10.,
            damping_under: 0.5,
            damping_over: 0.4,
        }
    };
    let initial_error_history = state.frame.error_history;
    let out = ae_pipeline::linear(
        &mut state,
        &mut route,
        &h,
        ae_decision::Input {
            target: 45.,
            measured: f("measured"),
            current_exposure,
            tolerance_percent: selected.tolerance_percent,
            minimum_exposure: 0.00005,
            maximum_exposure: 15.36,
            saturated: false,
        },
        ae_controller::Policy {
            dynamic: if b("dynamic") {
                Some(ae_brightness::Dynamic {
                    enabled: b("dynamic_enabled"),
                    mode: ae_damping::Mode::Default,
                    history: initial_error_history,
                })
            } else {
                None
            },
            damping_under: selected.damping_under,
            damping_over: selected.damping_over,
            fps: f("fps"),
            delay_enabled: b("enabled"),
            same_mode: b("same_mode"),
            negative_delay: 3,
            positive_delay: 2,
        },
        ae_route::Limits {
            minimum_time: 0.00005,
            maximum_time: 0.03,
            minimum_gain: 1.,
            maximum_gain: 512.,
            time_quantum: 0.01,
            floor_tolerance_coefficient: 8.,
            line_length: 2800.,
            pixel_clock_mhz: 114.24,
        },
        ae_frame::Target {
            levels: &[0., 1.],
            points: &[45., 45.],
            bias_percent: 0.,
        },
        calibration.conversion(calibration::RuntimeTiming {
            frame_length: 1360,
            pixel_clock_mhz: 114.24,
            line_length_pixels: 2800,
        }),
        ae_register::Policy {
            isp_range: [1., 32.],
            time_range: [0.00005, 0.03],
            gain_range: [1., 512.],
            analogue_minimum: 1.,
            time_quantum: 0.01,
            flicker_enabled: true,
            automatic: true,
            suppress_isp_compensation: false,
        },
        v["frame"].as_i64().unwrap() as i32,
        q8,
        [2., 3., 4.],
        effective,
        count,
    )
    .unwrap();
    let c = &state.controller;
    let p = &state.publication;
    let r = &state.retained_records[state.retained_count - 1];
    let word = |o| u32::from_le_bytes(r[o..o + 4].try_into().unwrap());
    let error = out
        .frame
        .control
        .map_or(out.frame.preprocessing_error, |c| c.relative_error);
    let mut words = vec![
        out.frame.run as u32,
        state.last_aggregate.to_bits(),
        word(4),
        word(12),
        word(0),
        word(32),
        word(36),
        error.to_bits(),
        c.previous_error.to_bits(),
        c.reference_error.to_bits(),
        c.environment.held_exposure.to_bits(),
        p.published_count as u32,
        c.index,
        p.synchronized_frame as u32,
        p.last_result_frame as u32,
        state.frame.convergence.dynamic_enabled as u32,
        state.frame.convergence.gating_enabled as u32,
        c.environment.priming as u32,
        c.saturated as u32,
        c.delay.changed as u32,
        c.cache.force as u32,
        c.delay.negative_start as u32,
        c.delay.positive_start as u32,
        c.delay.negative_count as u32,
        c.delay.positive_count as u32,
        c.cache.exposure.to_bits(),
        c.cache.point.gain.to_bits(),
        c.cache.point.isp_gain.to_bits(),
        c.cache.point.time.to_bits(),
    ];
    words.extend(state.frame.error_history.map(f32::to_bits));
    words.extend(state.runtime.previous_q8.map(u32::from));
    words.push(state.runtime.previous_mean.to_bits());
    words.extend(state.runtime.previous_hdr_means.map(f32::to_bits));
    words.extend(route.iter().map(|p| p.time.to_bits()));
    let mut result = words
        .iter()
        .map(|w| format!("{w:08x}"))
        .collect::<Vec<_>>()
        .join(",");
    let hex = |b: &[u8]| b.iter().map(|x| format!("{x:02x}")).collect::<String>();
    result += &format!(
        ":{}:{}:{}:{}:",
        out.publication.count,
        hex(&out.publication.records.concat()),
        hex(&p.published.concat()),
        hex(&p.previous_final)
    );
    let mut words = Vec::new();
    for r in c.history {
        words.extend([
            r.frame as u32,
            r.current_exposure.to_bits(),
            r.published_exposure.to_bits(),
            r.error.to_bits(),
        ]);
        words.extend(r.queued.map(f32::to_bits));
        words.push(r.queued_count);
    }
    let bytes: Vec<_> = words.into_iter().flat_map(u32::to_le_bytes).collect();
    result += &hex(&bytes);
    result
}

pub fn run(v: &serde_json::Value) -> String {
    let (mut state, mut route) = initialize(v);
    step(v, &mut state, &mut route)
}
pub fn sequence(v: &serde_json::Value) -> String {
    let initial = &v["initial"];
    let (mut state, mut route) = initialize(initial);
    v["frames"]
        .as_array()
        .unwrap()
        .iter()
        .map(|frame| {
            let mut input = initial.clone();
            for (key, value) in frame.as_object().unwrap() {
                input[key] = value.clone();
            }
            step(&input, &mut state, &mut route)
        })
        .collect::<Vec<_>>()
        .join("|")
}

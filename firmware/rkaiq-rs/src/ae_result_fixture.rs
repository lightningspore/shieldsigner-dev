use shieldsigner_rkaiq::*;
pub fn run(v: &serde_json::Value) -> String {
    let p = |x: &serde_json::Value| ae_route::Point {
        time: x[0].as_f64().unwrap() as f32,
        gain: x[1].as_f64().unwrap() as f32,
        isp_gain: x[2].as_f64().unwrap() as f32,
    };
    let number = |k: &str| v[k].as_f64().unwrap() as f32;
    let mut route: Vec<_> = v["route"].as_array().unwrap().iter().map(p).collect();
    let profile = calibration::SensorCalibration::from_value(&v["profile"]).unwrap();
    let calibration = profile.conversion(calibration::RuntimeTiming {
        frame_length: 1360,
        pixel_clock_mhz: 114.24,
        line_length_pixels: 2800,
    });
    let text = v["previous"].as_str().unwrap();
    let previous =
        core::array::from_fn(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap());
    let mut published = [[0; 244]; 6];
    for (i, value) in v["published"].as_array().unwrap().iter().enumerate() {
        let x = p(value);
        for (o, n) in [(0, x.time), (4, x.gain), (8, 1.), (12, x.isp_gain)] {
            published[i][o..o + 4].copy_from_slice(&n.to_le_bytes());
        }
    }
    let mut state = ae_publication::State {
        previous_final: previous,
        published,
        published_count: v["published"].as_array().unwrap().len(),
        synchronized_frame: v["sync"].as_i64().unwrap() as i32,
        last_result_frame: 0,
    };
    let mut convergence = ae_convergence::State {
        dynamic_enabled: v["dynamic"].as_u64().unwrap() as u8,
        gating_enabled: v["gating"].as_u64().unwrap() as u8,
    };
    let mut history = core::array::from_fn(|i| ae_environment::Record {
        frame: i as i32,
        current_exposure: 0.003,
        published_exposure: 0.006,
        error: 0.2,
        queued: [0.001, 0.002, 0.003, 0.004, 0.005, 0.006],
        queued_count: 2,
    });
    let out = ae_result::linear(
        &mut state,
        &mut convergence,
        &mut history,
        v["index"].as_u64().unwrap() as u32,
        p(&v["proposed"]),
        number("target"),
        number("held"),
        ae_convergence::Exposure {
            time_code: v["effective"][0].as_u64().unwrap() as u32,
            gain_code: v["effective"][1].as_u64().unwrap() as u32,
            isp_gain: v["effective"][2].as_f64().unwrap() as f32,
        },
        v["frame_id"].as_i64().unwrap() as i32,
        v["count"].as_u64().unwrap() as usize,
        &mut route,
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
        calibration,
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
    )
    .unwrap();
    let c = out.conversion.current;
    let mut words = vec![
        c.gain.to_bits(),
        c.isp_gain.to_bits(),
        c.seconds.to_bits(),
        c.codes.integration_time,
        c.codes.gain,
    ];
    for entry in out.conversion.intermediate.into_iter().flatten() {
        let c = entry.converted;
        words.extend([
            entry.aggregate.to_bits(),
            c.gain.to_bits(),
            c.isp_gain.to_bits(),
            c.seconds.to_bits(),
            u32::MAX,
            c.codes.integration_time,
            c.codes.gain,
            0,
        ]);
    }
    words.extend(route.iter().map(|p| p.time.to_bits()));
    let mut result = words
        .iter()
        .map(|w| format!("{w:08x}"))
        .collect::<Vec<_>>()
        .join(",");
    let hex = |b: &[u8]| b.iter().map(|v| format!("{v:02x}")).collect::<String>();
    let o = out.publication;
    result += &format!(
        ":{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:",
        o.count,
        o.synchronized_frame,
        hex(&o.records.concat()),
        hex(&o.final_record),
        state.published_count,
        state.last_result_frame,
        convergence.dynamic_enabled,
        convergence.gating_enabled,
        hex(&state.published.concat()),
        hex(&state.previous_final)
    );
    let mut words = Vec::new();
    for r in history {
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

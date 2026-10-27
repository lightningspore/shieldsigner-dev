//! Deterministic state/frame builder for the original-ARM preparation corpus.
use serde_json::Value;
use shieldsigner_rkaiq::{awb_gain::Gains, awb_preparation::*, awb_probability::Curve};
fn bytes(mut state: u32, size: usize) -> Vec<u8> {
    (0..size)
        .map(|_| {
            state = state.wrapping_mul(1664525).wrapping_add(1013904223);
            (state >> 24) as u8
        })
        .collect()
}
fn words(seed: u32, n: usize) -> Vec<u32> {
    bytes(seed, n * 4)
        .chunks_exact(4)
        .map(|b| u32::from_le_bytes(b.try_into().unwrap()))
        .collect()
}
fn gain(seed: u32) -> Gains {
    let w = words(seed, 4);
    core::array::from_fn(|i| 0.5 + (w[i] >> 16) as f32 / 65536.)
}
fn put32(b: &mut [u8], o: usize, v: u32) {
    b[o..o + 4].copy_from_slice(&v.to_le_bytes());
}
fn put64(b: &mut [u8], o: usize, v: i64) {
    b[o..o + 8].copy_from_slice(&v.to_le_bytes());
}
fn putgain(b: &mut [u8], o: usize, v: Gains) {
    for (i, x) in v.iter().enumerate() {
        put32(b, o + i * 4, x.to_bits());
    }
}
fn name(text: &str) -> ModeName {
    let mut b = [0x4b; 64];
    b[..text.len()].copy_from_slice(text.as_bytes());
    b[text.len()] = 0;
    ModeName(b)
}
fn frame(v: &Value, step: usize) -> [u8; FRAME_BYTES] {
    let seed = v["seed"].as_u64().unwrap() as u32;
    let n = v["n"].as_u64().unwrap() as usize;
    let groups = v["groups"].as_u64().unwrap() as usize;
    let mut b: [u8; FRAME_BYTES] = bytes(seed ^ 0xabcdef00 ^ step as u32, FRAME_BYTES)
        .try_into()
        .unwrap();
    let at = 0x1d70;
    put32(
        &mut b,
        at,
        (v["mode"].as_u64().unwrap() as u32 + step as u32) % 3,
    );
    let indices = v["indices"].as_array().unwrap();
    b[at + 4] = indices.len() as u8;
    put32(
        &mut b,
        at + 8,
        if v["fast"].as_bool().unwrap() && v["fast_minus"].as_bool().unwrap() {
            u32::MAX
        } else {
            ((v["group"].as_u64().unwrap() as usize + step) % groups) as u32
        },
    );
    for (i, index) in indices.iter().enumerate() {
        let mut index = index.as_u64().unwrap() as usize;
        if v["rotate"].as_bool().unwrap() && index < n {
            index = (index + step * indices.len()) % n;
        }
        put32(&mut b, at + 12 + i * 4, index as u32);
    }
    let text = if v["fast"].as_bool().unwrap() {
        "FASTAWBACT"
    } else if v["rename"].as_bool().unwrap() && step > 0 {
        "cfg-B"
    } else {
        "cfg-A"
    };
    b[at + 28..at + 92].copy_from_slice(&name(text).0);
    let mut pg = gain(seed ^ 0xa0);
    pg[0] += step as f32 * 0.125;
    pg[3] += step as f32 * 0.0625;
    putgain(&mut b, at + 92, pg);
    for i in 0..225 {
        if v["zero_grid"].as_bool().unwrap() && i % 3 == 0 {
            put32(&mut b, 0xd0 + i * 32, 0);
        }
    }
    for local in 0..indices.len() {
        for region in 0..2 {
            let o = local * 48 + region * 24;
            if v["zero_lights"].as_bool().unwrap() && local % 2 == 0 {
                put64(&mut b, o, 0);
            } else if v["direct_counts"].as_bool().unwrap() {
                put64(
                    &mut b,
                    o,
                    [0, 511, 512, 513, 4294966784, i64::MAX][(local + region + step) % 6],
                );
            }
        }
    }
    for i in 0..4 {
        if v["zero_exclusions"].as_bool().unwrap() {
            put64(&mut b, 0x1cf0 + i * 24, 0);
        }
    }
    let (r, g, blue) = match v["sum_mode"].as_u64().unwrap() {
        0 => (100, 200, 100),
        1 => (0, 123, 100),
        2 => (-1, 123, 100),
        _ => (1, i64::MAX, 2),
    };
    put64(&mut b, 0x1de8, r);
    put64(&mut b, 0x1df0, g);
    put64(&mut b, 0x1df8, blue);
    b
}
fn render(s: &State<'_>) -> String {
    let mut out = vec![
        s.update as u8,
        s.stability_mask,
        s.active_lights,
        s.complete as u8,
        s.grid_valid as u8,
        s.second_grid_valid as u8,
        s.exclusions_valid as u8,
    ];
    for gain in s.history {
        for x in gain {
            out.extend(x.to_le_bytes());
        }
    }
    for name in s.mode_names {
        out.extend(name.0);
    }
    out.extend_from_slice(s.seen);
    for light in s.lights.iter() {
        out.extend(light.0);
    }
    for a in [&*s.second_counts, &*s.total_counts] {
        for x in a {
            out.extend(x.to_le_bytes());
        }
    }
    for x in s.previous_pre_gain {
        out.extend(x.to_le_bytes());
    }
    for pixel in s.grid.iter() {
        for x in pixel {
            out.extend(x.to_le_bytes());
        }
    }
    for range in &s.exclusions {
        out.extend(range);
    }
    out.extend(s.exclusion_aggregate);
    for row in s.histogram_cache {
        for x in row {
            out.extend(x.to_le_bytes());
        }
    }
    for x in s.histogram_aggregate {
        out.extend(x.to_le_bytes());
    }
    out.iter().map(|b| format!("{b:02x}")).collect()
}
pub fn run(v: &Value) -> String {
    let seed = v["seed"].as_u64().unwrap() as u32;
    let n = v["n"].as_u64().unwrap() as usize;
    let groups = v["groups"].as_u64().unwrap() as usize;
    let mut seen = vec![0; n];
    for (i, b) in seen.iter_mut().enumerate() {
        *b = if v["seen"].as_bool().unwrap() {
            1
        } else {
            (i % 2) as u8
        };
    }
    let mut lights: Vec<LightRecord> = bytes(seed ^ 0x11, n * LIGHT_BYTES)
        .chunks_exact(LIGHT_BYTES)
        .map(|b| LightRecord(b.try_into().unwrap()))
        .collect();
    for (i, light) in lights.iter_mut().enumerate() {
        for region in 0..2 {
            putgain(
                &mut light.0,
                region * REGION_BYTES + 4,
                gain(seed ^ 0x1000 ^ (i * 4 + region) as u32),
            );
        }
        putgain(&mut light.0, 0x9c, gain(seed ^ 0x2000 ^ i as u32));
    }
    let mut second = words(seed ^ 0x22, n);
    let mut totals = words(seed ^ 0x33, n.max(2));
    let w = words(seed ^ 0x44, 225 * 3);
    let mut grid = core::array::from_fn(|i| {
        core::array::from_fn(|j| 0.5 + (w[i * 3 + j] >> 16) as f32 / 65536.)
    });
    let exclusions = core::array::from_fn(|i| {
        bytes(seed ^ 0x55, 7 * REGION_BYTES)[i * REGION_BYTES..(i + 1) * REGION_BYTES]
            .try_into()
            .unwrap()
    });
    let hw = words(seed ^ 0x77, 32);
    let history = core::array::from_fn(|i| match v["history"].as_u64().unwrap() {
        0 => [2., 1., 1., 2.],
        1 => [1.; 4],
        2 => {
            if i == groups - 1 {
                [1.; 4]
            } else {
                [2., 1., 1., 2.]
            }
        }
        _ => [0.; 4],
    });
    let names = core::array::from_fn(|i| match v["names"].as_u64().unwrap() {
        0 => name("cfg-A"),
        1 => name(if i == groups - 1 { "cfg-B" } else { "cfg-A" }),
        _ => name(""),
    });
    let mut s = State {
        update: v["update"].as_bool().unwrap(),
        stability_mask: seed as u8,
        history,
        mode_names: names,
        seen: &mut seen,
        active_lights: n as u8,
        complete: seed & 1 != 0,
        lights: &mut lights,
        second_counts: &mut second,
        total_counts: &mut totals,
        previous_pre_gain: gain(seed ^ 0x99),
        grid_valid: seed & 2 != 0,
        second_grid_valid: seed & 4 != 0,
        grid: &mut grid,
        exclusions_valid: seed & 8 != 0,
        exclusions,
        exclusion_aggregate: bytes(seed ^ 0x66, REGION_BYTES).try_into().unwrap(),
        histogram_cache: core::array::from_fn(|i| core::array::from_fn(|j| hw[i * 8 + j])),
        histogram_aggregate: words(seed ^ 0x88, 8).try_into().unwrap(),
    };
    let knots = [0., 1., 3.];
    let weights: [Vec<f32>; 4] = core::array::from_fn(|i| {
        v["weights"][i]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_f64().unwrap() as f32)
            .collect()
    });
    let settings = Settings {
        groups,
        fast_light_count: v["fast_count"].as_u64().unwrap() as u32,
        stability_threshold: v["threshold"].as_f64().unwrap() as f32,
        exclusion_kind: core::array::from_fn(|i| v["exclusion_kind"][i].as_i64().unwrap() as i32),
        exclusion_weight: core::array::from_fn(|i| Curve {
            knots: &knots,
            weights: &weights[i],
        }),
        prior_sample: v["sample"].as_f64().unwrap() as f32,
    };
    let mut out = Vec::new();
    for step in 0..v["frames"].as_u64().unwrap() as usize {
        s.update = v["update"].as_bool().unwrap();
        let f = frame(v, step);
        prepare(&mut s, &Frame(&f), &settings).unwrap();
        out.push(render(&s));
    }
    out.join("|")
}

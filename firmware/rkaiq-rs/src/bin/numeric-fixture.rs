//! Line protocol used by the ARM-original differential harness.
use shieldsigner_rkaiq::*;
use std::io::{self, BufRead};
fn f(s: &str) -> f32 {
    f32::from_bits(u32::from_str_radix(s, 16).unwrap())
}
fn floats(s: &str) -> Vec<f32> {
    s.split(',').map(f).collect()
}
fn emit(values: &[f32]) {
    println!(
        "{}",
        values
            .iter()
            .map(|v| format!("{:08x}", v.to_bits()))
            .collect::<Vec<_>>()
            .join(",")
    );
}
fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let a: Vec<_> = line.split_whitespace().collect();
        match a[0] {
            "interp" => emit(&[interpolate(&floats(a[2]), &floats(a[3]), f(a[1])).unwrap()]),
            "matrix" | "offset" => {
                let x = floats(a[4]);
                let y = floats(a[5]);
                let first = ColorProfile {
                    saturation: f(a[2]),
                    matrix: x[..9].try_into().unwrap(),
                    offsets: x[9..].try_into().unwrap(),
                };
                let second = ColorProfile {
                    saturation: f(a[3]),
                    matrix: y[..9].try_into().unwrap(),
                    offsets: y[9..].try_into().unwrap(),
                };
                if a[0] == "matrix" {
                    emit(&saturation_matrix(f(a[1]), &first, &second).unwrap());
                } else {
                    emit(&saturation_offsets(f(a[1]), &first, &second).unwrap());
                }
            }
            "defect" => {
                let x: Vec<i32> = a[2].split(',').map(|v| v.parse().unwrap()).collect();
                let y: Vec<i32> = a[3].split(',').map(|v| v.parse().unwrap()).collect();
                println!(
                    "{}",
                    defect_pixel_interpolate(
                        a[1].parse().unwrap(),
                        x.as_slice().try_into().unwrap(),
                        y.as_slice().try_into().unwrap()
                    )
                    .unwrap()
                );
            }
            "iso" => {
                use shieldsigner_rkaiq::gain::*;
                let knots: Vec<i32> = a[3].split(',').map(|v| v.parse().unwrap()).collect();
                let table = GainTable {
                    enabled: a[2] == "1",
                    iso: knots.try_into().unwrap(),
                    short: floats(a[4]).try_into().unwrap(),
                    middle: floats(a[5]).try_into().unwrap(),
                };
                let mut e = ExposureSet {
                    mode: HdrMode::Linear,
                    time: [1.; 3],
                    analog_gain: [1.; 3],
                    digital_gain: [1.; 3],
                    iso: [0; 3],
                };
                e.iso[0] = a[1].parse().unwrap();
                let out = select_gain_scales(&table, &e).unwrap();
                println!(
                    "{} {} {} {:08x} {:08x}",
                    out.low,
                    out.high,
                    out.scales.enabled as u8,
                    out.scales.short.to_bits(),
                    out.scales.middle.to_bits()
                );
            }
            "awb" => {
                use shieldsigner_rkaiq::isp32::*;
                let mut state: u32 = a[1].parse().unwrap();
                let mut params = [0u8; PARAMETER_BYTES];
                for value in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *value = (state >> 24) as u8;
                }
                let mut cache = [0u8; 32];
                let values = floats(a[4]);
                let gain = WhiteBalanceGain {
                    red: values[0],
                    green_red: values[1],
                    green_blue: values[2],
                    blue: values[3],
                    position: if a[3] == "0" {
                        ApplyPosition::Gain0
                    } else {
                        ApplyPosition::Gain1
                    },
                };
                apply_awb_gain(&mut params, &mut cache, gain, a[2] == "1").unwrap();
                let hex = |data: &[u8]| {
                    data.iter()
                        .map(|v| format!("{:02x}", v))
                        .collect::<String>()
                };
                println!(
                    "{}:{}:{}",
                    hex(&params[..24]),
                    hex(&params[AWB_GAIN_OFFSET..AWB_GAIN_OFFSET + 32]),
                    hex(&cache)
                );
            }
            "dgain" => {
                use shieldsigner_rkaiq::isp32::*;
                let mut state: u32 = a[1].parse().unwrap();
                let mut params = [0u8; PARAMETER_BYTES];
                for value in &mut params {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *value = (state >> 24) as u8;
                }
                let mut cache = [0u8; AWB_GAIN_BYTES];
                for (i, value) in a[4].split(',').enumerate() {
                    cache[i * 2..i * 2 + 2]
                        .copy_from_slice(&value.parse::<u16>().unwrap().to_le_bytes());
                }
                let values = floats(a[3]);
                let gain = if a[2] == "0" {
                    ExposureDigitalGain::Linear(values[0])
                } else {
                    ExposureDigitalGain::Hdr(values.try_into().unwrap())
                };
                apply_exposure_digital_gain(&mut params, &cache, gain).unwrap();
                let hex = |data: &[u8]| {
                    data.iter()
                        .map(|v| format!("{:02x}", v))
                        .collect::<String>()
                };
                println!(
                    "{}:{}",
                    hex(&params[..24]),
                    hex(&params[AWB_GAIN_OFFSET..AWB_GAIN_OFFSET + 32])
                );
            }
            "aehist" => {
                use shieldsigner_rkaiq::{ae::Bls, ae_histogram::*};
                let mut state: u32 = a[1].parse().unwrap();
                let count: usize = a[2].parse().unwrap();
                let input: Vec<u32> = (0..count)
                    .map(|_| {
                        state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                        state
                    })
                    .collect();
                let read = |s: &str| {
                    let v: Vec<i16> = s.split(',').map(|v| v.parse().unwrap()).collect();
                    Bls {
                        red: v[0],
                        green_red: v[1],
                        green_blue: v[2],
                        blue: v[3],
                    }
                };
                let mode = match a[3] {
                    "2" => Mode::Red,
                    "3" => Mode::Green,
                    "4" => Mode::Blue,
                    _ => Mode::Luma,
                };
                let config = Config {
                    mode,
                    optical_black_rb: a[4].parse().unwrap(),
                    optical_black_green: a[5].parse().unwrap(),
                    black: read(a[6]),
                    gain: read(a[7]),
                    bypass: a[8] == "1",
                };
                let mut output = vec![0xa5a5a5a5; count];
                correct(&input, &mut output, config).unwrap();
                println!(
                    "{}",
                    output
                        .iter()
                        .map(|v| format!("{v:08x}"))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "ae-damping" => {
                use shieldsigner_rkaiq::ae_damping::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |key: &str| v[key].as_f64().unwrap() as f32;
                let history: [f32; 10] = v["history"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_f64().unwrap() as f32)
                    .collect::<Vec<_>>()
                    .try_into()
                    .unwrap();
                let mode = if v["custom"].as_bool().unwrap() {
                    Mode::Custom {
                        scale: n("custom_scale"),
                        middle: n("middle"),
                    }
                } else {
                    Mode::Default
                };
                let result = calculate(
                    n("coefficient"),
                    n("scale"),
                    v["enabled"].as_bool().unwrap(),
                    mode,
                    v["frame"].as_u64().unwrap() as u32,
                    &history,
                )
                .unwrap();
                if let Some(d) = result.diagnostics {
                    println!(
                        "{:08x}:{}:{:08x}:{:08x}:{:08x}",
                        result.coefficient.to_bits(),
                        d.slot,
                        d.trend.to_bits(),
                        d.normalized_trend.to_bits(),
                        d.normalized_current.to_bits()
                    );
                } else {
                    println!("{:08x}:none", result.coefficient.to_bits());
                }
            }
            "ae-decision" => {
                use shieldsigner_rkaiq::ae_decision::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |key: &str| v[key].as_f64().unwrap() as f32;
                let histogram = v["histogram"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|x| x.as_u64().unwrap() as u32)
                    .collect::<Vec<_>>();
                let input = Input {
                    target: n("target"),
                    measured: n("measured"),
                    current_exposure: n("exposure"),
                    tolerance_percent: n("tolerance"),
                    minimum_exposure: n("minimum"),
                    maximum_exposure: n("maximum"),
                    saturated: v["saturated"].as_bool().unwrap(),
                };
                let result = solve(&histogram, input).unwrap();
                println!(
                    "{:08x}:{}",
                    result.exposure.to_bits(),
                    result.saturated as u8
                );
            }
            "iq-exposure" => {
                use shieldsigner_rkaiq::calibration::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let profile = SensorCalibration::from_value(&v["profile"]).unwrap();
                let timing = RuntimeTiming {
                    frame_length: v["frame"].as_u64().unwrap() as u32,
                    pixel_clock_mhz: v["clock"].as_f64().unwrap() as f32,
                    line_length_pixels: v["line"].as_u64().unwrap() as u32,
                };
                let codes = profile
                    .linear_codes(
                        v["time"].as_f64().unwrap() as f32,
                        v["gain"].as_f64().unwrap() as f32,
                        timing,
                    )
                    .unwrap();
                println!("{}:{}", codes.integration_time, codes.gain);
            }
            "sensor-descriptor" => {
                use shieldsigner_rkaiq::sensor_descriptor::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                struct Trace {
                    v: serde_json::Value,
                    trace: Vec<String>,
                }
                impl Trace {
                    fn operation(&mut self, name: &str) -> Result<(), ()> {
                        self.trace.push(name.into());
                        if self.v["fail"]
                            .as_str()
                            .unwrap()
                            .split('+')
                            .any(|v| v == name)
                        {
                            Err(())
                        } else {
                            Ok(())
                        }
                    }
                    fn n(&self, key: &str) -> u32 {
                        self.v[key].as_u64().unwrap() as u32
                    }
                }
                impl Backend for Trace {
                    type Error = ();
                    fn format(&mut self) -> Result<Format, ()> {
                        self.operation("format")?;
                        Ok(Format {
                            width: self.n("width"),
                            height: self.n("height"),
                            media_bus_code: self.n("bus"),
                        })
                    }
                    fn minimum(&mut self, id: u32) -> Result<i32, ()> {
                        let name = match id {
                            HBLANK => "hblank",
                            VBLANK => "vblank",
                            _ => "exposure",
                        };
                        self.operation(name)?;
                        Ok(self.v[name].as_i64().unwrap() as i32)
                    }
                    fn frame_interval(&mut self) -> Result<(u32, u32), ()> {
                        self.operation("interval")?;
                        if self.v["fps_fail"] == true {
                            return Err(());
                        }
                        Ok((self.n("numerator"), self.n("denominator")))
                    }
                    fn pixel_rate(&mut self) -> Result<i64, ()> {
                        self.operation("pixel_rate")?;
                        Ok(self.v["pixel_rate"].as_i64().unwrap())
                    }
                    fn nr_switch(&mut self) -> Result<[u32; 4], ()> {
                        self.operation("nr")?;
                        Ok(core::array::from_fn(|i| {
                            self.v["nr"][i].as_u64().unwrap() as u32
                        }))
                    }
                    fn dcg_ratio(&mut self) -> Result<[u32; 3], ()> {
                        self.operation("dcg")?;
                        Ok(core::array::from_fn(|i| {
                            self.v["dcg"][i].as_u64().unwrap() as u32
                        }))
                    }
                }
                let mut backend = Trace {
                    v,
                    trace: Vec::new(),
                };
                let result = read(&mut backend);
                let (status, data) = match result {
                    Ok(d) => (
                        0,
                        d.bytes()
                            .iter()
                            .map(|v| format!("{v:02x}"))
                            .collect::<String>(),
                    ),
                    Err(_) => (-9, "-".into()),
                };
                println!("{}|{status}|{data}", backend.trace.join(";"));
            }
            "exposure" => {
                use shieldsigner_rkaiq::exposure::*;
                let v: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let n = |name: &str| v[name].as_f64().unwrap() as f32;
                let timing = |key: &str| {
                    let t = &v[key];
                    Timing {
                        minimum: t["minimum"].as_u64().unwrap() as u16,
                        step: t["step"].as_f64().unwrap() as f32,
                        offset: t["offset"].as_f64().unwrap() as f32,
                    }
                };
                let bands: Vec<_> = v["bands"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|b| {
                        let f = |i: usize| b[i].as_f64().unwrap() as f32;
                        GainBand {
                            lower: f(0),
                            upper: f(1),
                            scale: f(2),
                            offset: f(3),
                            exponent: f(4),
                            minimum: f(5),
                            maximum: f(6),
                        }
                    })
                    .collect();
                let cfg = Calibration {
                    gain: if v["model"] == 0 {
                        GainModel::Bands(&bands)
                    } else {
                        GainModel::Logarithmic
                    },
                    factors: core::array::from_fn(|i| v["factors"][i].as_f64().unwrap() as f32),
                    frame_length: n("frame_length"),
                    pixel_clock_mhz: n("pixel_clock"),
                    line_length_pixels: n("line_length"),
                    linear: timing("linear"),
                    hdr: [timing("hdr2"), timing("hdr3")],
                    linear_dcg_ratio: n("linear_ratio"),
                    hdr_dcg_ratio: n("hdr_ratio"),
                };
                let mode = match v["mode"].as_u64().unwrap() {
                    0 => Mode::Linear,
                    1 => Mode::HdrTwo,
                    _ => Mode::HdrThree,
                };
                let result = convert(
                    n("time"),
                    n("gain"),
                    mode,
                    v["dcg"].as_i64().unwrap() as i32,
                    cfg,
                )
                .unwrap();
                println!("{}:{}", result.integration_time, result.gain);
            }
            "sensor-linear" => {
                use shieldsigner_rkaiq::sensor::*;
                struct Trace {
                    descriptor: Descriptor,
                    trace: Vec<String>,
                    fail: usize,
                    calls: usize,
                }
                impl Trace {
                    fn operation(&mut self, text: String) -> Result<(), ()> {
                        self.trace.push(text);
                        self.calls += 1;
                        if self.fail == self.calls {
                            Err(())
                        } else {
                            Ok(())
                        }
                    }
                }
                impl Backend for Trace {
                    type Error = ();
                    fn descriptor(&mut self) -> Result<Descriptor, ()> {
                        self.trace.push("descriptor".into());
                        Ok(self.descriptor)
                    }
                    fn control(&mut self, id: u32, value: i32) -> Result<(), ()> {
                        self.operation(format!("control:{id:08x}:{value}"))
                    }
                    fn conversion_gain(&mut self, value: u32) -> Result<(), ()> {
                        self.operation(format!("dcg:{value}"))
                    }
                }
                let mut backend = Trace {
                    descriptor: Descriptor {
                        line_periods_per_field: a[1].parse().unwrap(),
                        output_height: a[2].parse().unwrap(),
                    },
                    trace: Vec::new(),
                    fail: a[10].parse().unwrap(),
                    calls: 0,
                };
                let exposure = LinearExposure {
                    frame_length_lines: a[3].parse().unwrap(),
                    dcg_mode: a[4].parse().unwrap(),
                    analogue_gain_code: a[5].parse().unwrap(),
                    digital_gain_code: a[6].parse().unwrap(),
                    coarse_integration_time: a[7].parse().unwrap(),
                };
                let mut mirror = if a[8] == "1" {
                    Some(a[9].parse().unwrap())
                } else {
                    None
                };
                let status = if program_linear(&mut backend, exposure, &mut mirror).is_ok() {
                    0
                } else {
                    -9
                };
                println!(
                    "{}|{status}|{}",
                    backend.trace.join(";"),
                    mirror.map(|v| v.to_string()).unwrap_or_else(|| "-".into())
                );
            }
            "aebig" => {
                use shieldsigner_rkaiq::ae::*;
                let mut state: u32 = a[1].parse().unwrap();
                fn next(s: &mut u32) -> u32 {
                    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                    *s
                }
                let input = core::array::from_fn(|_| next(&mut state));
                let raw_sums = RawSums {
                    red: core::array::from_fn(|_| next(&mut state)),
                    green: core::array::from_fn(|_| next(&mut state)),
                    blue: core::array::from_fn(|_| next(&mut state)),
                };
                let initial = core::array::from_fn(|_| (next(&mut state) >> 24) as u8);
                let mut output = BigGrid::from_bytes(&initial);
                let weights = core::array::from_fn(|_| (next(&mut state) >> 24) as u8);
                let read = |s: &str| {
                    let v: Vec<i16> = s.split(',').map(|v| v.parse().unwrap()).collect();
                    Bls {
                        red: v[0],
                        green_red: v[1],
                        green_blue: v[2],
                        blue: v[3],
                    }
                };
                let selection = match a[2] {
                    "1" => Selection::Luma,
                    "2" => Selection::Red,
                    "4" => Selection::Green,
                    "8" => Selection::Blue,
                    "14" => Selection::Rgb,
                    _ => Selection::RgbAndLuma,
                };
                let range = if a[3] == "0" {
                    LumaRange::Full
                } else {
                    LumaRange::Limited
                };
                let mut mean = a[7].parse().unwrap();
                let pixels = a[6]
                    .split(',')
                    .map(|v| v.parse().unwrap())
                    .collect::<Vec<u32>>()
                    .try_into()
                    .unwrap();
                correct_big_grid(
                    &input,
                    raw_sums,
                    &mut output,
                    &mut mean,
                    &weights,
                    selection,
                    range,
                    read(a[4]),
                    read(a[5]),
                    pixels,
                )
                .unwrap();
                println!(
                    "{}:{mean}",
                    output
                        .bytes()
                        .iter()
                        .map(|v| format!("{v:02x}"))
                        .collect::<String>()
                );
            }
            "aegrid" => {
                use shieldsigner_rkaiq::ae::*;
                let mut state: u32 = a[1].parse().unwrap();
                fn next(s: &mut u32) -> u32 {
                    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                    *s
                }
                let input = core::array::from_fn(|_| next(&mut state));
                let mut output =
                    Grid::from_words(core::array::from_fn(|_| (next(&mut state) >> 16) as u16));
                let weights = core::array::from_fn(|_| (next(&mut state) >> 24) as u8);
                let read_bls = |s: &str| {
                    let v: Vec<i16> = s.split(',').map(|v| v.parse().unwrap()).collect();
                    Bls {
                        red: v[0],
                        green_red: v[1],
                        green_blue: v[2],
                        blue: v[3],
                    }
                };
                let mut mean = a[6].parse().unwrap();
                let selection = match a[2] {
                    "1" => Selection::Luma,
                    "2" => Selection::Red,
                    "4" => Selection::Green,
                    "8" => Selection::Blue,
                    "14" => Selection::Rgb,
                    _ => Selection::RgbAndLuma,
                };
                let range = if a[3] == "0" {
                    LumaRange::Full
                } else {
                    LumaRange::Limited
                };
                correct_lite_grid(
                    &input,
                    &mut output,
                    &mut mean,
                    &weights,
                    selection,
                    range,
                    read_bls(a[4]),
                    read_bls(a[5]),
                )
                .unwrap();
                println!(
                    "{}:{mean}",
                    output
                        .words()
                        .iter()
                        .map(|v| v.to_string())
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            "statistics" => {
                use shieldsigner_rkaiq::statistics::*;
                let mut state: u32 = a[1].parse().unwrap();
                let mut bytes = [0u8; BUFFER_BYTES];
                for b in &mut bytes {
                    state = state.wrapping_mul(1664525).wrapping_add(1013904223);
                    *b = (state >> 24) as u8;
                }
                bytes[MEASUREMENT_OFFSET..MEASUREMENT_OFFSET + 4]
                    .copy_from_slice(&0x20u32.to_le_bytes());
                let stats = Statistics::parse(&bytes).unwrap();
                let grid = stats
                    .awb()
                    .unwrap()
                    .map(|v| format!("{},{},{},{}", v.red, v.green, v.blue, v.white_points))
                    .collect::<Vec<_>>()
                    .join(",");
                let sums = stats
                    .awb_sums()
                    .unwrap()
                    .map(|v| {
                        format!(
                            "{},{},{},{},{},{},{}",
                            v.red_normal,
                            v.blue_normal,
                            v.points_normal,
                            v.points_second,
                            v.red_big,
                            v.blue_big,
                            v.points_big
                        )
                    })
                    .collect::<Vec<_>>()
                    .join(",");
                let hist = stats
                    .awb_luma_histogram()
                    .unwrap()
                    .map(|v| v.to_string())
                    .collect::<Vec<_>>()
                    .join(",");
                println!("{}:{grid}:{sums}:{hist}", stats.frame_id());
            }
            "binding" => {
                use shieldsigner_rkaiq::discovery::*;
                let input: serde_json::Value = serde_json::from_str(a[1]).unwrap();
                let sensors: Vec<_> = input["sensors"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|s| {
                        let paths = |key: &str| {
                            s[key]
                                .as_array()
                                .unwrap()
                                .iter()
                                .map(|v| v.as_str().unwrap())
                                .collect::<Vec<_>>()
                        };
                        Sensor {
                            name: s["name"].as_str().unwrap(),
                            has_isp: s["isp"].as_bool().unwrap(),
                            isp_paths: paths("paths").try_into().unwrap(),
                            cif_paths: if s["cif"].is_null() {
                                None
                            } else {
                                Some(paths("cif").try_into().unwrap())
                            },
                            media: match s["media"].as_i64().unwrap() {
                                -1 => MediaStatus::Missing,
                                -2 => MediaStatus::OpenFailed,
                                -3 => MediaStatus::EntityUnavailable,
                                -4 => MediaStatus::NoLinks,
                                n => MediaStatus::FirstLinkFlags(n as u32),
                            },
                        }
                    })
                    .collect();
                println!(
                    "{}",
                    serde_json::to_string(&bound_sensor(&sensors, input["query"].as_str()))
                        .unwrap()
                );
            }
            "engine" => {
                use shieldsigner_rkaiq::engine::*;
                struct Trace(Vec<String>);
                impl Backend for Trace {
                    type Error = ();
                    fn initialize(&mut self, sensor: &str, iq: &str) -> Result<(), ()> {
                        self.0.push(format!("init:{sensor}:{iq}"));
                        Ok(())
                    }
                    fn listen_in_library(&mut self, enabled: bool) -> Result<(), ()> {
                        self.0.push(format!("listen:{}", enabled as u8));
                        Ok(())
                    }
                    fn multiple_cameras(&mut self) -> Result<(), ()> {
                        self.0.push("multicam:1".into());
                        Ok(())
                    }
                    fn prepare_linear(&mut self, w: u32, h: u32) -> Result<(), ()> {
                        self.0.push(format!("prepare:{w}:{h}:0"));
                        Ok(())
                    }
                    fn subscribe(&mut self, e: u32) -> Result<(), ()> {
                        self.0.push(format!("subscribe:{e}"));
                        Ok(())
                    }
                    fn start(&mut self) -> Result<(), ()> {
                        self.0.push("start".into());
                        Ok(())
                    }
                    fn stop(&mut self, keep: bool) -> Result<(), ()> {
                        self.0.push(format!("stop:{}", keep as u8));
                        Ok(())
                    }
                }
                let config = Config {
                    sensor: a[4],
                    iq_directory: a[5],
                    width: a[2].parse().unwrap(),
                    height: a[3].parse().unwrap(),
                    multiple_cameras: a[1] == "1",
                };
                let mut engine = Engine::prepare(Trace(Vec::new()), config).unwrap();
                if a[6] != "-" {
                    for e in a[6].split(',') {
                        engine.on_event(e.parse().unwrap()).unwrap();
                    }
                }
                println!("{}", engine.backend().0.join(";"));
            }
            "gain" => {
                use shieldsigner_rkaiq::gain::*;
                let mode = match a[1] {
                    "0" => HdrMode::Linear,
                    "1" => HdrMode::TwoFrame,
                    "2" => HdrMode::ThreeFrame,
                    _ => panic!("invalid HDR mode"),
                };
                let e = ExposureSet {
                    mode,
                    time: floats(a[5]).try_into().unwrap(),
                    analog_gain: floats(a[6]).try_into().unwrap(),
                    digital_gain: floats(a[7]).try_into().unwrap(),
                    iso: a[8]
                        .split(',')
                        .map(|v| v.parse().unwrap())
                        .collect::<Vec<_>>()
                        .try_into()
                        .unwrap(),
                };
                let scales = GainScales {
                    enabled: a[2] == "1",
                    short: f(a[3]),
                    middle: f(a[4]),
                };
                let out = pack_gain_registers(scales, e)
                    .unwrap()
                    .little_endian_bytes();
                println!(
                    "{}",
                    out.iter().map(|v| format!("{:02x}", v)).collect::<String>()
                );
            }
            "quant" => println!("{}", quantize_gain(f(a[1]), a[2].parse().unwrap()).unwrap()),
            "lut" => {
                let mut state: u32 = a[2].parse().unwrap();
                fn next(s: &mut u32) -> u16 {
                    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
                    (*s >> 16) as u16
                }
                let mut first = [0; LUT_VALUES];
                let mut second = [0; LUT_VALUES];
                let mut out = [0; LUT_VALUES];
                for v in &mut first {
                    *v = next(&mut state);
                }
                for v in &mut second {
                    *v = next(&mut state);
                }
                blend_lut(f(a[1]), &first, &second, &mut out).unwrap();
                println!(
                    "{}",
                    out.iter()
                        .map(|v| format!("{:04x}", v))
                        .collect::<Vec<_>>()
                        .join(",")
                );
            }
            _ => panic!("unknown fixture operation"),
        }
    }
}

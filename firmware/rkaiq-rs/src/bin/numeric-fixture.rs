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

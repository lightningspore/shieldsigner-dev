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

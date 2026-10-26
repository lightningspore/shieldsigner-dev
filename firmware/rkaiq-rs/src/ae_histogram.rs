//! Histogram redistribution recovered from calcAecHistBinStatsV32.
use crate::{ae::Bls, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub enum Mode {
    Luma,
    Red,
    Green,
    Blue,
}
#[derive(Clone, Copy, Debug)]
pub struct Config {
    pub mode: Mode,
    pub optical_black_rb: u16,
    pub optical_black_green: u16,
    pub black: Bls,
    pub gain: Bls,
    pub bypass: bool,
}
/// Correct one 64- or 256-bin histogram, preserving native u32 counter wrapping.
/// Validates all destination indices before writing. Bypass copies without
/// reading calibration fields. Invalid gain divisors/negative indices are errors.
pub fn correct(input: &[u32], output: &mut [u32], config: Config) -> Result<(), InvalidInput> {
    let count = input.len();
    if output.len() != count || !matches!(count, 64 | 256) {
        return Err(InvalidInput::Length);
    }
    if config.bypass {
        output.copy_from_slice(input);
        return Ok(());
    }
    let rb = (config.optical_black_rb as i32) >> 2;
    let green = (config.optical_black_green as i32) >> 4;
    let (threshold, scale, offset, divisor) = match config.mode {
        Mode::Red | Mode::Green | Mode::Blue => {
            let (ob, black, gain) = match config.mode {
                Mode::Red => (rb, (config.black.red as i32) >> 2, config.gain.red),
                Mode::Green => (
                    green,
                    (config.black.green_red as i32) >> 4,
                    config.gain.green_red,
                ),
                Mode::Blue => (rb, (config.black.blue as i32) >> 2, config.gain.blue),
                _ => unreachable!(),
            };
            let threshold = ob + black;
            (
                threshold,
                gain as u16 as i32,
                (threshold * gain as i32) as i16 as i32,
                256,
            )
        }
        Mode::Luma => {
            let gains = [
                config.gain.red as i32,
                config.gain.green_red as i32,
                config.gain.blue as i32,
            ];
            if gains.contains(&0) {
                return Err(InvalidInput::DegenerateRange);
            }
            let ob = ((green * 587 + 500 + rb * 413) as u16 as i32) / 1000;
            let black = (((config.black.green_red as i32 >> 4) * 587
                + (config.black.red as i32 >> 2) * 299
                + 500
                + (config.black.blue as i32 >> 2) * 114) as i16 as i32)
                / 1000;
            let divisor = (7655 / gains[0] + 15027 / gains[1] + 2919 / gains[2]) as u16 as i32;
            if divisor == 0 {
                return Err(InvalidInput::DegenerateRange);
            }
            let threshold = ob + black;
            (threshold, 100, (threshold * 100) as i16 as i32, divisor)
        }
    };
    let mut indices = [0usize; 256];
    for (i, index) in indices[..count].iter_mut().enumerate() {
        let value = if count == 256 {
            i as i32
        } else {
            (i * 4 + 2) as i32
        };
        let mapped = if value <= threshold {
            0
        } else {
            (value * scale + (divisor / 2 - offset)) / divisor
        };
        let mapped = if count == 256 {
            mapped.min(255)
        } else {
            mapped.min(254) / 4
        };
        if mapped < 0 || mapped as usize >= count {
            return Err(InvalidInput::GainRange);
        }
        *index = mapped as usize;
    }
    output.fill(0);
    for (value, index) in input.iter().zip(indices) {
        output[index] = output[index].wrapping_add(*value);
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    fn config() -> Config {
        Config {
            mode: Mode::Luma,
            optical_black_rb: 0,
            optical_black_green: 0,
            black: Bls {
                red: 0,
                green_red: 0,
                green_blue: 0,
                blue: 0,
            },
            gain: Bls {
                red: 0,
                green_red: 0,
                green_blue: 0,
                blue: 0,
            },
            bypass: false,
        }
    }
    #[test]
    fn rejects_invalid_divisor_atomically_but_bypass_needs_no_gain() {
        let mut output = [77; 64];
        assert!(correct(&[1; 64], &mut output, config()).is_err());
        assert_eq!(output, [77; 64]);
        let mut cfg = config();
        cfg.bypass = true;
        correct(&[1; 64], &mut output, cfg).unwrap();
        assert_eq!(output, [1; 64]);
    }
    #[test]
    fn merged_counts_wrap_like_native_registers() {
        let mut cfg = config();
        cfg.mode = Mode::Red;
        let mut output = [0; 64];
        let mut input = [0; 64];
        input[0] = u32::MAX;
        input[1] = 2;
        correct(&input, &mut output, cfg).unwrap();
        assert_eq!(output[0], 1);
        assert!(output[1..].iter().all(|v| *v == 0));
    }
    #[test]
    fn negative_destination_is_rejected_before_any_output_changes() {
        let mut cfg = config();
        cfg.mode = Mode::Red;
        cfg.black.red = -200;
        cfg.gain.red = 1000;
        let mut output = [77; 256];
        assert!(correct(&[1; 256], &mut output, cfg).is_err());
        assert_eq!(output, [77; 256]);
    }
}

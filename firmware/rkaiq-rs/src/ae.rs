//! AE0 (5×5) measurement correction recovered from calcAecLiteWinStatsV32.
//! This computes corrected grid values/weighted mean, not an exposure decision.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Bls {
    pub red: i16,
    pub green_red: i16,
    pub green_blue: i16,
    pub blue: i16,
}
#[derive(Clone, Copy, Debug)]
pub enum Selection {
    RgbAndLuma,
    Luma,
    Red,
    Green,
    Blue,
    Rgb,
}
#[derive(Clone, Copy, Debug)]
pub enum LumaRange {
    Full,
    Limited,
}
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Grid {
    pub red: [u16; 25],
    pub green: [u16; 25],
    pub blue: [u16; 25],
    pub luma: [u16; 25],
}
impl Grid {
    pub fn from_words(words: [u16; 100]) -> Self {
        let mut out = Self::default();
        out.red.copy_from_slice(&words[..25]);
        out.green.copy_from_slice(&words[25..50]);
        out.blue.copy_from_slice(&words[50..75]);
        out.luma.copy_from_slice(&words[75..]);
        out
    }
    pub fn words(self) -> [u16; 100] {
        let mut out = [0; 100];
        out[..25].copy_from_slice(&self.red);
        out[25..50].copy_from_slice(&self.green);
        out[50..75].copy_from_slice(&self.blue);
        out[75..].copy_from_slice(&self.luma);
        out
    }
}
fn corrected(value: u16, gain: i16, black: i16) -> i32 {
    (value as i32 * gain as i32) / 256 - black as i32
}
fn luma(red: i32, green: i32, blue: i32, range: LumaRange) -> u16 {
    let (r, g, b, offset) = match range {
        LumaRange::Full => (0.299f32, 0.587f32, 0.114f32, 0.),
        LumaRange::Limited => (0.25, 0.5, 0.1094, 16.),
    };
    let value = libm::fmaf(blue as f32, b, libm::fmaf(red as f32, r, green as f32 * g)) + offset;
    libm::roundf(value).clamp(0., 255.) as u16
}
/// Mutates only fields written by the selected original branch; RGB-only keeps
/// luma/mean untouched. The second green component of each BLS record is unused.
/// Zero total weight is rejected before mutation except in RGB-only mode, which
/// does not compute a mean. All gain/BLS operands retain signed 16-bit behavior.
pub fn correct_lite_grid(
    input: &[u32; 25],
    output: &mut Grid,
    mean: &mut u16,
    weights: &[u8; 25],
    selection: Selection,
    range: LumaRange,
    black: Bls,
    gain: Bls,
) -> Result<(), InvalidInput> {
    let total: u32 = weights.iter().map(|w| *w as u32).sum();
    if total == 0 && !matches!(selection, Selection::Rgb) {
        return Err(InvalidInput::DegenerateRange);
    }
    let mut weighted = 0u32;
    for i in 0..25 {
        let raw = crate::statistics::ae_sample(input[i]);
        let red = corrected(raw.red, gain.red, black.red);
        let green = corrected(raw.green, gain.green_red, black.green_red);
        let blue = corrected(raw.blue, gain.blue, black.blue);
        let (r, g, b) = (
            red.clamp(0, 1023) as u16,
            green.clamp(0, 4095) as u16,
            blue.clamp(0, 1023) as u16,
        );
        let sample = match selection {
            Selection::Red => {
                output.red[i] = r;
                r >> 2
            }
            Selection::Green => {
                output.green[i] = g;
                g >> 4
            }
            Selection::Blue => {
                output.blue[i] = b;
                b >> 2
            }
            Selection::Luma => {
                let y = luma(red >> 2, green >> 4, blue >> 2, range);
                output.luma[i] = y;
                y
            }
            Selection::Rgb => {
                output.red[i] = r;
                output.green[i] = g;
                output.blue[i] = b;
                0
            }
            Selection::RgbAndLuma => {
                output.red[i] = r;
                output.green[i] = g;
                output.blue[i] = b;
                let y = luma((r >> 2) as i32, (g >> 4) as i32, (b >> 2) as i32, range);
                output.luma[i] = y;
                y
            }
        };
        weighted += sample as u32 * weights[i] as u32;
    }
    if !matches!(selection, Selection::Rgb) {
        *mean = libm::roundf((weighted as f32 * 256.) / (total as f32)) as u16;
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn zero_weights_fail_atomically_except_rgb_only() {
        let unity = Bls {
            red: 256,
            green_red: 256,
            green_blue: 256,
            blue: 256,
        };
        let black = Bls {
            red: 0,
            green_red: 0,
            green_blue: 0,
            blue: 0,
        };
        let mut grid = Grid::from_words([123; 100]);
        let original = grid;
        let mut mean = 77;
        assert!(correct_lite_grid(
            &[u32::MAX; 25],
            &mut grid,
            &mut mean,
            &[0; 25],
            Selection::Luma,
            LumaRange::Full,
            black,
            unity
        )
        .is_err());
        assert_eq!(grid, original);
        assert_eq!(mean, 77);
        correct_lite_grid(
            &[u32::MAX; 25],
            &mut grid,
            &mut mean,
            &[0; 25],
            Selection::Rgb,
            LumaRange::Full,
            black,
            unity,
        )
        .unwrap();
        assert_eq!(mean, 77);
        assert_eq!(grid.luma, [123; 25]);
        assert_eq!(grid.red, [1023; 25]);
    }
}

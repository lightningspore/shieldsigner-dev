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
    correct_grid(
        input,
        [
            &mut output.red,
            &mut output.green,
            &mut output.blue,
            &mut output.luma,
        ],
        mean,
        weights,
        selection,
        range,
        black,
        gain,
    )
}
fn correct_grid(
    input: &[u32],
    output: [&mut [u16]; 4],
    mean: &mut u16,
    weights: &[u8],
    selection: Selection,
    range: LumaRange,
    black: Bls,
    gain: Bls,
) -> Result<(), InvalidInput> {
    let [red_out, green_out, blue_out, luma_out] = output;
    let total: u32 = weights.iter().map(|w| *w as u32).sum();
    if total == 0 && !matches!(selection, Selection::Rgb) {
        return Err(InvalidInput::DegenerateRange);
    }
    let mut weighted = 0u32;
    for i in 0..input.len() {
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
                red_out[i] = r;
                r >> 2
            }
            Selection::Green => {
                green_out[i] = g;
                g >> 4
            }
            Selection::Blue => {
                blue_out[i] = b;
                b >> 2
            }
            Selection::Luma => {
                let y = luma(red >> 2, green >> 4, blue >> 2, range);
                luma_out[i] = y;
                y
            }
            Selection::Rgb => {
                red_out[i] = r;
                green_out[i] = g;
                blue_out[i] = b;
                0
            }
            Selection::RgbAndLuma => {
                red_out[i] = r;
                green_out[i] = g;
                blue_out[i] = b;
                let y = luma((r >> 2) as i32, (g >> 4) as i32, (b >> 2) as i32, range);
                luma_out[i] = y;
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

pub const BIG_RECORD_BYTES: usize = 1928;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BigGrid {
    pub red: [u16; 225],
    pub green: [u16; 225],
    pub blue: [u16; 225],
    pub luma: [u16; 225],
    pub window_channels: [[u16; 4]; 4],
    pub red_sums: [u64; 4],
    pub green_sums: [u64; 4],
    pub blue_sums: [u64; 4],
}
impl BigGrid {
    pub fn from_bytes(bytes: &[u8; BIG_RECORD_BYTES]) -> Self {
        let words: [u16; 916] = core::array::from_fn(|i| {
            u16::from_le_bytes(bytes[i * 2..i * 2 + 2].try_into().unwrap())
        });
        let sums: [u64; 12] = core::array::from_fn(|i| {
            u64::from_le_bytes(bytes[1832 + i * 8..1840 + i * 8].try_into().unwrap())
        });
        Self {
            red: words[..225].try_into().unwrap(),
            green: words[225..450].try_into().unwrap(),
            blue: words[450..675].try_into().unwrap(),
            luma: words[675..900].try_into().unwrap(),
            window_channels: core::array::from_fn(|i| {
                words[900 + i * 4..904 + i * 4].try_into().unwrap()
            }),
            red_sums: sums[..4].try_into().unwrap(),
            green_sums: sums[4..8].try_into().unwrap(),
            blue_sums: sums[8..].try_into().unwrap(),
        }
    }
    pub fn bytes(&self) -> [u8; BIG_RECORD_BYTES] {
        let mut bytes = [0; BIG_RECORD_BYTES];
        for (i, value) in self
            .red
            .iter()
            .chain(&self.green)
            .chain(&self.blue)
            .chain(&self.luma)
            .chain(self.window_channels.iter().flatten())
            .enumerate()
        {
            bytes[i * 2..i * 2 + 2].copy_from_slice(&value.to_le_bytes());
        }
        for (i, value) in self
            .red_sums
            .iter()
            .chain(&self.green_sums)
            .chain(&self.blue_sums)
            .enumerate()
        {
            bytes[1832 + i * 8..1840 + i * 8].copy_from_slice(&value.to_le_bytes());
        }
        bytes
    }
}
#[derive(Clone, Copy, Debug)]
pub struct RawSums {
    pub red: [u32; 4],
    pub green: [u32; 4],
    pub blue: [u32; 4],
}
fn corrected_sum(raw: u32, gain: i16, black: i16, pixels: u32, shift: u32, maximum: u64) -> u64 {
    // Preserve the binary's signed product, logical 64-bit shift, and wrapped
    // *32-bit* BLS×pixel term rather than replacing them with signed arithmetic.
    let scaled = ((raw as i64 * gain as i64) as u64) >> 8;
    let subtraction = (pixels >> shift).wrapping_mul(black as u32) as u64;
    let result = scaled.wrapping_sub(subtraction) as i64;
    if result < 0 {
        0
    } else {
        (result as u64).min(maximum)
    }
}
/// Reconstruct calcAecBigWinStatsV32 (ELF 0x86444). All selection branches also
/// update four subwindow RGB sums. The window-channel means remain untouched.
pub fn correct_big_grid(
    input: &[u32; 225],
    raw_sums: RawSums,
    output: &mut BigGrid,
    mean: &mut u16,
    weights: &[u8; 225],
    selection: Selection,
    range: LumaRange,
    black: Bls,
    gain: Bls,
    pixels: [u32; 4],
) -> Result<(), InvalidInput> {
    correct_grid(
        input,
        [
            &mut output.red,
            &mut output.green,
            &mut output.blue,
            &mut output.luma,
        ],
        mean,
        weights,
        selection,
        range,
        black,
        gain,
    )?;
    for i in 0..4 {
        output.red_sums[i] = corrected_sum(
            raw_sums.red[i],
            gain.red,
            black.red,
            pixels[i],
            2,
            0x1fffffff,
        );
        output.green_sums[i] = corrected_sum(
            raw_sums.green[i],
            gain.green_red,
            black.green_blue,
            pixels[i],
            1,
            u32::MAX as u64,
        );
        output.blue_sums[i] = corrected_sum(
            raw_sums.blue[i],
            gain.blue,
            black.blue,
            pixels[i],
            2,
            0x1fffffff,
        );
    }
    Ok(())
}

#[cfg(test)]
mod big_tests {
    use super::*;
    #[test]
    fn preserves_native_logical_shift_and_unsigned_black_product() {
        assert_eq!(corrected_sum(1, -1, 0, 0, 2, 0x1fffffff), 0x1fffffff);
        assert_eq!(corrected_sum(0, 256, -1, 4, 2, 0x1fffffff), 0);
        assert_eq!(corrected_sum(1, 256, 0, 0, 2, 0x1fffffff), 1);
    }
    #[test]
    fn invalid_mean_weights_leave_entire_big_record_unchanged() {
        let mut grid = BigGrid::from_bytes(&[7; BIG_RECORD_BYTES]);
        let original = grid;
        let mut mean = 9;
        let values = Bls {
            red: 256,
            green_red: 256,
            green_blue: 256,
            blue: 256,
        };
        let sums = RawSums {
            red: [1; 4],
            green: [2; 4],
            blue: [3; 4],
        };
        assert!(correct_big_grid(
            &[0; 225],
            sums,
            &mut grid,
            &mut mean,
            &[0; 225],
            Selection::Luma,
            LumaRange::Full,
            values,
            values,
            [4; 4]
        )
        .is_err());
        assert_eq!(grid, original);
        assert_eq!(mean, 9);
    }
}

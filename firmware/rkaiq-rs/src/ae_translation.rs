//! Minimum linear/source-1/full-range path of translateAecStatsV32. The supplied
//! parameter snapshot is explicit; associating it with a frame remains external.
use crate::{
    ae::{self, Bls},
    ae_histogram,
    isp32::*,
    isp_ae_measurement, isp_black_level, statistics, InvalidInput,
};
#[derive(Clone, Copy, Debug)]
struct Correction {
    pub grid_black: Bls,
    pub histogram_black: Bls,
    pub gain: Bls,
    pub optical_black: u16,
}
fn word(b: &[u8], o: usize) -> u16 {
    u16::from_le_bytes(b[o..o + 2].try_into().unwrap())
}
fn scaled(gain: i16, value: i32) -> i16 {
    let product = (gain as i32).wrapping_mul(value);
    let rounded = product.wrapping_add(128);
    let adjusted = if rounded < 0 {
        product.wrapping_add(383)
    } else {
        rounded
    };
    ((adjusted as u32) >> 8) as i16
}
fn correction(bls: &[u8; 44], awb: &[u8; 32], hdr_mode: i32) -> Correction {
    let ob = word(bls, 36);
    let divisor = (word(bls, 38) >> 8).max(1) as i32;
    let stage = |i: usize| {
        if bls[2] != 0 && hdr_mode < 1 {
            (word(bls, 28 + i * 2) as i16 as i32) / divisor
        } else {
            0
        }
    };
    let histogram_black = Bls {
        red: (stage(0) >> 2) as i16,
        green_red: stage(1) as i16,
        green_blue: stage(2) as i16,
        blue: (stage(3) >> 2) as i16,
    };
    let gain = Bls {
        red: word(awb, 6).max(256) as i16,
        green_red: word(awb, 2).max(256) as i16,
        green_blue: word(awb, 0).max(256) as i16,
        blue: word(awb, 4).max(256) as i16,
    };
    let grid_black = Bls {
        red: scaled(gain.red, histogram_black.red as i32 + (ob >> 2) as i32),
        green_red: scaled(gain.green_red, histogram_black.green_red as i32 + ob as i32),
        green_blue: scaled(
            gain.green_blue,
            histogram_black.green_blue as i32 + ob as i32,
        ),
        blue: scaled(gain.blue, histogram_black.blue as i32 + (ob >> 2) as i32),
    };
    Correction {
        grid_black,
        histogram_black,
        gain,
        optical_black: ob,
    }
}
pub struct Measurement {
    pub mean: u16,
    pub grid: ae::BigGrid,
    pub histogram: [u32; 256],
}
pub fn measure_linear(
    bytes: &[u8],
    params: &[u8; PARAMETER_BYTES],
) -> Result<Option<Measurement>, InvalidInput> {
    let stats = statistics::Statistics::parse(bytes).map_err(|_| InvalidInput::Length)?;
    if stats.measurements() & ((1 << 8) | (1 << 12)) != ((1 << 8) | (1 << 12)) {
        return Ok(None);
    }
    let a = isp_ae_measurement::AE_OFFSET;
    let h = isp_ae_measurement::HISTOGRAM_OFFSET;
    if params[a] != 1
        || params[a + 10] != 1
        || params[a + 102] != 3
        || params[h + 41 + 3] != 5
        || params[h + 41 + 5..h + 41 + 9] != [0, 29, 75, 77]
    {
        return Err(InvalidInput::Exposure);
    }
    let correction = correction(
        params[isp_black_level::OFFSET..isp_black_level::OFFSET + 44]
            .try_into()
            .unwrap(),
        params[AWB_GAIN_OFFSET..AWB_GAIN_OFFSET + 32]
            .try_into()
            .unwrap(),
        0,
    );
    let read = |o| u32::from_le_bytes(bytes[o..o + 4].try_into().unwrap());
    let input = core::array::from_fn(|i| read(0x390 + i * 4));
    let sums = ae::RawSums {
        red: core::array::from_fn(|i| read(0xb98 + i * 4)),
        green: core::array::from_fn(|i| read(0xb98 + 16 + i * 4)),
        blue: core::array::from_fn(|i| read(0xb98 + 32 + i * 4)),
    };
    let pixels = core::array::from_fn(|i| {
        let o = a + 10 + 14 + i * 8;
        word(params, o + 4) as u32 * word(params, o + 6) as u32
    });
    let weights = params[h + 58..h + 283].try_into().unwrap();
    let mut mean = 0;
    let mut grid = ae::BigGrid::from_bytes(&[0; ae::BIG_RECORD_BYTES]);
    ae::correct_big_grid(
        &input,
        sums,
        &mut grid,
        &mut mean,
        weights,
        ae::Selection::Luma,
        ae::LumaRange::Full,
        correction.grid_black,
        correction.gain,
        pixels,
    )?;
    let raw_histogram: [u32; 256] = core::array::from_fn(|i| read(0x1400 + i * 4));
    let mut histogram = [0; 256];
    ae_histogram::correct(
        &raw_histogram,
        &mut histogram,
        ae_histogram::Config {
            mode: ae_histogram::Mode::Luma,
            optical_black_rb: correction.optical_black >> 2,
            optical_black_green: correction.optical_black,
            black: correction.histogram_black,
            gain: correction.gain,
            bypass: false,
        },
    )?;
    Ok(Some(Measurement {
        mean,
        grid,
        histogram,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn requires_both_primary_validity_flags() {
        let mut raw = [0u8; statistics::BUFFER_BYTES];
        let params = [0; PARAMETER_BYTES];
        for flags in [0u32, 1 << 8, 1 << 12] {
            raw[statistics::MEASUREMENT_OFFSET..statistics::MEASUREMENT_OFFSET + 4]
                .copy_from_slice(&flags.to_le_bytes());
            assert!(measure_linear(&raw, &params).unwrap().is_none());
        }
        assert!(measure_linear(&raw[..16], &params).is_err());
    }
}

//! Gain-module register conversion recovered from ELF address 0xe7a68.
//! Source ABI corroboration: SDK RK_GAIN_Fix_V2_s and Again_ExpInfo_V2_s headers.
use crate::{quantize_gain, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub enum HdrMode {
    Linear,
    TwoFrame,
    ThreeFrame,
}
impl HdrMode {
    fn last(self) -> usize {
        match self {
            Self::Linear => 0,
            Self::TwoFrame => 1,
            Self::ThreeFrame => 2,
        }
    }
}
#[derive(Clone, Copy, Debug)]
pub struct ExposureSet {
    pub mode: HdrMode,
    pub time: [f32; 3],
    pub analog_gain: [f32; 3],
    pub digital_gain: [f32; 3],
    pub iso: [i32; 3],
}
#[derive(Clone, Copy, Debug)]
pub struct GainScales {
    pub enabled: bool,
    pub short: f32,
    pub middle: f32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct GainRegisters {
    pub controls: [u8; 13],
    pub gain: [u32; 3],
}
impl GainRegisters {
    /// Kernel-facing SDK register record: 13 controls, 3 padding bytes, 3 u32 gains.
    /// The padding is explicitly zeroed; the original function leaves it unchanged.
    pub fn little_endian_bytes(self) -> [u8; 28] {
        let mut out = [0u8; 28];
        out[..13].copy_from_slice(&self.controls);
        for i in 0..3 {
            out[16 + i * 4..20 + i * 4].copy_from_slice(&self.gain[i].to_le_bytes());
        }
        out
    }
}
/// Reproduce gain_fix_transfer_v2's successful, finite calibration path.
/// The binary's fourth f32 argument and isp_dgain[] fields are unused here.
/// Logging/null-pointer error paths are not part of this safe value API.
pub fn pack_gain_registers(
    scales: GainScales,
    exposure: ExposureSet,
) -> Result<GainRegisters, InvalidInput> {
    let last = exposure.mode.last();
    let mut gain = [0.; 3];
    let mut weighted_time = [0.; 3];
    for i in 0..3 {
        let source = i.min(last);
        let t = exposure.time[source];
        let a = exposure.analog_gain[source];
        let d = exposure.digital_gain[source];
        let iso = exposure.iso[source];
        if !t.is_finite() || !a.is_finite() || !d.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if t <= 0. || a <= 0. || d <= 0. || iso <= 0 {
            return Err(InvalidInput::Exposure);
        }
        gain[i] = a * d;
        weighted_time[i] = (iso as f32) * t;
        if !gain[i].is_finite() || !weighted_time[i].is_finite() {
            return Err(InvalidInput::NonFinite);
        }
    }
    let mut fixed = [0; 3];
    for i in 0..3 {
        let ratio = weighted_time[last] / weighted_time[i];
        let normalized = (ratio * gain[i]) / gain[2];
        let quantized = quantize_gain(normalized, 6)? as u32;
        let limit = if i == 0 { 262143 } else { 16383 };
        let scale = if scales.enabled && last > 0 && i == 0 {
            Some(scales.short)
        } else if scales.enabled && last == 2 && i == 1 {
            Some(scales.middle)
        } else {
            None
        };
        fixed[i] = if let Some(scale) = scale {
            if !scale.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            if scale < 0. {
                return Err(InvalidInput::Exposure);
            }
            ((quantized as f32) * scale) as u32
        } else {
            quantized
        }
        .min(limit);
    }
    Ok(GainRegisters {
        controls: [0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1],
        gain: fixed,
    })
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn linear_uses_only_first_exposure() {
        let e = ExposureSet {
            mode: HdrMode::Linear,
            time: [0.01, 0., 0.],
            analog_gain: [2., 0., 0.],
            digital_gain: [3., 0., 0.],
            iso: [300, 0, 0],
        };
        let r = pack_gain_registers(
            GainScales {
                enabled: false,
                short: 1.,
                middle: 1.,
            },
            e,
        )
        .unwrap();
        assert_eq!(r.gain, [64, 64, 64]);
        assert_eq!(r.little_endian_bytes().len(), 28);
    }
    #[test]
    fn invalid_zero_time_rejected() {
        let e = ExposureSet {
            mode: HdrMode::Linear,
            time: [0.; 3],
            analog_gain: [1.; 3],
            digital_gain: [1.; 3],
            iso: [50; 3],
        };
        assert_eq!(
            pack_gain_registers(
                GainScales {
                    enabled: false,
                    short: 1.,
                    middle: 1.
                },
                e
            ),
            Err(InvalidInput::Exposure)
        );
    }
}

/// Thirteen-entry ISO calibration table used by the pinned gain selector.
#[derive(Clone, Copy, Debug)]
pub struct GainTable {
    pub enabled: bool,
    pub iso: [i32; 13],
    pub short: [f32; 13],
    pub middle: [f32; 13],
}
#[derive(Clone, Copy, Debug)]
pub struct SelectedGain {
    pub scales: GainScales,
    pub low: usize,
    pub high: usize,
}
/// Recovered gain_select_params_by_ISO_V2 (ELF 0xe784c).
/// ISO is first integer-divided by 50. Exact interior knots choose the interval
/// beginning at that knot, and samples outside the table extrapolate.
pub fn select_gain_scales(
    table: &GainTable,
    exposure: &ExposureSet,
) -> Result<SelectedGain, InvalidInput> {
    let sample = exposure.iso[exposure.mode.last()];
    if sample < 0 {
        return Err(InvalidInput::Exposure);
    }
    let gain = (sample / 50).max(1);
    let mut knots = [0i32; 13];
    for i in 0..13 {
        if table.iso[i] < 50 {
            return Err(InvalidInput::Exposure);
        }
        knots[i] = table.iso[i] / 50;
        if !table.short[i].is_finite() || !table.middle[i].is_finite() {
            return Err(InvalidInput::NonFinite);
        }
    }
    if knots.windows(2).any(|p| p[0] >= p[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let (mut low, mut high) = (0, 1);
    for i in 0..12 {
        if knots[i] <= gain && gain <= knots[i + 1] {
            low = i;
            high = i + 1;
        }
    }
    if gain > knots[12] {
        low = 11;
        high = 12;
    }
    if gain < knots[1] {
        low = 0;
        high = 1;
    }
    let ratio = ((gain - knots[low]) as f32) / ((knots[high] - knots[low]) as f32);
    let short = libm::fmaf(
        table.short[high] - table.short[low],
        ratio,
        table.short[low],
    );
    let middle = libm::fmaf(
        table.middle[high] - table.middle[low],
        ratio,
        table.middle[low],
    );
    Ok(SelectedGain {
        scales: GainScales {
            enabled: table.enabled,
            short,
            middle,
        },
        low,
        high,
    })
}

#[cfg(test)]
mod selection_tests {
    use super::*;
    fn fixture() -> (GainTable, ExposureSet) {
        (
            GainTable {
                enabled: true,
                iso: core::array::from_fn(|i| (i as i32 + 1) * 50),
                short: core::array::from_fn(|i| i as f32),
                middle: [1.; 13],
            },
            ExposureSet {
                mode: HdrMode::Linear,
                time: [1.; 3],
                analog_gain: [1.; 3],
                digital_gain: [1.; 3],
                iso: [150; 3],
            },
        )
    }
    #[test]
    fn exact_knot_uses_next_interval_and_above_table_extrapolates() {
        let (table, mut exposure) = fixture();
        let selected = select_gain_scales(&table, &exposure).unwrap();
        assert_eq!((selected.low, selected.high), (2, 3));
        assert_eq!(selected.scales.short, 2.);
        exposure.iso[0] = 750;
        let selected = select_gain_scales(&table, &exposure).unwrap();
        assert_eq!((selected.low, selected.high), (11, 12));
        assert_eq!(selected.scales.short, 14.);
    }
    #[test]
    fn distinct_iso_knots_with_equal_integer_gain_are_rejected() {
        let (mut table, exposure) = fixture();
        table.iso[1] = 99;
        assert!(matches!(
            select_gain_scales(&table, &exposure),
            Err(InvalidInput::NonIncreasing)
        ));
    }
}

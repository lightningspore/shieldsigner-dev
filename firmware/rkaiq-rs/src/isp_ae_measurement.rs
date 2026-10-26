//! ISP32 dispatcher branches for selected AE/histogram measurement results.
//! Window/weight selection, calibrated initialization and frame-state gating
//! belong to the outer AE controller and remain separate.
use crate::{isp32::PARAMETER_BYTES, InvalidInput};
pub const AE_INPUT_BYTES: usize = 104;
pub const HISTOGRAM_INPUT_BYTES: usize = 529;
pub const AE_OFFSET: usize = 0x41b;
pub const AE_BYTES: usize = 148;
pub const HISTOGRAM_OFFSET: usize = 0x4af;
pub const HISTOGRAM_BYTES: usize = 767;
// Preserve the entire native masks, including the inherited YUVAE/SIHST bits.
pub const AE_MASK: u64 = 0x003c4000;
pub const HISTOGRAM_MASK: u64 = 0x07800008;
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Window {
    pub horizontal_offset: u16,
    pub vertical_offset: u16,
    pub width: u16,
    pub height: u16,
}
impl Window {
    fn read(b: &[u8]) -> Self {
        let word = |o| u16::from_le_bytes(b[o..o + 2].try_into().unwrap());
        Self {
            horizontal_offset: word(0),
            vertical_offset: word(2),
            width: word(4),
            height: word(6),
        }
    }
    fn write(self, b: &mut [u8]) {
        for (i, v) in [
            self.horizontal_offset,
            self.vertical_offset,
            self.width,
            self.height,
        ]
        .iter()
        .enumerate()
        {
            b[i * 2..i * 2 + 2].copy_from_slice(&v.to_le_bytes());
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct LiteMeasurement {
    pub source_selection: u8,
    pub window_mode: u8,
    pub window: Window,
}
impl LiteMeasurement {
    fn read(b: &[u8]) -> Self {
        Self {
            source_selection: b[0],
            window_mode: b[1],
            window: Window::read(&b[2..10]),
        }
    }
    fn write(self, b: &mut [u8]) {
        b[0] = self.source_selection;
        b[1] = self.window_mode;
        self.window.write(&mut b[2..10]);
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BigMeasurement {
    pub source_selection: u8,
    pub window_mode: u8,
    pub subwindow_enabled: [u8; 4],
    pub window: Window,
    pub subwindows: [Window; 4],
}
impl BigMeasurement {
    fn read(b: &[u8]) -> Self {
        Self {
            source_selection: b[0],
            window_mode: b[1],
            subwindow_enabled: b[2..6].try_into().unwrap(),
            window: Window::read(&b[6..14]),
            subwindows: core::array::from_fn(|i| Window::read(&b[14 + i * 8..22 + i * 8])),
        }
    }
    fn write(self, b: &mut [u8]) {
        b[0] = self.source_selection;
        b[1] = self.window_mode;
        b[2..6].copy_from_slice(&self.subwindow_enabled);
        self.window.write(&mut b[6..14]);
        for i in 0..4 {
            self.subwindows[i].write(&mut b[14 + i * 8..22 + i * 8]);
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct AeMeasurement {
    /// These source flags are not consulted by this dispatcher branch.
    pub enabled: bool,
    pub update: bool,
    pub rawae0: LiteMeasurement,
    pub rawae1: BigMeasurement,
    pub rawae3: BigMeasurement,
}
impl AeMeasurement {
    pub fn from_record(b: &[u8; AE_INPUT_BYTES]) -> Result<Self, InvalidInput> {
        if b[0] > 1 || b[1] > 1 {
            return Err(InvalidInput::BooleanValue);
        }
        Ok(Self {
            enabled: b[0] != 0,
            update: b[1] != 0,
            rawae0: LiteMeasurement::read(&b[2..12]),
            rawae1: BigMeasurement::read(&b[12..58]),
            rawae3: BigMeasurement::read(&b[58..104]),
        })
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct LiteHistogram {
    pub data: u8,
    pub waterline: u8,
    pub mode: u8,
    pub step: u8,
    pub offset: u8,
    pub blue_coefficient: u8,
    pub green_coefficient: u8,
    pub red_coefficient: u8,
    pub window: Window,
    pub weights: [u8; 25],
}
impl LiteHistogram {
    fn read(b: &[u8]) -> Self {
        Self {
            data: b[0],
            waterline: b[1],
            mode: b[2],
            step: b[3],
            offset: b[4],
            blue_coefficient: b[5],
            green_coefficient: b[6],
            red_coefficient: b[7],
            window: Window::read(&b[8..16]),
            weights: b[16..41].try_into().unwrap(),
        }
    }
    fn write(self, b: &mut [u8]) {
        b[..8].copy_from_slice(&[
            self.data,
            self.waterline,
            self.mode,
            self.step,
            self.offset,
            self.blue_coefficient,
            self.green_coefficient,
            self.red_coefficient,
        ]);
        self.window.write(&mut b[8..16]);
        b[16..41].copy_from_slice(&self.weights);
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BigHistogram {
    pub window_mode: u8,
    pub data: u8,
    pub waterline: u8,
    pub mode: u8,
    pub step: u8,
    pub offset: u8,
    pub blue_coefficient: u8,
    pub green_coefficient: u8,
    pub red_coefficient: u8,
    pub window: Window,
    pub weights: [u8; 225],
}
impl BigHistogram {
    fn read(b: &[u8]) -> Self {
        Self {
            window_mode: b[0],
            data: b[1],
            waterline: b[2],
            mode: b[3],
            step: b[4],
            offset: b[5],
            blue_coefficient: b[6],
            green_coefficient: b[7],
            red_coefficient: b[8],
            window: Window::read(&b[9..17]),
            weights: b[17..242].try_into().unwrap(),
        }
    }
    fn write(self, b: &mut [u8]) {
        b[..9].copy_from_slice(&[
            self.window_mode,
            self.data,
            self.waterline,
            self.mode,
            self.step,
            self.offset,
            self.blue_coefficient,
            self.green_coefficient,
            self.red_coefficient,
        ]);
        self.window.write(&mut b[9..17]);
        b[17..242].copy_from_slice(&self.weights);
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct HistogramMeasurement {
    /// Flags/swap/selection are carried in the source result but not consulted
    /// by this parameter-dispatch branch. Outer processing owns their policy.
    pub enabled: bool,
    pub update: bool,
    pub ae_swap: u8,
    pub ae_selection: u8,
    pub rawhist0: LiteHistogram,
    pub rawhist1: BigHistogram,
    pub rawhist3: BigHistogram,
}
impl HistogramMeasurement {
    pub fn from_record(b: &[u8; HISTOGRAM_INPUT_BYTES]) -> Result<Self, InvalidInput> {
        if b[0] > 1 || b[1] > 1 {
            return Err(InvalidInput::BooleanValue);
        }
        Ok(Self {
            enabled: b[0] != 0,
            update: b[1] != 0,
            ae_swap: b[2],
            ae_selection: b[3],
            rawhist0: LiteHistogram::read(&b[4..45]),
            rawhist1: BigHistogram::read(&b[45..287]),
            rawhist3: BigHistogram::read(&b[287..529]),
        })
    }
}
fn masks(params: &mut [u8; PARAMETER_BYTES], mask: u64) {
    for offset in [0usize, 8, 16] {
        let value = u64::from_le_bytes(params[offset..offset + 8].try_into().unwrap()) | mask;
        params[offset..offset + 8].copy_from_slice(&value.to_le_bytes());
    }
}
/// Reconstruct result type 1 in convert3aResultsToIspCfg. All masks are set
/// regardless of source enable/update booleans; result publication gates this.
pub fn apply_ae(
    params: &mut [u8; PARAMETER_BYTES],
    cache: &mut [u8; AE_BYTES],
    input: &AeMeasurement,
) {
    let mut block = [0; AE_BYTES];
    input.rawae0.write(&mut block[..10]);
    input.rawae1.write(&mut block[10..56]);
    input.rawae1.write(&mut block[56..102]);
    input.rawae3.write(&mut block[102..148]);
    masks(params, AE_MASK);
    params[AE_OFFSET..AE_OFFSET + AE_BYTES].copy_from_slice(&block);
    *cache = block;
}
/// Reconstruct result type 2. Native ISP32 maps hist1->hist1, hist3->hist2/hist3.
pub fn apply_histogram(
    params: &mut [u8; PARAMETER_BYTES],
    cache: &mut [u8; HISTOGRAM_BYTES],
    input: &HistogramMeasurement,
) {
    let mut block = [0; HISTOGRAM_BYTES];
    input.rawhist0.write(&mut block[..41]);
    input.rawhist1.write(&mut block[41..283]);
    input.rawhist3.write(&mut block[283..525]);
    input.rawhist3.write(&mut block[525..767]);
    masks(params, HISTOGRAM_MASK);
    params[HISTOGRAM_OFFSET..HISTOGRAM_OFFSET + HISTOGRAM_BYTES].copy_from_slice(&block);
    *cache = block;
}

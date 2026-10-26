//! Recovered demosaic hardware quantization and ISP32 serialization.
//! Calibration selection, frame-state handling and live submission are separate.
use crate::{isp32::PARAMETER_BYTES, InvalidInput};
pub const SELECTED_BYTES: usize = 132;
pub const HARDWARE_BYTES: usize = 112;
pub const OFFSET: usize = 0x1282;
pub const BYTES: usize = 57;
pub const MODULE_MASK: u64 = 1 << 35;
pub type HardwareRecord = [u8; HARDWARE_BYTES];
#[derive(Clone, Copy, Debug)]
pub struct SelectedParameters {
    pub debayer_en: bool,
    pub lowfreq_filter1: [i32; 4],
    pub highfreq_filter2: [i32; 4],
    pub c_alpha_gaus_coe: [i32; 3],
    pub c_guid_gaus_coe: [i32; 3],
    pub c_ce_gaus_coe: [i32; 3],
    pub debayer_clip_en: u8,
    pub debayer_gain_offset: u16,
    pub debayer_max_ratio: u8,
    pub debayer_hf_offset: u16,
    pub debayer_thed0: u8,
    pub debayer_thed1: u8,
    pub debayer_dist_scale: u8,
    pub debayer_select_thed: u8,
    pub debayer_gfilter_en: u8,
    pub debayer_gfilter_offset: u16,
    pub debayer_cfilter_en: u8,
    pub debayer_loggd_offset: u16,
    pub debayer_cfilter_str: f32,
    pub debayer_wet_clip: f32,
    pub debayer_wet_ghost: f32,
    pub debayer_wgtslope: f32,
    pub debayer_bf_sgm: f32,
    pub debayer_bf_clip: u8,
    pub debayer_bf_curwgt: u8,
    pub debayer_loghf_offset: u16,
    pub debayer_alpha_offset: u16,
    pub debayer_alpha_scale: f32,
    pub debayer_edge_offset: u16,
    pub debayer_edge_scale: f32,
}
impl SelectedParameters {
    /// Decode the pinned SDK value record without unaligned loads or copying padding.
    pub fn from_record(bytes: &[u8; SELECTED_BYTES]) -> Result<Self, InvalidInput> {
        if bytes[0] > 1 {
            return Err(InvalidInput::BooleanValue);
        }
        Ok(Self {
            debayer_en: bytes[0] != 0,
            lowfreq_filter1: [
                i32::from_le_bytes(bytes[4..8].try_into().unwrap()),
                i32::from_le_bytes(bytes[8..12].try_into().unwrap()),
                i32::from_le_bytes(bytes[12..16].try_into().unwrap()),
                i32::from_le_bytes(bytes[16..20].try_into().unwrap()),
            ],
            highfreq_filter2: [
                i32::from_le_bytes(bytes[20..24].try_into().unwrap()),
                i32::from_le_bytes(bytes[24..28].try_into().unwrap()),
                i32::from_le_bytes(bytes[28..32].try_into().unwrap()),
                i32::from_le_bytes(bytes[32..36].try_into().unwrap()),
            ],
            c_alpha_gaus_coe: [
                i32::from_le_bytes(bytes[36..40].try_into().unwrap()),
                i32::from_le_bytes(bytes[40..44].try_into().unwrap()),
                i32::from_le_bytes(bytes[44..48].try_into().unwrap()),
            ],
            c_guid_gaus_coe: [
                i32::from_le_bytes(bytes[48..52].try_into().unwrap()),
                i32::from_le_bytes(bytes[52..56].try_into().unwrap()),
                i32::from_le_bytes(bytes[56..60].try_into().unwrap()),
            ],
            c_ce_gaus_coe: [
                i32::from_le_bytes(bytes[60..64].try_into().unwrap()),
                i32::from_le_bytes(bytes[64..68].try_into().unwrap()),
                i32::from_le_bytes(bytes[68..72].try_into().unwrap()),
            ],
            debayer_clip_en: bytes[72],
            debayer_gain_offset: u16::from_le_bytes(bytes[74..76].try_into().unwrap()),
            debayer_max_ratio: bytes[76],
            debayer_hf_offset: u16::from_le_bytes(bytes[78..80].try_into().unwrap()),
            debayer_thed0: bytes[80],
            debayer_thed1: bytes[81],
            debayer_dist_scale: bytes[82],
            debayer_select_thed: bytes[83],
            debayer_gfilter_en: bytes[84],
            debayer_gfilter_offset: u16::from_le_bytes(bytes[86..88].try_into().unwrap()),
            debayer_cfilter_en: bytes[88],
            debayer_loggd_offset: u16::from_le_bytes(bytes[90..92].try_into().unwrap()),
            debayer_cfilter_str: f32::from_le_bytes(bytes[92..96].try_into().unwrap()),
            debayer_wet_clip: f32::from_le_bytes(bytes[96..100].try_into().unwrap()),
            debayer_wet_ghost: f32::from_le_bytes(bytes[100..104].try_into().unwrap()),
            debayer_wgtslope: f32::from_le_bytes(bytes[104..108].try_into().unwrap()),
            debayer_bf_sgm: f32::from_le_bytes(bytes[108..112].try_into().unwrap()),
            debayer_bf_clip: bytes[112],
            debayer_bf_curwgt: bytes[113],
            debayer_loghf_offset: u16::from_le_bytes(bytes[114..116].try_into().unwrap()),
            debayer_alpha_offset: u16::from_le_bytes(bytes[116..118].try_into().unwrap()),
            debayer_alpha_scale: f32::from_le_bytes(bytes[120..124].try_into().unwrap()),
            debayer_edge_offset: u16::from_le_bytes(bytes[124..126].try_into().unwrap()),
            debayer_edge_scale: f32::from_le_bytes(bytes[128..132].try_into().unwrap()),
        })
    }
}
fn put16(bytes: &mut [u8], offset: usize, value: u16) {
    bytes[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
}
fn put32(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
fn rounded(value: f32) -> i32 {
    ((value as f64) + if value <= 0. { -0.5 } else { 0.5 }) as i32
}
/// Reconstruct AdebayerGetProcResult: preserve previous padding/update flag in
/// the returned record, then clear only the cached update flag. Errors are atomic.
pub fn quantize(
    previous: &mut HardwareRecord,
    selected: SelectedParameters,
) -> Result<HardwareRecord, InvalidInput> {
    let s = selected;
    let floats = [
        s.debayer_cfilter_str,
        s.debayer_wet_clip,
        s.debayer_wet_ghost,
        s.debayer_wgtslope,
        s.debayer_bf_sgm,
        s.debayer_alpha_scale,
        s.debayer_edge_scale,
    ];
    if floats.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if s.debayer_cfilter_str <= 0. || s.debayer_bf_sgm <= 0. || s.debayer_wgtslope <= 0. {
        return Err(InvalidInput::DegenerateRange);
    }
    let inverse = rounded(78715.2890625 / (s.debayer_cfilter_str * 4096.));
    let slope = rounded(s.debayer_wgtslope * 128.) as u16;
    let product = (slope as i32).wrapping_mul(inverse);
    if product <= 0 {
        return Err(InvalidInput::DegenerateRange);
    }
    let exponent =
        ((libm::log(product as f64) / core::f64::consts::LN_2 - 7.) as i32).max(0) as u32;
    let divisor = (1i32 << exponent) as f32;
    let mut out = *previous;

    out[1] = s.debayer_en as u8;
    out[2] = s.debayer_gfilter_en;
    out[3] = s.debayer_cfilter_en;
    out[4] = s.debayer_clip_en;
    out[5] = s.debayer_dist_scale;
    out[6] = s.debayer_thed0;
    out[7] = s.debayer_thed1;
    out[8] = s.debayer_select_thed;
    out[9] = s.debayer_max_ratio;
    for i in 0..4 {
        put32(&mut out, 12 + i * 4, s.lowfreq_filter1[i] as u32);
    }
    for i in 0..4 {
        put32(&mut out, 28 + i * 4, s.highfreq_filter2[i] as u32);
    }
    for i in 0..3 {
        put32(&mut out, 44 + i * 4, s.c_guid_gaus_coe[i] as u32);
    }
    for i in 0..3 {
        put32(&mut out, 56 + i * 4, s.c_ce_gaus_coe[i] as u32);
    }
    for i in 0..3 {
        put32(&mut out, 68 + i * 4, s.c_alpha_gaus_coe[i] as u32);
    }
    out[80] = rounded(product as f32 / divisor) as u8;
    out[81] = 16u8.wrapping_sub(exponent as u8);
    out[82] = rounded(s.debayer_wet_clip * 8.) as u8;
    out[83] = rounded(s.debayer_wet_ghost * 64.) as u8;
    out[84] = s.debayer_bf_clip;
    out[85] = s.debayer_bf_curwgt;
    put16(
        &mut out,
        86,
        (55659.7265625 / (s.debayer_bf_sgm * 4095.)) as i32 as u16,
    );
    put16(&mut out, 88, s.debayer_hf_offset);
    put16(&mut out, 90, s.debayer_gain_offset);
    put16(&mut out, 92, s.debayer_gfilter_offset);
    put16(&mut out, 94, s.debayer_loghf_offset);
    put16(&mut out, 96, s.debayer_loggd_offset);
    put16(&mut out, 98, slope);
    put16(&mut out, 100, s.debayer_alpha_offset);
    put16(&mut out, 102, s.debayer_edge_offset);
    put32(&mut out, 104, rounded(s.debayer_edge_scale * 1024.) as u32);
    put32(&mut out, 108, rounded(s.debayer_alpha_scale * 1024.) as u32);
    *previous = out;
    previous[0] = 0;
    Ok(out)
}
/// Reconstruct convertAiqAdebayerToIsp32Params. update=false is a full no-op.
/// Disabled updates clear the enable bit and set enable-update, while preserving
/// the prior config-update mask; enabled updates set all three masks.
pub fn apply(params: &mut [u8; PARAMETER_BYTES], hardware: &HardwareRecord) {
    if hardware[0] == 0 {
        return;
    }
    for (offset, mask) in [(0, MODULE_MASK), (8, MODULE_MASK), (16, MODULE_MASK)] {
        let previous = u64::from_le_bytes(params[offset..offset + 8].try_into().unwrap());
        let next = if offset == 8 && hardware[1] == 0 {
            previous & !mask
        } else if offset == 16 && hardware[1] == 0 {
            previous
        } else {
            previous | mask
        };
        params[offset..offset + 8].copy_from_slice(&next.to_le_bytes());
    }
    let block = &mut params[OFFSET..OFFSET + BYTES];
    block[..8].copy_from_slice(&hardware[2..10]);
    for i in 0..17 {
        block[8 + i] = hardware[12 + i * 4];
    }
    block[25..31].copy_from_slice(&hardware[80..86]);
    block[31..57].copy_from_slice(&hardware[86..112]);
}

#[cfg(test)]
mod tests {
    use super::*;
    fn selected() -> SelectedParameters {
        let mut bytes = [0u8; SELECTED_BYTES];
        for offset in [92usize, 104, 108] {
            bytes[offset..offset + 4].copy_from_slice(&1f32.to_le_bytes());
        }
        SelectedParameters::from_record(&bytes).unwrap()
    }
    #[test]
    fn result_retains_update_flag_then_clears_cached_flag() {
        let mut previous = [0x55; HARDWARE_BYTES];
        previous[0] = 1;
        let output = quantize(&mut previous, selected()).unwrap();
        assert_eq!(output[0], 1);
        assert_eq!(previous[0], 0);
        assert_eq!(&output[1..], &previous[1..]);
        assert_eq!(&output[10..12], &[0x55; 2]);
    }
    #[test]
    fn zero_inverse_domain_is_rejected_before_mutation() {
        let mut previous = [0x55; HARDWARE_BYTES];
        let before = previous;
        let mut value = selected();
        value.debayer_cfilter_str = 0.;
        assert_eq!(
            quantize(&mut previous, value),
            Err(InvalidInput::DegenerateRange)
        );
        assert_eq!(previous, before);
    }
    #[test]
    fn inactive_record_does_not_change_any_parameter_byte() {
        let mut params = [0x55; PARAMETER_BYTES];
        let original = params;
        let mut record = [0xff; HARDWARE_BYTES];
        record[0] = 0;
        apply(&mut params, &record);
        assert_eq!(params, original);
    }
}

//! Recovered automatic demosaic tuning selection. ISP/frame-state and queue
//! integration remain separate from this checked value API.
use crate::{isp_demosaic::SelectedParameters, InvalidInput};
pub const ISO_STEPS: usize = 13;
#[derive(Clone, Copy, Debug)]
pub struct GreenInterpolation {
    pub iso: [f32; ISO_STEPS],
    pub debayer_clip_en: [u8; ISO_STEPS],
    pub debayer_gain_offset: [u16; ISO_STEPS],
    pub debayer_max_ratio: [u8; ISO_STEPS],
}
#[derive(Clone, Copy, Debug)]
pub struct GreenDirection {
    pub iso: [f32; ISO_STEPS],
    pub debayer_hf_offset: [u16; ISO_STEPS],
    pub debayer_thed0: [u8; ISO_STEPS],
    pub debayer_thed1: [u8; ISO_STEPS],
    pub debayer_dist_scale: [u8; ISO_STEPS],
    pub debayer_select_thed: [u8; ISO_STEPS],
}
#[derive(Clone, Copy, Debug)]
pub struct GreenFilter {
    pub iso: [f32; ISO_STEPS],
    pub debayer_gfilter_en: [u8; ISO_STEPS],
    pub debayer_gfilter_offset: [u16; ISO_STEPS],
}
#[derive(Clone, Copy, Debug)]
pub struct ColorFilter {
    pub iso: [f32; ISO_STEPS],
    pub debayer_cfilter_en: [u8; ISO_STEPS],
    pub debayer_loggd_offset: [u16; ISO_STEPS],
    pub debayer_cfilter_str: [f32; ISO_STEPS],
    pub debayer_wet_clip: [f32; ISO_STEPS],
    pub debayer_wet_ghost: [f32; ISO_STEPS],
    pub debayer_wgtslope: [f32; ISO_STEPS],
    pub debayer_bf_sgm: [f32; ISO_STEPS],
    pub debayer_bf_clip: [u8; ISO_STEPS],
    pub debayer_bf_curwgt: [u8; ISO_STEPS],
    pub debayer_loghf_offset: [u16; ISO_STEPS],
    pub debayer_alpha_offset: [u16; ISO_STEPS],
    pub debayer_alpha_scale: [f32; ISO_STEPS],
    pub debayer_edge_offset: [u16; ISO_STEPS],
    pub debayer_edge_scale: [f32; ISO_STEPS],
}
#[derive(Clone, Copy, Debug)]
pub struct Calibration {
    pub debayer_en: bool,
    pub lowfreq_filter1: [i32; 4],
    pub highfreq_filter2: [i32; 4],
    pub c_alpha_gaus_coe: [i32; 3],
    pub c_guid_gaus_coe: [i32; 3],
    pub c_ce_gaus_coe: [i32; 3],
    pub g_interp: GreenInterpolation,
    pub g_drctwgt: GreenDirection,
    pub g_filter: GreenFilter,
    pub c_filter: ColorFilter,
}
fn bracket(knots: &[f32; ISO_STEPS], iso: i32) -> Result<(usize, usize, f32), InvalidInput> {
    if knots.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if knots.iter().any(|v| *v < 0. || *v > 16_777_216.) {
        return Err(InvalidInput::DegenerateRange);
    }
    if knots
        .windows(2)
        .any(|w| w[0] >= w[1] || (w[0] as i32) >= (w[1] as i32))
    {
        return Err(InvalidInput::NonIncreasing);
    }
    for (high, knot) in knots.iter().enumerate() {
        if (iso as f32) < *knot {
            if high == 0 {
                return Ok((0, 0, 0.));
            }
            let low = high - 1;
            // The original compares f32 knots, then truncates them to i32
            // before forming the interpolation numerator and denominator.
            let ratio =
                (iso - knots[low] as i32) as f32 / (knots[high] as i32 - knots[low] as i32) as f32;
            return Ok((low, high, ratio));
        }
    }
    Ok((12, 12, 1.))
}
fn blend(low: f32, high: f32, ratio: f32) -> f32 {
    libm::fmaf(high - low, ratio, low)
}
fn integer(low: f32, high: f32, ratio: f32) -> i32 {
    let value = blend(low, high, ratio);
    ((value as f64) + if value <= 0. { -0.5 } else { 0.5 }) as i32
}
impl Calibration {
    /// Validate all knots/float tables without selecting a particular ISO.
    pub fn validate(&self) -> Result<(), InvalidInput> {
        bracket(&self.g_interp.iso, 0)?;
        bracket(&self.g_drctwgt.iso, 0)?;
        bracket(&self.g_filter.iso, 0)?;
        bracket(&self.c_filter.iso, 0)?;
        if self
            .c_filter
            .debayer_cfilter_str
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if self
            .c_filter
            .debayer_wet_clip
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if self
            .c_filter
            .debayer_wet_ghost
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if self
            .c_filter
            .debayer_wgtslope
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if self.c_filter.debayer_bf_sgm.iter().any(|v| !v.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        if self
            .c_filter
            .debayer_alpha_scale
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        if self
            .c_filter
            .debayer_edge_scale
            .iter()
            .any(|v| !v.is_finite())
        {
            return Err(InvalidInput::NonFinite);
        }
        Ok(())
    }
    /// Reconstruct the automatic branch of AdebayerProcess and its complete
    /// AdebayerSelectParam call. Outer mode/update state is not managed here.
    pub fn select(&self, iso: i32) -> Result<SelectedParameters, InvalidInput> {
        self.validate()?;
        let mut out = SelectedParameters::default();
        out.debayer_en = self.debayer_en;
        out.lowfreq_filter1 = self.lowfreq_filter1;
        out.highfreq_filter2 = self.highfreq_filter2;
        out.c_alpha_gaus_coe = self.c_alpha_gaus_coe;
        out.c_guid_gaus_coe = self.c_guid_gaus_coe;
        out.c_ce_gaus_coe = self.c_ce_gaus_coe;

        let (low, high, ratio) = bracket(&self.g_interp.iso, iso)?;
        out.debayer_clip_en = integer(
            self.g_interp.debayer_clip_en[low] as f32,
            self.g_interp.debayer_clip_en[high] as f32,
            ratio,
        ) as u8;
        out.debayer_gain_offset = integer(
            self.g_interp.debayer_gain_offset[low] as f32,
            self.g_interp.debayer_gain_offset[high] as f32,
            ratio,
        ) as u16;
        out.debayer_max_ratio = integer(
            self.g_interp.debayer_max_ratio[low] as f32,
            self.g_interp.debayer_max_ratio[high] as f32,
            ratio,
        ) as u8;
        let (low, high, ratio) = bracket(&self.g_drctwgt.iso, iso)?;
        out.debayer_hf_offset = integer(
            self.g_drctwgt.debayer_hf_offset[low] as f32,
            self.g_drctwgt.debayer_hf_offset[high] as f32,
            ratio,
        ) as u16;
        out.debayer_thed0 = integer(
            self.g_drctwgt.debayer_thed0[low] as f32,
            self.g_drctwgt.debayer_thed0[high] as f32,
            ratio,
        ) as u8;
        out.debayer_thed1 = integer(
            self.g_drctwgt.debayer_thed1[low] as f32,
            self.g_drctwgt.debayer_thed1[high] as f32,
            ratio,
        ) as u8;
        out.debayer_dist_scale = integer(
            self.g_drctwgt.debayer_dist_scale[low] as f32,
            self.g_drctwgt.debayer_dist_scale[high] as f32,
            ratio,
        ) as u8;
        out.debayer_select_thed = integer(
            self.g_drctwgt.debayer_select_thed[low] as f32,
            self.g_drctwgt.debayer_select_thed[high] as f32,
            ratio,
        ) as u8;
        let (low, high, ratio) = bracket(&self.g_filter.iso, iso)?;
        out.debayer_gfilter_en = integer(
            self.g_filter.debayer_gfilter_en[low] as f32,
            self.g_filter.debayer_gfilter_en[high] as f32,
            ratio,
        ) as u8;
        out.debayer_gfilter_offset = integer(
            self.g_filter.debayer_gfilter_offset[low] as f32,
            self.g_filter.debayer_gfilter_offset[high] as f32,
            ratio,
        ) as u16;
        let (low, high, ratio) = bracket(&self.c_filter.iso, iso)?;
        out.debayer_cfilter_en = integer(
            self.c_filter.debayer_cfilter_en[low] as f32,
            self.c_filter.debayer_cfilter_en[high] as f32,
            ratio,
        ) as u8;
        out.debayer_loggd_offset = integer(
            self.c_filter.debayer_loggd_offset[low] as f32,
            self.c_filter.debayer_loggd_offset[high] as f32,
            ratio,
        ) as u16;
        out.debayer_cfilter_str = blend(
            self.c_filter.debayer_cfilter_str[low],
            self.c_filter.debayer_cfilter_str[high],
            ratio,
        );
        out.debayer_wet_clip = blend(
            self.c_filter.debayer_wet_clip[low],
            self.c_filter.debayer_wet_clip[high],
            ratio,
        );
        out.debayer_wet_ghost = blend(
            self.c_filter.debayer_wet_ghost[low],
            self.c_filter.debayer_wet_ghost[high],
            ratio,
        );
        out.debayer_wgtslope = blend(
            self.c_filter.debayer_wgtslope[low],
            self.c_filter.debayer_wgtslope[high],
            ratio,
        );
        out.debayer_bf_sgm = blend(
            self.c_filter.debayer_bf_sgm[low],
            self.c_filter.debayer_bf_sgm[high],
            ratio,
        );
        out.debayer_bf_clip = integer(
            self.c_filter.debayer_bf_clip[low] as f32,
            self.c_filter.debayer_bf_clip[high] as f32,
            ratio,
        ) as u8;
        out.debayer_bf_curwgt = integer(
            self.c_filter.debayer_bf_curwgt[low] as f32,
            self.c_filter.debayer_bf_curwgt[high] as f32,
            ratio,
        ) as u8;
        out.debayer_loghf_offset = integer(
            self.c_filter.debayer_loghf_offset[low] as f32,
            self.c_filter.debayer_loghf_offset[high] as f32,
            ratio,
        ) as u16;
        out.debayer_alpha_offset = integer(
            self.c_filter.debayer_alpha_offset[low] as f32,
            self.c_filter.debayer_alpha_offset[high] as f32,
            ratio,
        ) as u16;
        out.debayer_alpha_scale = blend(
            self.c_filter.debayer_alpha_scale[low],
            self.c_filter.debayer_alpha_scale[high],
            ratio,
        );
        out.debayer_edge_offset = integer(
            self.c_filter.debayer_edge_offset[low] as f32,
            self.c_filter.debayer_edge_offset[high] as f32,
            ratio,
        ) as u16;
        out.debayer_edge_scale = blend(
            self.c_filter.debayer_edge_scale[low],
            self.c_filter.debayer_edge_scale[high],
            ratio,
        );
        Ok(out)
    }
}

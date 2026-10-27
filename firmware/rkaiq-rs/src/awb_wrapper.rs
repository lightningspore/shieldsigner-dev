//! AwbCalAwbGain (ELF 0xc803c): resets, adaptive controls, strategy, saved site.
use crate::{
    awb_gain,
    awb_gain_controller::{Frame, Light, LightResult, Settings, State},
    awb_high_gain,
    awb_preparation::LightRecord,
    awb_probability::Probability,
    awb_single_color_grid::Detection,
    awb_site, interpolate, InvalidInput,
};
pub struct Controls<'a> {
    pub damping: awb_gain::DampingParameters,
    pub variance: f32,
    pub tolerance_knots: &'a [f32],
    pub tolerance_values: &'a [f32],
    pub site: &'a awb_site::Settings,
    pub site_input: &'a awb_site::Input,
}
/// Full represented gain-wrapper state transition. The prepared adapter guards
/// the unresolved native AUTO/ALWAYS Exclusion cross-record read. All outputs,
/// including site state, commit only after the entire transition succeeds.
pub fn process<const CAP: usize>(
    state: &mut State<CAP>,
    site: &mut awb_site::State,
    frame: &Frame,
    records: &[LightRecord],
    lights: &[Light<'_>],
    output: &mut [LightResult],
    settings: &Settings<'_>,
    controls: &Controls<'_>,
) -> Result<(), InvalidInput> {
    let n = lights.len();
    if n < 4 || n > 255 || output.len() != n || records.len() != n {
        return Err(InvalidInput::Length);
    }
    let mut next = state.clone();
    let mut next_site = site.clone();
    next.low.detection = Detection {
        selected: 0,
        color: 0,
        candidate_counts: [0; 14],
        color_counts: [0; 14],
        valid: false,
        disagreements: 0,
        votes: 0,
        mean_distance: 0.,
        gain: [0.; 4],
    };
    next.low.low.temporal_source = [0.; 4];
    next.temporal_weight = -1.;
    next.selection_status = 255;
    next.strategy_flag = false;
    next.low.low.used_previous = false;
    next.high_gain = [0.; 4];
    next.low.low.low_result = [0.; 4];
    next.high_low_weight = -1.;
    next.low.low.temporal_result = [0.; 4];
    next.low.single_weight = -1.;
    next.low.low.spatial_result = [0.; 4];
    next.low.low.spatial_weight = -1.;
    next.post.clipped = false;
    next.post.clipped_gain = [0.; 4];
    next.post.adjust_before = [0.; 4];
    next.post.adjust_after = [0.; 4];
    next.post.adjust_coordinates_before = [0.; 2];
    next.post.adjust_coordinates_after = [0.; 2];
    next.post.offset_gain = [0.; 4];
    next.post.coefficient = controls
        .damping
        .adapt(next.post.coefficient, controls.variance)?;
    let tolerance = interpolate(
        controls.tolerance_knots,
        controls.tolerance_values,
        settings.probability.brightness as f32,
    )?;
    let post = crate::awb_postprocess::Settings {
        tolerance,
        ..*settings.post
    };
    let region = crate::awb_xy_selection::Settings {
        variance: controls.variance,
        ..*settings.region
    };
    let settings = Settings {
        post: &post,
        region: &region,
        single: settings
            .single
            .map(|input| crate::awb_low_single_color::Input {
                brightness_sample: settings.probability.prior_sample,
                ..input
            }),
        ..*settings
    };
    let empty = LightResult {
        probability: Probability {
            total: 0.,
            distance: 0.,
            luma: 0.,
            prior: 0.,
            white_points: 0.,
        },
        gain: awb_high_gain::LightResult {
            statistic: [0.; 4],
            spatial: [0.; 4],
            spatial_weight: 0.,
            extra_weight: 0.,
        },
    };
    let mut staged = [empty; 255];
    next.process_prepared(frame, records, lights, &mut staged[..n], &settings)?;
    let site_input = awb_site::Input {
        frame: settings.probability.frame,
        sample: settings.probability.prior_sample,
        ..*controls.site_input
    };
    next_site.apply(&mut next.post.current, &site_input, controls.site)?;
    next.post.previous = next.post.current;
    next.low.low.current = next.post.current;
    output.copy_from_slice(&staged[..n]);
    *state = next;
    *site = next_site;
    Ok(())
}

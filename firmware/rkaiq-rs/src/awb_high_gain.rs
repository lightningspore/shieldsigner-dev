//! Complete AwbCalGainWpTypeHigh (ELF 0xc6a20) value-level call chain.
//! Calibrated per-light inputs and total probabilities are supplied by callers.
use crate::{
    awb_gain::{self, Gains},
    awb_probability, InvalidInput,
};

#[derive(Clone, Copy)]
pub struct Light {
    pub selected_gain: Gains,
    pub selected_count: u32,
    pub extra_gain: Gains,
    pub extra_count: u32,
    pub extra_enabled: bool,
    pub low_threshold: u32,
    pub high_threshold: u32,
    pub low_gain: Gains,
    pub high_gain: Gains,
    pub spatial_percentage: u8,
    pub probability: f32,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct LightResult {
    pub statistic: Gains,
    pub spatial: Gains,
    /// Preserved in FASTAWBACT mode, which bypasses this blend.
    pub spatial_weight: f32,
    /// Preserved if extra mixing is disabled or selected_count is zero.
    pub extra_weight: f32,
}

#[derive(Clone, Copy)]
pub struct Settings {
    pub fast: bool,
    pub brightness: u32,
    pub temporal_default: Gains,
    pub temporal_knots: [u32; 16],
    pub temporal_percentages: [u8; 16],
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Result {
    pub gain: Gains,
    /// Raw percentage, matching native context 0x33f8.
    pub temporal_weight: f32,
    /// Copied directly, without normalization, into native context 0x33e8.
    pub temporal: Gains,
}

/// Outputs are committed together only after every numerical stage succeeds.
pub fn calculate(
    lights: &[Light],
    output: &mut [LightResult],
    settings: &Settings,
) -> core::result::Result<Result, InvalidInput> {
    let n = lights.len();
    if n == 0 || n > 255 || output.len() != n {
        return Err(InvalidInput::Length);
    }
    let empty = LightResult {
        statistic: [0.; 4],
        spatial: [0.; 4],
        spatial_weight: 0.,
        extra_weight: 0.,
    };
    let mut staged = [empty; 255];
    staged[..n].copy_from_slice(output);
    for (light, result) in lights.iter().zip(&mut staged[..n]) {
        result.statistic = light.selected_gain;
        if light.extra_enabled && light.selected_count != 0 {
            let ratio = light.extra_count as f32 / light.selected_count as f32;
            let weight = if ratio > 1. { 1. } else { ratio };
            result.extra_weight = weight;
            result.statistic = awb_gain::mixture(light.extra_gain, light.selected_gain, weight)?;
        }
        result.spatial = awb_gain::spatial(
            settings.brightness,
            light.low_threshold,
            light.high_threshold,
            light.low_gain,
            light.high_gain,
        )?;
        if !settings.fast {
            (result.statistic, result.spatial_weight) = awb_gain::spatial_statistics(
                result.statistic,
                result.spatial,
                light.spatial_percentage,
            )?;
        }
    }
    let current = awb_probability::weighted_gain_values(
        lights
            .iter()
            .zip(&staged[..n])
            .map(|(l, r)| (r.statistic, l.probability)),
    )?;
    let (gain, temporal_weight) = awb_gain::temporal_blend(
        current,
        settings.temporal_default,
        settings.brightness,
        &settings.temporal_knots,
        &settings.temporal_percentages,
    )?;
    output.copy_from_slice(&staged[..n]);
    Ok(Result {
        gain,
        temporal_weight,
        temporal: settings.temporal_default,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn late_invalid_probability_does_not_publish_partial_light_results() {
        let light = Light {
            selected_gain: [2.; 4],
            selected_count: 100,
            extra_gain: [3.; 4],
            extra_count: 50,
            extra_enabled: true,
            low_threshold: 100,
            high_threshold: 200,
            low_gain: [4.; 4],
            high_gain: [5.; 4],
            spatial_percentage: 50,
            probability: f32::NAN,
        };
        let settings = Settings {
            fast: false,
            brightness: 150,
            temporal_default: [1.; 4],
            temporal_knots: [0; 16],
            temporal_percentages: [0; 16],
        };
        let before = LightResult {
            statistic: [9.; 4],
            spatial: [8.; 4],
            spatial_weight: 0.25,
            extra_weight: 0.75,
        };
        let mut output = [before];
        assert_eq!(
            calculate(&[light], &mut output, &settings),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(output, [before]);
    }
}

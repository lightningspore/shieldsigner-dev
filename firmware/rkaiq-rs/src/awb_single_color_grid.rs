//! AwbSingleColorProcess2 (ELF 0xcb208): complete grid/candidate/history path.
use crate::{
    awb_color,
    awb_gain::Gains,
    awb_luma_history::History,
    awb_single_color::{self, Line},
    InvalidInput,
};

pub struct Candidate {
    pub red: f32,
    pub blue: f32,
}
pub struct Color {
    pub chroma: f32,
    pub hue: f32,
    pub cct_knots: [f32; 3],
    pub distance_thresholds: [f32; 3],
}
pub struct Calibration<'a> {
    pub candidates: &'a [Candidate],
    pub colors: &'a [Color],
    pub alpha: f32,
    pub history_target: u16,
    pub first: Line,
    pub second: Line,
}
#[derive(Clone, Debug, PartialEq)]
pub struct Detection {
    pub selected: i32,
    pub color: i32,
    pub candidate_counts: [i32; 14],
    pub color_counts: [i32; 14],
    pub valid: bool,
    pub disagreements: i32,
    pub votes: i32,
    pub mean_distance: f32,
    pub gain: Gains,
}
#[derive(Clone, Debug, PartialEq)]
pub struct State<const CAP: usize> {
    pub history: History<CAP>,
    pub result: Detection,
}

impl<const CAP: usize> State<CAP> {
    /// Optional prior is appended only if Gr and Gb are strictly above 1e-5.
    /// History entries must refer to currently available candidates; native
    /// out-of-range list indices would access uninitialized/out-of-bounds data.
    pub fn process(
        &mut self,
        grid: &[[f32; 3]; 225],
        cal: &Calibration<'_>,
        prior: Option<Gains>,
    ) -> Result<(), InvalidInput> {
        let mut gains = [[0.; 4]; 14];
        let mut n = cal.candidates.len();
        let colors = cal.colors.len();
        if n == 0 || n > 14 || colors == 0 || colors > 14 {
            return Err(InvalidInput::Length);
        }
        if !cal.alpha.is_finite() || grid.iter().flatten().any(|v| !v.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        for (gain, candidate) in gains.iter_mut().zip(cal.candidates) {
            if !candidate.red.is_finite() || !candidate.blue.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            *gain = [candidate.red, 1., 1., candidate.blue];
        }
        if let Some(prior) = prior {
            if prior.iter().any(|v| !v.is_finite()) {
                return Err(InvalidInput::NonFinite);
            }
            if prior[1] as f64 > 0.00001 && prior[2] as f64 > 0.00001 {
                if n == 14 {
                    return Err(InvalidInput::Length);
                }
                gains[n] = [prior[0] / prior[1], 1., 1., prior[3] / prior[2]];
                if gains[n].iter().any(|v| !v.is_finite()) {
                    return Err(InvalidInput::NonFinite);
                }
                n += 1;
            }
        }
        if self.history.values().iter().any(|&v| v as usize >= n) {
            return Err(InvalidInput::Length);
        }
        for color in cal.colors {
            if !color.chroma.is_finite() || !color.hue.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            awb_single_color::curve(&color.cct_knots, &color.distance_thresholds, 0.)?;
        }
        let mut next = self.clone();
        let mut selected = [0usize; 225];
        let mut labels = [0usize; 225];
        let mut distances = [0.; 225];
        let mut best_candidate = 0;
        let mut best_color = 0;
        for (i, rgb) in grid.iter().enumerate() {
            let mut minimum = 999999.;
            for (candidate, gain) in gains[..n].iter().enumerate() {
                let red = rgb[0] * gain[0];
                let blue = rgb[2] * gain[3];
                let xyz = awb_color::rgb_to_xyz([
                    if red > 1. { 1. } else { red },
                    rgb[1],
                    if blue > 1. { 1. } else { blue },
                ])?;
                let lab = awb_color::xyz_to_lab(xyz)?;
                let [chroma, hue] = awb_color::lab_to_lch([lab[1], lab[2]])?;
                for (label, color) in cal.colors.iter().enumerate() {
                    let delta = libm::fabsf(hue - color.hue);
                    let wrapped = 360. - delta;
                    let hue_delta = if wrapped < delta { wrapped } else { delta };
                    let chroma_term =
                        ((1. - cal.alpha) * libm::fabsf(chroma - color.chroma)) * 180.;
                    let distance = libm::fmaf(hue_delta * cal.alpha, 140., chroma_term);
                    if !distance.is_finite() {
                        return Err(InvalidInput::NonFinite);
                    }
                    if minimum > distance {
                        minimum = distance;
                        best_candidate = candidate;
                        best_color = label;
                    }
                }
            }
            selected[i] = best_candidate;
            labels[i] = best_color;
            distances[i] = minimum;
        }
        let mut candidate_counts = [0i32; 14];
        let mut color_counts = [0i32; 14];
        let mut accepted = 0;
        let mut distance_sum = 0.;
        let mut disagreements = 0;
        for i in 0..225 {
            let row = i / 15;
            let col = i % 15;
            let neighbors = [
                if col == 0 { i } else { i - 1 },
                if col == 14 { i } else { i + 1 },
                if row == 0 { i } else { i - 15 },
                if row == 14 { i } else { i + 15 },
            ];
            let different = neighbors
                .iter()
                .filter(|&&j| labels[j] != labels[i])
                .count();
            disagreements += different as i32;
            let temperature =
                awb_single_color::color_temperature(gains[selected[i]], cal.first, cal.second)?;
            let color = &cal.colors[labels[i]];
            let threshold = awb_single_color::curve(
                &color.cct_knots,
                &color.distance_thresholds,
                temperature.cct,
            )?;
            if different == 0 && !(threshold < distances[i]) {
                accepted += 1;
                distance_sum += distances[i];
                candidate_counts[selected[i]] += 1;
                color_counts[labels[i]] += 1;
            }
        }
        next.result.candidate_counts[..n].copy_from_slice(&candidate_counts[..n]);
        next.result.color_counts[..colors].copy_from_slice(&color_counts[..colors]);
        next.result.disagreements = disagreements;
        next.result.gain = [1.; 4];
        next.result.valid = false;
        next.result.selected = -1;
        if accepted == 0 {
            next.result.color = -1;
            next.result.votes = -1;
            next.result.mean_distance = 9999.;
        } else {
            let winner = |counts: &[i32]| {
                let mut best = 0;
                for i in 1..counts.len() {
                    if counts[i] > counts[best] {
                        best = i;
                    }
                }
                best
            };
            let raw = winner(&candidate_counts[..n]);
            next.result.color = winner(&color_counts[..colors]) as i32;
            next.result.votes = candidate_counts[raw];
            next.result.mean_distance = distance_sum / accepted as f32;
            next.history.update(raw as i32, cal.history_target as i32)?;
            let mut chosen = raw;
            if next.history.values().len() > 1 && cal.candidates.len() + 1 > 1 {
                let mut votes = [0i32; 15];
                for &value in next.history.values() {
                    votes[value as usize] += 1;
                }
                chosen = winner(&votes[..cal.candidates.len() + 1]);
            }
            if chosen >= n {
                return Err(InvalidInput::Length);
            }
            next.result.selected = chosen as i32;
            next.result.valid = true;
            next.result.gain = gains[chosen];
        }
        *self = next;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejected_history_update_does_not_publish_detection() {
        let mut state = State::<4> {
            history: History::from_values(&[0]).unwrap(),
            result: Detection {
                selected: -1,
                color: -1,
                candidate_counts: [7; 14],
                color_counts: [8; 14],
                valid: false,
                disagreements: 9,
                votes: 10,
                mean_distance: 11.,
                gain: [2.; 4],
            },
        };
        let before = state.clone();
        let line = Line {
            a: 0.,
            b: 0.,
            c: 0.,
            valid: false,
        };
        let candidates = [Candidate { red: 1., blue: 1. }];
        let colors = [Color {
            chroma: 0.,
            hue: 0.,
            cct_knots: [0., 1., 2.],
            distance_thresholds: [1000000.; 3],
        }];
        let cal = Calibration {
            candidates: &candidates,
            colors: &colors,
            alpha: 0.5,
            history_target: 1,
            first: line,
            second: line,
        };
        assert_eq!(
            state.process(&[[0.2; 3]; 225], &cal, None),
            Err(InvalidInput::Length)
        );
        assert_eq!(state, before);
    }
}

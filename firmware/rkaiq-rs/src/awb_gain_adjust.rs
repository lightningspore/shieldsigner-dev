//! AwbCtShift3 (ELF 0xca340) and AwbGainAdjust3 (ELF 0xcad70).
use crate::{
    awb_gain::Gains,
    awb_single_color::{self, ColorTemperature, Line},
    InvalidInput,
};
pub struct Lut {
    pub sample: f32,
    pub x: [f32; 9],
    pub y: [f32; 11],
    pub mapped_x: [f32; 99],
    pub mapped_y: [f32; 99],
}

fn axis<const N: usize>(
    knots: &[f32; N],
    value: f32,
) -> Result<(usize, f32, f32, f32, bool), InvalidInput> {
    if !value.is_finite() || knots.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    let descending = knots[N - 1] < knots[0];
    if knots.windows(2).any(|v| {
        if descending {
            v[0] <= v[1]
        } else {
            v[0] >= v[1]
        }
    }) {
        return Err(InvalidInput::NonIncreasing);
    }
    let before = if descending {
        value > knots[0]
    } else {
        value < knots[0]
    };
    let after = if descending {
        value < knots[N - 1]
    } else {
        value > knots[N - 1]
    };
    let clamped = if before {
        knots[0]
    } else if after {
        knots[N - 1]
    } else {
        value
    };
    // Use the final valid cell at the endpoint. Native reads a zero-weight
    // adjacent cell beyond the last axis point; bounded storage avoids that.
    let index = if before || value == knots[0] {
        0
    } else if after || value == knots[N - 1] {
        N - 2
    } else {
        knots
            .iter()
            .position(|&v| if descending { clamped > v } else { clamped < v })
            .ok_or(InvalidInput::Length)?
            - 1
    };
    let width = knots[index + 1] - knots[index];
    let delta = clamped - knots[index];
    Ok((
        index,
        (width - delta) / width,
        delta / width,
        clamped,
        before || after,
    ))
}

/// Row-major bilinear lookup with native product/FMA order. Inputs outside
/// either axis retain their offset from its endpoint after lookup.
pub fn shift(lut: &Lut, input: [f32; 2]) -> Result<[f32; 2], InvalidInput> {
    if lut
        .mapped_x
        .iter()
        .chain(&lut.mapped_y)
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    let (x, left, right, cx, out_x) = axis(&lut.x, input[0])?;
    let (y, lower, upper, cy, out_y) = axis(&lut.y, input[1])?;
    // Native's final point uses the following axis/table word as a phantom
    // next knot. Equal values make its zero-weight calculation divide 0/0.
    if (cx == lut.x[8] && lut.y[0] - lut.x[8] == 0.)
        || (cy == lut.y[10] && lut.mapped_x[0] - lut.y[10] == 0.)
    {
        return Err(InvalidInput::DegenerateRange);
    }
    let interpolate = |table: &[f32; 99]| {
        let at = y * 9 + x;
        let low = libm::fmaf(left, table[at], right * table[at + 1]);
        let high = libm::fmaf(left, table[at + 9], right * table[at + 10]);
        libm::fmaf(upper, high, lower * low)
    };
    let mut output = [interpolate(&lut.mapped_x), interpolate(&lut.mapped_y)];
    if out_x {
        output[0] = input[0] + (output[0] - cx);
    }
    if out_y {
        output[1] = input[1] + (output[1] - cy);
    }
    if output.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    Ok(output)
}

#[derive(Clone, Debug, PartialEq)]
pub struct State {
    pub gain: Gains,
    /// Native CCT/CCRI value caches; padding/undefined validity words are not
    /// part of the value API. Direct-ratio mode preserves both caches.
    pub before: [f32; 2],
    pub after: [f32; 2],
}
pub struct Settings {
    pub temperature_mode: bool,
    pub sample: f32,
    pub first: Line,
    pub second: Line,
}
impl State {
    pub fn adjust(&mut self, luts: &[Lut], settings: &Settings) -> Result<(), InvalidInput> {
        let mut next = self.clone();
        let input = if settings.temperature_mode {
            let temperature =
                awb_single_color::color_temperature(self.gain, settings.first, settings.second)?;
            next.before = [temperature.cct, temperature.ccri];
            next.before
        } else {
            if self.gain.iter().any(|v| !v.is_finite()) {
                return Err(InvalidInput::NonFinite);
            }
            if (self.gain[1] as f64) < 0.00001 || (self.gain[2] as f64) < 0.00001 {
                return Ok(());
            }
            [self.gain[0] / self.gain[1], self.gain[3] / self.gain[2]]
        };
        if luts.is_empty() {
            return Err(InvalidInput::Length);
        }
        if !settings.sample.is_finite() || luts.iter().any(|v| !v.sample.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        if luts.windows(2).any(|v| v[0].sample > v[1].sample) {
            return Err(InvalidInput::NonIncreasing);
        }
        let output = if settings.sample <= luts[0].sample || luts.len() == 1 {
            shift(&luts[0], input)?
        } else if settings.sample >= luts[luts.len() - 1].sample {
            shift(&luts[luts.len() - 1], input)?
        } else {
            let upper = luts
                .iter()
                .position(|v| settings.sample < v.sample)
                .unwrap();
            let lower = upper - 1;
            let low = shift(&luts[lower], input)?;
            let high = shift(&luts[upper], input)?;
            let width = luts[upper].sample - luts[lower].sample;
            if (width as f64) >= 0.00001 {
                let weight = (settings.sample - luts[lower].sample) / width;
                core::array::from_fn(|i| libm::fmaf(weight, high[i] - low[i], low[i]))
            } else {
                low
            }
        };
        if settings.temperature_mode {
            next.after = output;
            (next.gain, _) = awb_single_color::gain_from_color_temperature(
                ColorTemperature {
                    valid: true,
                    cct: output[0],
                    ccri: output[1],
                },
                settings.first,
                settings.second,
                self.gain,
            )?;
        } else {
            next.gain = [output[0], 1., 1., output[1]];
        }
        if next.gain.iter().any(|v| !v.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        *self = next;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn native_endpoint_nan_is_rejected_without_changing_gain_or_caches() {
        let lut = Lut {
            sample: 0.,
            x: core::array::from_fn(|i| 2.5 - i as f32 * 0.25),
            y: core::array::from_fn(|i| 0.5 + i as f32 * 0.25),
            mapped_x: [1.; 99],
            mapped_y: [1.; 99],
        };
        let mut state = State {
            gain: [0.5, 1., 1., 0.5],
            before: [12., 13.],
            after: [14., 15.],
        };
        let before = state.clone();
        let line = Line {
            a: 0.,
            b: 0.,
            c: 0.,
            valid: false,
        };
        let settings = Settings {
            temperature_mode: false,
            sample: 0.,
            first: line,
            second: line,
        };
        assert_eq!(
            state.adjust(&[lut], &settings),
            Err(InvalidInput::DegenerateRange)
        );
        assert_eq!(state, before);
    }
}

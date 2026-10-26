//! Recovered AecDynamicDamp. This computes a coefficient, not sensor settings.
use crate::InvalidInput;

#[derive(Clone, Copy, Debug)]
pub enum Mode {
    Default,
    /// Native mode 2 replaces the brightness scale and middle rule value.
    Custom {
        scale: f32,
        middle: f32,
    },
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Diagnostics {
    /// The native routine stores these in the oldest history slot after walking
    /// nine differences, rather than in the current frame's slot.
    pub slot: usize,
    pub trend: f32,
    pub normalized_trend: f32,
    pub normalized_current: f32,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Output {
    pub coefficient: f32,
    pub diagnostics: Option<Diagnostics>,
}

pub fn calculate(
    coefficient: f32,
    scale: f32,
    enabled: bool,
    mode: Mode,
    frame: u32,
    history: &[f32; 10],
) -> Result<Output, InvalidInput> {
    if !coefficient.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if !enabled {
        return Ok(Output {
            coefficient,
            diagnostics: None,
        });
    }
    let (scale, middle, adjacent) = match mode {
        Mode::Default => (
            scale,
            (coefficient + 2.) / 3.,
            libm::fmaf(coefficient, 2., 1.) / 3.,
        ),
        Mode::Custom { scale, middle } => (scale, middle, (coefficient + middle) * 0.5),
    };
    if !scale.is_finite()
        || !middle.is_finite()
        || !adjacent.is_finite()
        || history.iter().any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if scale <= 0. || frame > i32::MAX as u32 {
        return Err(InvalidInput::Exposure);
    }
    let mut index = frame as usize % 10;
    let current = history[index];
    let mut trend = 0.;
    for weight in (2..=10).rev() {
        let previous = (index + 9) % 10;
        trend = libm::fmaf(history[index] - history[previous], weight as f32, trend);
        index = previous;
    }
    trend /= 54.;
    let x = (current / (scale / 100.)).clamp(-4., 4.);
    let y = (trend / 0.03).clamp(-4., 4.);
    if !trend.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let mut table = [coefficient; 81];
    for i in [3, 4, 11, 20, 28, 38, 42, 52, 60, 69, 76, 77] {
        table[i] = adjacent;
    }
    for i in [12, 13, 21, 22, 29, 30, 39, 41, 50, 51, 58, 59, 67, 68] {
        table[i] = middle;
    }
    for i in [31, 40, 49] {
        table[i] = 1.;
    }
    let weights = |v: f32| {
        if v >= 4. {
            (7usize, 8usize, 0., 1.)
        } else {
            let lo = libm::floorf(v) as i32;
            let low_weight = (v - (lo + 1) as f32) / -1.;
            (
                (lo + 4) as usize,
                (lo + 5) as usize,
                low_weight,
                1. - low_weight,
            )
        }
    };
    let (xl, xh, wl, wh) = weights(x);
    let (yl, yh, vl, vh) = weights(y);
    let low = libm::fmaf(vl, table[yl * 9 + xl], vh * table[yh * 9 + xl]);
    let high = libm::fmaf(vl, table[yl * 9 + xh], vh * table[yh * 9 + xh]);
    let result = libm::fmaf(low, wl, high * wh);
    Ok(Output {
        coefficient: result,
        diagnostics: Some(Diagnostics {
            slot: index,
            trend,
            normalized_trend: y,
            normalized_current: x,
        }),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn disabled_preserves_coefficient_without_reading_inactive_state() {
        let out = calculate(
            0.625,
            f32::NAN,
            false,
            Mode::Default,
            u32::MAX,
            &[f32::NAN; 10],
        )
        .unwrap();
        assert_eq!(
            out,
            Output {
                coefficient: 0.625,
                diagnostics: None
            }
        );
    }
    #[test]
    fn stable_zero_history_selects_center_rule_and_oldest_slot() {
        for frame in 0..20 {
            let out = calculate(0.2, 30., true, Mode::Default, frame, &[0.; 10]).unwrap();
            assert_eq!(out.coefficient, 1.);
            assert_eq!(out.diagnostics.unwrap().slot, (frame as usize + 1) % 10);
        }
    }
    #[test]
    fn invalid_active_scale_is_rejected() {
        assert_eq!(
            calculate(0.2, 0., true, Mode::Default, 0, &[0.; 10]),
            Err(InvalidInput::Exposure)
        );
        assert_eq!(
            calculate(
                0.2,
                30.,
                true,
                Mode::Custom {
                    scale: 0.,
                    middle: 0.5
                },
                0,
                &[0.; 10]
            ),
            Err(InvalidInput::Exposure)
        );
    }
}

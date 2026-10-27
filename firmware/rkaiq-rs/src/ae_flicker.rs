//! Flicker-quantum selection in AecUpdateConfig (ELF 0xa9068). This does not
//! implement minimum/maximum shutter policy or automatic flicker detection.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub quantum: f32,
    pub alternate: f32,
    pub frequency_selector: i32,
}
#[derive(Clone, Copy, Debug)]
pub struct LineTiming {
    pub line_length: f32,
    pub pixel_clock_mhz: f32,
    pub coefficient: f32,
}
pub fn select(
    previous: State,
    enabled: bool,
    frequency_selector: i32,
    detected_period: f32,
    timing: Option<LineTiming>,
) -> Result<State, InvalidInput> {
    if !detected_period.is_finite()
        || !previous.quantum.is_finite()
        || !previous.alternate.is_finite()
    {
        return Err(InvalidInput::NonFinite);
    }
    let mut next = State {
        frequency_selector,
        ..previous
    };
    if !enabled {
        let t = timing.ok_or(InvalidInput::Length)?;
        if !t.line_length.is_finite()
            || !t.pixel_clock_mhz.is_finite()
            || !t.coefficient.is_finite()
        {
            return Err(InvalidInput::NonFinite);
        }
        if t.pixel_clock_mhz <= 0. || t.coefficient == 0. || t.line_length <= 0. {
            return Err(InvalidInput::Exposure);
        }
        next.frequency_selector = 0;
        next.quantum = ((t.line_length / (t.pixel_clock_mhz * 1_000_000.)) / t.coefficient).abs();
        if !next.quantum.is_finite() || next.quantum <= 0. {
            return Err(InvalidInput::Exposure);
        }
        return Ok(next);
    }
    let sixty = if frequency_selector == 2 {
        true
    } else if frequency_selector == 3 {
        let period = detected_period as f64;
        let epsilon = f32::EPSILON as f64;
        if detected_period.abs() <= f32::EPSILON || (period - 0.01).abs() <= epsilon {
            false
        } else if (period - 1.0 / 120.0).abs() <= epsilon {
            true
        } else {
            return Ok(next);
        }
    } else {
        false
    };
    (next.quantum, next.alternate) = if sixty {
        (1.0f32 / 120.0, 0.01)
    } else {
        (0.01, 1.0f32 / 120.0)
    };
    Ok(next)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unknown_detected_period_preserves_previous_pair() {
        let previous = State {
            quantum: 0.012,
            alternate: 0.013,
            frequency_selector: 1,
        };
        let next = select(previous, true, 3, 0.02, None).unwrap();
        assert_eq!(next.quantum, previous.quantum);
        assert_eq!(next.alternate, previous.alternate);
        assert_eq!(next.frequency_selector, 3);
        assert!(select(previous, false, 1, 0., None).is_err());
    }
}

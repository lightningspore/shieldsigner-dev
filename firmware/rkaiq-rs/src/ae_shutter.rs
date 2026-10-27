//! Linear fixed-frame shutter-bound subset of AecUpdateConfig (ELF 0xa9068).
//! FPS selection, HDR, gain/DCG bounds and frame scheduling remain separate.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Input {
    pub frame_length: f32,
    pub line_length: f32,
    pub pixel_clock_mhz: f32,
    pub factors: [f32; 4],
    pub minimum_register: u16,
    pub maximum_register_factors: [f32; 2],
    pub route_minimum: f32,
    pub route_maximum: f32,
    /// Native zero-valued override entries mean no override for that bound.
    pub overrides: Option<[f32; 2]>,
    /// Quantum plus the native explicit-minimum mode (mode selector == 1).
    pub flicker: Option<(f32, bool)>,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Bounds {
    pub minimum: f32,
    pub maximum: f32,
    pub physical_minimum: f32,
    pub physical_maximum: f32,
}
pub fn fixed_frame(input: Input) -> Result<Bounds, InvalidInput> {
    let i = input;
    let values = [
        i.frame_length,
        i.line_length,
        i.pixel_clock_mhz,
        i.route_minimum,
        i.route_maximum,
        i.factors[0],
        i.factors[1],
        i.factors[2],
        i.factors[3],
        i.maximum_register_factors[0],
        i.maximum_register_factors[1],
    ];
    if values.iter().any(|v| !v.is_finite())
        || i.overrides
            .is_some_and(|v| v.iter().any(|v| !v.is_finite()))
        || i.flicker.is_some_and(|(q, _)| !q.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if i.frame_length <= 0.
        || i.line_length <= 0.
        || i.pixel_clock_mhz <= 0.
        || i.factors[2] == 0.
        || i.route_minimum < 0.
        || i.route_maximum < i.route_minimum
        || i.minimum_register == 0
        || i.flicker.is_some_and(|(q, _)| q <= 0.)
    {
        return Err(InvalidInput::Exposure);
    }
    let clock = i.pixel_clock_mhz * 1_000_000.;
    let physical_minimum =
        (((i.minimum_register as f32 * i.line_length) / clock) / i.factors[2]).abs();
    let numerator = (libm::fmaf(
        i.frame_length,
        i.maximum_register_factors[0],
        -i.maximum_register_factors[1],
    ) - i.frame_length * i.factors[0])
        - i.factors[1];
    let physical_maximum = ((numerator / i.factors[2]) * i.line_length) / clock;
    if !physical_minimum.is_finite() || !physical_maximum.is_finite() || physical_maximum <= 0. {
        return Err(InvalidInput::Exposure);
    }
    let overrides = i.overrides.unwrap_or([0.; 2]);
    let mut minimum = if overrides[0] == 0. {
        i.route_minimum.max(physical_minimum)
    } else {
        overrides[0].max(physical_minimum)
    };
    if let Some((quantum, true)) = i.flicker {
        minimum = physical_minimum.max(quantum);
    }
    let mut maximum = if overrides[1] == 0. {
        i.route_maximum.min(physical_maximum)
    } else {
        overrides[1].min(physical_maximum)
    };
    if maximum <= minimum {
        if minimum <= physical_maximum {
            maximum = minimum;
        } else {
            minimum = maximum;
        }
    }
    if let Some((quantum, _)) = i.flicker {
        if quantum < maximum {
            let residual = libm::fmaf(quantum, libm::ceilf(maximum / quantum), -maximum);
            let tolerance = ((i.maximum_register_factors[1] as f64 * 1.5) * i.line_length as f64)
                / clock as f64;
            if residual as f64 >= tolerance {
                maximum = quantum * libm::floorf(maximum / quantum);
            }
        }
        if minimum >= maximum {
            minimum = maximum;
        }
    }
    Ok(Bounds {
        minimum,
        maximum,
        physical_minimum,
        physical_maximum,
    })
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_zero_time_coefficient() {
        let input = Input {
            frame_length: 1320.,
            line_length: 2500.,
            pixel_clock_mhz: 99.,
            factors: [0., 0., 0., 0.5],
            minimum_register: 1,
            maximum_register_factors: [1., 8.],
            route_minimum: 0.,
            route_maximum: 0.03,
            overrides: None,
            flicker: None,
        };
        assert!(fixed_frame(input).is_err());
    }
}

//! Linear, DCG-disabled gain bounds from AecUpdateConfig (ELF 0xa9068).
use crate::InvalidInput;
#[derive(Clone, Copy, Debug)]
pub struct Input {
    pub analogue: [f32; 2],
    pub digital: [f32; 2],
    pub isp: [f32; 2],
    pub route_gain: [f32; 2],
    pub route_isp: [f32; 2],
    /// Gain minimum/maximum followed by ISP minimum/maximum; zero falls back.
    pub overrides: Option<[f32; 4]>,
}
#[derive(Clone, Copy, Debug)]
pub struct Bounds {
    pub physical_gain: [f32; 2],
    pub gain: [f32; 2],
    pub isp: [f32; 2],
}
pub fn linear(input: Input) -> Result<Bounds, InvalidInput> {
    for r in [
        input.analogue,
        input.digital,
        input.isp,
        input.route_gain,
        input.route_isp,
    ] {
        if r.iter().any(|v| !v.is_finite()) {
            return Err(InvalidInput::NonFinite);
        }
        if r[0] <= 0. || r[0] > r[1] {
            return Err(InvalidInput::GainRange);
        }
    }
    let overrides = input.overrides.unwrap_or([0.; 4]);
    if overrides.iter().any(|v| !v.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    if overrides.iter().any(|v| *v < 0.) {
        return Err(InvalidInput::GainRange);
    }
    let physical_gain = [
        input.analogue[0] * input.digital[0],
        input.analogue[1] * input.digital[1],
    ];
    if physical_gain.iter().any(|v| !v.is_finite()) || physical_gain[0] <= 0. {
        return Err(InvalidInput::GainRange);
    }
    let select = |physical: [f32; 2], route: [f32; 2], o: &[f32]| {
        let maximum = physical[1].min(if o[1] == 0. { route[1] } else { o[1] });
        let minimum = physical[0]
            .max(if o[0] == 0. { route[0] } else { o[0] })
            .min(maximum);
        [minimum, maximum]
    };
    Ok(Bounds {
        physical_gain,
        gain: select(physical_gain, input.route_gain, &overrides[..2]),
        isp: select(input.isp, input.route_isp, &overrides[2..]),
    })
}

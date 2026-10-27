//! Linear convergence flags in AecGetProcResults (ELF 0xb1e70).
//! Sensor-code and ISP-gain equality gates the next processing/damping policy.
use crate::InvalidInput;

#[derive(Clone, Copy, Debug)]
pub struct Exposure {
    pub time_code: u32,
    pub gain_code: u32,
    pub isp_gain: f32,
}
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub dynamic_enabled: u8,
    pub gating_enabled: u8,
}
/// `effective` is the preprocessing exposure; `proposed` is the newly computed
/// output; `published` is the prior published exposure. Publication/association
/// of these records is outside this helper.
pub fn linear(
    state: &mut State,
    effective: Exposure,
    proposed: Exposure,
    published: Exposure,
) -> Result<(), InvalidInput> {
    if [effective.isp_gain, proposed.isp_gain, published.isp_gain]
        .iter()
        .any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if proposed.isp_gain < 0. || published.isp_gain < 0. || effective.isp_gain < 0. {
        return Err(InvalidInput::Exposure);
    }
    let equal = effective.time_code == proposed.time_code
        && effective.gain_code == proposed.gain_code
        && effective.time_code == published.time_code
        && effective.gain_code == published.gain_code
        && f64::from((effective.isp_gain - published.isp_gain).abs())
            <= f64::from(published.isp_gain) * 0.001
        && f64::from((effective.isp_gain - proposed.isp_gain).abs())
            <= f64::from(proposed.isp_gain) * 0.001;
    if equal {
        state.dynamic_enabled = 1;
        state.gating_enabled = 1;
    } else {
        // Native mismatch clears only +0x4fb9. Dynamic enable is sticky.
        state.gating_enabled = 0;
    }
    Ok(())
}

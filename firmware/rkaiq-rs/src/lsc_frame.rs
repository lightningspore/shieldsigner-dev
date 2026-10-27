//! Persistent normal-case, no-OTP LSC automatic processing callback.
use crate::{
    isp_lsc::RESULT_BYTES, lsc_calibration::Automatic, lsc_damping, lsc_illuminant, lsc_tables,
    InvalidInput,
};
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Information {
    pub current: [f32; 3],
    pub damping: f32,
    pub force: bool,
    pub bypass: bool,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub history: lsc_illuminant::State,
    pub target: [u16; lsc_tables::SAMPLES],
    pub current: [u16; lsc_tables::SAMPLES],
    pub last_gain: f32,
    pub last_wb: [f32; 2],
    pub effective_wb: [f32; 2],
    pub vignetting: f32,
    pub illuminant: usize,
    pub high: [u8; 32],
    pub low: [u8; 32],
    pub converged: bool,
    pub input_changed: bool,
    pub frame_count: u32,
    pub force: bool,
}
impl Default for State {
    fn default() -> Self {
        Self {
            history: Default::default(),
            target: [0; lsc_tables::SAMPLES],
            current: [0; lsc_tables::SAMPLES],
            last_gain: -1.,
            last_wb: [-1.; 2],
            effective_wb: [0.; 2],
            vignetting: 0.,
            illuminant: 0,
            high: [0; 32],
            low: [0; 32],
            converged: false,
            input_changed: true,
            frame_count: 0,
            force: true,
        }
    }
}
impl State {
    /// Transactional proposal: caller commits this state only after successful
    /// hardware submission. No publication preserves every caller output byte.
    pub fn process(
        &mut self,
        cal: &Automatic,
        info: Information,
        output: &mut [u8; RESULT_BYTES],
    ) -> Result<bool, InvalidInput> {
        if info.current.iter().any(|n| !n.is_finite()) || !info.damping.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if !(0. ..=1.).contains(&info.damping) {
            return Err(InvalidInput::AlphaRange);
        }
        if cal.illuminants.is_empty() || cal.illuminants.len() > 7 {
            return Err(InvalidInput::Length);
        }
        let mut next = *self;
        next.force |= info.force;
        let enabled = cal.enabled && !info.bypass;
        let mut updated = false;
        if enabled {
            let gain_changed = (info.current[0] - next.last_gain).abs() > 0.2;
            if gain_changed {
                next.last_gain = info.current[0];
            }
            let red = next.last_wb[0] - info.current[1];
            let blue = next.last_wb[1] - info.current[2];
            let wb_changed = 0.05f32 * 0.05 < libm::fmaf(red, red, blue * blue);
            if wb_changed {
                next.last_wb = [info.current[1], info.current[2]];
            }
            next.effective_wb = next.last_wb;
            next.input_changed = gain_changed || wb_changed;
            if next.input_changed || !next.converged || next.force {
                let mut wb = [[0.; 2]; 7];
                for (out, ill) in wb.iter_mut().zip(&cal.illuminants) {
                    *out = ill.wb;
                }
                if let Some(estimate) = next
                    .history
                    .process(&wb[..cal.illuminants.len()], next.effective_wb)?
                {
                    let ill = &cal.illuminants[estimate.selected];
                    let vignetting = crate::interpolate(&ill.gains, &ill.vig, info.current[0])?;
                    let near = ((next.vignetting - vignetting).abs() as f64) <= 0.00001;
                    let mut target_changed = false;
                    if next.force || !near || next.illuminant != estimate.selected {
                        if ill.tables.is_empty() || ill.tables.len() > lsc_tables::MAX_PROFILES {
                            return Err(InvalidInput::Length);
                        }
                        let profiles = core::array::from_fn::<_, 5, _>(|i| {
                            let p = &ill.tables[if i < ill.tables.len() { i } else { 0 }];
                            lsc_tables::Profile {
                                vignetting: p.vignetting,
                                samples: &p.samples,
                            }
                        });
                        let selected =
                            lsc_tables::select(&profiles[..ill.tables.len()], vignetting)?;
                        let high = ill.tables[selected.high].name;
                        let low = ill.tables[selected.low].name;
                        target_changed =
                            next.force || !near || high != next.high || low != next.low;
                        next.vignetting = vignetting;
                        next.illuminant = estimate.selected;
                        if target_changed {
                            next.high = high;
                            next.low = low;
                            next.target = selected.samples;
                        }
                    }
                    if target_changed || !next.converged {
                        next.converged = lsc_damping::process(
                            &mut next.current,
                            &next.target,
                            info.damping,
                            cal.damping_enabled,
                            next.frame_count,
                        )?;
                        updated = true;
                    }
                }
            }
        } else {
            updated = next.force;
        }
        next.force = false;
        next.frame_count = if next.frame_count < 65535 {
            next.frame_count + 1
        } else {
            2
        };
        if updated {
            *output = cal.result(&next.current, enabled);
        }
        *self = next;
        Ok(updated)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    extern crate alloc;
    #[test]
    fn invalid_proposal_preserves_state_and_result() {
        let cal = Automatic {
            enabled: true,
            damping_enabled: true,
            resolution: [0; 32],
            sectors: [[1; 16]; 2],
            gradients: [[32768; 16]; 2],
            illuminants: alloc::vec![],
        };
        let mut state = State::default();
        let before = state;
        let mut result = [0xa5; RESULT_BYTES];
        let info = Information {
            current: [1.; 3],
            damping: f32::NAN,
            force: true,
            bypass: false,
        };
        assert_eq!(
            state.process(&cal, info, &mut result),
            Err(InvalidInput::NonFinite)
        );
        assert_eq!(state, before);
        assert_eq!(result, [0xa5; RESULT_BYTES]);
    }
}

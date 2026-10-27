//! Supported automatic CCM AccmConfig/AccmAutoConfig composition.
//! Default user inhibition=0/saturation=50; symmetric, non-blended IQ only.
use crate::{
    ccm_calibration::Automatic, ccm_damping, ccm_input, ccm_luma, ccm_runtime, ccm_saturation,
    interpolate, isp_ccm::RESULT_BYTES, InvalidInput,
};
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub result: [u8; RESULT_BYTES],
    pub selection: ccm_runtime::State,
    pub baseline: [f32; 3],
    pub current: [f32; 3],
    pub converged: bool,
    pub frames: u32,
    pub alpha: f32,
    pub saturation: f32,
    pub previous_luma_weight: f32,
    pub previous_luma_upper: usize,
    pub inputs_changed: bool,
    pub published: bool,
}
fn get(result: &[u8; RESULT_BYTES], offset: usize) -> f32 {
    f32::from_le_bytes(result[offset..offset + 4].try_into().unwrap())
}
fn put(result: &mut [u8; RESULT_BYTES], offset: usize, value: f32) {
    result[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
impl State {
    /// Explicit ConfigbyCalib-compatible initial state, not a native ABI object.
    pub fn new(cal: &Automatic) -> Self {
        let mut result = cal.static_result;
        for i in 0..17 {
            put(&mut result, 56 + i * 4, cal.luma[0].curve[i]);
        }
        result[2..4].copy_from_slice(&u16::from(cal.enhancement_enabled).to_le_bytes());
        put(&mut result, 152, cal.enhancement_ratios[0]);
        Self {
            result,
            selection: ccm_runtime::State {
                illuminant: 0,
                saturation: 0.,
                high_name: [0; 25],
                low_name: [0; 25],
                matrix: [0.; 9],
                offsets: [0.; 3],
            },
            baseline: [1.; 3],
            current: [1.; 3],
            converged: false,
            frames: 0,
            alpha: 1.,
            saturation: 100.,
            previous_luma_weight: 0.,
            previous_luma_upper: 0,
            inputs_changed: false,
            published: true,
        }
    }
    /// `active` is native context byte 0x55c; `prior_publish` is externally owned
    /// context byte 0x560. Outer reconfiguration/attribute flags are explicit.
    /// Commit all state only after the supported configuration succeeds.
    pub fn process(
        &mut self,
        cal: &Automatic,
        current: [f32; 3],
        damping: f32,
        active: bool,
        attributes_changed: bool,
        reconfigure: bool,
        gray: bool,
        prior_publish: bool,
    ) -> Result<(), InvalidInput> {
        let mut next = *self;
        next.current = current;
        next.published = prior_publish;
        if current.iter().any(|v| !v.is_finite()) || !damping.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        if current[0] < 1. || !(0. ..=1.).contains(&damping) {
            return Err(InvalidInput::GainRange);
        }
        if cal.enabled && !gray {
            next.result[0] = 1;
            let changed = ccm_input::filter(
                &mut next.baseline,
                &mut next.current,
                cal.gain_tolerance,
                cal.wb_tolerance,
            )?;
            next.inputs_changed = changed || reconfigure;
            if attributes_changed || next.inputs_changed || !next.converged {
                next.automatic(cal, damping, active, attributes_changed, reconfigure)?;
            }
        } else {
            next.result[0] = 0;
            next.published |= attributes_changed || reconfigure;
        }
        next.frames = if next.frames.wrapping_add(2) < 0x10001 {
            next.frames.wrapping_add(1)
        } else {
            2
        };
        *self = next;
        Ok(())
    }
    fn automatic(
        &mut self,
        cal: &Automatic,
        damping: f32,
        active: bool,
        attributes_changed: bool,
        reconfigure: bool,
    ) -> Result<(), InvalidInput> {
        let gain = self.current[0];
        let mut selected = false;
        let mut curve_changed = false;
        if self.inputs_changed {
            self.selection.process(
                &cal.views(),
                gain,
                [self.current[1], self.current[2]],
                reconfigure,
                self.published,
                &mut selected,
            )?;
        }
        if self.inputs_changed || attributes_changed {
            let alpha = interpolate(&cal.alpha_gains, &cal.alpha_scales, gain)?;
            let mut curve = [0.; 17];
            for i in 0..17 {
                curve[i] = get(&self.result, 56 + i * 4);
            }
            let luma_changed = ccm_luma::symmetric(
                &cal.luma,
                gain * 50.,
                self.previous_luma_weight,
                self.previous_luma_upper,
                !active || reconfigure,
                &mut curve,
            )?;
            for i in 0..17 {
                put(&mut self.result, 56 + i * 4, curve[i]);
            }
            if selected
                || ((alpha - self.alpha).abs() as f64) > 0.00001
                || ((50. - self.saturation).abs() as f64) > 0.00001
            {
                self.alpha = alpha;
                self.saturation = 50.;
                ccm_saturation::apply(&mut self.selection.matrix, alpha, 50.)?;
                for i in 0..18 {
                    let value = get(&self.result, 56 + i * 4) * alpha;
                    put(&mut self.result, 56 + i * 4, value);
                }
                if !active {
                    self.restore_static(cal);
                }
                curve_changed = true;
                selected = true;
            } else if !active {
                self.restore_static(cal);
                curve_changed = true;
                selected = true;
            } else {
                curve_changed = luma_changed;
            }
        }
        let factor = if cal.damping_enabled && self.frames >= 2 && active {
            damping
        } else {
            0.
        };
        let mut did_damp = false;
        if !self.converged || selected {
            let mut actual = ccm_damping::State {
                matrix: [0.; 9],
                offsets: [0.; 3],
            };
            for i in 0..9 {
                actual.matrix[i] = get(&self.result, 8 + i * 4);
            }
            for i in 0..3 {
                actual.offsets[i] = get(&self.result, 44 + i * 4);
            }
            self.converged = actual.process(
                &ccm_damping::State {
                    matrix: self.selection.matrix,
                    offsets: self.selection.offsets,
                },
                factor,
            )?;
            for i in 0..9 {
                put(&mut self.result, 8 + i * 4, actual.matrix[i]);
            }
            for i in 0..3 {
                put(&mut self.result, 44 + i * 4, actual.offsets[i]);
            }
            did_damp = true;
        }
        let mut enhance_changed = false;
        if self.inputs_changed || !active {
            let ratio = if cal.enhancement_enabled {
                interpolate(&cal.enhancement_gains, &cal.enhancement_ratios, gain)?
            } else {
                0.
            };
            let enabled = u16::from_le_bytes(self.result[2..4].try_into().unwrap());
            if enabled != u16::from(cal.enhancement_enabled)
                || ((ratio - get(&self.result, 152)).abs() as f64) > 0.00001
            {
                self.result[2..4]
                    .copy_from_slice(&u16::from(cal.enhancement_enabled).to_le_bytes());
                put(&mut self.result, 152, ratio);
                enhance_changed = true;
            }
        }
        self.published |= did_damp || curve_changed || enhance_changed;
        Ok(())
    }
    fn restore_static(&mut self, cal: &Automatic) {
        for range in [1..2, 4..5, 124..151] {
            self.result[range.clone()].copy_from_slice(&cal.static_result[range]);
        }
    }
}

#[cfg(test)]
mod tests {
    extern crate alloc;
    use super::*;
    use crate::{
        ccm_calibration::OwnedIlluminant, ccm_luma::Row, ccm_runtime::NamedProfile,
        ccm_selection::Profile,
    };
    use alloc::vec;
    #[test]
    fn late_configuration_error_does_not_commit_partial_state() {
        let cal = Automatic {
            enabled: true,
            damping_enabled: true,
            enhancement_enabled: false,
            wb_tolerance: 0.,
            gain_tolerance: 0.2,
            illuminants: vec![OwnedIlluminant {
                gains: [1., 1.],
                sensor_gains: [1., 2., 4., 8.],
                saturations: [100.; 4],
                profiles: vec![NamedProfile {
                    name: [0; 25],
                    profile: Profile {
                        saturation: 100.,
                        matrix: [1.; 9],
                        offsets: [0.; 3],
                    },
                }],
            }],
            luma: core::array::from_fn(|i| Row {
                iso: 50. * (i + 1) as f32,
                curve: [100.; 17],
            }),
            alpha_gains: [1., 2., 4., 8., 16., 32., 64., 128., 256.],
            alpha_scales: [2.; 9],
            enhancement_gains: [1., 2., 4., 8., 16., 32., 64., 128., 256.],
            enhancement_ratios: [0.; 9],
            static_result: [0; RESULT_BYTES],
        };
        let mut state = State::new(&cal);
        let before = state;
        assert!(state
            .process(&cal, [2., 1., 1.], 0.5, true, false, true, false, false)
            .is_err());
        assert_eq!(state, before);
    }
}

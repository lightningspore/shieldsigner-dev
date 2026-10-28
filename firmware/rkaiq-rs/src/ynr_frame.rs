//! Persistent prepared normal-exposure YNR processing callback.
use crate::{isp_ynr::RESULT_BYTES, ynr_calibration, ynr_quantize, ynr_selection};
extern crate alloc;
use alloc::{format, string::String};
use serde_json::Value;
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Information {
    pub seconds: f32,
    pub gains: [f32; 3],
    pub blc_predgain: f32,
    pub snr_mode: u8,
    pub gray: bool,
    pub force: bool,
}
impl Information {
    /// Caller must verify NR-switch availability. This supports the selected
    /// no-switch path, using associated AE fields and native signed-DCG SNR.
    pub fn from_record(
        record: &crate::ae_publication::Record,
        blc_predgain: f32,
    ) -> Result<Self, String> {
        let mut exposure = *record;
        let snr_mode = crate::ae_cis::normal(&mut exposure, None)
            .map_err(|e| format!("YNR sensor metadata: {e:?}"))?;
        Ok(Self {
            seconds: f32_at(record, 0),
            gains: core::array::from_fn(|i| f32_at(record, 4 + i * 4)),
            blc_predgain,
            snr_mode,
            gray: false,
            force: false,
        })
    }
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub table: [u8; ynr_selection::TABLE_BYTES],
    pub selected: [u8; ynr_selection::ROW_BYTES],
    pub exposure: [u8; 88],
    pub strength: [u8; 16],
    pub gray: bool,
    pub parameter_mode: i32,
    pub recalculate: bool,
    pub geometry: [u32; 2],
}
fn i32_at(b: &[u8], p: usize) -> i32 {
    i32::from_le_bytes(b[p..p + 4].try_into().unwrap())
}
fn f32_at(b: &[u8], p: usize) -> f32 {
    f32::from_bits(i32_at(b, p) as u32)
}
fn put_i32(b: &mut [u8], p: usize, n: i32) {
    b[p..p + 4].copy_from_slice(&n.to_le_bytes());
}
fn put_f32(b: &mut [u8], p: usize, n: f32) {
    b[p..p + 4].copy_from_slice(&n.to_le_bytes());
}
impl State {
    /// Prepared native defaults: HSNR/normal table, prior SNR one, zero prior
    /// exposure, enabled unit strength, forced first calculation. Auto mode only.
    pub fn new(calibration: &Value, geometry: [u32; 2]) -> Result<Self, String> {
        if geometry.iter().any(|n| *n == 0 || *n > 65535) {
            return Err("Invalid YNR raw geometry".into());
        }
        let mut state = Self {
            table: [0; ynr_selection::TABLE_BYTES],
            selected: [0; ynr_selection::ROW_BYTES],
            exposure: [0; 88],
            strength: [0; 16],
            gray: false,
            parameter_mode: 1,
            recalculate: true,
            geometry,
        };
        ynr_calibration::prepare(calibration, "HSNR", &mut state.table)?;
        put_i32(&mut state.exposure, 4, 1);
        put_f32(&mut state.strength, 8, 1.);
        state.strength[12] = 1;
        Ok(state)
    }
    pub fn seeded(
        calibration: &Value,
        information: Information,
        geometry: [u32; 2],
    ) -> Result<(Self, [u8; RESULT_BYTES]), String> {
        let mut state = Self::new(calibration, geometry)?;
        let mut result = [0; RESULT_BYTES];
        state.process(calibration, information, &mut result)?;
        Ok((state, result))
    }
    /// Stage state and output together; caller retains this proposal only after
    /// successful submission. No-update leaves all result bytes untouched.
    pub fn process(
        &mut self,
        calibration: &Value,
        information: Information,
        result: &mut [u8; RESULT_BYTES],
    ) -> Result<bool, String> {
        let info = information;
        if info.snr_mode > 1
            || !info.seconds.is_finite()
            || info.seconds <= 0.
            || !info.blc_predgain.is_finite()
            || info.gains.iter().any(|g| !g.is_finite())
        {
            return Err("Invalid normal YNR exposure metadata".into());
        }
        let gains = info.gains.map(|g| g.max(1.));
        let blc = info.blc_predgain.max(1.);
        // Native multiplies predgain and 50 before ISP digital gain. Reordering
        // can change the truncation at an ISO boundary.
        let iso_float = (((gains[0] * gains[1]) * blc) * 50.) * gains[2];
        if !iso_float.is_finite() || iso_float <= 0. || iso_float > i32::MAX as f32 {
            return Err("YNR ISO is not representable".into());
        }
        let iso = iso_float as i32;
        let mut exposure = [0; 88];
        put_i32(&mut exposure, 4, i32::from(info.snr_mode));
        for i in 0..3 {
            put_f32(
                &mut exposure,
                8 + i * 4,
                if i == 0 {
                    info.seconds
                } else {
                    f32::from_bits(0x3c23d70a)
                },
            );
            put_f32(
                &mut exposure,
                20 + i * 4,
                if i == 0 { gains[0] } else { 1. },
            );
            put_f32(
                &mut exposure,
                32 + i * 4,
                if i == 0 { gains[1] } else { 1. },
            );
            put_i32(&mut exposure, 60 + i * 4, if i == 0 { iso } else { 50 });
        }
        put_f32(&mut exposure, 44, gains[2]);
        put_f32(&mut exposure, 56, blc);
        let mut next = *self;
        next.recalculate |=
            info.force || next.gray != info.gray || f32_at(&next.exposure, 56) != info.blc_predgain;
        next.gray = info.gray;
        let difference = (i64::from(iso) - i64::from(i32_at(&next.exposure, 60))).abs();
        next.recalculate |= difference >= 11;
        let updated = next.recalculate;
        if updated {
            let parameter_mode = if info.gray { 3 } else { 1 };
            if i32_at(&next.exposure, 4) != i32::from(info.snr_mode)
                || next.parameter_mode != parameter_mode
            {
                next.parameter_mode = parameter_mode;
                ynr_calibration::prepare(
                    calibration,
                    if info.snr_mode == 0 { "LSNR" } else { "HSNR" },
                    &mut next.table,
                )?;
            }
            let [low, high] = ynr_selection::select(&next.table, iso, &mut next.selected)
                .map_err(|e| format!("YNR select: {e:?}"))?;
            put_i32(&mut exposure, 72, low as i32);
            put_i32(&mut exposure, 76, high as i32);
            put_i32(&mut exposure, 80, next.geometry[0] as i32);
            put_i32(&mut exposure, 84, next.geometry[1] as i32);
            next.exposure = exposure;
            let mut fixed = *result;
            ynr_quantize::quantize(&next.selected, &next.strength, &next.exposure, &mut fixed)
                .map_err(|e| format!("YNR quantize: {e:?}"))?;
            *result = fixed;
        }
        next.recalculate = false;
        *self = next;
        Ok(updated)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn failed_recalculation_preserves_controller_and_result() {
        let state = State {
            table: [0; ynr_selection::TABLE_BYTES],
            selected: [0; ynr_selection::ROW_BYTES],
            exposure: [0; 88],
            strength: [0; 16],
            gray: false,
            parameter_mode: 1,
            recalculate: true,
            geometry: [2304, 1296],
        };
        let mut current = state;
        let mut result = [0xa5; RESULT_BYTES];
        let info = Information {
            seconds: 0.003,
            gains: [1.; 3],
            blc_predgain: 1.,
            snr_mode: 0,
            gray: false,
            force: true,
        };
        assert!(current.process(&Value::Null, info, &mut result).is_err());
        assert_eq!(current, state);
        assert_eq!(result, [0xa5; RESULT_BYTES]);
    }
}

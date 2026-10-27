//! Persistent ordinary AE event loop. Statistics are corrected and associated
//! through the scheduler's own reported map; proposed batches become later SOF
//! writes. Startup sensor programming and ISP parameter programming are external.
extern crate alloc;
use crate::{
    ae_publication::Record,
    ae_session::{ParameterSnapshot, Session, StatisticsOutput},
    exposure_association, isp32, sensor,
    sensor_scheduler::{EffectPolicy, Outcome, Scheduler},
    sensor_submission,
    sensor_timing::Delays,
};
use alloc::{format, string::String, vec::Vec};

pub struct Runtime {
    pub session: Session,
    pub sensor: Scheduler<Record>,
    pub frame_length_mirror: Option<u32>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct IspGainOutput {
    pub exposure_frame: u32,
    pub exact_exposure: bool,
}
pub struct SofOutput<E> {
    /// Native scheduling state includes attempted exposures after writer errors.
    pub scheduled: Outcome<Record>,
    pub driver_error: Option<E>,
}
impl Runtime {
    /// The sensor must already be initialized. Supply its explicit initial
    /// effective record; creating the loop does not program that exposure.
    pub fn new(session: Session, initial: Record, policy: EffectPolicy) -> Result<Self, String> {
        let delays = session.scheduling_delays()?;
        let sensor = Scheduler::new(initial, delays, policy)
            .map_err(|e| format!("Sensor scheduling: {e:?}"))?;
        Ok(Self {
            session,
            sensor,
            frame_length_mirror: None,
        })
    }
    /// Apply gain results using the same effective exposure lookup as native
    /// setIspConfig. This merges into a caller-owned batch; the caller controls
    /// mask reset, frame ID, WB inclusion, pool reuse and driver submission.
    /// Do not substitute the latest proposed AE exposure for this lookup.
    pub fn apply_isp_gain_results(
        &self,
        frame: u32,
        parameters: &mut [u8; isp32::PARAMETER_BYTES],
        unscaled_wb: &mut [u8; isp32::AWB_GAIN_BYTES],
        white_balance: Option<isp32::WhiteBalanceGain>,
    ) -> Result<IspGainOutput, String> {
        let effective = self.sensor.effective().collect::<Vec<_>>();
        let frames = effective.iter().map(|e| e.frame).collect::<Vec<_>>();
        let selected = exposure_association::effective_index(&frames, frame)
            .map_err(|e| format!("ISP exposure lookup: {e:?}"))?
            .ok_or("No effective exposure for ISP gain")?;
        let entry = &effective[selected.index];
        let gain = f32::from_le_bytes(entry.exposure[12..16].try_into().unwrap());
        isp32::apply_gain_results(
            parameters,
            unscaled_wb,
            white_balance,
            Some(isp32::ExposureDigitalGain::Linear(gain)),
        )
        .map_err(|e| format!("ISP gain conversion: {e:?}"))?;
        Ok(IspGainOutput {
            exposure_frame: entry.frame,
            exact_exposure: selected.exact,
        })
    }
    pub fn on_sof<B: sensor::Backend>(
        &mut self,
        frame: u32,
        backend: &mut B,
    ) -> SofOutput<B::Error> {
        let mut error = None;
        let mirror = &mut self.frame_length_mirror;
        let scheduled = self.sensor.on_sof(frame, |record| {
            match sensor::program_linear(
                backend,
                sensor_submission::linear_controls(&record),
                mirror,
            ) {
                Ok(()) => 0,
                Err(e) => {
                    error = Some(e);
                    -9
                }
            }
        });
        SofOutput {
            scheduled,
            driver_error: error,
        }
    }
    /// The event owner orders statistics relative to SOFs. Missing measurements
    /// do not submit a new batch. Discard the runtime after a controller or queue
    /// error because subordinate updates are not transactional.
    pub fn step_statistics(
        &mut self,
        bytes: &[u8],
        parameters: &[ParameterSnapshot<'_>],
    ) -> Result<Option<StatisticsOutput>, String> {
        let effective = self.sensor.effective().collect::<Vec<_>>();
        let output = self
            .session
            .step_statistics(bytes, parameters, &effective)?;
        if let Some(out) = &output {
            let p = &out.control.publication;
            sensor_submission::submit(&mut self.sensor, &p.final_record, &p.records[..p.count])
                .map_err(|e| format!("Exposure submission: {e:?}"))?;
        }
        Ok(output)
    }
}
impl Session {
    /// Bind the actual sensor IQ delay fields to the recovered delay policy.
    /// These are declared scheduling delays, not measured application latency.
    pub fn scheduling_delays(&self) -> Result<Delays, String> {
        let values = self.sensor_update_delays();
        if values.iter().any(|v| *v > 10) {
            return Err("Sensor delay outside SDK range".into());
        }
        let mut delays = Delays {
            time: 0,
            gain: 0,
            dcg: 0,
            split_gain: false,
            split_dcg: false,
            dcg_with_time: false,
        };
        if delays.configure(values[0] as i32, values[1] as i32, values[2] as i32) != 0 {
            return Err("Unsupported sensor delay combination".into());
        }
        Ok(delays)
    }
}

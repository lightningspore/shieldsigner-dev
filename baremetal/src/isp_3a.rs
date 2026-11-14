// SPDX-License-Identifier: MIT
//! Exercise the existing calibrated sessions against real DUT ISP statistics.
//! Bounded feedback diagnostic; normal AWB time-share measurements; full Phase8 gate still separate.
use core::fmt::Write;
use shieldsigner_rkaiq as iq;
const PROFILE: &[u8] = include_bytes!("../.tools/sc3336-iq.json");
const PARAMETERS: &[u8; iq::isp32::PARAMETER_BYTES] =
    include_bytes!("../.tools/isp-initial-parameters.bin");
const AWB: &[u8; 1204] = include_bytes!("../.tools/isp-awb-sdk.bin");

pub struct Feedback {
    ae: iq::ae_session::Session,
    awb: iq::awb_session::Session,
    current_record: iq::ae_publication::Record,
    next_record: iq::ae_publication::Record,
    parameters: [u8; iq::isp32::PARAMETER_BYTES],
    active_parameters: [u8; iq::isp32::PARAMETER_BYTES],
    next_parameters: [u8; iq::isp32::PARAMETER_BYTES],
    cache: [u8; iq::isp32::AWB_GAIN_BYTES],
    measured_sdk: [u8; 1204],
    active_sdk: [u8; 1204],
    next_sdk: [u8; 1204],
    address: usize,
    pub index: u32,
}
impl Feedback {
    pub fn new(stats_address: usize, frame_us: u64) -> Result<Self, &'static str> {
        #[allow(unused_mut)] // runtime camera settings optionally override the profile's AE target.
        let mut profile: serde_json::Value =
            serde_json::from_slice(PROFILE).map_err(|_| "profile-json")?;
        #[cfg(feature = "runtime-board")]
        {
            let target = super::runtime::camera_target();
            if target != 0 {
                let points=profile.pointer_mut("/main_scene/0/sub_scene/0/scene_isp32/ae_calib/LinearAeCtrl/DySetpoint/DySetpoint")
                .and_then(serde_json::Value::as_array_mut).ok_or("ae-target-profile")?;
                for point in points {
                    *point = serde_json::Value::from(target);
                }
            }
        }
        let sensor = iq::calibration::SensorCalibration::from_value(&profile)
            .map_err(|_| "sensor-calibration")?;
        let hi = super::i2c::read_sensor(0x320c).map_err(|_| "hts-high")?;
        let lo = super::i2c::read_sensor(0x320d).map_err(|_| "hts-low")?;
        let hts = ((hi as u32) << 8 | lo as u32) * 2;
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_3A_TIMING_INPUT hi={} lo={} frame_us={}\r",
            hi,
            lo,
            frame_us
        );
        if hts == 0 || !(30_000..40_000).contains(&frame_us) {
            return Err("measured-timing");
        }
        // Effective pixel rate inferred from actual frame period and live HTS/VTS,
        // not the Linux driver's nominal pixel-rate control. Normal VTS1360.
        let timing = iq::calibration::RuntimeTiming {
            frame_length: super::camera::CONTROL_FRAME_LINES,
            pixel_clock_mhz: (hts as f32 * super::camera::CONTROL_FRAME_LINES as f32)
                / frame_us as f32,
            line_length_pixels: hts,
        };
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_3A_TIMING hts={} vts=1360 measured_frame_us={} effective_pixel_mhz={}\r",
            hts,
            frame_us,
            timing.pixel_clock_mhz
        );
        let ae = iq::ae_session::Session::from_profile(&profile, timing, 2304, 1296)
            .map_err(|_| "ae-session")?;
        let current_record = {
            let codes = iq::exposure::Codes {
                integration_time: super::camera::initial_control_lines(),
                gain: 128,
            };
            let decoded = iq::exposure::decode_linear(codes, -1, sensor.conversion(timing))
                .map_err(|_| "exposure-decode")?;
            iq::ae_publication::pack(
                iq::ae_route::Point {
                    time: decoded.seconds,
                    gain: decoded.gain,
                    isp_gain: 1.,
                },
                codes,
                -1,
                iq::ae_publication::Timing {
                    frame_length: super::camera::CONTROL_FRAME_LINES,
                    line_length: hts as u16,
                    pixel_clock_mhz: timing.pixel_clock_mhz,
                },
            )
        };
        let wb = profile
            .pointer("/main_scene/0/sub_scene/0/scene_isp32/wb_v32")
            .ok_or("awb-profile-path")?;
        let awb = iq::awb_session::Session::new(wb, [2304, 1296], 1).map_err(|_| "awb-session")?;

        Ok(Self {
            ae,
            awb,
            current_record,
            next_record: current_record,
            parameters: *PARAMETERS,
            active_parameters: *PARAMETERS,
            next_parameters: *PARAMETERS,
            cache: [0; iq::isp32::AWB_GAIN_BYTES],
            measured_sdk: *AWB,
            active_sdk: *AWB,
            next_sdk: *AWB,
            address: stats_address,
            index: 0,
        })
    }
    pub fn consume(&mut self) -> Result<(), &'static str> {
        let index = self.index;
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_HEAP frame={} bytes={}\r",
            index,
            super::heap::used()
        );
        let bytes = unsafe {
            core::slice::from_raw_parts(self.address as *const u8, iq::statistics::BUFFER_BYTES)
        };
        let stats = iq::statistics::Statistics::parse(bytes).map_err(|_| "statistics")?;
        if stats.frame_id() != index || stats.parameters_id() != index.saturating_sub(1) {
            return Err("feedback-statistics-association");
        }
        let measurement = iq::ae_translation::measure_linear(bytes, &self.parameters)
            .map_err(|_| "ae-translation")?
            .ok_or("ae-no-measurement")?;
        let output = self
            .ae
            .step(
                index as i32,
                [measurement.mean, 0, 0, 0],
                &measurement.histogram,
                self.current_record,
            )
            .map_err(|_| "ae-step")?;
        let proposed = output.publication.final_record;
        let controls = iq::sensor_submission::linear_controls(&proposed);
        let _ = writeln!(super::cpu::Console,"@@ISP_3A_AE frame={} mean_q8={} proposed_lines={} proposed_gain={} normalized_brightness={}\r",index,measurement.mean,controls.coarse_integration_time,controls.analogue_gain_code,self.ae.preprocessing.normalized_brightness);
        let mut frame = [0; iq::awb_preparation::FRAME_BYTES];
        let mut destination = iq::awb_translation::Destination {
            frame: &mut frame,
            valid: false,
            frame_info_valid: false,
            frame_id: 0,
            proxy_sequence: 0,
        };
        // The measurement snapshot below belongs to this completed frame,
        // separately from the configuration just applied by its frame-end IRQ.
        let outcome = iq::awb_translation::translate_associated(
            &stats,
            &[iq::awb_translation::Snapshot {
                id: index.saturating_sub(1),
                measurement: &self.measured_sdk,
            }],
            &mut destination,
        )
        .map_err(|_| "awb-translation")?;
        if outcome != iq::awb_translation::Outcome::Translated {
            return Err("awb-no-measurement");
        }
        let gain = f32::from_le_bytes(self.current_record[4..8].try_into().unwrap());
        let result = self
            .awb
            .process(
                &frame,
                &iq::awb_session::Input {
                    requested_update: index == 0,
                    exposure_luma: Some([self.ae.preprocessing.normalized_brightness, 0.]),
                    iso: 50. * gain,
                    site_reference: None,
                },
            )
            .map_err(|_| "awb-step")?;
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_3A_AWB frame={} complete={} gain={:?} controller_frame={}\r",
            index,
            result.complete,
            result.current_gain,
            result.controller_frame
        );
        if controls.frame_length_lines != super::camera::CONTROL_FRAME_LINES
            || f32::from_le_bytes(proposed[12..16].try_into().unwrap()) != 1.
        {
            return Err("feedback-vts-or-isp-gain-not-implemented");
        }
        self.next_parameters = self.active_parameters;
        let [red, green_red, green_blue, blue] = result.current_gain;
        iq::isp32::apply_awb_gain(
            &mut self.next_parameters,
            &mut self.cache,
            iq::isp32::WhiteBalanceGain {
                red,
                green_red,
                green_blue,
                blue,
                position: iq::isp32::ApplyPosition::Gain1,
            },
            true,
        )
        .map_err(|_| "gain-serialization")?;
        self.next_sdk = self.active_sdk;
        if result.action.reconfigure && index != 0 {
            let mut signature = [0; 64];
            let name = b"BM-AWB-NORMAL-v1";
            signature[..name.len()].copy_from_slice(name);
            self.awb
                .next_measurement(&mut self.next_sdk, &signature)
                .map_err(|_| "awb-next-measurement")?;
            iq::isp_awb_measurement::Measurement(self.next_sdk)
                .apply(&mut self.next_parameters, true);
        }

        self.next_record = proposed;
        Ok(())
    }
    pub fn publish_controls(&self) {
        #[cfg(feature = "runtime-board")]
        {
            let actual = iq::sensor_submission::linear_controls(&self.current_record);
            super::runtime::camera_completed(
                actual.coarse_integration_time,
                actual.analogue_gain_code,
            );
        }
    }
    pub fn advance(&mut self, streaming: bool) -> Result<(), &'static str> {
        let controls = iq::sensor_submission::linear_controls(&self.next_record);
        super::isp::stage_gains(&self.active_parameters, &self.next_parameters)?;
        let raw = if streaming {
            super::camera::next_stream_raw(
                controls.coarse_integration_time,
                controls.analogue_gain_code,
            )?
        } else {
            super::camera::next_raw(
                controls.coarse_integration_time,
                controls.analogue_gain_code,
            )?
        };
        self.address = super::isp::next_frame(raw, self.index + 1, self.index)?;
        self.measured_sdk = self.active_sdk;
        self.active_sdk = self.next_sdk;
        self.parameters = self.active_parameters;
        self.active_parameters = self.next_parameters;
        self.current_record = self.next_record;
        self.index += 1;
        Ok(())
    }
}
fn run(stats_address: usize, frame_us: u64) -> Result<(), &'static str> {
    let mut state = Feedback::new(stats_address, frame_us)?;
    for index in 0..32 {
        state.consume()?;
        if index == 31 {
            state.publish_controls();
            break;
        }
        state.advance(false)?;
    }
    Ok(())
}
pub fn diagnose(stats_address: usize, frame_us: u64) {
    #[cfg(feature = "runtime-board")]
    if super::camera_preview::active() {
        super::camera_preview::prepare(stats_address, frame_us);
        return;
    }
    match run(stats_address, frame_us) {
        Ok(()) => super::put(
            b"@@ISP_3A_FEEDBACK_DIAGNOSTIC 32-frames; normal-timeshare; not-full-gate\r\n",
        ),
        Err(error) => {
            let _ = writeln!(super::cpu::Console, "@@FAIL isp-3a-diagnostic {}\r", error);
        }
    }
}

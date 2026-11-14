// SPDX-License-Identifier: MIT
//! Exercise the existing calibrated sessions against real DUT ISP statistics.
//! Bounded feedback diagnostic; normal AWB time-share measurements; full Phase8 gate still separate.
use core::fmt::Write;
use shieldsigner_rkaiq as iq;
const PROFILE: &[u8] = include_bytes!("../.tools/sc3336-iq.json");
const PARAMETERS: &[u8; iq::isp32::PARAMETER_BYTES] =
    include_bytes!("../.tools/isp-initial-parameters.bin");
const AWB: &[u8; 1204] = include_bytes!("../.tools/isp-awb-sdk.bin");

fn run(stats_address: usize, frame_us: u64) -> Result<(), &'static str> {
    let profile: serde_json::Value = serde_json::from_slice(PROFILE).map_err(|_| "profile-json")?;
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
        pixel_clock_mhz: (hts as f32 * super::camera::CONTROL_FRAME_LINES as f32) / frame_us as f32,
        line_length_pixels: hts,
    };
    let _ = writeln!(
        super::cpu::Console,
        "@@ISP_3A_TIMING hts={} vts=1360 measured_frame_us={} effective_pixel_mhz={}\r",
        hts,
        frame_us,
        timing.pixel_clock_mhz
    );
    let mut ae = iq::ae_session::Session::from_profile(&profile, timing, 2304, 1296)
        .map_err(|_| "ae-session")?;
    let mut current_record = {
        let codes = iq::exposure::Codes {
            integration_time: super::camera::CONTROL_INITIAL_LINES,
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
    let mut awb = iq::awb_session::Session::new(wb, [2304, 1296], 1).map_err(|_| "awb-session")?;
    let mut parameters = *PARAMETERS;
    let mut active_parameters = *PARAMETERS;
    let mut cache = [0; iq::isp32::AWB_GAIN_BYTES];
    let mut measured_sdk = *AWB;
    let mut active_sdk = *AWB;
    let mut address = stats_address;
    for index in 0..32u32 {
        let _=writeln!(super::cpu::Console,"@@ISP_HEAP frame={} bytes={}\r",index,super::heap::used());
        let bytes = unsafe {
            core::slice::from_raw_parts(address as *const u8, iq::statistics::BUFFER_BYTES)
        };
        let stats = iq::statistics::Statistics::parse(bytes).map_err(|_| "statistics")?;
        if stats.frame_id() != index || stats.parameters_id() != index.saturating_sub(1) {
            return Err("feedback-statistics-association");
        }
        let measurement = iq::ae_translation::measure_linear(bytes, &parameters)
            .map_err(|_| "ae-translation")?
            .ok_or("ae-no-measurement")?;
        let output = ae
            .step(
                index as i32,
                [measurement.mean, 0, 0, 0],
                &measurement.histogram,
                current_record,
            )
            .map_err(|_| "ae-step")?;
        let proposed = output.publication.final_record;
        let controls = iq::sensor_submission::linear_controls(&proposed);
        let _ = writeln!(super::cpu::Console,"@@ISP_3A_AE frame={} mean_q8={} proposed_lines={} proposed_gain={} normalized_brightness={}\r",index,measurement.mean,controls.coarse_integration_time,controls.analogue_gain_code,ae.preprocessing.normalized_brightness);
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
                measurement: &measured_sdk,
            }],
            &mut destination,
        )
        .map_err(|_| "awb-translation")?;
        if outcome != iq::awb_translation::Outcome::Translated {
            return Err("awb-no-measurement");
        }
        let gain = f32::from_le_bytes(current_record[4..8].try_into().unwrap());
        let result = awb
            .process(
                &frame,
                &iq::awb_session::Input {
                    requested_update: index == 0,
                    exposure_luma: Some([ae.preprocessing.normalized_brightness, 0.]),
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
        if index == 31 {
            break;
        }
        if controls.frame_length_lines != super::camera::CONTROL_FRAME_LINES
            || f32::from_le_bytes(proposed[12..16].try_into().unwrap()) != 1.
        {
            return Err("feedback-vts-or-isp-gain-not-implemented");
        }
        let mut next_parameters = active_parameters;
        let [red, green_red, green_blue, blue] = result.current_gain;
        iq::isp32::apply_awb_gain(
            &mut next_parameters,
            &mut cache,
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
        let mut next_sdk = active_sdk;
        if result.action.reconfigure && index != 0 {
            let mut signature = [0; 64];
            let name = b"BM-AWB-NORMAL-v1";
            signature[..name.len()].copy_from_slice(name);
            awb.next_measurement(&mut next_sdk, &signature)
                .map_err(|_| "awb-next-measurement")?;
            iq::isp_awb_measurement::Measurement(next_sdk).apply(&mut next_parameters, true);
        }
        super::isp::stage_gains(&active_parameters, &next_parameters)?;
        let raw = super::camera::next_raw(
            controls.coarse_integration_time,
            controls.analogue_gain_code,
        )?;
        address = super::isp::next_frame(raw, index + 1, index)?;
        // This frame used the previous active parameters; its frame-end IRQ
        // applied the queued gains for the subsequent frame.
        measured_sdk = active_sdk;
        active_sdk = next_sdk;
        parameters = active_parameters;
        active_parameters = next_parameters;
        current_record = proposed;
    }
    Ok(())
}
pub fn diagnose(stats_address: usize, frame_us: u64) {
    match run(stats_address, frame_us) {
        Ok(()) => super::put(
            b"@@ISP_3A_FEEDBACK_DIAGNOSTIC 32-frames; normal-timeshare; not-full-gate\r\n",
        ),
        Err(error) => {
            let _ = writeln!(super::cpu::Console, "@@FAIL isp-3a-diagnostic {}\r", error);
        }
    }
}

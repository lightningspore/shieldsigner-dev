// Continuous application owner; SIGINT/SIGTERM finish the current image and unwind all queues.
fn stream_sc3336(args: &[String]) -> io::Result<()> {
    if args.len() != 7 { return Err(error("stream-sc3336 PLAN IQ PARAM IMAGE OUT STATS SOCKET")); }
    // Take ownership before graph/sensor reconfiguration, not merely at STREAMON.
    // Keep the inode: unlinking a held flock would let a new opener bypass it.
    let ownership = OpenOptions::new().read(true).write(true).create(true)
        .mode(0o600).custom_flags(libc::O_NOFOLLOW).open("/tmp/shieldsigner-camera-owner.lock")?;
    if unsafe { libc::flock(ownership.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
        return Err(error("Another Rust camera owner is already running"));
    }
    let _signals = CameraStreamSignals::install()?;
    // A managed application session must not orphan a camera owner if Python dies.
    if let Some(expected) = std::env::var_os("SHIELDSIGNER_CAMERA_PARENT_PID") {
        let expected = expected.to_str().and_then(|v| v.parse::<u32>().ok())
            .filter(|v| *v > 1).ok_or_else(|| error("Invalid managed camera parent PID"))?;
        if unsafe { libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGTERM) } != 0 {
            return Err(io::Error::last_os_error());
        }
        if unsafe { libc::getppid() } as u32 != expected {
            return Err(error("Managed camera parent exited before startup"));
        }
    }
    if let Some(fd) = std::env::var_os("SHIELDSIGNER_CAMERA_READY_FD") {
        use std::os::fd::FromRawFd;
        let fd = fd.to_str().and_then(|v| v.parse::<i32>().ok()).filter(|fd| *fd >= 3)
            .ok_or_else(|| error("Invalid managed camera readiness descriptor"))?;
        // Acknowledge only after signal handling and parent-death cleanup are armed.
        let mut ready = unsafe { File::from_raw_fd(fd) };
        ready.write_all(b"1")?;
    }
    std::env::set_var("SHIELDSIGNER_CAMERA_SOCKET", &args[6]);
    auto_awb_frame_sc3336(&args[..6])
}
// Included in camera-probe's Linux module. Fixed initial checkpoint, not 3A.
fn first_frame_sc3336(args: &[String]) -> io::Result<()> {
    first_frame_sc3336_observed(args, None)
}
fn first_frame_sc3336_observed(
    args: &[String],
    observer: Option<CameraAeSender>,
) -> io::Result<()> {
    first_frame_sc3336_mode(args, observer, false, None)
}
fn auto_frame_sc3336(args: &[String]) -> io::Result<()> {
    first_frame_sc3336_mode(args, None, true, None)
}
fn auto_awb_frame_sc3336(args: &[String]) -> io::Result<()> {
    if !matches!(args.len(), 6 | 8) {
        return Err(error("auto-awb-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE [--frames 33..3600]"));
    }
    let frames = if args.len() == 8 {
        if args[6] != "--frames" {
            return Err(error("Expected --frames"));
        }
        let n = args[7]
            .parse::<u32>()
            .map_err(|_| error("Invalid frame count"))?;
        if !(33..=3600).contains(&n) {
            return Err(error("Live diagnostic requires 33..3600 image frames"));
        }
        Some(n)
    } else {
        None
    };
    first_frame_sc3336_with_gain(
        &args[..6],
        None,
        true,
        Some(shieldsigner_rkaiq::awb_session::SINGLE_CAMERA_SAMPLE_SCALE),
        None,
        true,
        frames,
    )
}
fn awb_measurement_frame_sc3336(args: &[String]) -> io::Result<()> {
    if args.len() != 7 {
        return Err(error("awb-measurement-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SAMPLE_SCALE"));
    }
    let scale = args[6]
        .parse::<u32>()
        .map_err(|_| error("Invalid sample scale"))?;
    if scale == 0 {
        return Err(error("Sample scale must be positive"));
    }
    first_frame_sc3336_mode(&args[..6], None, false, Some(scale))
}
fn awb_gain_frame_sc3336(args: &[String]) -> io::Result<()> {
    if args.len() != 11 {
        return Err(error("awb-gain-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SAMPLE_SCALE R GR GB B"));
    }
    let scale = args[6]
        .parse::<u32>()
        .map_err(|_| error("Invalid sample scale"))?;
    if scale == 0 {
        return Err(error("Sample scale must be positive"));
    }
    let mut gain = [0.; 4];
    for (out, value) in gain.iter_mut().zip(&args[7..]) {
        *out = value.parse::<f32>().map_err(|_| error("Invalid gain"))?;
        if !out.is_finite() || *out <= 0. || *out > 2047. / 256. {
            return Err(error("Gain outside ISP Q8 range"));
        }
    }
    first_frame_sc3336_with_gain(
        &args[..6],
        None,
        false,
        Some(scale),
        Some(gain),
        false,
        None,
    )
}
fn first_frame_sc3336_mode(
    args: &[String],
    observer: Option<CameraAeSender>,
    automatic: bool,
    awb_sample_scale: Option<u32>,
) -> io::Result<()> {
    first_frame_sc3336_with_gain(
        args,
        observer,
        automatic,
        awb_sample_scale,
        None,
        false,
        None,
    )
}
fn first_frame_sc3336_with_gain(
    args: &[String],
    observer: Option<CameraAeSender>,
    automatic: bool,
    awb_sample_scale: Option<u32>,
    gain_override: Option<[f32; 4]>,
    live_awb: bool,
    image_frames: Option<u32>,
) -> io::Result<()> {
    use shieldsigner_rkaiq::{
        calibration::{RuntimeTiming, SensorCalibration},
        sensor, sensor_descriptor,
    };
    use std::io::Read;
    if (automatic && args.len() != 6) || (!automatic && !matches!(args.len(), 5 | 6 | 10)) {
        return Err(error(if automatic {
            "auto-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE"
        } else {
            "first-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT [STATS_NODE [--step-at FRAME (--step-seconds SECONDS | --step-gain GAIN)]]"
        }));
    }
    let step = if args.len() == 10 {
        if args[6] != "--step-at" || !matches!(args[8].as_str(), "--step-seconds" | "--step-gain") {
            return Err(error("Expected --step-at FRAME followed by --step-seconds SECONDS or --step-gain GAIN"));
        }
        let frame = args[7]
            .parse::<u32>()
            .map_err(|_| error("Invalid step frame"))?;
        let seconds = args[9]
            .parse::<f32>()
            .map_err(|_| error("Invalid step seconds"))?;
        if frame > 64 || !seconds.is_finite() || seconds <= 0. {
            return Err(error("Invalid exposure-step request"));
        }
        Some((frame, seconds, args[8] == "--step-gain"))
    } else {
        None
    };
    let read = |path: &str, limit: u64| -> io::Result<Vec<u8>> {
        let mut bytes = Vec::new();
        File::open(path)?.take(limit + 1).read_to_end(&mut bytes)?;
        if bytes.len() as u64 > limit {
            return Err(error("Startup input exceeds bound"));
        }
        Ok(bytes)
    };
    let plan: Value =
        serde_json::from_slice(&read(&args[0], 65536)?).map_err(|e| error(e.to_string()))?;
    let (sensor_path, isp, tx, rx, sof) = pipeline_configuration::linear_cif_nodes(&plan)?;
    let iq: Value = serde_json::from_slice(&read(&args[1], 8 * 1024 * 1024)?)
        .map_err(|e| error(e.to_string()))?;
    let profile = SensorCalibration::from_value(&iq).map_err(error)?;
    if profile.width != 2304 || profile.height != 1296 || profile.linear_dcg_supported {
        return Err(error(
            "This first-frame command supports the SC3336 2304x1296 profile with DCG disabled",
        ));
    }
    let statistics = args.get(5);
    if let Some(node) = statistics {
        use std::os::unix::fs::{FileTypeExt, MetadataExt};
        let info = fs::metadata(node)?;
        if !info.file_type().is_char_device() {
            return Err(error("Statistics endpoint must be a character device"));
        }
        for path in [&sensor_path, &isp, &tx, &rx, &args[2], &args[3]] {
            if fs::metadata(path)?.rdev() == info.rdev() {
                return Err(error(
                    "Statistics endpoint must be distinct from other camera nodes",
                ));
            }
        }
        for path in [
            format!("{}.stats.raw", args[4]),
            format!("{}.stats.raw.json", args[4]),
        ] {
            if std::path::Path::new(&path).exists() {
                return Err(error("Statistics output already exists"));
            }
        }
    }
    let (mut parameters, mut initial, sdk) = if let Some(scale) = awb_sample_scale {
        if (automatic && !live_awb) || statistics.is_none() || step.is_some() {
            return Err(error(
                "AWB measurement capture requires fixed startup and a statistics node",
            ));
        }
        let (parameters, initial, sdk) =
            shieldsigner_rkaiq::initial_parameters::assemble_with_awb(&iq, scale).map_err(error)?;
        (parameters, initial, Some(sdk))
    } else {
        let (parameters, initial) = if statistics.is_some() {
            shieldsigner_rkaiq::initial_parameters::assemble_with_ae(&iq).map_err(error)?
        } else {
            shieldsigner_rkaiq::initial_parameters::assemble(&iq).map_err(error)?
        };
        (parameters, initial, None)
    };
    if let Some(g) = gain_override {
        use shieldsigner_rkaiq::isp32::{apply_awb_gain, awb_prepare_position, WhiteBalanceGain};
        apply_awb_gain(
            &mut parameters,
            &mut [0; 32],
            WhiteBalanceGain {
                red: g[0],
                green_red: g[1],
                green_blue: g[2],
                blue: g[3],
                position: awb_prepare_position(0),
            },
            true,
        )
        .map_err(|e| error(format!("WB gain override: {e:?}")))?;
        initial["diagnosticWhiteBalanceOverride"] = json!(g);
        initial["automaticWhiteBalance"] = json!(false);
    }
    if std::env::var_os("SHIELDSIGNER_CAMERA_SOCKET").is_some() && !camera_bt601_parameters(&parameters) {
        return Err(error("RGB streaming requires the supported BT.601 CSM and unscaled CGC profile"));
    }
    let sdk_path = format!("{}.awb-sdk.bin", args[4]);
    if sdk.is_some() && std::path::Path::new(&sdk_path).exists() {
        return Err(error("AWB SDK output already exists"));
    }
    let parameter_path = format!("{}.initial.bin", args[4]);
    let report_path = format!("{}.initial.json", args[4]);
    for path in [
        &args[4],
        &format!("{}.json", args[4]),
        &parameter_path,
        &report_path,
    ] {
        if std::path::Path::new(path).exists() {
            return Err(error(
                "Startup output already exists; choose a new output basename",
            ));
        }
    }
    if sdk.is_some() {
        for suffix in [
            ".awb-translated.bin",
            ".awb-translated.json",
            ".awb-effective-sdk.bin",
        ] {
            if std::path::Path::new(&format!("{}{suffix}", args[4])).exists() {
                return Err(error("AWB translation output already exists"));
            }
        }
    }
    // Read-only graph preflight before any settings or sensor controls change.
    pipeline_configuration::run(&[args[0].clone(), "--dry-run".into()])?;
    let mut params = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&parameter_path)?;
    params.write_all(&parameters)?;
    params.sync_all()?;
    if let Some(sdk) = sdk {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&sdk_path)?;
        file.write_all(&sdk)?;
        file.sync_all()?;
    }
    let mut report = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&report_path)?;
    serde_json::to_writer_pretty(&mut report, &initial).map_err(|e| error(e.to_string()))?;
    report.sync_all()?;
    println!(
        "{}",
        json!({"event":"first-frame-starting","sensor":sensor_path,"parameters":parameter_path,"initialReport":report_path,"automatic3A":false,"automaticExposure":automatic,"awbMeasurementsConfigured":awb_sample_scale.is_some(),"automaticWhiteBalance":live_awb,"coldStartProven":false})
    );
    let outcome = (|| -> io::Result<()> {
        pipeline_configuration::run(&[args[0].clone()])?;
        let mut device = SensorDevice {
            file: open(&sensor_path, true)?,
            queries: vec![],
            bus: None,
            writes: vec![],
        };
        let descriptor = sensor_descriptor::read(&mut device)?;
        if descriptor.width() != profile.width || descriptor.height() != profile.height {
            return Err(error("Active sensor resolution differs from calibration"));
        }
        let timing = RuntimeTiming {
            frame_length: descriptor.line_periods_per_field() as u32,
            pixel_clock_mhz: descriptor.pixel_clock_mhz(),
            line_length_pixels: descriptor.pixel_periods_per_line() as u32,
        };
        let seconds = initial["requestedExposureSeconds"]
            .as_f64()
            .ok_or_else(|| error("Missing initial exposure"))? as f32;
        let gain = initial["requestedGain"]
            .as_f64()
            .ok_or_else(|| error("Missing initial gain"))? as f32;
        let codes = profile.linear_codes(seconds, gain, timing).map_err(error)?;
        // SC3336 handles combined analogue/digital gain through ANALOGUE_GAIN;
        // its nonexistent generic digital-gain control must be skipped (code 0).
        for (id, value) in [
            (sensor::ANALOGUE_GAIN, codes.gain),
            (sensor::EXPOSURE, codes.integration_time),
        ] {
            let mut range = [0u8; 68];
            put32(&mut range, 0, id);
            ioctl(device.file.as_raw_fd(), 0xc0445624, &mut range)?;
            let min = get32(&range, 40) as i32;
            let max = get32(&range, 44) as i32;
            let step = get32(&range, 48) as i32;
            if value > i32::MAX as u32
                || (value as i32) < min
                || (value as i32) > max
                || step <= 0
                || (value as i64 - min as i64) % step as i64 != 0
                || get32(&range, 56) & 1 != 0
            {
                return Err(error(
                    "Initial exposure/gain code is outside active driver control range",
                ));
            }
        }
        println!(
            "{}",
            json!({"event":"initial-exposure-derived","seconds":seconds,"gain":gain,"frameLines":timing.frame_length,"gainCode":codes.gain,"integrationCode":codes.integration_time,"digitalCode":0,"dcgMode":-1})
        );
        drop(device);
        apply_linear(&[
            sensor_path.clone(),
            timing.frame_length.to_string(),
            codes.gain.to_string(),
            "0".into(),
            codes.integration_time.to_string(),
            "-1".into(),
        ])?;
        let control = if automatic {
            let session = shieldsigner_rkaiq::ae_session::Session::from_profile(
                &iq,
                timing,
                profile.width,
                profile.height,
            )
            .map_err(error)?;
            let initial_record = session.state.publication.previous_final;
            let runtime = shieldsigner_rkaiq::ae_runtime::Runtime::new(
                session,
                initial_record,
                shieldsigner_rkaiq::sensor_scheduler::EffectPolicy {
                    shorten_enabled: false,
                    designated_frame: 0,
                    shorten_all: false,
                },
            )
            .map_err(error)?;
            let sensor = SensorDevice {
                file: open(&sensor_path, true)?,
                queries: vec![],
                bus: None,
                writes: vec![],
            };
            let (sender, events) = std::sync::mpsc::sync_channel(64);
            let mut owner = CameraAeOwner::new(runtime, sensor, 0, parameters);
            owner.demosaic = Some((
                shieldsigner_rkaiq::demosaic_selection::Calibration::from_value(
                    &iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["debayer_v2"]["param"]
                ).map_err(error)?,
                shieldsigner_rkaiq::demosaic_runtime::State {
                    iso: initial["iso"].as_i64().ok_or_else(|| error("Missing startup ISO"))? as i32,
                    reconfigure: true,
                    hardware: [0; shieldsigner_rkaiq::isp_demosaic::HARDWARE_BYTES],
                },
            ));
            owner.dpcc = Some(CameraDpcc {
                calibration: shieldsigner_rkaiq::dpcc_calibration::Automatic::from_value(
                    &iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["adpcc_calib"]["DpccTuningPara"]
                ).map_err(error)?,
                state: shieldsigner_rkaiq::dpcc_runtime::State::default(),
                result: [0; shieldsigner_rkaiq::isp_dpcc::RESULT_BYTES],
            });
            if live_awb {
                owner.awb = Some(CameraAwb {
                    session: shieldsigner_rkaiq::awb_session::Session::new(
                        &iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["wb_v32"],
                        [profile.width, profile.height],
                        awb_sample_scale.unwrap(),
                    )
                    .map_err(error)?,
                    sdk: sdk.ok_or_else(|| error("Live AWB requires an SDK snapshot"))?,
                    last_iso: None,
                    sample_directory: std::env::var_os("SHIELDSIGNER_AWB_SAMPLE_DIR").map(std::path::PathBuf::from),
                    sampled_groups: 0,
                    gains: vec![],
                    measurements: vec![(0, sdk.unwrap())],
                    processed: 0,
                    last: None,
                });
            }
            Some(AutomaticCapture {
                owner,
                events,
                sender,
                statistics_node: statistics.unwrap().clone(),
                statistics_output: format!("{}.stats.raw", args[4]),
                initial_parameters: parameters,
                target: initial["initialTargetLuma"]
                    .as_f64()
                    .ok_or_else(|| error("Missing AE target"))? as f32,
            })
        } else {
            None
        };
        let capture_observer = control
            .as_ref()
            .map(|c| c.sender.clone())
            .or_else(|| observer.clone());
        let step_codes = step
            .map(|(frame, value, gain_step)| {
                profile
                    .linear_codes(if gain_step { seconds } else { value }, if gain_step { value } else { gain }, timing)
                    .map(|c| (frame, if gain_step { c.gain } else { c.integration_time }, gain_step))
            })
            .transpose()
            .map_err(error)?;
        let capture = || {
            let mut command = vec![args[2].clone(), parameter_path.clone(), tx, rx, isp];
            if let Some(node) = sof {
                command.extend(["--sof-node".into(), node]);
            }
            if let Some((frame, code, gain_step)) = step_codes {
                command.extend([
                    if gain_step { "--gain-step" } else { "--exposure-step" }.into(),
                    sensor_path.clone(),
                    frame.to_string(),
                    code.to_string(),
                ]);
            }
            command.extend([
                "--".into(),
                args[3].clone(),
                args[4].clone(),
                "--fourcc".into(),
                "NV12".into(),
                "--timeout-ms".into(),
                "10000".into(),
            ]);
            if CAMERA_CONTINUOUS.load(std::sync::atomic::Ordering::Relaxed) {
                // A fresh ISP defaults to native 2304x1296. The app expects VGA,
                // and native-sized image buffers exhaust this board's 12 MiB CMA.
                command.extend(["--width".into(), "640".into(), "--height".into(), "480".into()]);
            }
            if let Some((frame, _, _)) = step_codes {
                command.extend(["--warmup".into(), (frame + 8).to_string()]);
            }
            if automatic {
                command.extend([
                    "--warmup".into(),
                    (image_frames.unwrap_or(33) - 1).to_string(),
                ]);
            } else if awb_sample_scale.is_some() {
                command.extend(["--warmup".into(), "8".into()]);
            }
            capture_cif_with_parameters_controlled(&command, capture_observer, control)
        };
        if automatic {
            return capture();
        }
        match statistics {
            Some(node) => statistics_session::during_observed(
                node,
                &format!("{}.stats.raw", args[4]),
                &parameters,
                initial["initialTargetLuma"]
                    .as_f64()
                    .ok_or_else(|| error("Missing calibrated initial AE target"))?
                    as f32,
                observer.clone(),
                capture,
            ),
            None => capture(),
        }
    })();
    let outcome = outcome.and_then(|()| {
        if let Some(sdk) = sdk.filter(|_| !live_awb) {
            save_awb_capture_translation(
                &format!("{}.stats.raw", args[4]),
                &sdk,
                u32::from_le_bytes(parameters[24..28].try_into().unwrap()),
                &format!("{}.awb-translated", args[4]),
            )?;
        }
        Ok(())
    });
    println!(
        "{}",
        json!({"event":"first-frame-finished","success":outcome.is_ok(),"cancelled":camera_stream_cancelled(),"error":outcome.as_ref().err().map(|e|e.to_string()),"automatic3A":false,"automaticExposure":automatic,"awbMeasurementsConfigured":awb_sample_scale.is_some(),"automaticWhiteBalance":live_awb,"coldStartProven":false,"partialSettingsMayRemain":true})
    );
    outcome
}

/// Translate only against the actual single initial parameter snapshot. Never
/// substitute the image sequence or a guessed/latest configuration ID.
fn save_awb_capture_translation(
    raw_path: &str,
    sdk: &[u8; 1204],
    parameter_id: u32,
    output: &str,
) -> io::Result<()> {
    use shieldsigner_rkaiq::{
        awb_preparation::FRAME_BYTES, awb_translation::*, statistics::Statistics,
    };
    use std::io::Read;
    let mut raw = Vec::new();
    File::open(raw_path)?.take(13041).read_to_end(&mut raw)?;
    let stats = Statistics::parse(&raw).map_err(|_| error("Unsupported AWB statistics size"))?;
    let mut frame = [0; FRAME_BYTES];
    let mut destination = Destination {
        frame: &mut frame,
        valid: false,
        frame_info_valid: false,
        frame_id: 0,
        proxy_sequence: 0,
    };
    let outcome = translate_associated(
        &stats,
        &[Snapshot {
            id: parameter_id,
            measurement: sdk,
        }],
        &mut destination,
    )
    .map_err(|e| error(format!("AWB configuration association: {e:?}")))?;
    if outcome != Outcome::Translated {
        return Err(error("Capture returned no valid AWB measurement"));
    }
    let frame_id = destination.frame_id;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(format!("{output}.bin"))?;
    file.write_all(&frame)?;
    file.sync_all()?;
    let groups=(0..sdk[0x48] as usize).map(|i|{
        let regions=(0..2).map(|r|{
            let at=i*48+r*24;let values:[i64;3]=core::array::from_fn(|j|i64::from_le_bytes(frame[at+j*8..at+j*8+8].try_into().unwrap()));
            let gain=if values[0]==0 {None}else{shieldsigner_rkaiq::awb_gain::statistics_gain(values[0],values[1],values[2]).ok()};
            json!({"region":r,"weightedCount":values[0],"normalizedCount":gain.map(|(_,n)|n),"normalizedGain":gain.map(|(g,_)|g)})
        }).collect::<Vec<_>>();json!({"physicalLight":i,"regions":regions})
    }).collect::<Vec<_>>();
    let report = json!({"event":"awb-statistics-translated","frameId":frame_id,"parametersId":stats.parameters_id(),"configurationId":parameter_id,"association":"exact-single-initial-snapshot","bytes":FRAME_BYTES,"physicalLights":sdk[0x48],"groups":groups,"automaticWhiteBalance":false,"limitations":["Translation and per-region diagnostic gains only; persistent AWB feedback/publication are not enabled.","Statistics frame is distinct from the saved image sequence; physical frame timing and cold startup remain unproven."]});
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(format!("{output}.json"))?;
    serde_json::to_writer_pretty(&mut file, &report).map_err(|e| error(e.to_string()))?;
    file.sync_all()?;
    println!("{report}");
    Ok(())
}

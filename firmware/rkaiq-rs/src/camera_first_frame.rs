// Included in camera-probe's Linux module. Fixed initial checkpoint, not 3A.
fn first_frame_sc3336(args: &[String]) -> io::Result<()> {
    use shieldsigner_rkaiq::{
        calibration::{RuntimeTiming, SensorCalibration},
        sensor, sensor_descriptor,
    };
    use std::io::Read;
    if !matches!(args.len(), 5 | 6) {
        return Err(error(
            "first-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT [STATS_NODE]",
        ));
    }
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
    let (sensor_path, isp, tx, rx) = pipeline_configuration::linear_cif_nodes(&plan)?;
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
    let (parameters, initial) = if statistics.is_some() {
        shieldsigner_rkaiq::initial_parameters::assemble_with_ae(&iq).map_err(error)?
    } else {
        shieldsigner_rkaiq::initial_parameters::assemble(&iq).map_err(error)?
    };
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
    // Read-only graph preflight before any settings or sensor controls change.
    pipeline_configuration::run(&[args[0].clone(), "--dry-run".into()])?;
    let mut params = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&parameter_path)?;
    params.write_all(&parameters)?;
    params.sync_all()?;
    let mut report = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&report_path)?;
    serde_json::to_writer_pretty(&mut report, &initial).map_err(|e| error(e.to_string()))?;
    report.sync_all()?;
    println!(
        "{}",
        json!({"event":"first-frame-starting","sensor":sensor_path,"parameters":parameter_path,"initialReport":report_path,"automatic3A":false,"coldStartProven":false})
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
        let capture = || {
            capture_cif_with_parameters(&[
                args[2].clone(),
                parameter_path.clone(),
                tx,
                rx,
                isp,
                "--".into(),
                args[3].clone(),
                args[4].clone(),
                "--fourcc".into(),
                "NV12".into(),
                "--timeout-ms".into(),
                "10000".into(),
            ])
        };
        match statistics {
            Some(node) => {
                statistics_session::during(node, &format!("{}.stats.raw", args[4]), capture)
            }
            None => capture(),
        }
    })();
    println!(
        "{}",
        json!({"event":"first-frame-finished","success":outcome.is_ok(),"error":outcome.as_ref().err().map(|e|e.to_string()),"automatic3A":false,"coldStartProven":false,"partialSettingsMayRemain":true})
    );
    outcome
}

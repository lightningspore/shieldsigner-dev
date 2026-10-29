//! Experimental standalone V4L2 diagnostic. No RKAIQ symbols or vendor library.
//! This does not yet configure the full media graph or replace the ISP engine.
use std::env;
#[cfg(any(target_os = "linux", test))]
#[path = "../camera_awb_trace.rs"]
mod camera_awb_trace;
#[cfg(any(target_os = "linux", test))]
#[path = "../camera_runtime_log.rs"]
mod camera_runtime_log;
#[cfg(any(target_os = "linux", test))]
#[path = "../camera_event_metrics.rs"]
mod camera_event_metrics;
#[cfg(any(target_os = "linux", test))]
#[path = "../camera_code_lock.rs"]
mod camera_code_lock;
#[cfg(target_os="linux")]
macro_rules! camera_observed_println {
    ($($arg:tt)*) => {{
        crate::camera_runtime_log::emit(
            CAMERA_CONTINUOUS.load(std::sync::atomic::Ordering::Relaxed),
            crate::camera_runtime_log::full_enabled(), || {
                let _log_phase = crate::camera_event_metrics::Phase::start("logging", None);
                println!($($arg)*);
            });
    }};
}

const HELP:&str=concat!("camera-probe ", env!("CARGO_PKG_VERSION"), " — experimental Rust camera diagnostic\n\nCommands:\n  camera-probe stream-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SOCKET\n  camera-probe auto-awb-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE [--frames 33..3600]\n  camera-probe awb-gain-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SAMPLE_SCALE R GR GB B\n  camera-probe awb-measurement-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SAMPLE_SCALE\n  camera-probe auto-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE\n  camera-probe first-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT [STATS_NODE [--step-at FRAME (--step-seconds SECONDS | --step-gain GAIN)]]\n  camera-probe list\n  camera-probe sensor-info /dev/v4l-subdevN\n  camera-probe configure-pipeline PLAN.json [--dry-run]\n  camera-probe apply-linear /dev/v4l-subdevN FRAME_LINES ANALOGUE_CODE DIGITAL_CODE SHUTTER_CODE [DCG_MODE]\n  camera-probe make-initial-parameters IQ.json OUT.bin [--ae-measurements | --awb-measurements SDK.bin SAMPLE_SCALE]\n  camera-probe self-test\n  camera-probe exposure-plan IQ.json SENSOR.json SECONDS GAIN [FRAME_LINES]\n  camera-probe stats /tmp/isp-statistics.raw\n  camera-probe capture-statistics /dev/videoN /tmp/isp-statistics.raw [options]\n  camera-probe capture-cif-with-parameters PARAM_NODE PARAM.bin RAW_TX RAW_RX ISP_NODE [--sof-node NODE] [--exposure-step SENSOR FRAME CODE | --gain-step SENSOR FRAME CODE] -- IMAGE_NODE OUT [capture options]\n  camera-probe capture-with-parameters PARAM_NODE PARAM.bin -- IMAGE_NODE OUT [capture options]\n  camera-probe submit-parameters /dev/videoN FULL_PARAMETERS.bin [--timeout-ms 3000] [--hold-ms 30000]\n  camera-probe events /dev/videoN [--timeout-ms 10000] [--count 8]\n  camera-probe capture /dev/videoN /tmp/frame.raw [options]\n\nOptions:\n  --width N --height N --fourcc NV12   Explicitly request a format (otherwise retain current)\n  --buffers N                         MMAP buffers: image 1–4 (default 1), statistics 2–4 (default 2)\n  --timeout-ms N                      Per-frame deadline (default 3000)\n  --warmup N                          Frames to discard before saving (default 2)\n  --require-no-rkaiq                  Refuse capture if rkaiq_3A_server/rkipc is running (always for statistics)\n\nWrites the last frame plus OUT.json metadata. Single-plane and multi-plane MMAP.\nThe existing kernel media graph, sensor driver, sensor settings and CMA memory\nmust already support capture. Does not start vendor software or modify boot.\n");
fn self_test() -> Result<(), String> {
    use shieldsigner_rkaiq::*;
    if interpolate(&[0., 1.], &[2., 4.], 0.5) != Ok(3.) {
        return Err("interpolation self-test failed".into());
    }
    let x = [0; LUT_VALUES];
    let y = [129; LUT_VALUES];
    let mut out = [0; LUT_VALUES];
    blend_lut(0.5, &x, &y, &mut out).map_err(|e| format!("{e:?}"))?;
    if out.iter().any(|&v| v != 64) {
        return Err("LUT self-test failed".into());
    }
    {
        use shieldsigner_rkaiq::media::*;
        let entities = [
            Entity {
                id: 1,
                kind: CAMERA_SENSOR,
            },
            Entity { id: 2, kind: 0 },
        ];
        let link = Link {
            source: Pad {
                entity: 1,
                ..Pad::default()
            },
            sink: Pad {
                entity: 2,
                ..Pad::default()
            },
            flags: 3,
            ..Link::default()
        };
        if upstream_sensor(&entities, &[link], 2, &mut [0; 2]) != Ok(Binding::Unique(1)) {
            return Err("Media topology self-test failed".into());
        }
    }
    println!("PASS: reconstructed interpolation, complete 2187-value LUT and media topology traversal. Full ARM-original differential test is separate.");
    Ok(())
}
fn decode_statistics(args: &[String]) -> Result<(), String> {
    use serde_json::json;
    use shieldsigner_rkaiq::statistics::*;
    if args.len() != 2 {
        return Err("stats requires exactly one saved full-ISP32 statistics buffer".into());
    }
    let bytes = std::fs::read(&args[1]).map_err(|e| e.to_string())?;
    let stats = Statistics::parse(&bytes).map_err(|_| {
        "Unsupported statistics size; expected one 13036/13040-byte full-ISP32 buffer".to_string()
    })?;
    let channels=[Channel::Ae0,Channel::Ae1,Channel::Ae2,Channel::Ae3].map(|c|json!({
        "grid":stats.ae(c).map(|grid|grid.map(|v|json!({"r":v.red,"g":v.green,"b":v.blue})).collect::<Vec<_>>()),
        "histogram":stats.histogram(c).map(|hist|hist.collect::<Vec<_>>())}));
    let report = json!({"layout":"full-ISP32","bytes":bytes.len(),"measurements":stats.measurements(),"frameId":stats.frame_id(),"parametersId":stats.parameters_id(),"ae":channels,
        "awb":stats.awb().map(|grid|grid.map(|v|json!({"r":v.red,"g":v.green,"b":v.blue,"whitePoints":v.white_points})).collect::<Vec<_>>()),
        "awbSums":stats.awb_sums().map(|sums|sums.map(|v|json!({"redNormal":v.red_normal,"blueNormal":v.blue_normal,"pointsNormal":v.points_normal,"pointsSecond":v.points_second,"redBig":v.red_big,"blueBig":v.blue_big,"pointsBig":v.points_big})).collect::<Vec<_>>()),
        "awbLumaHistogram":stats.awb_luma_histogram().map(|hist|hist.collect::<Vec<_>>()),
        "limitations":["Raw measurement decoding only; no IQ calibration, BLS correction, exposure selection or AWB gains are computed.","The supplied bytes must come from the pinned full-ISP32 statistics endpoint; size alone cannot identify hardware/layout."]});
    println!(
        "{}",
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
    );
    Ok(())
}
fn exposure_plan(args: &[String]) -> Result<(), String> {
    use serde_json::json;
    use shieldsigner_rkaiq::calibration::*;
    if !matches!(args.len(), 5 | 6) {
        return Err("exposure-plan requires IQ.json SENSOR.json SECONDS GAIN [FRAME_LINES]".into());
    }
    let text = std::fs::read_to_string(&args[1]).map_err(|e| e.to_string())?;
    let profile = SensorCalibration::from_json(&text)?;
    let sensor: serde_json::Value =
        serde_json::from_slice(&std::fs::read(&args[2]).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    let unsigned = |key: &str| -> Result<u32, String> {
        sensor[key]
            .as_u64()
            .filter(|v| *v <= u32::MAX as u64)
            .map(|v| v as u32)
            .ok_or_else(|| format!("Missing/invalid sensor snapshot field {key}"))
    };
    if unsigned("width")? != profile.width || unsigned("height")? != profile.height {
        return Err("IQ sensor resolution does not match the active sensor descriptor".into());
    }
    let minimum_frame = unsigned("linePeriodsPerField")?;
    let frame = if let Some(text) = args.get(5) {
        text.parse::<u32>().map_err(|_| "Invalid frame length")?
    } else {
        minimum_frame
    };
    if frame < minimum_frame {
        return Err("Frame length is below the sensor descriptor minimum".into());
    }
    let clock = sensor["pixelClockMHz"]
        .as_f64()
        .ok_or("Missing/invalid sensor pixelClockMHz")? as f32;
    let timing = RuntimeTiming {
        frame_length: frame,
        pixel_clock_mhz: clock,
        line_length_pixels: unsigned("pixelPeriodsPerLine")?,
    };
    let seconds = args[3]
        .parse::<f32>()
        .map_err(|_| "Invalid exposure seconds")?;
    let gain = args[4].parse::<f32>().map_err(|_| "Invalid real gain")?;
    let codes = profile.linear_codes(seconds, gain, timing)?;
    let band = profile
        .bands
        .iter()
        .find(|b| b.lower <= gain && gain <= b.upper);
    let report = json!({"kind":"offline-linear-exposure-plan","writesSensor":false,"automaticExposure":false,"iqSource":args[1],"sensorSnapshot":args[2],"seconds":seconds,"realGain":gain,"dcgMode":if profile.linear_dcg_supported {0}else{-1},"resolution":{"width":profile.width,"height":profile.height},"frameLengthLines":frame,"frameLengthSource":if args.len()==6 {"explicit"}else{"descriptor-minimum"},"lineLengthPixels":timing.line_length_pixels,"pixelClockMHz":clock,"integrationTimeCode":codes.integration_time,"gainCode":codes.gain,"gainModel":if profile.logarithmic_gain{"logarithmic"}else{"bands"},"usedGainFallback":!profile.logarithmic_gain && band.is_none_or(|b|b.scale==0.),"linearMaximumTimeFactors":profile.linear_max_factors,"analogueGainRange":profile.analogue_range,"digitalGainRange":profile.digital_range,"ispGainRange":profile.isp_gain_range,"linearUpdateDelays":{"time":profile.linear_update_delays[0],"gain":profile.linear_update_delays[1],"dcg":profile.linear_update_delays[2]},"limitations":["Converts explicit inputs only; no AE decision, frame scheduling, ISP setup or sensor writes.","Frame length defaults to descriptor minima and is not a measurement of current timing.","Returned codes still need sensor-specific limit/support checks before live programming; this tool does not apply the higher-level maximum-time rules."]});
    println!(
        "{}",
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
    );
    Ok(())
}
fn make_initial_parameters(args: &[String]) -> Result<(), String> {
    use std::io::{Read, Write};
    let measurements = args.len() == 4 && args[3] == "--ae-measurements";
    let awb = args.len() == 6 && args[3] == "--awb-measurements";
    if args.len() != 3 && !measurements && !awb {
        return Err("usage: make-initial-parameters IQ.json OUT.bin [--ae-measurements | --awb-measurements SDK.bin SAMPLE_SCALE]".into());
    }
    let mut input = Vec::new();
    std::fs::File::open(&args[1])
        .map_err(|e| e.to_string())?
        .take(8 * 1024 * 1024 + 1)
        .read_to_end(&mut input)
        .map_err(|e| e.to_string())?;
    if input.len() > 8 * 1024 * 1024 {
        return Err("IQ file exceeds 8 MiB".into());
    }
    let iq = serde_json::from_slice(&input).map_err(|e| e.to_string())?;
    let (params, report, sdk) = if awb {
        if args[2] == args[4] || std::path::Path::new(&args[4]).exists() {
            return Err("SDK output must be a distinct new path".into());
        }
        let scale=args[5].parse::<u32>().map_err(|_|"Invalid sample scale")?;
        if scale==0 {return Err("Sample scale must be positive".into());}
        let (params,report,sdk)=shieldsigner_rkaiq::initial_parameters::assemble_with_awb(&iq,scale)?;
        (params,report,Some(sdk))
    } else {
        let (params,report)=if measurements {shieldsigner_rkaiq::initial_parameters::assemble_with_ae(&iq)?} else {shieldsigner_rkaiq::initial_parameters::assemble(&iq)?};
        (params,report,None)
    };
    let mut out = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&args[2])
        .map_err(|e| e.to_string())?;
    out.write_all(&params).map_err(|e| e.to_string())?;
    if let Some(sdk)=sdk {
        let mut file=std::fs::OpenOptions::new().write(true).create_new(true).open(&args[4]).map_err(|e|e.to_string())?;
        file.write_all(&sdk).map_err(|e|e.to_string())?;
    }
    println!(
        "{}",
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
    );
    Ok(())
}
fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let result = match args.first().map(String::as_str) {
        None | Some("--help") | Some("-h") => {
            print!("{HELP}");
            Ok(())
        }
        Some("--version") => {
            println!(
                "camera-probe {} (partial RKAIQ reconstruction; standalone V4L2 diagnostic)",
                env!("CARGO_PKG_VERSION")
            );
            Ok(())
        }
        Some("self-test") => self_test(),
        Some("stats") => decode_statistics(&args),
        Some("exposure-plan") => exposure_plan(&args),
        Some("make-initial-parameters") => make_initial_parameters(&args),
        _ => platform(&args),
    };
    if let Err(error) = result {
        eprintln!("camera-probe: {error}");
        std::process::exit(1);
    }
}
#[cfg(not(target_os = "linux"))]
fn platform(_: &[String]) -> Result<(), String> {
    Err("camera access requires Linux; --help and self-test work on this host".into())
}
#[cfg(target_os = "linux")]
fn platform(args: &[String]) -> Result<(), String> {
    // Managed streaming acknowledges armed shutdown before potentially slow
    // file-backed code prefaulting. Other command behavior stays unchanged.
    let _code_lock = if args.first().map(String::as_str) == Some("stream-sc3336") {
        None
    } else {
        camera_code_lock::from_env().map_err(|e| e.to_string())?
    };
    linux::run(args).map_err(|e| e.to_string())
}

#[cfg(target_os = "linux")]
mod linux {
    use serde_json::{json, Value};
    use std::os::raw::c_long;
    use std::{
        fs::{self, File, OpenOptions},
        io::{self, Write},
        os::fd::{AsRawFd, RawFd},
        os::unix::fs::OpenOptionsExt,
        ptr,
        time::{Duration, Instant},
    };
    const CAPTURE: u32 = 1;
    const MPLANE: u32 = 9;
    const META_CAPTURE: u32 = 13;
    const META_OUTPUT: u32 = 14;
    const MMAP: u32 = 1;
    const PLANES: usize = 8;
    #[repr(C)]
    #[derive(Clone, Copy)]
    union FormatData {
        raw: [u8; 200],
        align: usize,
    }
    #[repr(C)]
    struct Format {
        kind: u32,
        data: FormatData,
    }
    #[repr(C)]
    #[derive(Clone, Copy)]
    union PlaneMemory {
        offset: u32,
        user: usize,
        fd: i32,
    }
    #[repr(C)]
    #[derive(Clone, Copy)]
    struct Plane {
        used: u32,
        length: u32,
        memory: PlaneMemory,
        offset: u32,
        reserved: [u32; 11],
    }
    // Deliberately use kernel long-sized time fields. ARM32's native 5.10 ioctl
    // uses the old 32-bit timeval layout, irrespective of musl time_t being 64-bit.
    #[repr(C)]
    struct KernelTimeval {
        seconds: c_long,
        microseconds: c_long,
    }
    #[repr(C)]
    struct Timecode {
        kind: u32,
        flags: u32,
        frames: u8,
        seconds: u8,
        minutes: u8,
        hours: u8,
        userbits: [u8; 4],
    }
    #[repr(C)]
    union BufferMemory {
        offset: u32,
        user: usize,
        planes: *mut Plane,
        fd: i32,
    }
    #[repr(C)]
    struct Buffer {
        index: u32,
        kind: u32,
        used: u32,
        flags: u32,
        field: u32,
        time: KernelTimeval,
        timecode: Timecode,
        sequence: u32,
        memory: u32,
        data: BufferMemory,
        length: u32,
        reserved: u32,
        request: i32,
    }
    #[repr(C)]
    struct RequestBuffers {
        count: u32,
        kind: u32,
        memory: u32,
        capabilities: u32,
        reserved: u32,
    }
    const fn ioc<T>(direction: u32, nr: u32) -> u32 {
        (direction << 30) | ((std::mem::size_of::<T>() as u32) << 16) | (b'V' as u32) << 8 | nr
    }
    const QUERYCAP: u32 = ioc::<[u8; 104]>(2, 0);
    const ENUMFMT: u32 = ioc::<[u8; 64]>(3, 2);
    const GETFMT: u32 = ioc::<Format>(3, 4);
    const SETFMT: u32 = ioc::<Format>(3, 5);
    const REQBUFS: u32 = ioc::<RequestBuffers>(3, 8);
    const QUERYBUF: u32 = ioc::<Buffer>(3, 9);
    const QUEUE: u32 = ioc::<Buffer>(3, 15);
    const DEQUEUE: u32 = ioc::<Buffer>(3, 17);
    const STREAMON: u32 = ioc::<u32>(1, 18);
    const STREAMOFF: u32 = ioc::<u32>(1, 19);
    #[cfg(target_pointer_width = "32")]
    const _: () = {
        assert!(std::mem::size_of::<Format>() == 204);
        assert!(std::mem::size_of::<Buffer>() == 68);
        assert!(std::mem::size_of::<Plane>() == 60);
        assert!(GETFMT == 0xc0cc5604);
        assert!(QUERYBUF == 0xc0445609);
    };
    #[cfg(target_pointer_width = "64")]
    const _: () = {
        assert!(std::mem::size_of::<Format>() == 208);
        assert!(std::mem::size_of::<Buffer>() == 88);
        assert!(std::mem::size_of::<Plane>() == 64);
    };
    fn error(message: impl Into<String>) -> io::Error {
        io::Error::other(message.into())
    }
    fn zero<T>() -> T {
        unsafe { std::mem::zeroed() }
    }
    fn ioctl<T>(fd: RawFd, request: u32, value: &mut T) -> io::Result<()> {
        #[cfg(test)]
        if let Some(result) = first_frame_driver::ioctl(fd, request, value) {
            return result;
        }
        #[cfg(test)]
        if let Some(result) = raw_bridge::mock_ioctl(fd, request, value) {
            return result;
        }
        loop {
            let result = unsafe { libc::ioctl(fd, request as _, value as *mut T) };
            if result >= 0 {
                return Ok(());
            }
            let e = io::Error::last_os_error();
            if e.kind() != io::ErrorKind::Interrupted {
                return Err(e);
            }
        }
    }
    fn get32(bytes: &[u8], at: usize) -> u32 {
        u32::from_ne_bytes(bytes[at..at + 4].try_into().unwrap())
    }
    fn put32(bytes: &mut [u8], at: usize, value: u32) {
        bytes[at..at + 4].copy_from_slice(&value.to_ne_bytes());
    }
    fn cstr(bytes: &[u8]) -> String {
        String::from_utf8_lossy(bytes.split(|&x| x == 0).next().unwrap_or_default()).into_owned()
    }
    fn fourcc(value: u32) -> String {
        value
            .to_le_bytes()
            .iter()
            .map(|&b| if b.is_ascii_graphic() { b as char } else { '?' })
            .collect()
    }
    fn open(path: &str, write: bool) -> io::Result<File> {
        #[cfg(test)]
        if let Some(file) = first_frame_driver::statistics_file(path) {
            return file;
        }
        let file = OpenOptions::new()
            .read(true)
            .write(write)
            .custom_flags(libc::O_NONBLOCK | libc::O_CLOEXEC)
            .open(path)?;
        #[cfg(test)]
        first_frame_driver::opened(path, file.as_raw_fd());
        Ok(file)
    }
    fn capability(file: &File) -> io::Result<([u8; 104], u32)> {
        let mut cap = [0; 104];
        ioctl(file.as_raw_fd(), QUERYCAP, &mut cap)?;
        let flags = get32(&cap, 84);
        Ok((
            cap,
            if flags & 0x80000000 != 0 {
                get32(&cap, 88)
            } else {
                flags
            },
        ))
    }
    fn format(file: &File, kind: u32) -> io::Result<Format> {
        let mut value: Format = zero();
        value.kind = kind;
        ioctl(file.as_raw_fd(), GETFMT, &mut value)?;
        Ok(value)
    }
    fn format_json(value: &Format) -> Value {
        let raw = unsafe { &value.data.raw };
        if matches!(value.kind, META_CAPTURE | META_OUTPUT) {
            return json!({"bufferType":value.kind,"fourcc":fourcc(get32(raw,0)),"fourccValue":get32(raw,0),"bufferSize":get32(raw,4)});
        }
        let multi = matches!(value.kind, MPLANE | 10); // capture or output mplane
        let count = if multi { raw[180] as usize } else { 1 };
        let mut planes = Vec::new();
        for n in 0..count.min(PLANES) {
            planes.push(if multi {
                json!({"sizeImage":get32(raw,20+n*20),"bytesPerLine":get32(raw,24+n*20)})
            } else {
                json!({"sizeImage":get32(raw,20),"bytesPerLine":get32(raw,16)})
            });
        }
        let (colorspace, ycbcr, quantization, transfer) = camera_colorimetry(value);
        json!({"bufferType":value.kind,"width":get32(raw,0),"height":get32(raw,4),"fourcc":fourcc(get32(raw,8)),"fourccValue":get32(raw,8),"planeCount":count,"planes":planes,"colorspace":colorspace,"ycbcrEncoding":ycbcr,"quantization":quantization,"transferFunction":transfer})
    }
    fn vendor_processes() -> Vec<String> {
        let mut found = Vec::new();
        if let Ok(entries) = fs::read_dir("/proc") {
            for entry in entries.flatten() {
                if entry.file_name().to_string_lossy().parse::<u32>().is_err() {
                    continue;
                }
                if let Ok(name) = fs::read_to_string(entry.path().join("comm")) {
                    let name = name.trim();
                    if ["rkipc", "rkaiq_3A_server"].contains(&name) {
                        found.push(format!("{}:{name}", entry.file_name().to_string_lossy()));
                    }
                }
            }
        }
        found
    }
    fn device_node(major: u32, minor: u32) -> Option<String> {
        use std::os::unix::fs::{FileTypeExt, MetadataExt};
        let valid = |path: &std::path::Path| {
            fs::metadata(path).ok().is_some_and(|m| {
                m.file_type().is_char_device()
                    && libc::major(m.rdev()) == major
                    && libc::minor(m.rdev()) == minor
            })
        };
        if let Ok(path) = fs::canonicalize(format!("/dev/char/{major}:{minor}")) {
            if valid(&path) {
                return Some(path.to_string_lossy().into_owned());
            }
        }
        // BusyBox/mdev images may not create /dev/char symlinks.
        if let Ok(info) = fs::read_to_string(format!("/sys/dev/char/{major}:{minor}/uevent")) {
            if let Some(name) = info.lines().find_map(|line| line.strip_prefix("DEVNAME=")) {
                let path = std::path::Path::new("/dev").join(name);
                if valid(&path) {
                    return Some(path.to_string_lossy().into_owned());
                }
            }
        }
        if let Ok(entries) = fs::read_dir("/dev") {
            for entry in entries.flatten() {
                let path = entry.path();
                if valid(&path) {
                    return Some(path.to_string_lossy().into_owned());
                }
            }
        }
        None
    }
    fn media_graph() -> Vec<Value> {
        use shieldsigner_rkaiq::media::{self, Binding, Entity, Link, LinksQuery, Pad};
        let mut graph = Vec::new();
        for index in 0..32 {
            let path = format!("/dev/media{index}");
            let file = match open(&path, false) {
                Ok(file) => file,
                Err(e) if e.kind() == io::ErrorKind::NotFound => continue,
                Err(e) => {
                    graph.push(json!({"device":path,"complete":false,"errors":[format!("Open media device: {e}")],"entities":[]}));
                    continue;
                }
            };
            let mut info = [0u8; 256];
            let info_request = (3u32 << 30) | (256u32 << 16) | ((b'|' as u32) << 8);
            if let Err(e) = ioctl(file.as_raw_fd(), info_request, &mut info) {
                graph.push(json!({"device":path,"complete":false,"errors":[format!("DEVICE_INFO: {e}")],"entities":[]}));
                continue;
            }
            let mut entities = Vec::new();
            let mut typed_entities = Vec::new();
            let mut typed_links: Vec<Link> = Vec::new();
            let mut links = Vec::new();
            let mut errors = Vec::new();
            let mut last = 0u32;
            let mut enumeration_ended = false;
            for _ in 0..1024 {
                let mut entity = [0u8; 256];
                put32(&mut entity, 0, last | 0x80000000);
                if let Err(e) = ioctl(file.as_raw_fd(), info_request | 1, &mut entity) {
                    if e.raw_os_error() != Some(libc::EINVAL) {
                        errors.push(format!("ENUM_ENTITIES: {e}"));
                    }
                    enumeration_ended = true;
                    break;
                }
                let id = get32(&entity, 0);
                if id <= last || id & 0x80000000 != 0 {
                    errors.push("Non-increasing/invalid entity ID".into());
                    break;
                }
                last = id;
                let major = get32(&entity, 72);
                let minor = get32(&entity, 76);
                let kind = get32(&entity, 36);
                let pad_count = u16::from_ne_bytes(entity[52..54].try_into().unwrap()) as usize;
                let link_count = u16::from_ne_bytes(entity[54..56].try_into().unwrap()) as usize;
                let mut pads = Vec::new();
                if pad_count > 4096 || link_count > 4096 {
                    errors.push(format!("Entity {id}: unreasonable pad/link count"));
                } else {
                    let mut raw_pads = vec![Pad::default(); pad_count];
                    let mut raw_links = vec![Link::default(); link_count];
                    let mut query = LinksQuery {
                        entity: id,
                        pads: if pad_count == 0 {
                            ptr::null_mut()
                        } else {
                            raw_pads.as_mut_ptr()
                        },
                        links: if link_count == 0 {
                            ptr::null_mut()
                        } else {
                            raw_links.as_mut_ptr()
                        },
                        reserved: [0; 4],
                    };
                    let request = (3u32 << 30)
                        | ((std::mem::size_of::<LinksQuery>() as u32) << 16)
                        | ((b'|' as u32) << 8)
                        | 2;
                    match ioctl(file.as_raw_fd(), request, &mut query) {
                        Err(e) => errors.push(format!("Entity {id} ENUM_LINKS: {e}")),
                        Ok(()) => {
                            for pad in raw_pads {
                                pads.push(json!({"entity":pad.entity,"index":pad.index,"flags":pad.flags}));
                            }
                            for link in raw_links {
                                if !typed_links.iter().any(|l| {
                                    l.source.entity == link.source.entity
                                        && l.source.index == link.source.index
                                        && l.sink.entity == link.sink.entity
                                        && l.sink.index == link.sink.index
                                        && l.flags == link.flags
                                }) {
                                    links.push(json!({"source":{"entity":link.source.entity,"pad":link.source.index},"sink":{"entity":link.sink.entity,"pad":link.sink.index},"flags":link.flags,"enabled":link.flags&1!=0}));
                                    typed_links.push(link);
                                }
                            }
                        }
                    }
                }
                typed_entities.push(Entity { id, kind });
                entities.push(json!({"id":id,"name":cstr(&entity[4..36]),"type":kind,"major":major,"minor":minor,"device":device_node(major,minor),"padCount":pad_count,"linkCount":link_count,"pads":pads}));
            }
            if !enumeration_ended {
                errors.push("Entity enumeration did not reach its end".into());
            }
            let mut bindings = Vec::new();
            if errors.is_empty() {
                let mut scratch = vec![0; typed_entities.len()];
                for entity in &entities {
                    if entity["device"].is_null() {
                        continue;
                    }
                    let id = entity["id"].as_u64().unwrap() as u32;
                    match media::upstream_sensor(&typed_entities, &typed_links, id, &mut scratch) {
                        Ok(binding) => {
                            let (status, sensor) = match binding {
                                Binding::None => ("none", None),
                                Binding::Ambiguous => ("ambiguous", None),
                                Binding::Unique(sensor) => (
                                    "unique",
                                    entities
                                        .iter()
                                        .find(|e| e["id"].as_u64() == Some(sensor as u64))
                                        .cloned(),
                                ),
                            };
                            bindings.push(json!({"device":entity["device"],"entity":id,"status":status,"sensor":sensor}));
                        }
                        Err(e) => {
                            errors.push(format!("Topology validation: {e:?}"));
                            bindings.clear();
                            break;
                        }
                    }
                }
            }
            graph.push(json!({"device":path,"driver":cstr(&info[..16]),"model":cstr(&info[16..48]),"complete":errors.is_empty(),"errors":errors,"entities":entities,"links":links,"sensorPaths":bindings,"scope":"One media device; enabled directed data links only; no cross-media inference or link changes"}));
        }
        graph
    }
    fn list() -> io::Result<()> {
        let mut devices = Vec::new();
        let mut paths = Vec::new();
        for entry in fs::read_dir("/dev")?.flatten() {
            let name = entry.file_name();
            let name = name.to_string_lossy();
            if name.strip_prefix("video").is_some_and(|suffix| {
                !suffix.is_empty() && suffix.bytes().all(|b| b.is_ascii_digit())
            }) {
                paths.push(entry.path());
            }
        }
        paths.sort();
        for path in paths {
            let name = path.to_string_lossy().to_string();
            let file = match open(&name, false) {
                Ok(f) => f,
                Err(e) => {
                    devices.push(json!({"device":name,"error":e.to_string()}));
                    continue;
                }
            };
            let (cap, flags) = match capability(&file) {
                Ok(c) => c,
                Err(e) => {
                    devices.push(json!({"device":name,"error":e.to_string()}));
                    continue;
                }
            };
            let mut formats = Vec::new();
            for kind in [CAPTURE, MPLANE, META_CAPTURE, META_OUTPUT] {
                for index in 0..128 {
                    let mut desc = [0; 64];
                    put32(&mut desc, 0, index);
                    put32(&mut desc, 4, kind);
                    if ioctl(file.as_raw_fd(), ENUMFMT, &mut desc).is_err() {
                        break;
                    }
                    formats.push(json!({"bufferType":kind,"fourcc":fourcc(get32(&desc,44)),"description":cstr(&desc[12..44])}));
                }
            }
            let kind = if flags & 1 != 0 {
                Some(CAPTURE)
            } else if flags & 0x1000 != 0 {
                Some(MPLANE)
            } else if flags & 0x00800000 != 0 {
                Some(META_CAPTURE)
            } else if flags & 0x08000000 != 0 {
                Some(META_OUTPUT)
            } else {
                None
            };
            let current = kind
                .and_then(|kind| format(&file, kind).ok())
                .map(|f| format_json(&f));
            devices.push(json!({"device":name,"driver":cstr(&cap[..16]),"card":cstr(&cap[16..48]),"capabilities":format!("0x{flags:08x}"),"currentFormat":current,"formats":formats}));
        }
        println!(
            "{}",
            serde_json::to_string_pretty(
                &json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"linksRkaiq":false,"vendorProcesses":vendor_processes(),"devices":devices,"mediaGraph":media_graph(),"limitations":["This is a Linux node/format inventory, not proof of camera capture or absence of vendor initialization at boot."]})
            )?
        );
        Ok(())
    }
    struct Mapping {
        address: *mut libc::c_void,
        length: usize,
    }
    impl Mapping {
        fn new(fd: RawFd, length: usize, offset: u32) -> io::Result<Self> {
            #[cfg(test)]
            if first_frame_driver::active() {
                let address = unsafe {
                    libc::mmap(
                        ptr::null_mut(),
                        length,
                        libc::PROT_READ | libc::PROT_WRITE,
                        libc::MAP_PRIVATE | libc::MAP_ANONYMOUS,
                        -1,
                        0,
                    )
                };
                if address == libc::MAP_FAILED {
                    return Err(io::Error::last_os_error());
                }
                first_frame_driver::mapped(fd, address, length);
                return Ok(Self { address, length });
            }
            if length == 0 || length > 128 * 1024 * 1024 {
                return Err(error("Invalid/oversized driver MMAP length"));
            }
            let address = unsafe {
                libc::mmap(
                    ptr::null_mut(),
                    length,
                    libc::PROT_READ | libc::PROT_WRITE,
                    libc::MAP_SHARED,
                    fd,
                    offset as libc::off_t,
                )
            };
            if address == libc::MAP_FAILED {
                return Err(io::Error::last_os_error());
            }
            Ok(Self { address, length })
        }
    }
    impl Drop for Mapping {
        fn drop(&mut self) {
            unsafe {
                libc::munmap(self.address, self.length);
            }
        }
    }
    struct Stream {
        fd: RawFd,
        kind: u32,
    }
    impl Drop for Stream {
        fn drop(&mut self) {
            let _ = ioctl(self.fd, STREAMOFF, &mut self.kind);
        }
    }
    fn buffer(index: u32, kind: u32, planes: &mut [Plane; PLANES]) -> Buffer {
        let mut value: Buffer = zero();
        value.index = index;
        value.kind = kind;
        value.memory = MMAP;
        if kind == MPLANE {
            value.length = PLANES as u32;
            value.data.planes = planes.as_mut_ptr();
        }
        value
    }
    fn camera_monotonic_ns() -> io::Result<u64> {
        let mut value: libc::timespec = unsafe { std::mem::zeroed() };
        if unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut value) } != 0 {
            return Err(io::Error::last_os_error());
        }
        let seconds = u64::try_from(value.tv_sec).map_err(|_| error("Negative monotonic seconds"))?;
        let nanos = u64::try_from(value.tv_nsec).map_err(|_| error("Negative monotonic nanoseconds"))?;
        if nanos >= 1_000_000_000 { return Err(error("Invalid monotonic nanoseconds")); }
        seconds.checked_mul(1_000_000_000).and_then(|v| v.checked_add(nanos))
            .ok_or_else(|| error("Monotonic timestamp overflow"))
    }
    fn check_camera_cancel(cancel: Option<&std::sync::atomic::AtomicBool>) -> io::Result<()> {
        if cancel.is_some_and(|flag| flag.load(std::sync::atomic::Ordering::Acquire)) {
            return Err(io::Error::new(
                io::ErrorKind::Interrupted,
                "Camera capture cancelled",
            ));
        }
        Ok(())
    }
    fn wait_cancelable(
        fd: RawFd,
        deadline: Instant,
        cancel: Option<&std::sync::atomic::AtomicBool>,
    ) -> io::Result<()> {
        check_camera_cancel(cancel)?;
        #[cfg(test)]
        if first_frame_driver::active() {
            return Ok(());
        }
        loop {
            check_camera_cancel(cancel)?;
            let left = deadline.saturating_duration_since(Instant::now());
            if left.is_zero() {
                return Err(error("Capture timeout: no completed frame; check media graph, sensor and memory allocation"));
            }
            let mut poll = libc::pollfd {
                fd,
                events: libc::POLLIN | libc::POLLPRI,
                revents: 0,
            };
            let result = unsafe {
                libc::poll(
                    &mut poll,
                    1,
                    left.as_millis().max(1).min(if cancel.is_some() {
                        100
                    } else {
                        i32::MAX as u128
                    }) as i32,
                )
            };
            if result > 0 {
                if poll.revents & (libc::POLLERR | libc::POLLHUP | libc::POLLNVAL) != 0 {
                    return Err(error(format!(
                        "Video poll error: revents=0x{:x}",
                        poll.revents
                    )));
                }
                return Ok(());
            }
            if result < 0 {
                let e = io::Error::last_os_error();
                if e.kind() != io::ErrorKind::Interrupted {
                    return Err(e);
                }
            }
        }
    }
    fn capture(args: &[String], statistics: bool) -> io::Result<()> {
        capture_cancelable(args, statistics, None)
    }
    fn capture_cancelable(
        args: &[String],
        statistics: bool,
        cancel: Option<&std::sync::atomic::AtomicBool>,
    ) -> io::Result<()> {
        check_camera_cancel(cancel)?;
        if args.len() < 2 {
            return Err(error("capture needs DEVICE and OUT; see --help"));
        }
        let device = &args[0];
        let output = &args[1];
        let (mut width, mut height, mut pixel) = (None, None, None);
        let (mut buffers, mut timeout, mut warmup) =
            (if statistics { 2u32 } else { 1u32 }, 3000u64, 2u32);
        let mut require_no_vendor = statistics;
        let mut i = 2;
        while i < args.len() {
            let key = args[i].as_str();
            if key == "--require-no-rkaiq" {
                require_no_vendor = true;
                i += 1;
                continue;
            }
            if statistics && matches!(key, "--width" | "--height" | "--fourcc") {
                return Err(error("Statistics capture retains its metadata format; image dimensions/FourCC options are unsupported"));
            }
            let value = args
                .get(i + 1)
                .ok_or_else(|| error(format!("Missing value for {key}")))?;
            match key {
                "--width" => {
                    width = Some(value.parse::<u32>().map_err(|_| error("Invalid width"))?)
                }
                "--height" => {
                    height = Some(value.parse::<u32>().map_err(|_| error("Invalid height"))?)
                }
                "--fourcc" => {
                    if value.len() != 4 || !value.is_ascii() {
                        return Err(error("FourCC needs four ASCII bytes"));
                    }
                    pixel = Some(u32::from_le_bytes(value.as_bytes().try_into().unwrap()));
                }
                "--buffers" => {
                    buffers = value.parse().map_err(|_| error("Invalid buffer count"))?
                }
                "--timeout-ms" => timeout = value.parse().map_err(|_| error("Invalid timeout"))?,
                "--warmup" => warmup = value.parse().map_err(|_| error("Invalid warmup count"))?,
                _ => return Err(error(format!("Unknown option {key}"))),
            }
            i += 2;
        }
        if !(1..=4).contains(&buffers) || !(1..=60000).contains(&timeout) || warmup > 10000 {
            return Err(error(
                "Options exceed bounds: buffers 1–4, timeout 1–60000 ms, warmup 0–10000",
            ));
        }
        if statistics && buffers < 2 {
            return Err(error(
                "The pinned statistics driver requires at least two buffers",
            ));
        }
        if std::path::Path::new(output).exists()
            || std::path::Path::new(&format!("{output}.json")).exists()
        {
            return Err(error(
                "Capture output or metadata already exists; choose a new output name",
            ));
        }
        let active = vendor_processes();
        if require_no_vendor && !active.is_empty() {
            return Err(error(format!(
                "Vendor camera processes still running: {active:?}"
            )));
        }
        let file = open(device, true)?;
        let fd = file.as_raw_fd();
        let (_, flags) = capability(&file)?;
        let kind = if statistics {
            if flags & 0x00800000 == 0 {
                return Err(error("Node is not a metadata-capture endpoint"));
            }
            META_CAPTURE
        } else if flags & 1 != 0 {
            CAPTURE
        } else if flags & 0x1000 != 0 {
            MPLANE
        } else {
            return Err(error("Node is not a video-capture endpoint"));
        };
        if flags & 0x04000000 == 0 {
            return Err(error("Node does not advertise streaming/MMAP capture"));
        }
        let mut fmt = format(&file, kind)?;
        if statistics {
            let raw = unsafe { &fmt.data.raw };
            if get32(raw, 0) != u32::from_le_bytes(*b"RK1S")
                || get32(raw, 4) != shieldsigner_rkaiq::statistics::BUFFER_BYTES as u32
            {
                return Err(error(format!(
                    "Unsupported statistics format/layout: {}",
                    format_json(&fmt)
                )));
            }
        }
        if width.is_some() || height.is_some() || pixel.is_some() {
            let raw = unsafe { &mut fmt.data.raw };
            if let Some(w) = width {
                if w == 0 {
                    return Err(error("Width must be nonzero"));
                }
                put32(raw, 0, w);
            }
            if let Some(h) = height {
                if h == 0 {
                    return Err(error("Height must be nonzero"));
                }
                put32(raw, 4, h);
            }
            if let Some(p) = pixel {
                put32(raw, 8, p);
            }
            if width.is_some() || height.is_some() {
                // G_FMT's stride/extent describe the old geometry. Reusing them
                // keeps native-width padding even after requesting a VGA image.
                if kind == MPLANE {
                    for plane in 0..PLANES {
                        put32(raw, 20 + plane * 20, 0);
                        put32(raw, 24 + plane * 20, 0);
                    }
                } else {
                    put32(raw, 16, 0);
                    put32(raw, 20, 0);
                }
            }
            ioctl(fd, SETFMT, &mut fmt)?;
        }
        let live_stream = if statistics { None } else { CameraFrameStream::from_environment(&fmt)? };
        let mut request = RequestBuffers {
            count: buffers,
            kind,
            memory: MMAP,
            capabilities: 0,
            reserved: 0,
        };
        ioctl(fd, REQBUFS, &mut request).map_err(|e| {
            error(format!(
                "REQBUFS failed ({e}); record current format and CMA/free-memory information"
            ))
        })?;
        if request.count == 0 || request.count > 16 {
            return Err(error("Driver returned invalid buffer count"));
        }
        let mut mapped = Vec::new();
        for index in 0..request.count {
            check_camera_cancel(cancel)?;
            let mut planes: [Plane; PLANES] = zero();
            let mut b = buffer(index, kind, &mut planes);
            ioctl(fd, QUERYBUF, &mut b)?;
            let count = if kind == MPLANE { b.length as usize } else { 1 };
            if count == 0 || count > PLANES {
                return Err(error("Driver returned invalid plane count"));
            }
            let mut mappings = Vec::new();
            for plane in planes.iter().take(count) {
                let (length, offset) = if kind == MPLANE {
                    (plane.length as usize, unsafe { plane.memory.offset })
                } else {
                    (b.length as usize, unsafe { b.data.offset })
                };
                mappings.push(Mapping::new(fd, length, offset)?);
            }
            mapped.push(mappings);
            ioctl(fd, QUEUE, &mut b)?;
        }
        let mut stream_kind = kind;
        check_camera_cancel(cancel)?;
        ioctl(fd, STREAMON, &mut stream_kind)?;
        let stream = Stream { fd, kind };
        let mut saved = None;
        let continuous = !statistics && CAMERA_CONTINUOUS.load(std::sync::atomic::Ordering::Relaxed);
        if continuous && live_stream.is_none() { return Err(error("Continuous capture requires an application socket")); }
        for frame in 0..=if continuous { u32::MAX } else { warmup } {
            if continuous && CAMERA_STREAM_STOP.load(std::sync::atomic::Ordering::Relaxed) { break; }
            check_camera_cancel(cancel)?;
            let deadline = Instant::now() + Duration::from_millis(timeout);
            let mut planes: [Plane; PLANES] = zero();
            let mut b = buffer(0, kind, &mut planes);
            loop {
                wait_cancelable(fd, deadline, cancel)?;
                match ioctl(fd, DEQUEUE, &mut b) {
                    Ok(()) => break,
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => continue,
                    Err(e) => return Err(e),
                }
            }
            if b.flags & 0x40 != 0 {
                return Err(error(format!(
                    "Driver marked frame {} as corrupted (V4L2_BUF_FLAG_ERROR)",
                    b.sequence
                )));
            }
            let mappings = mapped
                .get(b.index as usize)
                .ok_or_else(|| error("Driver returned out-of-range buffer index"))?;
            if kind == MPLANE && b.length as usize != mappings.len() {
                return Err(error("Dequeued plane count changed unexpectedly"));
            }
            if frame == warmup || live_stream.is_some() {
                let mut bytes = Vec::new();
                let mut metadata = Vec::new();
                for (n, mapping) in mappings.iter().enumerate() {
                    let (used, offset) = if kind == MPLANE {
                        (planes[n].used as usize, planes[n].offset as usize)
                    } else {
                        (b.used as usize, 0)
                    };
                    if used == 0 || used > mapping.length || offset > used {
                        return Err(error("Driver returned empty or invalid frame payload"));
                    }
                    let data = unsafe {
                        std::slice::from_raw_parts(
                            mapping.address.cast::<u8>().add(offset),
                            used - offset,
                        )
                    };
                    metadata.push(json!({"plane":n,"fileOffset":bytes.len(),"bytes":data.len(),"dataOffset":offset}));
                    bytes.extend_from_slice(data);
                }
                if let Some(stream) = &live_stream { stream.publish(b.sequence, &bytes); }
                if frame == warmup || continuous { saved = Some((
                    bytes,
                    metadata,
                    b.sequence,
                    b.time.seconds,
                    b.time.microseconds,
                )); }
            }
            ioctl(fd, QUEUE, &mut b)?;
        }
        drop(stream);
        drop(mapped);
        request.count = 0;
        ioctl(fd, REQBUFS, &mut request)?;
        if saved.is_none() && continuous && camera_stream_cancelled() {
            println!("{}", json!({"event":"image-capture-cancelled","beforeFirstFrame":true}));
            return Ok(());
        }
        let (bytes, planes, sequence, seconds, microseconds) =
            saved.ok_or_else(|| error("No frame saved"))?;
        let statistics_header = if statistics {
            let decoded = shieldsigner_rkaiq::statistics::Statistics::parse(&bytes)
                .map_err(|_| error("Driver returned an unsupported statistics payload size"))?;
            Some(
                json!({"layout":"full-ISP32","measurements":decoded.measurements(),"frameId":decoded.frame_id(),"parametersId":decoded.parameters_id()}),
            )
        } else {
            None
        };
        check_camera_cancel(cancel)?;
        // App streaming delivers scene pixels over the private socket. Saving a
        // final scene image is a diagnostic opt-in, not normal scan behavior.
        let scene_image_saved = !continuous
            || std::env::var("SHIELDSIGNER_CAMERA_SAVE_IMAGE").as_deref() == Ok("1");
        if scene_image_saved {
            let mut out = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(output)?;
            out.write_all(&bytes)?;
        }
        let report = json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"device":device,"captureKind":if statistics {"isp-statistics"}else{"image"},"payloadSaved":scene_image_saved,"sceneImageSaved":!statistics && scene_image_saved,"statistics":statistics_header,"linksRkaiq":false,"vendorProcessesBeforeCapture":active,"vendorProcessesAfterCapture":vendor_processes(),"requireNoRkaiq":require_no_vendor,"format":format_json(&fmt),"bytes":bytes.len(),"planes":planes,"sequence":sequence,"timestamp":{"seconds":seconds,"microseconds":microseconds},"limitations":["This low-level capture report does not establish ISP calibration or automatic-control behavior; consult the enclosing command log for applied parameters, exposure control and white-balance mode.","Absent vendor processes do not prove the graph was never initialized by vendor software during boot."]});
        let meta = format!("{output}.json");
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&meta)?;
        file.write_all(serde_json::to_string_pretty(&report)?.as_bytes())?;
        println!("{}", serde_json::to_string_pretty(&report)?);
        Ok(())
    }
    const CAMERA_TRACE_LIMIT:usize=256;
    fn record_camera_trace(trace:&mut Vec<Value>,value:Value) {
        if trace.len()==CAMERA_TRACE_LIMIT {trace.remove(0);}
        trace.push(value);
    }
    // Raw ARM32 kernel event storage: do not use musl's time64 timespec.
    struct SensorDevice {
        file: File,
        queries: Vec<Value>,
        bus: Option<u32>,
        writes: Vec<Value>,
    }
    impl SensorDevice {
        fn query<T>(&mut self, label: &str, request: u32, value: &mut T) -> io::Result<()> {
            let result = ioctl(self.file.as_raw_fd(), request, value);
            record_camera_trace(&mut self.queries,json!({"query":label,"request":format!("0x{request:08x}"),"error":result.as_ref().err().map(|e|e.to_string())}));
            result
        }
    }
    impl shieldsigner_rkaiq::sensor_descriptor::Backend for SensorDevice {
        type Error = io::Error;
        fn format(&mut self) -> io::Result<shieldsigner_rkaiq::sensor_descriptor::Format> {
            let mut value = [0u8; 88];
            put32(&mut value, 0, 1);
            self.query("active-pad-0-format", 0xc0585604, &mut value)?;
            self.bus = Some(get32(&value, 16));
            Ok(shieldsigner_rkaiq::sensor_descriptor::Format {
                width: get32(&value, 8),
                height: get32(&value, 12),
                media_bus_code: get32(&value, 16),
            })
        }
        fn minimum(&mut self, id: u32) -> io::Result<i32> {
            let mut value = [0u8; 68];
            put32(&mut value, 0, id);
            self.query(
                &format!("control-minimum-0x{id:08x}"),
                0xc0445624,
                &mut value,
            )?;
            Ok(get32(&value, 40) as i32)
        }
        fn frame_interval(&mut self) -> io::Result<(u32, u32)> {
            let mut value = [0u8; 48];
            self.query("pad-0-frame-interval", 0xc0305615, &mut value)?;
            Ok((get32(&value, 4), get32(&value, 8)))
        }
        fn pixel_rate(&mut self) -> io::Result<i64> {
            let mut control = [0u8; 20];
            put32(&mut control, 0, 0x009f0902);
            let mut controls = [0u8; 24];
            put32(&mut controls, 0, 0x009f0000);
            put32(&mut controls, 4, 1);
            put32(&mut controls, 20, control.as_mut_ptr() as usize as u32);
            self.query("pixel-rate-fallback", 0xc0185647, &mut controls)?;
            Ok(i64::from_ne_bytes(control[12..20].try_into().unwrap()))
        }
        fn nr_switch(&mut self) -> io::Result<[u32; 4]> {
            let mut value = [0u8; 16];
            self.query("optional-noise-switch", 0x801056c9, &mut value)?;
            Ok(core::array::from_fn(|i| get32(&value, i * 4)))
        }
        fn dcg_ratio(&mut self) -> io::Result<[u32; 3]> {
            let mut value = [0u8; 12];
            self.query("optional-conversion-gain-ratio", 0x800c56d2, &mut value)?;
            Ok(core::array::from_fn(|i| get32(&value, i * 4)))
        }
    }
    impl shieldsigner_rkaiq::sensor::Backend for SensorDevice {
        type Error = io::Error;
        fn descriptor(&mut self) -> io::Result<shieldsigner_rkaiq::sensor::Descriptor> {
            let descriptor = shieldsigner_rkaiq::sensor_descriptor::read(self)?;
            Ok(shieldsigner_rkaiq::sensor::Descriptor {
                line_periods_per_field: descriptor.line_periods_per_field(),
                output_height: descriptor.height(),
            })
        }
        fn control(&mut self, id: u32, value: i32) -> io::Result<()> {
            let mut control = shieldsigner_rkaiq::sensor::Control { id, value };
            let result = ioctl(self.file.as_raw_fd(), 0xc008561c, &mut control);
            record_camera_trace(&mut self.writes,json!({"operation":"set-control","id":id,"value":value,"request":"0xc008561c","success":result.is_ok(),"error":result.as_ref().err().map(|e|e.to_string())}));
            result
        }
        fn conversion_gain(&mut self, value: u32) -> io::Result<()> {
            let mut code = value;
            let result = ioctl(self.file.as_raw_fd(), 0x400456c6, &mut code);
            record_camera_trace(&mut self.writes,json!({"operation":"conversion-gain","value":value,"request":"0x400456c6","success":result.is_ok(),"error":result.as_ref().err().map(|e|e.to_string())}));
            result
        }
    }
    fn apply_linear(args: &[String]) -> io::Result<()> {
        use shieldsigner_rkaiq::sensor;
        if !matches!(args.len(), 5 | 6) {
            return Err(error("apply-linear requires DEVICE FRAME_LINES ANALOGUE_CODE DIGITAL_CODE SHUTTER_CODE [DCG_MODE]"));
        }
        let mut values = [0u32; 4];
        for (i, value) in values.iter_mut().enumerate() {
            *value = args[i + 1]
                .parse()
                .map_err(|_| error("Invalid unsigned control code"))?;
            if *value > i32::MAX as u32 {
                return Err(error(
                    "Control codes/frame length must fit a nonnegative signed 32-bit value",
                ));
            }
        }
        let dcg = if let Some(value) = args.get(5) {
            value
                .parse::<i32>()
                .map_err(|_| error("Invalid DCG mode"))?
        } else {
            -1
        };
        if !matches!(dcg, -1 | 0 | 1) {
            return Err(error("DCG mode must be -1 (skip), 0 or 1"));
        }
        if std::mem::size_of::<usize>() != 4 {
            return Err(error("Sensor write ABI currently targets ARM32 Linux only"));
        }
        let active = vendor_processes();
        if !active.is_empty() {
            return Err(error(format!(
                "Vendor camera processes still running: {active:?}"
            )));
        }
        let mut device = SensorDevice {
            file: open(&args[0], true)?,
            queries: Vec::new(),
            bus: None,
            writes: Vec::new(),
        };
        let exposure = sensor::LinearExposure {
            frame_length_lines: values[0],
            analogue_gain_code: values[1],
            digital_gain_code: values[2],
            coarse_integration_time: values[3],
            dcg_mode: dcg,
        };
        let mut frame_mirror = Some(0);
        let result = sensor::program_linear(&mut device, exposure, &mut frame_mirror);
        let wrote_frame = device
            .writes
            .first()
            .is_some_and(|v| v["success"] == true && v["id"] == sensor::VBLANK);
        let mut readback = Vec::new();
        if !device.writes.is_empty() {
            for id in [
                sensor::VBLANK,
                sensor::ANALOGUE_GAIN,
                sensor::DIGITAL_GAIN,
                sensor::EXPOSURE,
            ] {
                let mut control = sensor::Control { id, value: 0 };
                let observed = ioctl(device.file.as_raw_fd(), 0xc008561b, &mut control);
                let mut range = [0u8; 68];
                put32(&mut range, 0, id);
                let queried = ioctl(device.file.as_raw_fd(), 0xc0445624, &mut range);
                readback.push(json!({"id":id,"value":if observed.is_ok(){Some(control.value)}else{None},"error":observed.err().map(|e|e.to_string()),"range":if queried.is_ok(){Some(json!({"minimum":get32(&range,40) as i32,"maximum":get32(&range,44) as i32,"step":get32(&range,48) as i32,"default":get32(&range,52) as i32,"flags":get32(&range,56)}))}else{None},"rangeError":queried.err().map(|e|e.to_string())}));
            }
        }
        let report = json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"kind":"manual-linear-sensor-programming","device":args[0],"writesSensor":true,"automaticExposure":false,"success":result.is_ok(),"error":result.as_ref().err().map(|e|e.to_string()),"requested":{"frameLengthLines":values[0],"analogueGainCode":values[1],"digitalGainCode":values[2],"coarseIntegrationTime":values[3],"dcgMode":dcg},"frameLengthWritten":if wrote_frame {frame_mirror}else{None},"writes":device.writes,"descriptorQueries":device.queries,"controlReadback":readback,"vendorProcessesBefore":active,"vendorProcessesAfter":vendor_processes(),"limitations":["Explicit register/control codes only; no gain splitting, AE decision, delay scheduling, HDR or ISP initialization.","Driver success/readback is control state, not proof of sensor-register timing or image quality.","Earlier successful writes remain applied when a later operation fails."]});
        println!("{}", serde_json::to_string_pretty(&report)?);
        result.map_err(|e| {
            error(format!(
                "Sensor programming stopped: {e}; see JSON report for partial writes"
            ))
        })
    }
    fn sensor_info(args: &[String]) -> io::Result<()> {
        if args.len() != 1 {
            return Err(error(
                "sensor-info requires exactly one sensor subdevice path",
            ));
        }
        if std::mem::size_of::<usize>() != 4 {
            return Err(error("Sensor query ABI currently targets ARM32 Linux only"));
        }
        let mut reader = SensorDevice {
            file: open(&args[0], false)?,
            queries: Vec::new(),
            bus: None,
            writes: Vec::new(),
        };
        let descriptor = shieldsigner_rkaiq::sensor_descriptor::read(&mut reader).map_err(|e| {
            error(format!(
                "Sensor descriptor failed: {e}; query trace: {}",
                json!(reader.queries)
            ))
        })?;
        let report = json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"device":args[0],"linksRkaiq":false,"changesSensorSettings":false,"vendorProcesses":vendor_processes(),"width":descriptor.width(),"height":descriptor.height(),"mediaBusCode":reader.bus,"pixelFormat":fourcc(descriptor.pixel_format()),"pixelFormatValue":descriptor.pixel_format(),"pixelPeriodsPerLine":descriptor.pixel_periods_per_line(),"linePeriodsPerField":descriptor.line_periods_per_field(),"pixelClockMHz":descriptor.pixel_clock_mhz(),"pixelClockBits":format!("{:08x}",descriptor.pixel_clock_mhz().to_bits()),"coarseIntegrationMinimum":descriptor.minimum_integration(),"coarseIntegrationMargin":descriptor.integration_margin(),"noiseSwitch":descriptor.noise_switch(),"conversionGainRatio":descriptor.conversion_gain_ratio(),"queries":reader.queries,"nativeDescriptorHex":descriptor.bytes().iter().map(|b|format!("{b:02x}")).collect::<String>(),"limitations":["Descriptor line/frame periods use minimum blanking, not necessarily the current frame timing.","Recovered arithmetic includes native 16-bit narrowing and pixel-rate fallback; calibration and physical validity still require checking.","Queries do not configure the sensor, media graph, ISP or an exposure loop."]});
        println!("{}", serde_json::to_string_pretty(&report)?);
        Ok(())
    }
    fn events(args: &[String]) -> io::Result<()> {
        use shieldsigner_rkaiq::engine::{STREAM_START, STREAM_STOP};
        if std::mem::size_of::<usize>() != 4 {
            return Err(error("Stream-event ABI currently targets ARM32 Linux only"));
        }
        if args.is_empty() {
            return Err(error("events requires the rkisp-input-params device path"));
        }
        let (mut timeout, mut count) = (10000u64, 8u32);
        let mut i = 1;
        while i < args.len() {
            let value = args
                .get(i + 1)
                .ok_or_else(|| error("Missing event option value"))?;
            match args[i].as_str() {
                "--timeout-ms" => {
                    timeout = value.parse().map_err(|_| error("Invalid event timeout"))?
                }
                "--count" => count = value.parse().map_err(|_| error("Invalid event count"))?,
                _ => return Err(error("Unknown events option")),
            }
            i += 2;
        }
        if !(1..=60000).contains(&timeout) || !(1..=1000).contains(&count) {
            return Err(error("Event deadline must be 1–60000 ms and count 1–1000"));
        }
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .custom_flags(libc::O_NONBLOCK)
            .open(&args[0])?;
        for event in [STREAM_START, STREAM_STOP] {
            let mut subscription = [0u32; 8];
            subscription[0] = event;
            ioctl(file.as_raw_fd(), 0x4020565a, &mut subscription)?;
        }
        println!(
            "{}",
            json!({"status":"subscribed","device":args[0],"configuresIsp":false,"timeoutMs":timeout})
        );
        io::stdout().flush()?;
        let deadline = Instant::now() + Duration::from_millis(timeout);
        let mut received = 0;
        while received < count {
            let remaining = deadline.saturating_duration_since(Instant::now());
            if remaining.is_zero() {
                break;
            }
            let mut poll = libc::pollfd {
                fd: file.as_raw_fd(),
                events: libc::POLLPRI,
                revents: 0,
            };
            let result = unsafe {
                libc::poll(
                    &mut poll,
                    1,
                    remaining.as_millis().max(1).min(i32::MAX as u128) as i32,
                )
            };
            if result < 0 {
                let e = io::Error::last_os_error();
                if e.kind() == io::ErrorKind::Interrupted {
                    continue;
                }
                return Err(e);
            }
            if result == 0 {
                break;
            }
            if poll.revents & (libc::POLLERR | libc::POLLHUP | libc::POLLNVAL) != 0 {
                return Err(error("Stream-event poll failed"));
            }
            if poll.revents & libc::POLLPRI == 0 {
                continue;
            }
            let mut event = [0u32; 32];
            if let Err(e) = ioctl(file.as_raw_fd(), 0x80805659, &mut event) {
                if e.kind() == io::ErrorKind::WouldBlock {
                    continue;
                }
                return Err(e);
            }
            let name = match event[0] {
                STREAM_START => "stream-start",
                STREAM_STOP => "stream-stop",
                _ => "other",
            };
            println!(
                "{}",
                json!({"event":name,"type":event[0],"sequence":event[19]})
            );
            io::stdout().flush()?;
            received += 1;
        }
        println!(
            "{}",
            json!({"status":"finished","events":received,"countLimitReached":received==count})
        );
        Ok(())
    }
    include!("../camera_stream.rs");
    include!("../camera_ae_events.rs");
    include!("../camera_raw_bridge.rs");
    include!("../camera_parameters.rs");
    include!("../camera_pipeline.rs");
    include!("../camera_statistics_session.rs");
    include!("../camera_first_frame.rs");
    #[cfg(test)]
    include!("../camera_first_frame_test.rs");
    pub fn run(args: &[String]) -> io::Result<()> {
        match args.first().map(String::as_str) {
            Some("list") if args.len() == 1 => list(),
            Some("capture") => capture(&args[1..], false),
            Some("capture-statistics") => capture(&args[1..], true),
            Some("events") => events(&args[1..]),
            Some("sensor-info") => sensor_info(&args[1..]),
            Some("apply-linear") => apply_linear(&args[1..]),
            Some("submit-parameters") => submit_parameters(&args[1..]),
            Some("capture-with-parameters") => capture_with_parameters(&args[1..]),
            Some("capture-cif-with-parameters") => capture_cif_with_parameters(&args[1..]),
            Some("configure-pipeline") => pipeline_configuration::run(&args[1..]),
            Some("stream-sc3336") => stream_sc3336(&args[1..]),
            Some("auto-awb-frame-sc3336") => auto_awb_frame_sc3336(&args[1..]),
            Some("awb-gain-frame-sc3336") => awb_gain_frame_sc3336(&args[1..]),
            Some("awb-measurement-frame-sc3336") => awb_measurement_frame_sc3336(&args[1..]),
            Some("first-frame-sc3336") => first_frame_sc3336(&args[1..]),
            Some("auto-frame-sc3336") => auto_frame_sc3336(&args[1..]),
            _ => Err(error("Unknown command; see --help")),
        }
    }
}

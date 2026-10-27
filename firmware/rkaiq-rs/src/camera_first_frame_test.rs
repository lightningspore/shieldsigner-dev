// Full userspace startup exercise: simulated ioctl/poll/MMAP boundaries only.
mod first_frame_driver {
    use super::*;
    use std::{collections::HashMap, sync::Mutex};
    #[derive(Default)]
    struct Driver {
        roles: HashMap<RawFd, String>,
        trace: Vec<String>,
        formats: HashMap<String, Vec<u8>>,
        sof_observed_frame: Option<u32>,
        parameter_on: bool,
        parameter_pending: std::collections::VecDeque<u32>,
        parameter_would_block: bool,
        parameter_error_flag: bool,
        raw_inflight: bool,
        triggered: bool,
        raw_frames: u32,
        image_frames: u32,
        statistics_frames: u32,
        statistics_required: bool,
        multi_tx: bool,
        statistics_on: bool,
        statistics_mapping: usize,
    }
    static DRIVER: Mutex<Option<Driver>> = Mutex::new(None);
    pub(super) fn active() -> bool {
        DRIVER.lock().unwrap().is_some()
    }
    pub(super) fn statistics_file(path: &str) -> Option<io::Result<File>> {
        if path != "/dev/tty" || !active() {
            return None;
        }
        let result = File::open("/dev/zero");
        if let Ok(file) = &result {
            DRIVER
                .lock()
                .unwrap()
                .as_mut()
                .unwrap()
                .roles
                .insert(file.as_raw_fd(), "statistics".into());
        }
        Some(result)
    }
    pub(super) fn mapped(fd: RawFd, address: *mut libc::c_void, _length: usize) {
        let mut lock = DRIVER.lock().unwrap();
        let Some(d) = lock.as_mut() else {
            return;
        };
        if d.roles.get(&fd).map(String::as_str) == Some("statistics") {
            d.statistics_mapping = address as usize;
        }
    }
    pub(super) fn opened(path: &str, fd: RawFd) {
        let role = match path {
            "/dev/null" => "sensor",
            "/dev/zero" => "parameters",
            "/dev/full" => "tx",
            "/dev/random" => "rx",
            "/dev/urandom" => "isp",
            "/dev/ptmx" => "image",
            _ => return,
        };
        if let Some(driver) = DRIVER.lock().unwrap().as_mut() {
            driver.roles.insert(fd, role.into());
        }
    }
    pub(super) fn ioctl<T>(fd: RawFd, request: u32, value: &mut T) -> Option<io::Result<()>> {
        let mut lock = DRIVER.lock().unwrap();
        let d = lock.as_mut()?;
        let role = d.roles.get(&fd).expect("unregistered startup fd").clone();
        let b = unsafe {
            std::slice::from_raw_parts_mut((value as *mut T).cast::<u8>(), std::mem::size_of::<T>())
        };
        let again = || Some(Err(io::Error::from_raw_os_error(libc::EAGAIN)));
        match request {
            0xc0585604 => {
                put32(b, 8, 2304);
                put32(b, 12, 1296);
                put32(b, 16, 0x3007);
            }
            0xc040563d => {
                put32(b, 24, 2304);
                put32(b, 28, 1296);
            }
            0xc0585605 | 0xc040563e => {
                d.trace.push(format!("{role}:configure"));
            }
            QUERYCAP => {
                let cap = match role.as_str() {
                    "tx" if d.multi_tx => 0x04001000,
                    "tx" | "image" => 0x04000001,
                    "rx" => 0x04000002,
                    "parameters" => 0x0c000000,
                    "statistics" => 0x04800000,
                    _ => panic!("caps {role}"),
                };
                put32(b, 84, cap);
            }
            GETFMT => {
                let multi = get32(b, 0) == 9;
                if let Some(format) = d.formats.get(&role) {
                    b.copy_from_slice(format);
                } else if role == "statistics" {
                    put32(b, 4, u32::from_le_bytes(*b"RK1S"));
                    put32(b, 8, 13040);
                } else if role == "parameters" {
                    put32(b, 4, u32::from_le_bytes(*b"RK1P"));
                    put32(b, 8, 11145);
                } else {
                    put32(b, 4, 2304);
                    put32(b, 8, 1296);
                    put32(
                        b,
                        12,
                        u32::from_le_bytes(if role == "image" { *b"NV12" } else { *b"BG10" }),
                    );
                    put32(b, 20, if role == "image" { 2304 } else { 3072 });
                    put32(b, 24, if role == "image" { 4478976 } else { 3981312 });
                }
                if multi {
                    put32(b, 20, 0);
                    put32(b, 24, 3981312);
                    put32(b, 28, 3072);
                    b[184] = 1;
                }
            }
            SETFMT => {
                let multi = get32(b, 0) == 9;
                put32(b, 20, if role == "image" { 2304 } else { 3072 });
                put32(b, 24, if role == "image" { 4478976 } else { 3981312 });
                if multi {
                    put32(b, 20, 0);
                    put32(b, 24, 3981312);
                    put32(b, 28, 3072);
                    b[184] = 1;
                }
                d.formats.insert(role.clone(), b.to_vec());
                d.trace.push(format!("{role}:format"));
            }
            0xc0445624 => {
                use shieldsigner_rkaiq::sensor::*;
                let id = get32(b, 0);
                let min = match id {
                    0x009e0902 => 196,
                    VBLANK => 24,
                    ANALOGUE_GAIN => 128,
                    EXPOSURE => 2,
                    _ => 0,
                };
                put32(b, 40, min);
                put32(b, 44, 100000);
                put32(b, 48, 1);
            }
            0xc0305615 => {
                put32(b, 4, 1);
                put32(b, 8, 30);
            }
            0x801056c9 | 0x800c56d2 => {
                return Some(Err(io::Error::from_raw_os_error(libc::ENOTTY)))
            }
            0xc008561c => {
                d.trace.push(format!("sensor:write:{:x}", get32(b, 0)));
            }
            0xc008561b => {
                put32(b, 4, 0);
            }
            REQBUFS => {
                d.trace.push(format!("{role}:req:{}", get32(b, 0)));
            }
            QUERYBUF => {
                if get32(b, 4) == 9 {
                    assert_eq!(get32(b, 56), 1);
                    let p = unsafe { &mut *(get32(b, 52) as usize as *mut Plane) };
                    p.length = 3981312;
                    return Some(Ok(()));
                }
                put32(
                    b,
                    56,
                    if role == "statistics" {
                        13040
                    } else if role == "parameters" {
                        11145
                    } else if role == "image" {
                        4478976
                    } else {
                        3981312
                    },
                );
                put32(b, 52, 0);
            }
            0xc0405610 => {
                let export = unsafe { libc::dup(fd) };
                assert!(export >= 0);
                put32(b, 16, export as u32);
            }
            0x800456c0 | 0x80045724 => {
                put32(b, 0, 0);
            }
            0x4020565a => {
                assert_eq!(get32(b, 0), 4);
            }
            0x80805659 => {
                if d.sof_observed_frame == Some(d.raw_frames) {
                    return again();
                }
                d.sof_observed_frame = Some(d.raw_frames);
                b.fill(0);
                put32(b, 0, 4);
                put32(b, 8, d.raw_frames);
                put32(b, 80, 4);
                put32(b, 84, d.raw_frames * 1_000_000);
            }
            STREAMON => {
                d.trace.push(format!("{role}:on"));
                if role == "statistics" {
                    d.statistics_on = true;
                }
                if role == "tx" && d.statistics_required {
                    assert!(d.statistics_on);
                }
                if role == "parameters" {
                    d.parameter_on = true;
                }
                if role == "image" {
                    assert!(d.parameter_on);
                    assert!(d.trace.contains(&"rx:on".into()));
                }
            }
            STREAMOFF => {
                d.trace.push(format!("{role}:off"));
                if role == "parameters" {
                    d.parameter_on = false;
                } else if role == "statistics" {
                    d.statistics_on = false;
                } else {
                    assert!(d.parameter_on, "parameters closed too early");
                }
            }
            QUEUE => {
                d.trace.push(format!("{role}:queue"));
                if role == "parameters" {
                    d.parameter_pending.push_back(get32(b, 0));
                }
                if role == "rx" {
                    assert!(!d.raw_inflight);
                    d.raw_inflight = true;
                }
            }
            DEQUEUE => match role.as_str() {
                "parameters" => {
                    if d.parameter_would_block {
                        d.parameter_would_block = false;
                        return again();
                    }
                    let Some(index) = d.parameter_pending.pop_front() else {
                        return again();
                    };
                    put32(b, 0, index);
                    if d.parameter_error_flag {
                        put32(b, 12, 0x40);
                    }
                    put32(b, 8, 11145);
                    put32(b, 56, 11145);
                    d.trace.push("parameters:ready".into());
                }
                "tx" => {
                    if d.raw_inflight {
                        return again();
                    }
                    put32(b, 0, 0);
                    if d.multi_tx {
                        assert_eq!(get32(b, 4), 9);
                        let p = unsafe { &mut *(get32(b, 52) as usize as *mut Plane) };
                        p.used = 3981312;
                        p.length = 3981312;
                    } else {
                        put32(b, 8, 3981312);
                    }
                    put32(b, 20, 4);
                    put32(b, 24, 500);
                    put32(b, 44, d.raw_frames);
                }
                "rx" => {
                    if !d.triggered {
                        return again();
                    }
                    put32(b, 0, 0);
                    d.raw_frames += 1;
                    d.triggered = false;
                    d.raw_inflight = false;
                    d.trace.push("rx:complete".into());
                }
                "statistics" => {
                    if d.raw_frames <= d.statistics_frames {
                        return again();
                    }
                    d.statistics_frames += 1;
                    put32(b, 0, 1);
                    put32(b, 8, 13040);
                    put32(b, 56, 13040);
                    put32(b, 44, d.statistics_frames);
                    let bytes = unsafe {
                        std::slice::from_raw_parts_mut(d.statistics_mapping as *mut u8, 13040)
                    };
                    put32(bytes, 13024, (1 << 8) | (1 << 12));
                    put32(bytes, 13028, d.statistics_frames);
                    put32(bytes, 13032, 0);
                }
                "image" => {
                    if d.statistics_required && d.statistics_frames <= d.image_frames {
                        return again();
                    }
                    if d.raw_frames <= d.image_frames {
                        return again();
                    }
                    d.image_frames += 1;
                    put32(b, 0, 0);
                    put32(b, 8, 4478976);
                    put32(b, 44, d.image_frames);
                    put32(b, 20, 4);
                }
                _ => panic!("DQ {role}"),
            },
            shieldsigner_rkaiq::raw_readback::TRIGGER_IOCTL => {
                assert!(d.raw_inflight);
                assert!(d.parameter_on);
                d.triggered = true;
                d.trace.push("isp:trigger".into());
            }
            _ => panic!("unexpected startup ioctl {request:x} {role}"),
        }
        Some(Ok(()))
    }
    #[test]
    #[ignore = "requires ARM32 Linux and the explicitly mounted full IQ fixture"]
    fn runtime_gain_parameter_reuse() {
        let (sender, receiver) = std::sync::mpsc::sync_channel(1);
        let observer = Some(sender);
        emit_camera_ae_event(
            &observer,
            CameraAeEvent::Sof {
                frame: 1,
                timestamp_ns: 10,
            },
        )
        .unwrap();
        assert!(emit_camera_ae_event(
            &observer,
            CameraAeEvent::Statistics {
                bytes: vec![0; 13040]
            }
        )
        .is_err());
        assert!(matches!(
            receiver.try_recv().unwrap(),
            CameraAeEvent::Sof {
                frame: 1,
                timestamp_ns: 10
            }
        ));
        drop(receiver);
        assert!(emit_camera_ae_event(
            &observer,
            CameraAeEvent::Sof {
                frame: 2,
                timestamp_ns: 20
            }
        )
        .is_err());
        use shieldsigner_rkaiq::{
            ae_runtime, ae_session, calibration::RuntimeTiming, isp32, sensor_scheduler,
        };
        let iq: Value = serde_json::from_slice(
            &fs::read(std::env::var("SHIELDSIGNER_TEST_IQ").unwrap()).unwrap(),
        )
        .unwrap();
        let make_runtime = |gain: f32| {
            let session = ae_session::Session::from_profile(
                &iq,
                RuntimeTiming {
                    frame_length: 1360,
                    line_length_pixels: 2800,
                    pixel_clock_mhz: 114.24,
                },
                2304,
                1296,
            )
            .unwrap();
            let mut initial = session.state.publication.previous_final;
            initial[12..16].copy_from_slice(&gain.to_le_bytes());
            ae_runtime::Runtime::new(
                session,
                initial,
                sensor_scheduler::EffectPolicy {
                    shorten_enabled: false,
                    designated_frame: 0,
                    shorten_all: false,
                },
            )
            .unwrap()
        };
        let boosted = make_runtime(2.);
        let unity = make_runtime(1.);
        *DRIVER.lock().unwrap() = Some(Driver::default());
        let initial_parameters = shieldsigner_rkaiq::initial_parameters::assemble_with_ae(&iq)
            .unwrap()
            .0;
        let sensor = SensorDevice {
            file: open("/dev/null", true).unwrap(),
            queries: vec![],
            bus: None,
            writes: vec![],
        };
        let mut owner = CameraAeOwner::new(make_runtime(1.), sensor, 0, initial_parameters);
        let raw = |frame: u32, id: u32| {
            let mut bytes = vec![0u8; 13040];
            put32(&mut bytes, 0x32e0, (1 << 8) | (1 << 12));
            put32(&mut bytes, 0x32e4, frame);
            put32(&mut bytes, 0x32e8, id);
            bytes
        };
        assert!(owner
            .handle(CameraAeEvent::Statistics { bytes: raw(1, 0) })
            .unwrap()
            .is_empty());
        assert_eq!(owner.pending.len(), 1);
        assert!(owner.finish().is_err());
        let outputs = owner
            .handle(CameraAeEvent::Sof {
                frame: 1,
                timestamp_ns: 1_000_000,
            })
            .unwrap();
        assert_eq!(outputs.len(), 1);
        assert_eq!(outputs[0].frame, 1);
        assert!(owner.pending.is_empty());
        let previous = owner.last_statistics;
        assert!(owner
            .handle(CameraAeEvent::Statistics { bytes: raw(1, 0) })
            .is_err());
        assert_eq!(owner.last_statistics, previous);
        owner.add_parameters(2, initial_parameters).unwrap();
        assert!(owner.add_parameters(2, initial_parameters).is_err());
        assert!(owner
            .handle(CameraAeEvent::Statistics { bytes: raw(3, 2) })
            .unwrap()
            .is_empty());
        assert!(owner
            .handle(CameraAeEvent::Sof {
                frame: 2,
                timestamp_ns: 2_000_000
            })
            .unwrap()
            .is_empty());
        let outputs = owner
            .handle(CameraAeEvent::Sof {
                frame: 3,
                timestamp_ns: 3_000_000,
            })
            .unwrap();
        assert_eq!(outputs.len(), 1);
        assert_eq!(outputs[0].parameters, 2);
        for frame in 4..9 {
            owner
                .handle(CameraAeEvent::Sof {
                    frame,
                    timestamp_ns: frame as u64 * 1_000_000,
                })
                .unwrap();
        }
        assert_eq!(owner.processed, 2);
        owner.finish().unwrap();
        assert!(!owner.sensor.writes.is_empty());
        let writes = owner.sensor.writes.len();
        assert!(owner
            .handle(CameraAeEvent::Sof {
                frame: 7,
                timestamp_ns: 7_000_000
            })
            .is_err());
        assert_eq!(owner.sensor.writes.len(), writes);
        drop(owner);
        let mut backend = ParameterBackend {
            file: Some(open("/dev/zero", true).unwrap()),
            requested: 2,
            allocated: false,
            mappings: vec![],
            buffers: vec![],
            calls: vec![],
            last_error: None,
            last_errno: None,
            last_dequeue: None,
            cleanup_errors: vec![],
            dequeue_would_block: 0,
        };
        let mut queue = parameter::Queue::default();
        assert_eq!(queue.start(&mut backend, false), 0);
        let mut cache = [0u8; 32];
        for pair in cache.chunks_exact_mut(2) {
            pair.copy_from_slice(&256u16.to_le_bytes());
        }
        let original_cache = cache;
        let first = backend
            .enqueue_runtime_gain(&mut queue, &boosted, 0, &mut cache, None)
            .unwrap()
            .unwrap();
        assert_eq!(first.0, 0);
        assert!(first.1.exact_exposure);
        let bytes = unsafe {
            std::slice::from_raw_parts(
                backend.mappings[0].address.cast::<u8>(),
                isp32::PARAMETER_BYTES,
            )
        };
        assert_eq!(u64::from_le_bytes(bytes[..8].try_into().unwrap()), 0);
        assert_eq!(
            u64::from_le_bytes(bytes[16..24].try_into().unwrap()),
            (1 << 63) | 32
        );
        assert_eq!(
            u16::from_le_bytes(
                bytes[isp32::AWB_GAIN_OFFSET + 8..isp32::AWB_GAIN_OFFSET + 10]
                    .try_into()
                    .unwrap()
            ),
            512
        );
        assert_eq!(cache, original_cache);
        assert_eq!(
            backend
                .enqueue_runtime_gain(&mut queue, &boosted, 1, &mut cache, None)
                .unwrap()
                .unwrap()
                .0,
            1
        );
        assert!(backend
            .enqueue_runtime_gain(&mut queue, &boosted, 2, &mut cache, None)
            .is_err());
        let cache_before_failure = cache;
        assert!(backend
            .enqueue_runtime_gain(
                &mut queue,
                &unity,
                2,
                &mut cache,
                Some(isp32::WhiteBalanceGain {
                    red: 4.,
                    green_red: 1.,
                    green_blue: 1.,
                    blue: 2.,
                    position: isp32::ApplyPosition::Gain1
                })
            )
            .is_err());
        assert_eq!(cache, cache_before_failure);
        assert!(backend
            .enqueue_runtime_gain(&mut queue, &unity, 2, &mut cache, None)
            .unwrap()
            .is_none());
        assert_eq!(queue.queued_count, 2);
        DRIVER
            .lock()
            .unwrap()
            .as_mut()
            .unwrap()
            .parameter_would_block = true;
        let before_buffers = backend.buffers.clone();
        assert!(backend.try_complete(&mut queue).unwrap().is_none());
        assert_eq!(backend.buffers, before_buffers);
        assert_eq!(queue.queued_count, 2);
        let completed = backend.try_complete(&mut queue).unwrap().unwrap();
        assert_eq!(completed["bufferIndex"], 0);
        assert_eq!(queue.queued_count, 1);
        assert!(!backend.buffers[0].queued);
        let wb = isp32::WhiteBalanceGain {
            red: 2.,
            green_red: 1.,
            green_blue: 1.,
            blue: 3.,
            position: isp32::ApplyPosition::Gain1,
        };
        assert_eq!(
            backend
                .enqueue_runtime_gain(&mut queue, &unity, 3, &mut cache, Some(wb))
                .unwrap()
                .unwrap()
                .0,
            0
        );
        let bytes = unsafe {
            std::slice::from_raw_parts(
                backend.mappings[0].address.cast::<u8>(),
                isp32::PARAMETER_BYTES,
            )
        };
        assert_eq!(get32(bytes, 24), 3);
        assert_eq!(
            u16::from_le_bytes(
                bytes[isp32::AWB_GAIN_OFFSET + 8..isp32::AWB_GAIN_OFFSET + 10]
                    .try_into()
                    .unwrap()
            ),
            256
        );
        assert_eq!(
            u16::from_le_bytes(
                bytes[isp32::AWB_GAIN_OFFSET + 6..isp32::AWB_GAIN_OFFSET + 8]
                    .try_into()
                    .unwrap()
            ),
            512
        );
        assert_eq!(queue.queued_count, 2);
        assert_eq!(
            backend.try_complete(&mut queue).unwrap().unwrap()["bufferIndex"],
            1
        );
        assert_eq!(queue.queued_count, 1);
        DRIVER
            .lock()
            .unwrap()
            .as_mut()
            .unwrap()
            .parameter_error_flag = true;
        assert!(backend.try_complete(&mut queue).is_err());
        assert!(
            backend.buffers[0].queued,
            "invalid completion must not recycle slot"
        );
        let allocated = backend.allocated;
        queue.stop(&mut backend, allocated);
        assert!(backend.cleanup_errors.is_empty());
        DRIVER
            .lock()
            .unwrap()
            .as_mut()
            .unwrap()
            .parameter_error_flag = false;
        queue = parameter::Queue::default();
        assert_eq!(queue.start(&mut backend, false), 0);
        let sensor = SensorDevice {
            file: open("/dev/null", true).unwrap(),
            queries: vec![],
            bus: None,
            writes: vec![],
        };
        let mut owner = CameraAeOwner::new(make_runtime(2.), sensor, 0, initial_parameters);
        let index = owner
            .submit_gain(&mut backend, &mut queue, 1, Some(wb))
            .unwrap()
            .unwrap();
        assert_eq!(owner.parameters.len(), 2);
        assert_eq!(owner.parameters[1].0, 1);
        let snapshot = &owner.parameters[1].1;
        assert_eq!(
            &snapshot[28..isp32::AWB_GAIN_OFFSET],
            &initial_parameters[28..isp32::AWB_GAIN_OFFSET]
        );
        assert_eq!(
            u16::from_le_bytes(
                snapshot[isp32::AWB_GAIN_OFFSET + 8..isp32::AWB_GAIN_OFFSET + 10]
                    .try_into()
                    .unwrap()
            ),
            256
        );
        let bytes = unsafe {
            std::slice::from_raw_parts(
                backend.mappings[index].address.cast::<u8>(),
                isp32::PARAMETER_BYTES,
            )
        };
        assert_eq!(
            u16::from_le_bytes(
                bytes[isp32::AWB_GAIN_OFFSET + 8..isp32::AWB_GAIN_OFFSET + 10]
                    .try_into()
                    .unwrap()
            ),
            512
        );
        owner
            .handle(CameraAeEvent::Sof {
                frame: 1,
                timestamp_ns: 1_000_000,
            })
            .unwrap();
        let outputs = owner
            .handle(CameraAeEvent::Statistics { bytes: raw(1, 1) })
            .unwrap();
        assert_eq!(outputs.len(), 1);
        assert_eq!(outputs[0].parameters, 1);
        DRIVER
            .lock()
            .unwrap()
            .as_mut()
            .unwrap()
            .parameter_would_block = true;
        owner
            .submit_gain(&mut backend, &mut queue, 2, Some(wb))
            .unwrap()
            .unwrap();
        let snapshots = owner.parameters.clone();
        DRIVER
            .lock()
            .unwrap()
            .as_mut()
            .unwrap()
            .parameter_would_block = true;
        assert!(owner
            .submit_gain(&mut backend, &mut queue, 3, Some(wb))
            .is_err());
        assert_eq!(owner.parameters, snapshots);
        assert!(owner
            .submit_gain(&mut backend, &mut queue, 2, Some(wb))
            .is_err());
        assert_eq!(owner.parameters, snapshots);
        owner
            .submit_gain(&mut backend, &mut queue, 3, Some(wb))
            .unwrap()
            .unwrap();
        assert_eq!(owner.parameters.len(), 4);
        assert_eq!(owner.parameters[3].0, 3);
        let allocated = backend.allocated;
        queue.stop(&mut backend, allocated);
        assert!(backend.cleanup_errors.is_empty());
        let driver = DRIVER.lock().unwrap().take().unwrap();
        assert_eq!(
            driver
                .trace
                .iter()
                .filter(|s| s.as_str() == "parameters:queue")
                .count(),
            6
        );
        println!();
        println!(
            "{}",
            json!({"event":"runtime-gain-queue-verified","hardwareVerified":false,"queued":6,"snapshotSubmissions":3,"poolExhaustionChecked":true,"unityNoopChecked":true})
        );
    }
    #[test]
    #[ignore = "requires ARM32 Linux and the explicitly mounted full IQ fixture"]
    fn full_first_frame_userspace_sequence() {
        let iq = std::env::var("SHIELDSIGNER_TEST_IQ").expect("set full IQ fixture path");
        let folder = format!("/tmp/shieldsigner-startup-test-{}", std::process::id());
        fs::create_dir(&folder).unwrap();
        let plan = format!("{folder}/plan.json");
        let output = format!("{folder}/frame.raw");
        fs::write(&plan,serde_json::to_vec(&json!({"sensor":"/dev/null","isp":"/dev/urandom","route":"cif","raw_tx":["/dev/full"],"raw_rx":["/dev/random"],"bridges":[],"links":[]})).unwrap()).unwrap();
        let statistics = std::env::var("SHIELDSIGNER_TEST_STATS").is_ok();
        let multi_tx = std::env::var("SHIELDSIGNER_TEST_MPLANE_TX").is_ok();
        *DRIVER.lock().unwrap() = Some(Driver {
            statistics_required: statistics,
            multi_tx,
            ..Driver::default()
        });
        let mut args = vec![
            plan,
            iq,
            "/dev/zero".into(),
            "/dev/ptmx".into(),
            output.clone(),
        ];
        if statistics {
            args.push("/dev/tty".into());
        }
        let (event_tx, event_rx) = std::sync::mpsc::sync_channel(64);
        let outcome = first_frame_sc3336_observed(&args, Some(event_tx));
        let events = event_rx.try_iter().collect::<Vec<_>>();
        let mut sof_events = 0;
        let mut statistics_events = 0;
        for event in events {
            match event {
                CameraAeEvent::Sof {
                    frame,
                    timestamp_ns,
                } => {
                    assert!(frame < 64);
                    assert_eq!(timestamp_ns, 4_000_000_000 + frame as u64 * 1_000_000);
                    sof_events += 1;
                }
                CameraAeEvent::Statistics { bytes } => {
                    let stats = shieldsigner_rkaiq::statistics::Statistics::parse(&bytes).unwrap();
                    assert_eq!(stats.parameters_id(), 0);
                    assert!(stats.frame_id() > 0);
                    statistics_events += 1;
                }
            }
        }
        assert!(sof_events > 0);
        let driver = DRIVER.lock().unwrap().take().unwrap();
        outcome.unwrap();
        assert_eq!(statistics_events, driver.statistics_frames);
        assert_eq!(driver.image_frames, 3);
        assert!(driver.raw_frames >= 3);
        assert_eq!(fs::metadata(&output).unwrap().len(), 4478976);
        assert_eq!(
            fs::metadata(format!("{output}.initial.bin")).unwrap().len(),
            11145
        );
        let position = |s: &str| driver.trace.iter().position(|v| v == s).unwrap();
        assert!(position("parameters:ready") < position("tx:on"));
        assert!(position("image:off") < position("rx:off"));
        assert!(position("rx:off") < position("parameters:off"));
        assert!(position("sensor:write:9e0901") < position("parameters:on"));
        if statistics {
            assert!(position("statistics:on") < position("tx:on"));
            assert!(position("parameters:off") < position("statistics:off"));
            assert_eq!(
                fs::metadata(format!("{output}.stats.raw")).unwrap().len(),
                13040
            );
            assert!(driver.statistics_frames >= 3);
            let report: Value =
                serde_json::from_slice(&fs::read(format!("{output}.stats.raw.json")).unwrap())
                    .unwrap();
            assert_eq!(
                report["framesReceived"].as_u64(),
                Some(driver.statistics_frames as u64)
            );
            assert_eq!(
                report["lastFrame"]["frameId"].as_u64(),
                Some(driver.statistics_frames as u64)
            );
            assert_eq!(
                report["lastFrame"]["measurements"].as_u64(),
                Some((1 << 8) | (1 << 12))
            );
            assert_eq!(report["automaticExposure"], false);
            assert_eq!(report["initialTargetLuma"], 45.0);
            assert_eq!(report["lastFrame"]["aeLinear"]["weightedMeanQ8"], 0);
            assert_eq!(
                report["lastFrame"]["aeLinear"]["correctedHistogramCount"],
                0
            );
            assert_eq!(
                report["lastFrame"]["aeLinear"]["initialSnapshotAssociationVerified"],
                false
            );
            assert_eq!(report["frameExposureAssociationVerified"], false);
        }
        println!(
            "{}",
            json!({"event":"simulated-startup-verified","sofEvents":sof_events,"statisticsEvents":statistics_events,"statisticsEnabled":statistics,"multiPlaneTx":multi_tx,"statisticsFrames":driver.statistics_frames,"imageFrames":driver.image_frames,"rawFrames":driver.raw_frames,"savedBytes":4478976,"hardwareVerified":false,"imageContent":"anonymous zero-filled simulated memory"})
        );
        fs::remove_dir_all(folder).unwrap();
    }
}

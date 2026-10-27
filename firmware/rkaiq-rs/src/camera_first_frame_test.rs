// Full userspace startup exercise: simulated ioctl/poll/MMAP boundaries only.
mod first_frame_driver {
    use super::*;
    use std::{collections::HashMap, sync::Mutex};
    #[derive(Default)]
    struct Driver {
        roles: HashMap<RawFd, String>,
        trace: Vec<String>,
        formats: HashMap<String, Vec<u8>>,
        parameter_on: bool,
        raw_inflight: bool,
        triggered: bool,
        raw_frames: u32,
        image_frames: u32,
        statistics_frames: u32,
        statistics_required: bool,
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
                    "tx" | "image" => 0x04000001,
                    "rx" => 0x04000002,
                    "parameters" => 0x0c000000,
                    "statistics" => 0x04800000,
                    _ => panic!("caps {role}"),
                };
                put32(b, 84, cap);
            }
            GETFMT => {
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
                    put32(b, 20, if role == "image" { 2304 } else { 4608 });
                    put32(b, 24, if role == "image" { 4478976 } else { 5971968 });
                }
            }
            SETFMT => {
                put32(b, 20, if role == "image" { 2304 } else { 4608 });
                put32(b, 24, if role == "image" { 4478976 } else { 5971968 });
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
                        5971968
                    },
                );
                put32(b, 52, 0);
            }
            0xc0405610 => {
                let export = unsafe { libc::dup(fd) };
                assert!(export >= 0);
                put32(b, 16, export as u32);
            }
            0x4020565a => {
                assert_eq!(get32(b, 0), 4);
            }
            0x80805659 => return again(),
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
                if role == "rx" {
                    assert!(!d.raw_inflight);
                    d.raw_inflight = true;
                }
            }
            DEQUEUE => match role.as_str() {
                "parameters" => {
                    put32(b, 0, 0);
                    put32(b, 8, 11145);
                    put32(b, 56, 11145);
                    d.trace.push("parameters:ready".into());
                }
                "tx" => {
                    if d.raw_inflight {
                        return again();
                    }
                    put32(b, 0, 0);
                    put32(b, 8, 5971968);
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
    fn full_first_frame_userspace_sequence() {
        let iq = std::env::var("SHIELDSIGNER_TEST_IQ").expect("set full IQ fixture path");
        let folder = format!("/tmp/shieldsigner-startup-test-{}", std::process::id());
        fs::create_dir(&folder).unwrap();
        let plan = format!("{folder}/plan.json");
        let output = format!("{folder}/frame.raw");
        fs::write(&plan,serde_json::to_vec(&json!({"sensor":"/dev/null","isp":"/dev/urandom","route":"cif","raw_tx":["/dev/full"],"raw_rx":["/dev/random"],"bridges":[],"links":[]})).unwrap()).unwrap();
        let statistics = std::env::var("SHIELDSIGNER_TEST_STATS").is_ok();
        *DRIVER.lock().unwrap() = Some(Driver {
            statistics_required: statistics,
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
        let outcome = first_frame_sc3336(&args);
        let driver = DRIVER.lock().unwrap().take().unwrap();
        outcome.unwrap();
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
            assert_eq!(report["frameExposureAssociationVerified"], false);
        }
        println!(
            "{}",
            json!({"event":"simulated-startup-verified","statisticsEnabled":statistics,"statisticsFrames":driver.statistics_frames,"imageFrames":driver.image_frames,"rawFrames":driver.raw_frames,"savedBytes":4478976,"hardwareVerified":false,"imageContent":"anonymous zero-filled simulated memory"})
        );
        fs::remove_dir_all(folder).unwrap();
    }
}

//! Exercise the same Unix transport source on the development host, without V4L2.
#![cfg(unix)]
#![allow(dead_code)]
use std::{
    fs,
    io::{self, Read, Write},
    time::Duration,
};
const MPLANE: u32 = 9;
struct Format {
    kind: u32,
    data: Data,
}
union Data {
    raw: [u8; 200],
}
fn get32(raw: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(raw[offset..offset + 4].try_into().unwrap())
}
fn error(value: &str) -> io::Error {
    io::Error::new(io::ErrorKind::Other, value)
}
include!("../src/camera_stream.rs");
#[test]
fn wire_reconnect_cleanup_and_endpoint_ownership() {
    use std::os::unix::net::UnixStream;
    let path = std::env::temp_dir().join(format!("ss-camera-test-{}.sock", std::process::id()));
    std::env::set_var("SHIELDSIGNER_CAMERA_SOCKET", &path);
    let mut raw = [0; 200];
    for (offset, value) in [
        (0, 2u32),
        (4, 2),
        (8, u32::from_le_bytes(*b"NV12")),
        (16, 2),
    ] {
        raw[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
    }
    let fmt = Format {
        kind: 1,
        data: Data { raw },
    };
    let owner = CameraFrameStream::from_environment(&fmt).unwrap().unwrap();
    assert!(CameraFrameStream::from_environment(&fmt).is_err());
    assert!(path.exists());
    let mut client = UnixStream::connect(&path).unwrap();
    client
        .set_read_timeout(Some(Duration::from_secs(2)))
        .unwrap();
    owner.publish(17, &[16, 235, 81, 145, 128, 128]);
    let mut bytes = [0; 36];
    client.read_exact(&mut bytes).unwrap();
    assert_eq!(&bytes[..8], b"SSRGB001");
    assert_eq!(get32(&bytes, 16), 17);
    assert_eq!(get32(&bytes, 20), 12);
    assert_eq!(
        &bytes[24..],
        &[0, 0, 0, 255, 255, 255, 76, 76, 76, 150, 150, 150]
    );
    drop(client);
    owner.publish(18, &[16; 6]);
    std::thread::sleep(Duration::from_millis(50));
    let mut client = UnixStream::connect(&path).unwrap();
    client
        .set_read_timeout(Some(Duration::from_secs(2)))
        .unwrap();
    owner.publish(19, &[16; 6]);
    client.read_exact(&mut bytes).unwrap();
    assert_eq!(get32(&bytes, 16), 19);
    drop(owner);
    assert!(!path.exists());
    std::env::remove_var("SHIELDSIGNER_CAMERA_SOCKET");
}

#[test]
fn stalled_reader_can_cancel_without_waiting_for_socket_timeout() {
    use std::{
        os::unix::net::UnixStream,
        sync::{
            atomic::{AtomicBool, Ordering},
            Arc,
        },
        time::Instant,
    };
    let (mut writer, _reader) = UnixStream::pair().unwrap();
    writer.set_nonblocking(true).unwrap();
    let stop = Arc::new(AtomicBool::new(false));
    let worker_stop = stop.clone();
    let worker = std::thread::spawn(move || {
        camera_stream_write(&mut writer, b"header", &vec![0; 2_000_000], &worker_stop)
    });
    std::thread::sleep(Duration::from_millis(50));
    let before = Instant::now();
    stop.store(true, Ordering::Relaxed);
    assert_eq!(
        worker.join().unwrap().unwrap_err().kind(),
        io::ErrorKind::Interrupted
    );
    assert!(before.elapsed() < Duration::from_millis(250));
}

#[test]
fn colorimetry_abi_defaults_and_profile_contract() {
    for kind in [1, MPLANE] {
        let mut raw = [0; 200];
        if kind == MPLANE {
            raw[182] = 1;
            raw[183] = 1;
            raw[184] = 2;
            raw[16..20].copy_from_slice(&8u32.to_le_bytes());
        } else {
            for (offset, value) in [(24, 8u32), (36, 1), (40, 1), (44, 2)] {
                raw[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
            }
        }
        assert_eq!(
            camera_colorimetry(&Format {
                kind,
                data: Data { raw }
            }),
            (8, 1, 1, 2)
        );
    }
    assert!(camera_bt601_range(0, 0, 1).unwrap());
    assert!(!camera_bt601_range(0, 0, 2).unwrap());
    assert!(!camera_bt601_range(0, 0, 0).unwrap());
    assert!(camera_bt601_range(7, 0, 0).unwrap());
    for (space, encoding, range) in [(3, 0, 1), (10, 0, 1), (0, 2, 1), (0, 0, 3)] {
        assert!(camera_bt601_range(space, encoding, range).is_err());
    }
    let mut params = [0; shieldsigner_rkaiq::isp32::PARAMETER_BYTES];
    params[8..16].copy_from_slice(&((1u64 << 43) | (1u64 << 44)).to_le_bytes());
    for (i, value) in [38i32, 75, 15, -22, -42, 64, 64, -54, -10]
        .iter()
        .enumerate()
    {
        params[0x2b59 + i * 4..0x2b5d + i * 4].copy_from_slice(&value.to_le_bytes());
    }
    assert!(camera_bt601_parameters(&params));
    params[0x2b7d] = 1;
    assert!(camera_bt601_parameters(&params));
    params[0x2b7e] = 1;
    assert!(!camera_bt601_parameters(&params));
    params[0x2b7e] = 0;
    params[0x2b59] = 37;
    assert!(!camera_bt601_parameters(&params));
}
#[test]
fn full_range_matches_independent_float_reference() {
    let clamp = |v: f64| v.round().clamp(0., 255.) as i32;
    let mut cases = 0;
    for full in [false, true] {
        for y in (0..=255u8).step_by(5) {
            for u in (0..=255u8).step_by(7) {
                for v in (0..=255u8).step_by(11) {
                    let result = camera_nv12_rgb(&[y, y, y, y, u, v], 2, 2, 2, full).unwrap();
                    let d = f64::from(u) - 128.;
                    let e = f64::from(v) - 128.;
                    let (c, r, g1, g2, b) = if full {
                        (f64::from(y), 1.402, 0.344136, 0.714136, 1.772)
                    } else {
                        (
                            (f64::from(y) - 16.) * 255. / 219.,
                            1.596027,
                            0.391762,
                            0.812968,
                            2.017232,
                        )
                    };
                    for (actual, expected) in result[..3].iter().zip([
                        clamp(c + r * e),
                        clamp(c - g1 * d - g2 * e),
                        clamp(c + b * d),
                    ]) {
                        assert!((i32::from(*actual) - expected).abs() <= 1);
                    }
                    cases += 1;
                }
            }
        }
    }
    assert_eq!(cases, 92352);
    // Full-range neutral tones retain their level; limited-range expands 16..235.
    assert_eq!(
        camera_nv12_rgb(&[16, 235, 81, 145, 128, 128], 2, 2, 2, true).unwrap(),
        [16, 16, 16, 235, 235, 235, 81, 81, 81, 145, 145, 145]
    );
}

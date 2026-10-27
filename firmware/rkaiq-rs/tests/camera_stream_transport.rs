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

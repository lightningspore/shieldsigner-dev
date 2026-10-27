static CAMERA_CONTINUOUS: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
static CAMERA_STREAM_STOP: std::sync::atomic::AtomicBool =
    std::sync::atomic::AtomicBool::new(false);
#[cfg(target_os = "linux")]
struct CameraStreamSignals {
    previous: Vec<(i32, libc::sigaction)>,
}
#[cfg(target_os = "linux")]
impl CameraStreamSignals {
    fn install() -> io::Result<Self> {
        extern "C" fn stop(_: i32) {
            CAMERA_STREAM_STOP.store(true, std::sync::atomic::Ordering::Relaxed);
        }
        let mut guard = Self {
            previous: Vec::new(),
        };
        CAMERA_STREAM_STOP.store(false, std::sync::atomic::Ordering::Relaxed);
        for signal in [libc::SIGINT, libc::SIGTERM] {
            let mut action: libc::sigaction = unsafe { std::mem::zeroed() };
            let mut previous = action;
            action.sa_sigaction = stop as *const () as usize;
            unsafe {
                libc::sigemptyset(&mut action.sa_mask);
            }
            if unsafe { libc::sigaction(signal, &action, &mut previous) } != 0 {
                return Err(io::Error::last_os_error());
            }
            guard.previous.push((signal, previous));
        }
        CAMERA_CONTINUOUS.store(true, std::sync::atomic::Ordering::Relaxed);
        Ok(guard)
    }
}
#[cfg(target_os = "linux")]
impl Drop for CameraStreamSignals {
    fn drop(&mut self) {
        CAMERA_CONTINUOUS.store(false, std::sync::atomic::Ordering::Relaxed);
        for (signal, previous) in &self.previous {
            unsafe {
                libc::sigaction(*signal, previous, std::ptr::null_mut());
            }
        }
    }
}
// Optional application transport; capture/3A never waits for a consumer.
// Included inside camera-probe's Linux module.
struct CameraFrameStream {
    sender: Option<std::sync::mpsc::SyncSender<(u32, Vec<u8>)>>,
    worker: Option<std::thread::JoinHandle<()>>,
    path: std::path::PathBuf,
    stop: std::sync::Arc<std::sync::atomic::AtomicBool>,
}
impl CameraFrameStream {
    fn from_environment(fmt: &Format) -> io::Result<Option<Self>> {
        use std::os::unix::{fs::PermissionsExt, net::UnixListener};
        let Some(path) = std::env::var_os("SHIELDSIGNER_CAMERA_SOCKET") else {
            return Ok(None);
        };
        let path = std::path::PathBuf::from(path);
        let raw = unsafe { &fmt.data.raw };
        let (width, height) = (get32(raw, 0) as usize, get32(raw, 4) as usize);
        let stride = get32(raw, if fmt.kind == MPLANE { 24 } else { 16 }) as usize;
        if get32(raw, 8) != u32::from_le_bytes(*b"NV12")
            || width == 0
            || height == 0
            || width % 2 != 0
            || height % 2 != 0
            || stride < width
            || width > 4096
            || height > 4096
            || (fmt.kind == MPLANE && raw[180] != 1)
        {
            return Err(error(
                "Application stream requires contiguous even-sized NV12, at most 4096x4096",
            ));
        }
        // Never unlink an existing endpoint: another camera owner may be using it.
        let listener = UnixListener::bind(&path)?;
        let setup = (|| {
            fs::set_permissions(&path, fs::Permissions::from_mode(0o600))?;
            listener.set_nonblocking(true)
        })();
        if let Err(e) = setup {
            let _ = fs::remove_file(&path);
            return Err(e);
        }
        let (sender, receiver) = std::sync::mpsc::sync_channel::<(u32, Vec<u8>)>(1);
        let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
        let worker_stop = stop.clone();
        let worker = std::thread::spawn(move || {
            let mut client = None;
            while let Ok((sequence, nv12)) = receiver.recv() {
                if worker_stop.load(std::sync::atomic::Ordering::Relaxed) {
                    break;
                }
                if client.is_none() {
                    if let Ok((stream, _)) = listener.accept() {
                        if stream.set_nonblocking(true).is_ok() {
                            client = Some(stream);
                        }
                    }
                }
                if let Some(stream) = &mut client {
                    let Some(rgb) = camera_nv12_rgb(&nv12, width, height, stride) else {
                        continue;
                    };
                    let mut header = Vec::from(*b"SSRGB001");
                    for value in [width as u32, height as u32, sequence, rgb.len() as u32] {
                        header.extend_from_slice(&value.to_le_bytes());
                    }
                    // A deadline/partial frame disconnects; the next client starts at a fresh header.
                    if let Err(e) = camera_stream_write(stream, &header, &rgb, &worker_stop) {
                        eprintln!(
                            "camera application stream disconnected at frame {sequence}: {e}"
                        );
                        client = None;
                    }
                }
            }
        });
        Ok(Some(Self {
            sender: Some(sender),
            worker: Some(worker),
            path,
            stop,
        }))
    }
    fn publish(&self, sequence: u32, bytes: &[u8]) {
        if let Some(sender) = &self.sender {
            let _ = sender.try_send((sequence, bytes.to_vec()));
        }
    }
}
impl Drop for CameraFrameStream {
    fn drop(&mut self) {
        self.stop.store(true, std::sync::atomic::Ordering::Relaxed);
        self.sender.take();
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
        let _ = fs::remove_file(&self.path);
    }
}
fn camera_nv12_rgb(bytes: &[u8], width: usize, height: usize, stride: usize) -> Option<Vec<u8>> {
    if width == 0
        || height == 0
        || width % 2 != 0
        || height % 2 != 0
        || stride < width
        || bytes.len() < stride.checked_mul(height)?.checked_mul(3)?.checked_div(2)?
    {
        return None;
    }
    let mut rgb = Vec::with_capacity(width.checked_mul(height)?.checked_mul(3)?);
    for y in 0..height {
        for x in 0..width {
            let c = i32::from(bytes[y * stride + x]) - 16;
            let uv = stride * height + y / 2 * stride + (x & !1);
            let d = i32::from(bytes[uv]) - 128;
            let e = i32::from(bytes[uv + 1]) - 128;
            // Limited-range BT.601, matching the existing app's NV12 converter.
            for v in [
                298 * c + 409 * e,
                298 * c - 100 * d - 208 * e,
                298 * c + 516 * d,
            ] {
                rgb.push(((v + 128) >> 8).clamp(0, 255) as u8);
            }
        }
    }
    Some(rgb)
}
#[cfg(test)]
mod camera_stream_tests {
    use super::*;
    #[test]
    fn nv12_stride_range_and_rejection() {
        assert_eq!(
            camera_nv12_rgb(&[16, 235, 0, 0, 81, 145, 0, 0, 128, 128, 0, 0], 2, 2, 4).unwrap(),
            [0, 0, 0, 255, 255, 255, 76, 76, 76, 150, 150, 150]
        );
        assert!(camera_nv12_rgb(&[0; 5], 2, 2, 2).is_none());
        assert!(camera_nv12_rgb(&[0; 12], 3, 2, 4).is_none());
        assert!(camera_nv12_rgb(&[0; 12], 2, 2, 1).is_none());
    }
}

fn camera_stream_write(
    stream: &mut std::os::unix::net::UnixStream,
    header: &[u8],
    rgb: &[u8],
    stop: &std::sync::atomic::AtomicBool,
) -> io::Result<()> {
    let deadline = std::time::Instant::now() + Duration::from_secs(2);
    for mut bytes in [header, rgb] {
        while !bytes.is_empty() {
            if stop.load(std::sync::atomic::Ordering::Relaxed) {
                return Err(io::Error::from(io::ErrorKind::Interrupted));
            }
            if std::time::Instant::now() >= deadline {
                return Err(io::Error::from(io::ErrorKind::TimedOut));
            }
            match stream.write(bytes) {
                Ok(0) => return Err(io::Error::from(io::ErrorKind::WriteZero)),
                Ok(n) => bytes = &bytes[n..],
                Err(e) if e.kind() == io::ErrorKind::WouldBlock => {
                    std::thread::sleep(Duration::from_millis(2))
                }
                Err(e) if e.kind() == io::ErrorKind::Interrupted => {}
                Err(e) => return Err(e),
            }
        }
    }
    Ok(())
}

fn camera_stream_cancelled() -> bool {
    CAMERA_CONTINUOUS.load(std::sync::atomic::Ordering::Relaxed)
        && CAMERA_STREAM_STOP.load(std::sync::atomic::Ordering::Relaxed)
}

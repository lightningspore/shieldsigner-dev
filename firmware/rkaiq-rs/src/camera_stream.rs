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
        let (colorspace, encoding, quantization, _) = camera_colorimetry(fmt);
        let full_range = camera_bt601_range(colorspace, encoding, quantization)?;
        let nv12_transport = match std::env::var("SHIELDSIGNER_CAMERA_STREAM_FORMAT") {
            Err(std::env::VarError::NotPresent) => false,
            Ok(value) if value == "rgb" => false,
            Ok(value) if value == "nv12" => true,
            _ => return Err(error("Camera stream format must be rgb or nv12")),
        };
        if nv12_transport && !full_range {
            return Err(error("NV12 desktop transport requires full-range BT.601"));
        }
        println!(
            "{}",
            serde_json::json!({"event":"application-rgb-conversion","matrix":"BT.601",
            "range":if full_range {"full"} else {"limited"},"driverColorspace":colorspace,
            "driverYcbcrEncoding":encoding,"driverQuantization":quantization})
        );
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
                    let payload = if nv12_transport {
                        camera_pack_nv12(&nv12, width, height, stride)
                    } else {
                        camera_nv12_rgb(&nv12, width, height, stride, full_range)
                    };
                    let Some(payload) = payload else { continue; };
                    let mut header = Vec::from(if nv12_transport { *b"SSNV12F1" } else { *b"SSRGB001" });
                    for value in [width as u32, height as u32, sequence, payload.len() as u32] {
                        header.extend_from_slice(&value.to_le_bytes());
                    }
                    // A deadline/partial frame disconnects; the next client starts at a fresh header.
                    if let Err(e) = camera_stream_write(stream, &header, &payload, &worker_stop) {
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
fn camera_colorimetry(fmt: &Format) -> (u32, u32, u32, u32) {
    let raw = unsafe { &fmt.data.raw };
    if fmt.kind == MPLANE {
        (
            get32(raw, 16),
            raw[182] as u32,
            raw[183] as u32,
            raw[184] as u32,
        )
    } else {
        (
            get32(raw, 24),
            get32(raw, 36),
            get32(raw, 40),
            get32(raw, 44),
        )
    }
}
fn camera_bt601_range(colorspace: u32, encoding: u32, quantization: u32) -> io::Result<bool> {
    // Pinned V4L2_MAP_YCBCR_ENC_DEFAULT: 709/DCI-P3, 2020 and 240M differ.
    if (encoding == 0 && matches!(colorspace, 2 | 3 | 10 | 12)) || encoding > 1 {
        return Err(error("Application stream supports BT.601 YCbCr only"));
    }
    match quantization {
        0 => Ok(colorspace == 7), // V4L2 YUV default: limited, except JPEG.
        1 => Ok(true),
        2 => Ok(false),
        _ => Err(error("Unsupported application stream quantization")),
    }
}
// Preserve raw NV12 samples while omitting driver row padding. This optional
// desktop protocol leaves the default RGB application protocol unchanged.
fn camera_pack_nv12(bytes: &[u8], width: usize, height: usize, stride: usize) -> Option<Vec<u8>> {
    if width == 0 || height == 0 || width % 2 != 0 || height % 2 != 0 || stride < width {
        return None;
    }
    let rows = height.checked_add(height / 2)?;
    if bytes.len() < stride.checked_mul(rows)? { return None; }
    let mut packed = Vec::with_capacity(width.checked_mul(rows)?);
    for row in bytes.chunks_exact(stride).take(rows) {
        packed.extend_from_slice(&row[..width]);
    }
    Some(packed)
}

fn camera_nv12_rgb(
    bytes: &[u8],
    width: usize,
    height: usize,
    stride: usize,
    full_range: bool,
) -> Option<Vec<u8>> {
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
    let (y_offset, y_scale, r_cr, g_cb, g_cr, b_cb) = if full_range {
        (0, 256, 359, 88, 183, 454)
    } else {
        (16, 298, 409, 100, 208, 516)
    };
    for y in 0..height {
        for x in 0..width {
            let c = i32::from(bytes[y * stride + x]) - y_offset;
            let uv = stride * height + y / 2 * stride + (x & !1);
            let d = i32::from(bytes[uv]) - 128;
            let e = i32::from(bytes[uv + 1]) - 128;
            // BT.601 Q8 inverse, with range selected from driver metadata.
            for v in [
                y_scale * c + r_cr * e,
                y_scale * c - g_cb * d - g_cr * e,
                y_scale * c + b_cb * d,
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
    fn nv12_transport_removes_only_row_padding() {
        let raw = [10,20,99,99,30,40,99,99,50,60,99,99];
        assert_eq!(camera_pack_nv12(&raw,2,2,4).unwrap(), [10,20,30,40,50,60]);
        assert!(camera_pack_nv12(&raw[..10],2,2,4).is_none());
        assert!(camera_pack_nv12(&raw,3,2,4).is_none());
    }
    #[test]
    fn nv12_stride_range_and_rejection() {
        assert_eq!(
            camera_nv12_rgb(
                &[16, 235, 0, 0, 81, 145, 0, 0, 128, 128, 0, 0],
                2,
                2,
                4,
                false
            )
            .unwrap(),
            [0, 0, 0, 255, 255, 255, 76, 76, 76, 150, 150, 150]
        );
        assert!(camera_nv12_rgb(&[0; 5], 2, 2, 2, false).is_none());
        assert!(camera_nv12_rgb(&[0; 12], 3, 2, 4, false).is_none());
        assert!(camera_nv12_rgb(&[0; 12], 2, 2, 1, false).is_none());
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

fn camera_bt601_parameters(params: &[u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES]) -> bool {
    let enabled = u64::from_le_bytes(params[8..16].try_into().unwrap());
    let required = (1u64 << 43) | (1u64 << 44);
    if enabled & required != required
        || params[0x2b55..0x2b59] != [0; 4]
        || params[0x2b7d] > 1
        || params[0x2b7e] != 0
    {
        return false;
    }
    [38, 75, 15, -22, -42, 64, 64, -54, -10]
        .iter()
        .enumerate()
        .all(|(i, expected)| {
            let offset = 0x2b59 + i * 4;
            i32::from_le_bytes(params[offset..offset + 4].try_into().unwrap()) == *expected
        })
}

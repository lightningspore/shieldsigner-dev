// Included in the Linux camera diagnostic. Linear, one-image-plane raw DMA-BUF
// transfer only. Formats/media links must already be configured explicitly.
mod raw_bridge {
    #[cfg(test)]
    pub(super) fn mock_ioctl<T>(
        fd: super::RawFd,
        request: u32,
        value: &mut T,
    ) -> Option<super::io::Result<()>> {
        super::raw_bridge_driver_test::mock(fd, request, value)
    }
    use super::*;
    use std::os::fd::{FromRawFd, OwnedFd};
    use std::sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    };
    #[repr(C)]
    struct Export {
        kind: u32,
        index: u32,
        plane: u32,
        flags: u32,
        fd: i32,
        reserved: [u32; 11],
    }
    struct Endpoint {
        file: File,
        kind: u32,
        memory: u32,
        allocated: bool,
        streaming: bool,
    }
    impl Endpoint {
        fn allocate(&mut self, count: u32) -> io::Result<u32> {
            let mut request = RequestBuffers {
                count,
                kind: self.kind,
                memory: self.memory,
                capabilities: 0,
                reserved: 0,
            };
            ioctl(self.file.as_raw_fd(), REQBUFS, &mut request)?;
            self.allocated = true;
            if request.count < 2 || request.count > 16 {
                return Err(error(format!("Raw buffer allocation outside requested bounds: type={} memory={} requested={} returned={}", self.kind, self.memory, count, request.count)));
            }
            Ok(request.count)
        }
        fn start(&mut self) -> io::Result<()> {
            ioctl(self.file.as_raw_fd(), STREAMON, &mut self.kind)?;
            self.streaming = true;
            Ok(())
        }
        fn stop(&mut self) -> io::Result<()> {
            if self.streaming {
                ioctl(self.file.as_raw_fd(), STREAMOFF, &mut self.kind)?;
                self.streaming = false;
            }
            Ok(())
        }
        fn release(&mut self) -> io::Result<()> {
            self.stop()?;
            if self.allocated {
                let mut request = RequestBuffers {
                    count: 0,
                    kind: self.kind,
                    memory: self.memory,
                    capabilities: 0,
                    reserved: 0,
                };
                ioctl(self.file.as_raw_fd(), REQBUFS, &mut request)?;
                self.allocated = false;
            }
            Ok(())
        }
        // Normalize the one-plane mplane ABI into the same logical descriptor
        // used by the single-plane path. The plane pointer lives through ioctl.
        fn buffer_ioctl(&self, request: u32, b: &mut Buffer) -> io::Result<()> {
            if !matches!(self.kind, 9 | 10) {
                return ioctl(self.file.as_raw_fd(), request, b);
            }
            let mut plane: Plane = zero();
            plane.used = b.used;
            plane.length = b.length;
            if self.memory == 4 {
                plane.memory.fd = unsafe { b.data.fd };
            }
            b.data.planes = &mut plane;
            b.length = 1;
            let outcome = ioctl(self.file.as_raw_fd(), request, b);
            b.data = BufferMemory { offset: 0 };
            if outcome.is_ok() && (b.length != 1 || plane.offset != 0) {
                return Err(error(
                    "Raw bridge requires exactly one plane with zero data offset",
                ));
            }
            b.used = plane.used;
            b.length = plane.length;
            outcome
        }
        fn record(&self, index: u32) -> Buffer {
            let mut b: Buffer = zero();
            b.index = index;
            b.kind = self.kind;
            b.memory = self.memory;
            b
        }
    }
    impl Drop for Endpoint {
        fn drop(&mut self) {
            let _ = self.release();
        }
    }
    pub struct Bridge {
        // RX must release imported buffers before exported handles/TX allocations.
        rx: Endpoint,
        exports: Vec<OwnedFd>,
        tx: Endpoint,
        isp: File,
        sof_device: Option<File>,
        lengths: Vec<u32>,
        inflight: Vec<bool>,
        first: bool,
        transferred: u64,
        sof: std::collections::VecDeque<(u32, u64)>,
        sof_matches: u64,
        sof_missing: u64,
        frames: std::collections::VecDeque<Value>,
        frame_records_dropped: u64,
    }
    impl Bridge {
        pub fn prepare(
            tx_path: &str,
            rx_path: &str,
            isp_path: &str,
            sof_path: Option<&str>,
        ) -> io::Result<Self> {
            use std::os::unix::fs::{FileTypeExt, MetadataExt};
            if std::mem::size_of::<usize>() != 4 {
                return Err(error("Raw bridge requires ARM32 Linux"));
            }
            let paths = [tx_path, rx_path, isp_path];
            let mut devices = Vec::new();
            for path in paths {
                let m = fs::metadata(path)?;
                if !m.file_type().is_char_device() || devices.contains(&m.rdev()) {
                    return Err(error(
                        "Raw TX, RX and ISP must be distinct character devices",
                    ));
                }
                devices.push(m.rdev());
            }
            if !vendor_processes().is_empty() {
                return Err(error("Vendor camera process running"));
            }
            let tx_file = open(tx_path, true)?;
            let rx_file = open(rx_path, true)?;
            let isp = open(isp_path, true)?;
            let sof_device = match sof_path {
                Some(path) if path != isp_path => {
                    let metadata = fs::metadata(path)?;
                    if !metadata.file_type().is_char_device() || devices.contains(&metadata.rdev())
                    {
                        return Err(error(
                            "Separate SOF endpoint must be a distinct character device",
                        ));
                    }
                    Some(open(path, true)?)
                }
                _ => None,
            };
            let (_, tx_caps) = capability(&tx_file)?;
            let (_, rx_caps) = capability(&rx_file)?;
            let kind = |caps: u32,
                        single: u32,
                        multi: u32,
                        single_bit: u32,
                        multi_bit: u32|
             -> io::Result<u32> {
                if caps & 0x04000000 == 0 {
                    return Err(error("Raw endpoint lacks streaming capability"));
                }
                if caps & multi_bit != 0 {
                    Ok(multi)
                } else if caps & single_bit != 0 {
                    Ok(single)
                } else {
                    Err(error("Raw endpoint lacks capture/output capability"))
                }
            };
            let tx_kind = kind(tx_caps, 1, 9, 1, 0x1000)?;
            let rx_kind = kind(rx_caps, 2, 10, 2, 0x2000)?;
            let tx_format = format(&tx_file, tx_kind)?;
            let rx_format = format(&rx_file, rx_kind)?;
            let t = unsafe { &tx_format.data.raw };
            let r = unsafe { &rx_format.data.raw };
            let geometry = |f: &[u8], kind: u32| -> io::Result<(u32, u32)> {
                if matches!(kind, 9 | 10) {
                    if f[180] != 1 {
                        return Err(error("Raw bridge supports one image plane only"));
                    }
                    Ok((get32(f, 24), get32(f, 20)))
                } else {
                    Ok((get32(f, 16), get32(f, 20)))
                }
            };
            let (stride, size) = geometry(t, tx_kind)?;
            let raw_fourcc = get32(t, 8).to_le_bytes();
            if ![*b"BG10", *b"GB10", *b"BA10", *b"RG10"].contains(&raw_fourcc) {
                return Err(error("Raw bridge requires a RAW10 Bayer format"));
            }
            if t[..12] != r[..12]
                || size == 0
                || stride == 0
                || (stride, size) != geometry(r, rx_kind)?
            {
                return Err(error(
                    "Raw TX/RX dimensions, FourCC, stride and sizeimage must match",
                ));
            }
            // Read only: never change an active device's memory mode here.
            let mut tx_mode = -1i32;
            let mut rx_mode = -1i32;
            ioctl(tx_file.as_raw_fd(), 0x800456c0, &mut tx_mode)?;
            ioctl(rx_file.as_raw_fd(), 0x80045724, &mut rx_mode)?;
            if tx_mode != rx_mode || !matches!(tx_mode, 0 | 2) {
                return Err(error(
                    "Raw CSI memory modes must match (compact or word-high-aligned)",
                ));
            }
            let width = get32(t, 0) as u64;
            let height = get32(t, 4) as u64;
            let minimum_stride = if tx_mode == 0 {
                (width * 10).div_ceil(8)
            } else {
                width * 2
            };
            if width == 0
                || height == 0
                || (stride as u64) < minimum_stride
                || (size as u64) < stride as u64 * height
            {
                return Err(error("Raw storage dimensions exceed stride/sizeimage"));
            }
            let mut bridge = Self {
                rx: Endpoint {
                    file: rx_file,
                    kind: rx_kind,
                    memory: 4,
                    allocated: false,
                    streaming: false,
                },
                exports: vec![],
                tx: Endpoint {
                    file: tx_file,
                    kind: tx_kind,
                    memory: 1,
                    allocated: false,
                    streaming: false,
                },
                isp,
                sof_device,
                lengths: vec![],
                inflight: vec![],
                first: true,
                transferred: 0,
                sof: std::collections::VecDeque::new(),
                sof_matches: 0,
                sof_missing: 0,
                frames: std::collections::VecDeque::new(),
                frame_records_dropped: 0,
            };
            let mut subscription = [0u32; 8];
            subscription[0] = 4;
            ioctl(
                bridge
                    .sof_device
                    .as_ref()
                    .unwrap_or(&bridge.isp)
                    .as_raw_fd(),
                0x4020565a,
                &mut subscription,
            )?;
            let count = bridge.tx.allocate(4)?;
            let count = count.min(bridge.rx.allocate(count)?);
            for index in 0..count {
                let mut b = bridge.tx.record(index);
                bridge.tx.buffer_ioctl(QUERYBUF, &mut b)?;
                if b.length < size || b.length > 128 * 1024 * 1024 {
                    return Err(error("Invalid raw TX buffer length"));
                }
                let mut export = Export {
                    kind: tx_kind,
                    index,
                    plane: 0,
                    flags: libc::O_CLOEXEC as u32,
                    fd: -1,
                    reserved: [0; 11],
                };
                ioctl(
                    bridge.tx.file.as_raw_fd(),
                    ioc::<Export>(3, 16),
                    &mut export,
                )?;
                if export.fd < 0 {
                    return Err(error("EXPBUF returned invalid FD"));
                }
                bridge
                    .exports
                    .push(unsafe { OwnedFd::from_raw_fd(export.fd) });
                bridge.lengths.push(b.length);
                bridge.inflight.push(false);
                bridge.tx.buffer_ioctl(QUEUE, &mut b)?;
            }
            Ok(bridge)
        }
        fn drain_sof(&mut self) -> io::Result<()> {
            // Bounded drain/cache prevents a noisy event source from starving raw I/O.
            for _ in 0..64 {
                let mut event = [0u8; 128];
                match ioctl(
                    self.sof_device.as_ref().unwrap_or(&self.isp).as_raw_fd(),
                    0x80805659,
                    &mut event,
                ) {
                    Ok(()) => {
                        if let Some(pair) = shieldsigner_rkaiq::raw_readback::frame_sync(&event)
                            .map_err(|_| error("Invalid SOF timestamp"))?
                        {
                            if let Some(entry) = self.sof.iter_mut().find(|entry| entry.0 == pair.0)
                            {
                                *entry = pair;
                            } else {
                                if self.sof.len() == 64 {
                                    self.sof.pop_front();
                                }
                                self.sof.push_back(pair);
                            }
                        }
                    }
                    // Linux v4l2_event_dequeue returns ENOENT for an empty
                    // nonblocking event queue (not the buffer API's EAGAIN).
                    Err(e)
                        if e.kind() == io::ErrorKind::WouldBlock
                            || e.raw_os_error() == Some(libc::ENOENT) =>
                    {
                        break
                    }
                    Err(e) => return Err(e),
                }
            }
            Ok(())
        }
        fn pump(&mut self, stop: &AtomicBool) -> io::Result<()> {
            let mut last = Instant::now();
            while !stop.load(Ordering::Acquire) {
                self.drain_sof()?;
                // Complete RX before admitting more TX. A TX buffer remains held
                // until the corresponding imported RX index has been dequeued.
                let mut done = self.rx.record(0);
                match self.rx.buffer_ioctl(DEQUEUE, &mut done) {
                    Ok(()) => {
                        let index = done.index as usize;
                        if index >= self.inflight.len()
                            || !self.inflight[index]
                            || done.flags & 0x40 != 0
                        {
                            return Err(error("Invalid/error raw RX completion"));
                        }
                        self.inflight[index] = false;
                        if let Some(record) = self.frames.iter_mut().rev().find(|r| {
                            r["bufferIndex"].as_u64() == Some(done.index as u64)
                                && r["rxCompleted"] == false
                        }) {
                            record["rxCompleted"] = json!(true);
                            record["rxSequence"] = json!(done.sequence);
                        }
                        let mut b = self.tx.record(done.index);
                        self.tx.buffer_ioctl(QUEUE, &mut b)?;
                        self.transferred += 1;
                        last = Instant::now();
                    }
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => (),
                    Err(e) => return Err(e),
                }
                let mut raw = self.tx.record(0);
                match self.tx.buffer_ioctl(DEQUEUE, &mut raw) {
                    Ok(()) => {
                        let index = raw.index as usize;
                        if index >= self.inflight.len()
                            || self.inflight[index]
                            || raw.flags & 0x40 != 0
                            || raw.used == 0
                            || raw.used > self.lengths[index]
                        {
                            return Err(error("Invalid/error raw TX completion"));
                        }
                        if raw.time.seconds < 0 || !(0..1_000_000).contains(&raw.time.microseconds)
                        {
                            return Err(error("Invalid raw frame timestamp"));
                        }
                        let mut input = self.rx.record(raw.index);
                        input.used = raw.used;
                        input.length = self.lengths[index];
                        input.field = raw.field;
                        input.data.fd = self.exports[index].as_raw_fd();
                        input.time = KernelTimeval {
                            seconds: raw.time.seconds,
                            microseconds: raw.time.microseconds,
                        };
                        self.rx.buffer_ioctl(QUEUE, &mut input)?;
                        self.inflight[index] = true;
                        let us = (raw.time.seconds as u64)
                            .wrapping_mul(1_000_000)
                            .wrapping_add(raw.time.microseconds as u64);
                        self.drain_sof()?;
                        // The original map lookup clamps signed-negative IDs to zero.
                        let lookup = if (raw.sequence as i32) < 0 {
                            0
                        } else {
                            raw.sequence
                        };
                        let sof = match self.sof.iter().find(|entry| entry.0 == lookup) {
                            Some(entry) => {
                                self.sof_matches += 1;
                                entry.1
                            }
                            None => {
                                self.sof_missing += 1;
                                0
                            }
                        };
                        let mut trigger = shieldsigner_rkaiq::raw_readback::linear_trigger(
                            raw.sequence,
                            sof,
                            us,
                            0,
                            self.first,
                            false,
                        );
                        ioctl(
                            self.isp.as_raw_fd(),
                            shieldsigner_rkaiq::raw_readback::TRIGGER_IOCTL,
                            &mut trigger,
                        )?;
                        if self.frames.len() == 256 {
                            self.frames.pop_front();
                            self.frame_records_dropped += 1;
                        }
                        self.frames.push_back(json!({"bufferIndex":raw.index,"rawFrameId":raw.sequence,"triggerFrameId":raw.sequence,"sofLookupFrameId":lookup,"sofMatched":self.sof.iter().any(|e|e.0==lookup),"sofTimestampNs":sof,"sensorTimestampUs":us,"rxCompleted":false,"rxSequence":null}));
                        self.first = false;
                        last = Instant::now();
                    }
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => (),
                    Err(e) => return Err(e),
                }
                if last.elapsed() > Duration::from_secs(10) {
                    return Err(error("Raw bridge made no progress for 10 seconds"));
                }
                std::thread::sleep(Duration::from_millis(1));
            }
            Ok(())
        }
        pub fn during<F: FnOnce() -> io::Result<()>>(mut self, work: F) -> io::Result<()> {
            let stop = Arc::new(AtomicBool::new(false));
            let flag = stop.clone();
            let (ready_tx, ready_rx) = std::sync::mpsc::sync_channel(1);
            std::thread::scope(|scope| {
                let worker=scope.spawn(move || {
                    // Startup must finish before image capture begins.
                    let started=self.tx.start().and_then(|_|self.rx.start());
                    let _=ready_tx.send(started.as_ref().map(|_|()).map_err(|e|e.to_string()));
                    let outcome=started.and_then(|_|self.pump(&flag));
                    let mut cleanup=Vec::new();
                    if let Err(e)=self.rx.release(){cleanup.push(e.to_string());}
                    self.exports.clear();
                    if let Err(e)=self.tx.release(){cleanup.push(e.to_string());}
                    println!("{}",json!({"event":"raw-bridge-finished","completedFrames":self.transferred,"sofMatches":self.sof_matches,"sofMissing":self.sof_missing,"recentFrames":self.frames,"recentFrameLimit":256,"frameRecordsDropped":self.frame_records_dropped,"frameExposureAssociationVerified":false,"error":outcome.as_ref().err().map(|e|e.to_string()),"cleanupErrors":cleanup,"hardwareVerified":false}));
                    outcome.and_then(|_|if cleanup.is_empty(){Ok(())}else{Err(error("Raw bridge cleanup failed"))})
                });
                let startup = ready_rx
                    .recv()
                    .map_err(|_| error("Raw bridge startup channel closed"))?;
                let result = match startup {
                    Ok(()) => work(),
                    Err(e) => Err(error(e)),
                };
                stop.store(true, Ordering::Release);
                let bridge_result = worker
                    .join()
                    .map_err(|_| error("Raw bridge worker panicked"))?;
                result.and(bridge_result)
            })
        }
    }
}

#[cfg(test)]
mod raw_bridge_driver_test {
    use super::*;
    use std::sync::Mutex;
    #[derive(Default)]
    struct Driver {
        tx: Option<RawFd>,
        rx: Option<RawFd>,
        isp: Option<RawFd>,
        trace: Vec<String>,
        mode: u8,
        api: u8,
        tx_dequeued: bool,
        rx_queued: bool,
        triggered: bool,
        finished: bool,
        sof_sent: bool,
    }
    static DRIVER: Mutex<Option<Driver>> = Mutex::new(None);
    pub(super) fn mock<T>(fd: RawFd, request: u32, value: &mut T) -> Option<io::Result<()>> {
        let mut lock = DRIVER.lock().unwrap();
        let driver = lock.as_mut()?;
        let b = unsafe {
            std::slice::from_raw_parts_mut((value as *mut T).cast::<u8>(), std::mem::size_of::<T>())
        };
        let mut outcome = Ok(());
        match request {
            QUERYCAP => {
                let cap = if driver.tx.is_none() {
                    driver.tx = Some(fd);
                    if driver.api & 1 != 0 {
                        0x04001000
                    } else {
                        0x04000001
                    }
                } else {
                    driver.rx = Some(fd);
                    if driver.api & 2 != 0 {
                        0x04002000
                    } else {
                        0x04000002
                    }
                };
                put32(b, 84, cap);
            }
            0x800456c0 | 0x80045724 => {
                put32(
                    b,
                    0,
                    if driver.mode == 5 && driver.rx == Some(fd) {
                        2
                    } else {
                        0
                    },
                );
            }
            GETFMT => {
                let multi = matches!(get32(b, 0), 9 | 10);
                for (o, v) in [
                    (4, 640),
                    (8, 480),
                    (12, u32::from_le_bytes(*b"BG10")),
                    (20, 1280),
                    (24, 614400),
                ] {
                    put32(b, o, v);
                }
                if multi {
                    put32(b, 20, 0);
                    put32(b, 24, 614400);
                    put32(b, 28, 1280);
                    b[184] = 1;
                }
            }
            REQBUFS => {
                // Real RV1106 returned two MMAP buffers when four were requested.
                if get32(b, 0) != 0 {
                    put32(b, 0, 2);
                }
                driver.trace.push(format!(
                    "{}:req:{}",
                    if driver.tx == Some(fd) { "tx" } else { "rx" },
                    get32(b, 0)
                ));
            }
            QUERYBUF => {
                if matches!(get32(b, 4), 9 | 10) {
                    assert_eq!(get32(b, 56), 1);
                    let p = unsafe { &mut *(get32(b, 52) as usize as *mut Plane) };
                    p.length = 614400;
                } else {
                    put32(b, 56, 614400);
                }
            }
            0xc0405610 => {
                let exported = unsafe { libc::dup(fd) };
                assert!(exported >= 0);
                put32(b, 16, exported as u32);
            }
            0x4020565a => {
                assert_eq!(get32(b, 0), 4);
                driver.isp = Some(fd);
                driver.trace.push("sof:subscribe".into());
            }
            0x80805659 => {
                if driver.sof_sent {
                    outcome = Err(io::Error::from_raw_os_error(libc::ENOENT));
                } else {
                    driver.sof_sent = true;
                    b.fill(0);
                    for (o, v) in [(0, 4), (8, 77), (76, 999), (80, 3), (84, 456)] {
                        put32(b, o, v);
                    }
                }
            }
            STREAMON => {
                let role = if driver.tx == Some(fd) { "tx" } else { "rx" };
                driver.trace.push(format!("{role}:on"));
                if driver.mode == 1 && role == "rx" {
                    outcome = Err(io::Error::from_raw_os_error(libc::EIO));
                    driver.finished = true;
                }
            }
            STREAMOFF => {
                driver.trace.push(format!(
                    "{}:off",
                    if driver.tx == Some(fd) { "tx" } else { "rx" }
                ));
            }
            QUEUE => {
                if driver.tx == Some(fd) {
                    if driver.tx_dequeued {
                        assert!(driver.finished, "TX reused before RX completion");
                        driver.trace.push("tx:requeue".into());
                    } else {
                        driver.trace.push("tx:initial-queue".into());
                    }
                } else {
                    driver.trace.push("rx:queue".into());
                    assert_eq!(get32(b, 48), 4);
                    let imported = if get32(b, 4) == 10 {
                        assert_eq!(get32(b, 56), 1);
                        let p = unsafe { &*(get32(b, 52) as usize as *const Plane) };
                        assert_eq!(p.used, 614400);
                        assert_eq!(p.length, 614400);
                        unsafe { p.memory.fd }
                    } else {
                        assert_eq!(get32(b, 8), 614400);
                        get32(b, 52) as RawFd
                    };
                    assert!(unsafe { libc::fcntl(imported, libc::F_GETFD) } >= 0);
                    if driver.mode == 2 {
                        driver.finished = true;
                        outcome = Err(io::Error::from_raw_os_error(libc::EIO));
                    } else {
                        driver.rx_queued = true;
                    }
                }
            }
            DEQUEUE => {
                if driver.tx == Some(fd) && !driver.tx_dequeued {
                    driver.tx_dequeued = true;
                    driver.trace.push("tx:dequeue".into());
                    put32(b, 0, 0);
                    if get32(b, 4) == 9 {
                        let p = unsafe { &mut *(get32(b, 52) as usize as *mut Plane) };
                        p.used = 614400;
                        p.length = 614400;
                    } else {
                        put32(b, 8, 614400);
                    }
                    put32(b, 20, 4);
                    put32(b, 24, 500);
                    put32(b, 44, 77);
                } else if driver.rx == Some(fd) && driver.triggered && !driver.finished {
                    driver.finished = true;
                    driver.trace.push("rx:dequeue".into());
                    put32(b, 0, 0);
                    if driver.mode == 4 {
                        put32(b, 12, 0x40);
                    }
                } else {
                    outcome = Err(io::Error::from_raw_os_error(libc::EAGAIN));
                }
            }
            shieldsigner_rkaiq::raw_readback::TRIGGER_IOCTL => {
                assert!(driver.rx_queued);
                assert_eq!(driver.isp, Some(fd));
                let expected = shieldsigner_rkaiq::raw_readback::linear_trigger(
                    77,
                    3_000_000_456,
                    4_000_500,
                    0,
                    true,
                    false,
                );
                assert_eq!(b, &expected);
                driver.trace.push("isp:trigger".into());
                if driver.mode == 3 {
                    driver.finished = true;
                    outcome = Err(io::Error::from_raw_os_error(libc::EIO));
                } else {
                    driver.triggered = true;
                }
            }
            _ => panic!("unexpected mocked request {request:x}"),
        }
        Some(outcome)
    }
    #[test]
    fn mismatched_storage_is_rejected_before_allocation() {
        *DRIVER.lock().unwrap() = Some(Driver {
            mode: 5,
            ..Driver::default()
        });
        let outcome = raw_bridge::Bridge::prepare("/dev/null", "/dev/zero", "/dev/full", None);
        assert!(outcome.is_err());
        let driver = DRIVER.lock().unwrap().take().unwrap();
        assert!(driver.trace.is_empty());
    }
    #[test]
    fn real_bridge_loop_success_and_driver_failures() {
        for api in 0..4 {
            for mode in 0..5 {
                *DRIVER.lock().unwrap() = Some(Driver {
                    mode,
                    api,
                    ..Driver::default()
                });
                let bridge =
                    raw_bridge::Bridge::prepare("/dev/null", "/dev/zero", "/dev/full", None)
                        .unwrap();
                let outcome = bridge.during(|| {
                    let deadline = Instant::now() + Duration::from_secs(2);
                    while !DRIVER.lock().unwrap().as_ref().unwrap().finished {
                        assert!(Instant::now() < deadline, "mock bridge stalled");
                        std::thread::sleep(Duration::from_millis(1));
                    }
                    Ok(())
                });
                let driver = DRIVER.lock().unwrap().take().unwrap();
                assert_eq!(outcome.is_ok(), mode == 0, "mode {mode}: {outcome:?}");
                let position = |s: &str| driver.trace.iter().position(|v| v == s);
                assert!(position("tx:off").is_some());
                assert!(position("tx:req:0").is_some());
                assert!(position("rx:req:0").is_some());
                if mode != 1 {
                    assert!(position("rx:off") < position("tx:off"));
                }
                if mode == 0 {
                    assert!(position("rx:queue") < position("isp:trigger"));
                    assert!(position("isp:trigger") < position("rx:dequeue"));
                    assert!(position("rx:dequeue") < position("tx:requeue"));
                } else {
                    assert!(position("tx:requeue").is_none());
                }
                if mode == 2 {
                    assert!(position("isp:trigger").is_none());
                }
            }
        }
    }
}

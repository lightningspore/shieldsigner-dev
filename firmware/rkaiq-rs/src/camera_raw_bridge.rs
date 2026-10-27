// Included in the Linux camera diagnostic. Linear, single-plane raw DMA-BUF
// transfer only. Formats/media links must already be configured explicitly.
mod raw_bridge {
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
            if request.count < count || request.count > 16 {
                return Err(error("Raw buffer allocation outside requested bounds"));
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
        lengths: Vec<u32>,
        inflight: Vec<bool>,
        first: bool,
        transferred: u64,
    }
    impl Bridge {
        pub fn prepare(tx_path: &str, rx_path: &str, isp_path: &str) -> io::Result<Self> {
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
            let (_, tx_caps) = capability(&tx_file)?;
            let (_, rx_caps) = capability(&rx_file)?;
            if tx_caps & 0x04000001 != 0x04000001 || rx_caps & 0x04000002 != 0x04000002 {
                return Err(error(
                    "Raw bridge currently requires single-plane streaming capture TX and output RX",
                ));
            }
            let tx_format = format(&tx_file, 1)?;
            let rx_format = format(&rx_file, 2)?;
            let t = unsafe { &tx_format.data.raw };
            let r = unsafe { &rx_format.data.raw };
            let raw_fourcc = get32(t, 8).to_le_bytes();
            if ![*b"BG10", *b"GB10", *b"BA10", *b"RG10"].contains(&raw_fourcc) {
                return Err(error("Raw bridge requires an unpacked RAW10 Bayer format"));
            }
            if t[..12] != r[..12]
                || get32(t, 20) == 0
                || get32(t, 20) != get32(r, 20)
                || get32(t, 16) != get32(r, 16)
            {
                return Err(error(
                    "Raw TX/RX dimensions, FourCC, stride and sizeimage must match",
                ));
            }
            let mut bridge = Self {
                rx: Endpoint {
                    file: rx_file,
                    kind: 2,
                    memory: 4,
                    allocated: false,
                    streaming: false,
                },
                exports: vec![],
                tx: Endpoint {
                    file: tx_file,
                    kind: 1,
                    memory: 1,
                    allocated: false,
                    streaming: false,
                },
                isp,
                lengths: vec![],
                inflight: vec![],
                first: true,
                transferred: 0,
            };
            let count = bridge.tx.allocate(4)?;
            bridge.rx.allocate(count)?;
            for index in 0..count {
                let mut b = bridge.tx.record(index);
                ioctl(bridge.tx.file.as_raw_fd(), QUERYBUF, &mut b)?;
                if b.length < get32(t, 20) || b.length > 128 * 1024 * 1024 {
                    return Err(error("Invalid raw TX buffer length"));
                }
                let mut export = Export {
                    kind: 1,
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
                ioctl(bridge.tx.file.as_raw_fd(), QUEUE, &mut b)?;
            }
            Ok(bridge)
        }
        fn pump(&mut self, stop: &AtomicBool) -> io::Result<()> {
            let mut last = Instant::now();
            while !stop.load(Ordering::Acquire) {
                // Complete RX before admitting more TX. A TX buffer remains held
                // until the corresponding imported RX index has been dequeued.
                let mut done = self.rx.record(0);
                match ioctl(self.rx.file.as_raw_fd(), DEQUEUE, &mut done) {
                    Ok(()) => {
                        let index = done.index as usize;
                        if index >= self.inflight.len()
                            || !self.inflight[index]
                            || done.flags & 0x40 != 0
                        {
                            return Err(error("Invalid/error raw RX completion"));
                        }
                        self.inflight[index] = false;
                        let mut b = self.tx.record(done.index);
                        ioctl(self.tx.file.as_raw_fd(), QUEUE, &mut b)?;
                        self.transferred += 1;
                        last = Instant::now();
                    }
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => (),
                    Err(e) => return Err(e),
                }
                let mut raw = self.tx.record(0);
                match ioctl(self.tx.file.as_raw_fd(), DEQUEUE, &mut raw) {
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
                        ioctl(self.rx.file.as_raw_fd(), QUEUE, &mut input)?;
                        self.inflight[index] = true;
                        let us = (raw.time.seconds as u64)
                            .wrapping_mul(1_000_000)
                            .wrapping_add(raw.time.microseconds as u64);
                        // SOF subscription is not integrated yet. Native missing
                        // SOF-map matches use zero; preserve that explicit case.
                        let mut trigger = shieldsigner_rkaiq::raw_readback::linear_trigger(
                            raw.sequence,
                            0,
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
                    println!("{}",json!({"event":"raw-bridge-finished","completedFrames":self.transferred,"error":outcome.as_ref().err().map(|e|e.to_string()),"cleanupErrors":cleanup,"hardwareVerified":false}));
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

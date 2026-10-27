// Included in camera-probe's Linux module to reuse its verified legacy ARM32
// V4L2 structs, syscall wrapper, mappings and device/process inventory.
use shieldsigner_rkaiq::parameter_queue as parameter;
struct ParameterBackend {
    file: Option<File>,
    requested: u32,
    allocated: bool,
    mappings: Vec<Mapping>,
    buffers: Vec<parameter::BufferState>,
    calls: Vec<Value>,
    last_error: Option<String>,
    last_errno: Option<i32>,
    last_dequeue: Option<parameter::BufferRecord>,
    cleanup_errors: Vec<String>,
    dequeue_would_block: u64,
}
impl ParameterBackend {
    fn call<T>(&mut self, operation: &str, request: u32, value: &mut T) -> i32 {
        let result = self
            .file
            .as_ref()
            .ok_or_else(|| error("Parameter device is closed"))
            .and_then(|file| ioctl(file.as_raw_fd(), request, value));
        match result {
            Ok(()) => {
                self.calls.push(json!({"operation":operation,"ok":true}));
                self.last_error = None;
                self.last_errno = None;
                0
            }
            Err(e) => {
                self.last_errno = e.raw_os_error();
                self.last_error = Some(e.to_string());
                if request == DEQUEUE && e.kind() == io::ErrorKind::WouldBlock {
                    self.dequeue_would_block = self.dequeue_would_block.saturating_add(1);
                } else {
                    self.calls
                        .push(json!({"operation":operation,"ok":false,"error":e.to_string()}));
                }
                -9
            }
        }
    }
    fn failure(&self, operation: &str, status: i32) -> io::Error {
        error(format!(
            "{operation} failed ({status}): {}",
            self.last_error
                .as_deref()
                .unwrap_or("invalid driver response")
        ))
    }
    fn initialize(&mut self) -> io::Result<()> {
        if !(2..=8).contains(&self.requested) {
            return Err(error(
                "Parameter driver returned an invalid buffer count (expected 2–8)",
            ));
        }
        for index in 0..self.requested {
            let mut planes: [Plane; PLANES] = zero();
            let mut b = buffer(index, META_OUTPUT, &mut planes);
            if self.call("QUERYBUF", QUERYBUF, &mut b) < 0 {
                return Err(self.failure("QUERYBUF", -9));
            }
            if b.kind != META_OUTPUT
                || b.memory != MMAP
                || b.index != index
                || b.length < shieldsigner_rkaiq::isp32::PARAMETER_BYTES as u32
                || b.length > 65536
            {
                return Err(error("Invalid metadata buffer descriptor/length"));
            }
            let fd = self
                .file
                .as_ref()
                .ok_or_else(|| error("Parameter device is closed"))?
                .as_raw_fd();
            let mapping = Mapping::new(fd, b.length as usize, unsafe { b.data.offset })?;
            let mut record = [0; parameter::BUFFER_BYTES];
            // Entry point rejects non-ARM32 before reaching this copy.
            unsafe {
                ptr::copy_nonoverlapping(
                    (&b as *const Buffer).cast::<u8>(),
                    record.as_mut_ptr(),
                    record.len(),
                );
            }
            let state = parameter::BufferState::from_record(record)
                .map_err(|v| error(format!("Invalid parameter buffer: {v:?}")))?;
            self.mappings.push(mapping);
            self.buffers.push(state);
        }
        Ok(())
    }
}
impl parameter::Backend for ParameterBackend {
    fn request_buffers(&mut self) -> i32 {
        let mut request = RequestBuffers {
            count: self.requested,
            kind: META_OUTPUT,
            memory: MMAP,
            capabilities: 0,
            reserved: 0,
        };
        let result = self.call("REQBUFS", REQBUFS, &mut request);
        if result == 0 {
            self.requested = request.count;
            self.allocated = request.count != 0;
        }
        result
    }
    fn initialize_pool(&mut self) -> i32 {
        match self.initialize() {
            Ok(()) => 0,
            Err(e) => {
                self.last_error = Some(e.to_string());
                self.calls
                    .push(json!({"operation":"initialize-pool","ok":false,"error":e.to_string()}));
                -2
            }
        }
    }
    fn stream_on(&mut self) -> i32 {
        let mut kind = META_OUTPUT;
        self.call("STREAMON", STREAMON, &mut kind)
    }
    fn stream_off(&mut self) -> i32 {
        let mut kind = META_OUTPUT;
        let result = self.call("STREAMOFF", STREAMOFF, &mut kind);
        if result < 0 {
            self.cleanup_errors
                .push(self.last_error.clone().unwrap_or_default());
        }
        result
    }
    fn close(&mut self) {
        self.file.take();
        self.calls.push(json!({"operation":"close"}));
    }
    fn finalize_pool(&mut self) {
        self.buffers.clear();
        self.mappings.clear();
        if self.allocated && self.file.is_some() {
            let mut request = RequestBuffers {
                count: 0,
                kind: META_OUTPUT,
                memory: MMAP,
                capabilities: 0,
                reserved: 0,
            };
            if self.call("REQBUFS-release", REQBUFS, &mut request) < 0 {
                self.cleanup_errors
                    .push(self.last_error.clone().unwrap_or_default());
            }
        }
        self.allocated = false;
    }
    // This diagnostic exclusively owns its queue and descriptors. No state is
    // shared across threads; the recovered lock boundaries require no mutex.
    fn lock(&mut self) {}
    fn unlock(&mut self) {}
    fn queue(&mut self, request: &mut parameter::BufferRecord) -> i32 {
        self.call("QBUF", QUEUE, request)
    }
    fn dequeue(&mut self, request: &mut parameter::BufferRecord) -> i32 {
        let result = self.call("DQBUF", DEQUEUE, request);
        if result == 0 {
            self.last_dequeue = Some(*request);
        }
        result
    }
}
fn wait_parameter(fd: RawFd, deadline: Instant) -> io::Result<()> {
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err(error(
                "Parameter completion timeout; configuration may be pending image streaming",
            ));
        }
        let mut poll = libc::pollfd {
            fd,
            events: libc::POLLIN | libc::POLLOUT,
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
            if e.kind() != io::ErrorKind::Interrupted {
                return Err(e);
            }
            continue;
        }
        if result == 0 {
            continue;
        }
        if poll.revents & (libc::POLLERR | libc::POLLHUP | libc::POLLNVAL) != 0 {
            return Err(error(format!(
                "Parameter poll failed: 0x{:x}",
                poll.revents
            )));
        }
        if poll.revents & (libc::POLLIN | libc::POLLOUT) != 0 {
            return Ok(());
        }
    }
}
fn capture_with_parameters(args: &[String]) -> io::Result<()> {
    use std::os::unix::fs::{FileTypeExt, MetadataExt};
    let separator = args.iter().position(|v| v == "--").ok_or_else(|| {
        error("capture-with-parameters PARAM_NODE PARAM.bin -- IMAGE_NODE OUT [capture options]")
    })?;
    if separator != 2 || args.len() < 5 {
        return Err(error(
            "Expected two parameter arguments, --, then image node and output",
        ));
    }
    let image = &args[3..];
    for path in [&image[1], &format!("{}.json", image[1])] {
        if std::path::Path::new(path).exists() {
            return Err(error("Capture output or metadata exists"));
        }
    }
    let metadata = fs::metadata(&args[0])?;
    let image_metadata = fs::metadata(&image[0])?;
    if !metadata.file_type().is_char_device()
        || !image_metadata.file_type().is_char_device()
        || metadata.rdev() == image_metadata.rdev()
    {
        return Err(error(
            "Parameter and image nodes must be distinct character devices",
        ));
    }
    let mut capture_args = image.to_vec();
    capture_args.push("--require-no-rkaiq".into());
    // Four image buffers for first-frame bring-up; explicit caller overrides remain supported.
    if !capture_args.iter().any(|v| v == "--buffers") {
        capture_args.extend(["--buffers".into(), "4".into()]);
    }
    let mut parameter_args = args[..2].to_vec();
    parameter_args.extend(["--hold-ms".into(), "0".into()]);
    submit_parameters_then(&parameter_args, || {
        println!(
            "{}",
            json!({"event":"image-capture-starting","parameterQueueHeldOpen":true,"device":image[0],"output":image[1],"coldStartProven":false})
        );
        io::stdout().flush()?;
        let outcome = capture(&capture_args, false);
        println!(
            "{}",
            json!({"event":"image-capture-finished","success":outcome.is_ok(),"error":outcome.as_ref().err().map(|e|e.to_string()),"parameterQueueHeldOpen":true,"coldStartProven":false})
        );
        outcome
    })
}
fn submit_parameters(args: &[String]) -> io::Result<()> {
    submit_parameters_then(args, || Ok(()))
}
// The callback executes while backend/queue/mappings are still alive and before
// STREAMOFF. Its error joins the ordinary cleanup path; no detached process.
fn submit_parameters_then<F: FnOnce() -> io::Result<()>>(
    args: &[String],
    after_ready: F,
) -> io::Result<()> {
    use std::io::Read;
    if std::mem::size_of::<usize>() != 4 {
        return Err(error(
            "Parameter submission currently targets ARM32 Linux only",
        ));
    }
    if args.len() < 2 {
        return Err(error(
            "submit-parameters requires NODE FULL_PARAMETERS.bin [--timeout-ms N] [--hold-ms N]",
        ));
    }
    let mut timeout = 3000u64;
    let mut hold = 30000u64;
    let mut next = 2;
    while next < args.len() {
        let option = &args[next];
        next += 1;
        let n = args
            .get(next)
            .ok_or_else(|| error("Missing parameter option value"))?
            .parse::<u64>()
            .map_err(|_| error("Invalid parameter option value"))?;
        next += 1;
        match option.as_str() {
            "--timeout-ms" if (1..=60000).contains(&n) => timeout = n,
            "--hold-ms" if n <= 300000 => hold = n,
            _ => {
                return Err(error(
                    "Unsupported parameter option/range; timeout 1–60000 ms, hold 0–300000 ms",
                ))
            }
        }
    }
    let mut payload = Vec::with_capacity(shieldsigner_rkaiq::isp32::PARAMETER_BYTES + 1);
    File::open(&args[1])?
        .take((shieldsigner_rkaiq::isp32::PARAMETER_BYTES + 1) as u64)
        .read_to_end(&mut payload)?;
    if payload.len() != shieldsigner_rkaiq::isp32::PARAMETER_BYTES {
        return Err(error(
            "Parameter file must contain exactly 11145 full-ISP32 bytes",
        ));
    }
    let updates = u64::from_le_bytes(payload[..8].try_into().unwrap())
        | u64::from_le_bytes(payload[16..24].try_into().unwrap());
    if updates == 0 {
        return Err(error("Parameter record has no module updates"));
    }
    let active = vendor_processes();
    if !active.is_empty() {
        return Err(error(format!(
            "Vendor camera processes still running: {active:?}"
        )));
    }
    let file = open(&args[0], true)?;
    let (_, cap) = capability(&file)?;
    if cap & 0x0c000000 != 0x0c000000 {
        return Err(error("Node must support metadata-output and streaming"));
    }
    let fmt = format(&file, META_OUTPUT)?;
    let raw = unsafe { &fmt.data.raw };
    if get32(raw, 0) != u32::from_le_bytes(*b"RK1P") || get32(raw, 4) != payload.len() as u32 {
        return Err(error(format!(
            "Unsupported parameter format/layout: {}",
            format_json(&fmt)
        )));
    }
    let mut backend = ParameterBackend {
        file: Some(file),
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
    let mut accepted = false;
    let mut completed = None;
    let outcome = (|| -> io::Result<()> {
        let status = queue.start(&mut backend, false);
        if status != 0 {
            return Err(backend.failure("Parameter startup", status));
        }
        let mut buffers = std::mem::take(&mut backend.buffers);
        let mapping = backend
            .mappings
            .first()
            .ok_or_else(|| error("No parameter buffer mapping"))?;
        unsafe {
            ptr::write_bytes(mapping.address.cast::<u8>(), 0, mapping.length);
            ptr::copy_nonoverlapping(
                payload.as_ptr(),
                mapping.address.cast::<u8>(),
                payload.len(),
            );
        }
        let status = queue.queue(&mut backend, &mut buffers[0], false, false);
        if status != 0 {
            return Err(backend.failure("Parameter QBUF", status));
        }
        accepted = true;
        let deadline = Instant::now() + Duration::from_millis(timeout);
        let index = loop {
            let fd = backend
                .file
                .as_ref()
                .ok_or_else(|| error("Parameter device is closed"))?
                .as_raw_fd();
            wait_parameter(fd, deadline)?;
            match queue.dequeue(&mut backend, &mut buffers, MMAP, false) {
                Ok(index) => break index,
                Err(_) if backend.last_errno == Some(libc::EAGAIN) => continue,
                Err(status) => return Err(backend.failure("Parameter DQBUF", status)),
            }
        };
        let record = backend
            .last_dequeue
            .as_ref()
            .ok_or_else(|| error("Missing parameter completion record"))?;
        if parameter::word(record, 12) & 0x40 != 0 {
            return Err(error("Driver returned a parameter buffer error flag"));
        }
        let length = parameter::word(record, 56) as usize;
        if parameter::word(record, 4) != META_OUTPUT
            || parameter::word(record, 48) != MMAP
            || length < payload.len()
            || length > backend.mappings[index].length
            || parameter::word(record, 8) as usize > length
        {
            return Err(error(
                "Driver returned invalid parameter completion bounds/type",
            ));
        }
        completed = Some(
            json!({"bufferIndex":index,"sequence":parameter::word(record,44),"bytesUsed":parameter::word(record,8),"length":parameter::word(record,56),"flags":parameter::word(record,12)}),
        );
        queue.return_to_pool(&mut backend, &mut buffers[index]);
        println!(
            "{}",
            json!({"event":"parameters-dequeued","frameApplicationVerified":false,"holdMs":hold,"completion":completed})
        );
        io::stdout().flush()?;
        after_ready()?;
        if hold != 0 {
            std::thread::sleep(Duration::from_millis(hold));
        }
        Ok(())
    })();
    let allocated = backend.allocated;
    queue.stop(&mut backend, allocated);
    let failure = outcome.err().map(|e| e.to_string()).or_else(|| {
        if backend.cleanup_errors.is_empty() {
            None
        } else {
            Some("Parameter cleanup failed; inspect cleanupErrors".into())
        }
    });
    println!(
        "{}",
        json!({"event":"finished","success":failure.is_none(),"error":failure,"device":args[0],"parameterFile":args[1],"parameterFrameId":get32(&payload,24),"payloadBytes":payload.len(),"parameterQueued":accepted,"frameApplicationVerified":false,"coldStartProven":false,"completion":completed,"holdMs":hold,"bufferCount":backend.requested,"cleanupErrors":backend.cleanup_errors,"dequeueWouldBlockCount":backend.dequeue_would_block,"calls":backend.calls})
    );
    match failure {
        Some(e) => Err(error(e)),
        None => Ok(()),
    }
}

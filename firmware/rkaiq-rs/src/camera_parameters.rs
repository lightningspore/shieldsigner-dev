// Shared native ordinary-batch header for gain-only and measurement updates.
fn mark_runtime_parameter_frame(
    payload: &mut [u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
    frame: u32,
) {
    let config = u64::from_le_bytes(payload[16..24].try_into().unwrap()) | (1u64 << 63);
    payload[16..24].copy_from_slice(&config.to_le_bytes());
    payload[24..28].copy_from_slice(&frame.to_le_bytes());
}
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
                record_camera_trace(&mut self.calls, json!({"operation":operation,"ok":true}));
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
                    record_camera_trace(
                        &mut self.calls,
                        json!({"operation":operation,"ok":false,"error":e.to_string()}),
                    );
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
    /// Acquire and fill one persistent MMAP slot, then queue it through the
    /// recovered state machine. Buffer ownership remains in this backend.
    fn enqueue_payload(
        &mut self,
        queue: &mut parameter::Queue,
        payload: &[u8],
    ) -> io::Result<usize> {
        if payload.len() != shieldsigner_rkaiq::isp32::PARAMETER_BYTES {
            return Err(error("Expected one complete ISP32 parameter record"));
        }
        let mut buffers = std::mem::take(&mut self.buffers);
        let result = (|| {
            let index = queue
                .get_buffer(self, &mut buffers, None)
                .map_err(|status| self.failure("Parameter acquisition", status))?;
            let result = (|| {
                let mapping = self
                    .mappings
                    .get(index)
                    .ok_or_else(|| error("No parameter buffer mapping"))?;
                if mapping.length < payload.len() {
                    return Err(error("Parameter mapping too short"));
                }
                unsafe {
                    ptr::write_bytes(mapping.address.cast::<u8>(), 0, mapping.length);
                    ptr::copy_nonoverlapping(
                        payload.as_ptr(),
                        mapping.address.cast::<u8>(),
                        payload.len(),
                    );
                }
                let status = queue.queue(self, &mut buffers[index], false, false);
                if status != 0 {
                    return Err(self.failure("Parameter QBUF", status));
                }
                Ok(index)
            })();
            if result.is_err() {
                queue.return_to_pool(self, &mut buffers[index]);
            }
            result
        })();
        self.buffers = buffers;
        result
    }
    /// Build and submit an ordinary linear gain batch from the runtime's actual
    /// effective map. This is an event-owner API, not an automatic capture loop.
    /// Commit the WB cache only after QBUF succeeds. Driver failures still
    /// require event-owner recovery; this method never retries automatically.
    fn enqueue_runtime_gain(
        &mut self,
        queue: &mut parameter::Queue,
        runtime: &shieldsigner_rkaiq::ae_runtime::Runtime,
        frame: u32,
        unscaled_wb: &mut [u8; shieldsigner_rkaiq::isp32::AWB_GAIN_BYTES],
        white_balance: Option<shieldsigner_rkaiq::isp32::WhiteBalanceGain>,
    ) -> io::Result<Option<(usize, shieldsigner_rkaiq::ae_runtime::IspGainOutput)>> {
        use shieldsigner_rkaiq::isp32;
        let mut payload = [0u8; isp32::PARAMETER_BYTES];
        payload[isp32::AWB_GAIN_OFFSET..isp32::AWB_GAIN_OFFSET + 32].copy_from_slice(unscaled_wb);
        let mut next_wb = *unscaled_wb;
        let association = runtime
            .apply_isp_gain_results(frame, &mut payload, &mut next_wb, white_balance)
            .map_err(error)?;
        let updates = u64::from_le_bytes(payload[..8].try_into().unwrap())
            | u64::from_le_bytes(payload[16..24].try_into().unwrap());
        if updates == 0 {
            return Ok(None);
        }
        // Native setIspConfig marks an ordinary ISP batch in the high mask word.
        mark_runtime_parameter_frame(&mut payload, frame);
        let index = self.enqueue_payload(queue, &payload)?;
        *unscaled_wb = next_wb;
        Ok(Some((index, association)))
    }
    /// Drain one nonblocking completion. EAGAIN preserves pool ownership;
    /// validated completions release their slot. Invalid driver results require
    /// teardown, and are never silently made available for another submission.
    fn try_complete(&mut self, queue: &mut parameter::Queue) -> io::Result<Option<Value>> {
        if queue.queued_count == 0 {
            return Ok(None);
        }
        let mut buffers = std::mem::take(&mut self.buffers);
        let result = (|| {
            let index = match queue.dequeue(self, &mut buffers, MMAP, false) {
                Ok(index) => index,
                Err(-9) if self.last_errno == Some(libc::EAGAIN) => return Ok(None),
                Err(status) => return Err(self.failure("Parameter DQBUF", status)),
            };
            let record = self
                .last_dequeue
                .as_ref()
                .ok_or_else(|| error("Missing parameter completion record"))?;
            let mapping = self
                .mappings
                .get(index)
                .ok_or_else(|| error("Missing completed parameter mapping"))?;
            let length = parameter::word(record, 56) as usize;
            if !buffers[index].queued
                || parameter::word(record, 12) & 0x40 != 0
                || parameter::word(record, 4) != META_OUTPUT
                || parameter::word(record, 48) != MMAP
                || length < shieldsigner_rkaiq::isp32::PARAMETER_BYTES
                || length > mapping.length
                || parameter::word(record, 8) as usize > length
            {
                return Err(error(
                    "Driver returned invalid parameter completion flags/bounds/type/ownership",
                ));
            }
            let completed = json!({"bufferIndex":index,"sequence":parameter::word(record,44),"bytesUsed":parameter::word(record,8),"length":parameter::word(record,56),"flags":parameter::word(record,12)});
            queue.return_to_pool(self, &mut buffers[index]);
            Ok(Some(completed))
        })();
        self.buffers = buffers;
        result
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
                record_camera_trace(
                    &mut self.calls,
                    json!({"operation":"initialize-pool","ok":false,"error":e.to_string()}),
                );
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
        record_camera_trace(&mut self.calls, json!({"operation":"close"}));
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
    #[cfg(test)]
    if first_frame_driver::active() {
        return Ok(());
    }
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
fn capture_cif_with_parameters(args: &[String]) -> io::Result<()> {
    capture_cif_with_parameters_observed(args, None)
}
fn capture_cif_with_parameters_observed(
    args: &[String],
    observer: Option<CameraAeSender>,
) -> io::Result<()> {
    capture_cif_with_parameters_controlled(args, observer, None)
}
fn capture_cif_with_parameters_controlled(
    args: &[String],
    observer: Option<CameraAeSender>,
    control: Option<AutomaticCapture>,
) -> io::Result<()> {
    use std::os::unix::fs::MetadataExt;
    let separator = args
        .iter()
        .position(|s| s == "--")
        .ok_or_else(|| error("Missing capture separator"))?;
    if separator < 5 {
        return Err(error("Missing raw bridge endpoints"));
    }
    let mut sof = None;
    let mut step = None;
    let mut i = 5;
    while i < separator {
        if args[i] == "--sof-node" && i + 1 < separator && sof.is_none() {
            sof = Some(args[i + 1].as_str());
            i += 2;
        } else if matches!(args[i].as_str(), "--exposure-step" | "--gain-step") && i + 3 < separator && step.is_none() {
            step = Some(raw_bridge::ExposureStep {
                control_id: if args[i] == "--gain-step" { 0x009e0903 } else { 0x00980911 },
                sensor: args[i + 1].clone(),
                frame: args[i + 2]
                    .parse()
                    .map_err(|_| error("Invalid step frame"))?,
                code: args[i + 3]
                    .parse()
                    .map_err(|_| error("Invalid step code"))?,
            });
            i += 4;
        } else {
            return Err(error("Unknown/duplicate raw bridge option"));
        }
    }
    if args.len() < separator + 3 {
        return Err(error("Missing image endpoint/output"));
    }
    let mut devices = Vec::new();
    for index in [0, 2, 3, 4, separator + 1] {
        let id = fs::metadata(&args[index])?.rdev();
        if devices.contains(&id) {
            return Err(error("All five camera endpoints must be distinct"));
        }
        devices.push(id);
    }
    if let Some(path) = sof {
        let id = fs::metadata(path)?.rdev();
        if devices.contains(&id) && id != fs::metadata(&args[4])?.rdev() {
            return Err(error(
                "SOF endpoint cannot alias image, parameter or raw endpoints",
            ));
        }
    }
    let bridge =
        raw_bridge::Bridge::prepare(&args[2], &args[3], &args[4], sof, step)?.observe_ae(observer);
    let mut combined = args[..2].to_vec();
    combined.extend_from_slice(&args[separator..]);
    capture_with_parameters_controlled(&combined, Some(bridge), control)
}
fn capture_with_parameters(args: &[String]) -> io::Result<()> {
    capture_with_parameters_using(args, None)
}
fn capture_with_parameters_using(
    args: &[String],
    raw: Option<raw_bridge::Bridge>,
) -> io::Result<()> {
    capture_with_parameters_controlled(args, raw, None)
}
fn capture_with_parameters_controlled(
    args: &[String],
    raw: Option<raw_bridge::Bridge>,
    control: Option<AutomaticCapture>,
) -> io::Result<()> {
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
    submit_parameters_then_with_backend(&parameter_args, |backend, queue| {
        println!(
            "{}",
            json!({"event":"image-capture-starting","parameterQueueHeldOpen":true,"device":image[0],"output":image[1],"coldStartProven":false})
        );
        io::stdout().flush()?;
        let outcome = if let Some(mut control) = control {
            use shieldsigner_rkaiq::isp32;
            let base = isp32::AWB_GAIN_OFFSET;
            let gain = |offset| {
                u16::from_le_bytes(
                    control.initial_parameters[base + offset..base + offset + 2]
                        .try_into()
                        .unwrap(),
                ) as f32
                    / 256.
            };
            let fixed_wb = isp32::WhiteBalanceGain {
                red: gain(6),
                green_red: gain(2),
                green_blue: gain(0),
                blue: gain(4),
                position: isp32::ApplyPosition::Gain1,
            };
            let awb_output = control.statistics_output.clone();
            let observer = Some(control.sender);
            let result = control.owner.during_capture_with_wb(
                backend,
                queue,
                &control.events,
                Some(fixed_wb),
                move |cancel| {
                    statistics_session::during_observed_cancelable(
                        &control.statistics_node,
                        &control.statistics_output,
                        &control.initial_parameters,
                        control.target,
                        observer,
                        Some(cancel),
                        || match raw {
                            Some(bridge) => bridge.during_cancelable(
                                || capture_cancelable(&capture_args, false, Some(cancel)),
                                Some(cancel),
                            ),
                            None => capture_cancelable(&capture_args, false, Some(cancel)),
                        },
                    )
                },
            );
            let result = result.and_then(|()| match control.owner.awb.as_ref() {
                Some(awb) if awb.last.is_none() && camera_stream_cancelled() => {
                    println!("{}", json!({"event":"automatic-awb-cancelled","processedStatistics":0}));
                    Ok(())
                }
                Some(awb) => awb.save(&awb_output),
                None => Ok(()),
            });
            println!(
                "{}",
                json!({"event":"automatic-ae-finished","success":result.is_ok(),"error":result.as_ref().err().map(|e|e.to_string()),"processedStatistics":control.owner.processed,"parameterSnapshots":control.owner.parameters.len(),"maxParameterSnapshots":control.owner.max_parameter_history,"parameterSubmissions":control.owner.parameter_submissions,"retiredParameterSnapshots":control.owner.retired_parameters,"sensorTraceLimit":CAMERA_TRACE_LIMIT,"lastSof":control.owner.last_sof,"lastSofTimestampNs":control.owner.last_sof_timestamp_ns,"sensorWrites":control.owner.sensor.writes,"sensorQueries":control.owner.sensor.queries,"automaticWhiteBalance":control.owner.awb.is_some(),"physicalApplicationVerified":false})
            );
            result
        } else {
            match raw {
                Some(bridge) => bridge.during(|| capture(&capture_args, false)),
                None => capture(&capture_args, false),
            }
        };
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
    submit_parameters_then_with_backend(args, |_, _| after_ready())
}
fn submit_parameters_then_with_backend<
    F: FnOnce(&mut ParameterBackend, &mut parameter::Queue) -> io::Result<()>,
>(
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
        backend.enqueue_payload(&mut queue, &payload)?;
        accepted = true;
        let deadline = Instant::now() + Duration::from_millis(timeout);
        loop {
            let fd = backend
                .file
                .as_ref()
                .ok_or_else(|| error("Parameter device is closed"))?
                .as_raw_fd();
            wait_parameter(fd, deadline)?;
            if let Some(record) = backend.try_complete(&mut queue)? {
                completed = Some(record);
                break;
            }
        }
        println!(
            "{}",
            json!({"event":"parameters-dequeued","frameApplicationVerified":false,"holdMs":hold,"completion":completed})
        );
        io::stdout().flush()?;
        after_ready(&mut backend, &mut queue)?;
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
        json!({"event":"finished","success":failure.is_none(),"error":failure,"device":args[0],"parameterFile":args[1],"parameterFrameId":get32(&payload,24),"payloadBytes":payload.len(),"parameterQueued":accepted,"frameApplicationVerified":false,"coldStartProven":false,"completion":completed,"holdMs":hold,"bufferCount":backend.requested,"cleanupErrors":backend.cleanup_errors,"dequeueWouldBlockCount":backend.dequeue_would_block,"calls":backend.calls,"callTraceLimit":CAMERA_TRACE_LIMIT})
    );
    match failure {
        Some(e) => Err(error(e)),
        None => Ok(()),
    }
}

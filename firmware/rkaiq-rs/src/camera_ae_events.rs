// Included in camera-probe's Linux module. Owned events cross worker boundaries;
// the event consumer below owns the AE runtime and sensor together.
#[derive(Debug)]
enum CameraAeEvent {
    Sof { frame: u32, timestamp_ns: u64 },
    Statistics { bytes: Vec<u8> },
}
type CameraAeSender = std::sync::mpsc::SyncSender<CameraAeEvent>;
fn emit_camera_ae_event(sender: &Option<CameraAeSender>, event: CameraAeEvent) -> io::Result<()> {
    if let Some(sender) = sender {
        sender.try_send(event).map_err(|e| match e {
            std::sync::mpsc::TrySendError::Full(_) => {
                error("AE event owner fell behind; event queue is full")
            }
            std::sync::mpsc::TrySendError::Disconnected(_) => error("AE event owner disconnected"),
        })?;
    }
    Ok(())
}

/// Single-threaded event consumer. The caller retains parameter queue ownership
/// and submits ISP batches for the returned processed-statistics outputs.
struct CameraAeOwner<B: shieldsigner_rkaiq::sensor::Backend> {
    runtime: shieldsigner_rkaiq::ae_runtime::Runtime,
    sensor: B,
    parameters: Vec<(u32, [u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES])>,
    last_sof: Option<u32>,
    last_sof_timestamp_ns: Option<u64>,
    last_statistics: Option<u32>,
    pending: std::collections::VecDeque<Vec<u8>>,
    processed: u64,
}
impl<B: shieldsigner_rkaiq::sensor::Backend> CameraAeOwner<B>
where
    B::Error: std::fmt::Debug,
{
    fn new(
        runtime: shieldsigner_rkaiq::ae_runtime::Runtime,
        sensor: B,
        initial_id: u32,
        initial: [u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
    ) -> Self {
        Self {
            runtime,
            sensor,
            parameters: vec![(initial_id, initial)],
            last_sof: None,
            last_sof_timestamp_ns: None,
            last_statistics: None,
            pending: std::collections::VecDeque::new(),
            processed: 0,
        }
    }
    /// Snapshots must represent complete effective translator state. This is an
    /// explicit event-owner input, not native map lifetime/accumulation policy.
    #[cfg(test)]
    fn add_parameters(
        &mut self,
        id: u32,
        bytes: [u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
    ) -> io::Result<()> {
        if self.parameters.len() == 128 || self.parameters.last().is_some_and(|p| p.0 >= id) {
            return Err(error(
                "AE parameter snapshots require increasing unique IDs and at most 128 entries",
            ));
        }
        self.parameters.push((id, bytes));
        Ok(())
    }
    /// Submit one gain-only ISP batch and register complete translator state
    /// under its frame ID. Queue failure cannot advance the snapshot cache.
    /// DQBUF confirms ownership only; statistics still choose their explicit ID.
    fn submit_gain(
        &mut self,
        backend: &mut ParameterBackend,
        queue: &mut parameter::Queue,
        frame: u32,
        white_balance: Option<shieldsigner_rkaiq::isp32::WhiteBalanceGain>,
    ) -> io::Result<Option<usize>> {
        use shieldsigner_rkaiq::isp32;
        // One drain is bounded by the driver's maximum pool size.
        for _ in 0..8 {
            if backend.try_complete(queue)?.is_none() {
                break;
            }
        }
        let mut snapshot = self
            .parameters
            .last()
            .ok_or_else(|| error("No initial AE parameters"))?
            .1;
        let mut cache: [u8; 32] = snapshot[isp32::AWB_GAIN_OFFSET..isp32::AWB_GAIN_OFFSET + 32]
            .try_into()
            .unwrap();
        let mut planned = [0u8; isp32::PARAMETER_BYTES];
        let mut planned_cache = cache;
        self.runtime
            .apply_isp_gain_results(frame, &mut planned, &mut planned_cache, white_balance)
            .map_err(error)?;
        let updates = u64::from_le_bytes(planned[..8].try_into().unwrap())
            | u64::from_le_bytes(planned[16..24].try_into().unwrap());
        if updates == 0 {
            return Ok(None);
        }
        if self.parameters.len() == 128 || self.parameters.last().is_some_and(|p| p.0 >= frame) {
            return Err(error("Gain batch requires a new increasing parameter ID"));
        }
        let Some((index, _)) =
            backend.enqueue_runtime_gain(queue, &self.runtime, frame, &mut cache, white_balance)?
        else {
            return Err(error("Gain batch changed between planning and enqueue"));
        };
        // Effective translator metadata uses the unscaled converter WB cache,
        // not the ISP-digital-gain-scaled register words submitted to hardware.
        snapshot[isp32::AWB_GAIN_OFFSET..isp32::AWB_GAIN_OFFSET + 32].copy_from_slice(&cache);
        snapshot[24..28].copy_from_slice(&frame.to_le_bytes());
        self.parameters.push((frame, snapshot));
        Ok(Some(index))
    }
    /// Statistics can overtake their SOF producer. Retain at most 16 complete
    /// owned payloads until SOF reaches their frame. Never guess a future map.
    /// Regressions/duplicates in statistics and regressing SOFs are errors.
    fn handle(
        &mut self,
        event: CameraAeEvent,
    ) -> io::Result<Vec<shieldsigner_rkaiq::ae_session::StatisticsOutput>> {
        match event {
            CameraAeEvent::Sof {
                frame,
                timestamp_ns,
            } => {
                if self.last_sof.is_some_and(|old| frame < old) {
                    return Err(error("Regressing AE SOF frame"));
                }
                let out = self.runtime.on_sof(frame, &mut self.sensor);
                if let Some(e) = out.driver_error {
                    return Err(error(format!("AE sensor writer: {e:?}")));
                }
                if out.scheduled.status != 0 {
                    return Err(error(format!(
                        "AE SOF scheduling: {}",
                        out.scheduled.status
                    )));
                }
                self.last_sof = Some(frame);
                self.last_sof_timestamp_ns = Some(timestamp_ns);
            }
            CameraAeEvent::Statistics { bytes } => {
                let stats = shieldsigner_rkaiq::statistics::Statistics::parse(&bytes)
                    .map_err(|_| error("Invalid AE statistics payload"))?;
                let frame = stats.frame_id();
                if self.last_statistics.is_some_and(|old| frame <= old) {
                    return Err(error("Duplicate or regressing AE statistics frame"));
                }
                if self.pending.len() == 16 {
                    return Err(error("AE statistics are too far ahead of SOF"));
                }
                self.last_statistics = Some(frame);
                self.pending.push_back(bytes);
            }
        }
        let mut results = Vec::new();
        while let Some(bytes) = self.pending.front() {
            let stats = shieldsigner_rkaiq::statistics::Statistics::parse(bytes)
                .map_err(|_| error("Invalid pending AE statistics"))?;
            if !self.last_sof.is_some_and(|frame| frame >= stats.frame_id()) {
                break;
            }
            let bytes = self.pending.pop_front().unwrap();
            let parameters = self
                .parameters
                .iter()
                .map(
                    |(id, bytes)| shieldsigner_rkaiq::ae_session::ParameterSnapshot {
                        id: *id,
                        bytes,
                    },
                )
                .collect::<Vec<_>>();
            if let Some(out) = self
                .runtime
                .step_statistics(&bytes, &parameters)
                .map_err(error)?
            {
                self.processed += 1;
                // Report the owner's snapshot-associated metric, rather than
                // the statistics worker's initial-snapshot diagnostic metric.
                let decision = out.control.frame.control.map(|c| {
                    json!({"timeSeconds":c.point.time,"analogueGain":c.point.gain,
                        "ispGain":c.point.isp_gain,"relativeError":c.relative_error,
                        "held":c.held})
                });
                println!("{}", json!({"event":"automatic-ae-statistics",
                    "frame":out.frame,"parametersId":out.parameters,
                    "exposureFrame":out.exposure_frame,"exactExposureLookup":out.exact_exposure,
                    "meanQ8":out.mean_q8,"run":out.control.frame.run,
                    "preprocessingError":out.control.frame.preprocessing_error,
                    "decision":decision,"physicalApplicationVerified":false}));
                results.push(out);
            }
        }
        Ok(results)
    }
    fn finish(&self) -> io::Result<()> {
        if !self.pending.is_empty() {
            return Err(error("AE stopped with statistics awaiting SOF"));
        }
        Ok(())
    }
}

impl<B: shieldsigner_rkaiq::sensor::Backend> CameraAeOwner<B>
where
    B::Error: std::fmt::Debug,
{
    /// Keep all controller/device/parameter ownership on this thread while a
    /// bounded capture task emits events. Capture must honor cancellation or
    /// its own finite deadlines; no worker is detached on any failure.
    #[cfg(test)]
    fn during_capture<F>(
        &mut self,
        backend: &mut ParameterBackend,
        queue: &mut parameter::Queue,
        events: &std::sync::mpsc::Receiver<CameraAeEvent>,
        capture: F,
    ) -> io::Result<()>
    where
        F: FnOnce(&std::sync::atomic::AtomicBool) -> io::Result<()> + Send,
    {
        self.during_capture_with_wb(backend, queue, events, None, capture)
    }
    fn during_capture_with_wb<F>(
        &mut self,
        backend: &mut ParameterBackend,
        queue: &mut parameter::Queue,
        events: &std::sync::mpsc::Receiver<CameraAeEvent>,
        fixed_wb: Option<shieldsigner_rkaiq::isp32::WhiteBalanceGain>,
        capture: F,
    ) -> io::Result<()>
    where
        F: FnOnce(&std::sync::atomic::AtomicBool) -> io::Result<()> + Send,
    {
        use std::sync::{
            atomic::{AtomicBool, Ordering},
            mpsc::{RecvTimeoutError, TryRecvError},
        };
        let cancel = AtomicBool::new(false);
        std::thread::scope(|scope| {
            let worker = scope.spawn(|| capture(&cancel));
            let mut progress = Instant::now();
            let mut shutdown_events = 0;
            let control = (|| {
                loop {
                    let event = if worker.is_finished() {
                        match events.try_recv() {
                            Ok(event) => {
                                shutdown_events += 1;
                                if shutdown_events > 64 {
                                    return Err(error(
                                        "AE producers did not quiesce after capture completion",
                                    ));
                                }
                                Some(event)
                            }
                            Err(TryRecvError::Empty | TryRecvError::Disconnected) => break,
                        }
                    } else {
                        match events.recv_timeout(Duration::from_millis(10)) {
                            Ok(event) => Some(event),
                            Err(RecvTimeoutError::Timeout) => None,
                            // Last sender can disappear just before the scoped
                            // task becomes is_finished(). Treat producer EOF as
                            // shutdown, then cancel/join capture and check pending
                            // statistics; do not race it into a spurious failure.
                            Err(RecvTimeoutError::Disconnected) => break,
                        }
                    };
                    if let Some(event) = event {
                        let processed = self.handle(event)?;
                        for output in processed {
                            // Frame zero already has the initial parameter ID.
                            if output.frame != 0 {
                                self.submit_gain(backend, queue, output.frame, fixed_wb)?;
                            }
                        }
                        progress = Instant::now();
                    } else {
                        for _ in 0..8 {
                            if backend.try_complete(queue)?.is_none() {
                                break;
                            }
                        }
                        if progress.elapsed() > Duration::from_secs(10) {
                            return Err(error("AE capture received no events for 10 seconds"));
                        }
                    }
                }
                self.finish()
            })();
            cancel.store(true, Ordering::Release);
            let captured = worker
                .join()
                .map_err(|_| error("AE capture task panicked"))?;
            control.and(captured)
        })
    }
}

/// Signal worker shutdown even when a scoped capture callback unwinds.
struct CameraStopGuard<'a>(&'a std::sync::atomic::AtomicBool);
impl Drop for CameraStopGuard<'_> {
    fn drop(&mut self) {
        self.0.store(true, std::sync::atomic::Ordering::Release);
    }
}

struct AutomaticCapture {
    owner: CameraAeOwner<SensorDevice>,
    events: std::sync::mpsc::Receiver<CameraAeEvent>,
    sender: CameraAeSender,
    statistics_node: String,
    statistics_output: String,
    initial_parameters: [u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
    target: f32,
}

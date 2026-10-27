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

/// Persistent AWB beside the AE owner, including FAST-to-normal scheduling.
/// Each successful submission registers its own effective measurement record.
struct CameraAwb {
    session: shieldsigner_rkaiq::awb_session::Session,
    sdk: [u8; shieldsigner_rkaiq::isp_awb_measurement::INPUT_BYTES],
    last_iso: Option<f32>,
    gains: Vec<(
        u32,
        shieldsigner_rkaiq::isp32::WhiteBalanceGain,
        Option<[u8; shieldsigner_rkaiq::isp_awb_measurement::INPUT_BYTES]>,
    )>,
    measurements: Vec<(
        u32,
        [u8; shieldsigner_rkaiq::isp_awb_measurement::INPUT_BYTES],
    )>,
    processed: u64,
    last: Option<(u32, u32, Vec<u8>)>,
}
impl CameraAwb {
    fn step(
        &mut self,
        bytes: &[u8],
        ae_pre: &shieldsigner_rkaiq::ae_preprocess::Standard,
    ) -> io::Result<()> {
        use shieldsigner_rkaiq::{
            awb_preparation::FRAME_BYTES, awb_translation::*, isp32, statistics::Statistics,
        };
        let stats = Statistics::parse(bytes).map_err(|_| error("Invalid live AWB statistics"))?;
        if ae_pre.frame < 0 || ae_pre.frame as u32 != stats.frame_id() {
            return Err(error(
                "AE pre-result does not match the AWB statistics frame",
            ));
        }
        // Decode only against SDK records registered after successful QBUF.
        // Old group configurations remain available while their frames arrive.
        let snapshots: Vec<_> = self
            .measurements
            .iter()
            .map(|(id, measurement)| Snapshot {
                id: *id,
                measurement,
            })
            .collect();
        let mut frame = [0; FRAME_BYTES];
        let mut destination = Destination {
            frame: &mut frame,
            valid: false,
            frame_info_valid: false,
            frame_id: 0,
            proxy_sequence: 0,
        };
        let outcome = translate_associated(&stats, &snapshots, &mut destination)
            .map_err(|e| error(format!("Live AWB association: {e:?}")))?;
        let mut next_measurement = None;
        if outcome == Outcome::Translated {
            let real_gain = |offset| {
                f32::from_le_bytes(ae_pre.exposure[offset..offset + 4].try_into().unwrap())
            };
            let iso = shieldsigner_rkaiq::awb_exposure::linear_iso([
                real_gain(4),
                real_gain(8),
                real_gain(12),
            ])
            .map_err(|e| error(format!("Live AWB ISO: {e:?}")))?;
            let result = self
                .session
                .process(
                    &frame,
                    &shieldsigner_rkaiq::awb_session::Input {
                        requested_update: self.processed == 0,
                        exposure_luma: Some([ae_pre.normalized_brightness, 0.]),
                        iso,
                        site_reference: None,
                    },
                )
                .map_err(|e| error(format!("Live AWB session: {e:?}")))?;
            if result.action.reconfigure && stats.frame_id() != 0 {
                let mut record = self
                    .gains
                    .iter()
                    .rev()
                    .find_map(|(_, _, record)| *record)
                    .unwrap_or(self.sdk);
                let mut signature = [0u8; 64];
                let name = b"RUST-AWB-NORMAL";
                signature[..name.len()].copy_from_slice(name);
                self.session
                    .next_measurement(&mut record, &signature)
                    .map_err(|e| error(format!("AWB next measurement: {e:?}")))?;
                next_measurement = Some(record);
            }
            self.last_iso = Some(iso);
            self.processed += 1;
            self.last = Some((stats.frame_id(), stats.parameters_id(), frame.to_vec()));
            println!(
                "{}",
                json!({"event":"automatic-awb-statistics","frame":stats.frame_id(),"parametersId":stats.parameters_id(),"gain":result.current_gain,"calculated":result.action.calculated,"controllerFrame":result.controller_frame,"countdown":result.countdown,"region":result.region,"retained":result.retained,"complete":result.complete,"activeLights":result.active_lights,"group":i32::from_le_bytes(frame[0x1d78..0x1d7c].try_into().unwrap()),"physicalLights":frame[0x1d74],"exposureMetadata":"same-frame-AE-normalized-brightness","aeNormalizedBrightness":ae_pre.normalized_brightness,"brightness":result.numeric.luma,"iso":iso,"isoSource":"same-frame-associated-real-gains","measurementConfiguration":"FAST-to-normal-timeshare"})
            );
        }
        let g = self.session.gain();
        if self.gains.len() == 128 {
            return Err(error("Live AWB gain history limit reached"));
        }
        self.gains.push((
            stats.frame_id(),
            isp32::WhiteBalanceGain {
                red: g[0],
                green_red: g[1],
                green_blue: g[2],
                blue: g[3],
                position: isp32::ApplyPosition::Gain1,
            },
            next_measurement,
        ));
        Ok(())
    }
    fn gain_for(&self, frame: u32) -> io::Result<shieldsigner_rkaiq::isp32::WhiteBalanceGain> {
        self.gains
            .iter()
            .find(|(id, _, _)| *id == frame)
            .map(|(_, g, _)| *g)
            .ok_or_else(|| error("Missing exact-frame AWB gain"))
    }
    fn measurement_for(
        &self,
        frame: u32,
    ) -> Option<[u8; shieldsigner_rkaiq::isp_awb_measurement::INPUT_BYTES]> {
        self.gains
            .iter()
            .find(|(id, _, _)| *id == frame)
            .and_then(|(_, _, record)| *record)
    }
    fn register(
        &mut self,
        id: u32,
        record: [u8; shieldsigner_rkaiq::isp_awb_measurement::INPUT_BYTES],
    ) {
        self.measurements.push((id, record));
        self.sdk = record;
    }
    fn save(&self, statistics_output: &str) -> io::Result<()> {
        let (frame, id, bytes) = self
            .last
            .as_ref()
            .ok_or_else(|| error("No valid live AWB measurements"))?;
        let base = statistics_output
            .strip_suffix(".stats.raw")
            .ok_or_else(|| error("Invalid AWB output basename"))?;
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(format!("{base}.awb-translated.bin"))?;
        file.write_all(bytes)?;
        let effective = self
            .measurements
            .iter()
            .find(|(registered, _)| registered == id)
            .ok_or_else(|| error("Missing saved AWB configuration"))?;
        let mut sdk_file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(format!("{base}.awb-effective-sdk.bin"))?;
        sdk_file.write_all(&effective.1)?;
        let report = json!({"event":"automatic-awb-finished","processedStatistics":self.processed,"frameId":frame,"parametersId":id,"association":"exact-registered-measurement-snapshot","gain":self.session.gain(),"automaticWhiteBalance":true,"measurementConfiguration":"FAST-to-normal-timeshare","exposureMetadata":"same-frame-AE-normalized-brightness","isoInput":self.last_iso,"isoSource":"same-frame-associated-real-gains","coldStartProven":false});
        let mut sidecar = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(format!("{base}.awb-translated.json"))?;
        serde_json::to_writer_pretty(&mut sidecar, &report).map_err(|e| error(e.to_string()))?;
        println!("{report}");
        Ok(())
    }
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
    awb: Option<CameraAwb>,
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
            awb: None,
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
    /// Submit a gain/optional measurement batch and register translator state
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
        let measurement = self.awb.as_ref().and_then(|awb| awb.measurement_for(frame));
        if let Some(record) = measurement {
            shieldsigner_rkaiq::isp_awb_measurement::Measurement(record).apply(&mut planned, true);
        }
        let updates = u64::from_le_bytes(planned[..8].try_into().unwrap())
            | u64::from_le_bytes(planned[16..24].try_into().unwrap());
        if updates == 0 {
            return Ok(None);
        }
        if self.parameters.len() == 128 || self.parameters.last().is_some_and(|p| p.0 >= frame) {
            return Err(error("Gain batch requires a new increasing parameter ID"));
        }
        let index = if self.awb.is_some() {
            mark_runtime_parameter_frame(&mut planned, frame);
            let index = backend.enqueue_payload(queue, &planned)?;
            cache = planned_cache;
            index
        } else {
            let Some((index, _)) = backend.enqueue_runtime_gain(
                queue,
                &self.runtime,
                frame,
                &mut cache,
                white_balance,
            )?
            else {
                return Err(error("Gain batch changed between planning and enqueue"));
            };
            index
        };
        // Effective translator metadata uses the unscaled converter WB cache,
        // not the ISP-digital-gain-scaled register words submitted to hardware.
        snapshot[isp32::AWB_GAIN_OFFSET..isp32::AWB_GAIN_OFFSET + 32].copy_from_slice(&cache);
        snapshot[24..28].copy_from_slice(&frame.to_le_bytes());
        if let Some(awb) = self.awb.as_mut() {
            let record = measurement.unwrap_or(awb.sdk);
            shieldsigner_rkaiq::isp_awb_measurement::Measurement(record).apply(&mut snapshot, true);
            awb.register(frame, record);
        }
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
                if let Some(awb) = self.awb.as_mut() {
                    awb.step(&bytes, &self.runtime.session.preprocessing)?;
                }
                self.processed += 1;
                // Report the owner's snapshot-associated metric, rather than
                // the statistics worker's initial-snapshot diagnostic metric.
                let decision = out.control.frame.control.map(|c| {
                    json!({"timeSeconds":c.point.time,"analogueGain":c.point.gain,
                        "ispGain":c.point.isp_gain,"relativeError":c.relative_error,
                        "held":c.held})
                });
                println!(
                    "{}",
                    json!({"event":"automatic-ae-statistics",
                    "frame":out.frame,"parametersId":out.parameters,
                    "exposureFrame":out.exposure_frame,"exactExposureLookup":out.exact_exposure,
                    "meanQ8":out.mean_q8,"run":out.control.frame.run,
                    "preprocessingError":out.control.frame.preprocessing_error,
                    "decision":decision,"physicalApplicationVerified":false})
                );
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
                                let wb = match self.awb.as_ref() {
                                    Some(awb) => Some(awb.gain_for(output.frame)?),
                                    None => fixed_wb,
                                };
                                self.submit_gain(backend, queue, output.frame, wb)?;
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

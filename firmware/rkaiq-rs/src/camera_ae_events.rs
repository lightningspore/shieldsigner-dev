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
            last_statistics: None,
            pending: std::collections::VecDeque::new(),
            processed: 0,
        }
    }
    /// Snapshots must represent complete effective translator state. This is an
    /// explicit event-owner input, not native map lifetime/accumulation policy.
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
                timestamp_ns: _,
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

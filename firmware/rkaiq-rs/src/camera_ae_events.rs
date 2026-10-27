// Included in camera-probe's Linux module. Owned events cross worker boundaries;
// a future event owner owns the AE runtime, sensor and parameter queue together.
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

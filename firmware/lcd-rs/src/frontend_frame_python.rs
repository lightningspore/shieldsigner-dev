use crate::frontend_frame::{Format, Frame};
use crate::frontend_receiver::Receiver;
use pyo3::exceptions::{PyOSError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::os::fd::{BorrowedFd, RawFd};
use std::sync::Arc;
use std::time::Duration;
#[pyclass(module = "shieldsigner_lcd", frozen)]
pub struct NativeFrame {
    pub frame: Arc<Frame>,
}
#[pymethods]
impl NativeFrame {
    #[getter]
    fn size(&self) -> (usize, usize) {
        (self.frame.width, self.frame.height)
    }
    #[getter]
    fn sequence(&self) -> u32 {
        self.frame.sequence
    }
    #[getter]
    fn format(&self) -> &'static str {
        match self.frame.format {
            Format::Nv12 => "nv12",
            Format::Rgb => "rgb",
        }
    }
    fn pixel_bytes<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        PyBytes::new(py, &self.frame.pixels)
    }
    // Compatibility/export API; production QR/preview will borrow the native
    // frame instead, avoiding this full-frame Python allocation.
    fn luma_bytes<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        if self.frame.format != Format::Nv12 {
            return Err(PyValueError::new_err("Luma requires NV12"));
        }
        Ok(PyBytes::new(
            py,
            &self.frame.pixels[..self.frame.width * self.frame.height],
        ))
    }
}
#[pyclass(module = "shieldsigner_lcd")]
pub struct FrameReceiver {
    receiver: Receiver,
}
#[pymethods]
impl FrameReceiver {
    #[new]
    #[pyo3(signature=(fd,width=640,height=480,format="nv12",frame_timeout=3.0,framerate=6.0))]
    fn new(
        fd: RawFd,
        width: usize,
        height: usize,
        format: &str,
        frame_timeout: f64,
        framerate: f64,
    ) -> PyResult<Self> {
        if fd < 0
            || !frame_timeout.is_finite()
            || frame_timeout <= 0.0
            || frame_timeout > 30.0
            || !framerate.is_finite()
            || framerate <= 0.0
            || framerate > 120.0
        {
            return Err(PyValueError::new_err("Invalid fd, timeout or frame rate"));
        }
        let format = match format {
            "nv12" => Format::Nv12,
            "rgb" => Format::Rgb,
            _ => return Err(PyValueError::new_err("Unknown frame format")),
        };
        // Python owns a live fd for the duration of this call. Duplicate it with
        // CLOEXEC: closing the receiver never closes the caller's descriptor.
        let owned = unsafe { BorrowedFd::borrow_raw(fd) }
            .try_clone_to_owned()
            .map_err(|e| PyOSError::new_err(e.to_string()))?;
        let receiver = Receiver::start(
            owned.into(),
            width,
            height,
            format,
            Duration::from_secs_f64(frame_timeout),
            Duration::from_secs_f64(1.0 / framerate),
        )
        .map_err(|e| PyOSError::new_err(e.to_string()))?;
        Ok(Self { receiver })
    }
    #[pyo3(signature=(consumer,timeout=0.2))]
    fn read(&self, py: Python<'_>, consumer: usize, timeout: f64) -> PyResult<Option<NativeFrame>> {
        if !timeout.is_finite() || !(0.0..=1.0).contains(&timeout) {
            return Err(PyValueError::new_err("Read timeout outside [0,1]"));
        }
        py.allow_threads(|| {
            self.receiver
                .read(consumer, Duration::from_secs_f64(timeout))
        })
        .map(|frame| frame.map(|frame| NativeFrame { frame }))
        .map_err(|e| {
            if e.kind() == std::io::ErrorKind::InvalidData {
                PyValueError::new_err(e.to_string())
            } else {
                PyOSError::new_err(e.to_string())
            }
        })
    }
    fn close(&self, py: Python<'_>) -> PyResult<()> {
        py.allow_threads(|| self.receiver.close())
            .map_err(|e| PyOSError::new_err(e.to_string()))
    }
    fn statistics(&self, py: Python<'_>) -> (u64, u64, bool) {
        py.allow_threads(|| self.receiver.statistics())
    }
}

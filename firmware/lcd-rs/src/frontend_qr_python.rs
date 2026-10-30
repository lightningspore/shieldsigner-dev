use crate::frontend_qr;
use pyo3::exceptions::{PyOSError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::path::Path;
use std::sync::Mutex;
use std::time::Duration;

#[pyclass(module = "shieldsigner_lcd")]
pub struct QrWorker {
    worker: Mutex<frontend_qr::Worker>,
}

#[pymethods]
impl QrWorker {
    #[new]
    #[pyo3(signature = (binary, timeout=5.0))]
    fn new(binary: &str, timeout: f64) -> PyResult<Self> {
        if !timeout.is_finite() || timeout <= 0.0 || timeout > 30.0 {
            return Err(PyValueError::new_err("QR timeout outside (0,30] seconds"));
        }
        let worker = frontend_qr::Worker::new(Path::new(binary), Duration::from_secs_f64(timeout))
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(Self {
            worker: Mutex::new(worker),
        })
    }

    fn decode_frame<'py>(
        &self,
        py: Python<'py>,
        frame: &crate::frontend_frame_python::NativeFrame,
    ) -> PyResult<Option<Bound<'py, PyBytes>>> {
        let frame = &frame.frame;
        if frame.format != crate::frontend_frame::Format::Nv12 {
            return Err(PyValueError::new_err("Native QR requires NV12"));
        }
        let payload = py
            .allow_threads(|| {
                self.worker
                    .lock()
                    .map_err(|_| {
                        std::io::Error::new(std::io::ErrorKind::Other, "QR worker mutex poisoned")
                    })?
                    .decode(
                        &frame.pixels[..frame.width * frame.height],
                        frame.width,
                        frame.height,
                    )
            })
            .map_err(|e| PyOSError::new_err(e.to_string()))?;
        Ok(payload.map(|data| PyBytes::new(py, &data)))
    }

    fn decode_luma<'py>(
        &self,
        py: Python<'py>,
        pixels: &Bound<'py, PyBytes>,
        width: usize,
        height: usize,
    ) -> PyResult<Option<Bound<'py, PyBytes>>> {
        let pixels = pixels.as_bytes();
        frontend_qr::validate_image(pixels, width, height)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        let payload = py
            .allow_threads(|| {
                self.worker
                    .lock()
                    .map_err(|_| {
                        std::io::Error::new(std::io::ErrorKind::Other, "QR worker mutex poisoned")
                    })?
                    .decode(pixels, width, height)
            })
            .map_err(|e| PyOSError::new_err(e.to_string()))?;
        Ok(payload.map(|data| PyBytes::new(py, &data)))
    }

    fn close(&self, py: Python<'_>) -> PyResult<()> {
        py.allow_threads(|| {
            self.worker
                .lock()
                .map_err(|_| {
                    std::io::Error::new(std::io::ErrorKind::Other, "QR worker mutex poisoned")
                })?
                .close()
        })
        .map_err(|e| PyOSError::new_err(e.to_string()))
    }

    fn statistics(&self) -> PyResult<(u64, u64, u64, u64, Option<f64>, Option<i32>)> {
        let worker = self
            .worker
            .try_lock()
            .map_err(|_| PyRuntimeError::new_err("QR worker busy"))?;
        let s = &worker.statistics;
        Ok((
            s.starts,
            s.calls,
            s.decoded,
            s.errors,
            s.last_seconds,
            s.last_exit_code,
        ))
    }

    #[getter]
    fn worker_pid(&self) -> PyResult<Option<u32>> {
        let worker = self
            .worker
            .try_lock()
            .map_err(|_| PyRuntimeError::new_err("QR worker busy"))?;
        Ok(worker.pid())
    }
}

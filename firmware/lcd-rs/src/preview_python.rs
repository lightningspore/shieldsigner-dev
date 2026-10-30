use crate::preview::luma_preview_into;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::sync::Mutex;

#[pyclass(module = "shieldsigner_lcd")]
pub struct PreviewRenderer {
    width: usize,
    height: usize,
    pixels: Mutex<Vec<u8>>,
}

#[pymethods]
impl PreviewRenderer {
    #[new]
    #[pyo3(signature = (width=240, height=180))]
    fn new(width: usize, height: usize) -> PyResult<Self> {
        if width == 0 || height == 0 || width > 320 || height > 320 {
            return Err(PyValueError::new_err("Preview geometry outside 1..320"));
        }
        Ok(Self {
            width,
            height,
            pixels: Mutex::new(vec![0; width * height * 3]),
        })
    }

    #[getter]
    fn buffer_bytes(&self) -> usize {
        self.width * self.height * 3
    }

    #[cfg(unix)]
    fn render_frame<'py>(
        &self,
        py: Python<'py>,
        frame: &crate::frontend_frame_python::NativeFrame,
        rotation: u16,
    ) -> PyResult<(usize, usize, Bound<'py, PyBytes>)> {
        let frame = &frame.frame;
        if frame.format != crate::frontend_frame::Format::Nv12 {
            return Err(PyValueError::new_err("Native preview requires NV12"));
        }
        let mut pixels = self
            .pixels
            .try_lock()
            .map_err(|_| PyRuntimeError::new_err("Preview renderer busy"))?;
        let target = pixels.as_mut_slice();
        let (dw, dh) = py
            .allow_threads(|| {
                luma_preview_into(
                    &frame.pixels[..frame.width * frame.height],
                    frame.width,
                    frame.height,
                    self.width,
                    self.height,
                    rotation,
                    target,
                )
            })
            .map_err(PyValueError::new_err)?;
        Ok((dw, dh, PyBytes::new(py, &pixels)))
    }

    fn render_luma<'py>(
        &self,
        py: Python<'py>,
        y: &Bound<'py, PyBytes>,
        width: usize,
        height: usize,
        rotation: u16,
    ) -> PyResult<(usize, usize, Bound<'py, PyBytes>)> {
        let y = y.as_bytes();
        let mut pixels = self
            .pixels
            .try_lock()
            .map_err(|_| PyRuntimeError::new_err("Preview renderer busy"))?;
        let target = pixels.as_mut_slice();
        let (dw, dh) = py
            .allow_threads(|| {
                luma_preview_into(y, width, height, self.width, self.height, rotation, target)
            })
            .map_err(PyValueError::new_err)?;
        Ok((dw, dh, PyBytes::new(py, &pixels)))
    }
}

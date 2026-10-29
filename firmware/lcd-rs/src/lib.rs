//! Bounded RGB888 -> ST7789 big-endian RGB565 frame transport.
//! GPIO/register initialization remains in the reviewed Python driver initially.
use std::io;

pub fn rgb565_into(rgb: &[u8], out: &mut [u8]) -> Result<(), &'static str> {
    if rgb.len() % 3 != 0 || out.len() != rgb.len() / 3 * 2 {
        return Err("RGB888/RGB565 lengths disagree");
    }
    for (pixel, dest) in rgb.chunks_exact(3).zip(out.chunks_exact_mut(2)) {
        let word = ((pixel[0] as u16 & 0xf8) << 8)
            | ((pixel[1] as u16 & 0xfc) << 3)
            | (pixel[2] as u16 >> 3);
        dest.copy_from_slice(&word.to_be_bytes());
    }
    Ok(())
}

/// Transfer chunks once, reducing only EMSGSIZE before retrying the same bytes.
/// Other errors/short transfers fail; uncertain hardware writes are not replayed.
pub fn transfer_chunks(
    data: &[u8],
    chunk: &mut usize,
    mut send: impl FnMut(&[u8]) -> io::Result<usize>,
) -> io::Result<()> {
    let mut offset = 0;
    while offset < data.len() {
        let size = (*chunk).min(data.len() - offset);
        if size == 0 {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "Zero SPI chunk",
            ));
        }
        match send(&data[offset..offset + size]) {
            Ok(n) if n == size => offset += n,
            Ok(_) => {
                return Err(io::Error::new(
                    io::ErrorKind::WriteZero,
                    "Short SPI message; frame incomplete",
                ))
            }
            Err(error) if error.raw_os_error() == Some(90) && *chunk > 256 => {
                *chunk = (*chunk / 2).max(256)
            }
            Err(error) => return Err(error),
        }
    }
    Ok(())
}

#[cfg(feature = "python")]
mod python {
    use super::*;
    use pyo3::exceptions::{PyOSError, PyRuntimeError, PyValueError};
    use pyo3::prelude::*;
    use pyo3::types::PyBytes;
    use std::fs::File;
    use std::os::fd::{AsRawFd, FromRawFd};
    use std::sync::Mutex;

    // Linux UAPI spi_ioc_transfer: fixed 32-byte layout on ARM32 and ARM64.
    #[repr(C)]
    #[derive(Default)]
    struct Transfer {
        tx_buf: u64,
        rx_buf: u64,
        len: u32,
        speed_hz: u32,
        delay_usecs: u16,
        bits_per_word: u8,
        cs_change: u8,
        tx_nbits: u8,
        rx_nbits: u8,
        word_delay_usecs: u8,
        pad: u8,
    }
    const _: [(); 32] = [(); std::mem::size_of::<Transfer>()];

    struct State {
        file: File,
        pixels: Vec<u8>,
        chunk: usize,
    }
    #[pyclass]
    struct FrameWriter {
        state: Mutex<State>,
        rgb_bytes: usize,
    }
    #[pymethods]
    impl FrameWriter {
        #[new]
        fn new(fd: i32, width: usize, height: usize) -> PyResult<Self> {
            if width == 0 || height == 0 || width > 320 || height > 320 {
                return Err(PyValueError::new_err("LCD geometry outside 1..320"));
            }
            // Duplicate, never take ownership of Python's existing SPI fd.
            let duplicate = unsafe { libc::fcntl(fd, libc::F_DUPFD_CLOEXEC, 0) };
            if duplicate < 0 {
                return Err(PyOSError::new_err(io::Error::last_os_error().to_string()));
            }
            Ok(Self {
                state: Mutex::new(State {
                    file: unsafe { File::from_raw_fd(duplicate) },
                    pixels: vec![0; width * height * 2],
                    chunk: 4096,
                }),
                rgb_bytes: width * height * 3,
            })
        }
        fn write_rgb(&self, py: Python<'_>, rgb: &Bound<'_, PyBytes>) -> PyResult<()> {
            let rgb = rgb.as_bytes();
            if rgb.len() != self.rgb_bytes {
                return Err(PyValueError::new_err(
                    "RGB byte count must match display geometry",
                ));
            }
            // Fail concurrent use instead of waiting for a mutex with the GIL
            // held while its current owner needs to reattach to Python.
            let mut state = self
                .state
                .try_lock()
                .map_err(|_| PyRuntimeError::new_err("LCD frame writer busy"))?;
            let state = &mut *state;
            py.allow_threads(|| {
                let State {
                    file,
                    pixels,
                    chunk,
                } = state;
                rgb565_into(rgb, pixels)
                    .map_err(|s| io::Error::new(io::ErrorKind::InvalidInput, s))?;
                transfer_chunks(pixels, chunk, |bytes| spi_message(file.as_raw_fd(), bytes))
            })
            .map_err(|e| PyOSError::new_err(e.to_string()))
        }
        fn clear_white(&self, py: Python<'_>) -> PyResult<()> {
            let mut state = self
                .state
                .try_lock()
                .map_err(|_| PyRuntimeError::new_err("LCD frame writer busy"))?;
            let state = &mut *state;
            py.allow_threads(|| {
                let State {
                    file,
                    pixels,
                    chunk,
                } = state;
                pixels.fill(255);
                transfer_chunks(pixels, chunk, |bytes| spi_message(file.as_raw_fd(), bytes))
            })
            .map_err(|e| PyOSError::new_err(e.to_string()))
        }
    }
    #[cfg(target_os = "linux")]
    fn spi_message(fd: i32, bytes: &[u8]) -> io::Result<usize> {
        let transfer = Transfer {
            tx_buf: bytes.as_ptr() as u64,
            len: bytes.len() as u32,
            ..Default::default()
        };
        // SPI_IOC_MESSAGE(1), _IOW('k',0,struct spi_ioc_transfer).
        let result = unsafe { libc::ioctl(fd, 0x40206b00u32 as libc::c_ulong, &transfer) };
        if result < 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(result as usize)
        }
    }
    #[cfg(not(target_os = "linux"))]
    fn spi_message(_: i32, _: &[u8]) -> io::Result<usize> {
        Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "Linux spidev required",
        ))
    }
    #[pyfunction]
    fn pack_rgb<'py>(py: Python<'py>, rgb: &[u8]) -> PyResult<Bound<'py, PyBytes>> {
        if rgb.len() % 3 != 0 {
            return Err(PyValueError::new_err(
                "RGB888 length must be divisible by three",
            ));
        }
        let mut out = vec![0; rgb.len() / 3 * 2];
        py.allow_threads(|| rgb565_into(rgb, &mut out))
            .map_err(PyValueError::new_err)?;
        Ok(PyBytes::new(py, &out))
    }
    #[pymodule]
    fn shieldsigner_lcd(module: &Bound<'_, PyModule>) -> PyResult<()> {
        module.add_class::<FrameWriter>()?;
        module.add_function(wrap_pyfunction!(pack_rgb, module)?)?;
        Ok(())
    }
    #[test]
    fn spi_layout() {
        assert_eq!(std::mem::size_of::<Transfer>(), 32);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn primary_colors_and_wire_order() {
        let mut out = [0; 12];
        rgb565_into(
            &[
                255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255, 0, 0, 0, 255, 128, 16,
            ],
            &mut out,
        )
        .unwrap();
        assert_eq!(out, [0xf8, 0, 7, 0xe0, 0, 0x1f, 255, 255, 0, 0, 0xfc, 2]);
    }
    #[test]
    fn all_channel_values() {
        for v in 0..=255u16 {
            let mut out = [0; 2];
            rgb565_into(&[v as u8, v as u8, v as u8], &mut out).unwrap();
            assert_eq!(
                u16::from_be_bytes(out),
                ((v >> 3) << 11) | ((v >> 2) << 5) | (v >> 3)
            );
        }
    }
    #[test]
    fn bad_sizes_fail() {
        assert!(rgb565_into(&[1, 2], &mut [0; 2]).is_err());
        assert!(rgb565_into(&[1, 2, 3], &mut [0; 3]).is_err());
    }
    #[test]
    fn emsgsize_retries_same_bytes_only() {
        let mut chunk = 4096;
        let data = vec![7; 5000];
        let mut delivered = Vec::new();
        transfer_chunks(&data, &mut chunk, |part| {
            if part.len() > 512 {
                return Err(io::Error::from_raw_os_error(90));
            }
            delivered.extend_from_slice(part);
            Ok(part.len())
        })
        .unwrap();
        assert_eq!(chunk, 512);
        assert_eq!(delivered, data);
    }
    #[test]
    fn arbitrary_errors_and_short_messages_never_replay() {
        for short in [false, true] {
            let mut calls = 0;
            assert!(transfer_chunks(&[1; 10], &mut 4096, |_| {
                calls += 1;
                if short {
                    Ok(3)
                } else {
                    Err(io::Error::from_raw_os_error(5))
                }
            })
            .is_err());
            assert_eq!(calls, 1);
        }
    }
}

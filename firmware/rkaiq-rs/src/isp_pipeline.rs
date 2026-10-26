//! Recovered setupPipelineFmtIsp orchestration. A live backend and the rest of
//! prepare/start, links, calibration and parameter queues remain unfinished.
pub const FORMAT_BYTES: usize = 88;
pub const SELECTION_BYTES: usize = 64;
pub type Format = [u8; FORMAT_BYTES];
pub type Selection = [u8; SELECTION_BYTES];
#[derive(Clone, Copy, Debug)]
pub struct Configuration {
    pub shared_cif: bool,
    pub shared_capture_first: bool,
    pub scaler: bool,
    pub pixel_format: u32,
}
/// Method results preserve native i32 status values. Raw-stream and scaler
/// results are deliberately ignored by this native orchestration function.
pub trait Backend {
    fn set_tx_format(&mut self, format: &Format, pixel_format: u32);
    fn set_rx_format(&mut self, format: &Format, pixel_format: u32);
    fn bits_per_pixel(&mut self, pixel_format: u32) -> i8;
    fn set_scaler_format(&mut self, selection: &Selection, pixel_format: u32, bits: i8);
    fn get_format(&mut self, which: u32, pad: u32, output: &mut Format) -> i32;
    fn set_format(&mut self, format: &mut Format) -> i32;
    fn set_selection(&mut self, selection: &mut Selection) -> i32;
}
fn word(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap())
}
fn put(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
/// Sensor format/crop inputs are opaque native UAPI records so that fields not
/// changed by the original routine survive get/set round trips byte for byte.
pub fn setup<B: Backend>(
    backend: &mut B,
    config: Configuration,
    sensor: &Format,
    crop: &Selection,
) -> i32 {
    if !config.shared_cif || config.shared_capture_first {
        backend.set_tx_format(sensor, config.pixel_format);
    }
    backend.set_rx_format(sensor, config.pixel_format);
    if config.scaler {
        let bits = backend.bits_per_pixel(config.pixel_format);
        backend.set_scaler_format(crop, config.pixel_format, bits);
    }
    let mut format = [0; FORMAT_BYTES];
    let mut status = backend.get_format(1, 0, &mut format);
    if status != 0 {
        return status;
    }
    format[8..20].copy_from_slice(&sensor[8..20]);
    status = backend.set_format(&mut format);
    if status != 0 {
        return status;
    }
    let mut selection = [0; SELECTION_BYTES];
    put(&mut selection, 0, 1); // ACTIVE; pad 0, CROP target, no flags.
    selection[16..32].copy_from_slice(&crop[16..32]);
    status = backend.set_selection(&mut selection);
    if status != 0 {
        return status;
    }
    put(&mut selection, 4, 2); // ISP output pad, zero origin.
    put(&mut selection, 8, 0); // Reset CROP target after possible driver adjustment.
    selection[24..32].copy_from_slice(&crop[24..32]);
    put(&mut selection, 16, 0);
    put(&mut selection, 20, 0);
    status = backend.set_selection(&mut selection);
    if status != 0 {
        return status;
    }
    status = backend.get_format(1, 2, &mut format);
    if status != 0 {
        return status;
    }
    put(&mut format, 8, word(&selection, 24));
    put(&mut format, 12, word(&selection, 28));
    backend.set_format(&mut format)
}

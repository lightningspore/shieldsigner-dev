//! AecHwConfig (ELF 0xa7730): geometry/source selection and uniform HW weights.
//! Calibration loading, default record initialization and later grid weighting
//! are separate stages; this alone must not enable an automatic controller.
use crate::InvalidInput;
pub const RECORD_BYTES: usize = 104 + 529;
const BASE: usize = 0x1d3c;
#[derive(Clone, Copy, Debug)]
pub struct Geometry {
    pub width: u32,
    pub height: u32,
    /// Horizontal/vertical offsets then width/height, as calibrated fractions.
    pub input: [f32; 4],
    pub tone_mapped: [f32; 4],
}
fn window(g: Geometry, scale: [f32; 4]) -> [u16; 4] {
    core::array::from_fn(|i| {
        let dimension = if i % 2 == 0 { g.width } else { g.height };
        let value = dimension as f32 * scale[i];
        if value > 0. {
            (value as i32) as u16
        } else {
            0
        }
    })
}
fn put_window(record: &mut [u8; RECORD_BYTES], offset: usize, values: [u16; 4]) {
    for (i, value) in values.iter().enumerate() {
        record[offset - BASE + i * 2..offset - BASE + i * 2 + 2]
            .copy_from_slice(&value.to_le_bytes());
    }
}
/// Mutate only fields written by the native routine. Mode 0 is linear; modes
/// 0x11/0x12 are accepted by the original but use its alternate routing branch.
/// Returns the source selections mirrored into native context 0x1fb8/0x1fbc.
pub fn configure(
    record: &mut [u8; RECORD_BYTES],
    geometry: Geometry,
    mode: i32,
) -> Result<[u32; 2], InvalidInput> {
    if !matches!(mode, 0 | 0x11 | 0x12) {
        return Err(InvalidInput::Exposure);
    }
    if geometry.width == 0
        || geometry.height == 0
        || geometry.width > 65535
        || geometry.height > 65535
    {
        return Err(InvalidInput::Length);
    }
    if geometry
        .input
        .iter()
        .chain(geometry.tone_mapped.iter())
        .any(|v| !v.is_finite() || v.abs() > 16.)
    {
        return Err(InvalidInput::NonFinite);
    }
    let selections = if mode == 0 { [1, 3] } else { [0, 0] };
    record[0x1d3e - BASE] = selections[0] as u8;
    record[0x1d48 - BASE] = selections[0] as u8;
    record[0x1d76 - BASE] = selections[1] as u8;
    let input = window(geometry, geometry.input);
    for offset in [0x1d40, 0x1db0, 0x1d4e, 0x1dda] {
        put_window(record, offset, input);
    }
    record[0x1db8 - BASE..0x1dd1 - BASE].fill(1);
    record[0x1de2 - BASE..0x1ec3 - BASE].fill(1);
    let last = if selections[1] == 3 {
        window(geometry, geometry.tone_mapped)
    } else {
        input
    };
    put_window(record, 0x1d7c, last);
    put_window(record, 0x1ecc, last);
    record[0x1ed4 - BASE..0x1fb5 - BASE].fill(1);
    Ok(selections)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_geometry_rejection_preserves_selected_records() {
        let original = [0x5a; RECORD_BYTES];
        let mut record = original;
        let mut geometry = Geometry {
            width: 2304,
            height: 1296,
            input: [0., 0., 1., 1.],
            tone_mapped: [0., 0., 1., 1.],
        };
        geometry.input[0] = f32::NAN;
        assert!(configure(&mut record, geometry, 0).is_err());
        assert_eq!(record, original);
        geometry.input[0] = 0.;
        assert!(configure(&mut record, geometry, 1).is_err());
        assert_eq!(record, original);
    }
}

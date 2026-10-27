//! Extra-region include weights from ConfigIncludeWei, ELF 0xc1d78.
use crate::{awb_probability::Curve, interpolate, isp_awb_measurement::INPUT_BYTES, InvalidInput};
pub struct Region<'a> {
    pub mode: u32,
    pub domain: u32,
    pub coordinates: [i32; 4],
    pub weight: Curve<'a>,
}
/// Construct native zero-initialized calibration region records, including the
/// four physical extra-region measurement enables. Whole startup composition
/// and the hardware-update gate belong to the caller.
pub fn initialize(
    record: &mut [u8; INPUT_BYTES],
    regions: &[Region<'_>; 7],
) -> Result<(), InvalidInput> {
    let mut next = [0u8; 196];
    for (i, r) in regions.iter().enumerate() {
        if r.domain > 1 || !matches!(r.mode, 1 | 3) {
            return Err(InvalidInput::UnsupportedRegion);
        }
        let at = i * 28;
        next[at..at + 4].copy_from_slice(&r.domain.to_le_bytes());
        next[at + 4] = u8::from(r.mode == 1);
        next[at + 5] = next[at + 4];
        next[at + 6] = u8::from(i < 4 && r.mode != 1);
        for (j, value) in r.coordinates.iter().enumerate() {
            next[at + 8 + j * 4..at + 12 + j * 4].copy_from_slice(&value.to_le_bytes());
        }
    }
    record[0x284..0x348].copy_from_slice(&next);
    Ok(())
}
/// Mode 3 retains the most recent interpolated mode-1 weight, matching native.
/// If the first region is not mode 1, native reads an uninitialized stack float;
/// reject that configuration instead of inventing a value. Errors are atomic.
pub fn apply_weights(
    record: &mut [u8; INPUT_BYTES],
    regions: &[Region<'_>; 7],
    brightness: f32,
) -> Result<(), InvalidInput> {
    if !brightness.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let mut current = None;
    let mut weights = [0u32; 7];
    for (i, r) in regions.iter().enumerate() {
        if !matches!(r.mode, 1 | 3) {
            return Err(InvalidInput::UnsupportedRegion);
        }
        if r.mode == 1 {
            current = Some(interpolate(r.weight.knots, r.weight.weights, brightness)?);
        }
        let scaled = current.ok_or(InvalidInput::UnsupportedRegion)? * 64.;
        if !scaled.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        weights[i] = ((scaled as f64 + 0.5) as u32).min(63);
    }
    for (i, n) in weights.iter().enumerate() {
        record[0x29c + i * 28..0x2a0 + i * 28].copy_from_slice(&n.to_le_bytes());
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn first_noninterpolating_region_does_not_invent_stack_value() {
        let regions = core::array::from_fn(|_| Region {
            mode: 3,
            domain: 1,
            coordinates: [0; 4],
            weight: Curve {
                knots: &[0.],
                weights: &[0.5],
            },
        });
        let mut record = [0xa5; INPUT_BYTES];
        assert!(apply_weights(&mut record, &regions, 0.).is_err());
        assert_eq!(record, [0xa5; INPUT_BYTES]);
    }
}

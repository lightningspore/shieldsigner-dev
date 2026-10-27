//! Native ReconfigLumaWeight/CalWeight policy with explicit histogram/calibration.
use crate::{interpolate, isp_awb_measurement::INPUT_BYTES, InvalidInput};
pub struct Row<'a> {
    pub brightness: f32,
    pub ratios: &'a [f32],
    pub weights: &'a [[f32; 9]],
}
#[derive(Clone, Copy)]
pub struct Input {
    pub frame_counter: u32,
    pub brightness: u32,
    pub histogram: [i32; 8],
    pub perfect: [bool; 8],
    pub minimum_count: f32,
    pub minimum_brightness: u32,
    pub damping: f32,
}
fn ratio_weights(row: &Row<'_>, ratio: f32) -> Result<[f32; 9], InvalidInput> {
    if row.ratios.is_empty()
        || row.ratios.len() != row.weights.len()
        || row.ratios.iter().any(|x| !x.is_finite())
        || row.ratios.windows(2).any(|p| p[0] >= p[1])
        || row.weights.iter().flatten().any(|x| !x.is_finite())
    {
        return Err(InvalidInput::Length);
    }
    if ratio <= row.ratios[0] {
        return Ok(row.weights[0]);
    }
    let last = row.ratios.len() - 1;
    if ratio >= row.ratios[last] {
        return Ok(row.weights[last]);
    }
    let upper = row
        .ratios
        .iter()
        .position(|x| ratio < *x)
        .ok_or(InvalidInput::Length)?;
    let lower = upper - 1;
    let span = row.ratios[upper] - row.ratios[lower];
    if (span as f64) < 1e-5 {
        return Ok(row.weights[lower]);
    }
    let factor = (ratio - row.ratios[lower]) / span;
    Ok(core::array::from_fn(|i| {
        libm::fmaf(
            factor,
            row.weights[upper][i] - row.weights[lower][i],
            row.weights[lower][i],
        )
    }))
}
/// CalWeight (ELF 0xc829a). The returned flag compares damped bytes with the
/// target bytes, rather than comparing them with the previous output record.
pub fn damp(
    previous: &mut [f32; 9],
    output: &mut [u8; 9],
    target: &[u8; 9],
    damping: f32,
) -> Result<bool, InvalidInput> {
    if !damping.is_finite() || previous.iter().any(|x| !x.is_finite()) {
        return Err(InvalidInput::NonFinite);
    }
    let mut next = [0.; 9];
    let mut bytes = [0; 9];
    for i in 0..9 {
        next[i] = libm::fmaf(previous[i], damping, target[i] as f32 * (1. - damping));
        if !next[i].is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        bytes[i] = ((next[i] as f64 + 0.5) as u32) as u8;
    }
    *previous = next;
    *output = bytes;
    Ok(bytes == *target)
}
/// Returns native target-reached flag. All output/cache writes are staged.
/// Disabled/first-three-frame paths still reset histogram region selection.
pub fn apply(
    record: &mut [u8; INPUT_BYTES],
    previous: &mut [f32; 9],
    rows: &[Row<'_>],
    input: &Input,
) -> Result<bool, InvalidInput> {
    let mut next = *record;
    next[0x35c..0x360].fill(0);
    if input.frame_counter <= 2 || (record[0x2e] == 0 && record[0x2f] == 0) {
        *record = next;
        return Ok(true);
    }
    if !input.minimum_count.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let mut total = 0i32;
    let mut perfect = 0i32;
    for i in 0..8 {
        total = total.wrapping_add(input.histogram[i]);
        if input.perfect[i] {
            perfect = perfect.wrapping_add(input.histogram[i]);
        }
    }
    let mut target = [63; 9];
    if perfect as f32 > input.minimum_count && input.brightness >= input.minimum_brightness {
        if rows.is_empty()
            || rows.iter().any(|r| !r.brightness.is_finite())
            || rows.windows(2).any(|p| p[0].brightness >= p[1].brightness)
        {
            return Err(InvalidInput::Length);
        }
        let ratio = if total == 0 {
            0.
        } else {
            perfect as f32 / total as f32
        };
        // No allocation is needed: select each component at the two levels
        // surrounding brightness using the original generic interpolation.
        let sample = input.brightness as f32;
        let upper = rows
            .iter()
            .position(|r| sample <= r.brightness)
            .unwrap_or(rows.len() - 1);
        let lower = if upper == 0 || sample >= rows[rows.len() - 1].brightness {
            upper
        } else {
            upper - 1
        };
        let first = ratio_weights(&rows[lower], ratio)?;
        let second = ratio_weights(&rows[upper], ratio)?;
        for i in 0..9 {
            let value = if lower == upper {
                first[i]
            } else {
                interpolate(
                    &[rows[lower].brightness, rows[upper].brightness],
                    &[first[i], second[i]],
                    sample,
                )?
            };
            let scaled = value * 63.;
            if !scaled.is_finite() {
                return Err(InvalidInput::NonFinite);
            }
            target[i] = ((scaled as f64 + 0.5) as u32) as u8;
        }
    }
    let mut cache = *previous;
    let mut output = [0; 9];
    let reached = damp(&mut cache, &mut output, &target, input.damping)?;
    next[0x351..0x35a].copy_from_slice(&output);
    *record = next;
    *previous = cache;
    Ok(reached)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn late_damping_failure_preserves_record_and_float_cache() {
        let mut record = [0xa5; INPUT_BYTES];
        record[0x2e] = 1;
        let before = record;
        let mut previous = [63.; 9];
        let input = Input {
            frame_counter: 3,
            brightness: 0,
            histogram: [0; 8],
            perfect: [false; 8],
            minimum_count: 0.,
            minimum_brightness: 0,
            damping: f32::NAN,
        };
        assert!(apply(&mut record, &mut previous, &[], &input).is_err());
        assert_eq!(record, before);
        assert_eq!(previous, [63.; 9]);
    }
    #[test]
    fn target_flag_is_distinct_from_previous_byte_equality() {
        let mut previous = [20.; 9];
        let mut output = [20; 9];
        assert_eq!(damp(&mut previous, &mut output, &[63; 9], 1.), Ok(false));
        assert_eq!(output, [20; 9]);
        assert_eq!(damp(&mut previous, &mut output, &[63; 9], 0.), Ok(true));
        assert_eq!(output, [63; 9]);
    }
}

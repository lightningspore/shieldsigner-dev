//! Geometry/count setup in AwbPrepareV32; calibration and input-bit selection
//! precede this stage. Dimensions are the active ISP input, not output preview.
use crate::InvalidInput;
pub struct Input {
    pub dimensions: [u32; 2],
    pub manual_window: Option<[f32; 4]>,
    pub downsample: u32,
    pub multiwindow: Option<[[f32; 4]; 4]>,
    pub sample_scale: u32,
    pub count_fraction: f32,
    pub luma_weight_fraction: f32,
}
#[derive(Debug, PartialEq)]
pub struct Geometry {
    pub window: [u16; 4],
    pub downsample: u32,
    pub block: [u8; 2],
    pub sampled_dimensions: [u32; 2],
    pub multiwindow: Option<[[u16; 4]; 4]>,
    pub count_threshold: f32,
    pub luma_weight_threshold: f32,
}
fn window(values: &[f32; 4], dimensions: [u32; 2]) -> Result<[u16; 4], InvalidInput> {
    let mut out = [0; 4];
    for i in 0..4 {
        if !values[i].is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        let n = dimensions[i % 2] as f32 * values[i] + 0.5;
        if !n.is_finite() {
            return Err(InvalidInput::NonFinite);
        }
        out[i] = if n > 0. { n as i32 as u16 } else { 0 };
    }
    Ok(out)
}
pub fn derive(input: &Input) -> Result<Geometry, InvalidInput> {
    let [w, h] = input.dimensions;
    if w == 0 || h == 0 || w > u16::MAX as u32 || h > u16::MAX as u32 || input.downsample > 1 {
        return Err(InvalidInput::Length);
    }
    if !input.count_fraction.is_finite() || !input.luma_weight_fraction.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    let area = match input.manual_window {
        Some(values) => window(&values, input.dimensions)?,
        None => [0, 0, w as u16, h as u16],
    };
    if input.manual_window.is_some()
        && (area[0] as u32 + area[2] as u32 > w || area[1] as u32 + area[3] as u32 > h)
    {
        return Err(InvalidInput::Length);
    }
    let downsample = if area[2] > 0x920 { 1 } else { input.downsample };
    let block = if downsample == 0 { [4, 4] } else { [8, 8] };
    let multiwindow = if let Some(values) = input.multiwindow {
        let mut result = [[0; 4]; 4];
        for i in 0..4 {
            result[i] = window(&values[i], input.dimensions)?;
        }
        Some(result)
    } else {
        None
    };
    // Reject signed-integer overflow outside this checked geometry domain.
    let rows = (area[2] as u32)
        .checked_mul(input.sample_scale)
        .ok_or(InvalidInput::Length)?
        / block[0] as u32;
    let samples = rows
        .checked_mul(area[3] as u32)
        .filter(|n| *n <= i32::MAX as u32)
        .ok_or(InvalidInput::Length)?
        / block[1] as u32;
    let count_threshold = samples as f32 * input.count_fraction;
    let luma_weight_threshold =
        ((((area[2] as f32 * input.luma_weight_fraction) / block[0] as f32) * area[3] as f32)
            / block[1] as f32)
            * input.sample_scale as f32;
    if !count_threshold.is_finite() || !luma_weight_threshold.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    Ok(Geometry {
        window: area,
        downsample,
        block,
        sampled_dimensions: [
            area[2] as u32 / block[0] as u32,
            area[3] as u32 / block[1] as u32,
        ],
        multiwindow,
        count_threshold,
        luma_weight_threshold,
    })
}
impl Geometry {
    pub fn apply(&self, record: &mut [u8; crate::isp_awb_measurement::INPUT_BYTES]) {
        record[0x34..0x38].copy_from_slice(&self.downsample.to_le_bytes());
        for (i, n) in self.window.iter().enumerate() {
            record[0x40 + i * 2..0x42 + i * 2].copy_from_slice(&n.to_le_bytes());
        }
        if let Some(windows) = self.multiwindow {
            record[0x3d] = 1;
            for (i, n) in windows.iter().flatten().enumerate() {
                record[0x264 + i * 2..0x266 + i * 2].copy_from_slice(&n.to_le_bytes());
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn width_override_and_partial_record_writes() {
        let mut input = Input {
            dimensions: [2336, 1296],
            manual_window: None,
            downsample: 0,
            multiwindow: None,
            sample_scale: 1,
            count_fraction: 0.0031,
            luma_weight_fraction: 0.004,
        };
        assert_eq!(derive(&input).unwrap().block, [4, 4]);
        input.dimensions[0] += 1;
        let result = derive(&input).unwrap();
        assert_eq!(result.block, [8, 8]);
        let mut record = [0xa5; crate::isp_awb_measurement::INPUT_BYTES];
        result.apply(&mut record);
        for (i, byte) in record.iter().enumerate() {
            if !(0x34..0x38).contains(&i) && !(0x40..0x48).contains(&i) {
                assert_eq!(*byte, 0xa5);
            }
        }
        input.manual_window = Some([0.8, 0., 0.5, 1.]);
        assert!(derive(&input).is_err());
        input.manual_window = Some([0., 0., f32::NAN, 1.]);
        assert!(derive(&input).is_err());
    }
}

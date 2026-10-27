//! ConfigHwParaTimeShare (ELF 0xc9240): select calibrated physical light slots.
//! Calibration loading and the outer hardware-update decision remain external.
use crate::{isp_awb_measurement::INPUT_BYTES, InvalidInput};
#[derive(Clone, Copy)]
pub struct Group {
    pub count: u8,
    pub indices: [u32; 7],
    pub rt_yuv: [bool; 7],
}
/// Fresh zero-reserved AwbTimeShareInit table. Nonzero reserved-light policy
/// remains separate; the ordinary pinned profile initializes that byte to zero.
#[derive(Clone, Copy)]
pub struct Schedule {
    pub groups: [Group; 4],
    pub count: usize,
}
pub fn initialize(total: u8, capacity: u8) -> Result<Schedule, InvalidInput> {
    if total == 0 || total > 7 || capacity == 0 || capacity > 4 {
        return Err(InvalidInput::Length);
    }
    let count = (total as usize).div_ceil(capacity as usize);
    if count > 4 {
        return Err(InvalidInput::Length);
    }
    let empty = Group {
        count: 0,
        indices: [0; 7],
        rt_yuv: [false; 7],
    };
    let mut next = Schedule {
        groups: [empty; 4],
        count,
    };
    if total > capacity {
        for group in &mut next.groups[..count] {
            group.indices.fill(15);
        }
    }
    for light in 0..total as usize {
        let group = light / capacity as usize;
        let slot = light % capacity as usize;
        next.groups[group].indices[slot] = light as u32;
        next.groups[group].rt_yuv[slot] = true;
        next.groups[group].count += 1;
    }
    Ok(next)
}
pub struct Strategy<'a> {
    pub groups: &'a [Group],
    pub signature: &'a [u8; 64],
    /// None preserves startup/default selectors; Some(false) disables all.
    pub xy_detection: Option<bool>,
}
pub struct Calibration<'a> {
    pub uv_enabled: u16,
    pub yuv_enabled: u16,
    pub capacity: u8,
    pub rt_yuv: &'a [[u8; 32]],
    pub uv: &'a [[u8; 36]],
    pub xy: &'a [[u8; 48]],
}
fn word(b: &[u8], o: usize) -> u32 {
    u32::from_le_bytes(b[o..o + 4].try_into().unwrap())
}
fn put16(b: &mut [u8], o: usize, v: u16) {
    b[o..o + 2].copy_from_slice(&v.to_le_bytes());
}
fn put32(b: &mut [u8], o: usize, v: u32) {
    b[o..o + 4].copy_from_slice(&v.to_le_bytes());
}
/// Stage the full SDK record so invalid group/light/name input is atomic.
/// Sentinel 15 occupies a physical slot but does not copy a calibrated region.
pub fn configure(
    record: &mut [u8; INPUT_BYTES],
    calibration: &Calibration<'_>,
    strategy: &Strategy<'_>,
) -> Result<(), InvalidInput> {
    if strategy.groups.is_empty() || strategy.groups.len() > 4 || calibration.capacity > 4 {
        return Err(InvalidInput::Length);
    }
    let end = strategy
        .signature
        .iter()
        .position(|b| *b == 0)
        .ok_or(InvalidInput::Length)?;
    let prior = word(record, 0x450) as i32;
    if prior < -1 || prior >= strategy.groups.len() as i32 {
        return Err(InvalidInput::Length);
    }
    let index = (prior + 1) as usize % strategy.groups.len();
    let group = &strategy.groups[index];
    if group.count > 4 {
        return Err(InvalidInput::Length);
    }
    let mut next = *record;
    if prior == -1 {
        put16(&mut next, 0x20, calibration.uv_enabled);
        put16(&mut next, 0x24, calibration.yuv_enabled);
    }
    if let Some(enabled) = strategy.xy_detection {
        let uv = if enabled { calibration.uv_enabled } else { 0 };
        put16(&mut next, 0x20, uv);
        put16(&mut next, 0x22, uv);
        put16(
            &mut next,
            0x24,
            if enabled { calibration.yuv_enabled } else { 0 },
        );
    }
    next[0x7c..0xfc].fill(0);
    for at in [0x26, 0x28, 0x2a, 0x2c] {
        put16(&mut next, at, 7);
    }
    next[0x464..0x464 + end + 1].copy_from_slice(&strategy.signature[..end + 1]);
    put32(&mut next, 0x450, index as u32);
    next[0x48] = group.count;
    for i in 0..4 {
        put32(&mut next, 0x454 + i * 4, 15);
    }
    let mut regions = 0;
    let mut uv_regions = 0;
    for i in 0..group.count as usize {
        let light = group.indices[i];
        put32(&mut next, 0x454 + i * 4, light);
        if light == 15 || regions >= calibration.capacity as usize {
            continue;
        }
        let light = light as usize;
        let uv = calibration.uv.get(light).ok_or(InvalidInput::Length)?;
        let xy = calibration.xy.get(light).ok_or(InvalidInput::Length)?;
        if group.rt_yuv[i] {
            let rt_yuv = calibration.rt_yuv.get(light).ok_or(InvalidInput::Length)?;
            put16(&mut next, 0x26 + uv_regions * 2, i as u16);
            next[0x7c + uv_regions * 32..0x7c + (uv_regions + 1) * 32].copy_from_slice(rt_yuv);
            uv_regions += 1;
        }
        next[0xfc + regions * 36..0xfc + (regions + 1) * 36].copy_from_slice(uv);
        next[0x1a4 + regions * 48..0x1a4 + (regions + 1) * 48].copy_from_slice(xy);
        regions += 1;
    }
    *record = next;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_light_does_not_partially_change_record() {
        let mut record = [0xa5; INPUT_BYTES];
        put32(&mut record, 0x450, u32::MAX);
        let before = record;
        let mut signature = [0; 64];
        signature[..6].copy_from_slice(b"NORMAL");
        let groups = [Group {
            count: 2,
            indices: [0, 9, 15, 15, 15, 15, 15],
            rt_yuv: [true; 7],
        }];
        let calibration = Calibration {
            uv_enabled: 1,
            yuv_enabled: 1,
            capacity: 4,
            rt_yuv: &[[0; 32]],
            uv: &[[0; 36]],
            xy: &[[0; 48]],
        };
        assert_eq!(
            configure(
                &mut record,
                &calibration,
                &Strategy {
                    groups: &groups,
                    signature: &signature,
                    xy_detection: Some(true),
                }
            ),
            Err(InvalidInput::Length)
        );
        assert_eq!(record, before);
    }
}

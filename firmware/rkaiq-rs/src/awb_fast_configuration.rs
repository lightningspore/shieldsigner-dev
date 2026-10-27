//! ConfigHwParaFstFF (ELF 0xc94a4), including calibrated automatic grouping.
use crate::{isp_awb_measurement::INPUT_BYTES, InvalidInput};
pub enum Mode<'a> {
    Automatic,
    Manual(&'a [[i32; 8]; 4]),
}
#[derive(Debug)]
pub struct Selection {
    pub groups: Option<[[i32; 3]; 4]>,
    pub active: u8,
}
fn word(b: &[u8], at: usize) -> i32 {
    i32::from_le_bytes(b[at..at + 4].try_into().unwrap())
}
fn put(b: &mut [u8], at: usize, n: i32) {
    b[at..at + 4].copy_from_slice(&n.to_le_bytes());
}
fn partition(
    groups: &mut [[i32; 3]; 4],
    start: usize,
    items: &[usize],
    count: usize,
) -> Result<(), InvalidInput> {
    if count == 0 {
        return if items.is_empty() {
            Ok(())
        } else {
            Err(InvalidInput::Length)
        };
    }
    let base = items.len() / count;
    let extra = items.len() % count;
    let mut cursor = 0;
    for i in 0..count {
        let n = base + usize::from(i < extra);
        if n > 3 || start + i >= 4 {
            return Err(InvalidInput::Length);
        }
        for j in 0..n {
            groups[start + i][j] = items[cursor + j] as i32;
        }
        cursor += n;
    }
    Ok(())
}
pub fn configure(
    record: &mut [u8; INPUT_BYTES],
    lights: &[[u8; 48]],
    valid_lights: usize,
    mode: Mode<'_>,
) -> Result<Selection, InvalidInput> {
    let mut next = *record;
    next[0x7c..0xfc].fill(0);
    for i in 0..4 {
        next[0x26 + i * 2..0x28 + i * 2].copy_from_slice(&7u16.to_le_bytes());
        put(&mut next, 0x454 + i * 4, i as i32);
    }
    next[0x464..0x46f].copy_from_slice(b"FASTAWBACT\0");
    let groups = match mode {
        Mode::Manual(regions) => {
            for (i, region) in regions.iter().enumerate() {
                for (j, n) in region.iter().enumerate() {
                    put(&mut next, 0x1a4 + i * 48 + j * 4, *n);
                }
            }
            next[0x48] = 4;
            None
        }
        Mode::Automatic => {
            let n = lights.len();
            if !(4..=7).contains(&n) || valid_lights > n {
                return Err(InvalidInput::Length);
            }
            let mut order = [0usize; 7];
            for (i, index) in order.iter_mut().enumerate() {
                *index = i;
            }
            // Native stable descending bubble sort of normal-region left edge.
            for end in (1..n).rev() {
                for i in 0..end {
                    if word(&lights[order[i]], 0) < word(&lights[order[i + 1]], 0) {
                        order.swap(i, i + 1);
                    }
                }
            }
            let mut closest = None;
            let mut minimum = 8096;
            let mut largest = None;
            let mut largest_distance = i32::MIN;
            for i in 0..n - 1 {
                let a = &lights[order[i]];
                let b = &lights[order[i + 1]];
                let gap = word(a, 0).wrapping_sub(word(b, 0));
                if gap < minimum {
                    minimum = gap;
                    closest = Some(i);
                }
                let distance = word(a, 8)
                    .wrapping_sub(word(b, 8))
                    .wrapping_abs()
                    .wrapping_add(word(a, 12).wrapping_sub(word(b, 12)).wrapping_abs());
                if distance > largest_distance {
                    largest_distance = distance;
                    largest = Some(i);
                }
            }
            let mut groups = [[-1; 3]; 4];
            if closest.is_some() && closest == largest {
                let pair = closest.unwrap();
                let left = pair;
                let right = n - 2 - pair;
                let (left_groups, right_groups) = if left < right {
                    let count = if left == 0 {
                        0
                    } else {
                        ((left / (n - 2)) * 4).max(1)
                    };
                    (count, 3 - count)
                } else {
                    let count = if right == 0 {
                        0
                    } else {
                        ((right / (n - 2)) * 4).max(1)
                    };
                    (3 - count, count)
                };
                partition(&mut groups, 0, &order[..pair], left_groups)?;
                groups[left_groups][0] = order[pair] as i32;
                groups[left_groups][1] = order[pair + 1] as i32;
                partition(
                    &mut groups,
                    left_groups + 1,
                    &order[pair + 2..n],
                    right_groups,
                )?;
            } else {
                partition(&mut groups, 0, &order[..n], 4)?;
            }
            next[0x1a4..0x264].fill(0);
            let mut active = 0;
            for group in &groups {
                let mut any = false;
                let mut bounds = [[8096, -8096, -8096, 8096]; 2];
                for &index in group {
                    if index < 0 || index as usize >= valid_lights {
                        continue;
                    }
                    any = true;
                    for (r, b) in bounds.iter_mut().enumerate() {
                        let l = &lights[index as usize];
                        b[0] = b[0].min(word(l, r * 16));
                        b[1] = b[1].max(word(l, r * 16 + 4));
                        b[2] = b[2].max(word(l, r * 16 + 8));
                        b[3] = b[3].min(word(l, r * 16 + 12));
                    }
                }
                if any {
                    for (r, b) in bounds.iter().enumerate() {
                        for (j, n) in b.iter().enumerate() {
                            put(&mut next, 0x1a4 + active * 48 + r * 16 + j * 4, *n);
                        }
                    }
                    active += 1;
                }
            }
            next[0x48] = active as u8;
            Some(groups)
        }
    };
    let active = next[0x48];
    *record = next;
    Ok(Selection { groups, active })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_light_table_is_atomic_and_manual_preserves_small_ranges() {
        let mut record = [0xa5; INPUT_BYTES];
        assert!(configure(&mut record, &[[0; 48]; 3], 3, Mode::Automatic).is_err());
        assert_eq!(record, [0xa5; INPUT_BYTES]);
        let manual = [[0; 8]; 4];
        configure(&mut record, &[], 0, Mode::Manual(&manual)).unwrap();
        for i in 0..4 {
            assert_eq!(
                &record[0x1a4 + i * 48 + 32..0x1a4 + (i + 1) * 48],
                &[0xa5; 16]
            );
        }
    }
}

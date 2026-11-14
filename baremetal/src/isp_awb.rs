// SPDX-License-Identifier: MIT
//! Original packed-parameter→ISP32 map for normal AWB time-share transitions.
//! Layout/register facts: pinned SDK UAPI and regs_v3x.h. No kernel code linked.
pub const MAX_WRITES: usize = 82;
const START: usize = 0xf4;
const END: usize = 0x41b;
fn word(p: &[u8], at: usize) -> u32 {
    u32::from_le_bytes(p[at..at + 4].try_into().unwrap())
}
fn half(p: &[u8], at: usize) -> u32 {
    u16::from_le_bytes(p[at..at + 2].try_into().unwrap()) as u32
}
fn pair(p: &[u8], low: usize, high: usize) -> u32 {
    half(p, low) | half(p, high) << 16
}
pub fn changes(
    old: &[u8; 11145],
    new: &[u8; 11145],
    control: u32,
    output: &mut [(usize, u32); MAX_WRITES],
) -> Result<usize, &'static str> {
    if old[START..END] == new[START..END] {
        return Ok(0);
    }
    // Reject new geometry, routing, thresholds, weights or black-level policy
    // until mapped; only the calibrated time-share fields below are supported.
    for at in START..END {
        let supported = (0xf8..0xff).contains(&at)
            || (0x103..0x107).contains(&at)
            || at == 0x238
            || (0x132..0x14e).contains(&at)
            || (0x25d..0x29d).contains(&at)
            || (0x2af..0x2ef).contains(&at)
            || (0x35f..0x3ff).contains(&at);
        if old[at] != new[at] && !supported {
            return Err("unsupported-awb-measurement-change");
        }
    }
    let mut count = 0;
    let mut push = |offset, value| {
        output[count] = (offset, value);
        count += 1;
    };
    for slot in 0..4 {
        for i in 0..4 {
            push(
                0x5040 + slot * 32 + i * 4,
                word(new, 0x25d + slot * 16 + i * 4),
            );
            push(
                0x5050 + slot * 32 + i * 4,
                word(new, 0x3bf + slot * 16 + i * 4),
            );
        }
        let c = 0x35f + slot * 12;
        let pairs = if slot == 2 {
            [(c, c + 2), (c + 4, c + 10), (c + 8, c + 6)]
        } else {
            [(c, c + 2), (c + 4, c + 6), (c + 8, c + 10)]
        };
        for (i, (low, high)) in pairs.into_iter().enumerate() {
            push(0x5140 + slot * 32 + i * 4, pair(new, low, high));
        }
        let b = 0x132 + slot * 7;
        push(
            0x514c + slot * 32,
            new[b] as u32 | (new[b + 1] as u32) << 16 | (new[b + 2] as u32) << 24,
        );
        push(0x5150 + slot * 32, word(new, b + 3));
        for i in 0..3 {
            push(
                0x5154 + slot * 32 + i * 4,
                word(new, 0x38f + slot * 12 + i * 4),
            );
        }
        for i in 0..2 {
            push(
                0x5210 + slot * 24 + i * 4,
                word(new, 0x2af + slot * 8 + i * 4),
            );
            push(
                0x5218 + slot * 24 + i * 4,
                word(new, 0x2cf + slot * 8 + i * 4),
            );
        }
    }
    let b = |at| u32::from(new[at] != 0);
    push(
        0x5004,
        half(new, 0x23d) << 16
            | b(0x23c) << 8
            | (new[0x23a] as u32 & 7) << 4
            | b(0x239) << 3
            | b(0x238) << 2
            | b(0x237) << 1
            | b(0x236),
    );
    let mut ctrl = control & 0x08800001; // module enable and two DDR-path selectors
    for (field, shift, mask) in [
        (0x107, 28, 1),
        (0x106, 26, 1),
        (0x105, 25, 1),
        (0x104, 24, 1),
        (0x103, 20, 7),
        (0x102, 19, 1),
        (0x101, 18, 1),
        (0x100, 17, 1),
        (0xff, 16, 1),
        (0xfe, 13, 7),
        (0xfd, 10, 7),
        (0xfc, 7, 7),
        (0xfb, 4, 7),
        (0xfa, 3, 1),
        (0xf9, 2, 1),
        (0xf8, 1, 1),
    ] {
        let v = if mask == 1 {
            u32::from(new[field] != 0)
        } else {
            new[field] as u32 & mask
        };
        ctrl |= v << shift;
    }
    push(0x5000, ctrl);
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn normal_secondary_regions_and_block_selector_are_supported() {
        let old=[0;11145];let mut new=old;
        new[0x104]=1;new[0x106]=1;new[0x238]=1;
        let mut out=[(0,0);MAX_WRITES];
        assert_eq!(changes(&old,&new,1,&mut out),Ok(MAX_WRITES));
        assert_eq!(out.iter().find(|(o,_)|*o==0x5000).unwrap().1,0x05000001);
        assert_eq!(out.iter().find(|(o,_)|*o==0x5004).unwrap().1,4);
    }
    #[test]
    fn mapped_values_match_observed_initial_isp_writes() {
        let new = include_bytes!("../.tools/isp-initial-parameters.bin");
        let mut old = *new;
        old[0x103] ^= 1; // force complete encoding of the original configuration
        let mut writes = [(0, 0); MAX_WRITES];
        assert_eq!(changes(&old, new, 1, &mut writes), Ok(MAX_WRITES));
        let mut observed = std::collections::BTreeMap::new();
        for line in include_str!("../logs/phase-8/isp-auto-events.txt")
            .lines()
            .skip(1)
        {
            let f: Vec<_> = line.split_whitespace().collect();
            let address = usize::from_str_radix(&f[4][2..], 16).unwrap();
            let value = u32::from_str_radix(&f[5][2..], 16).unwrap();
            if (0xffa00000..0xffa07f00).contains(&address) {
                observed.insert(address - 0xffa00000, value);
            }
            if address == 0xffa01c00 && value == 0x20820401 {
                break;
            }
        }
        for (offset, value) in writes {
            assert_eq!(observed.get(&offset), Some(&value), "register{offset:#x}");
        }
    }
    #[test]
    fn unsupported_field_change_rejects_before_output() {
        let old = [0; 11145];
        let mut new = old;
        new[0x24f] = 2;
        let mut out = [(123, 456); MAX_WRITES];
        assert!(changes(&old, &new, 1, &mut out).is_err());
        assert_eq!(out, [(123, 456); MAX_WRITES]);
    }
}

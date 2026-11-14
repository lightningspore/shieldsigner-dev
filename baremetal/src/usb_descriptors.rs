// SPDX-License-Identifier: MIT
//! USB2 CDC ACM descriptors shared by the controller and host-side contract tests.
const DEVICE: &[u8] = &[
    18, 1, 0, 2, 0xef, 2, 1, 64, 0x09, 0x12, 0x03, 0x00, 0, 1, 1, 2, 3, 1,
];
const CONFIG: &[u8] = &[
    9, 2, 75, 0, 2, 1, 0, 0x80, 50, 8, 11, 0, 2, 2, 2, 1, 0, 9, 4, 0, 0, 1, 2, 2, 1, 0, 5, 0x24, 0,
    0x10, 1, 5, 0x24, 1, 0, 1, 4, 0x24, 2, 2, 5, 0x24, 6, 0, 1, 7, 5, 0x81, 3, 16, 0, 16, 9, 4, 1,
    0, 2, 0x0a, 0, 0, 0, 7, 5, 2, 2, 0, 2, 0, 7, 5, 0x82, 2, 0, 2, 0,
];
/// Populate the complete descriptor; caller truncates to setup.wLength.
/// Other-speed configuration describes full-speed bulk64, even though initial
/// controller bring-up currently rejects a non-high-speed connection.
pub fn descriptor(value: u16, out: &mut [u8; 128]) -> Option<usize> {
    let index = (value & 255) as u8;
    let bytes: &[u8] = match value >> 8 {
        1 if index == 0 => DEVICE,
        2 | 7 if index == 0 => CONFIG,
        6 if index == 0 => &[10, 6, 0, 2, 0xef, 2, 1, 64, 1, 0],
        3 if index == 0 => &[4, 3, 9, 4],
        3 => {
            let text: &[u8] = match index {
                1 => b"ShieldSigner",
                2 => b"RV1103 USB Console",
                3 => match option_env!("RV1103_USB_SERIAL") { Some(s) => s.as_bytes(), None => b"rv1103-dev-001" },
                _ => return None,
            };
            if text.len() > 48 || !text.is_ascii() { return None; }
            out[0] = (text.len() * 2 + 2) as u8;
            out[1] = 3;
            for (i, c) in text.iter().enumerate() {
                out[2 + i * 2] = *c;
                out[3 + i * 2] = 0;
            }
            return Some(text.len() * 2 + 2);
        }
        _ => return None,
    };
    out[..bytes.len()].copy_from_slice(bytes);
    if value >> 8 == 7 {
        out[1] = 7;
        let mut pos = 0;
        while pos < bytes.len() {
            if out[pos + 1] == 5 && out[pos + 3] == 2 {
                out[pos + 4] = 64;
                out[pos + 5] = 0;
            }
            pos += out[pos] as usize;
        }
    }
    Some(bytes.len())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn configuration_endpoints_match_controller() {
        let mut b = [0; 128];
        let n = descriptor(0x200, &mut b).unwrap();
        assert_eq!(n, u16::from_le_bytes([b[2], b[3]]) as usize);
        let mut p = 0;
        let mut interfaces = 0;
        let mut endpoints = 0;
        while p < n {
            assert!(b[p] >= 2);
            assert!(p + b[p] as usize <= n);
            if b[p + 1] == 4 {
                interfaces += 1;
            }
            if b[p + 1] == 5 {
                let address = b[p + 2];
                let packet = u16::from_le_bytes([b[p + 4], b[p + 5]]);
                match address {
                    0x81 => {
                        assert_eq!(packet, 16);
                        endpoints |= 1;
                    }
                    2 => {
                        assert_eq!(packet, 512);
                        endpoints |= 2;
                    }
                    0x82 => {
                        assert_eq!(packet, 512);
                        endpoints |= 4;
                    }
                    _ => panic!("unexpected endpoint"),
                }
            }
            p += b[p] as usize;
        }
        assert_eq!(p, n);
        assert_eq!(interfaces, b[4]);
        assert_eq!(endpoints, 7);
    }
    #[test]
    fn other_speed_uses_full_speed_packets() {
        let mut b = [0; 128];
        let n = descriptor(0x700, &mut b).unwrap();
        assert_eq!(b[1], 7);
        let mut p = 0;
        while p < n {
            if b[p + 1] == 5 && b[p + 3] == 2 {
                assert_eq!(&b[p + 4..p + 6], &[64, 0]);
            }
            p += b[p] as usize;
        }
    }
    #[test]
    fn strings_are_bounded_utf16_and_indices_are_checked() {
        let mut b = [0xff; 128];
        for i in 1..=3 {
            let n = descriptor(0x300 | i, &mut b).unwrap();
            assert_eq!(n, b[0] as usize);
            assert_eq!(b[1], 3);
            for j in (3..n).step_by(2) {
                assert_eq!(b[j], 0);
            }
        }
        for value in [0x101, 0x201, 0x304, 0x601, 0xf00, 0x701] {
            assert_eq!(descriptor(value, &mut b), None);
        }
    }
}

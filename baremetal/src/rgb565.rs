// SPDX-License-Identifier: MIT
//! Integer limited-range BT.601 NV12 → big-endian RGB565 for app preview.
//! Fixed camera contract640x480; center480x480 crop downsampled to240x240.
pub const FRAME_BYTES: usize = 640 * 480 * 3 / 2;
pub fn pixel(y: u8, u: u8, v: u8) -> u16 {
    let c = y as i32 - 16;
    let d = u as i32 - 128;
    let e = v as i32 - 128;
    let r = ((298 * c + 409 * e + 128) >> 8).clamp(0, 255) as u16;
    let g = ((298 * c - 100 * d - 208 * e + 128) >> 8).clamp(0, 255) as u16;
    let b = ((298 * c + 516 * d + 128) >> 8).clamp(0, 255) as u16;
    ((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3)
}
pub fn center_crop_row(frame: &[u8], row: usize, out: &mut [u8; 480]) -> Result<(), &'static str> {
    if frame.len() != FRAME_BYTES || row >= 240 {
        return Err("nv12-frame-contract");
    }
    for x in 0..240 {
        let source_x = 80 + x * 2;
        let y = frame[row * 2 * 640 + source_x];
        let uv = 640 * 480 + row * 640 + source_x;
        out[x * 2..x * 2 + 2].copy_from_slice(&pixel(y, frame[uv], frame[uv + 1]).to_be_bytes());
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn broadcast_color_vectors_and_saturation() {
        assert_eq!(pixel(16, 128, 128), 0);
        assert_eq!(pixel(235, 128, 128), 0xffff);
        assert_eq!(pixel(81, 90, 240), 0xf800);
        assert_eq!(pixel(145, 54, 34), 0x07e0);
        assert_eq!(pixel(41, 240, 110), 0x001f);
        assert_eq!(pixel(0, 128, 128), 0);
        assert_eq!(pixel(255, 128, 128), 0xffff);
    }
    #[test]
    fn crop_stride_chroma_and_big_endian_match_camera_contract() {
        let mut frame = vec![128; FRAME_BYTES];
        frame[..640 * 480].fill(16);
        frame[0] = 235;
        frame[80] = 235;
        frame[558] = 235;
        frame[478 * 640 + 80] = 235;
        let mut out = [0; 480];
        center_crop_row(&frame, 0, &mut out).unwrap();
        assert_eq!(&out[..4], &[255, 255, 0, 0]);
        assert_eq!(&out[478..], &[255, 255]);
        center_crop_row(&frame, 239, &mut out).unwrap();
        assert_eq!(&out[..2], &[255, 255]);
        assert!(center_crop_row(&frame, 240, &mut out).is_err());
        assert!(center_crop_row(&frame[..FRAME_BYTES - 1], 0, &mut out).is_err());
    }
}

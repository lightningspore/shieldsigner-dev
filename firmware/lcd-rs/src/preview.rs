//! Preview-only nearest resize and expanded orthogonal rotation.
//! Sequential f64 pixel centers match pinned Pillow NEAREST, including tie rounding.
//! Decode/entropy inputs stay full size.

pub fn luma_preview_into(
    y: &[u8],
    width: usize,
    height: usize,
    preview_width: usize,
    preview_height: usize,
    rotation: u16,
    out: &mut [u8],
) -> Result<(usize, usize), &'static str> {
    if width == 0
        || height == 0
        || width > 1920
        || height > 1920
        || width * height > 2_073_600
        || y.len() != width * height
    {
        return Err("Invalid bounded luma geometry");
    }
    if preview_width == 0
        || preview_height == 0
        || preview_width > 320
        || preview_height > 320
        || out.len() != preview_width * preview_height * 3
    {
        return Err("Invalid bounded preview geometry");
    }
    if !matches!(rotation, 0 | 90 | 180 | 270) {
        return Err("Preview rotation must be 0, 90, 180 or 270");
    }
    let (dw, dh) = if rotation == 90 || rotation == 270 {
        (preview_height, preview_width)
    } else {
        (preview_width, preview_height)
    };
    // Pillow ImagingScaleAffine accumulates f64 centers rather than computing
    // each coordinate as an exact rational. Its tie rounding is observable.
    let mut xs = [0usize; 320];
    let mut ys = [0usize; 320];
    let scale_x = width as f64 / preview_width as f64;
    let scale_y = height as f64 / preview_height as f64;
    let mut center_x = scale_x * 0.5;
    let mut center_y = scale_y * 0.5;
    for sample in &mut xs[..preview_width] {
        *sample = (center_x as usize).min(width - 1);
        center_x += scale_x;
    }
    for sample in &mut ys[..preview_height] {
        *sample = (center_y as usize).min(height - 1);
        center_y += scale_y;
    }
    for dy in 0..dh {
        for dx in 0..dw {
            let (px, py) = match rotation {
                90 => (preview_width - 1 - dy, dx),
                180 => (preview_width - 1 - dx, preview_height - 1 - dy),
                270 => (dy, preview_height - 1 - dx),
                _ => (dx, dy),
            };
            let sx = xs[px];
            let sy = ys[py];
            let value = y[sy * width + sx];
            out[(dy * dw + dx) * 3..(dy * dw + dx + 1) * 3].fill(value);
        }
    }
    Ok((dw, dh))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rotations_preserve_all_pixels_and_expanded_geometry() {
        let source = [0, 1, 2, 3, 4, 5, 6, 7];
        for (angle, geometry, expected) in [
            (0, (4, 2), vec![0, 1, 2, 3, 4, 5, 6, 7]),
            (90, (2, 4), vec![3, 7, 2, 6, 1, 5, 0, 4]),
            (180, (4, 2), vec![7, 6, 5, 4, 3, 2, 1, 0]),
            (270, (2, 4), vec![4, 0, 5, 1, 6, 2, 7, 3]),
        ] {
            let mut out = [0; 24];
            assert_eq!(
                luma_preview_into(&source, 4, 2, 4, 2, angle, &mut out).unwrap(),
                geometry
            );
            assert_eq!(
                out.chunks_exact(3).map(|p| p[0]).collect::<Vec<_>>(),
                expected
            );
            assert!(out.chunks_exact(3).all(|p| p[0] == p[1] && p[1] == p[2]));
        }
    }
    #[test]
    fn nearest_uses_pixel_centers_and_does_not_mutate_input() {
        let source = (0..48).collect::<Vec<u8>>();
        let mut out = [0; 36];
        luma_preview_into(&source, 8, 6, 4, 3, 0, &mut out).unwrap();
        assert_eq!(
            out.chunks_exact(3).map(|p| p[0]).collect::<Vec<_>>(),
            [9, 11, 13, 15, 25, 27, 29, 31, 41, 43, 45, 47]
        );
        assert_eq!(source, (0..48).collect::<Vec<u8>>());
    }
    #[test]
    fn invalid_input_fails_before_output_changes() {
        let mut out = [19; 12];
        for (data, w, h, pw, ph, angle) in [
            (&[0u8; 4][..], 0, 2, 2, 2, 0),
            (&[0u8; 3][..], 2, 2, 2, 2, 0),
            (&[0u8; 4][..], 2, 2, 2, 2, 45),
            (&[0u8; 4][..], 2, 2, 0, 2, 0),
        ] {
            assert!(luma_preview_into(data, w, h, pw, ph, angle, &mut out).is_err());
            assert_eq!(out, [19; 12]);
        }
    }
}

//! Convert a supported camera-probe capture into a grayscale PGM for inspection.
//! Bayer uses simple 2×2 binning, not reconstructed vendor demosaic/calibration.
use serde_json::Value;
use std::{
    env,
    fs::{self, OpenOptions},
    io::Write,
};
fn pixel(data: &[u8], stride: usize, x: usize, y: usize, kind: &str) -> Result<u8, String> {
    let row = y.checked_mul(stride).ok_or("Row offset overflow")?;
    let at = |offset: usize| {
        data.get(row + offset)
            .copied()
            .ok_or_else(|| "Truncated frame or inconsistent stride".to_string())
    };
    match kind {
        "NV12" | "NV21" | "NM12" | "NM21" | "YU12" | "YV12" | "GREY" => at(x),
        "YUYV" | "YVYU" => at(x * 2),
        "UYVY" | "VYUY" => at(x * 2 + 1),
        // Rockchip CSI compact memory mode: little-endian contiguous 10-bit
        // samples, with row padding retained. This is not MIPI RAW10 packing.
        "RK10" => {
            let bit = x * 10;
            let byte = bit / 8;
            let word = u16::from_le_bytes([at(byte)?, at(byte + 1)?]);
            Ok((((word >> (bit % 8)) & 1023) >> 2) as u8)
        }
        "BG10" | "GB10" | "BA10" | "RG10" => {
            Ok((u16::from_le_bytes([at(x * 2)?, at(x * 2 + 1)?]) >> 2).min(255) as u8)
        }
        "BG12" | "GB12" | "BA12" | "RG12" => {
            Ok((u16::from_le_bytes([at(x * 2)?, at(x * 2 + 1)?]) >> 4).min(255) as u8)
        }
        "BG16" | "GB16" | "GR16" | "RG16" => {
            Ok((u16::from_le_bytes([at(x * 2)?, at(x * 2 + 1)?]) >> 8) as u8)
        }
        // In V4L2's packed RAW10/12 layout each first byte is the pixel's upper 8
        // bits; low bits occupy the trailing group byte. An 8-bit preview drops them.
        "pBAA" | "pGAA" | "pgAA" | "pRAA" => at((x / 4) * 5 + x % 4),
        "pBCC" | "pGCC" | "pgCC" | "pRCC" => at((x / 2) * 3 + x % 2),
        _ => Err(format!(
            "Unsupported FourCC {kind:?}; preserve raw data and metadata for analysis"
        )),
    }
}
fn bayer(kind: &str) -> bool {
    matches!(
        kind,
        "RK10"
            | "BG10"
            | "GB10"
            | "BA10"
            | "RG10"
            | "BG12"
            | "GB12"
            | "BA12"
            | "RG12"
            | "BG16"
            | "GB16"
            | "GR16"
            | "RG16"
            | "pBAA"
            | "pGAA"
            | "pgAA"
            | "pRAA"
            | "pBCC"
            | "pGCC"
            | "pgCC"
            | "pRCC"
    )
}
fn convert(
    data: &[u8],
    width: usize,
    height: usize,
    stride: usize,
    kind: &str,
) -> Result<(usize, usize, Vec<u8>), String> {
    if width == 0 || height == 0 || width > 16384 || height > 16384 || stride == 0 {
        return Err("Invalid image dimensions or stride".into());
    }
    let minimum = match kind {
        "YUYV" | "YVYU" | "UYVY" | "VYUY" => width * 2,
        "BG10" | "GB10" | "BA10" | "RG10" | "BG12" | "GB12" | "BA12" | "RG12" | "BG16" | "GB16"
        | "GR16" | "RG16" => width * 2,
        "RK10" => (width * 10).div_ceil(8),
        "pBAA" | "pGAA" | "pgAA" | "pRAA" => width.div_ceil(4) * 5,
        "pBCC" | "pGCC" | "pgCC" | "pRCC" => width.div_ceil(2) * 3,
        _ => width,
    };
    if stride < minimum
        || stride
            .checked_mul(height)
            .is_none_or(|size| size > data.len())
    {
        return Err("Frame is shorter than its declared dimensions/stride".into());
    }
    let bin = if bayer(kind) { 2 } else { 1 };
    let w = width / bin;
    let h = height / bin;
    if w == 0 || h == 0 {
        return Err("Frame too small for Bayer binning".into());
    }
    let mut gray = Vec::with_capacity(w * h);
    for y in 0..h {
        for x in 0..w {
            let value = if bin == 1 {
                pixel(data, stride, x, y, kind)? as u16
            } else {
                let (x, y) = (x * 2, y * 2);
                (pixel(data, stride, x, y, kind)? as u16
                    + pixel(data, stride, x + 1, y, kind)? as u16
                    + pixel(data, stride, x, y + 1, kind)? as u16
                    + pixel(data, stride, x + 1, y + 1, kind)? as u16)
                    / 4
            };
            gray.push(value as u8);
        }
    }
    Ok((w, h, gray))
}
fn run() -> Result<(), String> {
    let args: Vec<_> = env::args().skip(1).collect();
    if args.len() != 3 && !(args.len() == 4 && args[3] == "--rockchip-compact-raw10") {
        return Err("Usage: frame-preview RAW RAW.json OUT.pgm [--rockchip-compact-raw10]; supports luma/YUV and common Bayer RAW10/12/16. Bayer is 2×2 binned; output is uncalibrated.".into());
    }
    let raw = fs::read(&args[0]).map_err(|e| e.to_string())?;
    let metadata: Value = serde_json::from_slice(&fs::read(&args[1]).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let get = |v: &Value| {
        v.as_u64()
            .and_then(|n| usize::try_from(n).ok())
            .ok_or_else(|| "Missing/invalid numeric metadata".to_string())
    };
    let width = get(&metadata["format"]["width"])?;
    let height = get(&metadata["format"]["height"])?;
    let stride = get(&metadata["format"]["planes"][0]["bytesPerLine"])?;
    let offset = get(&metadata["planes"][0]["fileOffset"])?;
    let length = get(&metadata["planes"][0]["bytes"])?;
    let plane = raw
        .get(offset..offset.checked_add(length).ok_or("Plane range overflow")?)
        .ok_or("Invalid plane extent")?;
    let kind = metadata["format"]["fourcc"]
        .as_str()
        .ok_or("Missing FourCC")?;
    let kind = if args.len() == 4 {
        if !matches!(kind, "BG10" | "GB10" | "BA10" | "RG10") {
            return Err("Compact RAW10 override requires a RAW10 Bayer FourCC".into());
        }
        "RK10"
    } else {
        kind
    };
    let (w, h, pixels) = convert(plane, width, height, stride, kind)?;
    let mut out = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&args[2])
        .map_err(|e| e.to_string())?;
    write!(out, "P5\n{w} {h}\n255\n").map_err(|e| e.to_string())?;
    out.write_all(&pixels).map_err(|e| e.to_string())?;
    let min = pixels.iter().min().unwrap();
    let max = pixels.iter().max().unwrap();
    let mean = pixels.iter().map(|&x| x as u64).sum::<u64>() as f64 / pixels.len() as f64;
    println!(
        "{}",
        serde_json::json!({"output":args[2],"width":w,"height":h,"minimum":min,"maximum":max,"mean":mean,"bayerBinning":bayer(kind),"calibrated":false,"rockchipCompactRaw10":kind == "RK10"})
    );
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("frame-preview: {e}");
        std::process::exit(1)
    }
}
#[cfg(test)]
mod tests {
    #[test]
    fn rockchip_compact_bits_and_row_padding() {
        // Four 10-bit samples [0, 1, 512, 1023], followed by row padding.
        let row = [0, 4, 0, 224, 255, 123, 123, 123];
        for (x, expected) in [0, 0, 128, 255].into_iter().enumerate() {
            assert_eq!(super::pixel(&row, 8, x, 0, "RK10").unwrap(), expected);
        }
        let data = [row, row].concat();
        assert_eq!(
            super::convert(&data, 4, 2, 8, "RK10").unwrap(),
            (2, 1, vec![0, 191])
        );
        assert!(super::convert(&data[..10], 4, 2, 8, "RK10").is_err());
    }

    use super::*;
    #[test]
    fn respects_y_plane_stride() {
        let data = [1, 2, 99, 99, 3, 4, 99, 99];
        assert_eq!(
            convert(&data, 2, 2, 4, "NV12").unwrap(),
            (2, 2, vec![1, 2, 3, 4])
        );
    }
    #[test]
    fn rejects_truncated_frames() {
        assert!(convert(&[0; 3], 2, 2, 2, "GREY").is_err());
    }
    #[test]
    fn bayer_10_unpacked_binning() {
        let data = [0, 0, 0, 1, 0, 2, 0, 3];
        assert_eq!(convert(&data, 2, 2, 4, "BG10").unwrap(), (1, 1, vec![96]));
    }
    #[test]
    fn packed_bayer_10_drops_group_low_bits() {
        let data = [10, 20, 30, 40, 255, 50, 60, 70, 80, 0];
        assert_eq!(
            convert(&data, 4, 2, 5, "pBAA").unwrap(),
            (2, 1, vec![35, 55])
        );
    }
}

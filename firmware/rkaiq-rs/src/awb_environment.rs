//! AwbCalLV (ELF 0xc9f68): two independent integer brightness classifications.
#[derive(Clone, Copy)]
pub struct Calibration<'a> {
    pub boundaries: &'a [u32],
    pub thresholds: [u32; 4],
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Classification {
    pub level: u32,
    pub environment: i32,
}
/// Unmatched values retain the final interval index, even below the first
/// boundary. With no intervals, the incoming environment value is preserved.
/// The five-level category uses strict threshold comparisons in supplied order.
pub fn classify(luma: u32, calibration: &Calibration<'_>, previous: i32) -> Classification {
    let mut environment = previous;
    for (i, pair) in calibration.boundaries.windows(2).enumerate() {
        environment = i as i32;
        if pair[0] <= luma && luma < pair[1] {
            break;
        }
    }
    let mut level = 1;
    for &threshold in &calibration.thresholds {
        if luma <= threshold {
            break;
        }
        level += 1;
    }
    Classification { level, environment }
}

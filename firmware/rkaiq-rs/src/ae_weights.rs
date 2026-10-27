//! Software mean-luma grid weights selected by AecUpdateConfig, separate from
//! uniform initial hardware histogram weights in AecHwConfig.
use crate::InvalidInput;
/// AecGridWeight15x15to5x5 (ELF 0xa6bf0). Each output is the truncated average
/// of its corresponding 3x3 input block, without rounding or normalization.
pub fn reduce(source: &[u8; 225]) -> [u8; 25] {
    core::array::from_fn(|index| {
        let row = index / 5 * 3;
        let col = index % 5 * 3;
        let mut sum = 0u16;
        for y in 0..3 {
            for x in 0..3 {
                sum += source[(row + y) * 15 + col + x] as u16;
            }
        }
        (sum / 9) as u8
    })
}
/// AecSetMeanLumaGridWeights.constprop.9 (ELF 0xa6e64). The lite path writes
/// only 25 bytes and preserves the remaining destination storage.
pub fn select(
    destination: &mut [u8; 225],
    source: &[u8; 225],
    cells: usize,
) -> Result<(), InvalidInput> {
    match cells {
        25 => destination[..25].copy_from_slice(&reduce(source)),
        225 => destination.copy_from_slice(source),
        _ => return Err(InvalidInput::Length),
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn reduction_truncates_and_selection_preserves_tail() {
        let mut input = [0; 225];
        input[0] = 8;
        assert_eq!(reduce(&input)[0], 0);
        input[0] = 9;
        let mut output = [0xa5; 225];
        select(&mut output, &input, 25).unwrap();
        assert_eq!(output[0], 1);
        assert_eq!(&output[25..], &[0xa5; 200]);
        let before = output;
        assert!(select(&mut output, &input, 24).is_err());
        assert_eq!(output, before);
    }
}

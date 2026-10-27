//! Automatic expert-mode ISO row selection (ELF 0x11b6e0) and basic result copy.
//! Table construction from the IQ profile and fast/manual modes remain separate.
use crate::{isp_dpcc::RESULT_BYTES, InvalidInput};
pub const ROW_BYTES: usize = 108;
pub const ROWS: usize = 13;
pub const TABLE_BYTES: usize = ROW_BYTES * ROWS;

/// Each row starts with a signed ISO and has 103 consumed basic-result bytes.
/// The final row byte is padding. Reject malformed knot order before mutation.
pub fn select(
    table: &[u8; TABLE_BYTES],
    iso: i32,
    result: &mut [u8; RESULT_BYTES],
) -> Result<usize, InvalidInput> {
    let knots: [i32; ROWS] = core::array::from_fn(|i| {
        i32::from_le_bytes(table[i * ROW_BYTES..i * ROW_BYTES + 4].try_into().unwrap())
    });
    if knots.windows(2).any(|p| p[0] >= p[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let selected = knots.iter().rposition(|k| *k <= iso).unwrap_or(0);
    let start = selected * ROW_BYTES + 4;
    result[..103].copy_from_slice(&table[start..start + 103]);
    Ok(selected)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_knots_leave_all_result_bytes_unchanged() {
        let mut result = [0xa5; RESULT_BYTES];
        assert_eq!(
            select(&[0; TABLE_BYTES], 50, &mut result),
            Err(InvalidInput::NonIncreasing)
        );
        assert_eq!(result, [0xa5; RESULT_BYTES]);
    }
}

//! Linear readback trigger selected by RawStreamProcUnit::trigger_isp_readback
//! (ELF 0x35cf0). Buffer transfer and stream ownership are separate prerequisites.
pub const TRIGGER_BYTES: usize = 28;
pub const TRIGGER_IOCTL: u32 = 0x401c56c0;

/// Build the native linear trigger after successfully queueing its raw RX buffer.
/// `frame_timestamp_us` is the source proxy's unsigned 64-bit timestamp; the
/// original converts it to nanoseconds with wrapping multiplication by 1000.
/// Missing SOF-map matches are represented by a zero timestamp by the caller.
pub fn linear_trigger(
    frame_id: u32,
    sof_timestamp_ns: u64,
    frame_timestamp_us: u64,
    detected_times: i32,
    first_trigger: bool,
    multi_isp: bool,
) -> [u8; TRIGGER_BYTES] {
    let mut times = if first_trigger {
        1
    } else {
        detected_times.min(2)
    };
    if multi_isp && times < 1 {
        times = 1;
    }
    let mut bytes = [0; TRIGGER_BYTES];
    bytes[..8].copy_from_slice(&sof_timestamp_ns.to_le_bytes());
    bytes[8..16].copy_from_slice(&frame_timestamp_us.wrapping_mul(1000).to_le_bytes());
    bytes[16..20].copy_from_slice(&frame_id.to_le_bytes());
    bytes[20..24].copy_from_slice(&times.to_le_bytes());
    bytes[24..28].copy_from_slice(&16u32.to_le_bytes());
    bytes
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn first_trigger_and_native_signed_times_rules() {
        let times = |value, first, multi| {
            let b = linear_trigger(7, 11, 13, value, first, multi);
            i32::from_le_bytes(b[20..24].try_into().unwrap())
        };
        assert_eq!(times(-1, false, false), -1);
        assert_eq!(times(-1, false, true), 1);
        assert_eq!(times(9, false, false), 2);
        assert_eq!(times(9, true, false), 1);
    }
    #[test]
    fn timestamp_is_full_width_wrapping_microseconds() {
        let b = linear_trigger(u32::MAX, 0x1122334455667788, u64::MAX, 0, false, false);
        assert_eq!(&b[..8], &0x1122334455667788u64.to_le_bytes());
        assert_eq!(&b[8..16], &u64::MAX.wrapping_mul(1000).to_le_bytes());
        assert_eq!(&b[16..20], &u32::MAX.to_le_bytes());
        assert_eq!(&b[24..], &16u32.to_le_bytes());
    }
}

//! Ordinary single-ISP metadata copies in CamHwIsp32::updateEffParams
//! (ELF 0x39700). Map allocation/lookup and split-ISP merging are external.
pub const RECORD_BYTES: usize = 0xbac0;
pub const AE_CACHE_BYTES: usize = 0x792;
pub const BLC_CACHE_BYTES: usize = 44;
pub const WB_CACHE_BYTES: usize = 32;
pub const AWB_CONFIGURATION_BYTES: usize = 0x4b4;
/// Copy the converter's unscaled caches into an existing effective-map record.
/// This does not copy scaled WB registers from the queued parameter buffer.
/// Missing AWB configuration preserves its previous record bytes, as native.
/// All unrelated fields, including frame/header and full ISP snapshots, remain.
pub fn copy_metadata(
    record: &mut [u8; RECORD_BYTES],
    ae: &[u8; AE_CACHE_BYTES],
    black_level: &[u8; BLC_CACHE_BYTES],
    white_balance: &[u8; WB_CACHE_BYTES],
    awb_configuration: Option<&[u8; AWB_CONFIGURATION_BYTES]>,
) {
    record[0xae2c..0xb5be].copy_from_slice(ae);
    record[0xb5be..0xb5ea].copy_from_slice(black_level);
    record[0xb5ea..0xb60a].copy_from_slice(white_balance);
    if let Some(configuration) = awb_configuration {
        record[0xb60c..0xbac0].copy_from_slice(configuration);
    }
}

//! Full single-ISP RV1106 AWB statistics translation, including effect metadata.
//! Smart-pointer ownership and multi-ISP delegation are outside this value API.
use crate::{
    awb_preparation::FRAME_BYTES, isp_awb_measurement::INPUT_BYTES, statistics::Statistics,
    InvalidInput,
};

fn word(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap())
}
fn put32(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
fn put64(bytes: &mut [u8], offset: usize, value: u64) {
    bytes[offset..offset + 8].copy_from_slice(&value.to_le_bytes());
}

/// Snapshot of the translator's selected AWB measurement configuration. Callers
/// must supply the configuration associated with the statistics they process;
/// this module does not discover or invent frame/configuration correlation.
pub struct Configuration {
    mode: u32,
    light_count: u8,
    group: u32,
    indices: [u32; 4],
    signature: [u8; 64],
    pre_gain: [u32; 4],
}
impl Configuration {
    pub fn from_measurement(record: &[u8; INPUT_BYTES]) -> Result<Self, InvalidInput> {
        if record[0x48] > 4 {
            return Err(InvalidInput::Length);
        }
        Ok(Self {
            mode: word(record, 0x38),
            light_count: record[0x48],
            group: word(record, 0x450),
            indices: core::array::from_fn(|i| word(record, 0x454 + i * 4)),
            signature: record[0x464..0x4a4].try_into().unwrap(),
            pre_gain: core::array::from_fn(|i| word(record, 0x4a4 + i * 4)),
        })
    }
    fn write(&self, frame: &mut [u8; FRAME_BYTES]) {
        let at = 0x1d70;
        put32(frame, at, self.mode);
        frame[at + 4] = self.light_count;
        // Three SDK padding bytes following light_count remain untouched.
        put32(frame, at + 8, self.group);
        for (i, value) in self.indices.iter().enumerate() {
            put32(frame, at + 12 + i * 4, *value);
        }
        frame[at + 28..at + 92].copy_from_slice(&self.signature);
        for (i, value) in self.pre_gain.iter().enumerate() {
            put32(frame, at + 92 + i * 4, *value);
        }
    }
}
pub struct Destination<'a> {
    pub frame: &'a mut [u8; FRAME_BYTES],
    pub valid: bool,
    pub frame_info_valid: bool,
    pub frame_id: u32,
    pub proxy_sequence: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Outcome {
    Translated,
    MissingBuffer,
    InvalidMeasurement,
}
impl Outcome {
    pub fn native_status(self) -> i32 {
        if self == Self::Translated {
            0
        } else {
            1
        }
    }
}

/// translateAwbStats, ELF 0x8818c. Both driver payload lengths accepted by
/// Statistics are supported. Bypass preserves native conditional output writes.
pub fn translate(
    stats: Option<&Statistics<'_>>,
    configuration: &Configuration,
    destination: &mut Destination<'_>,
) -> Outcome {
    let Some(stats) = stats else {
        return Outcome::MissingBuffer;
    };
    destination.valid = stats.measurements() & 0x20 != 0;
    if !destination.valid {
        return Outcome::InvalidMeasurement;
    }
    let source = stats.raw_bytes();
    let frame = &mut *destination.frame;
    put32(
        frame,
        0x1ddc,
        if word(source, 0x2af8) == 2 {
            word(source, 0x2afc)
        } else {
            u32::MAX
        },
    );
    configuration.write(frame);
    for (i, sum) in stats
        .awb_sums()
        .unwrap()
        .take(configuration.light_count as usize)
        .enumerate()
    {
        for (region, count, red, blue) in [
            (0, sum.points_normal, sum.red_normal, sum.blue_normal),
            (1, sum.points_big, sum.red_big, sum.blue_big),
        ] {
            let at = i * 48 + region * 24;
            put64(frame, at, count as u64);
            put64(frame, at + 8, red as u64);
            put64(frame, at + 16, blue as u64);
        }
        put32(frame, 0xc0 + i * 4, sum.points_second);
    }
    frame[0x1de0..0x1e00].fill(0);
    let mut total = [0u64; 3];
    for (i, sample) in stats.awb().unwrap().enumerate() {
        let at = 0xd0 + i * 32;
        put64(frame, at, sample.white_points as u64);
        for (channel, value) in [sample.red, sample.green, sample.blue].iter().enumerate() {
            put64(frame, at + 8 + channel * 8, *value as u64);
            total[channel] += *value as u64;
        }
    }
    // Native global WpNo remains zero; only R/G/B totals accumulate.
    for (i, value) in total.iter().enumerate() {
        put64(frame, 0x1de8 + i * 8, *value);
    }
    for (i, value) in stats.awb_luma_histogram().unwrap().enumerate() {
        put32(frame, 0x1d50 + i * 4, value);
    }
    for i in 0..4 {
        let source_at = 0x32a0 + i * 16;
        let target = 0x1cf0 + i * 24;
        put64(frame, target, word(source, source_at + 8) as u64);
        put64(frame, target + 8, word(source, source_at) as u64);
        put64(frame, target + 16, word(source, source_at + 4) as u64);
    }
    destination.frame_info_valid = true;
    destination.frame_id = stats.frame_id();
    destination.proxy_sequence = stats.frame_id();
    Outcome::Translated
}

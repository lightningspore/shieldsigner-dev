//! Borrowed decoder for the pinned full-ISP32 statistics buffer (RV1106).
//! No calibration, exposure decision or white-balance decision is applied here.
pub const PAYLOAD_BYTES: usize = 13036;
pub const BUFFER_BYTES: usize = 13040;
pub const MEASUREMENT_OFFSET: usize = 0x32e0;
pub const AWB_OFFSET: usize = 0x2b00;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Length,
}
#[derive(Clone, Copy, Debug)]
pub enum Channel {
    Ae0,
    Ae1,
    Ae2,
    Ae3,
}
impl Channel {
    fn index(self) -> usize {
        match self {
            Self::Ae0 => 0,
            Self::Ae1 => 1,
            Self::Ae2 => 2,
            Self::Ae3 => 3,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AeSample {
    pub red: u16,
    pub green: u16,
    pub blue: u16,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AwbSample {
    pub red: u32,
    pub green: u32,
    pub blue: u32,
    pub white_points: u16,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AwbSum {
    pub red_normal: u32,
    pub blue_normal: u32,
    pub points_normal: u32,
    pub points_second: u32,
    pub red_big: u32,
    pub blue_big: u32,
    pub points_big: u32,
}
fn word(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap())
}
pub fn ae_sample(packed: u32) -> AeSample {
    AeSample {
        green: (packed & 0xfff) as u16,
        blue: ((packed >> 12) & 0x3ff) as u16,
        red: (packed >> 22) as u16,
    }
}
pub fn awb_sample(packed: u64) -> AwbSample {
    AwbSample {
        blue: (packed & 0x3ffff) as u32,
        green: ((packed >> 18) & 0x3ffff) as u32,
        red: ((packed >> 36) & 0x3ffff) as u32,
        white_points: (packed >> 54) as u16,
    }
}
pub struct Statistics<'a> {
    bytes: &'a [u8],
}
impl<'a> Statistics<'a> {
    pub(crate) fn raw_bytes(&self) -> &[u8] {
        self.bytes
    }
    /// Accept one packed payload or the driver's one-ISP 16-byte-aligned buffer.
    /// Lite, united/multi-ISP and arbitrary/truncated buffers are unsupported.
    pub fn parse(bytes: &'a [u8]) -> Result<Self, Error> {
        if bytes.len() != PAYLOAD_BYTES && bytes.len() != BUFFER_BYTES {
            return Err(Error::Length);
        }
        Ok(Self { bytes })
    }
    pub fn measurements(&self) -> u32 {
        word(self.bytes, MEASUREMENT_OFFSET)
    }
    pub fn frame_id(&self) -> u32 {
        word(self.bytes, MEASUREMENT_OFFSET + 4)
    }
    pub fn parameters_id(&self) -> u32 {
        word(self.bytes, MEASUREMENT_OFFSET + 8)
    }
    pub fn ae(&self, channel: Channel) -> Option<impl Iterator<Item = AeSample> + '_> {
        let index = channel.index();
        if self.measurements() & (1 << (7 + index)) == 0 {
            return None;
        }
        let offset = [0xab0, 0x390, 0x720, 0][index];
        let count = if index == 0 { 25 } else { 225 };
        Some((0..count).map(move |i| ae_sample(word(self.bytes, offset + i * 4))))
    }
    pub fn histogram(&self, channel: Channel) -> Option<impl Iterator<Item = u32> + '_> {
        let index = channel.index();
        if self.measurements() & (1 << (11 + index)) == 0 {
            return None;
        }
        let offset = [0x1000, 0x1400, 0x1800, 0xc00][index];
        Some((0..256).map(move |i| word(self.bytes, offset + i * 4)))
    }
    pub fn awb(&self) -> Option<impl Iterator<Item = AwbSample> + '_> {
        if self.measurements() & 0x20 == 0 {
            return None;
        }
        Some((0..225).map(move |i| {
            awb_sample(u64::from_le_bytes(
                self.bytes[AWB_OFFSET + i * 8..AWB_OFFSET + i * 8 + 8]
                    .try_into()
                    .unwrap(),
            ))
        }))
    }
    pub fn awb_sums(&self) -> Option<impl Iterator<Item = AwbSum> + '_> {
        if self.measurements() & 0x20 == 0 {
            return None;
        }
        Some((0..4).map(move |i| {
            let at = 0x3210 + i * 32;
            AwbSum {
                red_normal: word(self.bytes, at),
                blue_normal: word(self.bytes, at + 4),
                points_normal: word(self.bytes, at + 8),
                points_second: word(self.bytes, at + 12),
                red_big: word(self.bytes, at + 16),
                blue_big: word(self.bytes, at + 20),
                points_big: word(self.bytes, at + 24),
            }
        }))
    }
    /// Native translator expands the high-bit encoded count by a factor of 8.
    pub fn awb_luma_histogram(&self) -> Option<impl Iterator<Item = u32> + '_> {
        if self.measurements() & 0x20 == 0 {
            return None;
        }
        Some((0..8).map(move |i| {
            let at = 0x3290 + i * 2;
            let value = u16::from_le_bytes(self.bytes[at..at + 2].try_into().unwrap()) as u32;
            if value & 0x8000 != 0 {
                (value & 0x7fff) << 3
            } else {
                value
            }
        }))
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_measurements_are_not_exposed_and_other_layouts_are_rejected() {
        let bytes = [0xff; PAYLOAD_BYTES - 1];
        assert!(matches!(Statistics::parse(&bytes), Err(Error::Length)));
        let bytes = [0; BUFFER_BYTES];
        let stats = Statistics::parse(&bytes).unwrap();
        assert!(stats.ae(Channel::Ae0).is_none());
        assert!(stats.awb().is_none());
        assert!(stats.histogram(Channel::Ae3).is_none());
    }
    #[test]
    fn packed_channels_and_encoded_histogram_preserve_ranges() {
        assert_eq!(
            ae_sample(0xffffffff),
            AeSample {
                red: 1023,
                green: 4095,
                blue: 1023
            }
        );
        assert_eq!(
            awb_sample(u64::MAX),
            AwbSample {
                red: 262143,
                green: 262143,
                blue: 262143,
                white_points: 1023
            }
        );
        let mut bytes = [0; PAYLOAD_BYTES];
        bytes[MEASUREMENT_OFFSET..MEASUREMENT_OFFSET + 4].copy_from_slice(&0x20u32.to_le_bytes());
        bytes[0x3290..0x3292].copy_from_slice(&0x8001u16.to_le_bytes());
        let stats = Statistics::parse(&bytes).unwrap();
        assert_eq!(stats.awb_luma_histogram().unwrap().next(), Some(8));
        assert_eq!(stats.awb().unwrap().count(), 225);
    }
}

//! Recovered SensorHw descriptor reads and arithmetic. All backend operations
//! are reads; the 172-byte native ARM result is serialized explicitly.
pub const BYTES: usize = 172;
pub const HBLANK: u32 = 0x009e0902;
pub const VBLANK: u32 = 0x009e0901;
pub const EXPOSURE: u32 = 0x00980911;
#[derive(Clone, Copy, Debug)]
pub struct Format {
    pub width: u32,
    pub height: u32,
    pub media_bus_code: u32,
}
pub trait Backend {
    type Error;
    fn format(&mut self) -> Result<Format, Self::Error>;
    fn minimum(&mut self, id: u32) -> Result<i32, Self::Error>;
    fn frame_interval(&mut self) -> Result<(u32, u32), Self::Error>;
    fn pixel_rate(&mut self) -> Result<i64, Self::Error>;
    fn nr_switch(&mut self) -> Result<[u32; 4], Self::Error>;
    fn dcg_ratio(&mut self) -> Result<[u32; 3], Self::Error>;
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Descriptor {
    bytes: [u8; BYTES],
}
impl Descriptor {
    fn put(&mut self, at: usize, value: u32) {
        self.bytes[at..at + 4].copy_from_slice(&value.to_le_bytes());
    }
    fn short(&mut self, at: usize, value: u16) {
        self.bytes[at..at + 2].copy_from_slice(&value.to_le_bytes());
    }
    fn word(&self, at: usize) -> u32 {
        u32::from_le_bytes(self.bytes[at..at + 4].try_into().unwrap())
    }
    pub fn bytes(&self) -> &[u8; BYTES] {
        &self.bytes
    }
    pub fn width(&self) -> u32 {
        self.word(32)
    }
    pub fn height(&self) -> u32 {
        self.word(36)
    }
    pub fn pixel_format(&self) -> u32 {
        self.word(40)
    }
    pub fn pixel_clock_mhz(&self) -> f32 {
        f32::from_bits(self.word(24))
    }
    pub fn pixel_periods_per_line(&self) -> u16 {
        u16::from_le_bytes(self.bytes[28..30].try_into().unwrap())
    }
    pub fn line_periods_per_field(&self) -> u16 {
        u16::from_le_bytes(self.bytes[30..32].try_into().unwrap())
    }
    pub fn minimum_integration(&self) -> u16 {
        u16::from_le_bytes(self.bytes[6..8].try_into().unwrap())
    }
    pub fn integration_margin(&self) -> u16 {
        u16::from_le_bytes(self.bytes[8..10].try_into().unwrap())
    }
    pub fn noise_switch(&self) -> Option<[u32; 4]> {
        if self.bytes[52] == 0 {
            None
        } else {
            Some(core::array::from_fn(|i| self.word(56 + i * 4)))
        }
    }
    pub fn conversion_gain_ratio(&self) -> Option<[u32; 3]> {
        if self.bytes[72] == 0 {
            None
        } else {
            Some(core::array::from_fn(|i| self.word(76 + i * 4)))
        }
    }
}
pub fn pixel_format(code: u32) -> u32 {
    let bytes = match code {
        0x2001 => *b"GREY",
        0x200a => *b"Y10 ",
        0x2013 => *b"Y12 ",
        0x3001 => *b"BA81",
        0x3002 => *b"GRBG",
        0x3007 => *b"BG10",
        0x3008 => *b"BG12",
        0x300a => *b"BA10",
        0x300e => *b"GB10",
        0x300f => *b"RG10",
        0x3010 => *b"GB12",
        0x3011 => *b"BA12",
        0x3012 => *b"RG12",
        0x3013 => *b"GBRG",
        0x3014 => *b"RGGB",
        _ => return u32::MAX,
    };
    u32::from_le_bytes(bytes)
}
/// Preserve query order, minimum-blanking arithmetic and the native fallback.
/// Required failures return immediately; optional NR/DCG failures clear validity.
/// This describes native timing minima, not necessarily current stream timing.
pub fn read<B: Backend>(backend: &mut B) -> Result<Descriptor, B::Error> {
    let mut result = Descriptor { bytes: [0; BYTES] };
    let format = backend.format()?;
    result.put(32, format.width);
    result.put(36, format.height);
    result.put(40, pixel_format(format.media_bus_code));
    let horizontal = backend.minimum(HBLANK)?;
    let vertical = backend.minimum(VBLANK)?;
    let line = format.width.wrapping_add(horizontal as u32) as u16;
    let frame = format.height.wrapping_add(vertical as u32) as u16;
    result.short(28, line);
    result.short(30, frame);
    let clock = match backend.frame_interval() {
        Ok((numerator, denominator)) => {
            ((line as f32 * frame as f32) * (denominator as f32 / numerator as f32)) / 1_000_000.
        }
        Err(_) => (backend.pixel_rate()? as u32 as i32) as f32 / 1_000_000.,
    };
    result.put(24, clock.to_bits());
    result.short(6, backend.minimum(EXPOSURE)? as u16);
    result.short(8, 10);
    if let Ok(values) = backend.nr_switch() {
        result.bytes[52] = 1;
        for (i, value) in values.iter().enumerate() {
            result.put(56 + i * 4, *value);
        }
    }
    if let Ok(values) = backend.dcg_ratio() {
        result.bytes[72] = 1;
        for (i, value) in values.iter().enumerate() {
            result.put(76 + i * 4, *value);
        }
    }
    Ok(result)
}

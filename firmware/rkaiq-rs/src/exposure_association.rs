//! SensorHw::getEffectiveExpParams selection policy (ELF 0x3bb70).
//! Map contents must come from the actual sensor scheduling path.
use crate::InvalidInput;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Match {
    pub index: usize,
    pub exact: bool,
}
pub fn effective_index(frames: &[u32], requested: u32) -> Result<Option<Match>, InvalidInput> {
    if frames.windows(2).any(|w| w[0] >= w[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    if frames.is_empty() {
        return Ok(None);
    }
    let requested = if requested == u32::MAX { 0 } else { requested };
    match frames.binary_search(&requested) {
        Ok(index) => Ok(Some(Match { index, exact: true })),
        Err(insertion) => Ok(Some(Match {
            index: if insertion == 0 {
                frames.len() - 1
            } else {
                insertion - 1
            },
            exact: false,
        })),
    }
}

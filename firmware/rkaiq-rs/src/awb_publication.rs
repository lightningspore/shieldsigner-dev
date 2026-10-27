//! AWB result publication from RkAiqAwbHandleInt::genIspResult (ELF 0x5ce20).
//! Owned records replace C++ proxy aliases. This does not run the AWB controller.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Item<const N: usize> {
    pub frame: u32,
    pub sync: u32,
    pub updated: bool,
    pub data: [u8; N],
}
pub type Gain = Item<20>;
pub type Configuration = Item<1204>;
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct State {
    pub gain_sync: u32,
    pub configuration_sync: u32,
    pub latest_gain: Option<Gain>,
    pub latest_configuration: Option<Configuration>,
}
#[derive(Clone, Copy, Debug)]
pub struct Input {
    pub frame: u32,
    pub initial: bool,
    pub bypass: bool,
    pub algorithm_id: i32,
    pub gain_changed: bool,
    pub configuration_changed: bool,
}
/// Return the remaining controller change flags (native clears published flags).
/// A missing latest item clears `updated` while still assigning the sync ID.
/// Native gain freshness compares against the *configuration* item's sync ID;
/// preserve that cross-item comparison even when the gain item has another ID.
pub fn publish(
    state: &mut State,
    gain: &mut Gain,
    configuration: &mut Configuration,
    input: Input,
) -> (bool, bool) {
    if input.bypass && input.algorithm_id == 0 {
        return (input.gain_changed, input.configuration_changed);
    }
    let frame = if input.initial { 0 } else { input.frame };
    gain.frame = frame;
    configuration.frame = frame;
    if input.gain_changed {
        state.gain_sync = input.frame;
        gain.sync = input.frame;
        gain.updated = true;
        state.latest_gain = Some(gain.clone());
    } else if state.gain_sync == configuration.sync {
        gain.updated = false;
    } else {
        gain.sync = state.gain_sync;
        gain.updated = state.latest_gain.is_some();
        if let Some(latest) = &state.latest_gain {
            gain.data = latest.data;
        }
    }
    if input.configuration_changed {
        state.configuration_sync = input.frame;
        configuration.sync = input.frame;
        configuration.updated = true;
        state.latest_configuration = Some(configuration.clone());
    } else if state.configuration_sync == configuration.sync {
        configuration.updated = false;
    } else {
        configuration.sync = state.configuration_sync;
        configuration.updated = state.latest_configuration.is_some();
        if let Some(latest) = &state.latest_configuration {
            configuration.data = latest.data;
        }
    }
    (false, false)
}

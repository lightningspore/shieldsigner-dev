//! CCM processing callback (ELF 0xfd126), with typed supported input records.
use crate::{ccm_automatic, ccm_calibration::Automatic, isp_ccm::RESULT_BYTES, InvalidInput};
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Information {
    pub current: [f32; 3],
    pub damping: f32,
    pub gray: bool,
    pub software_gray: bool,
    pub converged: bool,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct State {
    pub automatic: ccm_automatic::State,
    pub active: bool,
    pub attributes_changed: bool,
    pub reconfigure: bool,
}
impl State {
    pub fn new(cal: &Automatic) -> Self {
        Self {
            automatic: ccm_automatic::State::new(cal),
            active: true,
            attributes_changed: false,
            reconfigure: true,
        }
    }
    /// Preserve output bytes on no-update. Native writes gray/convergence back
    /// into software information; convergence reflects the pre-process state.
    /// Typed records exclude arbitrary SDK padding and unused metadata words.
    pub fn process(
        &mut self,
        cal: &Automatic,
        information: &mut Information,
        output: &mut [u8; RESULT_BYTES],
    ) -> Result<bool, InvalidInput> {
        let mut next = *self;
        let mut info = *information;
        let prior_publish = next.automatic.published || info.software_gray != info.gray;
        info.software_gray = info.gray;
        info.converged = next.automatic.converged;
        next.automatic.process(
            cal,
            info.current,
            info.damping,
            next.active,
            next.attributes_changed,
            next.reconfigure,
            info.gray,
            prior_publish,
        )?;
        let updated = next.automatic.published;
        if updated {
            *output = next.automatic.result;
        }
        next.automatic.published = false;
        next.attributes_changed = false;
        next.reconfigure = false;
        *self = next;
        *information = info;
        Ok(updated)
    }
}

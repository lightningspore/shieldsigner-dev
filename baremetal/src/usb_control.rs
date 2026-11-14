// SPDX-License-Identifier: MIT
//! DWC3 endpoint-zero control phases, independent of MMIO and DMA.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Control {
    Setup,
    InData,
    OutData,
    InStatus,
    OutStatus,
    StatusIn,
    StatusOut,
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Completion {
    Setup,
    DataSent,
    LineCoding,
    Finished,
}
impl Control {
    /// A completion belongs to exactly one direction. Do not advance on an
    /// unexpected event: otherwise stale/bad events could expose old DMA data.
    pub fn complete(&mut self, ep: usize) -> Result<Completion, &'static str> {
        let (next, action) = match (*self, ep) {
            (Self::Setup, 0) => (Self::Setup, Completion::Setup),
            (Self::InData, 1) => (Self::OutStatus, Completion::DataSent),
            (Self::OutData, 0) => (Self::InStatus, Completion::LineCoding),
            (Self::StatusIn, 1) | (Self::StatusOut, 0) => (Self::Setup, Completion::Finished),
            _ => return Err("usb-control-completion-state"),
        };
        *self = next;
        Ok(action)
    }
    /// DWC3 asks for the status TRB through XferNotReady. The TRB type is3
    /// for two-stage requests,4 for setup+data+status requests.
    pub fn not_ready(&mut self, ep: usize, three_stage: bool) -> Result<Option<u32>, &'static str> {
        let next = match *self {
            Self::InStatus if ep == 1 => Self::StatusIn,
            Self::OutStatus if ep == 0 => Self::StatusOut,
            Self::InStatus | Self::OutStatus => return Err("usb-status-direction"),
            _ => return Ok(None),
        };
        *self = next;
        Ok(Some(if three_stage { 4 } else { 3 }))
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn descriptor_read_has_out_status() {
        let mut c = Control::Setup;
        assert_eq!(c.complete(0), Ok(Completion::Setup));
        c = Control::InData;
        assert_eq!(c.complete(1), Ok(Completion::DataSent));
        assert_eq!(c.not_ready(0, true), Ok(Some(4)));
        assert_eq!(c.complete(0), Ok(Completion::Finished));
        assert_eq!(c, Control::Setup);
    }
    #[test]
    fn line_coding_write_has_in_status() {
        let mut c = Control::OutData;
        assert_eq!(c.complete(0), Ok(Completion::LineCoding));
        assert_eq!(c.not_ready(1, true), Ok(Some(4)));
        assert_eq!(c.complete(1), Ok(Completion::Finished));
    }
    #[test]
    fn no_data_write_has_two_stage_in_status() {
        let mut c = Control::InStatus;
        assert_eq!(c.not_ready(1, false), Ok(Some(3)));
        assert_eq!(c.complete(1), Ok(Completion::Finished));
    }
    #[test]
    fn wrong_direction_never_advances_phase() {
        for (phase, ep) in [
            (Control::Setup, 1),
            (Control::InData, 0),
            (Control::OutData, 1),
            (Control::StatusIn, 0),
            (Control::StatusOut, 1),
            (Control::InStatus, 1),
            (Control::OutStatus, 0),
        ] {
            let mut c = phase;
            assert!(c.complete(ep).is_err());
            assert_eq!(c, phase);
        }
        for (phase, ep) in [(Control::InStatus, 0), (Control::OutStatus, 1)] {
            let mut c = phase;
            assert!(c.not_ready(ep, true).is_err());
            assert_eq!(c, phase);
        }
    }
    #[test]
    fn unrelated_not_ready_does_not_start_duplicate_transfer() {
        for phase in [
            Control::Setup,
            Control::InData,
            Control::OutData,
            Control::StatusIn,
            Control::StatusOut,
        ] {
            let mut c = phase;
            assert_eq!(c.not_ready(0, true), Ok(None));
            assert_eq!(c, phase);
        }
    }
}

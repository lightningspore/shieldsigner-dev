//! Linear sensor-write sequencing recovered from SensorHw::setLinearSensorExposure.
//! Descriptor lookup and device ioctls are provided by the backend; this does not
//! convert seconds/real gain to register codes or schedule frame-delayed updates.
pub const VBLANK: u32 = 0x009e0901;
pub const ANALOGUE_GAIN: u32 = 0x009e0903;
pub const DIGITAL_GAIN: u32 = 0x00980913;
pub const EXPOSURE: u32 = 0x00980911;
#[derive(Clone, Copy, Debug)]
pub struct Descriptor {
    pub line_periods_per_field: u16,
    pub output_height: u32,
}
#[derive(Clone, Copy, Debug)]
pub struct LinearExposure {
    pub frame_length_lines: u32,
    pub dcg_mode: i32,
    pub analogue_gain_code: u32,
    pub digital_gain_code: u32,
    pub coarse_integration_time: u32,
}
pub trait Backend {
    type Error;
    fn descriptor(&mut self) -> Result<Descriptor, Self::Error>;
    fn control(&mut self, id: u32, value: i32) -> Result<(), Self::Error>;
    fn conversion_gain(&mut self, value: u32) -> Result<(), Self::Error>;
}
/// Apply the recovered write order. A present frame-length mirror updates after
/// VBLANK succeeds, even if a later operation fails; absent mirrors stay absent.
/// Preserve native u32 blanking subtraction and control-value bit patterns,
/// allowing the driver to reject unsupported/out-of-range controls.
/// Descriptor errors are returned, unlike the original unchecked descriptor call.
pub fn program_linear<B: Backend>(
    backend: &mut B,
    exposure: LinearExposure,
    frame_length_mirror: &mut Option<u32>,
) -> Result<(), B::Error> {
    let descriptor = backend.descriptor()?;
    let frame = (descriptor.line_periods_per_field as u32).max(exposure.frame_length_lines);
    backend.control(VBLANK, frame.wrapping_sub(descriptor.output_height) as i32)?;
    if frame_length_mirror.is_some() {
        *frame_length_mirror = Some(frame);
    }
    if matches!(exposure.dcg_mode, 0 | 1) {
        backend.conversion_gain(exposure.dcg_mode as u32)?;
    }
    backend.control(ANALOGUE_GAIN, exposure.analogue_gain_code as i32)?;
    if exposure.digital_gain_code != 0 {
        backend.control(DIGITAL_GAIN, exposure.digital_gain_code as i32)?;
    }
    if exposure.coarse_integration_time != 0 {
        backend.control(EXPOSURE, exposure.coarse_integration_time as i32)?;
    }
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    struct Missing;
    impl Backend for Missing {
        type Error = ();
        fn descriptor(&mut self) -> Result<Descriptor, ()> {
            Err(())
        }
        fn control(&mut self, _: u32, _: i32) -> Result<(), ()> {
            panic!("must not write after descriptor failure")
        }
        fn conversion_gain(&mut self, _: u32) -> Result<(), ()> {
            panic!("must not write after descriptor failure")
        }
    }
    #[test]
    fn descriptor_failure_is_returned_without_changing_mirror() {
        let mut mirror = Some(123);
        assert!(program_linear(
            &mut Missing,
            LinearExposure {
                frame_length_lines: 200,
                dcg_mode: 0,
                analogue_gain_code: 1,
                digital_gain_code: 1,
                coarse_integration_time: 1
            },
            &mut mirror
        )
        .is_err());
        assert_eq!(mirror, Some(123));
    }
}

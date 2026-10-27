//! Joined post-preparation dispatch and complete AWB gain wrapper.
use crate::{
    awb_dispatch,
    awb_gain_controller::{self, Frame, Light, LightResult, Settings},
    awb_preparation::LightRecord,
    awb_site, awb_wrapper, InvalidInput,
};
#[derive(Clone, Debug, PartialEq)]
pub struct State<const CAP: usize> {
    pub dispatch: awb_dispatch::State,
    pub controller: awb_gain_controller::State<CAP>,
    pub site: awb_site::State,
}
impl<const CAP: usize> State<CAP> {
    /// Runs through the request for hardware reconfiguration; its execution is
    /// still external. Clone staging includes callback-owned state, making a
    /// late output-scaling overflow atomic across every persistent component.
    pub fn process(
        &mut self,
        update: bool,
        frame: &Frame,
        records: &[LightRecord],
        lights: &[Light<'_>],
        output: &mut [LightResult],
        settings: &Settings<'_>,
        controls: &awb_wrapper::Controls<'_>,
        scale: Option<[f32; 2]>,
    ) -> Result<awb_dispatch::Action, InvalidInput> {
        if !update || !frame.complete {
            return self.dispatch.process(
                update,
                false,
                &mut self.controller.post.current,
                scale,
                |_| unreachable!(),
            );
        }
        let n = lights.len();
        if n < 4 || n > 255 || records.len() != n || output.len() != n {
            return Err(InvalidInput::Length);
        }
        let mut next = self.clone();
        let mut staged = [output[0]; 255];
        staged[..n].copy_from_slice(output);
        let settings = Settings {
            probability: crate::awb_probability::Settings {
                frame: next.dispatch.frame,
                ..settings.probability
            },
            ..*settings
        };
        let mut current = next.controller.post.current;
        let action = next
            .dispatch
            .process(update, true, &mut current, scale, |gain| {
                awb_wrapper::process(
                    &mut next.controller,
                    &mut next.site,
                    frame,
                    records,
                    lights,
                    &mut staged[..n],
                    &settings,
                    controls,
                )?;
                *gain = next.controller.post.current;
                Ok(())
            })?;
        next.controller.post.current = current;
        next.controller.low.low.current = current;
        output.copy_from_slice(&staged[..n]);
        *self = next;
        Ok(action)
    }
}

//! Single-camera service orchestration recovered from rkaiq_3A_server engine_thread.
//! The ISP backend is still incomplete; this module does not implement 3A itself.
pub const STREAM_START: u32 = 0x08000001;
pub const STREAM_STOP: u32 = 0x08000002;

#[derive(Clone, Copy, Debug)]
pub struct Config<'a> {
    pub sensor: &'a str,
    pub iq_directory: &'a str,
    pub width: u32,
    pub height: u32,
    pub multiple_cameras: bool,
}
/// Required processing and event-source operations. A native ISP implementation
/// must provide these before this controller can replace the vendor service.
pub trait Backend {
    type Error;
    fn initialize(&mut self, sensor: &str, iq_directory: &str) -> Result<(), Self::Error>;
    fn listen_in_library(&mut self, enabled: bool) -> Result<(), Self::Error>;
    fn multiple_cameras(&mut self) -> Result<(), Self::Error>;
    fn prepare_linear(&mut self, width: u32, height: u32) -> Result<(), Self::Error>;
    fn subscribe(&mut self, event: u32) -> Result<(), Self::Error>;
    fn start(&mut self) -> Result<(), Self::Error>;
    fn stop(&mut self, keep_external_hardware: bool) -> Result<(), Self::Error>;
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum State {
    WaitingForStart,
    WaitingForStop,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Action {
    Start,
    Stop,
}

pub struct Engine<B: Backend> {
    backend: B,
    state: State,
}
impl<B: Backend> Engine<B> {
    /// Prepare once, then subscribe to the two Rockchip ISP stream events.
    /// Unlike the original process-exit paths, backend errors are returned.
    pub fn prepare(mut backend: B, config: Config<'_>) -> Result<Self, B::Error> {
        backend.initialize(config.sensor, config.iq_directory)?;
        backend.listen_in_library(false)?;
        if config.multiple_cameras {
            backend.multiple_cameras()?;
        }
        backend.prepare_linear(config.width, config.height)?;
        backend.subscribe(STREAM_START)?;
        backend.subscribe(STREAM_STOP)?;
        Ok(Self {
            backend,
            state: State::WaitingForStart,
        })
    }
    pub fn state(&self) -> State {
        self.state
    }
    pub fn backend(&self) -> &B {
        &self.backend
    }
    /// Ignore all events except the event currently awaited by the original.
    /// On backend failure retain state and return the error, allowing the caller
    /// to handle it explicitly rather than silently advancing like the binary.
    pub fn on_event(&mut self, event: u32) -> Result<Option<Action>, B::Error> {
        match (self.state, event) {
            (State::WaitingForStart, STREAM_START) => {
                self.backend.start()?;
                self.state = State::WaitingForStop;
                Ok(Some(Action::Start))
            }
            (State::WaitingForStop, STREAM_STOP) => {
                self.backend.stop(false)?;
                self.state = State::WaitingForStart;
                Ok(Some(Action::Stop))
            }
            _ => Ok(None),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    struct Failing {
        fail_start: bool,
        starts: u32,
        stops: u32,
    }
    impl Backend for Failing {
        type Error = ();
        fn initialize(&mut self, _: &str, _: &str) -> Result<(), ()> {
            Ok(())
        }
        fn listen_in_library(&mut self, _: bool) -> Result<(), ()> {
            Ok(())
        }
        fn multiple_cameras(&mut self) -> Result<(), ()> {
            Ok(())
        }
        fn prepare_linear(&mut self, _: u32, _: u32) -> Result<(), ()> {
            Ok(())
        }
        fn subscribe(&mut self, _: u32) -> Result<(), ()> {
            Ok(())
        }
        fn start(&mut self) -> Result<(), ()> {
            if self.fail_start {
                Err(())
            } else {
                self.starts += 1;
                Ok(())
            }
        }
        fn stop(&mut self, keep: bool) -> Result<(), ()> {
            assert!(!keep);
            self.stops += 1;
            Ok(())
        }
    }
    #[test]
    fn failed_start_does_not_advance_and_duplicates_do_not_repeat_actions() {
        let mut engine = Engine::prepare(
            Failing {
                fail_start: true,
                starts: 0,
                stops: 0,
            },
            Config {
                sensor: "sensor",
                iq_directory: "/iq",
                width: 640,
                height: 480,
                multiple_cameras: false,
            },
        )
        .unwrap();
        assert_eq!(engine.on_event(STREAM_STOP), Ok(None));
        assert_eq!(engine.on_event(STREAM_START), Err(()));
        assert_eq!(engine.state(), State::WaitingForStart);
        engine.backend.fail_start = false;
        assert_eq!(engine.on_event(STREAM_START), Ok(Some(Action::Start)));
        assert_eq!(engine.on_event(STREAM_START), Ok(None));
        assert_eq!(engine.on_event(STREAM_STOP), Ok(Some(Action::Stop)));
        assert_eq!(engine.on_event(STREAM_STOP), Ok(None));
        assert_eq!((engine.backend.starts, engine.backend.stops), (1, 1));
    }
}

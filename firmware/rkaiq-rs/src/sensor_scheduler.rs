//! Ordinary, unsplit linear SensorHw::handle_sof path (ELF 0x3d558).
//! Payloads identify caller-owned complete exposure snapshots.
use crate::{sensor_timing::Delays, InvalidInput};
#[derive(Clone, Copy, Debug)]
pub struct EffectPolicy {
    pub shorten_enabled: bool,
    pub designated_frame: u32,
    pub shorten_all: bool,
}
#[derive(Clone, Copy, Debug)]
pub struct Entry<T: Copy> {
    pub frame: u32,
    pub exposure: T,
}
#[derive(Clone, Copy, Debug)]
pub struct Outcome<T: Copy> {
    pub written: Option<T>,
    pub effective_frame: Option<u32>,
    pub status: i32,
}
pub struct Scheduler<T: Copy> {
    pending: [Option<T>; 32],
    head: usize,
    pending_count: usize,
    effective: [Option<Entry<T>>; 11],
    effective_count: usize,
    pub current: T,
    pub last_sof: u32,
    delay: u32,
    pub policy: EffectPolicy,
}
impl<T: Copy> Scheduler<T> {
    pub fn new(initial: T, delays: Delays, policy: EffectPolicy) -> Result<Self, InvalidInput> {
        if delays.time < 0 || delays.time != delays.gain || delays.split_gain || delays.split_dcg {
            return Err(InvalidInput::Exposure);
        }
        let mut s = Self {
            pending: [None; 32],
            head: 0,
            pending_count: 0,
            effective: [None; 11],
            effective_count: 1,
            current: initial,
            last_sof: u32::MAX,
            delay: delays.time as u32,
            policy,
        };
        s.effective[0] = Some(Entry {
            frame: 0,
            exposure: initial,
        });
        Ok(s)
    }
    pub fn enqueue(&mut self, exposure: T) -> Result<(), InvalidInput> {
        if self.pending_count == 32 {
            return Err(InvalidInput::Length);
        }
        self.pending[(self.head + self.pending_count) % 32] = Some(exposure);
        self.pending_count += 1;
        Ok(())
    }
    pub fn effective(&self) -> impl Iterator<Item = Entry<T>> + '_ {
        self.effective[..self.effective_count]
            .iter()
            .map(|e| e.unwrap())
    }
    pub fn on_sof(&mut self, frame: u32, mut write: impl FnMut(T) -> i32) -> Outcome<T> {
        self.last_sof = frame;
        // Native retention runs before queue processing, including idle SOFs.
        if self.effective_count > 10 {
            self.effective.copy_within(1..self.effective_count, 0);
            self.effective_count -= 1;
            self.effective[self.effective_count] = None;
        }
        if self.pending_count == 0 {
            return Outcome {
                written: None,
                effective_frame: None,
                status: 0,
            };
        }
        let exposure = self.pending[self.head].take().unwrap();
        self.head = (self.head + 1) % 32;
        self.pending_count -= 1;
        self.current = exposure;
        let status = write(exposure);
        let effective_frame = if self.policy.shorten_enabled
            && (self.policy.shorten_all || self.policy.designated_frame == frame)
            && self.delay > 1
        {
            frame.wrapping_add(1)
        } else {
            frame.wrapping_add(self.delay)
        };
        let mut at = 0;
        while at < self.effective_count && self.effective[at].unwrap().frame < effective_frame {
            at += 1;
        }
        if at == self.effective_count || self.effective[at].unwrap().frame != effective_frame {
            self.effective.copy_within(at..self.effective_count, at + 1);
            self.effective_count += 1;
        }
        // The native routine records the dequeued snapshot even after a writer
        // error. This map is reported state, not proof of physical application.
        self.effective[at] = Some(Entry {
            frame: effective_frame,
            exposure,
        });
        Outcome {
            written: Some(exposure),
            effective_frame: Some(effective_frame),
            status,
        }
    }
}

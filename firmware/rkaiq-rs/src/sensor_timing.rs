//! SensorHw delay-policy configuration (ELF 0x3a7a0).
//! Preserves native partial state changes, including on rejected combinations.
#[derive(Clone, Copy, Debug)]
pub struct Delays {
    pub time: i32,
    pub gain: i32,
    pub dcg: i32,
    pub split_gain: bool,
    pub split_dcg: bool,
    pub dcg_with_time: bool,
}
impl Delays {
    /// Native status: 0 accepted, -2 rejected. Fields can change on rejection.
    /// This is policy arithmetic, not validation of a particular sensor's delays.
    pub fn configure(&mut self, time: i32, gain: i32, dcg: i32) -> i32 {
        self.time = time;
        self.gain = gain;
        self.dcg = dcg;
        if gain < time {
            self.split_gain = true;
        } else if time != gain {
            return -2;
        } else {
            self.split_gain = false;
        }
        if time < dcg {
            return -2;
        }
        if dcg < 1 {
            if time != dcg {
                self.dcg_with_time = false;
                return 0;
            }
        } else if time != dcg {
            if gain != dcg {
                self.split_dcg = true;
                return 0;
            }
            self.dcg_with_time = false;
            return 0;
        }
        self.dcg_with_time = true;
        0
    }
}

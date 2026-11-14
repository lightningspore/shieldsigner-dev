// SPDX-License-Identifier: MIT
//! Per-acquisition stage timings. These are not power-on or app-ready timings.
use core::sync::atomic::{AtomicU32, Ordering};
const MISSING: u32 = u32::MAX;
static START_LOW: AtomicU32 = AtomicU32::new(0);
static START_HIGH: AtomicU32 = AtomicU32::new(0);
static FIRST_ISP: AtomicU32 = AtomicU32::new(MISSING);
static CAPTURE: AtomicU32 = AtomicU32::new(MISSING);

pub fn begin() {
    let ticks = crate::cpu::counter();
    START_LOW.store(ticks as u32, Ordering::Relaxed);
    START_HIGH.store((ticks >> 32) as u32, Ordering::Relaxed);
    FIRST_ISP.store(MISSING, Ordering::Relaxed);
    CAPTURE.store(MISSING, Ordering::Relaxed);
}

fn elapsed() -> u32 {
    let start = ((START_HIGH.load(Ordering::Relaxed) as u64) << 32)
        | START_LOW.load(Ordering::Relaxed) as u64;
    (crate::cpu::counter().wrapping_sub(start) / 24).min(i32::MAX as u64) as u32
}

pub fn first_isp() {
    FIRST_ISP.store(elapsed(), Ordering::Relaxed);
}

pub fn capture_complete() {
    CAPTURE.store(elapsed(), Ordering::Relaxed);
}

#[no_mangle]
extern "C" fn bm_camera_timing(id: u32) -> i32 {
    let value = match id {
        0 => FIRST_ISP.load(Ordering::Relaxed),
        1 => CAPTURE.load(Ordering::Relaxed),
        _ => MISSING,
    };
    if value == MISSING { -1 } else { value as i32 }
}

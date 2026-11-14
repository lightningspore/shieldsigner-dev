// SPDX-License-Identifier: MIT
//! Single foreground owner; IRQs never access or allocate this state.
extern crate alloc;

use alloc::boxed::Box;
use core::sync::atomic::{AtomicBool, Ordering};
static ACTIVE: AtomicBool = AtomicBool::new(false);
static mut SESSION: Option<Box<super::isp_3a::Feedback>> = None;
static mut FIRST: bool = false;
pub fn active() -> bool {
    ACTIVE.load(Ordering::Acquire)
}
pub fn prepare(address: usize, frame_us: u64) {
    if let Ok(mut state) = super::isp_3a::Feedback::new(address, frame_us) {
        if state.consume().is_ok() {
            state.publish_controls();
            unsafe {
                SESSION = Some(Box::new(state));
                FIRST = true;
            }
        }
    }
}
#[no_mangle]
pub extern "C" fn bm_camera_preview(op: u32) -> i32 {
    match op {
        0 => {
            if ACTIVE.swap(true, Ordering::AcqRel) {
                return -1;
            }
            super::camera_timing::begin();
            super::runtime::board::quiet(|| super::camera::run());
            if unsafe { (&*core::ptr::addr_of!(SESSION)).is_none() } {
                stop();
                return -1;
            }
            super::camera_timing::capture_complete();
            0
        }
        1 => {
            if !active() {
                return -1;
            }
            let result: Result<(), &'static str> = super::runtime::board::quiet(|| unsafe {
                if FIRST {
                    FIRST = false;
                    return Ok(());
                }
                let state = (&mut *core::ptr::addr_of_mut!(SESSION))
                    .as_mut()
                    .ok_or("preview-state")?;
                state.advance(true)?;
                state.consume()?;
                state.publish_controls();
                Ok(())
            });
            if result.is_err() {
                let interrupted=super::runtime::take_interrupt();
                stop();
                if interrupted {-2}else{-1}
            } else {
                0
            }
        }
        2 => {
            stop();
            0
        }
        3 => active() as i32,
        4 => unsafe {
            (&*core::ptr::addr_of!(SESSION))
                .as_ref()
                .map_or(0, |s| s.index as i32 + 1)
        },
        _ => -1,
    }
}
fn stop() {
    super::runtime::board::quiet(|| {
        let _ = super::camera::stop_stream();
    });
    unsafe {
        SESSION = None;
        FIRST = false;
    }
    ACTIVE.store(false, Ordering::Release);
}

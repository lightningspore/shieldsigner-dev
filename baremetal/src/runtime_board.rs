// SPDX-License-Identifier: MIT
use core::sync::atomic::{AtomicBool, AtomicU32, Ordering};
pub static QUIET: AtomicBool = AtomicBool::new(false);
static INITIALIZED: AtomicBool = AtomicBool::new(false);
static FRAME_READY: AtomicBool = AtomicBool::new(false);
static CONTROL_READY: AtomicBool = AtomicBool::new(false);
static TARGET: AtomicU32 = AtomicU32::new(0);
static SEED: AtomicU32 = AtomicU32::new(122);
static EXPOSURE: AtomicU32 = AtomicU32::new(0);
static GAIN: AtomicU32 = AtomicU32::new(0);
fn quiet<T>(f: impl FnOnce() -> T) -> T {
    let old = QUIET.swap(true, Ordering::SeqCst);
    let result = f();
    QUIET.store(old, Ordering::SeqCst);
    result
}
pub fn camera_seed() -> u32 {
    SEED.load(Ordering::Relaxed)
}
pub fn camera_target() -> u32 {
    TARGET.load(Ordering::Relaxed)
}
pub fn camera_completed(exposure: u32, gain: u32) {
    EXPOSURE.store(exposure, Ordering::Relaxed);
    GAIN.store(gain, Ordering::Relaxed);
    CONTROL_READY.store(true, Ordering::Release);
}
pub fn camera_validated() {
    FRAME_READY.store(CONTROL_READY.load(Ordering::Acquire), Ordering::Release);
}
#[no_mangle]
extern "C" fn bm_pin(id: u32, mode: i32, value: i32) -> i32 {
    if !(-1..=1).contains(&mode) || !(-1..=1).contains(&value) {
        return -1;
    }
    crate::gpio::pin(
        id,
        if mode < 0 { None } else { Some(mode != 0) },
        if value < 0 { None } else { Some(value != 0) },
    )
    .map_or(-1, |v| v as i32)
}
#[no_mangle]
extern "C" fn bm_i2c_init() -> i32 {
    quiet(|| crate::i2c::init().map_or(-1, |_| 0))
}
#[no_mangle]
unsafe extern "C" fn bm_i2c_read(addr: u32, register: u32, data: *mut u8, len: usize) -> i32 {
    if addr != 0x30 || len > 32 || register > 65535 || register + len as u32 > 65536 {
        return -1;
    }
    for i in 0..len {
        match crate::i2c::read_sensor((register + i as u32) as u16) {
            Ok(v) => data.add(i).write(v),
            Err(_) => return -1,
        }
    }
    0
}
#[no_mangle]
unsafe extern "C" fn bm_i2c_write(addr: u32, register: u32, data: *const u8, len: usize) -> i32 {
    if addr != 0x30 || len > 32 || register > 65535 || register + len as u32 > 65536 {
        return -1;
    }
    for i in 0..len {
        if crate::i2c::write_sensor((register + i as u32) as u16, data.add(i).read()).is_err() {
            return -1;
        }
    }
    0
}
#[no_mangle]
unsafe extern "C" fn bm_spi_transfer(hz: u32, tx: *const u8, rx: *mut u8, len: usize) -> i32 {
    if len == 0 || len > 4096 || !(100000..=50000000).contains(&hz) {
        return -1;
    }
    // Copy before borrowing receive memory: Python permits in-place SPI.
    let mut transmit = [0; 4096];
    core::ptr::copy_nonoverlapping(tx, transmit.as_mut_ptr(), len);
    quiet(|| {
        let source = match crate::spi::init() {
            Ok(v) => v,
            Err(_) => return -1,
        };
        let divisor = ((source.div_ceil(hz) + 1) & !1).clamp(2, 65534);
        crate::spi::transfer(
            divisor,
            &transmit[..len],
            core::slice::from_raw_parts_mut(rx, len),
        )
        .map_or(-1, |_| 0)
    })
}
#[no_mangle]
extern "C" fn bm_camera_init() -> i32 {
    let ok = quiet(|| {
        crate::i2c::init().is_ok() && crate::i2c::read_id(0x30, false, false) == Ok(0xcc41)
    });
    INITIALIZED.store(ok, Ordering::Release);
    if ok {
        0
    } else {
        -1
    }
}
#[no_mangle]
extern "C" fn bm_camera_capture() -> i32 {
    if !INITIALIZED.load(Ordering::Acquire) {
        return -1;
    }
    FRAME_READY.store(false, Ordering::Release);
    CONTROL_READY.store(false, Ordering::Release);
    crate::camera_timing::begin();
    quiet(|| crate::camera::run());
    if FRAME_READY.load(Ordering::Acquire) {
        crate::camera_timing::capture_complete();
        0
    } else {
        -1
    }
}
#[no_mangle]
extern "C" fn bm_camera_setting(id: i32, value: i32) -> i32 {
    if value < -1 {
        return -1;
    }
    if value >= 0 {
        match id {
            0 if value == 0 || (8..=200).contains(&value) => {
                TARGET.store(value as u32, Ordering::Relaxed)
            }
            1 if (1..=1352).contains(&value) => SEED.store(value as u32, Ordering::Relaxed),
            _ => return -1,
        }
    }
    (match id {
        0 => camera_target(),
        1 => camera_seed(),
        2 => EXPOSURE.load(Ordering::Relaxed),
        3 => GAIN.load(Ordering::Relaxed),
        4 => crate::heap::used() as u32,
        _ => return -1,
    }) as i32
}

#[no_mangle]
unsafe extern "C" fn bm_display(op:u32,x:u32,y:u32,w:u32,h:u32,data:*const u8,len:usize)->i32 {
    #[cfg(feature = "bench-ui")]
    {
        match op {
            0 if x<=1=>crate::display::init(x!=0).map_or(-1,|_|0),
            1 if x<=65535=>crate::display::fill(x as u16).map_or(-1,|_|0),
            2 if x<240 && y<240 && w>0 && h>0 && w<=240 && h<=240 && x+w<=240 && y+h<=240 && len==w as usize*h as usize*2=>
                crate::display::blit(x as u16,y as u16,w as u16,h as u16,core::slice::from_raw_parts(data,len)).map_or(-1,|_|0),
            3=>crate::display::buttons().map_or(-1,|v|v as i32),
            4=>crate::display::status(x).map_or(-1,|v|v as i32),
            5 if len==crate::rgb565::FRAME_BYTES=>crate::display::blit_nv12(core::slice::from_raw_parts(data,len)).map_or(-1,|_|0),
            _=>-1,
        }
    }
    #[cfg(not(feature = "bench-ui"))]
    {let _=(op,x,y,w,h,data,len);-1}
}

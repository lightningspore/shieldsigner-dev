// SPDX-License-Identifier: MIT
//! Mini's active-high GPIO3_C6 work LED;5Hz heartbeat from the1kHz timer IRQ.
//! Pin/clock facts: pinned Luckfox Mini DTS, rv1106 pinctrl and clock tables.
use core::arch::asm;
use core::ptr::{read_volatile, write_volatile};
use core::sync::atomic::{AtomicBool, AtomicU32, Ordering};
const GPIO: usize = 0xff550000;
const IOC: usize = 0xff558000;
const BLINK_HZ: u32 = 5;
const HALF_PERIOD_TICKS: u32 = 1000 / (2 * BLINK_HZ);
const BIT: u32 = 1 << 6; // high register half: C6 is bank offset22
static READY: AtomicBool = AtomicBool::new(false);
static STATE: AtomicBool = AtomicBool::new(false);
static DIVIDER: AtomicU32 = AtomicU32::new(0);
static TRANSITIONS: AtomicU32 = AtomicU32::new(0);
static PAD_ERRORS: AtomicU32 = AtomicU32::new(0);

unsafe fn masked(address: usize, mask: u32, value: u32) {
    write_volatile(address as *mut u32, (mask << 16) | (value & mask));
}

pub fn init() {
    unsafe {
        masked(0xff3b4800, 1 << 2, 0); // PCLK_VI_ROOT
        masked(0xff3b4804, 1 << 15, 0); // PCLK_GPIO3
        asm!("dsb sy", options(nostack));
        let version = read_volatile((GPIO + 0x78) as *const u32);
        if version != 0x01000c2b && version != 0x0101157c {
            crate::put(b"@@FAIL led-gpio-version\r\n");
            return;
        }
        masked(GPIO + 0x0c, BIT, 0);
        masked(IOC + 0x54, 0x0f00, 0); // only C6 mux; leave SD A pins untouched
        masked(IOC + 0x1a8, BIT, BIT); // input enable for real pad readback
        masked(IOC + 0x1e8, 0x3000, 0); // C6 pull disabled
        masked(GPIO + 4, BIT, 0);
        masked(GPIO + 0x0c, BIT, BIT);
        asm!("dsb sy", options(nostack));
    }
    READY.store(true, Ordering::Release);
    crate::put(b"@@LED_HEARTBEAT gpio3_c6=118 hz=5\r\n");
}

pub fn tick() {
    if !READY.load(Ordering::Acquire) || DIVIDER.fetch_add(1, Ordering::Relaxed) != HALF_PERIOD_TICKS - 1 {
        return;
    }
    DIVIDER.store(0, Ordering::Relaxed);
    let on = !STATE.fetch_xor(true, Ordering::Relaxed);
    unsafe {
        masked(GPIO + 4, BIT, if on { BIT } else { 0 });
        asm!("dsb sy", options(nostack));
        let pad = (read_volatile((GPIO + 0x70) as *const u32) >> 22) & 1;
        if pad != on as u32 {
            PAD_ERRORS.fetch_add(1, Ordering::Relaxed);
        }
    }
    TRANSITIONS.fetch_add(1, Ordering::Relaxed);
}

#[no_mangle]
extern "C" fn bm_led_status(field: u32) -> u32 {
    match field {
        0 => READY.load(Ordering::Acquire) as u32,
        1 => TRANSITIONS.load(Ordering::Relaxed),
        2 => PAD_ERRORS.load(Ordering::Relaxed),
        3 => STATE.load(Ordering::Relaxed) as u32,
        4 => BLINK_HZ,
        _ => 0,
    }
}

// SPDX-License-Identifier: MIT
//! Non-secure DesignWare watchdog (RV1106/RV1103 `watchdog@ff5a0000`).
//!
//! USB console input is polled, not interrupt driven, so a wedged native call or
//! a panic spin leaves the device unrecoverable without a power cycle. The
//! watchdog is fed only from the MicroPython VM hook and the USB poll path; a
//! stall longer than the timeout performs a global reset. With no boot medium,
//! the ROM then enters maskrom exactly like a power cycle, allowing hands-free
//! reload. The reset routing writes mirror the vendor U-Boot RV1106 sequence
//! ("release the wdt"). This is a recovery aid, not a security or reliability
//! qualification.
use core::ptr::{read_volatile, write_volatile};
use core::sync::atomic::{AtomicBool, Ordering};

const WDT: usize = 0xff5a_0000;
const CR: usize = 0x00;
const TORR: usize = 0x04;
const CRR: usize = 0x0c;
const PERI_GRF_PERI_CON1: usize = 0xff00_0004;
const CRU_GLB_RST_CON: usize = 0xff3b_0c10;
/// PERICRU CLKGATE_CON1: bit2 pclk_wdt_ns, bit3 tclk_wdt_ns (xin24m); 1 = gated.
const PERI_CLKGATE_CON1: usize = 0xff3c_2804;
/// Timeout period 2^(16+14) clocks of the 24 MHz tclk: ~44.7 s.
const TOP: u32 = 14;
static ENABLED: AtomicBool = AtomicBool::new(false);

pub fn enable() {
    unsafe {
        write_volatile(PERI_CLKGATE_CON1 as *mut u32, 0x000c_0000);
        write_volatile(PERI_GRF_PERI_CON1 as *mut u32, 0x0200_0200);
        write_volatile(CRU_GLB_RST_CON as *mut u32, 0x0040_0040);
        write_volatile((WDT + TORR) as *mut u32, TOP | (TOP << 4));
        // Response mode 0: reset directly on first timeout.
        write_volatile((WDT + CR) as *mut u32, 1);
        write_volatile((WDT + CRR) as *mut u32, 0x76);
    }
    ENABLED.store(true, Ordering::Release);
}

#[inline]
pub fn feed() {
    if ENABLED.load(Ordering::Relaxed) {
        unsafe { write_volatile((WDT + CRR) as *mut u32, 0x76) }
    }
}

/// Diagnostic register read for machine.watchdog(): 0 CR, 1 TORR, 2 CCVR,
/// 3 clock gate, 4 enabled flag.
#[no_mangle]
extern "C" fn bm_watchdog_status(field: u32) -> u32 {
    unsafe {
        match field {
            0 => read_volatile((WDT + CR) as *const u32),
            1 => read_volatile((WDT + TORR) as *const u32),
            2 => read_volatile((WDT + 0x08) as *const u32),
            3 => read_volatile(PERI_CLKGATE_CON1 as *const u32),
            _ => ENABLED.load(Ordering::Relaxed) as u32,
        }
    }
}

/// Deliberate unfed stall proving hands-free recovery. Never returns: without a
/// working watchdog the device stays wedged until power is cycled.
#[no_mangle]
extern "C" fn bm_watchdog_selftest() -> ! {
    unsafe { core::arch::asm!("cpsid if", options(nostack)) };
    loop { core::hint::spin_loop(); }
}

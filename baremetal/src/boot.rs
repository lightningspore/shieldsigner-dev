// SPDX-License-Identifier: MIT
//! Payload-entry timing, excluding ROM/card discovery and vendor DDR init.
use core::fmt::Write;
use core::sync::atomic::{AtomicU32, Ordering};
static ENTRY_LOW: AtomicU32 = AtomicU32::new(0);
static ENTRY_HIGH: AtomicU32 = AtomicU32::new(0);

pub fn begin(low: u32, high: u32) {
    ENTRY_LOW.store(low, Ordering::Relaxed);
    ENTRY_HIGH.store(high, Ordering::Relaxed);
}

pub fn repl_ready() {
    let now = super::cpu::counter();
    let entry = ((ENTRY_HIGH.load(Ordering::Relaxed) as u64) << 32)
        | ENTRY_LOW.load(Ordering::Relaxed) as u64;
    // GPIO1_C4 goes high near _start, low immediately after mp_init.
    // The phase10 observer owns the matching REF pin as input.
    #[cfg(not(feature = "app-runtime"))]
    let _ = super::gpio::pin(52, Some(true), Some(false));
    let _ = writeln!(
        super::cpu::Console,
        "@@BOOT payload_entry_to_repl_us={} excludes_rom_ddr=1\r",
        now.wrapping_sub(entry) / 24
    );
}

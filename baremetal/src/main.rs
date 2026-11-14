// SPDX-License-Identifier: MIT
// Original minimal code. DDR init and UART2 setup are inherited from the unchanged vendor blob.
#![no_std]
#![no_main]

use core::arch::{asm, global_asm};
use core::ptr::{read_volatile, write_volatile};
#[cfg(feature = "fast-boot")]
mod boot;
#[cfg(feature = "runtime-repl")]
mod runtime;
#[cfg(feature = "usb-console")]
mod usb;
#[cfg(feature = "usb-console")]
mod usb_descriptors;
#[cfg(feature = "usb-console")]
mod usb_control;

#[cfg(feature = "camera-test")]
mod camera;
#[cfg(feature = "runtime-board")]
mod camera_timing;
#[cfg(feature = "runtime-board")]
mod led;
#[cfg(feature = "camera-test")]
mod camera_replay_data;
#[cfg(feature = "cpu-base")]
mod cpu;
#[cfg(feature = "gpio-test")]
mod gpio;
#[cfg(feature = "cpu-base")]
mod heap;
#[cfg(feature = "i2c-test")]
mod i2c;
#[cfg(feature = "cpu-base")]
mod interrupts;
#[cfg(feature = "isp-test")]
mod isp;
#[cfg(feature = "isp-3a-test")]
mod isp_3a;
#[cfg(feature = "isp-3a-test")]
mod isp_awb;
#[cfg(feature = "isp-test")]
mod isp_replay_data;
#[cfg(feature = "spi-test")]
mod spi;

global_asm!(
    r#"
    .section .text.entry,"ax"
    .arm
    .global _start
_start:
    cpsid if
    .if {fast}
    mrrc p15, 0, r4, r5, c14
    .if {probe}
    // Blue GPIO1_C4: REF must remain input. Orange C5 stays untouched.
    ldr r0, =0xff3ba800
    ldr r1, =0x80000000
    str r1, [r0]
    ldr r0, =0xff53000c
    ldr r1, =0x00100000
    str r1, [r0]
    ldr r0, =0xff538014
    ldr r1, =0x000f0000
    str r1, [r0]
    ldr r0, =0xff5381c8
    ldr r1, =0x03000000
    str r1, [r0]
    ldr r0, =0xff530004
    ldr r1, =0x00100010
    str r1, [r0]
    ldr r0, =0xff53000c
    str r1, [r0]
    dsb sy
    .endif
    .endif
    ldr sp, =0x00400000
    ldr r0, =__bss_start
    ldr r1, =__bss_end
    mov r2, #0
1:  cmp r0, r1
    strlo r2, [r0], #4
    blo 1b
    .if {fast}
    mov r0, r4
    mov r1, r5
    .endif
    bl rust_main
2:  b 2b
"#,
    fast = const cfg!(feature = "fast-boot") as u32,
    probe = const cfg!(all(feature = "fast-boot", not(feature = "app-runtime"))) as u32,
);

const UART: usize = 0xff4c0000;

fn put(bytes: &[u8]) {
    #[cfg(feature = "runtime-board")]
    if runtime::QUIET.load(core::sync::atomic::Ordering::Relaxed) {
        return;
    }
    for &byte in bytes {
        unsafe {
            while read_volatile((UART + 0x14) as *const u32) & 0x20 == 0 {}
            write_volatile(UART as *mut u32, byte as u32);
        }
    }
}

#[no_mangle]
extern "C" fn rust_main(entry_low: u32, entry_high: u32) -> ! {
    #[cfg(feature = "fast-boot")]
    boot::begin(entry_low, entry_high);
    #[cfg(not(feature = "fast-boot"))]
    let _ = (entry_low, entry_high);
    put(b"\r\n@@PASS hello\r\n");
    #[cfg(feature = "cpu-base")]
    cpu::run();
    #[cfg(feature = "gpio-test")]
    gpio::init();
    #[cfg(feature = "runtime-board")]
    led::init();
    #[cfg(all(feature = "i2c-test", not(feature = "camera-test")))]
    i2c::run();
    #[cfg(all(feature = "spi-test", not(feature = "runtime-repl")))]
    spi::run();
    #[cfg(all(feature = "camera-test", not(feature = "runtime-repl")))]
    camera::run();
    #[cfg(feature = "usb-console")]
    if let Err(reason) = usb::init() {
        use core::fmt::Write;
        let _ = writeln!(cpu::Console, "@@FAIL {}\r", reason);
    }
    #[cfg(feature = "runtime-repl")]
    runtime::run();
    // Keep a UART recovery path while USB is absent in this minimal payload.
    // 'R' requests a warm reset; no storage writes are involved.
    #[cfg(not(feature = "runtime-repl"))]
    loop {
        #[cfg(not(feature = "cpu-base"))]
        unsafe {
            #[cfg(not(feature = "cpu-base"))]
            if read_volatile((UART + 0x14) as *const u32) & 1 != 0
                && read_volatile(UART as *const u32) as u8 == b'R'
            {
                reset();
            }
        }
    }
}

fn reset() -> ! {
    #[cfg(feature = "runtime-board")]
    runtime::QUIET.store(false, core::sync::atomic::Ordering::Relaxed);
    put(b"@@RESET\r\n");
    unsafe {
        asm!("cpsid if", options(nostack));
        while read_volatile((UART + 0x14) as *const u32) & 0x40 == 0 {}
        asm!("dsb sy", options(nostack));
        write_volatile(0xff3b0c08 as *mut u32, 0xfdb9);
        asm!("dsb sy", options(nostack));
    }
    loop {
        core::hint::spin_loop();
    }
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    put(b"@@FAIL panic\r\n");
    loop {
        core::hint::spin_loop();
    }
}

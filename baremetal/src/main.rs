// SPDX-License-Identifier: MIT
// Original minimal code. DDR init and UART2 setup are inherited from the unchanged vendor blob.
#![no_std]
#![no_main]

use core::arch::{asm, global_asm};
use core::ptr::{read_volatile, write_volatile};

#[cfg(feature = "camera-test")]
mod camera;
#[cfg(feature = "camera-test")]
mod camera_replay_data;
#[cfg(feature = "isp-test")]
mod isp;
#[cfg(feature = "isp-test")]
mod isp_replay_data;
#[cfg(feature = "isp-3a-test")]
mod isp_3a;
#[cfg(feature = "isp-3a-test")]
mod isp_awb;
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
#[cfg(feature = "spi-test")]
mod spi;

global_asm!(
    r#"
    .section .text.entry,"ax"
    .arm
    .global _start
_start:
    cpsid if
    ldr sp, =0x00400000
    ldr r0, =__bss_start
    ldr r1, =__bss_end
    mov r2, #0
1:  cmp r0, r1
    strlo r2, [r0], #4
    blo 1b
    bl rust_main
2:  b 2b
"#
);

const UART: usize = 0xff4c0000;

fn put(bytes: &[u8]) {
    for &byte in bytes {
        unsafe {
            while read_volatile((UART + 0x14) as *const u32) & 0x20 == 0 {}
            write_volatile(UART as *mut u32, byte as u32);
        }
    }
}

#[no_mangle]
extern "C" fn rust_main() -> ! {
    put(b"\r\n@@PASS hello\r\n");
    #[cfg(feature = "cpu-base")]
    cpu::run();
    #[cfg(feature = "gpio-test")]
    gpio::init();
    #[cfg(all(feature = "i2c-test", not(feature = "camera-test")))]
    i2c::run();
    #[cfg(feature = "spi-test")]
    spi::run();
    #[cfg(feature = "camera-test")]
    camera::run();
    // Keep a UART recovery path while USB is absent in this minimal payload.
    // 'R' requests a warm reset; no storage writes are involved.
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

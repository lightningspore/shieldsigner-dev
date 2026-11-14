// SPDX-License-Identifier: MIT
//! Phase 4 pins only: GPIO1_C4 output (blue) and GPIO1_C5 input (orange).
//! Direction starts as input for both; only a host '0'/'1' command enables C4 output.
use core::arch::asm;
use core::ptr::{read_volatile, write_volatile};
use core::sync::atomic::{AtomicBool, Ordering};

const GPIO1: usize = 0xff530000;
const IOC: usize = 0xff538000;
static READY: AtomicBool = AtomicBool::new(false);

unsafe fn write(address: usize, value: u32) {
    write_volatile(address as *mut u32, value);
}
unsafe fn read(address: usize) -> u32 {
    read_volatile(address as *const u32)
}

unsafe fn masked(address: usize, mask: u16, value: u16) {
    write(address, ((mask as u32) << 16) | ((value & mask) as u32));
}

pub fn init() {
    unsafe {
        // GPIO1 PCLK gate: VEPUCRU_CLKGATE_CON0 bit15, 0 enables clock.
        masked(0xff3ba800, 1 << 15, 0);
        // High halves cover GPIO offsets16..31: C4=bit4, C5=bit5.
        masked(GPIO1 + 0x0c, 0x30, 0); // both inputs before selecting GPIO mux
        masked(IOC + 0x14, 0x00ff, 0); // GPIO1_C4/C5 mux function 0
        masked(IOC + 0x1c8, 0x0f00, 0); // disable pulls for these two 3.3V pins
        masked(GPIO1 + 0x04, 0x10, 0); // prepare low C4 output latch
        asm!("dsb sy", options(nostack));
        let version = read(GPIO1 + 0x78);
        if version != 0x01000c2b && version != 0x0101157c {
            super::put(b"@@FAIL gpio-version\r\n");
            return;
        }
    }
    READY.store(true, Ordering::Release);
    super::put(b"@@GPIO_READY C4=input C5=input\r\n");
}

pub fn command(byte: u8) -> bool {
    if READY.load(Ordering::Acquire) && byte == b'Z' {
        unsafe {
            masked(GPIO1 + 0x0c, 0x30, 0);
        }
        super::put(b"@@GPIO_RELEASED\r\n");
        return true;
    }
    if !READY.load(Ordering::Acquire) || (byte != b'0' && byte != b'1') {
        return false;
    }
    let value = byte == b'1';
    unsafe {
        masked(GPIO1 + 0x04, 0x10, if value { 0x10 } else { 0 });
        masked(GPIO1 + 0x0c, 0x10, 0x10); // enable C4 output only, C5 stays input
        asm!("dsb sy", options(nostack));
        let input = (read(GPIO1 + 0x70) >> 21) & 1;
        let line = [
            b'@',
            b'@',
            b'G',
            b'P',
            b'I',
            b'O',
            b' ',
            b'o',
            b'u',
            b't',
            b'=',
            byte,
            b' ',
            b'i',
            b'n',
            b'=',
            b'0' + input as u8,
            b'\r',
            b'\n',
        ];
        super::put(&line);
    }
    true
}

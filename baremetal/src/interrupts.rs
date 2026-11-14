// SPDX-License-Identifier: MIT
use core::arch::{asm, global_asm};
use core::ptr::{addr_of, addr_of_mut, read_volatile, write_volatile};
const DIST: usize = 0xff1f1000;
const CPU: usize = 0xff1f2000;
static mut TICKS: u32 = 0;
static mut UART_BYTES: u32 = 0;
static mut PERIOD: u32 = 24000;

global_asm!(
    r#"
    .section .text.vectors,"ax"
    .balign 32
    .global exception_vectors
exception_vectors:
    b _start
    b exception_fault
    b exception_fault
    b exception_fault
    b exception_fault
    b exception_fault
    b irq_entry
    b exception_fault
irq_entry:
    push {{r0-r12,lr}}
    bl rust_irq
    pop {{r0-r12,lr}}
    subs pc, lr, #4
exception_fault:
    cpsid if
    cps #0x13
    movw sp, #0
    movt sp, #0x0040
    bl rust_fault
"#
);

unsafe fn write(base: usize, offset: usize, value: u32) {
    write_volatile((base + offset) as *mut u32, value);
}
unsafe fn read(base: usize, offset: usize) -> u32 {
    read_volatile((base + offset) as *const u32)
}

pub unsafe fn start(frequency: u32) {
    extern "C" {
        static exception_vectors: u8;
    }
    // Separate banked IRQ stack at2MiB; SVC grows down from4MiB. The earlier
    // 64KiB spacing was too small for calibrated3A's large temporary records.
    asm!(
        "cps #0x12",
        // Materialize the constant directly; an inline literal pool can move
        // beyond LDR range when LTO grows the camera startup function.
        "movw sp, #0",
        "movt sp, #0x0020",
        "cps #0x13",
        options(nostack)
    );
    asm!("mcr p15, 0, {0}, c12, c0, 0", in(reg) addr_of!(exception_vectors) as u32, options(nostack));
    let mut control: u32;
    asm!("mrc p15, 0, {0}, c1, c0, 0", out(reg) control, options(nostack));
    control &= !(1 << 13); // use VBAR rather than high vectors
    asm!("mcr p15, 0, {0}, c1, c0, 0", "isb", in(reg) control, options(nostack));
    write(DIST, 0, 0);
    write(CPU, 0, 0);
    for id in [29u32, 30, 59] {
        let bank = (id / 32) as usize * 4;
        let mask = 1u32 << (id % 32);
        write(DIST, 0x180 + bank, mask); // disable while configuring
        write(DIST, 0x280 + bank, mask); // clear pending
        write(DIST, 0x80 + bank, read(DIST, 0x80 + bank) | mask); // Group 1
        let word = (id / 4) as usize * 4;
        let shift = (id % 4) * 8;
        write(
            DIST,
            0x400 + word,
            (read(DIST, 0x400 + word) & !(255 << shift)) | (128 << shift),
        );
        if id >= 32 {
            write(
                DIST,
                0x800 + word,
                (read(DIST, 0x800 + word) & !(255 << shift)) | (1 << shift),
            );
        }
        write(DIST, 0x100 + bank, mask);
    }
    write(CPU, 4, 255); // priority mask
    write(CPU, 8, 0); // binary point
    write(DIST, 0, 3);
    write(CPU, 0, 7); // enable groups; secure IAR may acknowledge Group 1
    write_volatile(addr_of_mut!(PERIOD), frequency / 1000);
    asm!("mcr p15, 0, {0}, c14, c2, 0", in(reg) frequency/1000, options(nostack));
    asm!("mcr p15, 0, {0}, c14, c2, 1", in(reg) 1u32, options(nostack));
    // FIFO trigger one byte, RX interrupt only; all TX remains polled.
    while read(super::UART, 0x14) & 0x40 == 0 {}
    write(super::UART, 8, 3);
    write(super::UART, 4, 1);
    asm!("dsb sy", "isb", "cpsie i", options(nostack));
}

pub fn ticks() -> u32 {
    unsafe { read_volatile(addr_of!(TICKS)) }
}
pub fn uart_bytes() -> u32 {
    unsafe { read_volatile(addr_of!(UART_BYTES)) }
}

#[no_mangle]
extern "C" fn rust_irq() {
    unsafe {
        let ack = read(CPU, 0x0c);
        let id = ack & 1023;
        if id == 29 || id == 30 {
            asm!("mcr p15, 0, {0}, c14, c2, 0", in(reg) read_volatile(addr_of!(PERIOD)), options(nostack));
            write_volatile(addr_of_mut!(TICKS), ticks().wrapping_add(1));
        } else if id == 54 {
            #[cfg(feature = "i2c-test")]
            super::i2c::irq();
        } else if id == 136 || id == 137 {
            #[cfg(feature = "isp-test")]
            super::isp::irq();
        } else if id == 59 {
            while read(super::UART, 0x14) & 1 != 0 {
                let byte = read(super::UART, 0) as u8;
                write_volatile(addr_of_mut!(UART_BYTES), uart_bytes().wrapping_add(1));
                if byte == b'R' {
                    super::reset();
                }
                #[cfg(feature = "gpio-test")]
                if super::gpio::command(byte) {
                    continue;
                }
                super::put(&[byte]);
            }
        }
        if id < 1020 {
            asm!("dsb sy", options(nostack));
            write(CPU, 0x10, ack);
        }
    }
}

#[cfg(feature = "isp-test")]
pub unsafe fn isp_irqs_enabled(enabled: bool) {
    for id in [136u32, 137] {
        let bank = (id / 32) as usize * 4;
        let bit = 1 << (id % 32);
        write(DIST, 0x180 + bank, bit);
        if enabled {
            let word = (id / 4) as usize * 4;
            let shift = (id % 4) * 8;
            write(DIST, 0x80 + bank, read(DIST, 0x80 + bank) | bit);
            write(
                DIST,
                0x400 + word,
                (read(DIST, 0x400 + word) & !(255 << shift)) | (128 << shift),
            );
            write(
                DIST,
                0x800 + word,
                (read(DIST, 0x800 + word) & !(255 << shift)) | (1 << shift),
            );
            write(DIST, 0x280 + bank, bit);
            write(DIST, 0x100 + bank, bit);
        }
    }
    asm!("dsb sy", options(nostack));
}

#[no_mangle]
extern "C" fn rust_fault() -> ! {
    super::put(b"@@FAIL exception\r\n");
    super::reset()
}

#[cfg(feature = "i2c-test")]
pub unsafe fn i2c_irq_enabled(enabled: bool) {
    let bit = 1u32 << 22; // INTID54 = I2C4 SPI22
    if enabled {
        write(DIST, 0x84, read(DIST, 0x84) | bit);
        write(DIST, 0x434, (read(DIST, 0x434) & !0x00ff0000) | 0x00800000);
        write(DIST, 0x834, (read(DIST, 0x834) & !0x00ff0000) | 0x00010000);
        write(DIST, 0x284, bit);
        write(DIST, 0x104, bit);
    } else {
        write(DIST, 0x184, bit);
    }
    asm!("dsb sy", options(nostack));
}

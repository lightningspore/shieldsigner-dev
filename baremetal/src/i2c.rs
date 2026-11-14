// SPDX-License-Identifier: MIT
//! Original bounded register-read driver for the Rockchip I2C4 controller.
use core::arch::asm;
use core::fmt::Write;
use core::ptr::{read_volatile, write_volatile};
use core::sync::atomic::{AtomicU32, Ordering};
static EVENTS: AtomicU32 = AtomicU32::new(0);
static IRQ_COUNT: AtomicU32 = AtomicU32::new(0);
const BASE: usize = 0xff470000;
unsafe fn read(a: usize) -> u32 {
    read_volatile(a as *const u32)
}
unsafe fn write(a: usize, v: u32) {
    write_volatile(a as *mut u32, v)
}
unsafe fn mask(a: usize, m: u16, v: u16) {
    write(a, ((m as u32) << 16) | ((v & m) as u32))
}
fn delay_ms(ms: u64) {
    let t = super::cpu::counter();
    while super::cpu::counter().wrapping_sub(t) < 24000 * ms {}
}
fn gcd(mut a: u32, mut b: u32) -> u32 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

unsafe fn camera_clock() -> Result<u32, &'static str> {
    let c0 = read(0xff3b0060);
    let c1 = read(0xff3b0064);
    let frac = read(0xff3b0068) & 0xffffff;
    let mode = (read(0xff3b0280) >> 4) & 1;
    let fb = c0 & 4095;
    let p1 = (c0 >> 12) & 7;
    let r = c1 & 63;
    let p2 = (c1 >> 6) & 7;
    if mode != 1 || r == 0 || p1 == 0 || p2 == 0 {
        return Err("gpll-state");
    }
    let fraction = if c1 & (1 << 12) != 0 { 0 } else { frac as u64 };
    let hz = (24000000u64 * ((fb as u64) * 16777216 + fraction)
        / r as u64
        / p1 as u64
        / p2 as u64
        / 16777216) as u32;
    let divisor = gcd(hz, 54000000);
    let numerator = 54000000 / divisor;
    let denominator = hz / divisor;
    if numerator > 65535 || denominator > 65535 || numerator >= denominator {
        return Err("mclk-ratio");
    }
    // Source GPLL /2, fractional output 27 MHz; only this clock branch is changed.
    mask(0xff3b0364, 0xfc, 1 << 2);
    write(0xff3b0368, (numerator << 16) | denominator);
    mask(0xff3b036c, 3, 1);
    mask(0xff3b080c, 0x70, 0);
    let _ = writeln!(
        super::cpu::Console,
        "@@MCLK gpll_hz={} numerator={} denominator={} target_hz=27000000\r",
        hz,
        numerator,
        denominator
    );
    Ok(hz)
}

pub fn init() -> Result<(), &'static str> {
    unsafe {
        // GPIO3 bus root at 24 MHz, GPIO3 PCLK enabled.
        mask(0xff3b4300, 0x30, 0x30);
        mask(0xff3b4800, 4, 0);
        mask(0xff3b4804, 0x8000, 0);
        let gpio = 0xff550000;
        // C5 is camera PWDN/reset, initially low before output enable.
        mask(gpio + 4, 0x20, 0);
        mask(gpio + 12, 0x20, 0x20);
        // Bank3 C4: MCLK function2; C5: GPIO0; C7: I2C4 SCL function3.
        mask(0xff558054, 0xf0ff, 0x3002);
        // Bank3 D0: I2C4 SDA function3.
        mask(0xff558058, 0x000f, 3);
        camera_clock()?;
        delay_ms(1);
        mask(gpio + 4, 0x20, 0x20);
        delay_ms(20);
        // I2C4 parent explicitly xin24m; peripheral gate enable.
        mask(0xff3b2308, 3, 3);
        mask(0xff3b2804, 0xc000, 0);
        write(BASE, 0);
        write(BASE + 0x18, 0);
        write(BASE + 0x1c, 255);
        // SCL = 24MHz / [8*((14+1)+(14+1))] =100kHz.
        write(BASE + 4, (14 << 16) | 14);
        asm!("dsb sy", options(nostack));
        let _ = writeln!(
            super::cpu::Console,
            "@@I2C init con={:#x} clkdiv={:#x} clksel={:#x}\r",
            read(BASE),
            read(BASE + 4),
            read(0xff3b2308)
        );
        Ok(())
    }
}

/// Bounded sensor write: address byte + big-endian16-bit register + one data byte.
pub fn write_sensor(register: u16, value: u8) -> Result<(), &'static str> {
    unsafe {
        super::interrupts::i2c_irq_enabled(false);
        write(BASE, 0);
        write(BASE + 0x18, 0);
        write(BASE + 0x1c, 255);
        let bytes = 0x60u32
            | (((register >> 8) as u32) << 8)
            | (((register & 255) as u32) << 16)
            | ((value as u32) << 24);
        write(BASE + 0x100, bytes);
        write(BASE, 1 | 8 | 64);
        write(BASE + 0x10, 4);
        let result = wait(4);
        stop();
        result.map(|_| ())
    }
}

/// One-byte sensor register read using the controller's combined-address RX mode.
#[cfg(feature = "camera-test")]
pub fn read_sensor(register: u16) -> Result<u8, &'static str> {
    unsafe {
        super::interrupts::i2c_irq_enabled(false);
        write(BASE, 0);
        write(BASE + 0x18, 0);
        write(BASE + 0x1c, 255);
        write(BASE + 8, (1 << 24) | 0x60);
        let bytes = ((register >> 8) as u32) | (((register & 255) as u32) << 8);
        write(BASE + 12, (3 << 24) | bytes);
        write(BASE, 1 | 2 | 8 | 32 | 64);
        write(BASE + 0x14, 1);
        let result = wait(8);
        let value = if result.is_ok() {
            read(BASE + 0x200) as u8
        } else {
            0
        };
        stop();
        result.map(|_| value)
    }
}

fn wait(mask: u32) -> Result<u32, &'static str> {
    let start = super::cpu::counter();
    loop {
        let pending = unsafe { read(BASE + 0x1c) };
        if pending & 64 != 0 {
            return Err("nack");
        }
        if pending & mask != 0 {
            return Ok(pending);
        }
        if super::cpu::counter().wrapping_sub(start) > 2400000 {
            return Err("timeout");
        }
    }
}
fn stop() {
    unsafe {
        let control = read(BASE);
        write(BASE, (control & !8) | 16);
        let start = super::cpu::counter();
        while read(BASE + 0x1c) & 32 == 0 && super::cpu::counter().wrapping_sub(start) < 2400000 {}
        write(BASE, 0);
        write(BASE + 0x1c, 255);
    }
}

/// IRQ handles completion/NAK notification; the owning transfer reads the FIFO.
pub fn irq() {
    unsafe {
        let events = read(BASE + 0x1c) & 0x4c;
        if events != 0 {
            write(BASE + 0x18, 0);
            write(BASE + 0x1c, events);
            EVENTS.store(events, Ordering::Release);
            IRQ_COUNT.fetch_add(1, Ordering::Relaxed);
        }
    }
}

fn wait_irq(deadline_ticks: u64) -> Result<u32, &'static str> {
    let start = super::cpu::counter();
    loop {
        let events = EVENTS.load(Ordering::Acquire);
        if events & 64 != 0 {
            return Err("nack");
        }
        if events & 8 != 0 {
            return Ok(events);
        }
        if super::cpu::counter().wrapping_sub(start) >= deadline_ticks {
            return Err("timeout");
        }
    }
}

/// A missed interrupt is a deliberate fault injection for bounded-time recovery tests.
pub fn read_id(address: u8, interrupt: bool, missed_interrupt: bool) -> Result<u16, &'static str> {
    unsafe {
        write(BASE, 0);
        write(BASE + 0x18, 0);
        write(BASE + 0x1c, 255);
        EVENTS.store(0, Ordering::Release);
        super::interrupts::i2c_irq_enabled(interrupt && !missed_interrupt);
        write(BASE + 8, (1 << 24) | ((address as u32) << 1));
        write(BASE + 12, (3 << 24) | 0x0731);
        write(BASE + 0x18, if interrupt { 0x48 } else { 0 });
        write(BASE, 1 | 2 | 8 | 32 | 64);
        write(BASE + 0x14, 2);
        let result = if interrupt {
            wait_irq(if missed_interrupt { 48000 } else { 2400000 })
        } else {
            wait(8)
        };
        write(BASE + 0x18, 0);
        let data = if result.is_ok() {
            Some(read(BASE + 0x200))
        } else {
            None
        };
        stop();
        super::interrupts::i2c_irq_enabled(false);
        match (result, data) {
            (Ok(_), Some(v)) => Ok((((v & 255) << 8) | ((v >> 8) & 255)) as u16),
            (Err(e), _) => Err(e),
            _ => Err("no-data"),
        }
    }
}

#[cfg(not(feature = "camera-test"))]
pub fn run() {
    if let Err(e) = init() {
        let _ = writeln!(super::cpu::Console, "@@FAIL i2c-init {}\r", e);
        return;
    }
    let polled = read_id(0x30, false, false);
    let _ = writeln!(super::cpu::Console, "@@SENSOR polled={:?}\r", polled);
    if polled == Ok(0xcc41) {
        super::put(b"@@PASS sensor-id-polled\r\n")
    } else {
        super::put(b"@@FAIL sensor-id-polled\r\n");
        return;
    }
    let before = IRQ_COUNT.load(Ordering::Relaxed);
    let interrupt = read_id(0x30, true, false);
    let after = IRQ_COUNT.load(Ordering::Relaxed);
    let _ = writeln!(
        super::cpu::Console,
        "@@SENSOR interrupt={:?} irqs={}\r",
        interrupt,
        after.wrapping_sub(before)
    );
    if interrupt == Ok(0xcc41) && after != before {
        super::put(b"@@PASS sensor-id-irq\r\n")
    } else {
        super::put(b"@@FAIL sensor-id-irq\r\n");
        return;
    }
    let nak_poll = read_id(0x31, false, false);
    let nak_irq = read_id(0x31, true, false);
    let start = super::cpu::counter();
    let timeout = read_id(0x30, true, true);
    let elapsed = super::cpu::counter().wrapping_sub(start);
    let recovered = read_id(0x30, true, false);
    let _=writeln!(super::cpu::Console,"@@I2C_ERRORS polled_nak={:?} irq_nak={:?} masked_irq_timeout={:?} elapsed_ticks={} recovered={:?}\r",nak_poll,nak_irq,timeout,elapsed,recovered);
    if nak_poll == Err("nack")
        && nak_irq == Err("nack")
        && timeout == Err("timeout")
        && elapsed < 2400000
        && recovered == Ok(0xcc41)
    {
        super::put(b"@@PASS i2c-errors\r\n@@PASS phase-5\r\n");
    } else {
        super::put(b"@@FAIL i2c-errors\r\n")
    }
}

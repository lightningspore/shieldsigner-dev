// SPDX-License-Identifier: MIT
//! Bench240 SeedSigner LCD/button backend, explicitly excludes the HOTHMI carrier.
//! Pin facts: installed FOX_22 io_config.json and PCB-SOFTWARE-COMPATIBILITY.md.
//! ST7789 command/register values follow the panel contract; no Linux APIs.
use core::ptr::{read_volatile, write_volatile};
use core::sync::atomic::{AtomicBool, AtomicU32, Ordering};
static SOFTWARE_SPI: AtomicBool = AtomicBool::new(false);
static READY: AtomicBool = AtomicBool::new(false);
static DIVISOR: AtomicU32 = AtomicU32::new(20);
const GPIO: usize = 0xff530000;
const IOC: usize = 0xff538000;
const PCB: bool = cfg!(feature="mini-pcb-ui");
const DC:u32=if PCB {0x10}else{0x100};
const RESET:u32=if PCB {8}else{0x200};
const BUTTONS: [u32; 8] = if PCB {[57,59,56,54,58,55,4,53]} else {[58,53,59,54,52,55,43,42]};
unsafe fn mask(address: usize, bits: u32, value: u32) {
    write_volatile(address as *mut u32, (bits << 16) | (value & bits));
}
fn pause(ms: u32) {
    let start = crate::cpu::counter();
    while crate::cpu::counter().wrapping_sub(start) < ms as u64 * 24000 {
        crate::usb::poll();
    }
}
fn data_mode(data: bool) {
    unsafe {
        mask(GPIO + 4, DC, if data { DC } else { 0 });
    }
}
fn tx(data: &[u8]) -> Result<(), &'static str> {
    for part in data.chunks(4096) {
        if SOFTWARE_SPI.load(Ordering::Relaxed) {
            software_write(part);
        } else {
            crate::spi::write_only(DIVISOR.load(Ordering::Relaxed), part)?;
        }
        crate::usb::poll();
    }
    Ok(())
}
fn command(command: u8, params: &[u8]) -> Result<(), &'static str> {
    data_mode(false);
    tx(&[command])?;
    if !params.is_empty() {
        data_mode(true);
        tx(params)?;
    }
    Ok(())
}
fn window(x: u16, y: u16, w: u16, h: u16) -> Result<(), &'static str> {
    if w == 0 || h == 0 || x as u32 + w as u32 > 240 || y as u32 + h as u32 > 240 {
        return Err("lcd-window");
    }
    let right = x + w - 1;
    let bottom = y + h - 1;
    command(
        0x2a,
        &[(x >> 8) as u8, x as u8, (right >> 8) as u8, right as u8],
    )?;
    command(
        0x2b,
        &[(y >> 8) as u8, y as u8, (bottom >> 8) as u8, bottom as u8],
    )?;
    command(0x2c, &[])?;
    data_mode(true);
    Ok(())
}
pub fn init(software_spi: bool) -> Result<(), &'static str> {
    READY.store(false, Ordering::Release);
    SOFTWARE_SPI.store(software_spi, Ordering::Relaxed);
    let source = unsafe { crate::spi::init_tx_only()? };
    let divisor = ((source.div_ceil(10_000_000) + 1) & !1).clamp(2, 65534);
    DIVISOR.store(divisor, Ordering::Relaxed);
    if software_spi {
        unsafe {
            mask(GPIO + 4, 7, 1);
            mask(GPIO + 0x0c, 7, 7);
            mask(IOC + 0x10, 0x0fff, 0);
        }
    }
    unsafe {
        if PCB {
            // Exact user-provided Mini PCB: D0..D3/C5..C7 are buttons.
            // Release former wrong-profile D0/D1 outputs before anything else.
            mask(GPIO+0x0c,0x0fe0,0);
            mask(IOC+0x18,0xffff,0);
            mask(IOC+0x14,0xffff,0);
            // LCD reset=C3/global51, DC=C4/global52, BL=B3/global43.
            mask(GPIO+4,0x18,8);
            mask(GPIO+0x0c,0x18,0x18);
            mask(IOC+0x10,0xf000,0);
            mask(IOC+8,0xf000,0);
            mask(IOC+0x1c4,0x00c0,0);
            mask(IOC+0x1c8,0xffc0,0x5400); // C3/C4 no pulls, C5..C7 up
            mask(IOC+0x1cc,0x00ff,0x55); // D0..D3 input pullups
            // KEY2 is GPIO0_A4 on this PCB, with external pullup.
            mask(0xff3b0800,2,0); // PMU root PCLK
            mask(0xff3b0804,4,0); // GPIO0 PCLK
            mask(0xff380008,0x10,0);
            mask(0xff388004,0x000f,0); // A4 mux0
            mask(0xff388038,0x0300,0x0100); // A4 pullup
            // Prepare backlight high before output-enable; this is not UART.
            mask(GPIO,0x800,0x800);
            mask(GPIO+8,0x800,0x800);
        } else {
        // LCD DC=D0/global56, RESET=D1/global57. Prepare latches first.
        mask(GPIO + 4, 0x0300, 0x0200);
        mask(GPIO + 0x0c, 0x0300, 0x0300);
        mask(IOC + 0x18, 0x00ff, 0);
        mask(IOC + 0x1cc, 0x000f, 0);
        // All eight buttons input-only, native-domain pullups; preserve LCD pads.
        mask(GPIO + 8, 0x0c00, 0);
        mask(GPIO + 0x0c, 0x0cf0, 0);
        mask(IOC + 8, 0xff00, 0);
        mask(IOC + 0x14, 0xffff, 0);
        mask(IOC + 0x18, 0xff00, 0);
        mask(IOC + 0x1c4, 0x00f0, 0x0050);
        mask(IOC + 0x1c8, 0xff00, 0x5500);
        mask(IOC + 0x1cc, 0x00f0, 0x0050);
        }
    }
    pause(10);
    unsafe {
        mask(GPIO + 4, RESET, 0);
    }
    pause(10);
    unsafe {
        mask(GPIO + 4, RESET, RESET);
    }
    pause(150);
    command(0x01, &[])?;
    pause(150);
    // Register values from the installed known-good ST7789 bench profile.
    // Keep explicit power/porch/gamma settings rather than relying on reset defaults.
    for (register, values) in [
        (0x36, &[0x70][..]),
        (0x3a, &[0x55][..]),
        (0xb2, &[0x0c, 0x0c, 0, 0x33, 0x33][..]),
        (0xb7, &[0x35][..]),
        (0xbb, &[0x19][..]),
        (0xc0, &[0x2c][..]),
        (0xc2, &[1][..]),
        (0xc3, &[0x12][..]),
        (0xc4, &[0x20][..]),
        (0xc6, &[0x0f][..]),
        (0xd0, &[0xa4, 0xa1][..]),
        (
            0xe0,
            &[
                0xd0, 4, 0x0d, 0x11, 0x13, 0x2b, 0x3f, 0x54, 0x4c, 0x18, 0x0d, 0x0b, 0x1f, 0x23,
            ][..],
        ),
        (
            0xe1,
            &[
                0xd0, 4, 0x0c, 0x11, 0x13, 0x2c, 0x3f, 0x44, 0x51, 0x2f, 0x1f, 0x1f, 0x20, 0x23,
            ][..],
        ),
    ] {
        command(register, values)?;
    }
    command(0x11, &[])?;
    pause(150);
    command(0x13, &[])?;
    // Match installed ST7789 NORMAL_COLORS_REQUIRE_INVERSION baseline.
    command(0x21, &[])?;
    command(0x29, &[])?;
    READY.store(true, Ordering::Release);
    Ok(())
}
pub fn buttons() -> Result<u32, &'static str> {
    if !READY.load(Ordering::Acquire) {
        return Err("lcd-not-initialized");
    }
    let levels = unsafe { read_volatile((GPIO + 0x70) as *const u32) };
    let mut result = 0;
    let gpio0 = if PCB {unsafe {read_volatile(0xff380070 as *const u32)}}else{0};
    for (index, pin) in BUTTONS.iter().enumerate() {
        let pressed=if *pin<32 {gpio0 & (1<<pin)==0}else{levels & (1<<(pin-32))==0};
        if pressed {
            result |= 1 << index;
        }
    }
    Ok(result)
}
pub fn fill(color: u16) -> Result<(), &'static str> {
    if !READY.load(Ordering::Acquire) {
        return Err("lcd-not-initialized");
    }
    // Clear the complete240x320 ST7789 backing RAM, including off-canvas rows.
    // This avoids stale edge pixels on240px panels with an80-row viewport offset.
    command(0x36, &[0])?;
    command(0x2a, &[0, 0, 0, 239])?;
    command(0x2b, &[0, 0, 1, 63])?;
    command(0x2c, &[])?;
    data_mode(true);
    let mut row = [0u8; 480];
    for p in row.chunks_exact_mut(2) {
        p.copy_from_slice(&color.to_be_bytes());
    }
    for _ in 0..320 {
        tx(&row)?;
    }
    command(0x36, &[0x70])?;
    Ok(())
}
pub fn blit(x: u16, y: u16, w: u16, h: u16, data: &[u8]) -> Result<(), &'static str> {
    if !READY.load(Ordering::Acquire) || data.len() != w as usize * h as usize * 2 {
        return Err("lcd-buffer");
    }
    window(x, y, w, h)?;
    tx(data)
}

/// Bounded pad/controller readbacks for bring-up; no arbitrary MMIO access.
pub fn status(field: u32) -> Result<u32, &'static str> {
    if field==14 {return Ok(unsafe {read_volatile(0xff380070 as *const u32)});}
    if field==15 {return Ok(unsafe {read_volatile((GPIO+8) as *const u32)} & 0x0c00);}
    if field==16 {return Ok(unsafe {read_volatile(GPIO as *const u32)} & 0x0800);}
    if field == 13 {
        return Ok(SOFTWARE_SPI.load(Ordering::Relaxed) as u32);
    }
    let (address, bits) = match field {
        0 => (GPIO + 0x70, 0x0fc00c00),
        1 => (GPIO + 8, 0x0c00),
        2 => (GPIO + 0x0c, 0x0ff8),
        3 => (IOC + 8, 0xff00),
        4 => (IOC + 0x14, 0xffff),
        5 => (IOC + 0x18, 0xffff),
        6 => (IOC + 0x1c4, 0xf0),
        7 => (IOC + 0x1c8, 0xff00),
        8 => (IOC + 0x1cc, 0xff),
        9 => (IOC + 0x10, 0x0fff),
        10 => (0xff500010, 0xffff),
        11 => (0xff500000, 0x00ffffff),
        12 => (0xff500004, 0xffff),
        _ => return Err("display-status-field"),
    };
    Ok(unsafe { read_volatile(address as *const u32) } & bits)
}

// Slow100kHz diagnostic path to isolate SPI-controller setup from the panel.
// Owns only the same explicit CS0/SCK/MOSI pads as the hardware path.
fn software_write(data: &[u8]) {
    fn edge_delay() {
        let start = crate::cpu::counter();
        while crate::cpu::counter().wrapping_sub(start) < 120 {}
    }
    unsafe {
        mask(GPIO + 4, 1, 0);
        for (index, byte) in data.iter().enumerate() {
            for bit in (0..8).rev() {
                mask(GPIO + 4, 6, if byte & (1 << bit) != 0 { 4 } else { 0 });
                edge_delay();
                mask(GPIO + 4, 2, 2);
                edge_delay();
            }
            if index & 63 == 63 {
                crate::usb::poll();
            }
        }
        mask(GPIO + 4, 2, 0);
        mask(GPIO + 4, 1, 1);
    }
}

/// Consume the bounded camera's read-only NV12 view synchronously. No frame copy
/// or Rust heap allocation; the caller keeps the source view alive for this call.
pub fn blit_nv12(frame:&[u8])->Result<(),&'static str> {
    if !READY.load(Ordering::Acquire) || frame.len()!=crate::rgb565::FRAME_BYTES {return Err("lcd-nv12-frame");}
    window(0,0,240,240)?;
    let mut row=[0u8;480];
    for y in 0..240 {crate::rgb565::center_crop_row(frame,y,&mut row)?;tx(&row)?;}
    Ok(())
}

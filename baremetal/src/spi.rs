// SPDX-License-Identifier: MIT
//! Original polled SPI0 loopback. Requires physical C2/MOSI-to-C3/MISO jumper.
use core::fmt::Write;
use core::ptr::{read_volatile, write_volatile};
const SPI: usize = 0xff500000;
unsafe fn read(a: usize) -> u32 {
    read_volatile(a as *const u32)
}
unsafe fn write(a: usize, v: u32) {
    write_volatile(a as *mut u32, v)
}
unsafe fn mask(a: usize, m: u16, v: u16) {
    write(a, ((m as u32) << 16) | ((m & v) as u32))
}

pub(crate) unsafe fn init() -> Result<u32, &'static str> {
    init_pads(true)
}
#[cfg(feature = "bench-ui")]
pub(crate) unsafe fn init_tx_only() -> Result<u32, &'static str> {
    init_pads(false)
}
unsafe fn init_pads(receive: bool) -> Result<u32, &'static str> {
    // Derive SPI clock from the inherited integer CPLL without retuning the PLL.
    let c0 = read(0xff3b0020);
    let c1 = read(0xff3b0024);
    let mode = (read(0xff3b0280) >> 2) & 1;
    let refdiv = c1 & 63;
    let post1 = (c0 >> 12) & 7;
    let post2 = (c1 >> 6) & 7;
    if mode != 1 || refdiv == 0 || post1 == 0 || post2 == 0 || c1 & (1 << 12) == 0 {
        return Err("cpll-state");
    }
    let hz = 24000000u64 * (c0 & 4095) as u64 / refdiv as u64 / post1 as u64 / post2 as u64;
    let _ = writeln!(super::cpu::Console, "@@SPI cpll_hz={}\r", hz);
    if !(900000000..=1100000000).contains(&hz) {
        return Err("cpll-rate");
    }
    // clk_200m_src selects CPLL /5; SPI0 uses that source. Other PLLs untouched.
    mask(0xff3b0304, 0x0fc0, 0x0900);
    mask(0xff3b0800, 1 << 4, 0);
    mask(0xff3ba300, 0x30c0, 0x0080); // SPI0 source0, peripheral bus xin24m
    mask(0xff3ba800, (1 << 3) | (1 << 15), 0); // peripheral root and GPIO1 PCLK
    mask(0xff3ba804, 12, 0); // SPI0 PCLK + functional clock
                             // GPIO1_C0 CS0, C1 CLK, C2 MOSI, C3 MISO.
    mask(0xff538010, if receive { 0xffff } else { 0x0fff }, 0x6644);
    mask(0xff5381c8, if receive { 0x00ff } else { 0x003f }, 0); // pulls disabled for these four pins only
                                                                // Moderate drive level2 (encoding0x07) for CS/SCK/MOSI, retaining MISO settings.
    mask(0xff5380a0, 0xffff, 0x0707);
    mask(0xff5380a4, 0x00ff, 0x0007);
    write(SPI + 8, 0);
    write(SPI + 0x0c, 0);
    write(SPI + 0x2c, 0);
    write(SPI + 0x3c, 0);
    let _ = writeln!(
        super::cpu::Console,
        "@@SPI version={:#x} source_hz={} root={:#x}\r",
        read(SPI + 0x48),
        hz / 5,
        read(0xff3b0304)
    );
    Ok((hz / 5) as u32)
}

pub(crate) fn transfer(divisor: u32, tx: &[u8], rx: &mut [u8]) -> Result<(), &'static str> {
    if tx.is_empty() || tx.len() > 4096 || tx.len() != rx.len() {
        return Err("spi-length");
    }
    let count = tx.len();
    unsafe {
        write(SPI + 8, 0);
        write(SPI + 0x38, 1);
        // Mode0, MSB-first, 8-bit frames; full duplex, no DMA/interrupts/internal loopback.
        write(SPI, 1 | (1 << 13) | (1 << 11) | (1 << 10));
        write(SPI + 4, (count - 1) as u32);
        write(SPI + 0x10, divisor);
        write(SPI + 0x14, 0);
        write(SPI + 0x18, 0);
        write(SPI + 0x0c, 1);
        write(SPI + 8, 1);
        let start = super::cpu::counter();
        let mut sent = 0;
        let mut received = 0;
        let mut result = Ok(());
        while received < count {
            // Limit in-flight words below even the smallest supported FIFO depth.
            while sent < count && sent - received < 16 && read(SPI + 0x1c) < 16 {
                write(SPI + 0x400, tx[sent] as u32);
                sent += 1;
            }
            while received < sent && read(SPI + 0x20) > 0 {
                rx[received] = read(SPI + 0x800) as u8;
                received += 1;
            }
            if read(SPI + 0x34) & 0x0e != 0 {
                result = Err("fifo-error");
                break;
            }
            if super::cpu::counter().wrapping_sub(start) > 12000000 {
                result = Err("timeout");
                break;
            }
        }
        while result.is_ok() && read(SPI + 0x24) & 1 != 0 {
            if super::cpu::counter().wrapping_sub(start) > 12000000 {
                result = Err("busy-timeout");
                break;
            }
        }
        write(SPI + 0x0c, 0);
        write(SPI + 8, 0);
        result
    }
}

#[cfg(not(feature = "runtime-repl"))]
pub fn run() {
    let source = match unsafe { init() } {
        Ok(hz) => hz,
        Err(e) => {
            let _ = writeln!(super::cpu::Console, "@@FAIL spi-init {}\r", e);
            return;
        }
    };
    let mut tx = [0u8; 4096];
    let mut rx = [0u8; 4096];
    let mut random = 0x7193ac55u32;
    for byte in &mut tx {
        random ^= random << 13;
        random ^= random >> 17;
        random ^= random << 5;
        *byte = random as u8;
    }
    for (hz, divisor) in [(1000000, 200), (10000000, 20), (50000000, 4)] {
        rx.fill(0);
        let result = transfer(divisor, &tx, &mut rx);
        let errors = tx.iter().zip(rx.iter()).filter(|(a, b)| a != b).count();
        let checksum = rx.iter().fold(2166136261u32, |h, b| {
            (h ^ (*b as u32)).wrapping_mul(16777619)
        });
        let _ = writeln!(
            super::cpu::Console,
            "@@SPI_RESULT requested_hz={} actual_hz={} bytes=4096 errors={} checksum={:#x} status={:?}\r",
            hz,
            source / divisor,
            errors,
            checksum,
            result
        );
        if result.is_err() || errors != 0 {
            super::put(b"@@FAIL spi-loopback\r\n");
            return;
        }
    }
    super::put(b"@@PASS phase-6\r\n");
}

/// TX-only FIFO transfer; C3/MISO is not used or remuxed by init_tx_only.
#[cfg(feature = "bench-ui")]
pub(crate) fn write_only(divisor: u32, tx: &[u8]) -> Result<(), &'static str> {
    if tx.is_empty() || tx.len() > 4096 {
        return Err("spi-length");
    }
    unsafe {
        write(SPI + 8, 0);
        write(SPI + 0x38, 1);
        write(SPI, 1 | (1 << 13) | (1 << 11) | (1 << 10) | (1 << 18));
        write(SPI + 4, (tx.len() - 1) as u32);
        write(SPI + 0x10, divisor);
        write(SPI + 0x0c, 1);
        write(SPI + 8, 1);
        let start = super::cpu::counter();
        let mut sent = 0;
        let mut result = Ok(());
        while sent < tx.len() {
            if read(SPI + 0x1c) < 16 {
                write(SPI + 0x400, tx[sent] as u32);
                sent += 1;
            }
            if read(SPI + 0x34) & 0x0e != 0 {
                result = Err("spi-tx-fifo");
                break;
            }
            if super::cpu::counter().wrapping_sub(start) > 12_000_000 {
                result = Err("spi-tx-timeout");
                break;
            }
        }
        while result.is_ok() && (read(SPI + 0x1c) != 0 || read(SPI + 0x24) & 1 != 0) {
            if super::cpu::counter().wrapping_sub(start) > 12_000_000 {
                result = Err("spi-tx-drain-timeout");
                break;
            }
        }
        write(SPI + 0x0c, 0);
        write(SPI + 8, 0);
        result
    }
}

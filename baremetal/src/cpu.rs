// SPDX-License-Identifier: MIT
use core::arch::asm;
use core::fmt::{self, Write};

pub(crate) struct Console;
impl Write for Console {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        super::put(s.as_bytes());
        Ok(())
    }
}

pub fn counter() -> u64 {
    let lo: u32;
    let hi: u32;
    unsafe {
        asm!("isb", "mrrc p15, 0, {lo}, {hi}, c14", lo=out(reg) lo, hi=out(reg) hi, options(nostack));
    }
    ((hi as u64) << 32) | lo as u64
}

pub fn run() {
    let sctlr: u32;
    let cpsr: u32;
    let frequency: u32;
    unsafe {
        asm!("mrc p15, 0, {0}, c1, c0, 0", out(reg) sctlr, options(nostack));
        asm!("mrs {0}, cpsr", out(reg) cpsr, options(nostack));
        asm!("mrc p15, 0, {0}, c14, c0, 0", out(reg) frequency, options(nostack));
    }
    let start = counter();
    for _ in 0..10000 {
        core::hint::spin_loop();
    }
    let elapsed = counter().wrapping_sub(start);
    let _ = writeln!(
        Console,
        "@@CPU cpsr={:#010x} sctlr={:#010x} cntfrq={} elapsed={}\r",
        cpsr, sctlr, frequency, elapsed
    );
    if frequency != 0 && elapsed != 0 {
        super::put(b"@@PASS cpu-counter\r\n");
        memory_gate();
        if super::heap::check() {
            super::put(b"@@PASS heap\r\n");
        } else {
            super::put(b"@@FAIL heap\r\n");
        }
        interrupt_gate(frequency);
    } else {
        super::put(b"@@FAIL cpu-counter\r\n");
    }
}

#[repr(C, align(16384))]
struct TranslationTable([u32; 4096]);
static mut TABLE: TranslationTable = TranslationTable([0; 4096]);
static mut WORK: [u32; 4096] = [0; 4096];

unsafe fn enable_memory() {
    use core::ptr::{addr_of_mut, write_volatile};
    // Cortex-A7 requires SMP enabled for normal shareable memory to be cacheable,
    // including a single-core system. The loader leaves this bit clear.
    let auxiliary: u32;
    asm!("mrc p15, 0, {0}, c1, c0, 1", out(reg) auxiliary, options(nostack));
    asm!("mcr p15, 0, {0}, c1, c0, 1", "isb", in(reg) auxiliary | (1 << 6), options(nostack));
    let table = addr_of_mut!(TABLE.0) as *mut u32;
    for section in 0..4096 {
        // Short-descriptor sections, domain 0, full privileged/user access.
        // DDR: normal WBWA, shareable; other addresses: shareable device, XN.
        let attrs = if cfg!(feature = "camera-test") && (48..56).contains(&section) {
            // Camera DMA buffers: normal noncacheable, shareable, execute-never.
            (1 << 12) | (1 << 4)
        } else if section < 64 {
            (1 << 12) | (1 << 3) | (1 << 2)
        } else {
            (1 << 4) | (1 << 2)
        };
        write_volatile(
            table.add(section),
            ((section as u32) << 20) | (1 << 16) | (3 << 10) | attrs | 2,
        );
    }
    // Invalidate data/unified caches by architectural set/way geometry.
    let clidr: u32;
    asm!("mrc p15, 1, {0}, c0, c0, 1", out(reg) clidr, options(nostack));
    for level in 0..7 {
        let kind = (clidr >> (level * 3)) & 7;
        if kind < 2 || kind > 4 {
            continue;
        }
        asm!("mcr p15, 2, {0}, c0, c0, 0", "isb", in(reg) level * 2, options(nostack));
        let geometry: u32;
        asm!("mrc p15, 1, {0}, c0, c0, 0", out(reg) geometry, options(nostack));
        let line_bits = (geometry & 7) + 4;
        let ways = ((geometry >> 3) & 1023) + 1;
        let sets = ((geometry >> 13) & 32767) + 1;
        let way_shift = (ways - 1).leading_zeros();
        for way in 0..ways {
            for set in 0..sets {
                let value = (level << 1)
                    | (set << line_bits)
                    | if ways == 1 { 0 } else { way << way_shift };
                asm!("mcr p15, 0, {0}, c7, c6, 2", in(reg) value, options(nostack));
            }
        }
    }
    let zero = 0u32;
    let domain = 1u32;
    asm!("dsb sy",
        "mcr p15, 0, {zero}, c7, c5, 0", // I-cache invalidate
        "mcr p15, 0, {zero}, c7, c5, 6", // branch predictor invalidate
        "mcr p15, 0, {zero}, c8, c7, 0", // unified TLB invalidate
        "mcr p15, 0, {zero}, c2, c0, 2", // TTBCR: all addresses via TTBR0
        "mcr p15, 0, {table}, c2, c0, 0",
        "mcr p15, 0, {domain}, c3, c0, 0",
        "dsb sy", "isb",
        zero=in(reg) zero, table=in(reg) table as u32, domain=in(reg) domain, options(nostack));
    let mut control: u32;
    asm!("mrc p15, 0, {0}, c1, c0, 0", out(reg) control, options(nostack));
    // Standard short-descriptor interpretation (TRE/AFE off), MMU, D/I caches and branch prediction.
    control = (control & !((1 << 28) | (1 << 29))) | 1 | (1 << 2) | (1 << 11) | (1 << 12);
    asm!("mcr p15, 0, {0}, c1, c0, 0", "isb", in(reg) control, options(nostack));
}

fn workload() -> (u64, u32) {
    use core::ptr::{addr_of, read_volatile};
    let start = counter();
    let mut checksum = 0u32;
    let work = addr_of!(WORK) as *const u32;
    for i in 0..262144 {
        checksum = checksum.wrapping_add(unsafe { read_volatile(work.add(i & 4095)) });
    }
    (counter().wrapping_sub(start), checksum)
}

fn memory_gate() {
    unsafe {
        let actlr: u32;
        asm!("mrc p15, 0, {0}, c1, c0, 1", out(reg) actlr, options(nostack));
        let _ = writeln!(Console, "@@ACTLR {:#010x}\r", actlr);
        asm!("mcr p15, 0, {0}, c9, c12, 0", in(reg) 7u32, options(nostack));
        asm!("mcr p15, 0, {0}, c9, c12, 1", in(reg) 0x80000000u32, options(nostack));
        let start = counter();
        let before: u32;
        asm!("mrc p15, 0, {0}, c9, c13, 0", out(reg) before, options(nostack));
        while counter().wrapping_sub(start) < 24000 {}
        let after: u32;
        asm!("mrc p15, 0, {0}, c9, c13, 0", out(reg) after, options(nostack));
        let _ = writeln!(
            Console,
            "@@CLOCK counter_ticks={} cpu_cycles={}\r",
            counter().wrapping_sub(start),
            after.wrapping_sub(before)
        );
    }
    unsafe {
        let work = core::ptr::addr_of_mut!(WORK) as *mut u32;
        for i in 0..4096 {
            core::ptr::write_volatile(work.add(i), i as u32);
        }
    }
    let (off, sum_off) = workload();
    let _ = writeln!(Console, "@@BENCH off_ticks={} checksum={}\r", off, sum_off);
    unsafe {
        enable_memory();
    }
    super::put(b"@@MMU enabled\r\n");
    let (on, sum_on) = workload();
    let _ = writeln!(Console, "@@BENCH on_ticks={} checksum={}\r", on, sum_on);
    if on != 0 && off >= on * 10 && sum_off == sum_on {
        super::put(b"@@PASS cache-benchmark\r\n");
    } else {
        super::put(b"@@FAIL cache-benchmark\r\n");
    }
}

fn interrupt_gate(frequency: u32) {
    super::put(b"@@IRQ starting\r\n");
    unsafe {
        super::interrupts::start(frequency);
    }
    let start = counter();
    let first = super::interrupts::ticks();
    while counter().wrapping_sub(start) < frequency as u64 {}
    let elapsed = counter().wrapping_sub(start);
    let ticks = super::interrupts::ticks().wrapping_sub(first);
    let _ = writeln!(
        Console,
        "@@TIMER ticks={} elapsed={} frequency={}\r",
        ticks, elapsed, frequency
    );
    if ticks >= 990 && ticks <= 1010 {
        super::put(b"@@PASS timer-irq\r\n@@ECHO_READY\r\n");
    } else {
        super::put(b"@@FAIL timer-irq\r\n");
        super::reset();
    }
}

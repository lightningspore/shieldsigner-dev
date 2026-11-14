// SPDX-License-Identifier: MIT
//! Initial offline RAW-to-NV12 diagnostic. Not the Phase8 gate or a 3A driver.
use core::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use core::{
    arch::asm,
    fmt::Write,
    ptr::{read_volatile, write_volatile},
};
static FRAMES: AtomicU32 = AtomicU32::new(0);
static OUTPUTS: AtomicU32 = AtomicU32::new(0);
static PARAMETER_UPDATES: AtomicU32 = AtomicU32::new(0);
static PENDING_READY: AtomicBool = AtomicBool::new(false);
static mut PENDING_GAINS: [u32; 8] = [0; 8];
#[cfg(feature = "isp-3a-test")]
static mut PENDING_MEASUREMENT: [(usize, u32); super::isp_awb::MAX_WRITES] =
    [(0, 0); super::isp_awb::MAX_WRITES];
static MEASUREMENT_WRITES: AtomicU32 = AtomicU32::new(0);
static COMPLETED_MEASUREMENTS: AtomicU32 = AtomicU32::new(0);
const MEASUREMENT_CONTROLS: [(usize, u32); 9] = [
    (0x4500, 7),
    (0x4600, 8),
    (0x4700, 9),
    (0x4400, 10),
    (0x4900, 11),
    (0x4a00, 12),
    (0x4b00, 13),
    (0x4800, 14),
    (0x5000, 5),
];
const ISP: usize = 0xffa00000;
const OUTPUT: usize = 0x03800000;
const STATS: usize = 0x03a00000;
const Y_BYTES: usize = 640 * 480;
unsafe fn read(offset: usize) -> u32 {
    read_volatile((ISP + offset) as *const u32)
}
unsafe fn write(offset: usize, value: u32) {
    write_volatile((ISP + offset) as *mut u32, value);
    asm!("dsb sy", options(nostack));
}
fn delay(us: u64) {
    let start = super::cpu::counter();
    while super::cpu::counter() - start < us * 24 {}
}
unsafe fn fixed_register_audit() {
    // Only documented ordinary configuration registers: no LUT/FIFO read ports.
    // Dynamic DONE/config-update bits and RAWAWB selector read normalization
    // have explicit masks. DMA addresses are checked separately by buffer role.
    for (offset, mask) in [
        (0x4, u32::MAX),
        (0x18, u32::MAX),
        (0x400, !0x210),
        (0x404, u32::MAX),
        (0xc00, !0x300),
        (0x4500, 0x7fffffff),
        (0x4600, 0x7fffffff),
        (0x4900, 0x7fffffff),
        (0x4a00, 0x7fffffff),
        (0x5000, 0x7fff000f),
        (0x5004, u32::MAX),
    ] {
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_FIXED_REG {:#06x} {:#010x} mask={:#010x}\r",
            offset,
            read(offset),
            mask
        );
    }
    for (start, end) in [
        (0x408, 0x418),
        (0x594, 0x5a4),
        (0x700, 0x72c),
        (0x800, 0x810),
        (0xc04, 0xc18),
        (0x2224, 0x2240),
        (0x2504, 0x2514),
        (0x3004, 0x3018),
        (0x3400, 0x3420),
        (0x3500, 0x3520),
        (0x3a04, 0x3a18),
        (0x3f04, 0x3f14),
        (0x4504, 0x450c),
        (0x4904, 0x4914),
        (0x5008, 0x5024),
    ] {
        for offset in (start..end).step_by(4) {
            let _ = writeln!(
                super::cpu::Console,
                "@@ISP_FIXED_REG {:#06x} {:#010x} mask=0xffffffff\r",
                offset,
                read(offset)
            );
        }
    }
}
pub fn irq() {
    unsafe {
        let isp = read(0x5c4);
        let mi = read(0x1500);
        if isp & 2 != 0 {
            let mut mask = 0;
            for (offset, bit) in MEASUREMENT_CONTROLS {
                if read(offset) & 0x80000000 != 0 {
                    mask |= 1 << bit;
                }
            }
            COMPLETED_MEASUREMENTS.store(mask, Ordering::Release);
            if PENDING_READY.swap(false, Ordering::AcqRel) {
                for i in 0..8 {
                    write(
                        0x530 + i * 4,
                        read_volatile(core::ptr::addr_of!(PENDING_GAINS).cast::<u32>().add(i)),
                    );
                }
                #[cfg(feature = "isp-3a-test")]
                for i in 0..MEASUREMENT_WRITES.load(Ordering::Relaxed) as usize {
                    let (offset, value) = read_volatile(
                        core::ptr::addr_of!(PENDING_MEASUREMENT)
                            .cast::<(usize, u32)>()
                            .add(i),
                    );
                    write(offset, value);
                }
                write(0x400, read(0x400) | 0x90); // AWB enable and frame-boundary configuration update
                PARAMETER_UPDATES.fetch_add(1, Ordering::Release);
            }
            FRAMES.fetch_add(1, Ordering::Release);
        }
        if mi & 1 != 0 {
            OUTPUTS.fetch_add(1, Ordering::Release);
        }
        write(0x5c8, isp);
        write(0x1504, mi);
    }
}
unsafe fn statistics(frame: u32, parameters: u32) {
    use shieldsigner_rkaiq::statistics::{Channel, Statistics, BUFFER_BYTES, MEASUREMENT_OFFSET};
    let mask = COMPLETED_MEASUREMENTS.load(Ordering::Acquire);
    for (offset, _) in MEASUREMENT_CONTROLS {
        let control = read(offset);
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_MEAS_CTRL {:#06x} {:#010x}\r",
            offset,
            control
        );
    }
    // The kernel populates this metadata, not the DMA engine. Derive validity
    // only from completed hardware measurement blocks; no fabricated validity.
    write_volatile((STATS + MEASUREMENT_OFFSET) as *mut u32, mask);
    write_volatile((STATS + MEASUREMENT_OFFSET + 4) as *mut u32, frame);
    write_volatile((STATS + MEASUREMENT_OFFSET + 8) as *mut u32, parameters);
    asm!("dsb sy", options(nostack));
    let bytes = core::slice::from_raw_parts(STATS as *const u8, BUFFER_BYTES);
    let stats = Statistics::parse(bytes).unwrap();
    let _ = writeln!(
        super::cpu::Console,
        "@@ISP_STATS mask={:#x} ae0_samples={} histogram0_samples={} awb_samples={}\r",
        stats.measurements(),
        stats.ae(Channel::Ae0).map_or(0, |s| s.count()),
        stats.histogram(Channel::Ae0).map_or(0, |s| s.count()),
        stats.awb().map_or(0, |s| s.count())
    );
    if let Some(samples) = stats.ae(Channel::Ae0) {
        let sum = samples.fold([0u32; 3], |mut sum, s| {
            sum[0] += s.red as u32;
            sum[1] += s.green as u32;
            sum[2] += s.blue as u32;
            sum
        });
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_AE0 mean_r={} mean_g={} mean_b={}\r",
            sum[0] / 25,
            sum[1] / 25,
            sum[2] / 25
        );
    }
    let changed = (0..BUFFER_BYTES)
        .step_by(4)
        .filter(|offset| read_volatile((STATS + offset) as *const u32) != 0xa5a5a5a5)
        .count();
    let _ = writeln!(
        super::cpu::Console,
        "@@ISP_STATS_DMA changed_words={}\r",
        changed
    );
}
#[cfg(feature = "isp-3a-test")]
pub fn stage_gains(
    old: &[u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
    params: &[u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
) -> Result<(), &'static str> {
    if PENDING_READY.load(Ordering::Acquire) {
        return Err("isp-pending-gains-busy");
    }
    unsafe {
        let mut changes = [(0, 0); super::isp_awb::MAX_WRITES];
        let count = super::isp_awb::changes(old, params, read(0x5000), &mut changes)?;
        for (i, entry) in changes[..count].iter().enumerate() {
            write_volatile(
                core::ptr::addr_of_mut!(PENDING_MEASUREMENT)
                    .cast::<(usize, u32)>()
                    .add(i),
                *entry,
            );
        }
        MEASUREMENT_WRITES.store(count as u32, Ordering::Relaxed);
        for i in 0..8 {
            let at = shieldsigner_rkaiq::isp32::AWB_GAIN_OFFSET + i * 4;
            write_volatile(
                core::ptr::addr_of_mut!(PENDING_GAINS).cast::<u32>().add(i),
                u32::from_le_bytes(params[at..at + 4].try_into().unwrap()),
            );
        }
    }
    PENDING_READY.store(true, Ordering::Release);
    Ok(())
}
#[cfg(feature = "isp-3a-test")]
pub fn next_frame(raw: usize, frame: u32, parameters: u32) -> Result<usize, &'static str> {
    unsafe {
        for offset in [
            0x4500, 0x4600, 0x4700, 0x4400, 0x4900, 0x4a00, 0x4b00, 0x4800, 0x5000,
        ] {
            write(offset, read(offset)); // completed measurement W1C acknowledgement
        }
        write(0x5dc, u32::MAX);
        write(0x5c8, u32::MAX);
        write(0x1504, u32::MAX);
        write(0x1890, raw as u32);
        write(0x1408, OUTPUT as u32);
        write(0x141c, (OUTPUT + Y_BYTES) as u32);
        write(0x197c, STATS as u32);
        write(0x1400, read(0x1400) | 1);
        write(0x1800, 0x10);
        write(0x1400, read(0x1400) & !1);
        let previous_frames = FRAMES.load(Ordering::Acquire);
        let previous_outputs = OUTPUTS.load(Ordering::Acquire);
        super::interrupts::isp_irqs_enabled(true);
        write(0x1c00, 0x20820401);
        let start = super::cpu::counter();
        while FRAMES.load(Ordering::Acquire) == previous_frames
            || OUTPUTS.load(Ordering::Acquire) == previous_outputs
        {
            if super::cpu::counter() - start > 24_000_000 {
                super::interrupts::isp_irqs_enabled(false);
                return Err("isp-feedback-timeout");
            }
        }
        super::interrupts::isp_irqs_enabled(false);
        if PENDING_READY.load(Ordering::Acquire)
            || PARAMETER_UPDATES.load(Ordering::Acquire) != parameters + 1
        {
            return Err("isp-boundary-update-count");
        }
        if read(0x150c) != 0 {
            return Err("isp-feedback-mi-error");
        }
        let mut matched = 0;
        for i in 0..6 {
            let expected = read_volatile(core::ptr::addr_of!(PENDING_GAINS).cast::<u32>().add(i));
            let actual = read(0x530 + i * 4);
            let same = if i < 2 {
                actual & 0xfff == expected & 0xfff
                    && (actual >> 12) & 0xfff == (expected >> 16) & 0xfff
            } else {
                actual == expected
            };
            if same {
                matched += 1;
            }
        }
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_GAIN_READBACK matched={} checked=6 unresolved_gain2=2\r",
            matched
        );
        if matched != 6 {
            return Err("isp-gain-readback");
        }
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_FEEDBACK_FRAME frame={} measured_parameters={} boundary_updates={}\r",
            frame,
            parameters,
            PARAMETER_UPDATES.load(Ordering::Acquire)
        );
        statistics(frame, parameters);
        Ok(STATS)
    }
}
pub fn run(raw: usize, frame_us: u64) {
    FRAMES.store(0, Ordering::Release);
    OUTPUTS.store(0, Ordering::Release);
    PARAMETER_UPDATES.store(0, Ordering::Release);
    PENDING_READY.store(false, Ordering::Release);
    COMPLETED_MEASUREMENTS.store(0, Ordering::Release);
    #[cfg(not(feature = "isp-3a-test"))]
    let _ = frame_us;
    super::put(b"@@ISP_DIAGNOSTIC offline-fixed-parameters; no-3A-gate\r\n");
    unsafe {
        // Ungate only ISP HCLK/ACLK/core; reset only the ISP core.
        write_volatile(0xff3b4800 as *mut u32, 0x03800000);
        write_volatile(0xff3b4a00 as *mut u32, 0x02000200);
        asm!("dsb sy", options(nostack));
        delay(10);
        write_volatile(0xff3b4a00 as *mut u32, 0x02000000);
        asm!("dsb sy", options(nostack));
        delay(10);
        for base in [OUTPUT, STATS] {
            for offset in (0..0x100000).step_by(4) {
                write_volatile((base + offset) as *mut u32, 0xa5a5a5a5);
            }
        }
        // Internal clock gates are direct hw.c stores outside the partial trace.
        write(0x10, 0x0001797b);
        write(0x0c, 0);
        let writes = if cfg!(feature = "isp-stats-test") {
            super::isp_replay_data::MEASUREMENT_WRITES
        } else {
            super::isp_replay_data::WRITES
        };
        for &(offset, literal, role) in writes {
            let value = match role {
                0 => literal,
                1 => OUTPUT as u32,
                2 => (OUTPUT + Y_BYTES) as u32,
                3 => raw as u32,
                4 => STATS as u32,
                _ => {
                    super::put(b"@@FAIL isp-buffer-role\r\n");
                    return;
                }
            };
            if offset == 0x1c00 && value == 0x20820401 {
                write(0x5bc, 2); // ISP frame-end only
                write(0x5d0, 0); // measurements inspected after frame, no 3A IRQ
                write(0x14f8, 1); // main-path output completion
                write(0x5c8, u32::MAX);
                write(0x1504, u32::MAX);
                super::interrupts::isp_irqs_enabled(true);
            }
            write(offset, value);
        }
        let start = super::cpu::counter();
        while super::cpu::counter() - start < 24_000_000 {
            if OUTPUTS.load(Ordering::Acquire) != 0 && FRAMES.load(Ordering::Acquire) != 0 {
                break;
            }
        }
        super::interrupts::isp_irqs_enabled(false);
        let _ = writeln!(
            super::cpu::Console,
            "@@ISP_IRQ frames={} outputs={}\r",
            FRAMES.load(Ordering::Acquire),
            OUTPUTS.load(Ordering::Acquire)
        );
        for offset in [
            0x8, 0x10, 0x400, 0x5c0, 0x5d4, 0x1400, 0x1478, 0x14fc, 0x150c, 0x1890, 0x1898, 0x1c00,
            0x1c84, 0x1cb0,
        ] {
            let _ = writeln!(
                super::cpu::Console,
                "@@ISP_REG {:#06x} {:#010x}\r",
                offset,
                read(offset)
            );
        }
        // Stop input after bounded polling, regardless of completion.
        write(0x1c00, read(0x1c00) & !1);
        if cfg!(feature = "isp-stats-test") {
            statistics(0, 0);
        }
        fixed_register_audit();
        #[cfg(feature = "isp-3a-test")]
        super::isp_3a::diagnose(STATS, frame_us);
        let changed = (0..Y_BYTES * 3 / 2)
            .step_by(4)
            .filter(|offset| read_volatile((OUTPUT + offset) as *const u32) != 0xa5a5a5a5)
            .count();
        let _ = writeln!(super::cpu::Console, "@@ISP_DMA changed_words={}\r", changed);
        if changed == 0 {
            super::put(b"@@FAIL isp-output-unchanged\r\n");
            return;
        }
        #[cfg(feature = "runtime-board")]
        super::runtime::camera_validated();
        #[cfg(not(feature = "runtime-board"))]
        {
            super::put(b"@@ISP_YUV_BEGIN 160 120\r\n");
            const HEX: &[u8] = b"0123456789abcdef";
            for y in 0..120 {
                super::put(b"@@ISP_YUV ");
                for x in 0..160 {
                    let uv = OUTPUT + Y_BYTES + y * 2 * 640 + x * 4;
                    for address in [OUTPUT + y * 4 * 640 + x * 4, uv, uv + 1] {
                        let value = read_volatile(address as *const u8);
                        super::put(&[HEX[(value >> 4) as usize], HEX[(value & 15) as usize]]);
                    }
                }
                super::put(b"\r\n");
            }
            super::put(b"@@ISP_YUV_END\r\n@@ISP_DIAGNOSTIC_FINISHED\r\n");
        }
    }
}

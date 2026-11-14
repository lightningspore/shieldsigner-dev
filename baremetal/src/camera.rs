// SPDX-License-Identifier: MIT
//! Original raw-camera diagnostic: named SC3336 and RV1103 receiver drivers.
//! Phase7 passed; optional ISP diagnostic consumes the last completed raw buffer.
mod receiver;
mod sc3336;
mod sensor_mode;
use core::arch::asm;
use core::fmt::Write;
use core::ptr::{read_volatile, write_volatile};
const CIF: usize = 0xffa10000;
const BUFFERS: [usize; 2] = [0x03000000, 0x03400000];
const FRAME_BYTES: usize = receiver::FRAME_BYTES;
#[cfg(feature = "isp-3a-test")]
pub const CONTROL_FRAME_LINES: u32 = sc3336::FRAME_LINES as u32;
#[cfg(all(feature = "isp-3a-test", not(feature = "runtime-board")))]
pub const CONTROL_INITIAL_LINES: u32 = sc3336::NORMAL_EXPOSURE as u32;
#[cfg(feature = "isp-3a-test")]
pub fn initial_control_lines() -> u32 {
    #[cfg(feature = "runtime-board")]
    {
        super::runtime::camera_seed()
    }
    #[cfg(not(feature = "runtime-board"))]
    {
        CONTROL_INITIAL_LINES
    }
}
unsafe fn read(address: usize) -> u32 {
    read_volatile(address as *const u32)
}
unsafe fn write(address: usize, value: u32) {
    write_volatile(address as *mut u32, value);
    asm!("dsb sy", options(nostack));
}
unsafe fn masked(address: usize, mask: u32, value: u32) {
    write(address, (mask << 16) | (value & mask));
}
fn delay_us(us: u64) {
    let start = super::cpu::counter();
    while super::cpu::counter().wrapping_sub(start) < us * 24 {}
}
unsafe fn prepare_receiver() {
    // REF's measured clock mux selects the24MHz oscillator despite the sensor
    // mode's27MHz nominal declaration. Match the live reference for Phase7.
    masked(0xff3b036c, 3, 2);
    super::put(b"@@CAM_MCLK reference-mux-xin24m target_hz=24000000\r\n");
    // Preserve inherited PLLs. VI root mux0 matches REF; actual inherited rates may differ.
    masked(0xff3b4300, 0x7f, 0);
    // VI bus roots, VICAP d/a/h clocks, external input gates; retain unrelated ISP gates.
    masked(0xff3b4800, 0xfc07, 0);
    masked(0xff3b4804, 0x401f, 0);
    // VICAP wrapper PCLK in VEPU domain, required by the REF device tree.
    masked(0xff3ba800, 1 << 14, 0);
    // Reset only VICAP/CSI0/D-PHY, then release while their clocks are running.
    masked(0xff3b4a00, 0xfc00, 0xfc00);
    masked(0xff3b4a04, 0x4017, 0x4017);
    delay_us(10);
    masked(0xff3b4a00, 0xfc00, 0);
    masked(0xff3b4a04, 0x4017, 0);
    delay_us(10);
    let _ = writeln!(
        super::cpu::Console,
        "@@CAM_CLOCK sel={:#x} gate0={:#x} gate1={:#x}\r",
        read(0xff3b4300),
        read(0xff3b4800),
        read(0xff3b4804)
    );
    for base in BUFFERS {
        for offset in (0..FRAME_BYTES).step_by(4) {
            write_volatile((base + offset) as *mut u32, 0xa5a5a5a5);
        }
    }
    asm!("dsb sy", options(nostack));
}
#[cfg(feature = "camera-replay")]
fn replay() -> Result<(), &'static str> {
    for &(kind, address, value, delay) in super::camera_replay_data::SETUP {
        delay_us(delay as u64);
        if kind == 2 {
            if address > 65535 || value > 255 {
                return Err("sensor-width");
            }
            if address == 0x100 && value == 1 {
                // User-authorized lights-out test: near full-frame integration,
                // sensor analog gain stage0x5f and4x digital gain. Not an AE result.
                for (register, value) in [
                    (0x3e00, 7),
                    (0x3e01, 255),
                    (0x3e02, 0x70),
                    (0x3e06, 3),
                    (0x3e07, 0x80),
                    (0x3e09, 0x5f),
                ] {
                    super::i2c::write_sensor(register, value)?;
                }
                super::put(b"@@CAM_SETTINGS exposure_lines=32759 vts=32767 again=0x5f dgain=0x03 fine=0x80\r\n");
                if cfg!(feature = "camera-pattern") {
                    // Keep diagnostic bars below clipping; high scene gain also
                    // amplifies sensor-generated values on this sensor.
                    for (register, value) in [
                        (0x3e00, 0),
                        (0x3e01, 8),
                        (0x3e02, 0),
                        (0x3e06, 0),
                        (0x3e07, 0x80),
                        (0x3e09, 0),
                    ] {
                        super::i2c::write_sensor(register, value)?;
                    }
                    // Sensor driver documents bit3; preserve the observed other bits.
                    super::i2c::write_sensor(0x4501, 0xcc)?;
                    super::put(b"@@CAM_PATTERN exposure_lines=128 unity_gain; sensor-generated; not a real-scene gate\r\n");
                }
            }
            super::i2c::write_sensor(address as u16, value as u8)?;
            if address == 0x103 {
                delay_us(5000);
            }
        } else {
            let allowed = if kind == 1 {
                address == 0xff050014
            } else {
                (0xffa10000..0xffa30000).contains(&address)
                    || (0xff3e8000..0xff3f0000).contains(&address)
            };
            if !allowed || address & 3 != 0 {
                return Err("mmio-range");
            }
            unsafe {
                // Polling capture: leave interrupt sources disabled at the peripheral.
                write(address, if address == CIF + 0x174 { 0 } else { value });
            }
        }
    }
    Ok(())
}
fn configure_camera() -> Result<(), &'static str> {
    #[cfg(feature = "camera-replay")]
    {
        super::put(b"@@CAM_DRIVER legacy-reference-replay\r\n");
        replay()
    }
    #[cfg(not(feature = "camera-replay"))]
    {
        super::put(b"@@CAM_DRIVER named-sc3336-rv1103\r\n");
        unsafe {
            receiver::configure();
        }
        sc3336::configure(cfg!(feature = "camera-pattern"))?;
        if cfg!(feature = "isp-3a-test") {
            Ok(())
        } else {
            sc3336::start()
        }
    }
}
fn stop_stream() -> Result<(), &'static str> {
    let result = sc3336::stop();
    receiver::stop();
    delay_us(10000);
    result
}
#[cfg(not(feature = "isp-test"))]
fn sample(base: usize, x: usize, y: usize) -> u8 {
    let bit = x * 10;
    let address = base + y * 3072 + bit / 8;
    unsafe {
        let word = (read_volatile(address as *const u8) as u32)
            | ((read_volatile((address + 1) as *const u8) as u32) << 8)
            | ((read_volatile((address + 2) as *const u8) as u32) << 16);
        ((word >> (bit % 8 + 2)) & 255) as u8
    }
}
#[cfg(not(feature = "isp-test"))]
fn preview(base: usize) {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    super::put(b"@@RGB_BEGIN 192 108\r\n");
    for y in 0..108 {
        super::put(b"@@RGB ");
        for x in 0..192 {
            let sx = x * 12;
            let sy = y * 12;
            let b = sample(base, sx, sy);
            let r = sample(base, sx + 1, sy + 1);
            let g = ((sample(base, sx + 1, sy) as u16 + sample(base, sx, sy + 1) as u16) / 2) as u8;
            for value in [r, g, b] {
                super::put(&[HEX[(value >> 4) as usize], HEX[(value & 15) as usize]]);
            }
        }
        super::put(b"\r\n");
    }
    super::put(b"@@RGB_END\r\n");
}
pub fn run() {
    if let Err(error) = super::i2c::init() {
        let _ = writeln!(super::cpu::Console, "@@FAIL camera-init {}\r", error);
        return;
    }
    let id = super::i2c::read_id(0x30, false, false);
    let _ = writeln!(super::cpu::Console, "@@CAM_SENSOR {:?}\r", id);
    if id != Ok(0xcc41) {
        super::put(b"@@FAIL camera-sensor-id\r\n");
        return;
    }
    unsafe {
        prepare_receiver();
    }
    if let Err(error) = configure_camera() {
        let _ = writeln!(super::cpu::Console, "@@FAIL camera-configure {}\r", error);
        let _ = stop_stream();
        return;
    }
    // Configuration readbacks for comparison with REF. No full-range claim;
    // frame/interrupt status values are dynamic and must be interpreted separately.
    for &address in super::camera_replay_data::READBACK {
        let _ = writeln!(
            super::cpu::Console,
            "@@CAM_REG {:#010x} {:#010x}\r",
            address,
            unsafe { read(address) }
        );
    }
    let mut last_buffer = 0;
    #[cfg(feature = "isp-3a-test")]
    if let Err(error) = sc3336::start() {
        let _ = writeln!(super::cpu::Console, "@@FAIL camera-start {}\r", error);
        return;
    }
    let mut previous_buffer = None;
    let mut first_end = 0;
    let mut last_end = 0;
    for frame in 0..10 {
        let start = super::cpu::counter();
        loop {
            let status = receiver::status();
            let completed = match receiver::completed_buffer(status) {
                Ok(completed) => completed,
                Err(error) => {
                    let _ = writeln!(
                        super::cpu::Console,
                        "@@FAIL camera-status {} {:#x}\r",
                        error,
                        status
                    );
                    let _ = stop_stream();
                    return;
                }
            };
            if let Some(buffer) = completed {
                if previous_buffer == Some(buffer)
                    || (frame > 0 && super::cpu::counter() - start > 28_800_000)
                {
                    super::put(b"@@FAIL camera-frame-sequence\r\n");
                    let _ = stop_stream();
                    return;
                }
                last_buffer = buffer;
                last_end = super::cpu::counter();
                if frame == 0 {
                    first_end = last_end;
                }
                previous_buffer = Some(buffer);
                receiver::acknowledge(status);
                // At30fps the vertical blank is shorter than a UART log line.
                // Stop on the last frame boundary before printing, avoiding a
                // mid-packet stop that leaves CSI/VICAP size-error state.
                if cfg!(feature = "isp-3a-test") && frame == 9 {
                    if let Err(error) = stop_stream() {
                        let _ = writeln!(
                            super::cpu::Console,
                            "@@FAIL camera-boundary-stop {}\r",
                            error
                        );
                        return;
                    }
                }
                let _ = writeln!(
                    super::cpu::Console,
                    "@@CAM_FRAME {} status={:#x} buffer={} us={}\r",
                    frame,
                    status,
                    last_buffer,
                    (super::cpu::counter() - start) / 24
                );
                break;
            }
            if super::cpu::counter() - start > 120000000 {
                let _ = writeln!(
                    super::cpu::Console,
                    "@@FAIL camera-frame-timeout status={:#x} ctrl={:#x} phy={:#x}\r",
                    status,
                    unsafe { read(CIF + 0x100) },
                    unsafe { read(0xff3e8000) }
                );
                let _ = stop_stream();
                return;
            }
        }
    }
    if let Err(error) = stop_stream() {
        let _ = writeln!(super::cpu::Console, "@@FAIL camera-stop {}\r", error);
        return;
    }
    let base = BUFFERS[last_buffer];
    let mut changed = 0;
    for offset in (0..FRAME_BYTES).step_by(4) {
        if unsafe { read(base + offset) } != 0xa5a5a5a5 {
            changed += 1;
        }
    }
    let _ = writeln!(super::cpu::Console, "@@CAM_DMA changed_words={}\r", changed);
    if changed == 0 {
        super::put(b"@@FAIL camera-dma-unchanged\r\n");
        return;
    }
    #[cfg(not(feature = "isp-test"))]
    preview(base);
    super::put(b"@@PASS camera-raw-ten-frames\r\n");
    #[cfg(feature = "isp-test")]
    super::isp::run(base, (last_end - first_end) / (9 * 24));
}

/// Bounded stop/configure/start cycle. Discard two frames for sensor latch
/// settling and return the third completed buffer, rather than assuming that
/// an I2C acknowledgement associates a setting with the immediately next frame.
#[cfg(feature = "isp-3a-test")]
pub fn next_raw(lines: u32, gain: u32) -> Result<usize, &'static str> {
    sc3336::apply_linear(lines, gain)?;
    unsafe {
        receiver::configure();
    }
    sc3336::start()?;
    let result = (|| {
        let mut previous = None;
        let mut last = 0;
        for _ in 0..3 {
            let start = super::cpu::counter();
            loop {
                let status = receiver::status();
                let completed = receiver::completed_buffer(status).map_err(|error| {
                    let _ = writeln!(
                        super::cpu::Console,
                        "@@CAM_FEEDBACK_ERROR status={:#x} csi_err1={:#x} csi_err2={:#x}\r",
                        status,
                        unsafe { read(0xffa20020) },
                        unsafe { read(0xffa20024) }
                    );
                    error
                })?;
                if let Some(buffer) = completed {
                    if previous == Some(buffer) {
                        return Err("feedback-raw-sequence");
                    }
                    previous = Some(buffer);
                    last = buffer;
                    receiver::acknowledge(status);
                    break;
                }
                if super::cpu::counter() - start > 120_000_000 {
                    return Err("feedback-raw-timeout");
                }
            }
        }
        Ok(BUFFERS[last])
    })();
    let stopped = stop_stream();
    match (result, stopped) {
        (Ok(base), Ok(())) => Ok(base),
        (Err(e), _) | (_, Err(e)) => Err(e),
    }
}

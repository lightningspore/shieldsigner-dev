// SPDX-License-Identifier: MIT
//! Original SC3336 control logic. Opaque analog preset values are measured facts;
//! reset, frame timing, gain, orientation and streaming are explicit operations.
use super::super::{cpu::Console, i2c};
use core::fmt::Write;
const STREAM: u16 = 0x0100;
const RESET: u16 = 0x0103;
const VTS_HIGH: u16 = 0x320e;
const VTS_LOW: u16 = 0x320f;
const EXPOSURE_HIGH: u16 = 0x3e00;
const EXPOSURE_MIDDLE: u16 = 0x3e01;
const EXPOSURE_LOW: u16 = 0x3e02;
const DIGITAL_GAIN: u16 = 0x3e06;
const FINE_GAIN: u16 = 0x3e07;
const ANALOG_GAIN: u16 = 0x3e09;
const ORIENTATION: u16 = 0x3221;
const TEST_PATTERN: u16 = 0x4501;
pub const FRAME_LINES: u16 = if cfg!(feature = "isp-3a-test") {
    1360
} else {
    32767
};
#[cfg(not(feature = "runtime-board"))]
pub const NORMAL_EXPOSURE: u16 = if cfg!(feature = "isp-3a-test") {
    122
} else {
    8192
};

fn set_frame_length(lines: u16) -> Result<(), &'static str> {
    if !(1304..=32767).contains(&lines) {
        return Err("sensor-frame-length");
    }
    i2c::write_sensor(VTS_HIGH, (lines >> 8) as u8)?;
    i2c::write_sensor(VTS_LOW, lines as u8)
}
fn set_exposure(lines: u16) -> Result<(), &'static str> {
    if lines == 0 || lines > FRAME_LINES - 8 {
        return Err("sensor-exposure-range");
    }
    // Low4 bits of the20-bit register encoding are fractional exposure.
    i2c::write_sensor(EXPOSURE_HIGH, ((lines >> 12) & 15) as u8)?;
    i2c::write_sensor(EXPOSURE_MIDDLE, (lines >> 4) as u8)?;
    i2c::write_sensor(EXPOSURE_LOW, ((lines & 15) << 4) as u8)
}
fn set_diagnostic_gain(low_light: bool) -> Result<(), &'static str> {
    // Unity gain for synthetic bars; measured high-gain stages for lights-out
    // scene testing. These are fixed diagnostics, not auto-exposure decisions.
    i2c::write_sensor(DIGITAL_GAIN, if low_light { 3 } else { 0 })?;
    i2c::write_sensor(FINE_GAIN, 0x80)?;
    i2c::write_sensor(ANALOG_GAIN, if low_light { 0x5f } else { 0 })
}
#[cfg(feature = "isp-3a-test")]
pub fn apply_linear(lines: u32, gain_code: u32) -> Result<(), &'static str> {
    if lines == 0 || lines > (FRAME_LINES - 8) as u32 || !(128..=99614).contains(&gain_code) {
        return Err("sensor-linear-control-range");
    }
    set_exposure(lines as u16)?;
    // SC3336 coarse gain stage anchors, units1/1000, with Q7 fine gain.
    // Select the highest stage not exceeding the requested multiplier.
    let stages = [
        (1000, 0x00, 0),
        (1520, 0x40, 0),
        (3040, 0x48, 0),
        (6080, 0x49, 0),
        (12160, 0x4b, 0),
        (24320, 0x4f, 0),
        (48640, 0x5f, 0),
        (97280, 0x5f, 1),
        (194560, 0x5f, 3),
        (389120, 0x5f, 7),
    ];
    let factor = gain_code * 1000 / 128;
    let &(anchor, analog, digital) = stages.iter().rev().find(|stage| factor >= stage.0).unwrap();
    let fine = (factor * 128 / anchor).min(255) as u8;
    for (register, value) in [
        (DIGITAL_GAIN, digital),
        (FINE_GAIN, fine),
        (ANALOG_GAIN, analog),
    ] {
        i2c::write_sensor(register, value)?;
        if i2c::read_sensor(register)? != value {
            return Err("sensor-gain-readback");
        }
    }
    for (register, value) in [
        (EXPOSURE_HIGH, ((lines >> 12) & 15) as u8),
        (EXPOSURE_MIDDLE, (lines >> 4) as u8),
        (EXPOSURE_LOW, ((lines & 15) << 4) as u8),
    ] {
        if i2c::read_sensor(register)? != value {
            return Err("sensor-exposure-readback");
        }
    }
    Ok(())
}
pub fn configure(pattern: bool) -> Result<(), &'static str> {
    i2c::write_sensor(RESET, 1)?;
    super::delay_us(5000);
    for &(register, value) in super::sensor_mode::MODE_PRESET {
        i2c::write_sensor(register, value)?;
    }
    super::delay_us(1000);
    set_frame_length(FRAME_LINES)?;
    let low_light = !pattern && cfg!(feature = "camera-low-light");
    let exposure = if pattern {
        128
    } else if low_light {
        FRAME_LINES - 8
    } else {
        #[cfg(feature = "runtime-board")]
        {
            super::initial_control_lines() as u16
        }
        #[cfg(not(feature = "runtime-board"))]
        {
            NORMAL_EXPOSURE
        }
    };
    set_exposure(exposure)?;
    set_diagnostic_gain(low_light)?;
    let orientation = i2c::read_sensor(ORIENTATION)?;
    i2c::write_sensor(ORIENTATION, orientation & !0x66)?;
    let test = i2c::read_sensor(TEST_PATTERN)?;
    i2c::write_sensor(TEST_PATTERN, (test & !8) | if pattern { 8 } else { 0 })?;
    let _ = writeln!(
        Console,
        "@@CAM_SETTINGS named-driver exposure_lines={} vts={} pattern={}\r",
        exposure, FRAME_LINES, pattern
    );
    // Read the actual bus values back before starting a stream. A completed
    // transmit is not sufficient proof that a control has the intended value.
    for (register, expected) in [
        (VTS_HIGH, (FRAME_LINES >> 8) as u8),
        (VTS_LOW, FRAME_LINES as u8),
        (EXPOSURE_HIGH, ((exposure >> 12) & 15) as u8),
        (EXPOSURE_MIDDLE, (exposure >> 4) as u8),
        (EXPOSURE_LOW, ((exposure & 15) << 4) as u8),
        (DIGITAL_GAIN, if low_light { 3 } else { 0 }),
        (FINE_GAIN, 0x80),
        (ANALOG_GAIN, if low_light { 0x5f } else { 0 }),
        (TEST_PATTERN, (test & !8) | if pattern { 8 } else { 0 }),
    ] {
        let actual = i2c::read_sensor(register)?;
        let _ = writeln!(
            Console,
            "@@CAM_SENSOR_REG {:#06x} {:#04x}\r",
            register, actual
        );
        if actual != expected {
            return Err("sensor-control-readback");
        }
    }
    Ok(())
}
pub fn start() -> Result<(), &'static str> {
    i2c::write_sensor(STREAM, 1)
}
pub fn stop() -> Result<(), &'static str> {
    i2c::write_sensor(STREAM, 0)
}

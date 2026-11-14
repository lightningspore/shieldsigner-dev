// SPDX-License-Identifier: MIT
//! Original RV1103 VICAP/CSI0/D-PHY configuration for the proven two-lane mode.
//! Register layouts were studied in the pinned SDK; no Linux implementation is
//! linked here. Timing/calibration choices remain specific to the measured mode.
use super::{masked, read, write, BUFFERS};
const VICAP: usize = 0xffa10000;
const ID0_CONTROL: usize = VICAP + 0x100;
const ID0_SIZE: usize = VICAP + 0x104;
const BUS_CONTROL: usize = VICAP + 0x120;
const FRAME0: usize = VICAP + 0x124;
const FRAME1: usize = VICAP + 0x128;
const STRIDE: usize = VICAP + 0x134;
const INTERRUPT_ENABLE: usize = VICAP + 0x174;
const INTERRUPT_STATUS: usize = VICAP + 0x178;
const LINE_THRESHOLDS_01: usize = VICAP + 0x17c;
const LINE_THRESHOLDS_23: usize = VICAP + 0x180;
const EFFECT_CODE0: usize = VICAP + 0x1ac;
const EFFECT_CODE1: usize = VICAP + 0x1b0;
const CSI: usize = 0xffa20000;
const PHY: usize = 0xff3e8000;
const PHY_GRF: usize = 0xff050014;
const CAPTURE_ENABLE: u32 = 1;
pub const FRAME_END: u32 = 3 << 8;
pub const FIFO_ERRORS: u32 = 0x0f0f0000;
pub const WIDTH: u32 = 2304;
pub const HEIGHT: u32 = 1296;
pub const ROW_STRIDE: u32 = 3072;
pub const FRAME_BYTES: usize = ROW_STRIDE as usize * HEIGHT as usize;

unsafe fn configure_vicap() {
    // Memory bus pressure/hurry thresholds and25% FIFO waterline, as on REF.
    let bus = (3 << 13) | (1 << 12) | (3 << 5) | (1 << 4) | (2 << 1) | 1;
    write(BUS_CONTROL, bus & !1);
    write(INTERRUPT_ENABLE, 0); // This bring-up driver polls; GIC source is unused.
    write(INTERRUPT_STATUS, FIFO_ERRORS | FRAME_END | 3);
    write(LINE_THRESHOLDS_01, 0x3fff3fff);
    write(LINE_THRESHOLDS_23, 0x3fff3fff);
    write(ID0_SIZE, (HEIGHT << 16) | WIDTH);
    write(FRAME0, BUFFERS[0] as u32);
    write(FRAME1, BUFFERS[1] as u32);
    write(STRIDE, ROW_STRIDE);
    // RAW10 packet type0x2b, compact little-endian DDR packing, command mode,
    // two ping-pong addresses and DMA/capture enabled. No HDR or crop.
    let raw10 = (1 << 28) | (0x2b << 10) | (1 << 4) | (1 << 1) | CAPTURE_ENABLE;
    write(ID0_CONTROL, raw10);
    // Retain measured SAV/EAV code fields even though this mode receives CSI2.
    write(EFFECT_CODE0, 0x02410251);
    write(EFFECT_CODE1, 0x02420252);
    write(BUS_CONTROL, bus);
}
unsafe fn configure_csi() {
    write(CSI + 0x04, 1); // two data lanes, encoded as count-1
                          // CSI short-packet data types: frame-start0, frame-end1, line-start2/end3.
    write(CSI + 0x40, (1 << 14) | (2 << 20) | (3 << 26));
    write(CSI + 0x28, 0);
    write(CSI + 0x2c, 0xf000); // mask unrecognized packet-ID reports, matching REF
    write(CSI + 0x10, 1); // release the CSI receiver reset
}
unsafe fn configure_dphy() {
    // Preserve the observed reset-default bit0, enable data lanes0/1 and clock.
    write(PHY, 1 | (3 << 2) | (1 << 6));
    write(PHY + 0x80, 0x1e);
    write(PHY + 0x80, 0x1f); // calibration mask then trigger
    masked(PHY_GRF, 0xf0, 3 << 4);
    masked(PHY_GRF, 1 << 8, 1 << 8);
    masked(PHY_GRF, 0xf, 0); // release forced RX mode
    const SETTLE_FROM_REF: u32 = 0x0e;
    for offset in [0x160, 0x1e0, 0x260] {
        write(PHY + offset, SETTLE_FROM_REF);
    }
    write(PHY + 0x44c, 2); // path0 CSI2 mode
    write(PHY + 0x84, 4); // measured clock-polarity control for this module
}
pub unsafe fn configure() {
    configure_vicap();
    configure_csi();
    configure_dphy();
}
pub fn status() -> u32 {
    unsafe { read(INTERRUPT_STATUS) }
}
pub fn acknowledge(status: u32) {
    unsafe {
        write(INTERRUPT_STATUS, status);
    }
}
pub fn completed_buffer(status: u32) -> Result<Option<usize>, &'static str> {
    if status & FIFO_ERRORS != 0 {
        return Err("receiver-fifo-status");
    }
    match status & FRAME_END {
        0 => Ok(None),
        0x100 => Ok(Some(0)),
        0x200 => Ok(Some(1)),
        _ => Err("receiver-multiple-frame-ends"),
    }
}
pub fn stop() {
    unsafe {
        write(ID0_CONTROL, read(ID0_CONTROL) & !CAPTURE_ENABLE);
    }
}

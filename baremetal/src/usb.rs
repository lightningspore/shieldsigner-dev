// SPDX-License-Identifier: MIT
//! Original RV1103 DWC3 USB2 device driver. Foreground-only ownership; no USB IRQ.
//! DMA lives at 60MiB in the existing noncacheable camera reservation, outside
//! RAW48/52, ISP56 and statistics58MiB. No allocator, filesystem or host mode.
use core::arch::asm;
use core::fmt::Write;
use core::ptr::{read_volatile, write_volatile};
const BASE: usize = 0xffb00000;
const DMA: usize = 0x03c00000;
const EVENT_SIZE: usize = 4096;
const N: usize = 4096;
const DCFG: usize = 0xc700;
const DCTL: usize = 0xc704;
const DSTS: usize = 0xc70c;
const ENABLE: usize = 0xc720;
// Control, interrupt81, bulk02 OUT/82 IN. Physical endpoints0,1,3,4,5.
use super::usb_control::{Completion, Control};
struct State {
    ready: bool,
    configured: bool,
    opened: bool,
    control: Control,
    three_stage: bool,
    event_pos: usize,
    busy: [bool; 6],
    resource: [u32; 6],
    rx: [u8; N],
    rh: usize,
    rt: usize,
    tx: [u8; N],
    th: usize,
    tt: usize,
    line: [u8; 7],
    trace: u32,
    zlp_pending: bool,
}
static mut STATE: State = State {
    ready: false,
    configured: false,
    opened: false,
    control: Control::Setup,
    three_stage: false,
    event_pos: 0,
    busy: [false; 6],
    resource: [0; 6],
    rx: [0; N],
    rh: 0,
    rt: 0,
    tx: [0; N],
    th: 0,
    tt: 0,
    line: [0, 0xc2, 1, 0, 0, 0, 8],
    trace: 0,
    zlp_pending: false,
};
unsafe fn rd(off: usize) -> u32 {
    read_volatile((BASE + off) as *const u32)
}
unsafe fn wr(off: usize, value: u32) {
    write_volatile((BASE + off) as *mut u32, value);
}
unsafe fn modify(off: usize, clear: u32, set: u32) {
    wr(off, (rd(off) & !clear) | set);
}
unsafe fn mask(address: usize, bits: u32, value: u32) {
    write_volatile(address as *mut u32, (bits << 16) | (value & bits));
}
fn barrier() {
    unsafe {
        asm!("dsb sy", options(nostack));
    }
}
fn delay(us: u64) {
    let start = super::cpu::counter();
    while super::cpu::counter().wrapping_sub(start) < us * 24 {}
}
unsafe fn wait(off: usize, bits: u32) -> Result<u32, &'static str> {
    let start = super::cpu::counter();
    loop {
        let v = rd(off);
        if v & bits == 0 {
            return Ok(v);
        }
        if super::cpu::counter().wrapping_sub(start) > 24 * 100_000 {
            return Err("usb-command-timeout");
        }
    }
}
unsafe fn command(ep: usize, cmd: u32, p0: u32, p1: u32, p2: u32) -> Result<u32, &'static str> {
    let off = 0xc800 + ep * 16;
    wr(off, p2);
    wr(off + 4, p1);
    wr(off + 8, p0);
    wr(off + 12, cmd | 0x400);
    let v = wait(off + 12, 0x400)?;
    if (v >> 12) & 15 != 0 {
        return Err("usb-endpoint-command-status");
    }
    Ok(v)
}
unsafe fn configure(ep: usize, kind: u32, packet: u32, action: u32) -> Result<(), &'static str> {
    let fifo = if ep & 1 != 0 { (ep / 2) as u32 } else { 0 };
    command(
        ep,
        1,
        (kind << 1) | (packet << 3) | (fifo << 17) | (action << 30),
        0x500 | ((ep as u32) << 25),
        0,
    )?;
    if action == 0 {
        command(ep, 2, 1, 0, 0)?;
    }
    Ok(())
}
fn trb(ep: usize) -> usize {
    DMA + 0x1000 + ep * 16
}
fn buffer(ep: usize) -> usize {
    DMA + 0x2000 + ep * 1024
}
unsafe fn transfer(s: &mut State, ep: usize, kind: u32, len: usize) -> Result<(), &'static str> {
    if s.busy[ep] {
        return Err("usb-endpoint-busy");
    }
    let t = trb(ep) as *mut u32;
    write_volatile(t, buffer(ep) as u32);
    write_volatile(t.add(1), 0);
    write_volatile(t.add(2), len as u32);
    write_volatile(t.add(3), 1 | 2 | (kind << 4) | (1 << 10) | (1 << 11));
    barrier();
    let value = command(ep, 6, 0, trb(ep) as u32, 0)?;
    s.resource[ep] = (value >> 16) & 0x7f;
    s.busy[ep] = true;
    Ok(())
}
unsafe fn setup(s: &mut State) -> Result<(), &'static str> {
    s.control = Control::Setup;
    transfer(s, 0, 2, 8)
}
unsafe fn send(s: &mut State, data: &[u8], limit: usize) -> Result<(), &'static str> {
    let len = data.len().min(limit);
    core::ptr::copy_nonoverlapping(data.as_ptr(), buffer(1) as *mut u8, len);
    s.control = Control::InData;
    transfer(s, 1, 5, len)
}
unsafe fn stall(s: &mut State) -> Result<(), &'static str> {
    command(0, 4, 0, 0, 0)?;
    setup(s)
}
unsafe fn handle_setup(s: &mut State) -> Result<(), &'static str> {
    let b = core::slice::from_raw_parts(buffer(0) as *const u8, 8);
    let request = b[1];
    let value = u16::from_le_bytes([b[2], b[3]]);
    let index = u16::from_le_bytes([b[4], b[5]]);
    let len = u16::from_le_bytes([b[6], b[7]]) as usize;
    s.three_stage = len != 0;
    if s.trace < 60 {
        let _ = writeln!(
            super::cpu::Console,
            "@@USB_SETUP {:02x} {} {} {} {}\r",
            b[0],
            request,
            value,
            index,
            len
        );
    }
    s.trace += 1;
    match (b[0], request) {
        (0x80, 6) => {
            let mut out = [0u8; 128];
            match super::usb_descriptors::descriptor(value, &mut out) {
                Some(n) => send(s, &out[..n], len)?,
                None => return stall(s),
            }
        }
        (0, 5) if value < 128 && len == 0 => {
            modify(DCFG, 0x7f << 3, (value as u32) << 3);
            s.control = Control::InStatus;
        }
        (0, 9) if value <= 1 && len == 0 => {
            s.configured = value == 1;
            s.opened = false;
            if s.configured {
                command(0, 9 | (2 << 16), 0, 0, 0)?;
                configure(3, 3, 16, 0)?;
                configure(4, 2, 512, 0)?;
                configure(5, 2, 512, 0)?;
                wr(ENABLE, 0x3b);
                transfer(s, 4, 1, 512)?;
            } else {
                wr(ENABLE, 3);
            }
            s.control = Control::InStatus;
        }
        (0x80, 8) => send(s, &[s.configured as u8], len)?,
        (0x80, 0) | (0x81, 0) | (0x82, 0) => send(s, &[0, 0], len)?,
        (0x81, 10) => send(s, &[0], len)?,
        (1, 11) if value == 0 && len == 0 => s.control = Control::InStatus,
        (0x21, 0x22) if index == 0 && len == 0 => {
            s.opened = value & 1 != 0;
            s.control = Control::InStatus;
        }
        (0x21, 0x20) if index == 0 && len == 7 => {
            s.control = Control::OutData;
            transfer(s, 0, 5, 64)?;
        }
        (0xa1, 0x21) if index == 0 => {
            let line = s.line;
            send(s, &line, len)?;
        }
        (2, 1) if value == 0 && len == 0 => {
            let ep = ((index & 15) * 2 + ((index >> 7) & 1)) as usize;
            if ep >= 6 {
                return stall(s);
            }
            command(ep, 5, 0, 0, 0)?;
            s.control = Control::InStatus;
        }
        _ => return stall(s),
    }
    Ok(())
}
unsafe fn event(s: &mut State, ev: u32) -> Result<(), &'static str> {
    if ev & 1 != 0 {
        let kind = (ev >> 8) & 15;
        let _ = writeln!(
            super::cpu::Console,
            "@@USB_DEVICE event={} dsts={:08x}\r",
            kind,
            rd(DSTS)
        );
        match kind {
            0 | 1 => {
                for ep in [0, 1, 3, 4, 5] {
                    if s.busy[ep] && s.resource[ep] != 0 {
                        command(ep, 8 | (1 << 11) | (s.resource[ep] << 16), 0, 0, 0)?;
                    }
                    s.busy[ep] = false;
                    command(ep, 5, 0, 0, 0)?;
                }
                s.configured = false;
                s.opened = false;
                s.rh = 0;
                s.rt = 0;
                s.th = 0;
                s.tt = 0;
                s.zlp_pending = false;
                modify(DCFG, 0x7f << 3, 0);
                wr(ENABLE, 3);
                s.control = Control::Setup;
            }
            2 => {
                let speed = rd(DSTS) & 7;
                if speed != 0 {
                    return Err("usb-high-speed-required");
                }
                configure(0, 0, 64, 2)?;
                configure(1, 0, 64, 2)?;
                if !s.busy[0] {
                    setup(s)?;
                }
            }
            _ => {}
        }
        return Ok(());
    }
    let ep = ((ev >> 1) & 31) as usize;
    let kind = (ev >> 6) & 15;

    if ep >= 6 {
        return Err("usb-unexpected-endpoint");
    }
    if kind == 1 {
        s.busy[ep] = false;
        let remaining = read_volatile((trb(ep) + 8) as *const u32);
        if remaining >> 28 != 0 {
            return Err("usb-trb-status");
        }
        if ep < 2 {
            match s.control.complete(ep)? {
                Completion::Setup => handle_setup(s)?,
                Completion::DataSent => {}
                Completion::LineCoding => {
                    if remaining & 0x00ffffff != 57 {
                        return Err("usb-line-coding-length");
                    }
                    core::ptr::copy_nonoverlapping(buffer(0) as *const u8, s.line.as_mut_ptr(), 7);
                }
                Completion::Finished => setup(s)?,
            }
        } else if ep == 4 {
            let len = 512usize
                .checked_sub((remaining & 0x00ffffff) as usize)
                .ok_or("usb-rx-length")?;
            for i in 0..len {
                let next = (s.rh + 1) % N;
                if next == s.rt {
                    return Err("usb-rx-overflow");
                }
                let byte = read_volatile((buffer(4) + i) as *const u8);
                if byte == 0x1d {
                    super::reset_record::simple(2);
                    super::reset();
                }
                if super::runtime::interrupt(byte) {
                    continue;
                }
                s.rx[s.rh] = byte;
                s.rh = next;
            }
        }
    } else if kind == 3 && ep < 2 {
        if let Some(kind) = s.control.not_ready(ep, s.three_stage)? {
            transfer(s, ep, kind, 0)?;
        }
    }
    Ok(())
}
unsafe fn pump(s: &mut State) -> Result<(), &'static str> {
    // A bounded pass prevents a host from starving Python or timer work.
    for _ in 0..128 {
        if rd(0xc40c) & 0xfffc == 0 {
            break;
        }
        barrier();
        let ev = read_volatile((DMA + s.event_pos) as *const u32);
        s.event_pos = (s.event_pos + 4) % EVENT_SIZE;
        event(s, ev)?;
        wr(0xc40c, 4);
    }
    if s.configured && !s.busy[4] && (s.rt + N - s.rh - 1) % N >= 512 {
        transfer(s, 4, 1, 512)?;
    }
    if s.configured && s.opened && !s.busy[5] && (s.tt != s.th || s.zlp_pending) {
        let mut len = 0;
        while len < 512 && s.tt != s.th {
            write_volatile((buffer(5) + len) as *mut u8, s.tx[s.tt]);
            s.tt = (s.tt + 1) % N;
            len += 1;
        }
        s.zlp_pending = len == 512;
        transfer(s, 5, 1, len)?;
    }
    Ok(())
}
pub fn init() -> Result<(), &'static str> {
    unsafe {
        // PERICRU gates4[7:9] (bus/ref/UTMI), gates5[1:2] (PHY APB/ref).
        mask(0xff3b2810, 0x380, 0);
        mask(0xff3b2814, 6, 0);
        mask(0xff3b2a10, 0x80, 0);
        mask(0xff3b2a14, 0x0e, 0);
        delay(1000);
        let id = rd(0xc120);
        let _ = writeln!(
            super::cpu::Console,
            "@@USB_CORE id={:08x} gctl={:08x} phy={:08x}\r",
            id,
            rd(0xc110),
            rd(0xc200)
        );
        if id >> 16 != 0x5533 {
            return Err("usb-core-id");
        }
        // Rockchip USB GRF: unsuspend PHY, force IDDIG=device, select valid VBUS.
        mask(0xff000050, 0x7ff, 0x600);
        mask(0xff000058, 0xc010, 0xc000);
        delay(1000);
        modify(DCTL, 1 << 31, 0);
        modify(DCTL, 0, 1 << 30);
        wait(DCTL, 1 << 30)?;
        modify(0xc110, 0, 1 << 11);
        modify(0xc200, 0, 1 << 31);
        delay(1000);
        // UTMI16, turnaround5; disable suspend/LPM/free-running-clock quirk.
        modify(
            0xc200,
            (1 << 31) | (1 << 30) | (15 << 10) | (1 << 8) | (1 << 6),
            (1 << 3) | (5 << 10),
        );
        delay(1000);
        modify(
            0xc110,
            (3 << 12) | (1 << 11) | (3 << 4) | (1 << 3) | (1 << 1),
            2 << 12,
        );
        // Stop hibernation, USB2 LPM and SuperSpeed, keep address zero.
        wr(DCFG, 0);
        wr(ENABLE, 0);
        core::ptr::write_bytes(DMA as *mut u8, 0, 0x4000);
        barrier();
        wr(0xc400, DMA as u32);
        wr(0xc404, 0);
        wr(0xc408, EVENT_SIZE as u32);
        wr(0xc40c, 0);
        wr(0xc708, 7 | (1 << 9) | (1 << 11));
        command(0, 9, 0, 0, 0)?;
        configure(0, 0, 64, 0)?;
        configure(1, 0, 64, 0)?;
        wr(ENABLE, 3);
        STATE.ready = true;
        modify(DCTL, 0, 1 << 31);
    }
    super::put(b"@@USB_READY usb2-cdc experimental\r\n");
    Ok(())
}
pub fn poll() {
    unsafe {
        let s = &mut *core::ptr::addr_of_mut!(STATE);
        if !s.ready {
            return;
        }
        if let Err(reason) = pump(s) {
            s.ready = false;
            modify(DCTL, 1 << 31, 0);
            let _ = writeln!(super::cpu::Console, "@@FAIL {}\r", reason);
        }
    }
}
pub fn read() -> Option<u8> {
    poll();
    unsafe {
        let s = &mut *core::ptr::addr_of_mut!(STATE);
        if s.rt == s.rh {
            return None;
        }
        let b = s.rx[s.rt];
        s.rt = (s.rt + 1) % N;
        if b == 0x1d {
            super::reset_record::simple(2);
            super::reset();
        }
        Some(b)
    }
}
pub fn write(data: &[u8]) {
    // Bound backpressure so a closed host cannot permanently wedge the REPL.
    // Never silently truncate an opened-console write: timeout disconnects and
    // leaves an explicit failure on the independent UART recovery console.
    let start = super::cpu::counter();
    let mut pos = 0;
    while pos < data.len() {
        poll();
        unsafe {
            let s = &mut *core::ptr::addr_of_mut!(STATE);
            if !s.ready || !s.opened {
                return;
            }
            while pos < data.len() && (s.th + 1) % N != s.tt {
                s.tx[s.th] = data[pos];
                s.th = (s.th + 1) % N;
                pos += 1;
            }
            if pos < data.len() && super::cpu::counter().wrapping_sub(start) > 24 * 2_000_000 {
                s.ready = false;
                modify(DCTL, 1 << 31, 0);
                super::put(b"@@FAIL usb-output-timeout\r\n");
                return;
            }
        }
    }
    poll();
}

pub fn is_ready() -> bool { unsafe { read_volatile(core::ptr::addr_of!(STATE.ready)) } }

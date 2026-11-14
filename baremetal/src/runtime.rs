// SPDX-License-Identifier: MIT
use core::sync::atomic::{AtomicBool, AtomicI32, AtomicUsize, Ordering};
static INTERRUPT_CHAR: AtomicI32 = AtomicI32::new(-1);
static INTERRUPTED: AtomicBool = AtomicBool::new(false);
pub fn interrupt_pending()->bool{INTERRUPTED.load(Ordering::Acquire)}
pub fn take_interrupt()->bool{INTERRUPTED.swap(false,Ordering::AcqRel)}
pub fn interrupt(byte: u8) -> bool {
    if byte as i32 == INTERRUPT_CHAR.load(Ordering::Relaxed) {
        INTERRUPTED.store(true, Ordering::Release); true
    } else { false }
}
#[no_mangle]
extern "C" fn bm_set_interrupt_char(c: i32) { INTERRUPT_CHAR.store(c, Ordering::Relaxed); }
#[no_mangle]
extern "C" fn bm_console_poll() -> i32 {
    #[cfg(feature = "usb-console")]
    super::usb::poll();
    INTERRUPTED.swap(false, Ordering::AcqRel) as i32
}
const CAPACITY: usize = 4096;
static HEAD: AtomicUsize = AtomicUsize::new(0);
static TAIL: AtomicUsize = AtomicUsize::new(0);
static mut RX: [u8; CAPACITY] = [0; CAPACITY];
pub fn receive(byte: u8) {
    if interrupt(byte) { return; }
    let head = HEAD.load(Ordering::Relaxed);
    let next = (head + 1) % CAPACITY;
    if next != TAIL.load(Ordering::Acquire) {
        unsafe {
            core::ptr::write_volatile(core::ptr::addr_of_mut!(RX).cast::<u8>().add(head), byte);
        }
        HEAD.store(next, Ordering::Release);
    }
}
#[no_mangle]
extern "C" fn bm_uart_getc() -> i32 {
    #[cfg(feature = "usb-console")]
    if let Some(byte) = super::usb::read() { return byte as i32; }
    let tail = TAIL.load(Ordering::Relaxed);
    if tail == HEAD.load(Ordering::Acquire) {
        return -1;
    }
    let byte = unsafe { core::ptr::read_volatile(core::ptr::addr_of!(RX).cast::<u8>().add(tail)) };
    TAIL.store((tail + 1) % CAPACITY, Ordering::Release);
    byte as i32
}
#[no_mangle]
unsafe extern "C" fn bm_uart_write(data: *const u8, len: usize) {
    let bytes = core::slice::from_raw_parts(data, len);
    super::put(bytes);
    #[cfg(feature = "usb-console")]
    super::usb::write(bytes);
}
#[no_mangle]
extern "C" fn bm_ticks_us() -> u32 {
    (super::cpu::counter() / 24) as u32
}
#[no_mangle]
extern "C" fn bm_ticks_ms() -> u32 {
    (super::cpu::counter() / 24000) as u32
}
#[no_mangle]
extern "C" fn bm_delay_us(us: u32) {
    let start = super::cpu::counter();
    while super::cpu::counter() - start < (us as u64) * 24 {
        #[cfg(feature = "usb-console")]
        super::usb::poll();
    }
}
#[no_mangle]
extern "C" fn bm_runtime_fault() -> ! {
    super::put(b"@@FAIL interpreter-fault\r\n");
    super::reset()
}
#[no_mangle]
extern "C" fn bm_repl_ready() {
    #[cfg(feature = "fast-boot")]
    super::boot::repl_ready();
}
pub fn run() -> ! {
    #[cfg(feature = "native-ui")]
    super::native_ui::constructors();
    unsafe {
        extern "C" {
            fn bm_micropython_main();
        }
        bm_micropython_main();
    }
    super::reset()
}
#[cfg(feature = "runtime-board")]
#[path = "runtime_board.rs"]
pub(crate) mod board;
#[cfg(feature = "runtime-board")]
pub use board::{camera_completed, camera_seed, camera_target, camera_validated, QUIET};

#[no_mangle]
extern "C" fn bm_console_status(field: u32) -> u32 {
    unsafe {
        match field {
            0 => cfg!(feature = "usb-only") as u32,
            1 => core::ptr::read_volatile(0xff538008 as *const u32) & 0xff00,
            2 => core::ptr::read_volatile(0xff530008 as *const u32) & 0x0c00,
            3 => core::ptr::read_volatile(0xff4c0004 as *const u32) & 15,
            4 => (core::ptr::read_volatile(0xff1f1104 as *const u32) >> 27) & 1,
            #[cfg(feature = "usb-console")]
            5 => super::usb::is_ready() as u32,
            _ => 0,
        }
    }
}

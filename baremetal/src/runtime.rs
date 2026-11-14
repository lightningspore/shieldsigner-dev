// SPDX-License-Identifier: MIT
use core::sync::atomic::{AtomicUsize, Ordering};
const CAPACITY: usize = 4096;
static HEAD: AtomicUsize = AtomicUsize::new(0);
static TAIL: AtomicUsize = AtomicUsize::new(0);
static mut RX: [u8; CAPACITY] = [0; CAPACITY];
pub fn receive(byte: u8) {
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
    super::put(core::slice::from_raw_parts(data, len));
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
    while super::cpu::counter() - start < (us as u64) * 24 {}
}
#[no_mangle]
extern "C" fn bm_runtime_fault() -> ! {
    super::put(b"@@FAIL interpreter-fault\r\n");
    super::reset()
}
pub fn run() -> ! {
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
mod board;
#[cfg(feature = "runtime-board")]
pub use board::{camera_completed, camera_seed, camera_target, camera_validated, QUIET};

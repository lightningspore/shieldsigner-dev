// SPDX-License-Identifier: MIT
//! Reclaiming DDR allocator for calibrated sessions and the interpreter bridge.
//! IRQ handlers remain allocation-free; never acquire this lock from an IRQ.
use buddy_system_allocator::LockedHeap;
use core::alloc::{GlobalAlloc, Layout};
pub const HEAP_START: usize = 0x00400000;
pub const HEAP_END: usize = 0x01000000;
pub const CAMERA_START: usize = 0x03000000;
pub const CAMERA_END: usize = 0x04000000;
#[global_allocator]
static HEAP: LockedHeap<25> = LockedHeap::empty();
pub unsafe fn init() {
    HEAP.lock().init(HEAP_START, HEAP_END - HEAP_START);
}
pub fn used() -> usize {
    HEAP.lock().stats_alloc_user()
}
pub fn check() -> bool {
    let baseline = used();
    for _ in 0..64 {
        let mut blocks = [core::ptr::null_mut(); 32];
        for i in 0..32 {
            let size = 17 + i * 197;
            let align = if i % 3 == 0 { 4096 } else { 64 };
            let layout = Layout::from_size_align(size, align).unwrap();
            let p = unsafe { HEAP.alloc(layout) };
            if p.is_null() || p as usize % align != 0 {
                return false;
            }
            unsafe {
                p.write_volatile(i as u8);
                p.add(size - 1).write_volatile(!(i as u8));
            }
            blocks[i] = p;
        }
        // Free interleaved blocks to exercise fragmentation and merging.
        for parity in 0..2 {
            for i in (parity..32).step_by(2) {
                let size = 17 + i * 197;
                let align = if i % 3 == 0 { 4096 } else { 64 };
                let p = blocks[i];
                unsafe {
                    if p.read_volatile() != i as u8 || p.add(size - 1).read_volatile() != !(i as u8)
                    {
                        return false;
                    }
                    HEAP.dealloc(p, Layout::from_size_align(size, align).unwrap());
                }
            }
        }
        if used() != baseline {
            return false;
        }
    }
    unsafe {
        let large = Layout::from_size_align(8 * 1024 * 1024, 4096).unwrap();
        let p = HEAP.alloc(large);
        if p.is_null() {
            return false;
        }
        HEAP.dealloc(p, large);
        if !HEAP
            .alloc(Layout::from_size_align(HEAP_END - HEAP_START + 1, 1).unwrap())
            .is_null()
        {
            return false;
        }
    }
    used() == baseline && HEAP_END < CAMERA_START && CAMERA_END == 0x04000000
}

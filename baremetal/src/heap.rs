// SPDX-License-Identifier: MIT
//! Monotonic DDR heap for early bring-up; deallocation is intentionally unsupported.
use core::alloc::{GlobalAlloc, Layout};
use core::ptr::null_mut;
use core::sync::atomic::{AtomicUsize, Ordering};

pub const HEAP_START: usize = 0x00400000;
pub const HEAP_END: usize = 0x00800000;
// Provisional 16 MB camera region, to be sized and mapped for DMA in Phase 7.
pub const CAMERA_START: usize = 0x03000000;
pub const CAMERA_END: usize = 0x04000000;

pub struct BumpHeap {
    next: AtomicUsize,
}
impl BumpHeap {
    pub const fn new() -> Self {
        Self {
            next: AtomicUsize::new(HEAP_START),
        }
    }
}
unsafe impl GlobalAlloc for BumpHeap {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let mut old = self.next.load(Ordering::Relaxed);
        loop {
            let Some(aligned) = old
                .checked_add(layout.align() - 1)
                .map(|n| n & !(layout.align() - 1))
            else {
                return null_mut();
            };
            let Some(end) = aligned.checked_add(layout.size()) else {
                return null_mut();
            };
            if end > HEAP_END {
                return null_mut();
            }
            match self
                .next
                .compare_exchange_weak(old, end, Ordering::SeqCst, Ordering::Relaxed)
            {
                Ok(_) => return aligned as *mut u8,
                Err(current) => old = current,
            }
        }
    }
    unsafe fn dealloc(&self, _: *mut u8, _: Layout) {}
}

#[global_allocator]
static HEAP: BumpHeap = BumpHeap::new();

#[cfg(feature = "isp-3a-test")]
pub fn used() -> usize {
    HEAP.next.load(Ordering::Relaxed) - HEAP_START
}

pub fn check() -> bool {
    // Run only after ACTLR.SMP and cache/MMU setup; ARM atomics require normal cacheable memory.
    let a = Layout::from_size_align(4096, 64).unwrap();
    let b = Layout::from_size_align(8192, 4096).unwrap();
    unsafe {
        let first = HEAP.alloc(a);
        let second = HEAP.alloc(b);
        if first.is_null()
            || second.is_null()
            || first as usize % 64 != 0
            || second as usize % 4096 != 0
            || (second as usize) < first as usize + 4096
        {
            return false;
        }
        for i in 0..4096 {
            first.add(i).write_volatile((i as u8) ^ 0xa5);
        }
        for i in 0..8192 {
            second.add(i).write_volatile((i as u8) ^ 0x5a);
        }
        for i in 0..4096 {
            if first.add(i).read_volatile() != (i as u8) ^ 0xa5 {
                return false;
            }
        }
        for i in 0..8192 {
            if second.add(i).read_volatile() != (i as u8) ^ 0x5a {
                return false;
            }
        }
        let oversized = Layout::from_size_align(HEAP_END - HEAP_START + 1, 1).unwrap();
        HEAP.alloc(oversized).is_null() && HEAP_END <= CAMERA_START && CAMERA_END == 0x04000000
    }
}

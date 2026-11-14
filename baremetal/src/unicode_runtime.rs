// SPDX-License-Identifier: MIT
//! Unicode15.0 normalization, matching REF CPython3.12's Unicode database.
use unicode_normalization::UnicodeNormalization;
const _: () = assert!(
    unicode_normalization::UNICODE_VERSION.0 == 15
        && unicode_normalization::UNICODE_VERSION.1 == 0
        && unicode_normalization::UNICODE_VERSION.2 == 0
);
const MAX_OUTPUT: usize = 1024 * 1024;
unsafe fn consume(iter: impl Iterator<Item = char>, out: *mut u8, capacity: usize) -> i32 {
    let mut len = 0;
    let mut chars = 0;
    for c in iter {
        if chars % 256 == 0 {
            crate::usb::poll();
            if crate::runtime::interrupt_pending() {
                crate::runtime::take_interrupt();
                return -2;
            }
        }
        chars += 1;
        let mut bytes = [0; 4];
        let bytes = c.encode_utf8(&mut bytes).as_bytes();
        if len + bytes.len() > MAX_OUTPUT {
            return -1;
        }
        if !out.is_null() {
            if len + bytes.len() > capacity {
                return -1;
            }
            core::ptr::copy_nonoverlapping(bytes.as_ptr(), out.add(len), bytes.len());
        }
        len += bytes.len();
    }
    len as i32
}
#[no_mangle]
pub unsafe extern "C" fn bm_unicode_normalize(
    mode: u32,
    data: *const u8,
    len: usize,
    out: *mut u8,
    capacity: usize,
) -> i32 {
    if len > 65536 {
        return -1;
    }
    let input = if len == 0 {
        ""
    } else {
        match core::str::from_utf8(core::slice::from_raw_parts(data, len)) {
            Ok(s) => s,
            Err(_) => return -1,
        }
    };
    match mode {
        0 => consume(input.nfc(), out, capacity),
        1 => consume(input.nfd(), out, capacity),
        2 => consume(input.nfkc(), out, capacity),
        3 => consume(input.nfkd(), out, capacity),
        _ => -1,
    }
}

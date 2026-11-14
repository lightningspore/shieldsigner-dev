// SPDX-License-Identifier: MIT
//! Flat, allocation-free hash contexts in MicroPython-owned aligned storage.
use shieldsigner_hash_core::{Engine, Error};
const BYTES: usize = 512;
// MicroPython may expose a null pointer for a valid empty mutable buffer.
unsafe fn bytes<'a>(data: *const u8, len: usize) -> &'a [u8] {
    if len == 0 {
        &[]
    } else {
        core::slice::from_raw_parts(data, len)
    }
}
const _: () = assert!(core::mem::size_of::<Engine>() <= BYTES);
const _: () = assert!(core::mem::align_of::<Engine>() <= 16);
const _: () = assert!(!core::mem::needs_drop::<Engine>());
#[no_mangle]
pub extern "C" fn bm_hash_size(id: u32) -> i32 {
    match id {
        0 => 28,
        1 => 32,
        2 => 48,
        3 => 64,
        4 | 5 => 20,
        _ => -1,
    }
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_init(state: *mut u8, id: u32) -> i32 {
    if state as usize % core::mem::align_of::<Engine>() != 0 {
        return -1;
    }
    match Engine::new(id) {
        Ok(value) => {
            state.cast::<Engine>().write(value);
            0
        }
        Err(_) => -1,
    }
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_update(state: *mut u8, data: *const u8, len: usize) {
    (&mut *state.cast::<Engine>()).update(bytes(data, len));
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_digest(state: *const u8, out: *mut u8) -> i32 {
    (&*state.cast::<Engine>())
        .digest(core::slice::from_raw_parts_mut(out, 64))
        .map_or(-1, |n| n as i32)
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_copy(out: *mut u8, state: *const u8) {
    out.cast::<Engine>()
        .write((&*state.cast::<Engine>()).clone());
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_clear(state: *mut u8) {
    shieldsigner_hash_core::wipe(core::slice::from_raw_parts_mut(state, BYTES));
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_hmac(
    id: u32,
    key: *const u8,
    key_len: usize,
    data: *const u8,
    len: usize,
    out: *mut u8,
) -> i32 {
    shieldsigner_hash_core::hmac(
        id,
        bytes(key, key_len),
        bytes(data, len),
        core::slice::from_raw_parts_mut(out, 64),
    )
    .map_or(-1, |n| n as i32)
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_pbkdf2(
    id: u32,
    password: *const u8,
    plen: usize,
    salt: *const u8,
    slen: usize,
    rounds: u32,
    out: *mut u8,
    len: usize,
) -> i32 {
    let result = shieldsigner_hash_core::pbkdf2(
        id,
        bytes(password, plen),
        bytes(salt, slen),
        rounds,
        core::slice::from_raw_parts_mut(out, len),
        || {
            crate::usb::poll();
            !crate::runtime::interrupt_pending()
        },
    );
    match result {
        Ok(()) => 0,
        Err(Error::Cancelled) => {
            crate::runtime::take_interrupt();
            -2
        }
        Err(_) => -1,
    }
}
#[no_mangle]
pub unsafe extern "C" fn bm_hash_compare(
    a: *const u8,
    alen: usize,
    b: *const u8,
    blen: usize,
) -> i32 {
    shieldsigner_hash_core::compare(bytes(a, alen), bytes(b, blen)) as i32
}

// SPDX-License-Identifier: MIT
//! Native screen runtime; headless DUT0 never drives LCD or button pins.
use core::{ptr,sync::atomic::{AtomicBool,Ordering}};
const SHADOW:usize=0x02000000;
pub const FRAME_BYTES:usize=240*240*2;
static CONSTRUCTED:AtomicBool=AtomicBool::new(false);
static READY:AtomicBool=AtomicBool::new(false);
extern "C" {fn bm_nativeui_init()->i32;}
pub fn constructors(){
    if CONSTRUCTED.swap(true,Ordering::AcqRel){return;}
    unsafe {
        extern "C" {static __init_array_start:usize;static __init_array_end:usize;}
        let mut next=ptr::addr_of!(__init_array_start);
        let end=ptr::addr_of!(__init_array_end);
        while next<end {
            let address=next.read();
            let call:unsafe extern "C" fn()=core::mem::transmute(address);call();next=next.add(1);
        }
    }
}
#[no_mangle]
extern "C" fn bm_ui_init()->i32 {
    if READY.load(Ordering::Acquire){return 0;}
    if !unsafe{super::c_alloc::check()}{return -1;}
    #[cfg(feature="bench-ui")]
    if super::display::init(false).is_err(){return -1;}
    unsafe {ptr::write_bytes(SHADOW as *mut u8,0,FRAME_BYTES);}
    let result=unsafe{bm_nativeui_init()};if result==0{READY.store(true,Ordering::Release);}result
}
#[no_mangle]
unsafe extern "C" fn bm_ui_flush(x:u32,y:u32,w:u32,h:u32,data:*const u8,length:usize)->i32 {
    if data.is_null()||w==0||h==0||x>=240||y>=240||w>240||h>240||x+w>240||y+h>240||length!=(w*h*2)as usize{return -1;}
    for row in 0..h as usize {
        ptr::copy_nonoverlapping(data.add(row*w as usize*2),(SHADOW as *mut u8).add(((y as usize+row)*240+x as usize)*2),w as usize*2);
    }
    #[cfg(feature="bench-ui")]
    if super::display::blit(x as u16,y as u16,w as u16,h as u16,core::slice::from_raw_parts(data,length)).is_err(){return -1;}
    super::usb::poll();0
}
#[no_mangle]
extern "C" fn bm_ui_heap_used()->u32{super::heap::used()as u32}
#[no_mangle]
extern "C" fn bm_ui_fatal()->!{super::put(b"@@FAIL native-ui-fatal\r\n");super::reset()}

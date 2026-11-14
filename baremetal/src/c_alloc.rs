// SPDX-License-Identifier: MIT
//! Foreground-only C/newlib allocation from the existing reclaiming Rust heap.
extern crate alloc;
use alloc::alloc::{alloc,dealloc};
use core::{alloc::Layout,ptr};
#[repr(C)]
struct Header {base:*mut u8,total:usize,length:usize,_reserved:usize}
unsafe fn allocate(length:usize,alignment:usize)->*mut u8 {
    if !alignment.is_power_of_two(){return ptr::null_mut();}
    let alignment=alignment.max(16);
    let Some(total)=length.max(1).checked_add(alignment).and_then(|v|v.checked_add(core::mem::size_of::<Header>())) else{return ptr::null_mut()};
    let Ok(layout)=Layout::from_size_align(total,16) else{return ptr::null_mut()};
    let base=alloc(layout);if base.is_null(){return base;}
    let address=(base as usize+core::mem::size_of::<Header>()+alignment-1)&!(alignment-1);
    let result=address as *mut u8;
    result.cast::<Header>().sub(1).write(Header{base,total,length,_reserved:0});result
}
#[no_mangle]
pub unsafe extern "C" fn malloc(length:usize)->*mut u8 {allocate(length,16)}
#[no_mangle]
pub unsafe extern "C" fn free(value:*mut u8){
    if value.is_null(){return;}
    let header=value.cast::<Header>().sub(1).read();
    dealloc(header.base,Layout::from_size_align_unchecked(header.total,16));
}
#[no_mangle]
pub unsafe extern "C" fn calloc(count:usize,length:usize)->*mut u8 {
    let Some(size)=count.checked_mul(length) else{return ptr::null_mut()};
    let value=malloc(size);if !value.is_null(){ptr::write_bytes(value,0,size);}value
}
#[no_mangle]
pub unsafe extern "C" fn realloc(value:*mut u8,length:usize)->*mut u8 {
    if value.is_null(){return malloc(length);}
    if length==0 {free(value);return ptr::null_mut();}
    let next=malloc(length);if next.is_null(){return next;}
    let old=&*value.cast::<Header>().sub(1);
    ptr::copy_nonoverlapping(value,next,old.length.min(length));free(value);next
}
#[no_mangle]
pub unsafe extern "C" fn memalign(alignment:usize,length:usize)->*mut u8 {allocate(length,alignment)}
#[no_mangle]
pub unsafe extern "C" fn aligned_alloc(alignment:usize,length:usize)->*mut u8 {
    if alignment==0||length%alignment!=0 {return ptr::null_mut();}allocate(length,alignment)
}
#[no_mangle]
pub unsafe extern "C" fn _malloc_r(_: *mut u8,n:usize)->*mut u8 {malloc(n)}
#[no_mangle]
pub unsafe extern "C" fn _free_r(_: *mut u8,p:*mut u8){free(p)}
#[no_mangle]
pub unsafe extern "C" fn _calloc_r(_: *mut u8,n:usize,s:usize)->*mut u8 {calloc(n,s)}
#[no_mangle]
pub unsafe extern "C" fn _realloc_r(_: *mut u8,p:*mut u8,n:usize)->*mut u8 {realloc(p,n)}
pub unsafe fn check()->bool {
    let baseline=crate::heap::used();
    for alignment in [16,64,4096] {
        let p=memalign(alignment,197);if p.is_null()||p as usize%alignment!=0 {return false;}
        ptr::write_bytes(p,0xa5,197);
        let q=realloc(p,400);if q.is_null(){free(p);return false;}
        let intact=core::slice::from_raw_parts(q,197).iter().all(|b|*b==0xa5);free(q);if !intact{return false;}
    }
    let p=calloc(7,13);if p.is_null(){return false;}
    let zero=core::slice::from_raw_parts(p,91).iter().all(|b|*b==0);free(p);
    zero&&calloc(usize::MAX,2).is_null()&&malloc(16*1024*1024).is_null()&&crate::heap::used()==baseline
}

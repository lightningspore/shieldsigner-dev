// SPDX-License-Identifier: MIT
//! Warm-reset evidence in noncacheable DDR, outside USB's16KiB DMA area.
//! No allocation, formatting, device I/O or Python/C++ exception on this path.
use core::{arch::asm,ptr::{read_volatile,write_volatile},sync::atomic::{AtomicBool,AtomicU32,Ordering}};
use super::reset_format::{self,WORDS,MAGIC,VERSION};
const ADDRESS:usize=0x03c10000; //60MiB+64KiB; reserve64bytes, camera/USB do not touch it.
static MARKED:AtomicBool=AtomicBool::new(false);
static MARKER:AtomicU32=AtomicU32::new(0);
pub fn mark(reason:u32,registers:[u32;7]) {
    if MARKED.compare_exchange(false,true,Ordering::AcqRel,Ordering::Acquire).is_err(){return;}
    let time=super::cpu::counter();
    let mut words=[0;WORDS];words[1]=VERSION;words[2]=reason;words[3]=MARKER.load(Ordering::Relaxed);
    words[4..11].copy_from_slice(&registers);words[11]=time as u32;words[12]=(time>>32)as u32;
    words[13]=reset_format::checksum(&words);words[14]=!MAGIC;
    unsafe {
        let destination=ADDRESS as *mut u32;
        write_volatile(destination,0);
        for (i,value) in words.iter().enumerate().skip(1){write_volatile(destination.add(i),*value);}
        asm!("dsb sy",options(nostack));write_volatile(destination,MAGIC);asm!("dsb sy",options(nostack));
    }
}
pub fn simple(reason:u32){mark(reason,[0;7]);}
#[no_mangle]
pub unsafe extern "C" fn bm_reset_info(destination:*mut u32,count:u32)->i32 {
    if destination.is_null()||count!=WORDS as u32{return -1;}
    let mut words=[0;WORDS];
    for (i,value) in words.iter_mut().enumerate(){*value=read_volatile((ADDRESS as *const u32).add(i));}
    if !reset_format::valid(&words){return 0;}
    core::ptr::copy_nonoverlapping(words.as_ptr(),destination,WORDS);WORDS as i32
}
#[no_mangle]
pub extern "C" fn bm_reset_clear(){unsafe{write_volatile(ADDRESS as *mut u32,0);asm!("dsb sy",options(nostack));}MARKED.store(false,Ordering::Release);}
#[no_mangle]
pub extern "C" fn bm_reset_marker(value:u32){MARKER.store(value,Ordering::Relaxed);}
#[no_mangle]
pub extern "C" fn bm_reset_probe_enabled()->u32{cfg!(feature="fault-probe")as u32}
#[no_mangle]
pub unsafe extern "C" fn bm_reset_probe(kind:u32)->i32 {
    #[cfg(not(feature="fault-probe"))]{let _=kind;-1}
    #[cfg(feature="fault-probe")]{
        match kind {
            1=>{let address=if cfg!(feature="native-ui"){0x01a00000u32}else{0x00200000u32};asm!("ldr {value}, [{address}]",address=in(reg)address,value=out(reg)_,options(nostack));-2},
            2=>{
                #[cfg(feature="native-ui")]{extern "C"{fn bm_nativeui_abort_probe()->!;}bm_nativeui_abort_probe()}
                #[cfg(not(feature="native-ui"))]{-1}
            },
            3=>{extern "C"{fn bm_runtime_fault()->!;}bm_runtime_fault()},
            4=>{bm_reset_clear();simple(1);let p=(ADDRESS as *mut u32).add(13);write_volatile(p,read_volatile(p)^1);asm!("dsb sy",options(nostack));0},
            _=>-1,
        }
    }
}

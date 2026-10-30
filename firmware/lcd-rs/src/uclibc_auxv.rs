//! Rust 1.82's Linux thread/alternate-stack implementation queries
//! AT_MINSIGSTKSZ through getauxval, absent in the pinned image's uClibc.
//! Link-time wrapping supplies that operation locally, without interposing
//! a getauxval symbol on Python or other shared libraries.
#[no_mangle]
pub unsafe extern "C" fn __wrap_getauxval(kind: libc::c_ulong) -> libc::c_ulong {
    let saved_errno = *libc::__errno_location();
    let fd = libc::open(
        b"/proc/self/auxv\0".as_ptr().cast(),
        libc::O_RDONLY | libc::O_CLOEXEC,
    );
    if fd < 0 {
        return 0;
    }
    let mut result = None;
    for _ in 0..1024 {
        let mut pair = [0usize; 2];
        let size = std::mem::size_of_val(&pair);
        let mut offset = 0;
        while offset < size {
            let n = libc::read(
                fd,
                pair.as_mut_ptr().cast::<u8>().add(offset).cast(),
                size - offset,
            );
            if n < 0 && *libc::__errno_location() == libc::EINTR {
                continue;
            }
            if n <= 0 {
                break;
            }
            offset += n as usize;
        }
        if offset != size || pair[0] == 0 {
            break;
        }
        if pair[0] == kind as usize {
            result = Some(pair[1] as libc::c_ulong);
            break;
        }
    }
    libc::close(fd);
    *libc::__errno_location() = if result.is_some() {
        saved_errno
    } else {
        libc::ENOENT
    };
    result.unwrap_or(0)
}

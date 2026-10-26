//! Experimental standalone V4L2 diagnostic. No RKAIQ symbols or vendor library.
//! This does not yet configure the full media graph or replace the ISP engine.
use std::env;
const HELP:&str=concat!("camera-probe ", env!("CARGO_PKG_VERSION"), " — experimental Rust camera diagnostic\n\nCommands:\n  camera-probe list\n  camera-probe self-test\n  camera-probe events /dev/videoN [--timeout-ms 10000] [--count 8]\n  camera-probe capture /dev/videoN /tmp/frame.raw [options]\n\nOptions:\n  --width N --height N --fourcc NV12   Explicitly request a format (otherwise retain current)\n  --buffers N                         MMAP buffer request, 1–4 (default 1)\n  --timeout-ms N                      Per-frame deadline (default 3000)\n  --warmup N                          Frames to discard before saving (default 2)\n  --require-no-rkaiq                  Refuse capture if rkaiq_3A_server/rkipc is running\n\nWrites the last frame plus OUT.json metadata. Single-plane and multi-plane MMAP.\nThe existing kernel media graph, sensor driver, sensor settings and CMA memory\nmust already support capture. Does not start vendor software or modify boot.\n");
fn self_test() -> Result<(), String> {
    use shieldsigner_rkaiq::*;
    if interpolate(&[0., 1.], &[2., 4.], 0.5) != Ok(3.) {
        return Err("interpolation self-test failed".into());
    }
    let x = [0; LUT_VALUES];
    let y = [129; LUT_VALUES];
    let mut out = [0; LUT_VALUES];
    blend_lut(0.5, &x, &y, &mut out).map_err(|e| format!("{e:?}"))?;
    if out.iter().any(|&v| v != 64) {
        return Err("LUT self-test failed".into());
    }
    {
        use shieldsigner_rkaiq::media::*;
        let entities = [
            Entity {
                id: 1,
                kind: CAMERA_SENSOR,
            },
            Entity { id: 2, kind: 0 },
        ];
        let link = Link {
            source: Pad {
                entity: 1,
                ..Pad::default()
            },
            sink: Pad {
                entity: 2,
                ..Pad::default()
            },
            flags: 3,
            ..Link::default()
        };
        if upstream_sensor(&entities, &[link], 2, &mut [0; 2]) != Ok(Binding::Unique(1)) {
            return Err("Media topology self-test failed".into());
        }
    }
    println!("PASS: reconstructed interpolation, complete 2187-value LUT and media topology traversal. Full ARM-original differential test is separate.");
    Ok(())
}
fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let result = match args.first().map(String::as_str) {
        None | Some("--help") | Some("-h") => {
            print!("{HELP}");
            Ok(())
        }
        Some("--version") => {
            println!(
                "camera-probe {} (partial RKAIQ reconstruction; standalone V4L2 diagnostic)",
                env!("CARGO_PKG_VERSION")
            );
            Ok(())
        }
        Some("self-test") => self_test(),
        _ => platform(&args),
    };
    if let Err(error) = result {
        eprintln!("camera-probe: {error}");
        std::process::exit(1);
    }
}
#[cfg(not(target_os = "linux"))]
fn platform(_: &[String]) -> Result<(), String> {
    Err("camera access requires Linux; --help and self-test work on this host".into())
}
#[cfg(target_os = "linux")]
fn platform(args: &[String]) -> Result<(), String> {
    linux::run(args).map_err(|e| e.to_string())
}

#[cfg(target_os = "linux")]
mod linux {
    use serde_json::{json, Value};
    use std::os::raw::c_long;
    use std::{
        fs::{self, File, OpenOptions},
        io::{self, Write},
        os::fd::{AsRawFd, RawFd},
        os::unix::fs::OpenOptionsExt,
        ptr,
        time::{Duration, Instant},
    };
    const CAPTURE: u32 = 1;
    const MPLANE: u32 = 9;
    const MMAP: u32 = 1;
    const PLANES: usize = 8;
    #[repr(C)]
    #[derive(Clone, Copy)]
    union FormatData {
        raw: [u8; 200],
        align: usize,
    }
    #[repr(C)]
    struct Format {
        kind: u32,
        data: FormatData,
    }
    #[repr(C)]
    #[derive(Clone, Copy)]
    union PlaneMemory {
        offset: u32,
        user: usize,
        fd: i32,
    }
    #[repr(C)]
    #[derive(Clone, Copy)]
    struct Plane {
        used: u32,
        length: u32,
        memory: PlaneMemory,
        offset: u32,
        reserved: [u32; 11],
    }
    // Deliberately use kernel long-sized time fields. ARM32's native 5.10 ioctl
    // uses the old 32-bit timeval layout, irrespective of musl time_t being 64-bit.
    #[repr(C)]
    struct KernelTimeval {
        seconds: c_long,
        microseconds: c_long,
    }
    #[repr(C)]
    struct Timecode {
        kind: u32,
        flags: u32,
        frames: u8,
        seconds: u8,
        minutes: u8,
        hours: u8,
        userbits: [u8; 4],
    }
    #[repr(C)]
    union BufferMemory {
        offset: u32,
        user: usize,
        planes: *mut Plane,
        fd: i32,
    }
    #[repr(C)]
    struct Buffer {
        index: u32,
        kind: u32,
        used: u32,
        flags: u32,
        field: u32,
        time: KernelTimeval,
        timecode: Timecode,
        sequence: u32,
        memory: u32,
        data: BufferMemory,
        length: u32,
        reserved: u32,
        request: i32,
    }
    #[repr(C)]
    struct RequestBuffers {
        count: u32,
        kind: u32,
        memory: u32,
        capabilities: u32,
        reserved: u32,
    }
    const fn ioc<T>(direction: u32, nr: u32) -> u32 {
        (direction << 30) | ((std::mem::size_of::<T>() as u32) << 16) | (b'V' as u32) << 8 | nr
    }
    const QUERYCAP: u32 = ioc::<[u8; 104]>(2, 0);
    const ENUMFMT: u32 = ioc::<[u8; 64]>(3, 2);
    const GETFMT: u32 = ioc::<Format>(3, 4);
    const SETFMT: u32 = ioc::<Format>(3, 5);
    const REQBUFS: u32 = ioc::<RequestBuffers>(3, 8);
    const QUERYBUF: u32 = ioc::<Buffer>(3, 9);
    const QUEUE: u32 = ioc::<Buffer>(3, 15);
    const DEQUEUE: u32 = ioc::<Buffer>(3, 17);
    const STREAMON: u32 = ioc::<u32>(1, 18);
    const STREAMOFF: u32 = ioc::<u32>(1, 19);
    #[cfg(target_pointer_width = "32")]
    const _: () = {
        assert!(std::mem::size_of::<Format>() == 204);
        assert!(std::mem::size_of::<Buffer>() == 68);
        assert!(std::mem::size_of::<Plane>() == 60);
        assert!(GETFMT == 0xc0cc5604);
        assert!(QUERYBUF == 0xc0445609);
    };
    #[cfg(target_pointer_width = "64")]
    const _: () = {
        assert!(std::mem::size_of::<Format>() == 208);
        assert!(std::mem::size_of::<Buffer>() == 88);
        assert!(std::mem::size_of::<Plane>() == 64);
    };
    fn error(message: impl Into<String>) -> io::Error {
        io::Error::other(message.into())
    }
    fn zero<T>() -> T {
        unsafe { std::mem::zeroed() }
    }
    fn ioctl<T>(fd: RawFd, request: u32, value: &mut T) -> io::Result<()> {
        loop {
            let result = unsafe { libc::ioctl(fd, request as _, value as *mut T) };
            if result >= 0 {
                return Ok(());
            }
            let e = io::Error::last_os_error();
            if e.kind() != io::ErrorKind::Interrupted {
                return Err(e);
            }
        }
    }
    fn get32(bytes: &[u8], at: usize) -> u32 {
        u32::from_ne_bytes(bytes[at..at + 4].try_into().unwrap())
    }
    fn put32(bytes: &mut [u8], at: usize, value: u32) {
        bytes[at..at + 4].copy_from_slice(&value.to_ne_bytes());
    }
    fn cstr(bytes: &[u8]) -> String {
        String::from_utf8_lossy(bytes.split(|&x| x == 0).next().unwrap_or_default()).into_owned()
    }
    fn fourcc(value: u32) -> String {
        value
            .to_le_bytes()
            .iter()
            .map(|&b| if b.is_ascii_graphic() { b as char } else { '?' })
            .collect()
    }
    fn open(path: &str, write: bool) -> io::Result<File> {
        OpenOptions::new()
            .read(true)
            .write(write)
            .custom_flags(libc::O_NONBLOCK | libc::O_CLOEXEC)
            .open(path)
    }
    fn capability(file: &File) -> io::Result<([u8; 104], u32)> {
        let mut cap = [0; 104];
        ioctl(file.as_raw_fd(), QUERYCAP, &mut cap)?;
        let flags = get32(&cap, 84);
        Ok((
            cap,
            if flags & 0x80000000 != 0 {
                get32(&cap, 88)
            } else {
                flags
            },
        ))
    }
    fn format(file: &File, kind: u32) -> io::Result<Format> {
        let mut value: Format = zero();
        value.kind = kind;
        ioctl(file.as_raw_fd(), GETFMT, &mut value)?;
        Ok(value)
    }
    fn format_json(value: &Format) -> Value {
        let raw = unsafe { &value.data.raw };
        let multi = value.kind == MPLANE;
        let count = if multi { raw[180] as usize } else { 1 };
        let mut planes = Vec::new();
        for n in 0..count.min(PLANES) {
            planes.push(if multi {
                json!({"sizeImage":get32(raw,20+n*20),"bytesPerLine":get32(raw,24+n*20)})
            } else {
                json!({"sizeImage":get32(raw,20),"bytesPerLine":get32(raw,16)})
            });
        }
        json!({"bufferType":value.kind,"width":get32(raw,0),"height":get32(raw,4),"fourcc":fourcc(get32(raw,8)),"fourccValue":get32(raw,8),"planeCount":count,"planes":planes})
    }
    fn vendor_processes() -> Vec<String> {
        let mut found = Vec::new();
        if let Ok(entries) = fs::read_dir("/proc") {
            for entry in entries.flatten() {
                if entry.file_name().to_string_lossy().parse::<u32>().is_err() {
                    continue;
                }
                if let Ok(name) = fs::read_to_string(entry.path().join("comm")) {
                    let name = name.trim();
                    if ["rkipc", "rkaiq_3A_server"].contains(&name) {
                        found.push(format!("{}:{name}", entry.file_name().to_string_lossy()));
                    }
                }
            }
        }
        found
    }
    fn device_node(major: u32, minor: u32) -> Option<String> {
        use std::os::unix::fs::{FileTypeExt, MetadataExt};
        let valid = |path: &std::path::Path| {
            fs::metadata(path).ok().is_some_and(|m| {
                m.file_type().is_char_device()
                    && libc::major(m.rdev()) == major
                    && libc::minor(m.rdev()) == minor
            })
        };
        if let Ok(path) = fs::canonicalize(format!("/dev/char/{major}:{minor}")) {
            if valid(&path) {
                return Some(path.to_string_lossy().into_owned());
            }
        }
        // BusyBox/mdev images may not create /dev/char symlinks.
        if let Ok(info) = fs::read_to_string(format!("/sys/dev/char/{major}:{minor}/uevent")) {
            if let Some(name) = info.lines().find_map(|line| line.strip_prefix("DEVNAME=")) {
                let path = std::path::Path::new("/dev").join(name);
                if valid(&path) {
                    return Some(path.to_string_lossy().into_owned());
                }
            }
        }
        if let Ok(entries) = fs::read_dir("/dev") {
            for entry in entries.flatten() {
                let path = entry.path();
                if valid(&path) {
                    return Some(path.to_string_lossy().into_owned());
                }
            }
        }
        None
    }
    fn media_graph() -> Vec<Value> {
        use shieldsigner_rkaiq::media::{self, Binding, Entity, Link, LinksQuery, Pad};
        let mut graph = Vec::new();
        for index in 0..32 {
            let path = format!("/dev/media{index}");
            let file = match open(&path, false) {
                Ok(file) => file,
                Err(e) if e.kind() == io::ErrorKind::NotFound => continue,
                Err(e) => {
                    graph.push(json!({"device":path,"complete":false,"errors":[format!("Open media device: {e}")],"entities":[]}));
                    continue;
                }
            };
            let mut info = [0u8; 256];
            let info_request = (3u32 << 30) | (256u32 << 16) | ((b'|' as u32) << 8);
            if let Err(e) = ioctl(file.as_raw_fd(), info_request, &mut info) {
                graph.push(json!({"device":path,"complete":false,"errors":[format!("DEVICE_INFO: {e}")],"entities":[]}));
                continue;
            }
            let mut entities = Vec::new();
            let mut typed_entities = Vec::new();
            let mut typed_links: Vec<Link> = Vec::new();
            let mut links = Vec::new();
            let mut errors = Vec::new();
            let mut last = 0u32;
            let mut enumeration_ended = false;
            for _ in 0..1024 {
                let mut entity = [0u8; 256];
                put32(&mut entity, 0, last | 0x80000000);
                if let Err(e) = ioctl(file.as_raw_fd(), info_request | 1, &mut entity) {
                    if e.raw_os_error() != Some(libc::EINVAL) {
                        errors.push(format!("ENUM_ENTITIES: {e}"));
                    }
                    enumeration_ended = true;
                    break;
                }
                let id = get32(&entity, 0);
                if id <= last || id & 0x80000000 != 0 {
                    errors.push("Non-increasing/invalid entity ID".into());
                    break;
                }
                last = id;
                let major = get32(&entity, 72);
                let minor = get32(&entity, 76);
                let kind = get32(&entity, 36);
                let pad_count = u16::from_ne_bytes(entity[52..54].try_into().unwrap()) as usize;
                let link_count = u16::from_ne_bytes(entity[54..56].try_into().unwrap()) as usize;
                let mut pads = Vec::new();
                if pad_count > 4096 || link_count > 4096 {
                    errors.push(format!("Entity {id}: unreasonable pad/link count"));
                } else {
                    let mut raw_pads = vec![Pad::default(); pad_count];
                    let mut raw_links = vec![Link::default(); link_count];
                    let mut query = LinksQuery {
                        entity: id,
                        pads: if pad_count == 0 {
                            ptr::null_mut()
                        } else {
                            raw_pads.as_mut_ptr()
                        },
                        links: if link_count == 0 {
                            ptr::null_mut()
                        } else {
                            raw_links.as_mut_ptr()
                        },
                        reserved: [0; 4],
                    };
                    let request = (3u32 << 30)
                        | ((std::mem::size_of::<LinksQuery>() as u32) << 16)
                        | ((b'|' as u32) << 8)
                        | 2;
                    match ioctl(file.as_raw_fd(), request, &mut query) {
                        Err(e) => errors.push(format!("Entity {id} ENUM_LINKS: {e}")),
                        Ok(()) => {
                            for pad in raw_pads {
                                pads.push(json!({"entity":pad.entity,"index":pad.index,"flags":pad.flags}));
                            }
                            for link in raw_links {
                                if !typed_links.iter().any(|l| {
                                    l.source.entity == link.source.entity
                                        && l.source.index == link.source.index
                                        && l.sink.entity == link.sink.entity
                                        && l.sink.index == link.sink.index
                                        && l.flags == link.flags
                                }) {
                                    links.push(json!({"source":{"entity":link.source.entity,"pad":link.source.index},"sink":{"entity":link.sink.entity,"pad":link.sink.index},"flags":link.flags,"enabled":link.flags&1!=0}));
                                    typed_links.push(link);
                                }
                            }
                        }
                    }
                }
                typed_entities.push(Entity { id, kind });
                entities.push(json!({"id":id,"name":cstr(&entity[4..36]),"type":kind,"major":major,"minor":minor,"device":device_node(major,minor),"padCount":pad_count,"linkCount":link_count,"pads":pads}));
            }
            if !enumeration_ended {
                errors.push("Entity enumeration did not reach its end".into());
            }
            let mut bindings = Vec::new();
            if errors.is_empty() {
                let mut scratch = vec![0; typed_entities.len()];
                for entity in &entities {
                    if entity["device"].is_null() {
                        continue;
                    }
                    let id = entity["id"].as_u64().unwrap() as u32;
                    match media::upstream_sensor(&typed_entities, &typed_links, id, &mut scratch) {
                        Ok(binding) => {
                            let (status, sensor) = match binding {
                                Binding::None => ("none", None),
                                Binding::Ambiguous => ("ambiguous", None),
                                Binding::Unique(sensor) => (
                                    "unique",
                                    entities
                                        .iter()
                                        .find(|e| e["id"].as_u64() == Some(sensor as u64))
                                        .cloned(),
                                ),
                            };
                            bindings.push(json!({"device":entity["device"],"entity":id,"status":status,"sensor":sensor}));
                        }
                        Err(e) => {
                            errors.push(format!("Topology validation: {e:?}"));
                            bindings.clear();
                            break;
                        }
                    }
                }
            }
            graph.push(json!({"device":path,"driver":cstr(&info[..16]),"model":cstr(&info[16..48]),"complete":errors.is_empty(),"errors":errors,"entities":entities,"links":links,"sensorPaths":bindings,"scope":"One media device; enabled directed data links only; no cross-media inference or link changes"}));
        }
        graph
    }
    fn list() -> io::Result<()> {
        let mut devices = Vec::new();
        let mut paths = Vec::new();
        for entry in fs::read_dir("/dev")?.flatten() {
            let name = entry.file_name();
            let name = name.to_string_lossy();
            if name.strip_prefix("video").is_some_and(|suffix| {
                !suffix.is_empty() && suffix.bytes().all(|b| b.is_ascii_digit())
            }) {
                paths.push(entry.path());
            }
        }
        paths.sort();
        for path in paths {
            let name = path.to_string_lossy().to_string();
            let file = match open(&name, false) {
                Ok(f) => f,
                Err(e) => {
                    devices.push(json!({"device":name,"error":e.to_string()}));
                    continue;
                }
            };
            let (cap, flags) = match capability(&file) {
                Ok(c) => c,
                Err(e) => {
                    devices.push(json!({"device":name,"error":e.to_string()}));
                    continue;
                }
            };
            let mut formats = Vec::new();
            for kind in [CAPTURE, MPLANE] {
                for index in 0..128 {
                    let mut desc = [0; 64];
                    put32(&mut desc, 0, index);
                    put32(&mut desc, 4, kind);
                    if ioctl(file.as_raw_fd(), ENUMFMT, &mut desc).is_err() {
                        break;
                    }
                    formats.push(json!({"bufferType":kind,"fourcc":fourcc(get32(&desc,44)),"description":cstr(&desc[12..44])}));
                }
            }
            let kind = if flags & 1 != 0 {
                Some(CAPTURE)
            } else if flags & 0x1000 != 0 {
                Some(MPLANE)
            } else {
                None
            };
            let current = kind
                .and_then(|kind| format(&file, kind).ok())
                .map(|f| format_json(&f));
            devices.push(json!({"device":name,"driver":cstr(&cap[..16]),"card":cstr(&cap[16..48]),"capabilities":format!("0x{flags:08x}"),"currentFormat":current,"formats":formats}));
        }
        println!(
            "{}",
            serde_json::to_string_pretty(
                &json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"linksRkaiq":false,"vendorProcesses":vendor_processes(),"devices":devices,"mediaGraph":media_graph(),"limitations":["This is a Linux node/format inventory, not proof of camera capture or absence of vendor initialization at boot."]})
            )?
        );
        Ok(())
    }
    struct Mapping {
        address: *mut libc::c_void,
        length: usize,
    }
    impl Mapping {
        fn new(fd: RawFd, length: usize, offset: u32) -> io::Result<Self> {
            if length == 0 || length > 128 * 1024 * 1024 {
                return Err(error("Invalid/oversized driver MMAP length"));
            }
            let address = unsafe {
                libc::mmap(
                    ptr::null_mut(),
                    length,
                    libc::PROT_READ | libc::PROT_WRITE,
                    libc::MAP_SHARED,
                    fd,
                    offset as libc::off_t,
                )
            };
            if address == libc::MAP_FAILED {
                return Err(io::Error::last_os_error());
            }
            Ok(Self { address, length })
        }
    }
    impl Drop for Mapping {
        fn drop(&mut self) {
            unsafe {
                libc::munmap(self.address, self.length);
            }
        }
    }
    struct Stream {
        fd: RawFd,
        kind: u32,
    }
    impl Drop for Stream {
        fn drop(&mut self) {
            let _ = ioctl(self.fd, STREAMOFF, &mut self.kind);
        }
    }
    fn buffer(index: u32, kind: u32, planes: &mut [Plane; PLANES]) -> Buffer {
        let mut value: Buffer = zero();
        value.index = index;
        value.kind = kind;
        value.memory = MMAP;
        if kind == MPLANE {
            value.length = PLANES as u32;
            value.data.planes = planes.as_mut_ptr();
        }
        value
    }
    fn wait(fd: RawFd, deadline: Instant) -> io::Result<()> {
        loop {
            let left = deadline.saturating_duration_since(Instant::now());
            if left.is_zero() {
                return Err(error("Capture timeout: no completed frame; check media graph, sensor and memory allocation"));
            }
            let mut poll = libc::pollfd {
                fd,
                events: libc::POLLIN | libc::POLLPRI,
                revents: 0,
            };
            let result = unsafe {
                libc::poll(
                    &mut poll,
                    1,
                    left.as_millis().max(1).min(i32::MAX as u128) as i32,
                )
            };
            if result > 0 {
                if poll.revents & (libc::POLLERR | libc::POLLHUP | libc::POLLNVAL) != 0 {
                    return Err(error(format!(
                        "Video poll error: revents=0x{:x}",
                        poll.revents
                    )));
                }
                return Ok(());
            }
            if result < 0 {
                let e = io::Error::last_os_error();
                if e.kind() != io::ErrorKind::Interrupted {
                    return Err(e);
                }
            }
        }
    }
    fn capture(args: &[String]) -> io::Result<()> {
        if args.len() < 2 {
            return Err(error("capture needs DEVICE and OUT; see --help"));
        }
        let device = &args[0];
        let output = &args[1];
        let (mut width, mut height, mut pixel) = (None, None, None);
        let (mut buffers, mut timeout, mut warmup) = (1u32, 3000u64, 2u32);
        let mut require_no_vendor = false;
        let mut i = 2;
        while i < args.len() {
            let key = args[i].as_str();
            if key == "--require-no-rkaiq" {
                require_no_vendor = true;
                i += 1;
                continue;
            }
            let value = args
                .get(i + 1)
                .ok_or_else(|| error(format!("Missing value for {key}")))?;
            match key {
                "--width" => {
                    width = Some(value.parse::<u32>().map_err(|_| error("Invalid width"))?)
                }
                "--height" => {
                    height = Some(value.parse::<u32>().map_err(|_| error("Invalid height"))?)
                }
                "--fourcc" => {
                    if value.len() != 4 || !value.is_ascii() {
                        return Err(error("FourCC needs four ASCII bytes"));
                    }
                    pixel = Some(u32::from_le_bytes(value.as_bytes().try_into().unwrap()));
                }
                "--buffers" => {
                    buffers = value.parse().map_err(|_| error("Invalid buffer count"))?
                }
                "--timeout-ms" => timeout = value.parse().map_err(|_| error("Invalid timeout"))?,
                "--warmup" => warmup = value.parse().map_err(|_| error("Invalid warmup count"))?,
                _ => return Err(error(format!("Unknown option {key}"))),
            }
            i += 2;
        }
        if !(1..=4).contains(&buffers) || !(1..=60000).contains(&timeout) || warmup > 100 {
            return Err(error(
                "Options exceed bounds: buffers 1–4, timeout 1–60000 ms, warmup 0–100",
            ));
        }
        let active = vendor_processes();
        if require_no_vendor && !active.is_empty() {
            return Err(error(format!(
                "Vendor camera processes still running: {active:?}"
            )));
        }
        let file = open(device, true)?;
        let fd = file.as_raw_fd();
        let (_, flags) = capability(&file)?;
        let kind = if flags & 1 != 0 {
            CAPTURE
        } else if flags & 0x1000 != 0 {
            MPLANE
        } else {
            return Err(error("Node is not a video-capture endpoint"));
        };
        if flags & 0x04000000 == 0 {
            return Err(error("Node does not advertise streaming/MMAP capture"));
        }
        let mut fmt = format(&file, kind)?;
        if width.is_some() || height.is_some() || pixel.is_some() {
            let raw = unsafe { &mut fmt.data.raw };
            if let Some(w) = width {
                if w == 0 {
                    return Err(error("Width must be nonzero"));
                }
                put32(raw, 0, w);
            }
            if let Some(h) = height {
                if h == 0 {
                    return Err(error("Height must be nonzero"));
                }
                put32(raw, 4, h);
            }
            if let Some(p) = pixel {
                put32(raw, 8, p);
            }
            ioctl(fd, SETFMT, &mut fmt)?;
        }
        let mut request = RequestBuffers {
            count: buffers,
            kind,
            memory: MMAP,
            capabilities: 0,
            reserved: 0,
        };
        ioctl(fd, REQBUFS, &mut request).map_err(|e| {
            error(format!(
                "REQBUFS failed ({e}); record current format and CMA/free-memory information"
            ))
        })?;
        if request.count == 0 || request.count > 16 {
            return Err(error("Driver returned invalid buffer count"));
        }
        let mut mapped = Vec::new();
        for index in 0..request.count {
            let mut planes: [Plane; PLANES] = zero();
            let mut b = buffer(index, kind, &mut planes);
            ioctl(fd, QUERYBUF, &mut b)?;
            let count = if kind == MPLANE { b.length as usize } else { 1 };
            if count == 0 || count > PLANES {
                return Err(error("Driver returned invalid plane count"));
            }
            let mut mappings = Vec::new();
            for plane in planes.iter().take(count) {
                let (length, offset) = if kind == MPLANE {
                    (plane.length as usize, unsafe { plane.memory.offset })
                } else {
                    (b.length as usize, unsafe { b.data.offset })
                };
                mappings.push(Mapping::new(fd, length, offset)?);
            }
            mapped.push(mappings);
            ioctl(fd, QUEUE, &mut b)?;
        }
        let mut stream_kind = kind;
        ioctl(fd, STREAMON, &mut stream_kind)?;
        let stream = Stream { fd, kind };
        let mut saved = None;
        for frame in 0..=warmup {
            let deadline = Instant::now() + Duration::from_millis(timeout);
            let mut planes: [Plane; PLANES] = zero();
            let mut b = buffer(0, kind, &mut planes);
            loop {
                wait(fd, deadline)?;
                match ioctl(fd, DEQUEUE, &mut b) {
                    Ok(()) => break,
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => continue,
                    Err(e) => return Err(e),
                }
            }
            if b.flags & 0x40 != 0 {
                return Err(error(format!(
                    "Driver marked frame {} as corrupted (V4L2_BUF_FLAG_ERROR)",
                    b.sequence
                )));
            }
            let mappings = mapped
                .get(b.index as usize)
                .ok_or_else(|| error("Driver returned out-of-range buffer index"))?;
            if kind == MPLANE && b.length as usize != mappings.len() {
                return Err(error("Dequeued plane count changed unexpectedly"));
            }
            if frame == warmup {
                let mut bytes = Vec::new();
                let mut metadata = Vec::new();
                for (n, mapping) in mappings.iter().enumerate() {
                    let (used, offset) = if kind == MPLANE {
                        (planes[n].used as usize, planes[n].offset as usize)
                    } else {
                        (b.used as usize, 0)
                    };
                    if used == 0 || used > mapping.length || offset > used {
                        return Err(error("Driver returned empty or invalid frame payload"));
                    }
                    let data = unsafe {
                        std::slice::from_raw_parts(
                            mapping.address.cast::<u8>().add(offset),
                            used - offset,
                        )
                    };
                    metadata.push(json!({"plane":n,"fileOffset":bytes.len(),"bytes":data.len(),"dataOffset":offset}));
                    bytes.extend_from_slice(data);
                }
                saved = Some((
                    bytes,
                    metadata,
                    b.sequence,
                    b.time.seconds,
                    b.time.microseconds,
                ));
            }
            ioctl(fd, QUEUE, &mut b)?;
        }
        drop(stream);
        drop(mapped);
        request.count = 0;
        ioctl(fd, REQBUFS, &mut request)?;
        let (bytes, planes, sequence, seconds, microseconds) =
            saved.ok_or_else(|| error("No frame saved"))?;
        let mut out = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(output)?;
        out.write_all(&bytes)?;
        let report = json!({"tool":format!("camera-probe {}",env!("CARGO_PKG_VERSION")),"device":device,"linksRkaiq":false,"vendorProcessesBeforeCapture":active,"requireNoRkaiq":require_no_vendor,"format":format_json(&fmt),"bytes":bytes.len(),"planes":planes,"sequence":sequence,"timestamp":{"seconds":seconds,"microseconds":microseconds},"limitations":["Captures from the existing kernel media graph; does not yet recreate ISP calibration, auto-exposure, white balance or graph initialization.","Absent vendor processes do not prove the graph was never initialized by vendor software during boot."]});
        let meta = format!("{output}.json");
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&meta)?;
        file.write_all(serde_json::to_string_pretty(&report)?.as_bytes())?;
        println!("{}", serde_json::to_string_pretty(&report)?);
        Ok(())
    }
    // Raw ARM32 kernel event storage: do not use musl's time64 timespec.
    fn events(args: &[String]) -> io::Result<()> {
        use shieldsigner_rkaiq::engine::{STREAM_START, STREAM_STOP};
        if std::mem::size_of::<usize>() != 4 {
            return Err(error("Stream-event ABI currently targets ARM32 Linux only"));
        }
        if args.is_empty() {
            return Err(error("events requires the rkisp-input-params device path"));
        }
        let (mut timeout, mut count) = (10000u64, 8u32);
        let mut i = 1;
        while i < args.len() {
            let value = args
                .get(i + 1)
                .ok_or_else(|| error("Missing event option value"))?;
            match args[i].as_str() {
                "--timeout-ms" => {
                    timeout = value.parse().map_err(|_| error("Invalid event timeout"))?
                }
                "--count" => count = value.parse().map_err(|_| error("Invalid event count"))?,
                _ => return Err(error("Unknown events option")),
            }
            i += 2;
        }
        if !(1..=60000).contains(&timeout) || !(1..=1000).contains(&count) {
            return Err(error("Event deadline must be 1–60000 ms and count 1–1000"));
        }
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .custom_flags(libc::O_NONBLOCK)
            .open(&args[0])?;
        for event in [STREAM_START, STREAM_STOP] {
            let mut subscription = [0u32; 8];
            subscription[0] = event;
            ioctl(file.as_raw_fd(), 0x4020565a, &mut subscription)?;
        }
        println!(
            "{}",
            json!({"status":"subscribed","device":args[0],"configuresIsp":false,"timeoutMs":timeout})
        );
        io::stdout().flush()?;
        let deadline = Instant::now() + Duration::from_millis(timeout);
        let mut received = 0;
        while received < count {
            let remaining = deadline.saturating_duration_since(Instant::now());
            if remaining.is_zero() {
                break;
            }
            let mut poll = libc::pollfd {
                fd: file.as_raw_fd(),
                events: libc::POLLPRI,
                revents: 0,
            };
            let result = unsafe {
                libc::poll(
                    &mut poll,
                    1,
                    remaining.as_millis().max(1).min(i32::MAX as u128) as i32,
                )
            };
            if result < 0 {
                let e = io::Error::last_os_error();
                if e.kind() == io::ErrorKind::Interrupted {
                    continue;
                }
                return Err(e);
            }
            if result == 0 {
                break;
            }
            if poll.revents & (libc::POLLERR | libc::POLLHUP | libc::POLLNVAL) != 0 {
                return Err(error("Stream-event poll failed"));
            }
            if poll.revents & libc::POLLPRI == 0 {
                continue;
            }
            let mut event = [0u32; 32];
            if let Err(e) = ioctl(file.as_raw_fd(), 0x80805659, &mut event) {
                if e.kind() == io::ErrorKind::WouldBlock {
                    continue;
                }
                return Err(e);
            }
            let name = match event[0] {
                STREAM_START => "stream-start",
                STREAM_STOP => "stream-stop",
                _ => "other",
            };
            println!(
                "{}",
                json!({"event":name,"type":event[0],"sequence":event[19]})
            );
            io::stdout().flush()?;
            received += 1;
        }
        println!(
            "{}",
            json!({"status":"finished","events":received,"countLimitReached":received==count})
        );
        Ok(())
    }
    pub fn run(args: &[String]) -> io::Result<()> {
        match args.first().map(String::as_str) {
            Some("list") if args.len() == 1 => list(),
            Some("capture") => capture(&args[1..]),
            Some("events") => events(&args[1..]),
            _ => Err(error("Unknown command; see --help")),
        }
    }
}

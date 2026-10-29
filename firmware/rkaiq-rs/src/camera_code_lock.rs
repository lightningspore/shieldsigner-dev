//! Opt-in bounded mlock of this executable's file-backed read-only mappings.
use std::io;
const MAX_BYTES:usize=4*1024*1024;
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
struct Range {start:usize,len:usize}
fn ranges(maps:&str,major:u64,minor:u64,inode:u64,page:usize)->io::Result<Vec<Range>> {
    let bad=||io::Error::new(io::ErrorKind::InvalidData,"Invalid executable mapping range");
    if page==0 || !page.is_power_of_two() || inode==0 {return Err(bad());}
    let mut selected=Vec::new();let mut total=0usize;
    for line in maps.lines() {
        let fields=line.split_whitespace().collect::<Vec<_>>();
        if fields.len()<5 {return Err(bad());}
        let Some((ma,mi))=fields[3].split_once(':') else{return Err(bad());};
        let dev=(u64::from_str_radix(ma,16).map_err(|_|bad())?,u64::from_str_radix(mi,16).map_err(|_|bad())?);
        let ino=fields[4].parse::<u64>().map_err(|_|bad())?;
        if ino!=inode || dev!=(major,minor) {continue;}
        let p=fields[1].as_bytes();
        if p.len()!=4 {return Err(bad());}
        // Never pin writable/BSS/heap/DMA or other executable/library mappings.
        if p[1]==b'w' || (p[0]!=b'r' && p[2]!=b'x') {continue;}
        let Some((a,b))=fields[0].split_once('-') else{return Err(bad());};
        let start=usize::from_str_radix(a,16).map_err(|_|bad())?;
        let end=usize::from_str_radix(b,16).map_err(|_|bad())?;
        let len=end.checked_sub(start).filter(|n|*n>0).ok_or_else(bad)?;
        if start%page!=0 || end%page!=0 {return Err(bad());}
        if selected.last().is_some_and(|r:&Range|r.start+r.len>start) {return Err(bad());}
        total=total.checked_add(len).filter(|n|*n<=MAX_BYTES).ok_or_else(||io::Error::new(io::ErrorKind::InvalidData,"Executable mapping lock exceeds 4 MiB cap"))?;
        selected.push(Range{start,len});
    }
    if selected.is_empty(){return Err(io::Error::new(io::ErrorKind::NotFound,"No read-only mappings match /proc/self/exe device/inode"));}
    Ok(selected)
}
#[cfg(target_os="linux")]
pub struct Guard {ranges:Vec<Range>,original:libc::rlimit,raised:bool}
#[cfg(target_os="linux")]
impl Drop for Guard {fn drop(&mut self){for r in &self.ranges {unsafe{libc::munlock(r.start as *const libc::c_void,r.len)};}if self.raised{unsafe{libc::setrlimit(libc::RLIMIT_MEMLOCK,&self.original)};}}}
#[cfg(target_os="linux")]
pub fn from_env()->io::Result<Option<Guard>> {
    use std::os::unix::fs::MetadataExt;
    match std::env::var("SHIELDSIGNER_CAMERA_LOCK_CODE") {
        Err(std::env::VarError::NotPresent)=>return Ok(None),
        Ok(v) if v=="0"=>return Ok(None),
        Ok(v) if v=="1"=>(),
        _=>return Err(io::Error::new(io::ErrorKind::InvalidInput,"SHIELDSIGNER_CAMERA_LOCK_CODE must be 0 or 1")),
    }
    let mut report=serde_json::json!({"event":"executable-code-lock","success":false,"capBytes":MAX_BYTES,"scope":"Only own-executable device/inode matched file mappings with no write permission; no heap/DMA/other libraries"});
    let result=(||->io::Result<Guard>{
        let mut original:libc::rlimit=unsafe{std::mem::zeroed()};
        if unsafe{libc::getrlimit(libc::RLIMIT_MEMLOCK,&mut original)}!=0{return Err(io::Error::last_os_error());}
        report["softLimitBytes"]=serde_json::json!(original.rlim_cur);report["hardLimitBytes"]=serde_json::json!(original.rlim_max);
        let meta=std::fs::metadata("/proc/self/exe")?;
        let page=unsafe{libc::sysconf(libc::_SC_PAGESIZE)};
        if page<=0{return Err(io::Error::new(io::ErrorKind::Other,"Cannot determine page size"));}
        let selected=ranges(&std::fs::read_to_string("/proc/self/maps")?,libc::major(meta.dev()) as u64,libc::minor(meta.dev()) as u64,meta.ino(),page as usize)?;
        let total=selected.iter().map(|r|r.len).sum::<usize>();
        report["requestedBytes"]=serde_json::json!(total);report["mappingCount"]=serde_json::json!(selected.len());
        // Respect the hard limit even if the process has CAP_IPC_LOCK; never
        // raise the hard limit or try to bypass the configured memory budget.
        if total as libc::rlim_t>original.rlim_max{return Err(io::Error::new(io::ErrorKind::PermissionDenied,"Executable lock bytes exceed RLIMIT_MEMLOCK hard limit"));}
        let mut guard=Guard{ranges:Vec::new(),original,raised:false};
        if total as libc::rlim_t>original.rlim_cur {
            let adjusted=libc::rlimit{rlim_cur:total as libc::rlim_t,rlim_max:original.rlim_max};
            if unsafe{libc::setrlimit(libc::RLIMIT_MEMLOCK,&adjusted)}!=0{return Err(io::Error::last_os_error());}
            guard.raised=true;
        }
        for r in selected {
            if unsafe{libc::mlock(r.start as *const libc::c_void,r.len)}!=0{return Err(io::Error::last_os_error());}
            guard.ranges.push(r);
        }
        report["success"]=serde_json::json!(true);report["lockedBytes"]=serde_json::json!(total);report["softLimitRaised"]=serde_json::json!(guard.raised);
        Ok(guard)
    })();
    if let Err(e)=&result {report["error"]=serde_json::json!(e.to_string());report["errno"]=serde_json::json!(e.raw_os_error());report["partialLocksRolledBack"]=serde_json::json!(true);}
    println!("{report}");
    result.map(Some)
}
#[cfg(test)]mod tests{
 use super::*;
 #[test]fn only_own_readonly_file_ranges(){let m="1000-2000 r-xp 0 08:01 42 /exe\n2000-3000 r--p 1000 08:01 42 /exe\n3000-4000 rw-p 2000 08:01 42 /exe\n4000-5000 r--p 0 08:01 43 /other\n5000-6000 r--p 0 00:00 0 [heap]";assert_eq!(ranges(m,8,1,42,4096).unwrap(),vec![Range{start:4096,len:4096},Range{start:8192,len:4096}]);}
 #[test]fn validates_bounds_and_alignment(){for r in ["2000-1000","1001-2000","1000-1000"]{assert!(ranges(&format!("{r} r-xp 0 08:01 42 /exe"),8,1,42,4096).is_err());}}
 #[test]fn cap_prevents_unbounded_lock(){assert!(ranges("1000-802000 r--p 0 08:01 42 /exe",8,1,42,4096).is_err());}
 #[test]fn inode_and_device_required(){assert!(ranges("1000-2000 r-xp 0 08:02 42 /exe",8,1,42,4096).is_err());}
}

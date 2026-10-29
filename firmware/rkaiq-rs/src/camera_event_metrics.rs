//! Bounded diagnostic bookkeeping; never owns, filters, or reorders camera events.
use std::{collections::HashMap, sync::{Mutex, OnceLock}, time::Instant};
use serde_json::{json, Value};
#[derive(Clone, Copy, Default)]
struct Kind { enqueued:u64, dequeued:u64, rejected:u64, handled:u64, max_age_us:u64, age_us:u64, max_handle_us:u64, handle_us:u64 }
#[derive(Default)]
struct Metrics { phases:HashMap<&'static str,PhaseTotals>, kinds:[Kind;2], pending:HashMap<(usize,u32),Instant>, high_water:usize, untracked:u64, wait_calls:u64, wait_us:u64, max_wait_us:u64 }
static METRICS:OnceLock<Mutex<Metrics>>=OnceLock::new();
fn metrics()->std::sync::MutexGuard<'static,Metrics> { METRICS.get_or_init(||Mutex::new(Metrics::default())).lock().unwrap_or_else(|p|p.into_inner()) }
pub fn reset(){*metrics()=Metrics::default();}
pub fn enqueue<T,E>(kind:usize, frame:u32, send:impl FnOnce()->Result<T,E>)->Result<T,E> {
    let mut m=metrics();
    // Serialize only bookkeeping around the existing nonblocking try_send, so
    // an owner cannot observe an event before its enqueue timestamp is recorded.
    let result=send();
    if result.is_ok() {m.kinds[kind].enqueued+=1;m.pending.insert((kind,frame),Instant::now());m.high_water=m.high_water.max(m.pending.len());}
    else {m.kinds[kind].rejected+=1;}
    result
}
pub fn dequeue(kind:usize,frame:u32) {
    let mut m=metrics();m.kinds[kind].dequeued+=1;
    if let Some(t)=m.pending.remove(&(kind,frame)) {let us=t.elapsed().as_micros() as u64;m.kinds[kind].age_us+=us;m.kinds[kind].max_age_us=m.kinds[kind].max_age_us.max(us);}
    else {m.untracked+=1;}
}
pub fn handled(kind:usize,start:Instant) {let us=start.elapsed().as_micros() as u64;let mut m=metrics();m.kinds[kind].handled+=1;m.kinds[kind].handle_us+=us;m.kinds[kind].max_handle_us=m.kinds[kind].max_handle_us.max(us);}
pub fn parameter_wait(start:Instant) {let us=start.elapsed().as_micros() as u64;let mut m=metrics();m.wait_calls+=1;m.wait_us+=us;m.max_wait_us=m.max_wait_us.max(us);}
pub fn summary()->Value {let m=metrics();let records=m.kinds.iter().enumerate().map(|(i,k)|json!({"kind":if i==0{"sof"}else{"statistics"},"enqueued":k.enqueued,"dequeued":k.dequeued,"rejected":k.rejected,"handled":k.handled,"queueAgeTotalUs":k.age_us,"queueAgeMaxUs":k.max_age_us,"handlingTotalUs":k.handle_us,"handlingMaxUs":k.max_handle_us})).collect::<Vec<_>>();json!({"phaseTimingScope":"RUSAGE_THREAD on Linux; nested spans overlap and totals must not be summed. Faults are per-thread deltas, not bytes; non-Linux counters are zero.","phases":m.phases.iter().map(|(name,p)|json!({"name":name,"calls":p.calls,"wallTotalUs":p.wall_us,"threadCpuTotalUs":p.cpu_us,"minorFaults":p.minor,"majorFaults":p.major,"worstWallUs":p.worst.wall_us,"worstThreadCpuUs":p.worst.cpu_us,"worstMinorFaults":p.worst.minor,"worstMajorFaults":p.worst.major,"worstFrame":p.frame})).collect::<Vec<_>>(),"capacity":64,"pendingAtFinish":m.pending.len(),"highWater":m.high_water,"untrackedDequeues":m.untracked,"kinds":records,"parameterSlotWaitCalls":m.wait_calls,"parameterSlotWaitTotalUs":m.wait_us,"parameterSlotWaitMaxUs":m.max_wait_us,"depthScope":"enqueued events not yet acknowledged by owner; may include an event just removed from mpsc before acknowledgement"})}
#[cfg(test)] mod tests {use super::*;#[test] fn tracks_success_rejection_dequeue_and_lazy_send(){reset();assert!(enqueue(0,7,||Ok::<_,()>(())).is_ok());assert!(enqueue(1,8,||Err::<(),_>(())).is_err());dequeue(0,7);handled(0,Instant::now());parameter_wait(Instant::now());{let _phase=Phase::start("test",Some(17));}let s=summary();assert_eq!(s["highWater"],1);assert_eq!(s["pendingAtFinish"],0);assert_eq!(s["kinds"][0]["enqueued"],1);assert_eq!(s["kinds"][0]["dequeued"],1);assert_eq!(s["kinds"][1]["rejected"],1);assert_eq!(s["parameterSlotWaitCalls"],1);assert_eq!(s["phases"][0]["name"],"test");assert_eq!(s["phases"][0]["calls"],1);assert_eq!(s["phases"][0]["worstFrame"],17);}}

#[derive(Clone, Copy, Default)]
struct Sample { wall_us:u64, cpu_us:u64, minor:u64, major:u64 }
#[derive(Default)]
struct PhaseTotals { calls:u64, wall_us:u64, cpu_us:u64, minor:u64, major:u64, worst:Sample, frame:Option<u32> }
fn usage() -> (u64,u64,u64) {
    #[cfg(target_os="linux")]
    { let mut r:libc::rusage=unsafe{std::mem::zeroed()};
      if unsafe{libc::getrusage(libc::RUSAGE_THREAD,&mut r)}==0 {
        let cpu=(r.ru_utime.tv_sec as u64+r.ru_stime.tv_sec as u64)*1_000_000+r.ru_utime.tv_usec as u64+r.ru_stime.tv_usec as u64;
        return(cpu,r.ru_minflt as u64,r.ru_majflt as u64);
      }
    }
    (0,0,0)
}
/// Thread-local CPU/fault counters accompany monotonic wall time. Phase spans
/// may nest (ISP includes its log calls); totals must not be added together.
pub struct Phase { name:&'static str, frame:Option<u32>, start:Instant, usage:(u64,u64,u64) }
impl Phase {
    pub fn start(name:&'static str, frame:Option<u32>)->Self {Self{name,frame,start:Instant::now(),usage:usage()}}
}
impl Drop for Phase {
    fn drop(&mut self) {
        let end=usage();let sample=Sample{wall_us:self.start.elapsed().as_micros() as u64,cpu_us:end.0.saturating_sub(self.usage.0),minor:end.1.saturating_sub(self.usage.1),major:end.2.saturating_sub(self.usage.2)};
        let mut m=metrics();let p=m.phases.entry(self.name).or_default();p.calls+=1;p.wall_us+=sample.wall_us;p.cpu_us+=sample.cpu_us;p.minor+=sample.minor;p.major+=sample.major;
        if sample.wall_us>=p.worst.wall_us {p.worst=sample;p.frame=self.frame;}
    }
}

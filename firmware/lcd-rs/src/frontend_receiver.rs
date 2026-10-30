//! Native delivery worker for an already-connected camera socket. Managed
//! process startup/reconnect policy belongs to the integration coordinator.
use crate::frontend_frame::{Format, Frame, Frames, SocketRead};
use std::io;
use std::os::unix::net::UnixStream;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Condvar, Mutex,
};
use std::thread::JoinHandle;
use std::time::{Duration, Instant};
struct Delivery {
    latest: Option<Arc<Frame>>,
    generation: u64,
    cursors: [(u64, Option<Instant>); 8],
    error: Option<(io::ErrorKind, String)>,
    stopped: bool,
    dropped: u64,
}
pub struct Receiver {
    shared: Arc<(Mutex<Delivery>, Condvar)>,
    stop: Arc<AtomicBool>,
    thread: Mutex<Option<JoinHandle<()>>>,
    period: Duration,
}
impl Receiver {
    pub fn start(
        mut socket: UnixStream,
        width: usize,
        height: usize,
        format: Format,
        timeout: Duration,
        period: Duration,
    ) -> io::Result<Self> {
        let mut frames = Frames::new(width, height, format)?;
        if timeout.is_zero() || timeout > Duration::from_secs(30) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "Invalid frame timeout",
            ));
        }
        let shared = Arc::new((
            Mutex::new(Delivery {
                latest: None,
                generation: 0,
                cursors: [(0, None); 8],
                error: None,
                stopped: false,
                dropped: 0,
            }),
            Condvar::new(),
        ));
        let stop = Arc::new(AtomicBool::new(false));
        let worker_stop = stop.clone();
        let worker_shared = shared.clone();
        let thread = std::thread::Builder::new()
            .name("camera-receive".into())
            .spawn(move || {
                let result = (|| -> io::Result<()> {
                    while !worker_stop.load(Ordering::Acquire) {
                        let published = frames.receive(&mut SocketRead::new(
                            &mut socket,
                            &worker_stop,
                            timeout,
                        )?)?;
                        let mut state = worker_shared.0.lock().unwrap();
                        state.dropped = frames.dropped;
                        if published {
                            state.latest = frames.latest();
                            state.generation = frames.generation;
                            worker_shared.1.notify_all();
                        }
                    }
                    Ok(())
                })();
                let mut state = worker_shared.0.lock().unwrap();
                if !worker_stop.load(Ordering::Acquire) {
                    state.error = result.err().map(|e| (e.kind(), e.to_string()));
                }
                state.stopped = true;
                state.latest = None;
                worker_shared.1.notify_all();
            })?;
        Ok(Self {
            shared,
            stop,
            thread: Mutex::new(Some(thread)),
            period,
        })
    }
    pub fn read(&self, consumer: usize, timeout: Duration) -> io::Result<Option<Arc<Frame>>> {
        if consumer >= 8 {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "Consumer must be within 0..8",
            ));
        }
        let deadline = Instant::now() + timeout;
        let mut state = self.shared.0.lock().unwrap();
        loop {
            if let Some((kind, error)) = &state.error {
                return Err(io::Error::new(*kind, error.clone()));
            }
            if state.stopped || self.stop.load(Ordering::Acquire) {
                return Ok(None);
            }
            let now = Instant::now();
            let (previous, due) = state.cursors[consumer];
            let fresh = state.latest.is_some() && state.generation != previous;
            if fresh && due.map_or(true, |due| now >= due) {
                state.cursors[consumer] = (state.generation, Some(now + self.period));
                return Ok(state.latest.clone());
            }
            if now >= deadline {
                return Ok(None);
            }
            let wait = if fresh {
                due.unwrap()
                    .saturating_duration_since(now)
                    .min(deadline - now)
            } else {
                deadline - now
            };
            state = self.shared.1.wait_timeout(state, wait).unwrap().0;
        }
    }
    pub fn statistics(&self) -> (u64, u64, bool) {
        let state = self.shared.0.lock().unwrap();
        (state.generation, state.dropped, state.stopped)
    }
    pub fn close(&self) -> io::Result<()> {
        self.stop.store(true, Ordering::Release);
        self.shared.1.notify_all();
        if let Some(thread) = self.thread.lock().unwrap().take() {
            thread.join().map_err(|_| {
                io::Error::new(io::ErrorKind::Other, "Camera reception thread panicked")
            })?;
        }
        Ok(())
    }
}
impl Drop for Receiver {
    fn drop(&mut self) {
        let _ = self.close();
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    #[test]
    fn receives_paces_independent_consumers_and_closes_stalled_socket() {
        let (socket, mut peer) = UnixStream::pair().unwrap();
        let mut reader = Receiver::start(
            socket,
            2,
            2,
            Format::Nv12,
            Duration::from_secs(3),
            Duration::ZERO,
        )
        .unwrap();
        let mut frame = b"SSNV12F1".to_vec();
        for n in [2u32, 2, 7, 6] {
            frame.extend(n.to_le_bytes());
        }
        frame.extend([7; 6]);
        peer.write_all(&frame).unwrap();
        assert_eq!(
            reader
                .read(0, Duration::from_secs(1))
                .unwrap()
                .unwrap()
                .sequence,
            7
        );
        assert_eq!(
            reader
                .read(1, Duration::from_secs(1))
                .unwrap()
                .unwrap()
                .pixels,
            [7; 6]
        );
        assert!(reader.read(0, Duration::from_millis(10)).unwrap().is_none());
        let start = Instant::now();
        reader.close().unwrap();
        reader.close().unwrap();
        assert!(start.elapsed() < Duration::from_millis(300));
        assert!(reader.read(0, Duration::ZERO).unwrap().is_none());
    }
    #[test]
    fn disconnect_is_reported_and_worker_stops() {
        let (socket, peer) = UnixStream::pair().unwrap();
        let mut reader = Receiver::start(
            socket,
            2,
            2,
            Format::Nv12,
            Duration::from_secs(1),
            Duration::ZERO,
        )
        .unwrap();
        drop(peer);
        assert!(reader.read(0, Duration::from_secs(1)).is_err());
        reader.close().unwrap();
        assert!(reader.statistics().2);
    }
}

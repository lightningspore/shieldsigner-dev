//! Bounded camera frame storage. Held consumer frames are immutable; reception
//! drops a frame when every slot is pinned rather than allocating another.
use std::io::{self, Read};
use std::sync::Arc;
use std::time::{Duration, Instant};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Format {
    Nv12,
    Rgb,
}
impl Format {
    pub fn payload_size(self, width: usize, height: usize) -> io::Result<usize> {
        if width == 0
            || height == 0
            || width > 1920
            || height > 1920
            || width * height > 2_073_600
            || (self == Self::Nv12 && (width % 2 != 0 || height % 2 != 0))
        {
            return Err(invalid("Invalid camera geometry"));
        }
        Ok(match self {
            Self::Nv12 => width * height * 3 / 2,
            Self::Rgb => width * height * 3,
        })
    }
}
fn invalid(message: &'static str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, message)
}
#[derive(Debug)]
pub struct Frame {
    pub pixels: Vec<u8>,
    pub sequence: u32,
    pub width: usize,
    pub height: usize,
    pub format: Format,
}
pub struct Frames {
    slots: [Arc<Frame>; 3],
    latest: Option<usize>,
    pub generation: u64,
    pub dropped: u64,
    size: usize,
    width: usize,
    height: usize,
    format: Format,
}
impl Frames {
    pub fn new(width: usize, height: usize, format: Format) -> io::Result<Self> {
        let size = format.payload_size(width, height)?;
        Ok(Self {
            slots: std::array::from_fn(|_| {
                Arc::new(Frame {
                    pixels: vec![0; size],
                    sequence: 0,
                    width,
                    height,
                    format,
                })
            }),
            latest: None,
            generation: 0,
            dropped: 0,
            size,
            width,
            height,
            format,
        })
    }
    // The caller supplies a deadline/cancellation-aware Read implementation.
    // A partial frame is never published or used as a resynchronization point.
    pub fn receive(&mut self, source: &mut impl Read) -> io::Result<bool> {
        let mut header = [0; 24];
        source.read_exact(&mut header)?;
        let word =
            |offset| u32::from_le_bytes(header[offset..offset + 4].try_into().unwrap()) as usize;
        let magic: &[u8] = match self.format {
            Format::Nv12 => b"SSNV12F1",
            Format::Rgb => b"SSRGB001",
        };
        if &header[..8] != magic
            || word(8) != self.width
            || word(12) != self.height
            || word(20) != self.size
        {
            return Err(invalid(
                "Unexpected camera protocol, dimensions or payload size",
            ));
        }
        let free =
            self.slots.iter().enumerate().position(|(index, frame)| {
                Some(index) != self.latest && Arc::strong_count(frame) == 1
            });
        if let Some(index) = free {
            let frame = Arc::get_mut(&mut self.slots[index]).unwrap();
            source.read_exact(&mut frame.pixels)?;
            frame.sequence = word(16) as u32;
            self.latest = Some(index);
            self.generation += 1;
            Ok(true)
        } else {
            let mut scratch = [0; 4096];
            let mut left = self.size;
            while left > 0 {
                let size = left.min(scratch.len());
                source.read_exact(&mut scratch[..size])?;
                left -= size;
            }
            self.dropped += 1;
            Ok(false)
        }
    }
    pub fn latest(&self) -> Option<Arc<Frame>> {
        self.latest.map(|index| Arc::clone(&self.slots[index]))
    }
}
/// Each consumer owns a cursor, so preview cannot steal the decoder's frame.
#[derive(Default)]
pub struct Cursor {
    generation: u64,
    next_due: Option<Instant>,
}
impl Cursor {
    pub fn take(&mut self, frames: &Frames, now: Instant, period: Duration) -> Option<Arc<Frame>> {
        if self.generation == frames.generation || self.next_due.is_some_and(|due| now < due) {
            return None;
        }
        let frame = frames.latest()?;
        self.generation = frames.generation;
        self.next_due = Some(now + period);
        Some(frame)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn packet(sequence: u32) -> Vec<u8> {
        let mut v = b"SSNV12F1".to_vec();
        for n in [2u32, 2, sequence, 6] {
            v.extend(n.to_le_bytes());
        }
        v.extend([sequence as u8; 6]);
        v
    }
    #[test]
    fn pinned_frames_bound_pool_and_drop_without_mutation() {
        let mut frames = Frames::new(2, 2, Format::Nv12).unwrap();
        let mut held = Vec::new();
        for n in 1..=3 {
            assert!(frames.receive(&mut &packet(n)[..]).unwrap());
            held.push(frames.latest().unwrap());
        }
        let addresses: Vec<_> = held.iter().map(|f| f.pixels.as_ptr()).collect();
        assert!(!frames.receive(&mut &packet(4)[..]).unwrap());
        assert_eq!((frames.generation, frames.dropped), (3, 1));
        for (i, f) in held.iter().enumerate() {
            assert_eq!(f.pixels, vec![(i + 1) as u8; 6]);
        }
        drop(held.remove(0));
        assert!(frames.receive(&mut &packet(5)[..]).unwrap());
        assert!(addresses.contains(&frames.latest().unwrap().pixels.as_ptr()));
    }
    #[test]
    fn partial_or_bad_header_never_publishes() {
        let mut frames = Frames::new(2, 2, Format::Nv12).unwrap();
        assert!(frames.receive(&mut &packet(1)[..25]).is_err());
        assert!(frames.latest().is_none());
        let mut bad = packet(2);
        bad[20] = 7;
        assert!(frames.receive(&mut &bad[..]).is_err());
        assert_eq!(frames.generation, 0);
    }
    #[test]
    fn consumers_independent_paced_latest_only() {
        let mut frames = Frames::new(2, 2, Format::Nv12).unwrap();
        let mut a = Cursor::default();
        let mut b = Cursor::default();
        let now = Instant::now();
        let period = Duration::from_millis(100);
        frames.receive(&mut &packet(1)[..]).unwrap();
        assert_eq!(a.take(&frames, now, period).unwrap().sequence, 1);
        assert_eq!(b.take(&frames, now, period).unwrap().sequence, 1);
        for n in 2..=5 {
            frames.receive(&mut &packet(n)[..]).unwrap();
        }
        assert!(a.take(&frames, now, period).is_none());
        assert_eq!(a.take(&frames, now + period, period).unwrap().sequence, 5);
        assert!(a.take(&frames, now + period + period, period).is_none());
    }
}

#[cfg(unix)]
pub struct SocketRead<'a> {
    socket: &'a mut std::os::unix::net::UnixStream,
    stop: &'a std::sync::atomic::AtomicBool,
    deadline: Instant,
}
#[cfg(unix)]
impl<'a> SocketRead<'a> {
    pub fn new(
        socket: &'a mut std::os::unix::net::UnixStream,
        stop: &'a std::sync::atomic::AtomicBool,
        timeout: Duration,
    ) -> io::Result<Self> {
        if timeout.is_zero() || timeout > Duration::from_secs(30) {
            return Err(invalid("Frame timeout outside (0,30] seconds"));
        }
        socket.set_nonblocking(true)?;
        Ok(Self {
            socket,
            stop,
            deadline: Instant::now() + timeout,
        })
    }
}
#[cfg(unix)]
impl Read for SocketRead<'_> {
    fn read(&mut self, bytes: &mut [u8]) -> io::Result<usize> {
        use std::os::fd::AsRawFd;
        use std::sync::atomic::Ordering;
        if bytes.is_empty() {
            return Ok(0);
        }
        loop {
            if self.stop.load(Ordering::Acquire) {
                return Err(io::Error::new(
                    io::ErrorKind::ConnectionAborted,
                    "Camera reception cancelled",
                ));
            }
            let remaining = self.deadline.saturating_duration_since(Instant::now());
            if remaining.is_zero() {
                return Err(io::Error::new(
                    io::ErrorKind::TimedOut,
                    "Camera whole-frame deadline",
                ));
            }
            let mut fd = libc::pollfd {
                fd: self.socket.as_raw_fd(),
                events: libc::POLLIN,
                revents: 0,
            };
            let ms = remaining.as_millis().saturating_add(1).min(20) as i32;
            let result = unsafe { libc::poll(&mut fd, 1, ms) };
            if result < 0 {
                let error = io::Error::last_os_error();
                if error.kind() != io::ErrorKind::Interrupted {
                    return Err(error);
                }
                continue;
            }
            if result == 0 {
                continue;
            }
            match self.socket.read(bytes) {
                Err(error)
                    if matches!(
                        error.kind(),
                        io::ErrorKind::Interrupted | io::ErrorKind::WouldBlock
                    ) =>
                {
                    continue
                }
                result => return result,
            }
        }
    }
}
#[cfg(all(test, unix))]
mod socket_tests {
    use super::*;
    use std::io::Write;
    use std::os::unix::net::UnixStream;
    use std::sync::atomic::{AtomicBool, Ordering};
    #[test]
    fn stop_interrupts_stalled_frame() {
        let (mut socket, _peer) = UnixStream::pair().unwrap();
        let stop = Arc::new(AtomicBool::new(false));
        let other = stop.clone();
        let task = std::thread::spawn(move || {
            std::thread::sleep(Duration::from_millis(30));
            other.store(true, Ordering::Release);
        });
        let start = Instant::now();
        let mut reader = SocketRead::new(&mut socket, &stop, Duration::from_secs(3)).unwrap();
        assert_eq!(
            reader.read(&mut [0; 24]).unwrap_err().kind(),
            io::ErrorKind::ConnectionAborted
        );
        assert!(start.elapsed() < Duration::from_millis(300));
        task.join().unwrap();
    }
    #[test]
    fn trickling_bytes_cannot_extend_whole_frame_deadline() {
        let (mut socket, mut peer) = UnixStream::pair().unwrap();
        let stop = AtomicBool::new(false);
        let task = std::thread::spawn(move || {
            for _ in 0..20 {
                if peer.write_all(&[1]).is_err() {
                    break;
                }
                std::thread::sleep(Duration::from_millis(15));
            }
        });
        let start = Instant::now();
        let mut reader = SocketRead::new(&mut socket, &stop, Duration::from_millis(60)).unwrap();
        assert_eq!(
            reader.read_exact(&mut [0; 24]).unwrap_err().kind(),
            io::ErrorKind::TimedOut
        );
        assert!(start.elapsed() < Duration::from_millis(250));
        drop(socket);
        task.join().unwrap();
    }
}

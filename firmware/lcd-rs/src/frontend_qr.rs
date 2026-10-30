//! Persistent, bounded ZXing worker protocol. No payload or image logging.
use std::fs;
use std::io::{self, Read, Write};
use std::net::Shutdown;
use std::os::fd::AsRawFd;
use std::os::fd::OwnedFd;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::net::UnixStream;
use std::os::unix::process::{CommandExt, ExitStatusExt};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

pub const MAX_REPLY: usize = 8192;
fn invalid(message: &'static str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, message)
}
fn remaining(deadline: Instant) -> io::Result<Duration> {
    let duration = deadline.saturating_duration_since(Instant::now());
    if duration.is_zero() {
        Err(io::Error::new(
            io::ErrorKind::TimedOut,
            "QR whole-operation deadline",
        ))
    } else {
        // Quantize to whole microseconds before platform timeval conversion.
        // Never extend the application deadline for each partial read.
        Ok(Duration::from_micros(duration.as_micros().max(1) as u64))
    }
}
fn ready(stream: &UnixStream, deadline: Instant, events: libc::c_short) -> io::Result<()> {
    loop {
        let duration = remaining(deadline)?;
        let mut fd = libc::pollfd {
            fd: stream.as_raw_fd(),
            events,
            revents: 0,
        };
        let millis = duration.as_millis().saturating_add(1).min(i32::MAX as u128) as i32;
        let result = unsafe { libc::poll(&mut fd, 1, millis) };
        if result > 0 {
            return Ok(());
        }
        if result == 0 {
            continue;
        }
        let error = io::Error::last_os_error();
        if error.kind() != io::ErrorKind::Interrupted {
            return Err(error);
        }
    }
}
pub(crate) fn read_deadline(
    stream: &mut UnixStream,
    mut out: &mut [u8],
    deadline: Instant,
) -> io::Result<()> {
    stream.set_nonblocking(true)?;
    while !out.is_empty() {
        ready(stream, deadline, libc::POLLIN)?;
        match stream.read(out) {
            Ok(0) => {
                return Err(io::Error::new(
                    io::ErrorKind::UnexpectedEof,
                    "QR worker closed its connection",
                ))
            }
            Ok(n) => out = &mut out[n..],
            Err(e)
                if matches!(
                    e.kind(),
                    io::ErrorKind::Interrupted | io::ErrorKind::WouldBlock
                ) =>
            {
                continue
            }
            Err(e) => return Err(e),
        }
    }
    Ok(())
}
pub(crate) fn write_deadline(
    stream: &mut UnixStream,
    mut bytes: &[u8],
    deadline: Instant,
) -> io::Result<()> {
    stream.set_nonblocking(true)?;
    while !bytes.is_empty() {
        ready(stream, deadline, libc::POLLOUT)?;
        match stream.write(bytes) {
            Ok(0) => return Err(io::Error::new(io::ErrorKind::WriteZero, "QR short write")),
            Ok(n) => bytes = &bytes[n..],
            Err(e)
                if matches!(
                    e.kind(),
                    io::ErrorKind::Interrupted | io::ErrorKind::WouldBlock
                ) =>
            {
                continue
            }
            Err(e) => return Err(e),
        }
    }
    Ok(())
}
pub fn validate_image(pixels: &[u8], width: usize, height: usize) -> io::Result<()> {
    if width == 0
        || height == 0
        || width > 1920
        || height > 1920
        || width * height > 2_073_600
        || pixels.len() != width * height
    {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "QR image geometry or byte count outside bounds",
        ));
    }
    Ok(())
}

pub struct Session {
    stream: UnixStream,
    timeout: Duration,
    poisoned: bool,
}
impl Session {
    pub fn open(mut stream: UnixStream, timeout: Duration) -> io::Result<Self> {
        let mut hello = [0; 8];
        read_deadline(&mut stream, &mut hello, Instant::now() + timeout)?;
        if &hello != b"SSQR001\n" {
            return Err(invalid("Unsupported QR protocol greeting"));
        }
        Ok(Self {
            stream,
            timeout,
            poisoned: false,
        })
    }
    pub fn decode(
        &mut self,
        pixels: &[u8],
        width: usize,
        height: usize,
    ) -> io::Result<Option<Vec<u8>>> {
        self.decode_until(pixels, width, height, Instant::now() + self.timeout)
    }
    fn decode_until(
        &mut self,
        pixels: &[u8],
        width: usize,
        height: usize,
        deadline: Instant,
    ) -> io::Result<Option<Vec<u8>>> {
        validate_image(pixels, width, height)?;
        if self.poisoned {
            return Err(invalid("QR session requires a fresh worker"));
        }
        let result = (|| {
            let mut header = [0; 12];
            header[..4].copy_from_slice(b"QRI1");
            header[4..8].copy_from_slice(&(width as u32).to_le_bytes());
            header[8..12].copy_from_slice(&(height as u32).to_le_bytes());
            write_deadline(&mut self.stream, &header, deadline)?;
            write_deadline(&mut self.stream, pixels, deadline)?;
            let mut response = [0; 8];
            read_deadline(&mut self.stream, &mut response, deadline)?;
            if &response[..4] != b"QRO1" {
                return Err(invalid("Malformed QR response magic"));
            }
            let size = u32::from_le_bytes(response[4..8].try_into().unwrap());
            if size == u32::MAX {
                return Ok(None);
            }
            if size as usize > MAX_REPLY {
                return Err(invalid("QR response exceeds bounded payload"));
            }
            let mut payload = vec![0; size as usize];
            read_deadline(&mut self.stream, &mut payload, deadline)?;
            Ok(Some(payload))
        })();
        if result.is_err() {
            self.poisoned = true;
            let _ = self.stream.shutdown(Shutdown::Both);
        }
        result
    }
}

#[derive(Clone, Default, Debug)]
pub struct Statistics {
    pub starts: u64,
    pub calls: u64,
    pub decoded: u64,
    pub errors: u64,
    pub last_seconds: Option<f64>,
    pub last_exit_code: Option<i32>,
}
pub struct Worker {
    binary: PathBuf,
    timeout: Duration,
    session: Option<Session>,
    child: Option<Child>,
    pub statistics: Statistics,
}
impl Worker {
    pub fn new(binary: &Path, timeout: Duration) -> io::Result<Self> {
        if !binary.is_absolute()
            || !binary.is_file()
            || fs::metadata(binary)?.permissions().mode() & 0o111 == 0
        {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "QR worker must be an absolute executable file",
            ));
        }
        if timeout.is_zero() || timeout > Duration::from_secs(30) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "QR timeout outside (0,30] seconds",
            ));
        }
        Ok(Self {
            binary: binary.into(),
            timeout,
            session: None,
            child: None,
            statistics: Statistics::default(),
        })
    }
    fn start(&mut self, deadline: Instant) -> io::Result<()> {
        if let Some(child) = &mut self.child {
            if child.try_wait()?.is_none() && self.session.is_some() {
                return Ok(());
            }
        }
        self.close()?;
        let (parent, child_socket) = UnixStream::pair()?;
        let input = Stdio::from(fs::File::from(OwnedFd::from(child_socket.try_clone()?)));
        let output = Stdio::from(fs::File::from(OwnedFd::from(child_socket)));
        let mut command = Command::new(&self.binary);
        command.stdin(input).stdout(output).stderr(Stdio::null());
        // Only an async-signal-safe syscall runs after fork; no Python callback.
        unsafe {
            command.pre_exec(|| {
                if libc::setsid() < 0 {
                    Err(io::Error::last_os_error())
                } else {
                    Ok(())
                }
            });
        }
        self.child = Some(command.spawn()?);
        match Session::open(parent, remaining(deadline)?) {
            Ok(session) => {
                self.session = Some(session);
                self.statistics.starts += 1;
                Ok(())
            }
            Err(e) => {
                let _ = self.close();
                Err(e)
            }
        }
    }
    pub fn decode(
        &mut self,
        pixels: &[u8],
        width: usize,
        height: usize,
    ) -> io::Result<Option<Vec<u8>>> {
        validate_image(pixels, width, height)?;
        let start = Instant::now();
        let result = self.start(start + self.timeout).and_then(|()| {
            self.session
                .as_mut()
                .unwrap()
                .decode_until(pixels, width, height, start + self.timeout)
        });
        match &result {
            Ok(payload) => {
                self.statistics.calls += 1;
                self.statistics.decoded += u64::from(payload.is_some());
                self.statistics.last_seconds = Some(start.elapsed().as_secs_f64());
            }
            Err(_) => {
                self.statistics.errors += 1;
                let _ = self.close();
            }
        }
        result
    }
    pub fn pid(&self) -> Option<u32> {
        self.child.as_ref().map(Child::id)
    }
    pub fn close(&mut self) -> io::Result<()> {
        if let Some(session) = self.session.take() {
            let _ = session.stream.shutdown(Shutdown::Both);
        }
        let Some(mut child) = self.child.take() else {
            return Ok(());
        };
        let result = (|| {
            for graceful in [true, false] {
                if !graceful {
                    let result = unsafe { libc::kill(child.id() as libc::pid_t, libc::SIGTERM) };
                    if result < 0 && io::Error::last_os_error().raw_os_error() != Some(libc::ESRCH)
                    {
                        return Err(io::Error::last_os_error());
                    }
                }
                let deadline = Instant::now() + Duration::from_millis(500);
                loop {
                    if let Some(status) = child.try_wait()? {
                        return Ok(status);
                    }
                    if Instant::now() >= deadline {
                        break;
                    }
                    std::thread::sleep(Duration::from_millis(10));
                }
            }
            child.kill()?;
            child.wait()
        })();
        match result {
            Ok(status) => {
                self.statistics.last_exit_code =
                    status.code().or_else(|| status.signal().map(|s| -s));
                Ok(())
            }
            Err(e) => {
                let _ = child.kill();
                let _ = child.wait();
                Err(e)
            }
        }
    }
}
impl Drop for Worker {
    fn drop(&mut self) {
        let _ = self.close();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn exchange(reply: Vec<u8>) -> (Session, std::thread::JoinHandle<()>) {
        let (client, mut server) = UnixStream::pair().unwrap();
        let task = std::thread::spawn(move || {
            for b in b"SSQR001\n" {
                server.write_all(&[*b]).unwrap();
            }
            let mut request = [0; 16];
            server.read_exact(&mut request).unwrap();
            assert_eq!(&request[..4], b"QRI1");
            assert_eq!(&request[12..], &[1, 2, 3, 4]);
            for byte in reply {
                if server.write_all(&[byte]).is_err() {
                    break;
                }
            }
        });
        (Session::open(client, Duration::from_secs(1)).unwrap(), task)
    }
    fn reply(data: &[u8]) -> Vec<u8> {
        let mut b = b"QRO1".to_vec();
        b.extend((data.len() as u32).to_le_bytes());
        b.extend(data);
        b
    }
    #[test]
    fn exact_binary_and_empty_results_survive_fragmented_io() {
        for data in [
            vec![0, 255, 10, 13, 0, 128],
            (0..=255).collect::<Vec<u8>>(),
            vec![],
        ] {
            let (mut session, task) = exchange(reply(&data));
            assert_eq!(session.decode(&[1, 2, 3, 4], 2, 2).unwrap(), Some(data));
            task.join().unwrap();
        }
    }
    #[test]
    fn no_symbol_is_distinct_from_empty_bytes() {
        let mut bytes = b"QRO1".to_vec();
        bytes.extend(u32::MAX.to_le_bytes());
        let (mut session, task) = exchange(bytes);
        assert_eq!(session.decode(&[1, 2, 3, 4], 2, 2).unwrap(), None);
        task.join().unwrap();
    }
    #[test]
    fn malformed_oversized_and_truncated_responses_poison_session() {
        let mut oversized = b"QRO1".to_vec();
        oversized.extend(8193u32.to_le_bytes());
        for response in [
            b"BAD!\0\0\0\0".to_vec(),
            oversized,
            b"QRO1\x05\0\0\0hi".to_vec(),
        ] {
            let (mut session, task) = exchange(response);
            assert!(session.decode(&[1, 2, 3, 4], 2, 2).is_err());
            assert!(session.decode(&[1, 2, 3, 4], 2, 2).is_err());
            task.join().unwrap();
        }
    }
    #[test]
    fn invalid_geometry_fails_before_any_request() {
        for (bytes, w, h) in [
            (&[0; 3][..], 2, 2),
            (&[][..], 0, 1),
            (&[][..], 1921, 1),
            (&[][..], 1920, 1920),
        ] {
            assert!(validate_image(bytes, w, h).is_err());
        }
    }
    #[test]
    fn whole_response_deadline_does_not_reset_for_each_byte() {
        let (client, mut server) = UnixStream::pair().unwrap();
        let task = std::thread::spawn(move || {
            server.write_all(b"SSQR001\n").unwrap();
            let mut request = [0; 16];
            server.read_exact(&mut request).unwrap();
            for b in reply(&[1, 2, 3]) {
                std::thread::sleep(Duration::from_millis(40));
                if server.write_all(&[b]).is_err() {
                    break;
                }
            }
        });
        let mut session = Session::open(client, Duration::from_millis(100)).unwrap();
        let start = Instant::now();
        assert!(session.decode(&[1, 2, 3, 4], 2, 2).is_err());
        assert!(start.elapsed() < Duration::from_secs(1));
        task.join().unwrap();
    }
    #[test]
    fn bad_or_missing_greeting_fails() {
        let (client, mut server) = UnixStream::pair().unwrap();
        server.write_all(b"BADHELLO").unwrap();
        assert!(Session::open(client, Duration::from_millis(100)).is_err());
        let (client, _server) = UnixStream::pair().unwrap();
        assert!(Session::open(client, Duration::from_millis(30)).is_err());
    }
    #[test]
    fn stubborn_owned_worker_is_killed_and_reaped() {
        let path = std::env::temp_dir().join(format!(
            "shieldsigner-qr-stubborn-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&path).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o700)).unwrap();
        let binary = path.join("worker");
        fs::write(
            &binary,
            b"#!/bin/sh\ntrap '' TERM\nprintf 'SSQR001\\n'\nexec sleep 10\n",
        )
        .unwrap();
        fs::set_permissions(&binary, fs::Permissions::from_mode(0o700)).unwrap();
        let mut worker = Worker::new(&binary, Duration::from_secs(1)).unwrap();
        worker
            .start(Instant::now() + Duration::from_secs(1))
            .unwrap();
        let pid = worker.pid().unwrap();
        let start = Instant::now();
        worker.close().unwrap();
        assert!(start.elapsed() < Duration::from_secs(3));
        assert_eq!(worker.statistics.last_exit_code, Some(-libc::SIGKILL));
        assert_eq!(unsafe { libc::kill(pid as libc::pid_t, 0) }, -1);
        fs::remove_dir_all(path).unwrap();
    }

    #[test]
    fn owned_worker_is_reaped_and_close_is_idempotent() {
        let path = std::env::temp_dir().join(format!(
            "shieldsigner-qr-worker-test-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&path).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o700)).unwrap();
        let binary = path.join("worker");
        fs::write(&binary, b"#!/bin/sh\nprintf 'SSQR001\\n'\ncat >/dev/null\n").unwrap();
        fs::set_permissions(&binary, fs::Permissions::from_mode(0o700)).unwrap();
        let mut worker = Worker::new(&binary, Duration::from_secs(1)).unwrap();
        worker
            .start(Instant::now() + Duration::from_secs(1))
            .unwrap();
        let pid = worker.child.as_ref().unwrap().id();
        worker.close().unwrap();
        worker.close().unwrap();
        assert_eq!(worker.statistics.starts, 1);
        assert_eq!(worker.statistics.last_exit_code, Some(0));
        assert_eq!(unsafe { libc::kill(pid as libc::pid_t, 0) }, -1);
        fs::remove_dir_all(path).unwrap();
    }
}

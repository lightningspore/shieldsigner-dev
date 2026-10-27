//! Recovered metadata-output branches of XCam V4l2Device. Device/pool methods
//! are explicit boundaries; full ISP parameter assembly/startup remains separate.
use crate::InvalidInput;
pub const BUFFER_BYTES: usize = 68;
pub const META_OUTPUT: u32 = 14;
pub type BufferRecord = [u8; BUFFER_BYTES];
pub fn word(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap())
}
pub fn put(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BufferState {
    pub record: BufferRecord,
    pub queued: bool,
    pub returned_length: u32,
}
impl BufferState {
    pub fn from_record(record: BufferRecord) -> Result<Self, InvalidInput> {
        if word(&record, 4) != META_OUTPUT || !matches!(word(&record, 48), 1 | 2) {
            return Err(InvalidInput::Length);
        }
        Ok(Self {
            record,
            queued: false,
            returned_length: 0,
        })
    }
    fn reset(&mut self) {
        self.record[20..48].fill(0); // timeval, timecode, sequence.
        self.queued = false;
    }
}
pub trait Backend {
    fn request_buffers(&mut self) -> i32;
    fn initialize_pool(&mut self) -> i32;
    fn stream_on(&mut self) -> i32;
    fn stream_off(&mut self) -> i32;
    fn close(&mut self);
    fn finalize_pool(&mut self);
    fn lock(&mut self);
    fn unlock(&mut self);
    fn queue(&mut self, request: &mut BufferRecord) -> i32;
    fn dequeue(&mut self, request: &mut BufferRecord) -> i32;
}
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Queue {
    pub queued_count: u32,
    pub active: bool,
}
impl Queue {
    /// Native get_buffer: prefer a free requested slot, otherwise scan from 0.
    /// Acquisition changes only the shared queued/in-use flag, not metadata or
    /// mapped parameter payload. Empty/exhausted pools return -3. Invalid
    /// preferred indexes are rejected instead of native unchecked vector access.
    pub fn get_buffer<B: Backend>(
        &self,
        backend: &mut B,
        buffers: &mut [BufferState],
        preferred: Option<usize>,
    ) -> Result<usize, i32> {
        backend.lock();
        let result = if buffers.is_empty() {
            Err(-3)
        } else if preferred.is_some_and(|i| i >= buffers.len()) {
            Err(-6)
        } else {
            let selected = preferred
                .filter(|&i| !buffers[i].queued)
                .or_else(|| buffers.iter().position(|b| !b.queued));
            if let Some(i) = selected {
                buffers[i].queued = true;
                Ok(i)
            } else {
                Err(-3)
            }
        };
        backend.unlock();
        result
    }

    pub fn prepare<B: Backend>(&mut self, backend: &mut B) -> i32 {
        let result = backend.request_buffers();
        if result != 0 {
            return result;
        }
        self.queued_count = 0;
        backend.initialize_pool() // META_OUTPUT does not auto-QBUF the pool.
    }
    pub fn start<B: Backend>(&mut self, backend: &mut B, already_prepared: bool) -> i32 {
        if !already_prepared {
            let result = self.prepare(backend);
            if result != 0 {
                return result;
            }
        }
        if backend.stream_on() < 0 {
            backend.close();
            return -9;
        }
        self.active = true;
        0
    }
    /// Cached record is reset; bytesused=length and optional cache-sync flags
    /// apply only to the temporary ioctl record, not the cached descriptor.
    pub fn queue<B: Backend>(
        &mut self,
        backend: &mut B,
        buffer: &mut BufferState,
        already_locked: bool,
        cache_sync: bool,
    ) -> i32 {
        if !already_locked {
            backend.lock();
        }
        buffer.reset();
        let mut request = buffer.record;
        put(&mut request, 8, word(&buffer.record, 56));
        self.queued_count = self.queued_count.wrapping_add(1);
        buffer.queued = true;
        if !already_locked {
            backend.unlock();
        }
        if cache_sync {
            put(&mut request, 12, 0x1800);
        }
        if backend.queue(&mut request) < 0 {
            if !already_locked {
                backend.lock();
            }
            buffer.queued = false;
            self.queued_count = self.queued_count.wrapping_sub(1);
            if !already_locked {
                backend.unlock();
            }
            return -9;
        }
        0
    }
    pub fn dequeue<B: Backend>(
        &mut self,
        backend: &mut B,
        buffers: &mut [BufferState],
        memory: u32,
        cache_sync: bool,
    ) -> Result<usize, i32> {
        if !self.active {
            return Err(-2);
        }
        let mut request = [0; BUFFER_BYTES];
        put(&mut request, 4, META_OUTPUT);
        put(&mut request, 48, memory);
        if cache_sync {
            put(&mut request, 12, 0x1800);
        }
        if backend.dequeue(&mut request) < 0 {
            return Err(-9);
        }
        let index = word(&request, 0) as usize;
        // Native checks index > count, permitting one-past-end access. The
        // checked Rust API intentionally rejects that invalid driver response.
        let Some(buffer) = buffers.get_mut(index) else {
            return Err(-6);
        };
        backend.lock();
        buffer.record[20..48].copy_from_slice(&request[20..48]);
        buffer.returned_length = word(&request, 56);
        // META_OUTPUT keeps queued=true until explicit return to pool.
        self.queued_count = self.queued_count.wrapping_sub(1);
        backend.unlock();
        Ok(index)
    }
    pub fn return_to_pool<B: Backend>(&mut self, backend: &mut B, buffer: &mut BufferState) {
        backend.lock();
        buffer.reset();
        backend.unlock();
    }
    /// Native stop ignores STREAMOFF status. The backend must retain cleanup
    /// errors if its caller needs them; closing the file remains its ownership.
    pub fn stop<B: Backend>(&mut self, backend: &mut B, has_pool: bool) {
        backend.lock();
        if self.active {
            backend.stream_off();
            self.active = false;
        }
        if has_pool {
            backend.finalize_pool();
        }
        backend.unlock();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    struct Driver;
    impl Backend for Driver {
        fn request_buffers(&mut self) -> i32 {
            0
        }
        fn initialize_pool(&mut self) -> i32 {
            0
        }
        fn stream_on(&mut self) -> i32 {
            0
        }
        fn stream_off(&mut self) -> i32 {
            0
        }
        fn close(&mut self) {}
        fn finalize_pool(&mut self) {}
        fn lock(&mut self) {}
        fn unlock(&mut self) {}
        fn queue(&mut self, _: &mut BufferRecord) -> i32 {
            0
        }
        fn dequeue(&mut self, r: &mut BufferRecord) -> i32 {
            put(r, 0, 1);
            0
        }
    }
    #[test]
    fn reject_native_one_past_end_response_without_changing_state() {
        let mut record = [0; BUFFER_BYTES];
        put(&mut record, 4, META_OUTPUT);
        put(&mut record, 48, 1);
        let buffer = BufferState::from_record(record).unwrap();
        let mut buffers = [buffer];
        let mut queue = Queue {
            active: true,
            queued_count: 1,
        };
        let before = queue;
        assert_eq!(queue.dequeue(&mut Driver, &mut buffers, 1, false), Err(-6));
        assert_eq!(queue, before);
        assert_eq!(buffers, [buffer]);
    }
    #[test]
    fn invalid_preferred_buffer_is_rejected_before_acquisition() {
        let mut record = [0; BUFFER_BYTES];
        put(&mut record, 4, META_OUTPUT);
        put(&mut record, 48, 1);
        let buffer = BufferState::from_record(record).unwrap();
        let mut buffers = [buffer];
        assert_eq!(
            Queue::default().get_buffer(&mut Driver, &mut buffers, Some(1)),
            Err(-6)
        );
        assert_eq!(buffers, [buffer]);
    }
}

// Persistent statistics ownership around first-frame startup. No AE decisions.
mod statistics_session {
    use super::*;
    use std::sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    };
    struct Session {
        file: Option<File>,
        maps: Vec<Mapping>,
        allocated: bool,
        streaming: bool,
        frames: u64,
        last: Option<Vec<u8>>,
        history: Vec<Value>,
        cleanup: Vec<String>,
    }
    impl Session {
        fn prepare(node: &str) -> io::Result<Self> {
            if std::mem::size_of::<usize>() != 4 {
                return Err(error("Statistics session requires ARM32 Linux"));
            }
            if !vendor_processes().is_empty() {
                return Err(error("Vendor camera process running"));
            }
            let file = open(node, true)?;
            let (_, caps) = capability(&file)?;
            if caps & 0x04800000 != 0x04800000 {
                return Err(error("Statistics node requires streaming metadata capture"));
            }
            let fmt = format(&file, META_CAPTURE)?;
            let raw = unsafe { &fmt.data.raw };
            if get32(raw, 0) != u32::from_le_bytes(*b"RK1S")
                || get32(raw, 4) != shieldsigner_rkaiq::statistics::BUFFER_BYTES as u32
            {
                return Err(error("Unsupported full ISP32 statistics layout"));
            }
            let mut session = Self {
                file: Some(file),
                maps: vec![],
                allocated: false,
                streaming: false,
                frames: 0,
                last: None,
                history: vec![],
                cleanup: vec![],
            };
            let fd = session.fd();
            let mut request = RequestBuffers {
                count: 2,
                kind: META_CAPTURE,
                memory: MMAP,
                capabilities: 0,
                reserved: 0,
            };
            ioctl(fd, REQBUFS, &mut request)?;
            session.allocated = true;
            if !(2..=8).contains(&request.count) {
                return Err(error("Statistics driver returned invalid buffer count"));
            }
            for index in 0..request.count {
                let mut planes = [zero(); PLANES];
                let mut b = buffer(index, META_CAPTURE, &mut planes);
                ioctl(fd, QUERYBUF, &mut b)?;
                if b.kind != META_CAPTURE
                    || b.memory != MMAP
                    || b.index != index
                    || b.length < shieldsigner_rkaiq::statistics::BUFFER_BYTES as u32
                    || b.length > 65536
                {
                    return Err(error("Invalid statistics buffer descriptor"));
                }
                session
                    .maps
                    .push(Mapping::new(fd, b.length as usize, unsafe {
                        b.data.offset
                    })?);
                ioctl(fd, QUEUE, &mut b)?;
            }
            let mut kind = META_CAPTURE;
            ioctl(fd, STREAMON, &mut kind)?;
            session.streaming = true;
            Ok(session)
        }
        fn fd(&self) -> RawFd {
            self.file.as_ref().unwrap().as_raw_fd()
        }
        fn receive(
            &mut self,
            stop: &AtomicBool,
            parameters: &[u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
        ) -> io::Result<()> {
            let mut progress = Instant::now();
            while !stop.load(Ordering::Acquire) {
                let mut planes = [zero(); PLANES];
                let mut b = buffer(0, META_CAPTURE, &mut planes);
                match ioctl(self.fd(), DEQUEUE, &mut b) {
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => {
                        if progress.elapsed() > Duration::from_secs(10) {
                            return Err(error("No statistics frames for 10 seconds"));
                        }
                        std::thread::sleep(Duration::from_millis(1));
                        continue;
                    }
                    Err(e) => return Err(e),
                    Ok(()) => (),
                }
                let mapping = self
                    .maps
                    .get(b.index as usize)
                    .ok_or_else(|| error("Statistics index out of range"))?;
                if b.flags & 0x40 != 0
                    || b.kind != META_CAPTURE
                    || b.memory != MMAP
                    || !matches!(b.used, 13036 | 13040)
                    || b.used as usize > mapping.length
                    || b.length < b.used
                    || b.length as usize > mapping.length
                {
                    return Err(error("Invalid/corrupted statistics completion"));
                }
                let bytes = unsafe {
                    std::slice::from_raw_parts(mapping.address.cast::<u8>(), b.used as usize)
                }
                .to_vec();
                let stats = shieldsigner_rkaiq::statistics::Statistics::parse(&bytes)
                    .map_err(|_| error("Invalid statistics payload"))?;
                let translated = match shieldsigner_rkaiq::ae_translation::measure_linear(
                    &bytes, parameters,
                ) {
                    Ok(Some(m)) => {
                        json!({"valid":true,"weightedMeanQ8":m.mean,"weightedMeanLuma":m.mean as f32/256.,"correctedHistogramCount":m.histogram.iter().map(|v|*v as u64).sum::<u64>(),"initialSnapshotAssociationVerified":false})
                    }
                    Ok(None) => {
                        json!({"valid":false,"reason":"AE1 and histogram1 validity bits are both required"})
                    }
                    Err(e) => json!({"valid":false,"error":format!("{e:?}")}),
                };
                let header = json!({"frameId":stats.frame_id(),"parametersId":stats.parameters_id(),"measurements":stats.measurements(),"bufferSequence":b.sequence,"aeLinear":translated});
                if self.history.len() == 256 {
                    self.history.remove(0);
                }
                self.history.push(header);
                self.last = Some(bytes);
                self.frames += 1;
                progress = Instant::now();
                ioctl(self.fd(), QUEUE, &mut b)?;
            }
            Ok(())
        }
        fn release(&mut self) {
            if self.streaming {
                let mut kind = META_CAPTURE;
                if let Err(e) = ioctl(self.fd(), STREAMOFF, &mut kind) {
                    self.cleanup.push(e.to_string());
                    self.file.take();
                }
                self.streaming = false;
            }
            self.maps.clear();
            if self.allocated && self.file.is_some() {
                let mut request = RequestBuffers {
                    count: 0,
                    kind: META_CAPTURE,
                    memory: MMAP,
                    capabilities: 0,
                    reserved: 0,
                };
                if let Err(e) = ioctl(self.fd(), REQBUFS, &mut request) {
                    self.cleanup.push(e.to_string());
                }
            }
            self.allocated = false;
        }
        fn save(&self, out: &str, initial_target: f32) -> io::Result<()> {
            let bytes = self
                .last
                .as_ref()
                .ok_or_else(|| error("Capture completed without any statistics frames"))?;
            let mut raw = OpenOptions::new().write(true).create_new(true).open(out)?;
            raw.write_all(bytes)?;
            let report = json!({"kind":"persistent-isp32-statistics-session","initialTargetLuma":initial_target,"framesReceived":self.frames,"lastFrame":self.history.last(),"recentFrames":self.history,"recentFrameLimit":256,"automaticExposure":false,"frameExposureAssociationVerified":false,"cleanupErrors":self.cleanup});
            let mut sidecar = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(format!("{out}.json"))?;
            serde_json::to_writer_pretty(&mut sidecar, &report)
                .map_err(|e| error(e.to_string()))?;
            Ok(())
        }
    }
    impl Drop for Session {
        fn drop(&mut self) {
            self.release();
        }
    }
    pub fn during<F: FnOnce() -> io::Result<()>>(
        node: &str,
        out: &str,
        parameters: &[u8; shieldsigner_rkaiq::isp32::PARAMETER_BYTES],
        initial_target: f32,
        work: F,
    ) -> io::Result<()> {
        let snapshot = *parameters;
        for path in [out, &format!("{out}.json")] {
            if std::path::Path::new(path).exists() {
                return Err(error("Statistics output already exists"));
            }
        }
        let stop = Arc::new(AtomicBool::new(false));
        let flag = stop.clone();
        let (ready_tx, ready_rx) = std::sync::mpsc::sync_channel(1);
        std::thread::scope(|scope| {
            let worker=scope.spawn(move || ->io::Result<()>{
                let mut session=match Session::prepare(node){Ok(s)=>s,Err(e)=>{let _=ready_tx.send(Err(e.to_string()));return Err(e);}};
                println!("{}",json!({"event":"statistics-ready","device":node,"automaticExposure":false}));
                let _=ready_tx.send(Ok(()));
                let result=session.receive(&flag,&snapshot);session.release();
                let saved=if session.last.is_some(){session.save(out,initial_target)}else{Err(error("No statistics frames captured"))};
                println!("{}",json!({"event":"statistics-finished","framesReceived":session.frames,"error":result.as_ref().err().map(|e|e.to_string()),"saveError":saved.as_ref().err().map(|e|e.to_string()),"cleanupErrors":session.cleanup,"automaticExposure":false}));
                result.and(saved).and_then(|_|if session.cleanup.is_empty(){Ok(())}else{Err(error("Statistics cleanup failed"))})
            });
            let outcome = match ready_rx.recv() {
                Ok(Ok(())) => work(),
                Ok(Err(e)) => Err(error(e)),
                Err(_) => Err(error("Statistics worker failed before readiness")),
            };
            stop.store(true, Ordering::Release);
            let metadata = worker
                .join()
                .map_err(|_| error("Statistics worker panicked"))?;
            outcome.and(metadata)
        })
    }
}

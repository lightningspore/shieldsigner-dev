//! Bounded private AWB attempt tracing, shared by the device owner and host regression.
use std::{fs::{self, OpenOptions}, io::{self, Write}};
use serde_json::json;

/// Bounded private input trace, independent of successful AWB state updates.
pub(crate) fn write_awb_trace_attempt(
    directory: &std::path::Path,
    attempts: &mut usize,
    blocks: [(&str, &[u8]); 3],
    mut metadata: serde_json::Value,
) -> io::Result<bool> {
    if *attempts >= 32 {
        return Ok(false);
    }
    fs::create_dir_all(directory)?;
    let index = *attempts;
    for (suffix, data) in blocks {
        let path = directory.join(format!("frame-{index:03}.{suffix}"));
        OpenOptions::new().write(true).create_new(true).open(path)?.write_all(data)?;
    }
    metadata["index"] = json!(index);
    let file = OpenOptions::new().write(true).create_new(true)
        .open(directory.join(format!("frame-{index:03}.json")))?;
    serde_json::to_writer_pretty(file, &metadata).map_err(io::Error::other)?;
    // Increment before Session::process: rejected statistics do not advance
    // its successful-frame counter, but must never reuse this filename.
    *attempts += 1;
    Ok(true)
}

#[cfg(test)]
mod awb_trace_tests {
    use super::*;

    #[test]
    fn rejected_session_retry_keeps_unique_trace_names_and_attempt_budget() {
        struct PrivateDirectory(std::path::PathBuf);
        impl Drop for PrivateDirectory {
            fn drop(&mut self) {
                let _ = fs::remove_dir_all(&self.0);
            }
        }
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos();
        let directory = PrivateDirectory(std::env::temp_dir()
            .join(format!("shieldsigner-awb-trace-{}-{unique}", std::process::id())));
        let mut attempts = 0;
        for index in 0..40 {
            // A rejected Session update leaves processedBeforeCapture at zero
            // for the retry. Input tracing must not reuse frame-000 anyway.
            let written = write_awb_trace_attempt(&directory.0, &mut attempts,
                [("stats.raw", &[1, 2]), ("sdk.bin", &[3, 4]), ("translated.bin", &[5, 6])],
                json!({"processedBeforeCapture":0,"requestedUpdate":true})).unwrap();
            assert_eq!(written, index < 32);
        }
        assert_eq!(attempts, 32);
        assert_eq!(fs::read_dir(&directory.0).unwrap().count(), 32 * 4);
        for index in [0, 1, 31] {
            let metadata: serde_json::Value = serde_json::from_slice(
                &fs::read(directory.0.join(format!("frame-{index:03}.json"))).unwrap()).unwrap();
            assert_eq!(metadata["index"], json!(index));
            assert_eq!(metadata["processedBeforeCapture"], json!(0));
        }
        assert!(!directory.0.join("frame-032.json").exists());
    }
}

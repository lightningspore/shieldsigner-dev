//! Ordinary SensorHw::setExposureParams queued snapshot assembly (ELF 0x3c474).
//! Initial immediate writes, custom I2C, DPCC and ownership/pool failures remain
//! separate. No descriptor timing values are invented for cached snapshots.
use crate::{ae_publication::Record, sensor_scheduler::Scheduler, InvalidInput};

/// The native queued snapshot starts as the complete main exposure. Only its
/// first 192 bytes, frame-length word and byte 240 come from each queue entry.
pub fn assemble(main: &Record, selected: &Record) -> Record {
    let mut result = *main;
    result[..192].copy_from_slice(&selected[..192]);
    result[232..236].copy_from_slice(&selected[232..236]);
    result[240] = selected[240];
    result
}
/// Submit an ordinary AE queue. Selected records are borrowed, so the caller
/// retains ownership of its publication count. Native pending batches
/// are pruned by their first-entry markers, not merely appended indefinitely.
pub fn submit(
    scheduler: &mut Scheduler<Record>,
    main: &Record,
    selected: &[Record],
) -> Result<(), InvalidInput> {
    if selected.len() > 6 {
        return Err(InvalidInput::Length);
    }
    let mut records = [[0; 244]; 6];
    for (out, entry) in records.iter_mut().zip(selected) {
        *out = assemble(main, entry);
    }
    scheduler.enqueue_batch(&records[..selected.len()])
}

/// Register fields consumed by the ordinary native linear sensor writer.
pub fn linear_controls(record: &Record) -> crate::sensor::LinearExposure {
    let word = |o| u32::from_le_bytes(record[o..o + 4].try_into().unwrap());
    crate::sensor::LinearExposure {
        frame_length_lines: word(232),
        dcg_mode: word(20) as i32,
        analogue_gain_code: word(36),
        digital_gain_code: word(40),
        coarse_integration_time: word(32),
    }
}

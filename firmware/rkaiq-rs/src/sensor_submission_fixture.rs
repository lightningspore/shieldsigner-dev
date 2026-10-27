use serde_json::{json, Value};
use shieldsigner_rkaiq::*;
fn decode(s: &str) -> ae_publication::Record {
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
        .collect::<Vec<_>>()
        .try_into()
        .unwrap()
}
pub fn run(v: &Value) -> String {
    let mut scheduler = sensor_scheduler::Scheduler::new(
        [0; 244],
        sensor_timing::Delays {
            time: 2,
            gain: 2,
            dcg: 0,
            split_gain: false,
            split_dcg: false,
            dcg_with_time: false,
        },
        sensor_scheduler::EffectPolicy {
            shorten_enabled: false,
            designated_frame: 0,
            shorten_all: false,
        },
    )
    .unwrap();
    let mut out = Vec::new();
    for step in v.as_array().unwrap() {
        let main = decode(step["main"].as_str().unwrap());
        let records = step["selected"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| decode(r.as_str().unwrap()))
            .collect::<Vec<_>>();
        sensor_submission::submit(&mut scheduler, &main, &records).unwrap();
        let pending = scheduler
            .pending()
            .map(|e| json!({"first":e.first,"record":hex(&e.exposure)}))
            .collect::<Vec<_>>();
        let mut sofs = Vec::new();
        for frame in step["sofs"].as_array().unwrap() {
            let mut written = None;
            let mut trace = None;
            let result = scheduler.on_sof(frame.as_u64().unwrap() as u32, |record| {
                written = Some(hex(&record));
                let mut backend = Backend {
                    trace: vec!["descriptor".into()],
                    operations: 0,
                    fail: step["fail"].as_u64().unwrap() as usize,
                };
                let status = if sensor::program_linear(
                    &mut backend,
                    sensor_submission::linear_controls(&record),
                    &mut None,
                )
                .is_ok()
                {
                    0
                } else {
                    -9
                };
                trace = Some(format!("{}|{status}|-", backend.trace.join(";")));
                status
            });
            sofs.push(json!({"status":result.status,"trace":trace,"pending":scheduler.pending().map(|e|json!({"first":e.first,"record":hex(&e.exposure)})).collect::<Vec<_>>(),"current":hex(&scheduler.current),"written":written,"effective":scheduler.effective().map(|e|json!({"frame":e.frame,"record":hex(&e.exposure)})).collect::<Vec<_>>()}));
        }
        out.push(json!({"pending":pending,"sofs":sofs}));
    }
    serde_json::to_string(&out).unwrap()
}

fn hex(record: &ae_publication::Record) -> String {
    record.iter().map(|b| format!("{b:02x}")).collect()
}

struct Backend {
    trace: Vec<String>,
    operations: usize,
    fail: usize,
}
impl Backend {
    fn result(&mut self) -> Result<(), ()> {
        self.operations += 1;
        if self.operations == self.fail {
            Err(())
        } else {
            Ok(())
        }
    }
}
impl sensor::Backend for Backend {
    type Error = ();
    fn descriptor(&mut self) -> Result<sensor::Descriptor, ()> {
        Ok(sensor::Descriptor {
            line_periods_per_field: 1360,
            output_height: 1296,
        })
    }
    fn control(&mut self, id: u32, value: i32) -> Result<(), ()> {
        self.trace.push(format!("control:{id:08x}:{value}"));
        self.result()
    }
    fn conversion_gain(&mut self, value: u32) -> Result<(), ()> {
        self.trace.push(format!("dcg:{value}"));
        self.result()
    }
}

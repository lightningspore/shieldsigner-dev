//! Continuous runtime tracing is opt-in; finite diagnostics preserve full records.
//! This changes observability only; callers perform and commit ISP work first.
pub fn select<T>(full: bool, diagnostic: impl FnOnce() -> T, summary: impl FnOnce() -> T) -> T {
    if full { diagnostic() } else { summary() }
}
pub fn full_enabled() -> bool {
    std::env::var_os("SHIELDSIGNER_CAMERA_LOG_FULL").is_some_and(|value| value == "1")
}

static SUPPRESSED:std::sync::atomic::AtomicUsize=std::sync::atomic::AtomicUsize::new(0);
pub fn enabled(continuous:bool, full:bool)->bool { !continuous || full }
/// The record closure includes formatting and the actual write, so normal
/// continuous capture neither builds JSON nor waits on a diagnostic stdout pipe.
pub fn emit(continuous:bool,full:bool,record:impl FnOnce())->bool {
    if enabled(continuous,full) {record();true} else {SUPPRESSED.fetch_add(1,std::sync::atomic::Ordering::Relaxed);false}
}
pub fn suppressed_count()->usize {SUPPRESSED.load(std::sync::atomic::Ordering::Relaxed)}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn continuous_default_does_not_format_or_write_any_record() {
        assert!(!emit(true,false,||panic!("default continuous logging must never evaluate record closure")));
        let mut observed=Vec::new();
        assert!(emit(false,false,||observed.push("finite")));
        assert!(emit(true,true,||observed.push("explicit-full")));
        assert_eq!(observed,["finite","explicit-full"]);
    }
    #[test]
    fn normal_mode_never_constructs_large_diagnostic_payload() {
        let record = select(false, || -> &str { panic!("diagnostic hex formatting must stay lazy") }, || "summary");
        assert_eq!(record, "summary");
    }
    #[test]
    fn explicit_full_mode_preserves_original_record() {
        let original = serde_json::json!({"event":"automatic-lsc-processed","result":"000102ff","frame":7});
        let record = select(true, || original.clone(), || panic!("full mode must not substitute summary"));
        assert_eq!(record, original);
    }
}

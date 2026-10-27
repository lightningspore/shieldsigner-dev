//! Sector-gradient calculation in native AlscManualGrad (ELF 0x119018).
use crate::InvalidInput;
/// Convert sixteen positive sector lengths on each axis to the native u16
/// inverse gradients. Resolution/sector selection is a separate operation.
/// Native computes 32768/length + 0.5 in f64 before truncating, not f32.
pub fn gradients(x: &[u16; 16], y: &[u16; 16]) -> Result<([u16; 16], [u16; 16]), InvalidInput> {
    if x.iter().chain(y.iter()).any(|v| *v == 0) {
        return Err(InvalidInput::DegenerateRange);
    }
    let convert =
        |axis: &[u16; 16]| core::array::from_fn(|i| (32768f64 / f64::from(axis[i]) + 0.5) as u16);
    Ok((convert(x), convert(y)))
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn zero_length_is_rejected_on_either_axis() {
        let good = [1; 16];
        let mut bad = good;
        bad[15] = 0;
        assert!(gradients(&bad, &good).is_err());
        assert!(gradients(&good, &bad).is_err());
    }
}

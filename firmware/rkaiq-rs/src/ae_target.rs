//! Dynamic linear AE setpoint branch of AecPreProcess (ELF 0xb33d0).
use crate::InvalidInput;
/// The original uses this operation order rather than the shared interpolation
/// helper. An empty curve returns native default zero before bias/clamping.
pub fn select(
    levels: &[f32],
    points: &[f32],
    exposure: f32,
    bias_percent: f32,
) -> Result<f32, InvalidInput> {
    if levels.len() != points.len() {
        return Err(InvalidInput::Length);
    }
    if !exposure.is_finite()
        || !bias_percent.is_finite()
        || levels.iter().chain(points).any(|v| !v.is_finite())
    {
        return Err(InvalidInput::NonFinite);
    }
    if levels.windows(2).any(|v| v[0] >= v[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    if levels.is_empty() {
        return Ok(0.);
    }
    let mut target = 0.;
    for i in 0..levels.len() - 1 {
        if levels[i] <= exposure && exposure <= levels[i + 1] {
            target = ((points[i] - points[i + 1]) * (levels[i + 1] - exposure))
                / (levels[i + 1] - levels[i])
                + points[i + 1];
            break;
        }
    }
    if exposure < levels[0] {
        target = points[0];
    }
    if exposure > levels[levels.len() - 1] {
        target = points[points.len() - 1];
    }
    let factor = bias_percent.abs() / 100. + 1.;
    target = if bias_percent < 0. {
        target / factor
    } else {
        target * factor
    };
    Ok(target.clamp(1., 255.))
}
#[cfg(feature = "diagnostics")]
pub fn initial_from_scene(scene: &serde_json::Value) -> Result<f32, alloc::string::String> {
    extern crate alloc;
    use alloc::{string::String, vec::Vec};
    let control = &scene["ae_calib"]["LinearAeCtrl"];
    let curve = &control["DySetpoint"];
    let array = |name: &str| -> Result<Vec<f32>, String> {
        let values = curve[name]
            .as_array()
            .ok_or("Missing dynamic AE target array")?;
        let count = curve[alloc::format!("{name}_len")]
            .as_u64()
            .ok_or("Missing dynamic AE target length")? as usize;
        if values.len() != count || count > 64 {
            return Err("Invalid dynamic AE target array length".into());
        }
        values
            .iter()
            .map(|v| {
                v.as_f64()
                    .map(|v| v as f32)
                    .ok_or("Invalid dynamic AE target value".into())
            })
            .collect()
    };
    let init = &control["InitExp"];
    let number = |v: &serde_json::Value| {
        v.as_f64()
            .map(|v| v as f32)
            .ok_or_else(|| String::from("Missing AE numeric value"))
    };
    let time = number(&init["InitTimeValue"])?;
    let gain = number(&init["InitGainValue"])?;
    let isp = number(&init["InitIspDGainValue"])?;
    if time <= 0. || gain <= 0. || isp <= 0. {
        return Err("Initial AE exposure must be positive".into());
    }
    select(
        &array("ExpLevel")?,
        &array("DySetpoint")?,
        gain * time * isp,
        number(&control["Evbias"])?,
    )
    .map_err(|_| "AE target inputs outside checked domain".into())
}
#[cfg(feature = "diagnostics")]
extern crate alloc;
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn empty_and_single_point_follow_native_branch_rules() {
        assert_eq!(select(&[], &[], 1., 50.), Ok(0.));
        assert_eq!(select(&[1.], &[45.], 1., 0.), Ok(1.));
        assert_eq!(select(&[1.], &[45.], 0., 0.), Ok(45.));
        assert!(select(&[1., 1.], &[2., 3.], 1., 0.).is_err());
    }
}

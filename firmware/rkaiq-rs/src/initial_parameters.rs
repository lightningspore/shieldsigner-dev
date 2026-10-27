//! Experimental linear first-frame profile assembly, not an automatic 3A engine.
use crate::{demosaic_selection::Calibration, isp32::*, isp_black_level, isp_color, isp_demosaic};
extern crate alloc;
use alloc::{format, string::String, vec::Vec};
use serde_json::{json, Value};
fn number(v: &Value) -> Result<f32, String> {
    let f = v.as_f64().ok_or("missing numeric calibration value")? as f32;
    if !f.is_finite() {
        return Err("nonfinite calibration value".into());
    }
    Ok(f)
}
fn byte(v: &Value) -> Result<u8, String> {
    u8::try_from(v.as_u64().ok_or("missing unsigned calibration value")?)
        .map_err(|_| "byte out of range".into())
}
fn flag(v: &Value) -> Result<bool, String> {
    match byte(v)? {
        0 => Ok(false),
        1 => Ok(true),
        _ => Err("invalid enable flag".into()),
    }
}
// This checkpoint supports the pinned SC3336 profile's constant BLC tables.
// Reject changing tables until their selection path is independently integrated.
fn constant(v: &Value) -> Result<f32, String> {
    let a = v.as_array().ok_or("missing BLC table")?;
    if a.len() != 13 {
        return Err("BLC table requires 13 entries".into());
    }
    let first = number(&a[0])?;
    if a.iter().any(|v| number(v).ok() != Some(first)) {
        return Err("nonconstant BLC table not supported by startup checkpoint".into());
    }
    Ok(first)
}
pub fn assemble(iq: &Value) -> Result<([u8; PARAMETER_BYTES], Value), String> {
    let scene = iq
        .pointer("/main_scene/0/sub_scene/0/scene_isp32")
        .ok_or("missing explicit scene 0/0")?;
    let exp = &scene["ae_calib"]["LinearAeCtrl"]["InitExp"];
    let seconds = number(&exp["InitTimeValue"])?;
    let gain = number(&exp["InitGainValue"])?;
    let isp_gain = number(&exp["InitIspDGainValue"])?;
    if seconds <= 0. || gain <= 0. || isp_gain != 1. {
        return Err("startup requires positive exposure/gain and unity ISP digital gain".into());
    }
    let iso = (gain * isp_gain * 50.) as i32;
    let mut params = [0u8; PARAMETER_BYTES];
    // Explicitly disable other ordinary modules plus VSM; CSM/CGC add their bits.
    params[..8].copy_from_slice(&((1u64 << 43) - 1 | 1u64 << 45).to_le_bytes());
    let blc = &scene["ablcV32_calib"];
    let channels = |stage: &str| -> Result<[i16; 4], String> {
        let mut out = [0; 4];
        for (i, name) in ["R_Channel", "Gr_Channel", "Gb_Channel", "B_Channel"]
            .iter()
            .enumerate()
        {
            let f = constant(&blc[stage]["BLC_Data"][name])?;
            if f.fract() != 0. || !(-32768.0..=32767.0).contains(&f) {
                return Err("BLC channel out of range".into());
            }
            out[i] = f as i16;
        }
        Ok(out)
    };
    let ob = &blc["BlcObPara"];
    let ob_enabled = flag(&ob["enable"])?;
    let offset = constant(&ob["BLC_OB_Data"]["isp_ob_Offset"])?;
    let predgain = constant(&ob["BLC_OB_Data"]["isp_ob_preDgain"])?;
    if !(0.0..=511.0).contains(&offset)
        || offset.fract() != 0.
        || !(0.0..=255.0).contains(&predgain)
    {
        return Err("optical black out of range".into());
    }
    let enabled = flag(&blc["Blc0TuningPara"]["enable"])?;
    let stage1_enabled = flag(&blc["Blc1TuningPara"]["enable"])?;
    isp_black_level::apply(
        &mut params,
        &mut [0; 44],
        isp_black_level::Configuration {
            enabled,
            fixed: if enabled {
                channels("Blc0TuningPara")?
            } else {
                [0; 4]
            },
            stage1_enabled,
            stage1: if stage1_enabled {
                channels("Blc1TuningPara")?
            } else {
                [0; 4]
            },
            optical_black_enabled: ob_enabled,
            optical_black_offset: if ob_enabled { offset as i16 } else { 0 },
            optical_black_predgain: if ob_enabled { predgain } else { 1. },
            optical_black_maximum: if ob_enabled {
                (predgain * 4096.) as i32 - offset as i32
            } else {
                1048575
            },
        },
    )
    .map_err(|e| format!("BLC: {e:?}"))?;
    let calibration = Calibration::from_value(&scene["debayer_v2"]["param"])?;
    let selected = calibration
        .select(iso)
        .map_err(|e| format!("demosaic: {e:?}"))?;
    let mut previous = [0; isp_demosaic::HARDWARE_BYTES];
    previous[0] = 1;
    let hardware =
        isp_demosaic::quantize(&mut previous, selected).map_err(|e| format!("demosaic: {e:?}"))?;
    isp_demosaic::apply(&mut params, &hardware);
    let wb = &scene["wb_v32"];
    let light = wb["autoExtPara"]["lightSourceForFirstFrame"]
        .as_str()
        .ok_or("missing first-frame light")?;
    let source = wb["autoPara"]["lightSources"]
        .as_array()
        .ok_or("missing WB lights")?
        .iter()
        .find(|v| v["name"].as_str() == Some(light))
        .ok_or("first-frame light not found")?;
    let gains = &source["standardGainValue"];
    if gains.as_array().map(Vec::len) != Some(4) {
        return Err("WB gains require four channels".into());
    }
    let g = [
        number(&gains[0])?,
        number(&gains[1])?,
        number(&gains[2])?,
        number(&gains[3])?,
    ];
    if g.iter().copied().fold(f32::INFINITY, f32::min) != 1. {
        return Err("startup WB seed requires normalized unity minimum".into());
    }
    apply_awb_gain(
        &mut params,
        &mut [0; 32],
        WhiteBalanceGain {
            red: g[0],
            green_red: g[1],
            green_blue: g[2],
            blue: g[3],
            position: ApplyPosition::Gain0,
        },
        true,
    )
    .map_err(|e| format!("WB: {e:?}"))?;
    let gamma = &scene["agamma_calib_v11"]["GammaTuningPara"];
    let curve = gamma["Gamma_curve"]
        .as_array()
        .ok_or("missing gamma curve")?;
    if curve.len() != 49 {
        return Err("gamma requires 49 points".into());
    }
    let mut points = [0u16; 49];
    for (out, v) in points.iter_mut().zip(curve) {
        *out = v.as_u64().ok_or("invalid gamma point")?.min(4095) as u16;
    }
    let offset = u16::try_from(
        gamma["Gamma_out_offset"]
            .as_u64()
            .ok_or("missing gamma offset")?,
    )
    .map_err(|_| "gamma offset out of range")?;
    isp_color::gamma(
        &mut params,
        flag(&gamma["Gamma_en"])?,
        0,
        true,
        offset,
        &points,
    );
    let csm = &scene["csm"]["TuningPara"];
    for name in ["csm", "cgc"] {
        match scene[name]["TuningPara"]["op_mode"].as_str() {
            Some("RK_AIQ_OP_MODE_AUTO") | Some("RK_AIQ_OP_MODE_MANUAL") => (),
            _ => return Err("unsupported CSM/CGC operation mode".into()),
        }
    }
    if csm["coeff"].as_array().map(Vec::len) != Some(9) {
        return Err("CSM requires nine coefficients".into());
    }
    let mut coefficients = [0.; 9];
    for (i, out) in coefficients.iter_mut().enumerate() {
        *out = number(&csm["coeff"][i])?;
    }
    isp_color::csm(
        &mut params,
        1,
        byte(&csm["full_range"])?,
        byte(&csm["y_offset"])?,
        byte(&csm["c_offset"])?,
        &coefficients,
    )
    .map_err(|e| format!("CSM: {e:?}"))?;
    let cgc = &scene["cgc"]["TuningPara"];
    isp_color::cgc(
        &mut params,
        1,
        byte(&cgc["cgc_ratio_en"])?,
        byte(&cgc["cgc_yuv_limit"])?,
    );
    Ok((
        params,
        json!({"kind":"experimental-linear-first-frame-parameters","scene":"/main_scene/0/sub_scene/0/scene_isp32","bytes":PARAMETER_BYTES,"iso":iso,"requestedExposureSeconds":seconds,"requestedGain":gain,"sensorExposureApplied":false,"whiteBalanceLight":light,"whiteBalanceSeed":g,"limitations":["Fixed first-frame checkpoint; no automatic exposure/white balance controller.","Constant BLC tables only; selected CSM/CGC profile values are explicit inputs, not recovered automatic selection.","No hardware qualification or usable-frame claim; other ISP modules explicitly disabled."]}),
    ))
}

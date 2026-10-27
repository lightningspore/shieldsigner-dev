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
fn startup_black_level(scene: &Value) -> Result<isp_black_level::Configuration, String> {
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
    Ok(isp_black_level::Configuration {
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
    })
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
    isp_black_level::apply(&mut params, &mut [0; 44], startup_black_level(scene)?)
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
    let dpcc = crate::dpcc_calibration::Automatic::from_value(&scene["adpcc_calib"]["DpccTuningPara"])?;
    let mut dpcc_result = [0; crate::isp_dpcc::RESULT_BYTES];
    dpcc.process(iso, &mut dpcc_result).map_err(|e| format!("DPCC: {e:?}"))?;
    crate::isp_dpcc::apply(&mut params, &dpcc_result);

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
            position: crate::isp32::awb_prepare_position(0),
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
        json!({"kind":"experimental-linear-first-frame-parameters","scene":"/main_scene/0/sub_scene/0/scene_isp32","bytes":PARAMETER_BYTES,"iso":iso,"requestedExposureSeconds":seconds,"requestedGain":gain,"sensorExposureApplied":false,"whiteBalanceLight":light,"whiteBalanceSeed":g,"whiteBalanceApplyPosition":"Gain1","limitations":["Fixed first-frame checkpoint; no automatic exposure/white balance controller.","Constant BLC tables only; selected CSM/CGC profile values are explicit inputs, not recovered automatic selection.","No hardware qualification or usable-frame claim; other ISP modules explicitly disabled."]}),
    ))
}

/// Experimental measurement-enabled initial record. Configures AE/histogram
/// collection only; no statistics queue, exposure decision or sensor update.
pub fn assemble_with_ae(iq: &Value) -> Result<([u8; PARAMETER_BYTES], Value), String> {
    use crate::isp_ae_measurement::*;
    let (mut params, mut report) = assemble(iq)?;
    let dimension = |name: &str| -> Result<u32, String> {
        u32::try_from(
            iq["sensor_calib"]["resolution"][name]
                .as_u64()
                .ok_or("Missing sensor dimensions for AE geometry")?,
        )
        .map_err(|_| "Invalid AE dimensions".into())
    };
    let comm = iq
        .pointer("/main_scene/0/sub_scene/0/scene_isp32/ae_calib/CommCtrl")
        .ok_or("Missing AE common calibration")?;
    let (selected, policy) =
        crate::ae_configuration::from_comm(comm, dimension("width")?, dimension("height")?)?;
    let ae = AeMeasurement::from_record(selected[..104].try_into().unwrap())
        .map_err(|e| format!("AE record: {e:?}"))?;
    let hist = HistogramMeasurement::from_record(selected[104..].try_into().unwrap())
        .map_err(|e| format!("Histogram record: {e:?}"))?;
    apply_ae(&mut params, &mut [0; AE_BYTES], &ae);
    apply_histogram(&mut params, &mut [0; HISTOGRAM_BYTES], &hist);
    report["initialTargetLuma"] = json!(crate::ae_target::initial_from_scene(
        iq.pointer("/main_scene/0/sub_scene/0/scene_isp32").unwrap()
    )?);
    // The pinned SC3336 profile explicitly requests fixed 50 Hz. This is a
    // route quantum, not a derived minimum shutter time or flicker detector.
    let flicker = &comm["AecAntiFlicker"];
    if flicker["enable"].as_u64() == Some(1)
        && flicker["Frequency"].as_str() == Some("AECV2_FLICKER_FREQUENCY_50HZ")
    {
        let state = crate::ae_flicker::select(
            crate::ae_flicker::State {
                quantum: 0.,
                alternate: 0.,
                frequency_selector: 0,
            },
            true,
            1,
            0.,
            None,
        )
        .map_err(|_| "Invalid fixed flicker timing")?;
        report["routeTimeQuantumSeconds"] = json!(state.quantum);
        report["minimumShutterTimeDerived"] = json!(false);
    }
    report["aeMeasurementsConfigured"] = json!(true);
    report["automaticExposure"] = json!(false);
    report["aeGeometry"] = json!({"width":dimension("width")?,"height":dimension("height")?,"source":"sensor_calib.resolution","requiresMatchingActiveIspGeometry":true});
    report["aePolicy"] = json!({"histogramMode":policy.histogram_mode,"rawMode":policy.raw_mode,"yRange":policy.y_range,"channelMask":policy.channel_mask});
    report["limitations"][2]=json!("Measurement configuration only; active ISP dimensions must match the profile. No live feedback or image-quality qualification; unselected modules remain disabled.");
    Ok((params, report))
}

/// Offline candidate with AWB measurement collection; fixed calibrated WB is
/// unchanged. Caller must explicitly opt into submitting this experimental record.
pub fn assemble_with_awb(
    iq: &Value,
    sample_scale: u32,
) -> Result<
    (
        [u8; PARAMETER_BYTES],
        Value,
        [u8; crate::isp_awb_measurement::INPUT_BYTES],
    ),
    String,
> {
    let (mut params, mut report) = assemble_with_ae(iq)?;
    let scene = iq
        .pointer("/main_scene/0/sub_scene/0/scene_isp32")
        .ok_or("Missing selected scene")?;
    let dimensions = ["width", "height"].map(|k| {
        iq["sensor_calib"]["resolution"][k]
            .as_u64()
            .and_then(|v| u32::try_from(v).ok())
    });
    let dimensions = [
        dimensions[0].ok_or("Invalid sensor width")?,
        dimensions[1].ok_or("Invalid sensor height")?,
    ];
    let (measurement, setup) = crate::awb_calibration::assemble_measurement_startup(
        &scene["wb_v32"],
        dimensions,
        sample_scale,
        startup_black_level(scene)?,
        report["iso"].as_i64().ok_or("Missing startup ISO")? as f32,
        1.,
    )?;
    crate::isp_awb_measurement::Measurement(measurement).apply(&mut params, true);
    report["awbMeasurementsConfigured"] = json!(true);
    report["automaticWhiteBalance"] = json!(false);
    report["awbMeasurementSetup"] = setup;
    Ok((params, report, measurement))
}

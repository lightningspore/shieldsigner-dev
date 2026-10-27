//! Explicit expert-table construction from CalibDbV2_Dpcc_s JSON fields.
//! Field ordering follows the pinned SDK and native expert initializer.
extern crate alloc;
use crate::dpcc_selection::{ROW_BYTES, TABLE_BYTES};
use alloc::{format, string::String};
use serde_json::Value;

fn byte(value: &Value, label: &str) -> Result<u8, String> {
    if let Some(b) = value.as_bool() {
        return Ok(b as u8);
    }
    value
        .as_u64()
        .filter(|v| *v <= 255)
        .map(|v| v as u8)
        .ok_or_else(|| format!("Expected u8 at {label}"))
}
fn flag(value: &Value, label: &str) -> Result<u8, String> {
    let b = byte(value, label)?;
    if b > 1 {
        return Err(format!("Expected boolean at {label}"));
    }
    Ok(b)
}
fn element(value: &Value, key: &str, index: usize) -> Result<u8, String> {
    let values = value[key]
        .as_array()
        .filter(|a| a.len() == 13)
        .ok_or_else(|| format!("Expected 13 entries at {key}"))?;
    byte(&values[index], key)
}

/// Input is the explicitly selected DpccTuningPara object. No scene fallback.
/// Native init leaves trailing row padding unchanged; fresh Rust tables use zero.
pub fn expert_table(value: &Value) -> Result<[u8; TABLE_BYTES], String> {
    if flag(&value["Fast_Mode"]["Fast_mode_en"], "Fast_mode_en")? != 0 {
        return Err("Expert table requires Fast_mode_en=0".into());
    }
    let enabled = flag(&value["Enable"], "Enable")?;
    let expert = &value["Expert_Mode"];
    let sets = &expert["SetEnable"];
    let knots = sets["ISO"]
        .as_array()
        .filter(|v| v.len() == 13)
        .ok_or("Expected 13 ISO knots")?;
    let mut result = [0; TABLE_BYTES];
    let mut previous = None;
    for index in 0..13 {
        let iso = knots[index]
            .as_i64()
            .and_then(|v| i32::try_from(v).ok())
            .ok_or("Invalid ISO knot")?;
        if previous.is_some_and(|p| p >= iso) {
            return Err("Non-increasing DPCC ISO grid".into());
        }
        previous = Some(iso);
        let row = &mut result[index * ROW_BYTES..(index + 1) * ROW_BYTES];
        row[..4].copy_from_slice(&iso.to_le_bytes());
        row[4] = flag(&expert["stage1_Enable"], "stage1_Enable")?;
        row[5] = flag(&expert["grayscale_mode"], "grayscale_mode")?;
        row[6] = enabled;
        row[7] = byte(&expert["rk_out_sel"], "rk_out_sel")?;
        for (offset, key) in [
            (8, "dpcc_out_sel"),
            (9, "stage1_rb_3x3"),
            (10, "stage1_g_3x3"),
            (11, "stage1_inc_rb_center"),
            (12, "stage1_inc_g_center"),
        ] {
            row[offset] = flag(&expert[key], key)?;
        }
        for (offset, key) in [(13, "fix_set"), (14, "set3"), (15, "set2"), (16, "set1")] {
            row[offset] = element(sets, key, index)?;
        }
        for group in 0..3 {
            let source = &expert[format!("set{}", group + 1)];
            for (channel, (method, key)) in [
                ("RK", "RK_enable"),
                ("RG", "RG_enable"),
                ("RND", "RND_enable"),
                ("RO", "RO_enable"),
                ("LC", "LC_enable"),
                ("PG", "PG_enable"),
            ]
            .iter()
            .enumerate()
            {
                let value = element(&source[*method], key, index)?;
                row[17 + group * 12 + channel] = value;
                row[17 + group * 12 + channel + 6] = value;
            }
            for (field, (method, key)) in [
                ("RK", "rb_sw_mindis"),
                ("RK", "g_sw_mindis"),
                ("LC", "rb_line_thr"),
                ("LC", "g_line_thr"),
                ("RK", "sw_dis_scale_min"),
                ("RK", "sw_dis_scale_max"),
                ("LC", "rb_line_mad_fac"),
                ("LC", "g_line_mad_fac"),
                ("PG", "rb_pg_fac"),
                ("PG", "g_pg_fac"),
                ("RND", "rb_rnd_thr"),
                ("RND", "g_rnd_thr"),
                ("RG", "rb_rg_fac"),
                ("RG", "g_rg_fac"),
            ]
            .iter()
            .enumerate()
            {
                row[53 + group * 14 + field] = element(&source[*method], key, index)?;
            }
            for (channel, color) in ["rb", "g"].iter().enumerate() {
                row[95 + (2 - group) * 2 + channel] =
                    element(&source["RO"], &format!("{color}_ro_lim"), index)?;
                row[101 + (2 - group) * 2 + channel] =
                    element(&source["RND"], &format!("{color}_rnd_offs"), index)?;
            }
        }
    }
    Ok(result)
}

fn signed(value: &Value, label: &str) -> Result<i32, String> {
    value
        .as_i64()
        .and_then(|v| i32::try_from(v).ok())
        .ok_or_else(|| format!("Expected i32 at {label}"))
}
fn point(value: &Value, key: &str, index: usize) -> Result<u8, String> {
    let a = value[key]
        .as_array()
        .filter(|a| a.len() == 16)
        .ok_or_else(|| format!("Expected 16 entries at {key}"))?;
    byte(&a[index], key)
}
/// Native dpcc_pdaf_params_init: normalize point enables, narrow i32 offsets
/// and counts to u16, retain x/y ordering, and zero fresh allocation padding.
pub fn pdaf_fields(value: &Value) -> Result<[u8; 62], String> {
    let mut out = [0; 62];
    out[0] = flag(&value["en"], "PDAF en")?;
    for i in 0..16 {
        out[1 + i] = (point(value, "point_en", i)? != 0) as u8;
        out[28 + i * 2] = point(value, "point_y", i)?;
        out[29 + i * 2] = point(value, "point_x", i)?;
    }
    for (offset, key) in [
        (18, "offsety"),
        (20, "offsetx"),
        (24, "wrapy_num"),
        (26, "wrapx_num"),
    ] {
        out[offset..offset + 2].copy_from_slice(&(signed(&value[key], key)? as u16).to_le_bytes());
    }
    out[22] = byte(&value["wrapy"], "wrapy")?;
    out[23] = byte(&value["wrapx"], "wrapx")?;
    out[60] = byte(&value["forward_med"], "forward_med")?;
    Ok(out)
}

/// Fresh automatic expert configuration with no PDAF or sensor-side auto DPCC.
/// Those are the explicit modes in the pinned SC3336 profile, not fallbacks.
pub struct Automatic {
    table: [u8; TABLE_BYTES],
    pdaf: [u8; 62],
}
impl Automatic {
    pub fn from_value(value: &Value) -> Result<Self, String> {
        if flag(
            &value["Sensor_dpcc"]["sensor_dpcc_auto_en"],
            "sensor_dpcc_auto_en",
        )? != 0
        {
            return Err("Sensor-side automatic DPCC is not supported".into());
        }
        if flag(&value["Dpcc_pdaf"]["en"], "PDAF en")? != 0 {
            return Err("Live SC3336 DPCC requires PDAF disabled".into());
        }
        Ok(Self {
            table: expert_table(value)?,
            pdaf: pdaf_fields(&value["Dpcc_pdaf"])?,
        })
    }
    /// Recovered automatic AdpccProcess output for the explicit linear ISO.
    /// Native fresh construction zeroes BPT; neither auto init nor this mode
    /// modifies that cache. Preserve result padding, just as native does.
    pub fn process(
        &self,
        iso: i32,
        result: &mut [u8; crate::isp_dpcc::RESULT_BYTES],
    ) -> Result<usize, crate::InvalidInput> {
        let mut next = *result;
        let row = crate::dpcc_selection::select(&self.table, iso, &mut next)?;
        next[104..128].fill(0);
        next[128..190].copy_from_slice(&self.pdaf);
        *result = next;
        Ok(row)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unsupported_modes_are_rejected_without_defaults() {
        assert!(Automatic::from_value(
            &serde_json::json!({"Sensor_dpcc":{"sensor_dpcc_auto_en":1}})
        )
        .is_err());
        assert!(Automatic::from_value(
            &serde_json::json!({"Sensor_dpcc":{"sensor_dpcc_auto_en":0},"Dpcc_pdaf":{"en":1}})
        )
        .is_err());
    }
}

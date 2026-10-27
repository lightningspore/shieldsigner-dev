//! PrepareMeasureResult and its native measurement-stability gate.
//! Private pointer-owned caches are explicit borrowed records in this API.
use crate::{
    awb_gain::{self, Gains},
    awb_probability::Curve,
    InvalidInput,
};
pub const FRAME_BYTES: usize = 0x1e00;
pub const LIGHT_BYTES: usize = 0xac;
pub const REGION_BYTES: usize = 0x34;

fn u32_at(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(bytes[offset..offset + 4].try_into().unwrap())
}
fn i64_at(bytes: &[u8], offset: usize) -> i64 {
    i64::from_le_bytes(bytes[offset..offset + 8].try_into().unwrap())
}
fn float_at(bytes: &[u8], offset: usize) -> f32 {
    f32::from_bits(u32_at(bytes, offset))
}
fn gains_at(bytes: &[u8], offset: usize) -> Gains {
    core::array::from_fn(|i| float_at(bytes, offset + i * 4))
}
fn put_word(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}
fn put_gains(bytes: &mut [u8], offset: usize, gain: Gains) {
    for (i, v) in gain.iter().enumerate() {
        put_word(bytes, offset + i * 4, v.to_bits());
    }
}
fn finite(values: &[f32]) -> Result<(), InvalidInput> {
    if values.iter().all(|v| v.is_finite()) {
        Ok(())
    } else {
        Err(InvalidInput::NonFinite)
    }
}

#[derive(Clone, Copy, Debug)]
pub struct ModeName(pub [u8; 64]);
impl ModeName {
    fn name(&self) -> Result<&[u8], InvalidInput> {
        let length = self
            .0
            .iter()
            .position(|b| *b == 0)
            .ok_or(InvalidInput::Length)?;
        Ok(&self.0[..length])
    }
    fn copy_from(&mut self, source: ModeName) -> Result<(), InvalidInput> {
        let n = source.name()?.len() + 1;
        self.0[..n].copy_from_slice(&source.0[..n]);
        Ok(())
    }
}
pub struct Frame<'a>(pub &'a [u8; FRAME_BYTES]);
impl Frame<'_> {
    fn weighted(&self, offset: usize) -> Result<(Gains, u32), InvalidInput> {
        let (gain, count) = awb_gain::statistics_gain(
            i64_at(self.0, offset),
            i64_at(self.0, offset + 8),
            i64_at(self.0, offset + 16),
        )?;
        Ok((gain, count as u32))
    }
    fn effect(&self) -> Effect {
        let at = 0x1d70;
        Effect {
            mode: u32_at(self.0, at) as i32,
            count: self.0[at + 4] as usize,
            group: u32_at(self.0, at + 8) as i32,
            indices: core::array::from_fn(|i| u32_at(self.0, at + 12 + i * 4) as i32),
            name: ModeName(self.0[at + 28..at + 92].try_into().unwrap()),
            pre_gain: gains_at(self.0, at + 92),
        }
    }
}
struct Effect {
    mode: i32,
    count: usize,
    group: i32,
    indices: [i32; 4],
    name: ModeName,
    pre_gain: Gains,
}
#[derive(Clone, Copy, Debug)]
pub struct LightRecord(pub [u8; LIGHT_BYTES]);
impl LightRecord {
    pub fn count(&self, region: usize) -> Option<u32> {
        (region < 3).then(|| u32_at(&self.0, region * REGION_BYTES))
    }
    pub fn gain(&self, region: usize) -> Option<Gains> {
        (region < 3).then(|| gains_at(&self.0, region * REGION_BYTES + 4))
    }
}
pub struct Settings<'a> {
    pub groups: usize,
    pub fast_light_count: u32,
    pub stability_threshold: f32,
    pub exclusion_kind: [i32; 4],
    pub exclusion_weight: [Curve<'a>; 4],
    pub prior_sample: f32,
}
pub struct State<'a> {
    pub update: bool,
    pub stability_mask: u8,
    pub history: [Gains; 4],
    pub mode_names: [ModeName; 4],
    pub seen: &'a mut [u8],
    pub active_lights: u8,
    pub complete: bool,
    pub lights: &'a mut [LightRecord],
    pub second_counts: &'a mut [u32],
    /// At least max(total light count, 2) entries. Native clearing uses only
    /// active_lights entries, although it subsequently adds both XY counts.
    pub total_counts: &'a mut [u32],
    pub previous_pre_gain: Gains,
    pub grid_valid: bool,
    pub second_grid_valid: bool,
    pub grid: &'a mut [[f32; 3]; 225],
    pub exclusions_valid: bool,
    pub exclusions: [[u8; REGION_BYTES]; 7],
    pub exclusion_aggregate: [u8; REGION_BYTES],
    pub histogram_cache: [[u32; 8]; 4],
    pub histogram_aggregate: [u32; 8],
}

/// IsMeasureResultStable4 (ELF 0xc2f90). Existing update=true is never cleared.
/// The selected history slot is replaced only if update is true after gating.
pub fn stability(
    state: &mut State<'_>,
    frame: &Frame<'_>,
    groups: usize,
    group: i32,
    threshold: f32,
) -> Result<(), InvalidInput> {
    if groups == 0 || groups > 4 || group < -1 || group as i64 >= groups as i64 {
        return Err(InvalidInput::Length);
    }
    finite(&[threshold])?;
    for gain in &state.history[..groups] {
        finite(gain)?;
    }
    let red = i64_at(frame.0, 0x1de8);
    let green = i64_at(frame.0, 0x1df0);
    let blue = i64_at(frame.0, 0x1df8);
    let gain = if red > 0 && blue > 0 {
        [
            green as f32 / red as f32,
            1.,
            1.,
            green as f32 / blue as f32,
        ]
    } else {
        [0.; 4]
    };
    state.stability_mask = 0;
    for (i, previous) in state.history[..groups].iter().enumerate() {
        if libm::fabsf(gain[0] - previous[0]) <= threshold
            && libm::fabsf(gain[3] - previous[3]) <= threshold
        {
            state.stability_mask |= 1 << i;
        }
    }
    if state.stability_mask != (1u8 << groups) - 1 {
        state.update = true;
    }
    if state.update {
        state.history[group.max(0) as usize] = gain;
    }
    Ok(())
}

/// Complete PrepareMeasureResult (ELF 0xc3180), including the original
/// stability helper, time-share cache, grid, exclusion and histogram paths.
/// Arithmetic/input errors may leave intermediate state changed.
pub fn prepare(
    state: &mut State<'_>,
    frame: &Frame<'_>,
    settings: &Settings<'_>,
) -> Result<(), InvalidInput> {
    let effect = frame.effect();
    let n = state.lights.len();
    let fast = effect.name.name()? == b"FASTAWBACT";
    if n == 0
        || n > 255
        || state.seen.len() != n
        || state.second_counts.len() != n
        || state.total_counts.len() < n.max(2)
        || settings.groups == 0
        || settings.groups > 4
        || effect.group < if fast { -1 } else { 0 }
        || effect.group as i64 >= settings.groups as i64
        || effect.count > 4
        || effect.indices[..effect.count].iter().any(|i| *i < 0)
    {
        return Err(InvalidInput::Length);
    }
    effect.name.name()?;
    for name in &state.mode_names {
        name.name()?;
    }
    finite(&effect.pre_gain)?;
    if effect.pre_gain[0] == 0. || effect.pre_gain[3] == 0. {
        return Err(InvalidInput::GainRange);
    }
    finite(&[settings.prior_sample])?;
    for i in 0..4 {
        if settings.exclusion_kind[i] == 3 {
            crate::interpolate(
                settings.exclusion_weight[i].knots,
                settings.exclusion_weight[i].weights,
                settings.prior_sample,
            )?;
        }
    }
    let active = if fast {
        settings.fast_light_count as u8 as usize
    } else {
        n
    };
    if active > n {
        return Err(InvalidInput::Length);
    }
    stability(
        state,
        frame,
        settings.groups,
        effect.group,
        settings.stability_threshold,
    )?;
    if !state.update {
        return Ok(());
    }

    if state.mode_names[0].name()? != effect.name.name()? {
        state.seen.fill(0);
        for name in &mut state.mode_names {
            name.0.fill(0);
        }
    }
    for local in 0..effect.count {
        let index = effect.indices[local] as usize;
        if index >= n {
            state.seen.fill(0);
            break;
        }
        state.seen[index] = 1;
        for region in 0..2 {
            let (gain, count) = frame.weighted(local * 48 + region * 24)?;
            let record = &mut state.lights[index].0;
            let at = region * REGION_BYTES;
            put_word(record, at, count);
            put_gains(record, at + 4, gain);
            state.second_counts[index] = u32_at(frame.0, 0xc0 + local * 4);
            put_gains(record, 0x9c, effect.pre_gain);
        }
    }
    state.complete = true;
    state.active_lights = active as u8;
    if fast {
        state.mode_names[0].copy_from(effect.name)?;
    } else {
        state.mode_names[effect.group as usize].copy_from(effect.name)?;
        for i in 1..settings.groups {
            if state.mode_names[0].name()? != state.mode_names[i].name()? {
                state.complete = false;
                break;
            }
        }
        if state.complete {
            for flag in state.seen.iter() {
                if flag & 1 == 0 {
                    state.complete = false;
                    break;
                }
            }
        }
    }
    if state.complete {
        state.total_counts[..active].fill(0);
        for light in &mut state.lights[..active] {
            let pre = gains_at(&light.0, 0x9c);
            for region in 0..2 {
                let at = region * REGION_BYTES;
                state.total_counts[region] =
                    state.total_counts[region].wrapping_add(u32_at(&light.0, at));
                let red = (float_at(&light.0, at + 4) * pre[0]) / effect.pre_gain[0];
                let blue = (float_at(&light.0, at + 16) * pre[3]) / effect.pre_gain[3];
                put_word(&mut light.0, at + 4, red.to_bits());
                put_word(&mut light.0, at + 16, blue.to_bits());
            }
        }
        state.previous_pre_gain = effect.pre_gain;
    }
    state.grid_valid = false;
    state.second_grid_valid = false;
    if effect.mode == 0 {
        for (i, pixel) in state.grid.iter_mut().enumerate() {
            let at = 0xd0 + i * 32;
            let count = u32_at(frame.0, at) as i32;
            if count != 0 {
                for (channel, value) in pixel.iter_mut().enumerate() {
                    *value =
                        (i64_at(frame.0, at + 8 + channel * 8) as f32 / count as f32) * (1. / 256.);
                }
            }
        }
        state.grid_valid = true;
    }
    state.exclusions_valid = true;
    state.exclusions.fill([0; REGION_BYTES]);
    state.exclusion_aggregate.fill(0);
    for i in 0..4 {
        let at = 0x1cf0 + i * 24;
        let count = i64_at(frame.0, at);
        let gain = awb_gain::ratios(
            count.wrapping_shl(8),
            i64_at(frame.0, at + 8),
            i64_at(frame.0, at + 16),
        );
        put_word(&mut state.exclusions[i], 0, count as u32);
        put_gains(&mut state.exclusions[i], 4, gain);
    }
    let mut weights = [0.; 4];
    let mut sum = 0.;
    for (i, weight) in weights.iter_mut().enumerate() {
        if settings.exclusion_kind[i] == 3 {
            *weight = crate::interpolate(
                settings.exclusion_weight[i].knots,
                settings.exclusion_weight[i].weights,
                settings.prior_sample,
            )?;
            sum = libm::fmaf(u32_at(&state.exclusions[i], 0) as f32, *weight, sum);
        }
    }
    if (sum as f64) > 0.00001 {
        let mut gain = [0.; 4];
        for (i, weight) in weights.iter().enumerate() {
            if settings.exclusion_kind[i] == 3 {
                let fraction = (u32_at(&state.exclusions[i], 0) as f32 * *weight) / sum;
                for (value, source) in gain.iter_mut().zip(gains_at(&state.exclusions[i], 4)) {
                    *value = libm::fmaf(source, fraction, *value);
                }
            }
        }
        put_gains(
            &mut state.exclusion_aggregate,
            4,
            awb_gain::normalize(gain)?,
        );
    }
    put_word(&mut state.exclusion_aggregate, 0, sum as u32);
    for i in 0..8 {
        // Native FASTAWBACT group -1 writes into the aggregate immediately
        // before clearing/rebuilding it from the existing group cache.
        if effect.group == -1 {
            state.histogram_aggregate[i] = u32_at(frame.0, 0x1d50 + i * 4);
        } else {
            state.histogram_cache[effect.group as usize][i] = u32_at(frame.0, 0x1d50 + i * 4);
        }
    }
    if state.complete {
        state.histogram_aggregate.fill(0);
        for row in &state.histogram_cache[..settings.groups] {
            for (sum, value) in state.histogram_aggregate.iter_mut().zip(row) {
                *sum = sum.wrapping_add(*value);
            }
        }
    }
    Ok(())
}

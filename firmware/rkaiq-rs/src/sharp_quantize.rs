//! Complete valid-domain SHARP V33 fixed-register conversion.
use crate::{
    isp_sharp::RESULT_BYTES,
    sharp_calibration::{f32_at, i32_at, put_u16, u16_at, ROW_BYTES},
    InvalidInput,
};
fn clip(n: i32, max: i32) -> u16 {
    n.clamp(0, max) as u16
}
fn round(n: f32) -> i32 {
    (f64::from(n) + if n <= 0. { -0.5 } else { 0.5 }) as i32
}
fn gaussian(sigma: f32, dist: &[f32]) -> [f32; 6] {
    let mut a = [0.; 6];
    for (i, d) in dist.iter().enumerate() {
        a[i] = libm::pow(
            2.71828182845905,
            ((f64::from(-*d) * 0.5) / f64::from(sigma)) / f64::from(sigma),
        ) as f32;
    }
    a
}
fn normalized3(sigma: f32) -> [f32; 6] {
    let mut a = gaussian(sigma, &[0., 1., 2.]);
    let sum = (a[0] + a[1] * 4.) + a[2] * 4.;
    for x in &mut a[..3] {
        *x /= sum;
    }
    a
}
fn normalized6(sigma: f32, radius: u8) -> [f32; 6] {
    let mut a = gaussian(
        sigma,
        if radius == 2 {
            &[0., 1., 2., 4., 5., 8.]
        } else {
            &[0., 1., 2., 1000., 1000., 1000.]
        },
    );
    let sum = ((((a[0] + a[1] * 4.) + a[2] * 4.) + a[3] * 4.) + a[4] * 8.) + a[5] * 4.;
    for x in &mut a {
        *x /= sum;
    }
    a
}
fn power(n: i32) -> f32 {
    let n = n as u32 & 255;
    if n < 32 {
        (1u32 << n) as i32 as f32
    } else {
        0.
    }
}
/// SDK padding is retained. The selected normal path reads raw dimensions at
/// exposure offsets 80/84. Invalid luma/sigma metadata is rejected atomically.
pub fn quantize(
    sel: &[u8; ROW_BYTES],
    strength: &[u8; 16],
    exposure: &[u8; 88],
    out: &mut [u8; RESULT_BYTES],
) -> Result<(), InvalidInput> {
    let f = |p| f32_at(sel, p);
    for p in (56..108)
        .step_by(4)
        .chain([112])
        .chain((120..276).step_by(4))
        .chain([280, 284])
        .chain((292..388).step_by(4))
    {
        if !f(p).is_finite() {
            return Err(InvalidInput::NonFinite);
        }
    }
    let mut factor = if strength[12] == 0 {
        1.
    } else {
        f32_at(strength, 8)
    };
    if !factor.is_finite() {
        return Err(InvalidInput::NonFinite);
    }
    if factor <= 0. {
        factor = f32::from_bits(0x358637bd);
    }
    let luma: [u16; 8] = core::array::from_fn(|i| u16_at(sel, 6 + i * 2));
    if luma.windows(2).any(|p| p[0] >= p[1]) {
        return Err(InvalidInput::NonIncreasing);
    }
    let mut next = *out;
    let width = i32_at(exposure, 80);
    let height = i32_at(exposure, 84);
    next[0] = sel[117];
    next[1] = u8::from(width > 3072 && height > 1728);
    next[2] = sel[4];
    next[3] = sel[3];
    next[4] = sel[0] ^ 1;
    next[5] = sel[0];
    next[144] = 0;
    next[145] = 0;
    put_u16(&mut next, 112, clip(width / 2, 8191));
    put_u16(&mut next, 114, clip(height / 2, 8191));
    next[6] = clip(round((f(60) / factor) * 128.), 128) as u8;
    next[7] = clip(round((f(68) / factor) * 128.), 128) as u8;
    let sharp = if sel[1] == 0 { f(72) } else { f(76) + f(80) };
    next[9] = clip(round((factor * sharp) * 4.), 127) as u8;
    next[8] = clip(round((f(88) / factor) * 128.), 128) as u8;
    for i in 0..7 {
        let log = libm::log(f64::from(luma[i + 1] - luma[i])) / core::f64::consts::LN_2;
        next[10 + i] = clip(log as i32 as i16 as i32, 15) as u8;
    }
    for (gain, add, dst, shift) in [(56, 64, 18, 50), (84, 92, 34, 51)] {
        let values: [f32; 8] =
            core::array::from_fn(|i| libm::fmaf(u16_at(sel, 22 + i * 2) as f32, f(gain), f(add)));
        let min = values
            .iter()
            .map(|v| libm::floorf(*v / factor) as i32)
            .min()
            .unwrap()
            .min(65536);
        if min <= 0 {
            return Err(InvalidInput::DegenerateRange);
        }
        let log = libm::logf(min as f32) / f32::from_bits(0x3f317218);
        let bits = (libm::floorf(log) as i32 as i16).wrapping_add(9) as i32;
        let scale = power(bits);
        next[shift] = clip(bits - 5, 15) as u8;
        for (i, v) in values.iter().enumerate() {
            let n = round(((1. / v) * factor) * scale) as i16 as i32;
            put_u16(&mut next, dst + i * 2, clip(n, 4095));
        }
    }
    for i in 0..8 {
        put_u16(
            &mut next,
            52 + i * 2,
            clip((u16_at(sel, 38 + i * 2) as f32 * factor) as i32, 1023),
        );
    }
    let kernel = sel[2] != 0;
    for (sigma, source, dst) in [(264, 292, 68), (268, 328, 71)] {
        let a = if kernel {
            if f(sigma) <= 0. {
                return Err(InvalidInput::DegenerateRange);
            }
            normalized3(f(sigma))
        } else {
            let mut a = [0.; 6];
            for i in 0..3 {
                a[i] = f(source + i * 4);
            }
            a
        };
        let x = clip(round(a[1] * 128.), 127) as u8;
        let y = clip(round(a[2] * 128.), 127) as u8;
        next[dst + 1] = x;
        next[dst + 2] = y;
        next[dst] = clip(128 - 4 * (i32::from(x) + i32::from(y)), 127) as u8;
    }
    let mut gauss = [0.; 6];
    if kernel {
        if sel[1] == 0 {
            if f(272) <= 0. {
                return Err(InvalidInput::DegenerateRange);
            }
            gauss = normalized6(f(272), sel[276]);
        } else {
            let sum = f(76) + f(80);
            if sum <= 0. || f(280) <= 0. || f(284) <= 0. {
                return Err(InvalidInput::DegenerateRange);
            }
            let a = normalized6(f(280), sel[288]);
            let b = normalized6(f(284), sel[289]);
            let r = f(76) / sum;
            let s = f(80) / sum;
            for i in 0..6 {
                gauss[i] = libm::fmaf(a[i], r, b[i] * s);
            }
        }
    } else if sel[1] == 0 {
        for i in 0..6 {
            gauss[i] = f(304 + i * 4);
        }
    } else {
        let sum = f(76) + f(80);
        if sum <= 0. {
            return Err(InvalidInput::DegenerateRange);
        }
        let a = f(76) / sum;
        let b = f(80) / sum;
        for i in 0..6 {
            gauss[i] = libm::fmaf(f(340 + i * 4), a, b * f(364 + i * 4));
        }
    }
    for i in 1..6 {
        next[74 + i] = clip(round(gauss[i] * 128.), 127) as u8;
    }
    next[74] = clip(
        128 - 4
            * (i32::from(next[75])
                + i32::from(next[76])
                + i32::from(next[77])
                + 2 * i32::from(next[78])
                + i32::from(next[79])),
        127,
    ) as u8;
    put_u16(&mut next, 80, clip((f(96) * 16.) as i32, 1023));
    next[82] = clip((f(100) * 8.) as i32, 8) as u8;
    next[83] = clip((f(104) * 128.) as i32, 128) as u8;
    for i in 0..14 {
        put_u16(
            &mut next,
            84 + i * 2,
            clip(round(f(120 + i * 4) * 1024.), 16384),
        );
    }
    for i in 0..22 {
        next[116 + i] = clip(round(f(176 + i * 4) * 128.), 128) as u8;
    }
    next[137] = match sel[108] {
        1 => 64,
        2 => 128,
        _ => 0,
    };
    put_u16(&mut next, 142, clip(round(f(112) * 1024.), 16383));
    next[140] = sel[116].min(9);
    put_u16(&mut next, 138, u16_at(sel, 118).min(1023));
    next[146..178].fill(0);
    *out = next;
    Ok(())
}

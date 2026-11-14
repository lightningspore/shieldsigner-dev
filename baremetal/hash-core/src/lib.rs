// SPDX-License-Identifier: MIT OR Apache-2.0
#![no_std]
use hmac::{Hmac, Mac};
use ripemd::Ripemd160;
use sha1::Sha1;
use sha2::{Digest, Sha224, Sha256, Sha384, Sha512};
use subtle::ConstantTimeEq;
mod pbkdf2_service;
#[derive(Clone)]
pub enum Engine {
    Sha224(Sha224),
    Sha256(Sha256),
    Sha384(Sha384),
    Sha512(Sha512),
    Sha1(Sha1),
    Ripemd160(Ripemd160),
}
#[derive(Debug, PartialEq, Eq)]
pub enum Error {
    Parameters,
    Cancelled,
}
impl Engine {
    pub fn new(id: u32) -> Result<Self, Error> {
        Ok(match id {
            0 => Self::Sha224(Sha224::new()),
            1 => Self::Sha256(Sha256::new()),
            2 => Self::Sha384(Sha384::new()),
            3 => Self::Sha512(Sha512::new()),
            4 => Self::Sha1(Sha1::new()),
            5 => Self::Ripemd160(Ripemd160::new()),
            _ => return Err(Error::Parameters),
        })
    }
    pub fn update(&mut self, data: &[u8]) {
        match self {
            Self::Sha224(s) => s.update(data),
            Self::Sha256(s) => s.update(data),
            Self::Sha384(s) => s.update(data),
            Self::Sha512(s) => s.update(data),
            Self::Sha1(s) => s.update(data),
            Self::Ripemd160(s) => s.update(data),
        }
    }
    pub fn digest(&self, out: &mut [u8]) -> Result<usize, Error> {
        macro_rules! finish {
            ($s:expr) => {{
                let bytes = $s.clone().finalize();
                if out.len() < bytes.len() {
                    return Err(Error::Parameters);
                }
                out[..bytes.len()].copy_from_slice(&bytes);
                Ok(bytes.len())
            }};
        }
        match self {
            Self::Sha224(s) => finish!(s),
            Self::Sha256(s) => finish!(s),
            Self::Sha384(s) => finish!(s),
            Self::Sha512(s) => finish!(s),
            Self::Sha1(s) => finish!(s),
            Self::Ripemd160(s) => finish!(s),
        }
    }
}
pub fn hmac(id: u32, key: &[u8], data: &[u8], out: &mut [u8]) -> Result<usize, Error> {
    macro_rules! calculate {
        ($t:ty) => {{
            let mut h = <Hmac<$t> as Mac>::new_from_slice(key).map_err(|_| Error::Parameters)?;
            Mac::update(&mut h, data);
            let bytes = h.finalize().into_bytes();
            if out.len() < bytes.len() {
                return Err(Error::Parameters);
            }
            out[..bytes.len()].copy_from_slice(&bytes);
            Ok(bytes.len())
        }};
    }
    match id {
        0 => calculate!(Sha224),
        1 => calculate!(Sha256),
        2 => calculate!(Sha384),
        3 => calculate!(Sha512),
        4 => calculate!(Sha1),
        5 => calculate!(Ripemd160),
        _ => Err(Error::Parameters),
    }
}
pub fn pbkdf2(
    id: u32,
    password: &[u8],
    salt: &[u8],
    rounds: u32,
    out: &mut [u8],
    mut service: impl FnMut() -> bool,
) -> Result<(), Error> {
    macro_rules! derive {
        ($t:ty) => {
            pbkdf2_service::derive::<Hmac<$t>, _>(password, salt, rounds, out, &mut service)
        };
    }
    let result = match id {
        0 => derive!(Sha224),
        1 => derive!(Sha256),
        2 => derive!(Sha384),
        3 => derive!(Sha512),
        4 => derive!(Sha1),
        5 => derive!(Ripemd160),
        _ => Err(Error::Parameters),
    };
    if result.is_err() {
        wipe(out);
    }
    result
}
pub fn compare(a: &[u8], b: &[u8]) -> bool {
    bool::from(a.ct_eq(b))
}
pub fn wipe(data: &mut [u8]) {
    for b in data {
        unsafe {
            core::ptr::write_volatile(b, 0);
        }
    }
    core::sync::atomic::compiler_fence(core::sync::atomic::Ordering::SeqCst);
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn derivation_matches_pinned_upstream() {
        macro_rules! check {
            ($id:expr,$t:ty) => {
                for rounds in [1, 2, 63, 64, 65, 127] {
                    for len in [1, 20, 32, 64, 65, 129] {
                        let mut expected = [0u8; 129];
                        let mut actual = [0u8; 129];
                        ::pbkdf2::pbkdf2::<Hmac<$t>>(
                            b"public password",
                            b"public salt",
                            rounds,
                            &mut expected[..len],
                        )
                        .unwrap();
                        pbkdf2(
                            $id,
                            b"public password",
                            b"public salt",
                            rounds,
                            &mut actual[..len],
                            || true,
                        )
                        .unwrap();
                        assert_eq!(expected, actual);
                    }
                }
            };
        }
        check!(0, Sha224);
        check!(1, Sha256);
        check!(2, Sha384);
        check!(3, Sha512);
        check!(4, Sha1);
        check!(5, Ripemd160);
    }
    #[test]
    fn cancelled_output_is_cleared() {
        let mut out = [0xa5; 129];
        let mut calls = 0;
        let result = pbkdf2(3, b"public", b"salt", 4096, &mut out, || {
            calls += 1;
            calls < 3
        });
        assert_eq!(result, Err(Error::Cancelled));
        assert_eq!(out, [0; 129]);
    }
    #[test]
    fn digest_is_non_consuming_and_copy_is_independent() {
        let mut a = Engine::new(1).unwrap();
        a.update(b"ab");
        let mut b = a.clone();
        a.update(b"c");
        b.update(b"d");
        let mut x = [0; 64];
        let mut y = [0; 64];
        a.digest(&mut x).unwrap();
        b.digest(&mut y).unwrap();
        assert_ne!(x, y);
        let original = x;
        a.digest(&mut x).unwrap();
        assert_eq!(original, x);
        assert!(compare(&x, &original));
        assert!(!compare(&x, &y));
    }
}

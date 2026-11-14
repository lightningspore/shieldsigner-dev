// SPDX-License-Identifier: MIT OR Apache-2.0
// Derived from RustCrypto/pbkdf2 0.12.2, src/lib.rs (RustCrypto Developers).
// Original PRF/XOR/block algorithm retained. Native service/cancel checkpoints
// added before each block and every64rounds; see UPSTREAM.md and licenses.
use crate::Error;
use hmac::digest::generic_array::typenum::Unsigned;
use hmac::digest::{FixedOutput, KeyInit, OutputSizeUser, Update};
#[inline(always)]
fn xor(res: &mut [u8], salt: &[u8]) {
    debug_assert!(salt.len() >= res.len());
    res.iter_mut().zip(salt.iter()).for_each(|(a, b)| *a ^= b);
}
pub fn derive<PRF, F>(
    password: &[u8],
    salt: &[u8],
    rounds: u32,
    res: &mut [u8],
    service: &mut F,
) -> Result<(), Error>
where
    PRF: KeyInit + Update + FixedOutput + Clone + Sync,
    F: FnMut() -> bool,
{
    if rounds == 0 || res.is_empty() {
        return Err(Error::Parameters);
    }
    let n = <PRF as OutputSizeUser>::OutputSize::to_usize();
    let prf = PRF::new_from_slice(password).map_err(|_| Error::Parameters)?;
    for (i, chunk) in res.chunks_mut(n).enumerate() {
        if !service() {
            return Err(Error::Cancelled);
        }
        for v in chunk.iter_mut() {
            *v = 0;
        }
        let mut salt = {
            let mut prfc = prf.clone();
            prfc.update(salt);
            prfc.update(&(i as u32 + 1).to_be_bytes());
            let salt = prfc.finalize_fixed();
            xor(chunk, &salt);
            salt
        };
        for round in 1..rounds {
            if round % 64 == 0 && !service() {
                return Err(Error::Cancelled);
            }
            let mut prfc = prf.clone();
            prfc.update(&salt);
            salt = prfc.finalize_fixed();
            xor(chunk, &salt);
        }
    }
    Ok(())
}

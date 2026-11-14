# Native hash core provenance

Production primitives use pinned RustCrypto crates: sha2 0.10.9, sha1 0.10.6,
ripemd 0.1.3, hmac 0.12.1 and subtle 2.6.1, with default features disabled.
The ARM firmware is built for armv7a-none-eabi; the core has no allocator or OS
calls. Root Cargo.lock records the production dependency checksums. This separate
crate's Cargo.lock also pins upstream pbkdf2 0.12.2 for differential host tests.

`src/pbkdf2_service.rs` derives from RustCrypto/pbkdf2 0.12.2 src/lib.rs, under
MIT OR Apache-2.0. Both licenses are retained here. The PRF, XOR, block counter
and output algorithm are retained. A callback checks service/cancellation before
each output block and every 64 rounds; cancellation returns an error and clears
the output. Zero rounds/empty output are refused, matching the native API's
parameter validation. No result from a cancelled operation is returned as a key.

The host test compares all six PRFs against the pinned unmodified upstream
implementation at 1/2/63/64/65/127 rounds and 1/20/32/64/65/129 output bytes
(216 combinations), and checks cancellation clearing and independent hash copies.
The Cortex-A7 hardware gate independently compares against CPython hashlib/hmac,
including public RFC4231/RFC6070 inputs and a public BIP39 English/TREZOR vector.
Those are primitive/API checks, not complete wallet or security qualification.

Sources: https://github.com/RustCrypto/hashes,
https://github.com/RustCrypto/MACs,
https://github.com/RustCrypto/password-hashes/tree/pbkdf2-v0.12.2/pbkdf2

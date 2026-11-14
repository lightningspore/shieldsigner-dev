# Native hashing prerequisites

Native app builds expose hashlib SHA224/SHA256/SHA384/SHA512/SHA1/RIPEMD160,
streaming update, repeatable digest/hexdigest, independent copy, name/block/digest
sizes, HMAC and PBKDF2-HMAC. Algorithms are actual pinned RustCrypto routines;
there are no placeholder hashes or shortened derivations. Existing micropython-lib
HMAC streaming logic and licenses are retained. The inherited `__new__` call uses
the working MicroPython object allocator; an explicit digestmod is required.
Native one-shot HMAC and subtle-backed compare_digest supplement that library.

Hash contexts live in aligned MicroPython-owned storage with compile-time Rust
size/alignment/no-drop checks and runtime alignment checks. No Rust allocation
is needed. GC finalizers clear stored context bytes, and an explicitly cleared
context cannot be reused. Digest clones state, so it does not consume the stream.
Empty mutable buffers are handled as valid empty slices even if their C pointer
is null. There is no claim here of complete application secret-memory erasure or
whole-system side-channel qualification.

PBKDF2 retains the upstream PRF/block/XOR algorithm with native service/cancel
checks before each output block and every 64 rounds. USB polling runs entirely
inside Rust; no Python callback or non-local exception crosses its stack. Ctrl-C
returns to C, clears partial output, and raises KeyboardInterrupt there. Full
iteration counts are used. Bounds are explicit: positive rounds, 1–4096 output
bytes, at most 1 MiB password/salt each, and at most one million PRF evaluations
(rounds × output blocks). Password/salt must be bytes-like; callers still own
Unicode normalization. Other hashlib algorithms and OpenSSL/FIPS policies are
not supplied; usedforsecurity is accepted for the native API without a FIPS claim.

Public CPython-generated vectors cover block boundaries, incremental/copy/repeated
digests, long/empty HMAC keys, multi-block PBKDF2, NUL bytes, invalid inputs and
context cleanup. Published reference inputs include
[RFC4231](https://www.rfc-editor.org/rfc/rfc4231.html),
[RFC6070](https://www.rfc-editor.org/rfc/rfc6070.html), and the
[public BIP39 vectors](https://github.com/trezor/python-mnemonic/blob/master/vectors.json).
The first hardware run passed all six algorithms; SHA1/4096 took 23 ms and the
SHA512/2048 public BIP39 derivation took 55 ms. These are derivation-call timings,
not ROM boot, app startup or full Seed model readiness.

A one-million-round SHA512 operation was interrupted over USB; the interpreter
then ran 500 further VM iterations, computed a fresh hash and returned native heap
to baseline. The host-observed response was about 0.10 s at 0.1 s serial-read
resolution. The callback itself is not claimed to have that measurement precision.

Unicode NFKD and the actual embit BIP39 leaf now have separate native gates
(UNICODE-PORT.md, BIP39-PORT.md, PASSPHRASE-PORT.md). The original Seed/UR/encryption
models, curve operations, Controller routing and SD assets remain unfinished. This checkpoint
supplies prerequisites; it does not establish seed generation or signing flows.

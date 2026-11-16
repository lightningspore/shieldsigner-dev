# Actual native secp256k1 and original Seed fingerprints

Native app builds link Bitcoin Core libsecp256k1 v0.7.0, commit
`a660a4976efe880bae7982ee410b9e0dc59ac983`. `secp/source.json`, original MIT
`secp/COPYING`, the build manifest and source hashes identify the implementation.
There is no replacement elliptic-curve algorithm or synthetic key/signature.
The original Seed finalization screen needs an actual fingerprint, so this
backend supplies a required dependency of the View/Controller port.

The original embit EC/BIP32 models now resolve the real provider, including
NUMS_PUBKEY's deferred original initializer. APIs cover key validation/creation,
SEC parsing/serialization, scalar/public tweaks and negation, DER/compact
signatures and low-S normalization, deterministic ECDSA, recoverable signatures,
x-only keys, BIP340 Schnorr and default SHA256 ECDH. Actual in-place tweak wrappers
require writable buffers. Missing APIs, custom Python nonce/ECDH callbacks and
external contexts fail explicitly. One foreground caller/context is supported.
No Python callback enters the library; Python errors are raised outside library
frames, and no exception crosses a Rust/C++ frame.

Python point tokens use validated big-endian X||Y and signature tokens use compact
big-endian R||S. They are private portable representations, not opaque C structs
and not an external storage ABI. Every point is parsed from canonical SEC before
use, so an arbitrary64-byte buffer cannot become an unchecked native pubkey.
The original app uses those values through embit/the binding APIs; serialized
SEC, DER/compact signatures, BIP32 keys and BIP340 outputs retain standard formats.
Malformed lengths/encodings/scalars are checked before library operations. The
library's invariant callbacks report a fixed fault rather than formatting secrets.

The portable ARM32 C build disables asm and uses upstream small precomputation
table options (verification window8, generator2KiB). Actual ECDH, extrakeys,
Schnorr and recovery modules are enabled. The context uses a preallocated arena;
the actual compiled context reports 180 bytes. Core algorithms and upstream source
are unchanged. Build: baremetal:secp:build, also called by native app builds.

Context randomization is a real library operation accepting caller-provided32
bytes, or None to reset its default. The gate supplies a PUBLIC test seed and
resets afterward. The randomized status records whether a seed was supplied; it
does not establish its entropy quality. The default valid library context is not
a qualified hardware-blinding entropy source. Native secrets.token_bytes remains
unavailable; no predictable bytes replace entropy. Optional BIP340 auxiliary
randomness follows the library's actual API, including its specified default.
TRNG integration, side-channel qualification, complete secret erasure and full
wallet/application qualification remain separate work.

The DUT gate passes all17published BIP32 valid paths (including leading zeros),
all16published invalid extended keys, and all19BIP340 vectors (including empty and
variable-length messages and invalid cases). It also verifies24original Seed
root/fingerprint cases against CPython embit0.8.0 and published BIP39 roots;
12 deterministic ECDSA DER comparisons with/without grinding;6 default ECDH pairs;
recoverable signing/recovery; low-S normalization; keypair coherence; in-place
operations; scalar/point relations; and repeated malformed input rejection with
subsequent healthy operations. Host reference provenance verifies the actual
ctypes backend, not a mock. All 54 host tests pass, including required embit ABI
coverage. These checks do not establish general wallet/security qualification.

Sources and licenses for the public corpora are linked in secp/VECTORS.md.
Prepare with baremetal:secp:prepare; run baremetal:secp:dut1:gate. The final gate
elapsed2740ms, excluding upload, ROM/DDR, boot and UI startup. Do not present that
number as a boot or whole-app time.

DUT1 final RAM image:
`3e476dbe2507acac55fd5c93a6e075ed4f9e85e2d4d0a15b50402d567781cc40`.
Load: logs/phase-11/dut1-20261115T001212Z.
Gate: logs/phase-11/usb-20261115T001235.503574Z.
Original Seed, PSBT, mnemonic, clearing and QR/scan regressions pass on this image.
The old curve-unavailable gate expectations now verify real public keys, NUMS and
the original Seed fingerprint API. Home restored 001318, preview stopped, no active
reader. Receipt: evidence/phase-12-native-curves.json. No SD/CAD/REF-storage writes.
Shared artifacts target DUT1; DUT0 still needs a clean RAM reload before its next
work because the older abandoned chr()-based fixture interned many characters.

Original View/Controller routing, displayed scan results, remaining compact/
encrypted/UR workflows, SD assets and actual printed-code optical qualification
remain unfinished. No fingerprint placeholder is needed for the original View.

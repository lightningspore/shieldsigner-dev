# Native Unicode normalization

Native app builds provide `unicodedata.normalize`, `is_normalized` and
`unidata_version`, using the actual no_std unicode-normalization 0.1.22 algorithms
and Unicode 15.0.0 tables. The version matches the read-only REF CPython 3.12.10
oracle. Cargo.lock pins dependencies; unicode/ retains upstream licenses,
provenance and the saved oracle. This is normalization support, not the entire
CPython unicodedata API: character categories, names and east_asian_width remain
unimplemented.

All four forms (NFC, NFD, NFKC, NFKD) accept UTF8 scalar strings. The API rejects
invalid forms and types, with CPython's empty-string behavior preserved. Bounds
are 65536 input bytes and 1 MiB output. Lone surrogate strings are outside this
UTF8 contract. Rust iterators count output before the C binding allocates its
MicroPython string. USB/cancellation checks run in Rust; interruption returns
through the ABI before C raises KeyboardInterrupt. Reordering temporary storage
uses the native heap; repeated combining-mark tests check return to baseline.
This does not establish complete secret-memory erasure.

`mise run baremetal:unicode:prepare` downloads and hash-verifies the official
[Unicode 15 normalization corpus](https://www.unicode.org/Public/15.0.0/ucd/NormalizationTest.txt).
`baremetal:unicode:gate` checks saved REF results, argument/boundary behavior,
reordering and heap cleanup. `baremetal:unicode:conformance` checks all 20
relations for each of the 19074 published rows through the actual board API.
`baremetal:unicode:identity` separately checks all four forms for each of the
1095035 scalar values absent from Part1 (surrogates excluded). These tests require
exclusive access to wired DUT0's USB console. The identity sweep is substantially
longer than the published-row gate; a host observation timeout does not prove a
device failure or stop computation.

Hardware evidence so far: API/REF gate passed at
logs/phase-11/usb-20261114T230549.084920Z. The published corpus passed at
logs/phase-12/unicode-conformance-20261114T230617.678970Z: 381480 comparisons in
6380 ms, with native heap at baseline. The separate identity sweep is pending;
its initial host capture timed out after 180 seconds. No full conformance claim
is made from the row test alone. Host regressions: 44 tests passed.

The RAM load's 20-second UART observation ended before the readiness marker;
USB enumerated and the subsequent hardware gates ran on that image. This is an
observation-window limit, not a measured cold boot. No SD or reference storage
was changed. DUT1 remains on the earlier app-ui image, with camera stopped and
Home restored after the user's demo. Mnemonic models, curve operations, complete
scan routing and optical QR success remain separate work.

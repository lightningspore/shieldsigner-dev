# Original SeedQR confirmation scanner

The original confirmation workflow now has a native device gate for matching,
wrong-seed, invalid-code, checksum-failure and cancellation paths. It runs from the
original Backup menu through QR export, confirmation prompt, scanner, result and
review/Done routes. The original Views decide success/error/navigation; tests do
not replace their selected results or decoder verdicts.

The gate supplies explicitly public CPython-generated NV12 pixel frames at the
camera boundary. Actual native ZXing, the original DecodeQR/seed comparison,
cooperative preview blit, native LVGL key events and Controller history run on
DUT1. Standard/compact12/24-word matches succeed. Wrong standard/compact seeds,
a recognized Bitcoin-address QR, unsupported text and a bad mnemonic checksum
return to QR review. Left/right cancellation uses timed logical raw input masks
through the real ButtonInput debounce/release logic, not a fake cancel return.
Each test pixel source starts/stops exactly once; the source seed remains intact
and no pending seed is substituted. These pixel fixtures do not qualify optical
acquisition or physical camera focus.

One app input fix accompanies the gate: HardwareButtons.check_for_low updates
controller activity after a debounced, unblocked low is accepted, as poll already
did. Scanner cancellation uses this path. Initial held keys and unaccepted raw
edges still do not count as presses; a debounced held level remains active until
release stabilizes. This prevents accepted scanner activity from retaining a stale
inactivity timestamp.

Compact detection exposed missing format-probe dependencies. The original detector
tries BIP38 and KEF encrypted-envelope parsing before resolving compact candidates.
Original BIP38/WIF/encryption/KEF/Base43 providers are now source-generated, keeping
format decisions and ambiguous compact/encrypted candidates. Public AES mode IDs
are extracted from pinned pycryptodomex3.23.0 during generation; this supplies no
native AES implementation. A local Base43 prepend buffer is a list because native
bytearray lacks insert; returned bytes match the original. Crypto entry points
check for their real AES/scrypt providers and fail explicitly when unavailable.
No encryption/decryption or wallet qualification follows from format detection.

`baremetal:app:qr:detection:prepare` regenerates original providers and an
independent oracle. `baremetal:app:qr:detection:dut1:gate` compares118raw/Base43
public probes with original unmodified CPython metadata code, including invalid
UTF8 IDs, malformed envelopes and compact/encrypted candidate overlap. It verifies
BIP38 container fields and explicit unavailable-crypto errors. The original Krux
MIT notice and all source/output hashes are retained.

`baremetal:app:seedqr:confirm:prepare` regenerates public scanner pixels;
`baremetal:app:seedqr:confirm:dut1:gate` runs the original workflow on normal DUT1
app-ui. Test seeds are discarded and settings restored afterward. The pixel source is
detached from the Controller, and the normal camera adapter and Home are restored. A separate existing
real-sensor error/idle gate remains the evidence for hardware preview cleanup.

Optical camera scanning, actual hand-transcription confirmation, qualified wallet
entropy, AES/scrypt workflows, broader signing and full SD startup remain open.
The earlier unexplained reset remains unresolved. No SD/CAD/REF/DUT0 writes are
needed for this stage; all target loads remain RAM-only.

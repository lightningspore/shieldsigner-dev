# Original QR model and cooperative Scan loop

The locked application's `models/decode_qr.py` and `gui/screens/scan_screens.py`
are byte-for-byte identical to the saved source from REF. The preparation tools
check the pinned application commit and repository source guards, retain all 27
QR model classes, and record class/method/output hashes in
`app/decode-qr-provenance.json` and `app/scan-loop-provenance.json`.
Upstream attribution remains in `app/LICENSE.SeedSigner`. The pinned
micropython-lib base64 source retains its author notices and full library license
in `app/LICENSE.micropython-lib`.

`seedsigner_port.decode_qr.DecodeQR` keeps the original classification, fragment
assembly, status and getter methods. Annotations are removed, PayloadAnalysis has
an explicit field constructor, and statuses retain their original integer values.
Dataclass/IntEnum introspection is not supplied. Logging calls that could include
payloads are omitted. The image backend uses existing native ZXing on640×480
luma/NV12. Feature imports load real implementations when used; an unported
module raises FeatureUnavailable, which is propagated before broad parse handlers
can misclassify it as invalid data. No fake crypto or permissive PSBT parser is
substituted. Full general scanning still needs the real seed/embit/UR/encryption
and other dependencies.

The generated ScanScreen._run preserves the original frame/status/completion/
invalid/back loop. NativeScanScreen supplies a foreground camera stream, wrap-safe
elapsed clock, ButtonInput names and cooperative preview metadata instead of
OS threads. It always stops its owned camera in finally. The camera retains Rust
AE/AWB state; consumers finish preview/QR access before fetching the next frame.
The internal stream is fixed640×480 NV12, not the complete original PIL Camera
API. Left/Right retains the original Scan Back behavior. The older preview-only
demo's center/Key3 exit is a separate adapter.

The original View/Controller now routes Main-menu Scan through this adapter.
Native instructions and fragment progress composite with camera pixels through
LVGL; see [SCAN-OVERLAY.md](SCAN-OVERLAY.md) for ownership and current gates.
The results below record the earlier model/loop stage, not full app qualification.

## Verified scope

- 44 host tests include whole-original-class comparisons for text/passphrases,
  invalid UTF8, SettingsQR, valid/invalid animated wallet fragments, unexpected
  fragment type changes and original Scan loop completion/invalid/back behavior.
- Real DUT0 and DUT1 native pixel fixtures pass through ZXing → original DecodeQR
  → original Scan loop, including SettingsQR completion, scripted Back and
  missing-dependency error cleanup. Native heap is stable after immutable QR
  lookup tables warm up. Base64 vectors and explicit unavailable-PSBT/UR errors
  also pass. The descriptor fixture is a public string, not a validated wallet.
- Real DUT0 camera/ZXing scan loop processed7 frames before USB Ctrl-C; DUT1
  camera/ZXing/LCD processed19 frames in the ten-second interruption test. Both
  returned camera/native heap to baseline; DUT1 restored native Home. This count
  includes startup and is not a preview-only FPS measurement.
- Observer snapshot confirms camera pixels on DUT1 LCD. The first full-resolution
  export timed out; transmission was drained to completion, then missing rows of
  the same retained snapshot were exported without another capture. The decoder
  validated all480 rows and rejected inconsistent duplicates.
- Optical QR recognition remains unqualified. The user placed a printed QR in the
  camera frame; native passes did not decode it. Full saved frames contain the
  complete symbol. An initial clipping diagnosis was corrected. The same pinned
  desktop ZXing detects a QR but reports Reed-Solomon checksum failure on that
  snapshot; cropping/sharpening/threshold variants did not recover it. This is
  evidence against an ARM-only failure, not proof of the exact optical cause.
  Images and diagnostic data remain in ignored local logs, not source control.

## Tasks

`baremetal:app:decode:prepare` regenerates the source-derived modules/fixtures.
`baremetal:app:decode:gate` runs public fixtures on wired DUT0; the `:dut1:gate`
variant runs them on the Mini PCB. `baremetal:app:scan:interrupt:gate` checks the
real wired camera. `baremetal:app:scan:lcd:interrupt:gate` checks the actual Mini
PCB camera/LCD for ten seconds, interrupts over USB and restores Home. The tool
rejects LCD output on wired DUT0, which still has its SPI loopback installed.

The latest shared build is app-ui with serial rv1103-dut1. DUT0 is on its own
headless native-ui image. Neither image has been written to SD; cold-power timing,
SD app/assets storage and complete SeedSigner workflows remain outstanding.

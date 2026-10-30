# Upstream divergences

This log separates upstream application behavior, our production integration and temporary diagnostics. A source change is not called image-integrated or hardware-qualified without its own evidence.

## Pinned sources

| Layer | Source and revision |
|---|---|
| Application build input | `3rdIteration/seedsigner` at `efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f` |
| OS build input | `3rdIteration/seedsigner-os` at `e7589465aff172f4f510ad46d18776ccc8d2c203` |
| Luckfox SDK | `3rdIteration/luckfox-pico` at `0b5c1f30ca6333b7ec5af70d26511da9ef8d39af` |
| Earlier SeedSigner reference | `SeedSigner/seedsigner` at `b2199c68b475eab0035b863b156f149757a1b4a6` (not the direct application build input) |

Hardware wiring follows the reviewed user fork's base-fork profile. It is a separately selected policy, not inferred from memory or display choices. Public source pins and exact-file guards in the builder/integration are authoritative; a similar repository name is not a substitute for its pinned revision.

## Existing production integration

| ID | Difference and reason | Source | Evidence and deployment |
|---|---|---|---|
| D01 | Rust SC3336 camera/ISP userspace and persistent native ZXing replace the vendor camera userspace path. Open kernel drivers and selected IQ data remain. | `firmware/rkaiq-rs`, image overlay/dependency scripts | 0.0.39-dev packaged verification and real-board soaks; `docs/CAMERA-MEMORY.md` records exact scope. Optical/coordinator tests remain separate. |
| D02 | Explicit base-fork display/buttons, UART2 disabled and PCSC autostart held to free GPIO42/43. Carrier profile keeps its own reader policy. | `scripts/configure-image-io-profile.py`, `firmware/bench-profiles/base-fork-io-config.json` | Compiled DTB checked; the base-fork image booted. Not qualification of a carrier's smartcard wiring. |
| D03 | PyO3 RGB565/SPI transport reuses the original guarded ST7789 initialization, GPIO, inversion and timing policy. | `firmware/lcd-rs` | Color-byte equivalence, bounded transfer and actual-board GUI soaks. No independent LCD thread. |
| D04 | Small-RAM policy defers optional background imports and the Scan-to-SLIP39 view edge; zram compresses pages in RAM without SD swap. Bounded logs, chunked QR executable hashing and read-only native code pinning reduce startup pressure/stalls. | Python integration, stream/log/QR adapters, image memory profile | Tested on Mini; See D10 for the now-deferred smartcard startup-route import. |
| D05 | Managed camera socket protocol, per-consumer pacing, bounded reconnects and full-resolution Y for QR, with preview-only reduction. | `shieldsigner_video_stream.py`, `shieldsigner_camera_compat.py` | Repeated Scan/Back/soaks; metrics distinguish API/diagnostic termination from actual navigation. |
| D06 | Image/entropy display reads produce RGB-shaped grayscale instead of L-mode scalar extrema. An active video stream is stopped before the app's error destination. Entropy checks and true still RGB transport remain. | `shieldsigner_camera_compat.py`, `shieldsigner_integration.py` | Seed creation/address/xpub exploration and 49 Python tests at `e25dc9b`. Included in the verified native image as guarded runtime integration; the pinned upstream app files remain unchanged. |

## Native frontend work in progress

| ID | Intended change | Status | Required verification |
|---|---|---|---|
| D08 | Rust preview resize, rotation and pixel preparation using bounded reusable buffers; upstream orientation, overlays and full QR resolution retained. | Implemented; packaged image and physical Mini cold boot verified | 16 byte-exact Pillow reference cases on host/ARM, four packed-image rotations, actual GUI previews. `frontend/native-image-cold-boot-validation-2026-10-30.json`. No SPI readback/colorimetry claim. |
| D09 | Native frame reception/latest-frame/pacing and QR IPC behind PyO3. Python retains managed-owner coordination; bounded buffers, deadlines, cancellation, retries, exact binary payloads and cleanup are preserved. | Implemented and selected in the cold-boot-verified image | 23 Rust/58 Python tests, five Mini socket/lifecycle cases, real Scan/Back/fault/entropy/wallet/still workflows, all-256-byte and animated-UR checks, and user-confirmed optical decoding after flash. Resource comparisons retain their stated limits. |
| D10 | Defer the optional smartcard startup graph while preserving original view identity, cache clearing and mandatory storage initialization. | Implemented; normal cold startup and Smartcard Tools menu navigation passed | Controlled ARM imports: 4.19 MiB fewer traced live bytes at startup and 4.32 MiB after Scan imports; 144 fewer modules. These are not total target-RAM savings. `frontend/startup-import-comparison-2026-10-29.json`. |

The existing `shieldsigner_lcd` extension/package name will initially remain a compatibility entry point for shared native display/frontend primitives. This avoids a second toolchain/bootstrap and duplicated native-library loading while the interface stabilizes. Camera ownership and cryptographic/signing policy must remain explicit; the module name does not imply those have already moved.

## Diagnostic differences

D07 is explicitly opt-in: button GPIO-read overlays, requested screen capture, GUI harnesses, allocation tracing and object census. They are not normal firmware features. Capture may retain an extra image; profiling changes page residency and may consume substantial RAM. The full tracemalloc snapshot tool refuses the Mini after a real unresponsive-board incident. Private captures and wallet/QR values stay outside public artifacts. Procedures and outcomes are in `docs/APP-DIAGNOSTICS.md`.

## Update procedure

For each change record the pinned source/guard, behavior before and after, rationale, source location, regression tests, hardware evidence and image deployment status. Preserve historical records rather than relabeling an older soak as proof of new code. Compare diagnostics separately from ordinary app runs. Mark a row implemented, packaged or boot-tested only after reading the corresponding evidence.

D08 implementation detail: pixel-center accumulation follows the observable rounding of pinned Pillow 11.0.0 `src/libImaging/Geometry.c` (`ImagingScaleAffine`). Exact rational center arithmetic differed at some fractional-scale ties and was rejected by the full-pixel fixture. PreviewRenderer reuses one bounded RGB output vector and returns independent immutable Python bytes; GPIO/SPI and the GUI are not touched by the reference test.

Coordinator follow-up: rejected starts now preserve live state, and reconnect connect-timeouts use the same bounded retry policy as read failures. Five real-Mini socket tests and a fresh real Scan/Back passed after the correction; `frontend/coordinator-lifecycle-hardware-2026-10-29.json`. The first native image attempt was intentionally stopped and superseded before flashing.

Verified image checkpoint: corrected bundle `9b8d31…` built and passed packed rootfs/ARM native frontend tests. Its exact packaged library/helpers also passed a temporary real-board Scan/Back trial. At that temporary-runtime checkpoint the installed image was still old. Subsequently, two complete identical-input SDK builds matched bit-for-bit, and physical flash/power-cycle plus packaged boot verification passed as recorded below.

Final deployment: corrected 9b8d31… image is physically flashed/cold-boot verified on the Mini. The user confirmed power removal/restoration and repeated successful optical QR decoding. Readback matched 112 packaged files/modes and the normally mapped d3b1dafe… extension; no unexpected runtime overlays were present. Latest camera exit 0 and zero camera/QR processes/DMA were independently checked. `frontend/native-image-cold-boot-validation-2026-10-30.json`.

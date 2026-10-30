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
| D04 | Small-RAM policy defers optional background imports and the Scan-to-SLIP39 view edge; zram compresses pages in RAM without SD swap. Bounded logs, chunked QR executable hashing and read-only native code pinning reduce startup pressure/stalls. | Python integration, stream/log/QR adapters, image memory profile | Tested on Mini; eager imports in `Controller.start()` still pull dependencies in. See D10. |
| D05 | Managed camera socket protocol, per-consumer pacing, bounded reconnects and full-resolution Y for QR, with preview-only reduction. | `shieldsigner_video_stream.py`, `shieldsigner_camera_compat.py` | Repeated Scan/Back/soaks; metrics distinguish API/diagnostic termination from actual navigation. |
| D06 | Image/entropy display reads produce RGB-shaped grayscale instead of L-mode scalar extrema. An active video stream is stopped before the app's error destination. Entropy checks and true still RGB transport remain. | `shieldsigner_camera_compat.py`, `shieldsigner_integration.py` | Seed creation/address/xpub exploration and 49 Python tests at `e25dc9b`. Live file overlays only; not yet in the previously flashed image. |

## Native frontend work in progress

| ID | Intended change | Status | Required verification |
|---|---|---|---|
| D08 | Rust preview resize, rotation and pixel preparation using bounded reusable buffers. Preserve upstream orientation, canvas/overlay behavior and full QR resolution. | Primitive/PyO3 renderer and guarded GUI adapter implemented; first physical Scan/Back cycles passed; not packaged | 8 Rust tests and 16 byte-exact Pillow 11.0.0 cases on host and physical ARM. `reverse-engineering/rkaiq/frontend/preview-arm-reference-2026-10-29.json`. First integrated hardware evidence: `frontend/native-gui-first-hardware-2026-10-29.json`; no SPI readback or new human visual qualification. |
| D09 | Native frame reception/latest-frame/pacing and QR IPC behind PyO3, preserving process ownership, deadlines, reconnect/cancel semantics and exact binary QR payloads. | QR IPC core/PyO3 implemented and cross-built; bounded frame pool, cursors and cancellable socket reader implemented; receiver thread/PyO3 socket interface implemented; managed reconnect coordinator implemented/tested; explicit app adapter selection implemented; three integrated hardware Scan/Back/reopen cycles passed; full workflows/image qualification remain | 23 Rust tests, 54 Python tests, host PyO3 frame/QR protocol/lifecycle tests, and current ARM/QEMU native reception/direct-frame QR/preview corpus (`frontend/receiver-arm-qemu-reference-2026-10-29.json`) (`frontend/qr-arm-qemu-reference-2026-10-29.json`); Protocol/error/cancel tests; no unbounded queues; full API/seed workflows; repeated hardware cycles, QR corpus and resource/memory comparison. |
| D10 | Defer `ToolsSmartcardMenuView` and other unnecessary startup-route imports until their branches are used. | Smartcard startup import deferred in the pinned Controller.start method; normal routes avoid importing its dependency graph, and the special case still uses original class identity | 55 Python tests, including cache-clear/identity and mandatory-store checks; Packed ARM controlled import comparison: 4.19 MiB fewer traced live bytes at startup, 4.32 MiB after Scan imports; 144 fewer modules. Patched startup reached Home on the board; matched resource comparison and smartcard-menu workflow remain pending. Source guards and routing tests; comparable startup allocations; real smartcard-menu availability and normal Scan/wallet navigation. |

The existing `shieldsigner_lcd` extension/package name will initially remain a compatibility entry point for shared native display/frontend primitives. This avoids a second toolchain/bootstrap and duplicated native-library loading while the interface stabilizes. Camera ownership and cryptographic/signing policy must remain explicit; the module name does not imply those have already moved.

## Diagnostic differences

D07 is explicitly opt-in: button GPIO-read overlays, requested screen capture, GUI harnesses, allocation tracing and object census. They are not normal firmware features. Capture may retain an extra image; profiling changes page residency and may consume substantial RAM. The full tracemalloc snapshot tool refuses the Mini after a real unresponsive-board incident. Private captures and wallet/QR values stay outside public artifacts. Procedures and outcomes are in `docs/APP-DIAGNOSTICS.md`.

## Update procedure

For each change record the pinned source/guard, behavior before and after, rationale, source location, regression tests, hardware evidence and image deployment status. Preserve historical records rather than relabeling an older soak as proof of new code. Compare diagnostics separately from ordinary app runs. Mark a row implemented, packaged or boot-tested only after reading the corresponding evidence.

D08 implementation detail: pixel-center accumulation follows the observable rounding of pinned Pillow 11.0.0 `src/libImaging/Geometry.c` (`ImagingScaleAffine`). Exact rational center arithmetic differed at some fractional-scale ties and was rejected by the full-pixel fixture. PreviewRenderer reuses one bounded RGB output vector and returns independent immutable Python bytes; GPIO/SPI and the GUI are not touched by the reference test.

# Native frontend implementation and acceptance plan

Implement the requested preview pipeline, camera/QR bridge and deferred startup imports one area at a time. Preserve existing signing/entropy behavior and the reviewed display/button map. Keep source, hardware and packaged-image evidence separate.

1. Build and test reusable Rust luma/RGB preview preparation against the current Pillow nearest-resize/expanded-rotation output. Preserve full-resolution decode/entropy/still APIs and GUI overlays.
2. Implement native socket frame reception, bounded latest-frame ownership and per-consumer pacing; move QR worker IPC behind PyO3 with exact binary results. Preserve managed-owner startup/stop, whole-frame deadlines, reconnect policy, cancellation, exit reporting and DMA cleanup. Keep existing behavior as an explicit comparison backend until the native path is qualified.
3. Remove unnecessary startup-route imports with exact pinned-source guards. Test every affected destination and measure import/ordinary startup memory.
4. Compare old/new ordinary app PSS/RSS/swap, allocations, CPU/frame/render/decode rates and interaction latency under the same image/hardware/configuration. Account for diagnostic overhead and native allocations outside tracemalloc.
5. Qualify integrated milestones on the board: Scan/Back/reopen, known public/binary QR data, camera seed generation, address/xpub/wallet navigation, error recovery and owner/DMA cleanup. Do not substitute direct-image decoding for optical capture.
6. Package the selected native path into a reproducible immutable image, verify the packed files/ABI/API, then flash and cold-boot test. Persisted source is not a deployed-image claim.
7. Update `UPSTREAM-DIVERGENCES.md`, evidence and runbooks throughout. Keep private captures and wallet data out of public records.

Initial checkpoint: clean source at `e25dc9b`; board has the reviewed 0.0.39-dev image plus temporary camera entropy/error-cleanup overlays and diagnostic input/capture. Those overlays must enter the next complete image. Existing quantitative evidence is in `MEMORY-THREADS.md` and `CAMERA-MEMORY.md`; it is a baseline, not a measurement of the new port.

Preview checkpoint: Rust resize/orthogonal rotation plus a reusable PyO3 PreviewRenderer passed 8 Rust tests and all 16 pinned-Pillow reference cases on the physical board. The ARM extension was built offline in an isolated output with the SDK cache mounted read-only. It is not yet selected by the app; native reception/integration is next.

# Phase7 passed

Phase7 passed on the real DUT in `logs/phase-7/20261114T152545Z`. After the user repositioned the target, the decoded raw preview shows a recognizable printed carton label/barcodes and contrasting surrounding material. Ten clean consecutive frames, nine sensor readbacks and32 selected receiver/configuration matches were verified. The normal build uses named original driver code. The retained receipt is [evidence/phase-7.json](evidence/phase-7.json); scene pixels remain ignored/local. ISP colour, 3A and interpreter qualification are still separate gates.

| Requirement | Current evidence | Limit |
| --- | --- | --- |
| REF ordered sensor/CIF/CSI/D-PHY observations | `logs/phase-7/live-events-2.txt`:201 entries, dropped0/errors0; original capture passed during/after hooks | MMIO observed before store; timestamps are not bus-completion order |
| Idle/streaming register state | `ref-dumps/{idle,streaming}.txt`, framed payloads, CRCs and SHA256 manifests | Main IOC tail0xff570000–0xff577fff not captured; first address faults |
| IOC pin controls | Separate PMU IOC page plus main IOC prefix; `ioc-source-coverage.json` covers all SDK-known drive/pull/Schmitt fields and conservative IOMUX bounds | This does not assert readable values for the excluded DT padding |
| Format/node | REF raw `/dev/video0`, BG10,2304×1296,stride3072,3,981,312bytes | ISP `/dev/video11` is later Phase8 |
| RAM-only raw capture | Latest named-driver run captured10 alternating clean frames; rejects FIFO errors, both ends, repeat slot and excessive interval | Fixed diagnostic exposure/profile, not AE |
| REF comparison |32 selected receiver/config readbacks match after explicit masks, DMA remaps and polling exception | Not full-state equivalence; dynamic W1C status excluded |
| Host preview |192×108 RGB preview decoded and inspected; real printed target recognized | Subsampled, uncalibrated Bayer colour |
| Replace replay with original named code | `camera/sc3336.rs`, `receiver.rs`, `sensor_mode.rs`; nine sensor controls correct and real-scene gate passing | ISP/3A remains Phase8 |

Latest named-driver runs:

- Gate run: `20261114T152545Z`, target repositioned by user. Printed label/barcodes recognizable, ten frames clean,32 selected registers match. Receipt includes firmware/serial/preview/snapshot hashes without publishing scene data.

- Resumed captures: `20261114T150900Z` night profile clipped white; `20261114T151123Z` unity/1024 lines was dim; `20261114T151455Z` unity/8192 lines showed real surface/edges. Latest run passed10 clean frames, nine sensor readbacks and32 selected register comparisons. `capture-audit.json` independently verifies mechanical evidence but explicitly requires visual review. It is not yet a colourful-scene gate pass.

- Pattern: `logs/phase-7/20261114T080339Z`,10 clean frames, nine controls correct,32 selected register matches. Preview `named-driver-pattern.png`.
- Real camera: `logs/phase-7/20261114T080816Z`,10 clean frames at~799203us, pattern disabled, exposure32759/VTS32767 and high gain read back correctly. Preview `named-driver-low-light.png` remains dark.

REF is healthy, original modules remain, no temporary bm module is loaded. Taint4096 is the historical out-of-tree flag. Last original full raw capture after reference ISP work passed (`logs/ref-isp/post-reference-raw-capture.txt`). Do not retry camera graph teardown or the faulting IOC address. DUT is stopped in the gate run's named real-camera payload and accepts UART R; all recent processes have finished.

To repeat the raw gate, rebuild with `mise run baremetal:camera:build`, send R through REF UART3 at115200, and run the existing RAM-only harness with a40-second capture and `--pass-pattern '@@PASS camera-raw-ten-frames'`. Decode and inspect the new preview; independently audit the ten frame records, sensor readbacks and selected register comparison. The next phase is ISP/YUV/statistics/parameter integration, followed by the interpreter after its hardware gate.

The previous replay image is preserved in ignored `build/phase-7-replay-baseline/`. The optional `camera-replay` feature compiled after the refactor but was not reloaded; it emits unused-code warnings because it bypasses named configuration. Compiling it changed the Cargo ELF artifact, **not** the packaged `build/hello-download.bin` or its manifest. Always use the build task before a new download. Build manifests now hash nested Rust driver files too.

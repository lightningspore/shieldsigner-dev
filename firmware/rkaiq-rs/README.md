# ShieldSigner RKAIQ Rust reconstruction

A partial, verified numerical reconstruction plus standalone camera-test diagnostics. See [the investigation](../../reverse-engineering/rkaiq/README.md) and [hardware procedure](../../reverse-engineering/rkaiq/HARDWARE-TEST.md).

This crate does **not** implement a complete RKAIQ library or auto-exposure/ISP startup. It is not installed into the existing image. `cargo test` covers local edge cases; the independent ARM-machine-code differential harness lives outside this crate and currently checks 8,050 cases.

Binaries:

- `camera-probe`: Linux V4L2/media inventory and bounded MMAP capture, no RKAIQ calls.
- `numeric-fixture`: line-based numerical comparison runner.
- `frame-preview`: supported frame payloads to uncalibrated grayscale PGM.

Use the repository's `camera:rust:*` mise tasks to build/test/package. `Cargo.lock` pins Rust dependencies. The static ARMv7/musl binaries use Linux syscalls and do not require the target image's dynamic uClibc runtime.

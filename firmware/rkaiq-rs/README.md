# ShieldSigner RKAIQ Rust reconstruction

An experimental runnable SC3336 camera path with calibrated ISP startup,
persistent automatic exposure/white balance, ISO-dependent demosaic tuning and
an opt-in SeedSigner Camera adapter. It uses existing Linux camera drivers and
does not link or call RKAIQ. It is not a complete RKAIQ ABI implementation;
optical QR and broader physical qualification remain open. See
[the investigation](../../reverse-engineering/rkaiq/README.md) and
[hardware procedure](../../reverse-engineering/rkaiq/HARDWARE-TEST.md).

Binaries:

- `camera-probe`: V4L2/media inventory, finite diagnostic capture and continuous
  application-owned RGB streaming. Streaming omits the final scene-image file
  unless `SHIELDSIGNER_CAMERA_SAVE_IMAGE=1` explicitly requests it; calibration,
  measurement and log diagnostics remain retained.
- `numeric-fixture`: line-based comparison runner for recovered native routines.
- `frame-preview`: supported frame payloads to uncalibrated grayscale PGM.

Use `camera:rust:*` mise tasks. `Cargo.lock` pins dependencies; static
ARMv7/musl binaries require no target dynamic uClibc runtime. Local tests,
original-ARM differential comparisons, hardware runs and their distinct limits
are recorded separately. No installed app or boot change is required by the
process-local launcher. Frozen kits retain their own versioned behavior.

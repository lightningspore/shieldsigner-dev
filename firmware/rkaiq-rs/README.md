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

Development 0.0.35 enables all eight advanced ISP blocks by default. See the
[combined hardware result](../../reverse-engineering/rkaiq/ISP.md#development-0035-combined-isp-hardware-result)
for evidence and remaining qualification limits.

The dashboard lives in `demo/`. Forward the camera owner's Unix stream socket
to local TCP 60366, then launch from the repository root:

```sh
uv run --python 3.13 --with pillow python firmware/rkaiq-rs/demo/server.py --camera-port 60366 --listen-port 8765 --static-dir firmware/rkaiq-rs/demo --rotate 180
```

Open http://127.0.0.1:8765/ for real frames, snapshots and fullscreen. The bridge
fans one camera connection out to browsers and retains previews in memory.
Optional `--metadata-file` supplies recorded enable/verification telemetry;
those indicators are not per-frame measurements.

### QR decoding path

The Rust owner configures the sensor/ISP, runs automatic camera controls,
receives NV12 frames and converts them into RGB. Its `SSRGB001` Unix-socket
stream delivers frames to `shieldsigner_video_stream.py`, which constructs
Pillow RGB images for the installed Camera interface.

SeedSigner's `DecodeQR.add_image()` passes those images to
`pyzbar.decode(..., symbols=[ZBarSymbol.QRCODE], binary=True)`. ZBar finds and
decodes the QR pixels; SeedSigner classifies the resulting payload and handles
animated formats such as UR. That decoder is separate from RKAIQ and remains
the installed application implementation. No new Rust QR decoder is required
to replace the proprietary camera-control library.

The optical checker compares camera-decoded content only against the bundled
public test target; synthetic fixture success does not qualify an optical scan.

### Faster desktop preview (0.0.37 development)

For the desktop demo only, set `SHIELDSIGNER_CAMERA_STREAM_FORMAT=nv12` on the
Rust owner process. It sends tightly packed full-range BT.601 NV12 using
`SSNV12F1`; `demo/server.py` converts to RGB on the desktop. VGA payloads are
460,800 bytes instead of 921,600 bytes. The RGB `SSRGB001` protocol remains the
default for the Python application. Other stream-format values fail, and NV12
mode rejects limited-range input rather than displaying incorrect levels.

[Hardware comparison](../../reverse-engineering/rkaiq/nv12-preview-hardware-validation.json):
delivered preview improved from about 4.7 to 10.6 FPS while camera sequence
advance stayed near 15 FPS. These are short desktop delivery measurements.
Pillow's higher-precision color conversion differed from the board's Q8
conversion by at most one channel level in the sampled test.

Run parser/color/invalid-frame checks with:

```sh
uv run --python 3.13 --with pillow python firmware/rkaiq-rs/demo/test_server.py
```

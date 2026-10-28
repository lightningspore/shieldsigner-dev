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
- `shieldsigner-qr-reader`: persistent QR-only ZXing-C++ worker, separate from
  the Rust RKAIQ replacement. It returns unchanged binary payloads over a local
  framed connection; no vendor runtime or target C++ installation is required.

Development **0.0.38-dev** fixes native dark-history damping (NaN variance is
compared rather than rejected), bounds runtime logs, and supports both the
legacy test-board app and the pinned image app Camera APIs. Its exact Rust
binary passed [fresh native ISP/AWB comparisons](../../reverse-engineering/rkaiq/isp-0.0.38-fresh-hardware-validation.json).
The [native QR integration check](../../reverse-engineering/rkaiq/native-qr-integration-hardware-validation.json)
passed binary payloads, CompactSeedQR, reversed/duplicated animated UR PSBT,
and the pinned image app's real stream/still APIs. Actual pinned scan/preview
rendering and software cancellation also pass on the existing rootfs. These
are distinct from a successful final SDK image build, booting that image, or
matching a live optical target with this exact runtime. The current target is
clipped; native optical qualification remains open.

[Selected-profile scope](../../reverse-engineering/rkaiq/selected-profile-runtime-scope.json)
records the boundary: CPROC's all-128 API settings are treated as neutral by
bypassing the block, an explicit identity assumption rather than native CPROC
control proof. CPSL Auto LED/force-gray is configured in IQ but unactivated and
unimplemented in this fixed color pipeline. Disabled optional blocks and
HDR/DCG/IR/autofocus/general-ABI support are not claimed.

To opt in on an existing app installation:

```sh
python3 python/shieldsigner_integration.py --app-root /ABSOLUTE/APP_ROOT --config /ABSOLUTE/owner.json --qr-reader /ABSOLUTE/shieldsigner-qr-reader
```

The launcher changes modules only in that process and rejects unreviewed
Camera source hashes. `--qr-reader` (or `SHIELDSIGNER_QR_READER`) selects the
persistent native worker. Without it, the existing ZBar/JPEG fallback remains
available. Stop closes the worker; failures are counted and the installed ZBar
extractor remains an emergency fallback. Binary bytes are never transcoded to
text before SeedSigner's existing payload classification/assembly.

Normal managed capture logs retain the first 256 KiB and newest 768 KiB, with
at most three explicitly owned finished bounded sessions. Scene frames and QR
payloads are not written. `SHIELDSIGNER_CAMERA_LOG_FULL=1` is an explicit
unbounded diagnostic mode required for full original-ARM replay traces.
[Actual bounded-log hardware evidence](../../reverse-engineering/rkaiq/bounded-logging-hardware-validation.json)
records 4.39 MB received and about 1 MiB retained, with clean shutdown.

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

SeedSigner's `DecodeQR.add_image()` uses the process-local extraction backend.
With `--qr-reader`, Pillow luminance pixels go to the persistent native
ZXing-C++ worker, which returns raw payload bytes. SeedSigner's existing
classification and animated UR assembly remain unchanged. This open-source
QR decoder is separate from the Rust RKAIQ camera-control replacement.

Without the native worker, the compatibility path uses
`pyzbar.decode(..., symbols=[ZBarSymbol.QRCODE], binary=True)`. The installed
extractor also remains the emergency path after a native worker error.

That non-native compatibility path adds a process-local retry: if the original
decoder finds no symbol in a Pillow frame, it retries an in-memory JPEG at
quality 85 with chroma subsampling disabled. Raw successes bypass the retry;
binary payloads and SeedSigner's format handling remain intact. No JPEG or
decoded payload is written to disk. A real target failed raw decoding but
decoded after this transformation of the **same** frame; simple blur and
median filters did not help. This establishes a useful workaround, not the
precise imaging cause. Misses incur an extra encode and ZBar pass.

[Optical hardware evidence](../../reverse-engineering/rkaiq/optical-qr-hardware-validation.json)
records a historical known public printed address decoded through the real
camera and installed decoder using a development JPEG retry with the frozen
0.0.37 executable. It does not qualify the exact 0.0.38/native worker optical
path, animated camera acquisition or every lighting condition.

Run the focused fallback contract checks with:

```sh
mise exec -- uv run --python 3.13 --with pillow python firmware/rkaiq-rs/python/test_qr_fallback.py
```

The optical checker compares camera-decoded content only against the bundled
public test target; synthetic fixture success does not qualify an optical scan.

#### QR robustness investigation

[Paired-frame investigation](../../reverse-engineering/rkaiq/qr-decoder-investigation.json)
found that JPEG quality 75 helped one live batch (8/8 versus raw 0/8 and
quality 85 3/8), but every tested JPEG variant failed subsequent batches.
There is no reliable quality-only fix established. ISP defaults and the current
application fallback remain unchanged.

ZXing-C++ 3.1.1 decoded all four saved raw frames from the last batch on the
desktop; ZBar decoded none of those same frames, with or without JPEG.
ZXing's `LocalAverage` binarizer passed 4/4; its `GlobalHistogram` and
`FixedThreshold` settings passed 0/4. This points to decoder/binarization
sensitivity and demonstrates readable data in the raw camera images. It does
not prove ideal ISP quality. The current uClibc board cannot use the ordinary
glibc Python wheel, so a static ARM executable was built instead.

[Native Luckfox comparison](../../reverse-engineering/rkaiq/qr-native-hardware-benchmark.json)
now passes: ZXing read 40/40 attempts on four identical saved camera luminance
frames, versus ZBar 0/40. With capture stopped, median decode times were
15.38 ms versus 58.04 ms (3.77x). This is a decode-only comparison excluding
process startup and file loading; it does not establish live scan-loop FPS.
Whole-process peak RSS was about 1.5 MiB for the native harness and 11.2 MiB
for the Python/ZBar harness; that is not a library-only memory comparison.

The native `Barcode::bytes()` API also preserved synthetic NUL/high-bit data,
all 256 byte values and a 32-byte payload exactly (9/9 total reads on Luckfox).
No text conversion is used. Subsequent [actual ARM/app tests](../../reverse-engineering/rkaiq/native-qr-integration-hardware-validation.json)
now pass byte-exact binary/CompactSeedQR and reversed/duplicate animated UR
assembly, plus real Camera stream/still APIs. Those QR fixtures enter as
generated pixels, not through camera optics. The actual
[pinned scan-loop check](../../reverse-engineering/rkaiq/pinned-image-scan-loop-hardware-validation.json)
executes render/cancel/cleanup with real frames, but its clipped target yields
no content match and its loop counts are not a throughput benchmark.

[quirc hardware comparison](../../reverse-engineering/rkaiq/quirc-native-hardware-comparison.json)
also tested upstream quirc, default and float builds. Both preserved all binary
fixtures (9/9 each), but found no QR in the four difficult raw frames (0/24
attempts each), versus ZXing 24/24. Default quirc took about 7.6 ms per failed
attempt and float about 6.8 ms, versus ZXing 15.3 ms per successful decode;
failure latency is not successful-read throughput. Native process peaks were
about 0.72 MiB for quirc versus 1.49 MiB for ZXing. Local box-threshold
preprocessing rescued only 1/4 frames at the best tested setting. This is a
limited scene comparison, not a universal ranking. ZXing remains the current
native integration backend; quirc remains a measured alternative rather than
an installed application backend. Rebuild with `mise run camera:qr:quirc-build`; retain
the upstream ISC license if distributing the resulting quirc binary.

The [successful-read pipeline comparison](../../reverse-engineering/rkaiq/qr-successful-pipeline-comparison.json)
now brings every decoder to 24/24 using the **same original four real camera
frames**, six attempts each. Every decoder follows a fixed sequence: full raw
frame, center crop `(160,120)-(480,360)`, then full-frame hybrid local threshold.
It stops at any decoded symbol, independently of the known public-target
comparison. No per-frame choice of settings or replacement synthetic images
is used. Both the raw failures above and the successful pipelines are retained.

| Reader | Raw reads | Pipeline reads | Median total | P95 total | Median CPU | Successful stage(s) |
|---|---:|---:|---:|---:|---:|---|
| ZXing-C++ | 24/24 | 24/24 | 35.1 ms | 37.7 ms | 33.9 ms | Raw: 24 |
| quirc float | 0/24 | 24/24 | 49.5 ms | 117.8 ms | 47.1 ms | Crop: 18; local threshold: 6 |
| quirc default | 0/24 | 24/24 | 54.5 ms | 127.8 ms | 52.2 ms | Crop: 18; local threshold: 6 |
| ZBar/pyzbar | 0/24 | 24/24 | 174.8 ms | 210.8 ms | 172.6 ms | Local threshold: 24 |

These are prototype pipeline times with capture stopped. They include failed
earlier stages, preprocessing, native process startup, input loading and
temporary I/O; source frames and initial Python imports precede the timer.
CPU includes child processes. They differ intentionally from decode-only times
above and do not establish final app FPS. All four readers also pass the same
binary fixtures (9/9 each, including NUL and all 256 byte values).

The shared final preprocessor is ZXing's `HybridBinarizer`, without its QR
reader. Successful quirc/ZBar pipelines therefore depend on that additional
component; they are not unassisted quirc/ZBar measurements. Reader-only RSS
figures above exclude the Python parent and preprocessing worker, so they
cannot be presented as total pipeline memory. The crop favors the central
scan area; whole-frame stages remain first and last. Broader independent
framing/lighting and physical animated-target acquisition remain open.

`python/qr_success_pipeline_benchmark.py` reproduces the cascade on the device
using `--directory PRIVATE_LUMA_DIRECTORY --native-directory NATIVE_DIRECTORY
--report NEW_JSON`. Its native directory contains `reader`, `quirc-default`,
`quirc-float`, and `threshold` (the built `qr-native-threshold` executable).
`mise run camera:qr:native-build` builds the threshold helper as well.

Rebuild the pinned QR-only ZXing 3.1.1 benchmark with
`mise run camera:qr:native-build`. It uses mise Zig 0.15.2 as a C/C++
cross-compiler for Cortex-A7/musl; no application code is written in Zig and no
board system libraries are replaced. The ignored `.tools` checkout preserves
upstream licensing. `python/qr_device_benchmark.py` alternates decoder order
across two rounds; the native reader accepts `LUMA WIDTH HEIGHT ITERATIONS`
and an optional expected-payload file for byte-exact synthetic checks.
`reverse-engineering/rkaiq/scripts/qr-binary-fixtures.py --output NEW_DIRECTORY`
generates the public binary fixtures using Pillow and qrcode. Keep real camera
frames private and stop the camera owner before repeating the timed comparison.

`python/qr_pipeline_hardware_check.py --config CONFIG --report NEW_JSON`
compares preprocessing on identical real frames. It owns the camera, so stop
the preview owner first. Optional `--compare-sharp` changes only the diagnostic
child's module selection. That A/B attempt produced no frames and remains
inconclusive. Images are not saved unless `--private-frame-directory` is
explicitly supplied; keep such frames under private ignored storage.

For an offline decoder comparison on those private lossless PNGs:

```sh
mise exec -- uv run --python 3.13 --with pillow --with zxing-cpp==3.1.1 python firmware/rkaiq-rs/python/qr_decoder_desktop_check.py --input-directory PRIVATE_PNG_DIRECTORY --report NEW_JSON
```

### Dark-history AWB correction (0.0.38)

Development 0.0.38 fixes the identified dark-history error: all-zero rounded
brightness history legitimately produces NaN variance in the original ARM
routine. Rust had preserved that value but incorrectly rejected it in damping
adaptation. It now follows the original ordered comparison, while retaining
finite checks on gains and calibrated parameters. Eighteen exceptional-value
cases and 32 zero-brightness diagnostic replay frames match native execution.
[Root-cause/fidelity evidence](../../reverse-engineering/rkaiq/awb-dark-variance-equivalence.json).

The earlier nonfinite recovery guard also remains: rejected transactional
updates retain previous state/gains while AE and capture continue. Its
[historical hardware recovery](../../reverse-engineering/rkaiq/awb-nonfinite-recovery-hardware-validation.json)
is separate from the final corrected algorithm. Physical dark/light changes
on the exact final runtime still need qualification.

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

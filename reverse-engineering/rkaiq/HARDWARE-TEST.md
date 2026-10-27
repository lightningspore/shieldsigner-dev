# First camera session

Current **0.0.31-dev source** has passed bounded live AE + AWB captures, including FAST-to-normal time sharing, on
the SC3336/Luckfox. The opt-in `auto-awb-frame-sc3336` command and its remaining
runtime limitations are documented in [AWB.md](AWB.md#rolling-snapshot-ownership-beyond-short-captures-2026-10-27).
Current live syntax takes the six path arguments and optional `--frames 33..3600`.
It derives scale from the single-camera binding, ISO from associated real gains,
and brightness from the same-frame AE pre-result.
The frozen **0.0.30-dev ZIP described below is unchanged** and does not contain
this new command. Build current source with `mise run camera:rust:arm` to use it.


Kit **0.0.30-dev** adds the bounded `auto-frame-sc3336` automatic-exposure command with fixed calibrated white balance. Its six ARM adapter scenarios pass with simulated devices; the new automatic command is not yet qualified on the camera. The matching full IQ profile and actual device inventory remain required.

This kit is an **experimental partial reconstruction**. It supplies recovered Rust numerical/control components and a camera diagnostic. It does not replace `librkaiq.so` or the existing image's startup/service scripts. No firmware flash is needed for these tests.

## Kit contents

- `bin/camera-probe`: standalone static ARMv7 Linux executable, no RKAIQ dependency.
- `bin/numeric-fixture`: the numerical reconstruction with a line-based test runner.
- `bin/frame-preview`: grayscale PGM conversion for supported capture formats.
- `fixtures/inputs.txt` and `fixtures/expected.txt`: 9,050 cases with reference results captured from the original ARM machine code under Unicorn.
- `run-numeric-test.sh`: run and compare the numerical corpus on the device.
- `lifecycle-fixtures/`: 100 call traces from the original daemon, replayed through the Rust orchestration core. This does not execute a complete Rust ISP backend.
- `binding-fixtures/`: 1,000 controlled sensor-selection cases. This checks the selector, not live inventory discovery.
- `statistics-fixtures/`: 100 full-ISP32 AWB buffer comparisons against original translator instructions.
- `ae-grid-fixtures/`: 1,000 AE0 correction/weighted-mean cases, all six modes and both luma ranges, compared with original ARM instructions.
- `ae-histogram-fixtures/`: 1,000 complete 64/256-bin correction/bypass cases compared with the original ARM helper.
- `ae-big-grid-fixtures/`: 1,000 complete 15×15 correction records, subwindow sums and weighted means compared with original ARM instructions.
- `sensor-linear-fixtures/`: 1,000 original-reference sensor-write sequences, including injected failures. Fixture replay does not write any camera controls.
- `exposure-fixtures/`: 1,000 gain/time code conversions against original RKAIQ and pinned uClibc math instructions. Replay does not program the camera.
- `sensor-descriptor-fixtures/`: 1,000 full descriptor/query-order cases, including optional-query failures, compared with original ARM code.
- `iq-calibration-fixtures/`: 100 SDK-profile load/conversion cases; the kit also includes a derived SC3336 exposure-only reference and an explicitly synthetic sensor snapshot.
- `ae-decision-fixtures/`: 1,000 histogram-driven exposure proposals and saturation flags compared with the original ARM solver. Fixture replay does not run an automatic sensor-control loop.
- `ae-damping-fixtures/`: 1,000 history-based damping coefficients and diagnostic writes compared with original ARM code. Replay does not configure the ISP or run automatic exposure.
- `isp-pipeline-fixtures/`: 1,000 native-reference ISP pad setup traces, including adjusted crop responses and failure ordering. Replay uses a recorded backend and does not configure devices.
- `isp-black-level-fixtures/`: 1,000 native-reference ISP32 BLS parameter blocks, masks and cache results; replay does not submit parameters to hardware.
- `isp-demosaic-fixtures/`: 1,000 selected-value-to-hardware cases plus 1,000 direct hardware-to-kernel packing cases. Replay does not select tuning from IQ or configure devices.
- `demosaic-selection-fixtures/`: 1,000 explicit-scene JSON/ISO-to-hardware/kernel cases, including 100 SDK SC3336 profile cases. `reference/sc3336-demosaic-subset.json` records its source scene and hash; this is a component reference, not complete startup IQ.
- `parameter-queue-fixtures/`: 1,000 metadata-output lifecycle/state traces. Replay uses recorded device/pool boundaries and performs no queue writes.
- `ae-measurement-fixtures/`: 1,000 AE-grid plus 1,000 histogram configuration cases, compared with native dispatcher branches. These contain deliberately wide patterns and are not complete/qualified initial IQ records.
- `manifest.json`: artifact sizes/hashes, target and source-file hashes.

Use a development microSD/image and a connected compatible camera. Keep the existing working camera setup available for baseline comparison. The kit makes no persistent boot changes. Commands below use `/tmp` for test output; check available space first because full-resolution Bayer frames can be several MB.

## 1. Check the processor and recovered functions

Unpack the kit into a writable directory on the Luckfox. From that directory:

```sh
chmod +x bin/* run-numeric-test.sh
./bin/camera-probe --version
./run-numeric-test.sh /tmp/shieldsigner-rust-results
```

**Numerical pass:** `self-test` succeeds and all 9,050 output lines exactly match the reference file. A numerical pass does not mean the camera or complete ISP port works.

## 2. Inventory the actual camera

```sh
./bin/camera-probe list > /tmp/shieldsigner-camera-nodes.json
cat /tmp/shieldsigner-camera-nodes.json
```

The report lists device capabilities/current formats, media-entity names and their `/dev` nodes, and any running `rkaiq_3A_server`/`rkipc` processes. Use this report to choose an actual capture node; `/dev/video0` is an example, not a guaranteed correct path. Statistics/parameter nodes are not image capture endpoints. The media graph should identify the attached sensor, such as SC3336, and expose sensor/CIF/ISP endpoints. Each media device now includes pad/link descriptors, `complete`/`errors`, and `sensorPaths` from enabled data links. Inspect errors before using path results. These are entity-level paths within one media device; separate CIF/ISP graphs and internal routing may remain unresolved.

If no camera nodes appear, preserve the report and inspect module loading, device tree, cable orientation and the sensor probe log. The Rust probe does not load kernel modules or create missing links.

## 3. Capture a baseline, then test with vendor processes stopped

First record a frame through the existing application/camera path and note lighting, sensor, resolution and whether exposure adjusts. Preserve a baseline rather than changing the working image.

For the independent probe test, stop the application's capture session and camera services through the image's normal controls. On our pinned image the ISP service is `/usr/bin/rkaiq-service`; a temporary `rkipc` bootstrap may also have been started. Confirm the inventory no longer lists those processes. Do not run the Rust probe concurrently with another program streaming from the same endpoint.

Choose the desired node from the report and use a **new output filename**:

```sh
./bin/camera-probe capture /dev/video0 /tmp/shieldsigner-frame.raw \
  --require-no-rkaiq --buffers 1 --warmup 2 --timeout-ms 3000
```

This retains the node's current format. It writes the last completed frame and `/tmp/shieldsigner-frame.raw.json` with format, plane extents, sequence, timestamp and vendor-process observations. It refuses existing output files and rejects driver error flags, empty buffers, invalid bounds and timeouts. It supports one- and multi-plane MMAP endpoints.

If the node supports a smaller format, an explicit request can reduce memory pressure:

```sh
./bin/camera-probe capture /dev/video0 /tmp/shieldsigner-small.raw \
  --width 640 --height 480 --fourcc NV12 --require-no-rkaiq
```

Use only a format advertised for that endpoint. The driver may adjust the request; the JSON records the **returned** format. A raw Bayer CIF endpoint may require its sensor's native resolution and may not support NV12 or scaling.

**Frame-capture pass:** a completed frame with nonzero payload is saved, with a matching format/metadata record and no error flag. Inspect it next. This is not yet an end-to-end RKAIQ replacement pass.

An empty vendor-process list proves only that these processes were absent at the observed time. The image may already have initialized the graph/ISP using them at boot. A future cold-start test with the vendor services/bootstrap disabled is required to establish independent initialization. The current kit does not change those boot settings.

## 4. Inspect the image

```sh
./bin/frame-preview /tmp/shieldsigner-frame.raw \
  /tmp/shieldsigner-frame.raw.json /tmp/shieldsigner-frame.pgm
```

The tool supports luma from NV12/NV21 and planar/multi-plane YUV variants, common packed YUV, GREY, and common packed/unpacked Bayer RAW10/12/16 formats. Unsupported formats fail explicitly. Output is an uncalibrated 8-bit grayscale PGM. Bayer is reduced by 2×2 binning; no vendor demosaic, white balance or auto-exposure is applied. It prints minimum/maximum/mean pixel values. Preserve the raw capture and metadata alongside the preview.

Copy the PGM to the Mac for viewing. A native Mac converter is also supplied under `host/` when the kit is built on this Mac. Use a known printed test QR and try a bright/dim scene. Record whether the image is clipped, dark, patterned, corrupted or stable. Frame capture/preview alone does not prove QR decoding reliability.


## Observe driver stream events

The original daemon waits on **rkisp-input-params**, not the image-capture node. Locate that entity's `/dev/videoN` path in the media inventory. In one terminal, run:

```sh
./bin/camera-probe events /dev/videoN --timeout-ms 10000 --count 8 > /tmp/shieldsigner-stream-events.jsonl
```

Start and stop a camera session using the existing application in another terminal while the monitor is active. The monitor subscribes on its own file descriptor, prints JSON lines, and ends after ten seconds or eight events. It does not start/stop the ISP, apply parameters, or change boot configuration. A timeout with zero events is a recorded observation, not proof of a defective camera; confirm the entity/node and that a session actually started during the window. Preserve this log with the inventory. This command currently models the pinned ARM32 event ABI only.

## If capture fails

- **REQBUFS/STREAMON returns ENOMEM:** record format size, buffer count, `/proc/meminfo` (especially CMA) and the kernel log. The 64 MB Mini and current CMA reservation can be limiting. A full-resolution raw frame may need much more memory than a scaled ISP frame. Do not infer that the port works or that the sensor is faulty from this error alone.
- **EINVAL / unsupported format:** preserve inventory, requested/returned format and exact error. Verify endpoint and single-/multi-plane type.
- **Timeout / no frames:** record media topology, sensor probe, streaming ownership and kernel log. Existing sensor/media/ISP setup may still be required.
- **Image only works after vendor startup:** record this dependency. It is evidence that independent graph/ISP initialization is not complete.
- **Unexpected ioctl failure:** preserve architecture, kernel version and exact error. ARM32 timestamp/structure ABI is explicitly modeled, but real driver compatibility is still being tested.

Provide the numerical results, node inventory, raw frame + JSON + PGM (if available), sensor model, image/kernel versions, which services were running before/after, and relevant camera/CMA kernel logs. Restart the normal camera service/application or reboot the unchanged development image to restore its normal startup sequence.

## Saved ISP statistics

`camera-probe stats SAVED_STATISTICS.raw` decodes a single saved buffer from the pinned **full ISP32 statistics endpoint**, printing JSON with frame/parameter IDs, valid AE grids/histograms and AWB blocks/sums/histogram. It accepts 13,036 payload bytes or the driver's 13,040-byte aligned allocation. Measurement-validity bits gate each output; invalid measurements appear as null.

This command is the offline decoder; the bounded queue reader is described below. Do not give it an image frame or a buffer from a different ISP. Length alone does not establish provenance. Processing synchronization and the automatic-control loop remain unfinished. See `research/STATISTICS.md` in the kit for supported fields and validation limits.

## Capture ISP statistics

The `rkisp-statistics` entity in the inventory identifies the metadata-capture node. Use its reported path, not the input-parameters or main image node. The format must be `RK1S` with a 13,040-byte buffer on our pinned full-ISP32 target. `capture-statistics` checks both before requesting buffers. It always refuses detected vendor camera processes; use the image's normal controls to stop them first. An application may hold the statistics queue even if no daemon process is shown, in which case ownership/busy errors must be resolved before proceeding.

The statistics reader subscribes to the **existing measurement stream**; it does not start the image pipeline or program measurement windows. After recording a working baseline, stop the application and vendor services. Then, in terminal A:

```sh
./bin/camera-probe capture-statistics /dev/videoSTATS /tmp/shieldsigner-statistics.raw \
  --buffers 2 --warmup 0 --timeout-ms 10000
```

Within that ten-second window, start an image stream in terminal B using the actual main capture node and its retained supported format:

```sh
./bin/camera-probe capture /dev/videoMAIN /tmp/shieldsigner-statistics-image.raw \
  --buffers 2 --warmup 10 --require-no-rkaiq
```

`videoSTATS` and `videoMAIN` are placeholders: replace them with different paths from the inventory. Use new output names on retries. A third terminal is not required. The two commands own separate queues. The pinned statistics driver needs at least two MMAP buffers; the tool enforces that and permits up to four. Deadlines apply per dequeued buffer, so using zero warmup gives a single bounded wait.

On success the statistics reader saves one complete buffer plus `.json` containing returned format, frame/parameter IDs, measurement-validity mask, V4L2 sequence/timestamp, byte count and vendor-process observations. Decode it:

```sh
./bin/camera-probe stats /tmp/shieldsigner-statistics.raw > /tmp/shieldsigner-statistics-decoded.json
```

Preserve raw data and both JSON files even when some decoded measurement groups are null. A zero validity mask means those measurements were not marked valid; raw data alone does not prove AE/AWB is working. `EBUSY` usually indicates another queue owner; `ENOMEM`/`EINVAL`, timeout and driver error flags must be recorded with node inventory and kernel logs. Neither command installs firmware or fixes missing sensor/media/ISP initialization. If both queues work only after vendor startup, record that dependency. Real metadata-queue capture remains unvalidated until this hardware session.

## Read the sensor descriptor

Find the actual sensor entity (for example, SC3336) and its `/dev/v4l-subdevN` path in the media inventory. Run:

```sh
./bin/camera-probe sensor-info /dev/v4l-subdevN > /tmp/shieldsigner-sensor-info.json
```

Replace `N` using the inventory. This command opens the node read-only and uses only get/query ioctls. It reads the active pad-0 format, minimum blanking, frame interval with pixel-rate fallback, minimum exposure, and optional noise/conversion-gain information. It does not stream, set controls or alter formats. Optional unsupported queries remain in the query trace and do not invalidate the whole descriptor.

The result includes native descriptor bytes for reproducible comparison, readable timing/format fields, clock float bits and per-query errors. Descriptor line/frame periods use **minimum** blanking rather than current blanking; they must not be presented as a measurement of current exposure timing. Preserve this file with the raw/statistics captures. If a required query fails, save stderr; do not guess descriptor fields to make a live control loop run. Actual driver-query compatibility still needs validation on the camera.

## Offline exposure plan using real sensor information

After `sensor-info` succeeds, combine its saved JSON with an IQ JSON profile whose sensor resolution matches the active sensor. The kit includes the **exposure-only** subset of the pinned SDK's `sc3336_CMK-OT2119-PC1_30IRC-F16` profile:

```sh
./bin/camera-probe exposure-plan reference/sc3336-exposure-subset.json \
  /tmp/shieldsigner-sensor-info.json 0.01 2
```

This converts an explicitly requested 0.01 seconds and real gain 2 using the loaded profile. It prints gain/shutter codes, source timing, profile ranges and update delays. It opens **no device** and writes no settings. Default frame length is the descriptor minimum; an optional final frame-line count may be supplied, but cannot be smaller than that minimum. Higher-level maximum-time/driver-limit checks and scheduling are still missing, so this output is a conversion report, not a ready-to-run automatic controller. The SC3336 reference now reports DCG mode -1 because DCG is disabled.

On the Mac, `host/camera-probe-macos-arm64` runs the same offline command against copied JSON files. To inspect the output before the camera session, use `examples/synthetic-sensor-info.json`; that file is explicitly fabricated test input and must not be mistaken for a hardware measurement. Linux device-access commands are unavailable in the Mac executable. Original full IQ JSON/BIN and vendor libraries are not bundled; the reference contains only functional exposure calibration fields and source attribution. See `research/CALIBRATION.md`.

## Manual sensor-write adapter test

This is the first kit command that **sets sensor controls**. It does not flash firmware or install a service. Start from the existing working camera setup, retain a baseline frame and `sensor-info` report, stop the camera application/vendor services, and use the sensor subdevice identified in the inventory. Keep other control writers out of this test; the command refuses the two known vendor daemon names but cannot establish exclusive ownership of the sensor.

Use explicitly reviewed frame length and gain/shutter codes, such as those produced by the offline plan after checking the driver's control limits:

```sh
./bin/camera-probe apply-linear /dev/v4l-subdevN FRAME_LINES ANALOGUE_CODE 0 SHUTTER_CODE \
  > /tmp/shieldsigner-sensor-write.json
```

Replace all placeholders with the actual node and numeric codes. For the pinned SC3336, leave the digital code at **0** and omit the optional DCG argument; its default **-1** skips conversion-gain programming. Do not copy a zero from older planner versions into that optional argument: explicitly passing 0 sends a conversion-gain ioctl. The offline planner now reports -1 for the disabled-DCG profile.

The driver accepts gain codes from 128 to 99,614, while the SDK profile can produce 99,615 at its upper end; do not assume that every conversion result passes driver validation. Frame length must also support the requested integration time, and the command does not add an AE policy to choose those values. It reads current descriptor minima, sets VBLANK first, then the optional DCG operation, analogue gain, optional digital gain and optional exposure, stopping on the first failure.

Preserve stdout JSON and stderr on failure. The JSON lists attempted writes, accepted frame length, partial effects and control readback/ranges. It returns a nonzero exit code when programming stops, with no rollback of earlier accepted controls. Driver readback may reflect cached state while the sensor is powered down; capture a subsequent image to verify actual behavior. Record whether a normal camera restart restores the baseline and keep the development image available for restoring normal startup. This command does not perform an AE loop, frame-delay scheduling or ISP/media initialization, and its real device path has not yet been validated.

## Parameter submission transport (requires a complete record)

This is a separate experimental step. **The kit does not ship a fully qualified initial ISP configuration.** Version 0.0.29 can generate the experimental fixed first-frame configuration documented below. Do not use per-module fixtures, the functional demosaic JSON subset or an arbitrary zeroed buffer as the input record. The baseline capture/descriptor tests above remain the useful first hardware session.

Once a complete, reviewed `isp32_isp_params_cfg` record is available, use `camera-probe list` to identify the RK1P metadata-output node and run, for example:

```sh
./bin/camera-probe submit-parameters /dev/videoN complete-initial-isp32.bin \
  --timeout-ms 3000 --hold-ms 60000
```

It requires known vendor processes to be stopped and makes no persistent boot changes. The first JSON event indicates dequeue, not verified image-frame application. While the parameter stream is held open, a separate terminal can attempt image/statistics capture on the appropriate other nodes. Normal parameter stream-off disables/clears configuration, so finishing this command can affect capture still in progress. Preserve its final JSON report and actual frames/errors. [Exact behavior, ABI, first-buffer semantics and remaining limits](PARAMETERS.md).

### First-frame parameter generator (0.0.29)

Kit 0.0.29 provides an offline command requiring the full matching IQ profile:

```sh
camera-probe make-initial-parameters sc3336_CMK-OT2119-PC1_30IRC-F16.json initial.bin > initial-report.json
```

It selects scene 0/0 explicitly and produces the full 11,145-byte kernel record.
The checkpoint uses the profile's constant BLC tables, ISO derived from initial
exposure gains, recovered demosaic selection/packing, normalized first-frame D50
WB gains, gamma curve, and explicit profile CSM/CGC values. Other ordinary ISP
modules and VSM are disabled; no mesh buffers or imported file descriptors are
required by these selected blocks. Nonconstant BLC tables are rejected pending
integration of their recovered selection path. The output file must not exist.

This is an experimental fixed first-frame configuration, **not complete RKAIQ
initialization or an automatic 3A controller**. The JSON reports the requested
sensor exposure (3 ms and gain 1 for the pinned profile), but this command does
not apply it. Queue ownership, sensor exposure programming and image startup
must still be coordinated. Do not close the parameter queue before starting the
image stream: STREAMOFF clears the driver's saved first configuration. No
vendor-free frame has yet been demonstrated.

Reproduce offline checks with the release host binaries built:

```sh
uv run --python 3.13 reverse-engineering/rkaiq/scripts/initial-parameters-check.py
uv run --python 3.13 --with unicorn==2.1.4 --with pyelftools==0.32 python reverse-engineering/rkaiq/scripts/isp-color.py
```

The first check covers assembled masks, stage-1 black level, gamma values,
malformed profile rejection and output collision protection. The second compares
the selected gamma/CSM/CGC dispatcher branches against original ARM instructions,
including all unrelated parameter bytes. Neither proves complete startup parity
or image quality.

### Development combined parameter/image capture

After configuring the media pipeline and applying the intended sensor exposure,
the development command keeps the parameter queue alive through image capture:

```sh
camera-probe capture-with-parameters /dev/videoPARAM initial.bin -- /dev/videoIMAGE frame.raw --fourcc NV12 --warmup 2 --timeout-ms 10000 > capture-events.jsonl
```

Replace both device placeholders using actual inventory. Parameter and image
nodes must be distinct character devices. The command refuses known vendor
camera processes and existing image/metadata outputs. It submits one full
parameter record, waits for its completion, then calls the image-capture path
with the parameter FD, mappings and STREAMON still held. Image buffers default
to four for this command. Image capture returns and closes its resources before
the parameter queue is stopped. Capture errors also pass through parameter
cleanup; stdout records parameter and image lifecycle events, including cleanup
errors. Keep stdout, stderr, `frame.raw.json`, raw bytes and kernel logs.

A parameter completion is not proof that pixels used those settings. Some
hardware paths may require a different startup order or raw TX/RX streaming;
this combined positive path has not yet run on the actual board. It does not
configure the graph, program exposure, stream raw readback endpoints, run
statistics/automatic 3A or prove cold startup. Those are still required work.
This command first appears in kit 0.0.29.

Run the static ARM CLI rejection checks with:

```sh
uv run --python 3.13 reverse-engineering/rkaiq/scripts/combined-capture-check.py
```

### Development linear CIF DMA-BUF bridge

The development source adds the raw bridge around combined image capture:

```sh
camera-probe capture-cif-with-parameters /dev/videoPARAM initial.bin /dev/videoRAW_TX /dev/videoRAW_RX /dev/v4l-subdevISP -- /dev/videoIMAGE frame.raw --fourcc NV12 --timeout-ms 10000 > capture-events.jsonl
```

All five endpoint paths must identify different actual devices. Configure links,
raw formats and sensor exposure first. This command currently accepts only
**single-plane unpacked RAW10 Bayer** TX/RX with matching dimensions, FourCC,
stride and sizeimage. It allocates at least four TX MMAP buffers, exports their
DMA-BUF descriptors, and allocates RX import slots. It does not map/copy the raw
pixels. Multiplane raw endpoints, packed RAW10, USERPTR and fallback copies are
rejected/unsupported, rather than silently guessed.

After the parameter record completes, it starts TX then RX and starts image
capture while a scoped worker pumps the raw bridge. Each dequeued TX index is
queued into its matching RX import slot. Only after RX QBUF succeeds does the
worker issue the linear readback trigger with the source sequence/timestamp.
A TX buffer is requeued only when its corresponding RX completion arrives.
The worker polls nonblocking DQBUF with a 1 ms backoff and a 10 s no-progress
limit. It stops and joins after image capture, releases RX imports, closes
exported descriptors and releases TX allocations. The parameter queue remains
open around that entire operation. The `raw-bridge-finished` event reports
completed raw frames, errors and cleanup errors.

The first trigger uses one readback pass; subsequent fixed-startup triggers use
zero extra passes. Before streaming, the ISP FD subscribes to FRAME_SYNC events.
The worker drains events into a bounded 64-frame cache and looks up the raw
frame sequence using the native signed-negative-ID-to-zero rule. It uses the
matched SOF timestamp in nanoseconds; a missing match uses zero, matching the
original caller's initialized fallback. `sofMatches` and `sofMissing` in the
final event expose this distinction. The cache bound and nonblocking drain are
explicit Rust service choices; no native ordered-map equivalence is claimed.
Automatic 3A, calibrated frame-delay
scheduling, hardware restart and full native queue-controller equivalence remain
unfinished. **No successful positive raw bridge/device path has been tested.**
ARM compilation, kernel ABI assertions and CLI rejection tests establish only
their stated offline coverage. Preserve errors and driver logs if STREAMON,
DMA-BUF import/export, trigger or capture fails; do not call it functional based
on compilation or parameter completion alone.

### ARM raw-bridge lifecycle simulation

`mise run camera:rust:raw-bridge-check` cross-compiles the camera diagnostic's
Rust test executable and runs its actual bridge preparation, worker and cleanup
under ARM Linux emulation. Only its ioctl boundary is replaced by a test-only
scripted driver; production builds do not include that replacement. Exported
buffer descriptors are real duplicated FDs whose ownership is checked during
RX queueing. The five scenarios cover a successful raw frame with matching SOF,
RX STREAMON failure, RX QBUF failure, trigger failure and a corrupted RX buffer.
The test asserts RX queue → trigger → RX completion → TX reuse order, no TX reuse
on failures, trigger suppression on failed queueing, and resource-release order.
[Recorded results](raw-bridge-validation.json) identify the test executable hash.

This is stronger coverage of userspace lifetime behavior than CLI rejection
checks, but it does not simulate the real kernel's internal buffer handling or
prove the selected startup order on hardware. It also does not exercise the
surrounding metadata/image capture paths or compare the complete native C++
queue controller. Keep those distinctions when assessing readiness.

### One-command fixed first-frame startup (0.0.29)

After filling the explicit linear CIF pipeline plan from actual device inventory:

```sh
camera-probe first-frame-sc3336 pipeline.json sc3336_CMK-OT2119-PC1_30IRC-F16.json /dev/videoPARAM /dev/videoIMAGE frame.raw > startup-events.txt 2> startup-errors.txt
```

The command combines read-only graph preflight, calibrated parameter generation,
actual graph/format configuration, active sensor timing queries, initial exposure
conversion, driver control-range checks, sensor programming, parameter submission,
raw bridging and image capture. It supports the SC3336 2304×1296 profile with DCG
disabled and one explicit CIF TX/RX pair. It sets the requested image format to
NV12 and uses the combined path's four image buffers, two discarded warmup frames
and 10 s per-frame timeout. It does not enable automatic exposure/white balance.

It leaves `frame.raw.initial.bin` and `frame.raw.initial.json` for inspection,
then writes `frame.raw` and its `.json` capture metadata on successful capture.
Existing outputs are rejected. Read-only graph preflight failure produces no
startup artifacts. A later failure can leave the initial artifacts and already
accepted graph/sensor settings; there is no automatic settings rollback. Logs
contain structured records, some formatted over multiple lines, so treat stdout
as a text log rather than a strict JSONL stream.

The initial exposure is derived from the profile and freshly queried sensor
line/frame timing. Both shutter and combined gain codes must fit active driver
control ranges/steps. Digital control code zero skips SC3336's unsupported
separate digital-gain control, and DCG -1 skips conversion-gain programming.
After programming, queue/capture startup uses the commands documented above.
A driver acceptance/readback still does not prove the requested exposure reached
the saved frame; verify that on the camera.

`uv run --python 3.13 python reverse-engineering/rkaiq/scripts/first-frame-check.py`
executes five static ARM preflight rejection cases, including a real nonsensor
ioctl failure. The full positive startup sequence has not yet run on hardware. The following
development test exercises its userspace path with simulated device boundaries. The goal remains usable independent frames,
QR validation and the required automatic controller, not a passing preflight.

### Full userspace startup simulation (0.0.30-dev)

Run `mise run camera:rust:first-frame-sequence-check`. It builds and executes the
actual ARM camera diagnostic test executable, including `first-frame-sc3336`,
using the SHA-pinned full SC3336 profile. Test-only boundaries supply ioctl
responses, readiness and anonymous image/metadata mappings. The real Rust
startup code performs graph setup, active timing conversion, driver-range
checks, sensor writes, parameter queue submission, raw bridging, three image
dequeues and artifact writing. Assertions verify parameter readiness before raw
startup and image → raw → parameter shutdown order. The test is explicitly
ignored by default and enabled only by this fixture runner.

[Recorded validation](first-frame-sequence-validation.json) identifies the test
binary and coverage. Saved pixels are zero-filled simulated memory. This is
userspace integration evidence, not sensor output, QR decoding, driver fidelity
or cold-start hardware evidence. Production builds contain none of these
simulated boundaries. Frozen kit 0.0.29 is unchanged.

### Optional AE measurement configuration (0.0.30-dev)

```sh
camera-probe make-initial-parameters SC3336_FULL_IQ.json initial-ae.bin --ae-measurements > initial-ae-report.json
```

This offline option adds the recovered AE and histogram selected configuration
to the full initial ISP record. It derives windows from `sensor_calib.resolution`
and the explicit first scene's AE calibration, applies the native full-range
coefficients and weighted histogram 1/3 grids, and uses the verified selected
record→kernel serializers. Active ISP geometry must match the profile. The
report identifies enabled measurements and keeps `automaticExposure:false`.
The checked profile subset requires enabled auto/Y-mode/full-range AE, nonzero
weights and windows not requiring native calibration correction.

The native comparison now runs `AecUpdateConfig` under update mask 0x80 through
normal return for the selected-measurement cases. Later histogram-3 publication
is included, not merely the earlier histogram-1 checkpoint. This does not prove
full private AE-state equivalence or subsequent frame-control behavior.

Host assembly checks verify module masks, histogram grid routing and preservation
of every nonmeasurement block. Actual ARM generation must match the host blob
byte-for-byte. This option does not open a statistics queue, choose exposure,
schedule sensor updates or alter `first-frame-sc3336` defaults. Persistent
statistics capture with image/raw/parameter streams and feedback integration are
still required before automatic exposure is available. Frozen kit 0.0.29 does
not include this development option.

### Persistent statistics with first-frame capture (0.0.30-dev)

Append the actual RK1S metadata-capture node to the first-frame command:

```sh
camera-probe first-frame-sc3336 pipeline.json SC3336_FULL_IQ.json /dev/videoPARAM /dev/videoIMAGE frame.raw /dev/videoSTATS > startup-events.txt 2> startup-errors.txt
```

This optional sixth argument selects the measurement-enabled initial record and
starts a separate persistent statistics queue before parameter/raw/image startup.
A readiness barrier requires successful statistics STREAMON before camera
capture proceeds. The queue stays open through image, raw and parameter teardown,
then stops and releases its mappings/buffers. The default five-argument command
retains its prior fixed first-frame configuration without AE measurements.

The statistics worker uses two MMAP buffers (accepting bounded driver allocation
of 2–8), nonblocking dequeues, an interruptible 1 ms backoff and a 10 s no-progress
limit. It validates layout, buffer index/type/memory, error flags and payload
bounds, copies 13,036-byte payloads or the driver's 13,040-byte aligned buffers,
and requeues each completed buffer. It saves the last buffer to
`frame.raw.stats.raw` and up to 256 recent frame headers to its `.json` sidecar.
Existing statistics outputs and aliases of the other camera nodes are rejected.
The report includes measurements, frame IDs, parameter IDs and cleanup errors;
a camera run with no received statistics returns an error. Partial artifacts
and already accepted settings may remain after failures.

This collects the inputs for feedback; it does not compute or apply automatic
exposure. A validity mask or matching-looking IDs are not proof of exposure/frame
association, and the report leaves that verification false. The full ARM
userspace simulation now covers both five-argument capture and this statistics
variant, verifying readiness/teardown order and saved artifact sizes. Its device
responses, pixels and metadata are synthetic. Real metadata delivery, validity,
frame correlation, restart and image quality remain hardware checks.

The development statistics sidecar's `recentFrames[].aeLinear` now contains
`weightedMeanQ8` (divide by 256 for luma), `weightedMeanLuma` and
`correctedHistogramCount` when the primary AE1/histogram1 pair is valid. These
values use the recovered native correction path and the initial submitted
parameter snapshot. `initialSnapshotAssociationVerified` remains false; a zero
histogram count is not usable exposure feedback. Invalid measurement flags or an
unsupported configuration are recorded as diagnostic status. No automatic
sensor writes are triggered by these fields. ARM integration tests verify the
synthetic metadata/report path; real frames and exposure association still need
hardware verification.

The measurement-enabled initial report and statistics sidecar also record
`initialTargetLuma`, currently 45 for the pinned SC3336 profile. Compare this
with measured `weightedMeanLuma` when inspecting a hardware run, while retaining
the unverified snapshot-association distinction. The target comes from the
recovered dynamic curve/bias branch using initial exposure settings. It is not
an automatic exposure decision and does not trigger sensor writes.

For the pinned fixed-50-Hz profile, the measurement-enabled initial report also
includes `routeTimeQuantumSeconds` (approximately 0.01 s). This describes the
recovered route timing quantum; `minimumShutterTimeDerived:false` makes clear
that it is not a computed minimum exposure. The current 3 ms first-frame setting
is retained. No flicker detector or automatic timing updates are enabled.


## SC3336 hardware observation — 2026-10-26

The ARM `0.0.30-dev` diagnostic ran on a Luckfox Pico (Linux 5.10.160).
The SC3336 sensor descriptor read successfully at 2304×1296, BG10, minimum
frame length 1360, line length 2800 and reported pixel clock 114.24 MHz.
A direct `/dev/video0` capture succeeded with no detected vendor camera
process before or after capture. This is **not cold-start proof**: vendor
`rkipc` had run earlier during boot.

The captured plane was 3,981,312 bytes with stride 3072. Although its FourCC
was BG10, it contained Rockchip compact contiguous little-endian 10-bit samples,
not unpacked 16-bit samples or MIPI RAW10 groups. A recognizable grayscale
preview was obtained; it was bright/clipped, with no QR qualification.
Use the explicit override for a capture known to use this memory layout:

```sh
frame-preview sensor.raw sensor.raw.json sensor.pgm --rockchip-compact-raw10
```

The override is never inferred from stride or FourCC. It accepts RAW10 Bayer
FourCCs only, preserves row padding and does 2×2 grayscale binning. Its tests
cover bit extraction across byte boundaries, padding and truncated input.

The combined Rust first-frame command did not reach streaming: querying DPHY
source-pad format returned EINVAL (use its supported sink pad), then switching
from the CIF online link to raw readback returned EBUSY. A subsequent attempt
to set CIF word-low-aligned memory mode stalled; new ADB shells stopped
responding although USB discovery still listed the device. Do not repeat that
mode change on an active pipeline. Hardware recovery and idle pipeline/link
ownership need checking before continuing ISP capture. No firmware was flashed
and no boot configuration was changed.

Private scene captures and logs remain under ignored
`dist/reverse-engineering/hardware-2026-10-26/`; they are not checked into Git.


### Input-link failure analysis

The pinned kernel's [`__media_entity_setup_link`](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/mc/mc-entity.c#L830)
returns EBUSY when a non-dynamic link changes while its source or sink has a
nonzero stream count. The failed operation was disabling
`rkcif-mipi-lvds:0 -> rkisp-isp-subdev:0`, not a failed image dequeue. Process
absence and an empty `fuser` result do not establish that this kernel count is
zero. The stalled device prevented checking the remaining stream owner/state.

The [`rkisp_subdev_link_setup`](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/platform/rockchip/isp/rkisp.c#L3198)
handler permits `INP_CIF` and raw-readback input bits together. Therefore the
next experiment should retain the existing CIF link and enable the required
raw-readback link only after establishing idle streaming state. Do not treat
these inputs as necessarily mutually exclusive. This is source evidence for
an experiment, not proof of successful capture with that graph.

The real CIF endpoint also advertised **multi-plane capture with one plane**;
the existing raw bridge requires the single-plane V4L2 API. Its endpoint API
handling must be extended before claiming that the combined bridge works on
this board. The captured BG10 FourCC did not imply unpacked storage: CSI
memory mode and returned plane geometry must also be tracked. Keep the working
compact capture mode during initial investigation rather than changing an
active device's memory mode. The saved local capture remains available while
the device is offline.


### Development bridge API follow-up

The raw bridge now selects capture/output API types independently from endpoint
capabilities. It accepts either the single-plane API or the multi-plane API
with exactly one image plane. Multi-plane QUERYBUF/QBUF/DQBUF use a live
`v4l2_plane` descriptor, plane lengths/bytes-used and the imported DMA-BUF fd;
EXPBUF and stream operations use the selected endpoint type. Nonzero data
offsets and additional image planes are rejected. Format comparison reads
stride/size from the appropriate API layout. Matching RAW10 FourCC does not
establish CSI memory-mode compatibility; matching storage layout is still an
explicit setup obligation.

The ARM driver-boundary test covers all four independent TX/RX API combinations,
each with success, RX-start failure, RX-queue failure, trigger failure and
corrupt RX completion (20 cases). FD export/import, scoped worker, TX retention,
SOF matching and teardown execute in the real bridge code. These are simulated
driver tests; the changed bridge has not yet captured on the physical board.
Run `mise run camera:rust:raw-bridge-check` to reproduce.


### CSI storage compatibility guard

Bridge preparation now issues read-only `RKCIF_CMD_GET_CSI_MEMORY_MODE` on TX
and `RKISP_CMD_GET_CSI_MEMORY_MODE` on RX before buffer allocation. Both must
report the same supported layout: compact (0) or word-high-aligned (2).
Mode 1 is rejected because the pinned UAPI describes different representations
across SoCs; no platform equivalence is assumed. Failed queries also abort.
The guard checks positive dimensions and that stride/sizeimage can contain the
RAW10 rows. It never sets either memory mode.

An additional ARM driver test returns different TX/RX modes and verifies
rejection before allocation, event subscription or streaming. The existing
20 lifecycle cases and both full startup simulations pass with matching
compact-mode query responses. Pinned-header ARM compilation independently
checks both query ioctl numbers. This prevents a known class of DMA layout
mismatches; it does not prove a positive device capture or cold startup.


The full ARM startup simulation also exercises compact RAW10 with both
single-plane TX and one-plane multi-plane TX, each with statistics disabled
and enabled (four scenarios). Its raw geometry uses the observed 2304×1296,
3072-byte stride and 3,981,312-byte plane extent. This tests pipeline-format
configuration/readback and bridge buffer descriptors together. Image/driver
responses remain synthetic and do not establish physical ISP capture.


### Reconnected-board follow-up

After a power cycle, ADB shells worked again. The image's normal
`/etc/init.d/S21appinit stop` eventually stopped `rkipc`; its shutdown was not
instant. Retaining the CIF link allowed graph setup, sensor writes and the
statistics queue to start. CIF REQBUFS requested four buffers but returned two
(type 9, MMAP). The bridge now accepts returned counts from 2 through 16 and
uses the smaller TX/RX count, exporting/queuing only that shared index range.
The ARM lifecycle mock now reproduces this two-buffer return.

The board reports a 12 MiB CMA pool. Full-resolution NV12 allocation failed
with ENOMEM after raw allocations. A separate combined capture at 640×480 with
two image buffers progressed beyond allocation. It exposed a nonblocking
SOF-event dequeue error: the pinned Linux
[`__v4l2_event_dequeue`](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/v4l2-core/v4l2-event.c#L35)
returns ENOENT when the event queue is empty. The bridge now treats that as
empty only in its event drain; image/raw-buffer errors are unaffected. The
ARM event mock exercises ENOENT after the first SOF.

With those fixes, raw inputs were queued/triggered (two SOF misses), but no RX
completion or ISP output arrived before the bounded timeout. No new image was
saved. Changing from `/dev/video17` (`rkisp_rawrd0_m`, middle exposure) toward
`/dev/video18` (`rkisp_rawrd2_s`, short/single exposure) was blocked by EBUSY.
The subsequent combined attempt reported EPERM and the kernel logged
`check rkisp_rawrd2_s link`; do not interpret that attempt as a valid configured
pipeline. Establish an idle graph with the correct linear input before retrying.
The board still answered diagnostic shells after these attempts. Captured logs
remain in the ignored local hardware artifact directory.


## Clean-boot ISP capture milestone

A subsequent controlled reboot skipped `/etc/init.d/S21appinit` for one boot.
The one-shot wrapper restored the original file before exiting; SHA-256
`61dcd3bdb6740771b296611ab83e3238f9bc45b2ca0ec5ae78b542085be592e5`
matched the saved original afterward, and the temporary backup was removed.
A boot marker and process/module inventory were retained locally. Ordinary
future boots retain their original behavior.

Skipping that service also skips its kernel module loader. The test loaded
available modules from `/oem/usr/ko` in this order: `rk_dvbm`,
`videobuf2-memops`, `videobuf2-common`, `videobuf2-v4l2`, `videobuf2-vmalloc`,
`videobuf2-cma-sg`, `sc3336`, `video_rkcif`, `video_rkisp`,
`phy-rockchip-csi2-dphy-hw`, `phy-rockchip-csi2-dphy`. Missing module files were
skipped because some components are built in. Then it wrote 1 to both CIF/ISP
`clr_unready_dev` parameters as the image's loader does. It did **not** run the
rest of `insmod_ko.sh`, load Rockit/its MCU firmware, or start `rkipc`/RKAIQ.

With the idle graph, the explicit plan selected sensor `/dev/v4l-subdev2`,
ISP `/dev/v4l-subdev3`, TX `/dev/video0`, RX `/dev/video18`, DPHY sink pad 0 and
CSI sink pad 0. It disabled middle-exposure entity 42's link and enabled
short/single-exposure entity 48's link to ISP entity 1, retaining the CIF link.
Entity/node numbers must be rediscovered on other images. Before startup,
`v4l2-ctl -d /dev/video11 --set-fmt-video=width=640,height=480,pixelformat=NV12`
selected the smaller image output; the existing first-frame command retains
that output size while configuring the sensor/ISP input at native resolution.

`first-frame-sc3336` then succeeded with parameter node `/dev/video20`, image
node `/dev/video11` and statistics node `/dev/video19`, using the matching full
SC3336 IQ file. It completed three raw transfers, saved a 460,800-byte NV12
image and two statistics frames. The preview is recognizable but dark at fixed
3 ms exposure. AE translation reported valid nonempty histograms. Four SOF
lookups missed and none matched; statistics/exposure association is not proven.
No automatic AE/AWB or QR-quality claim follows from this capture.

[Hardware result and image hash](hardware-first-frame-validation.json).
Detailed logs, raw images and previews stay in the ignored local artifact
directory. `isp-clean-upright.png` is the original luma preview rotated for
viewing; `isp-clean-contrast.png` additionally applies display-only autocontrast.
The command's conservative `coldStartProven:false` is unchanged; the separate
report records the controlled reboot evidence for this particular session.


### Capture-side SOF timestamps

A follow-up physical test selected the CIF CSI subdevice `/dev/v4l-subdev0`
as the FRAME_SYNC event source, independently from the ISP trigger subdevice
`/dev/v4l-subdev3`. The pinned kernel's
[`rkcif_csi2_event_inc_sof`](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/platform/rockchip/cif/mipi-csi2.c#L551)
queues capture-side frame IDs there. Ghidra's `CamHwIsp20::prepare` also selects
between CIF and ISP subdevice pointers for `RKSofEventStream`; using the ISP
node unconditionally was insufficient for this CIF path.

The combined command accepts an optional event source before its separator:

```sh
camera-probe capture-cif-with-parameters /dev/video20 initial.bin /dev/video0 /dev/video18 /dev/v4l-subdev3 --sof-node /dev/v4l-subdev0 -- /dev/video11 frame.raw --width 640 --height 480 --fourcc NV12 --buffers 2 --warmup 3 --timeout-ms 10000
```

The strict pipeline plan also accepts `"sof": "/dev/v4l-subdev0"`.
`first-frame-sc3336` forwards it; omitting it retains the old ISP-event-source
behavior. A separate source must be a character device distinct from raw,
image and parameter endpoints. It is opened before subscription/streaming and
held for the bridge lifetime; readback triggers still target the ISP node.

The explicit combined hardware test completed four frames with four SOF
matches and zero misses. The one-command startup then succeeded with three
completed transfers, four matches, zero misses and two statistics frames.
One additional input can be queued during image shutdown, so matches count
queued triggers rather than completed transfers. These prove timestamp lookup
on this board, not complete statistics/parameter/exposure delay association.

Color follow-up: the grayscale previews intentionally use NV12 luma only.
An NV12-to-RGB conversion showed color data with a pronounced purple cast;
color processing/white balance still need work. Display-only autocontrast is
not an ISP correction. Scene lighting may change during later tests because
the user plans to turn off the room light.


### Manual dark-room exposure test

After room lighting was reduced, a fixed 3 ms/1× capture had luma mean 24.02
and maximum 29/255. A requested 30 ms/1× capture had mean 25.21 and maximum 31.
The user then requested 500 ms. The existing recovered conversion selected
frame length 20416, gain code 128 and integration code 20400 using the reported
runtime descriptor; the driver accepted/read back exposure 20400 and VBLANK
19120. The subsequent raw/ISP capture succeeded with four completed frames,
four SOF matches and no misses. Its NV12 luma mean was 34.72 and maximum 51,
revealing room/monitor outlines. These are requested timing and control readback,
not independently measured optical integration duration. Gain stayed at 1×.
The purple cast remains; no color correction was applied to this test.
Private images/logs remain local under the hardware artifact directory.


### Raw/SOF/trigger/statistics correspondence

The bridge completion event now includes `recentFrames` (bounded to 256) and
`frameRecordsDropped`. Each queued trigger records buffer index, raw sequence,
trigger frame ID, SOF lookup ID/match/timestamp, source timestamp and RX
completion/sequence. Completion updates the newest in-flight record for that
buffer index, avoiding confusion when indices are reused. A final queued input
may remain incomplete when image capture stops; it is reported as such.

Two physical stream starts at fixed startup exposure produced statistics
frames 0 and 1 matching completed raw transfers, trigger IDs and CIF SOF IDs.
Both runs had four matched SOFs, no misses and three completed transfers.
The RX dequeue sequence was **zero for all completed transfers**: it is not
the raw/statistics frame key on this driver. The test reset exposure to the
startup 3 ms setting; it did not retain the earlier manual 500 ms experiment.
[Observed ID correspondence](frame-association-validation.json).

The reusable checker joins IDs and verifies completion/SOF evidence:

```sh
uv run --python 3.13 python reverse-engineering/rkaiq/scripts/frame-association-check.py startup-events.txt frame.raw.stats.raw.json --output frame-id-check.json
```

It rejects dropped traces, ambiguous/missing raw IDs, missing SOFs and
incomplete matching RX records. Those rejection paths were exercised by
mutating the successful local trace. The ARM bridge test verifies the trace's
frame/timestamp values and completion updates; full startup simulations pass.
The checker retains `frameExposureAssociationVerified:false`: matching IDs at
fixed exposure do not measure sensor update latency or prove the exposure and
parameter record that physically produced a frame. Exposure changes and
per-frame application evidence remain to be tested before live AE scheduling.


## One-shot shutter latency probe

Development startup accepts an explicit diagnostic step when statistics are
requested:

```sh
camera-probe first-frame-sc3336 pipeline.json SC3336_FULL_IQ.json /dev/video20 /dev/video11 step.raw /dev/video19 --step-at 6 --step-seconds 0.03
```

The initial exposure remains profile-derived (3 ms/1× in the pinned profile).
The requested step is converted with the recovered sensor conversion and active
timing. At the selected CIF SOF, the bridge writes only the exposure control
and reads it back. Gain and frame length are unchanged. It logs
`exposure-step-applied` with SOF/time and before/requested/readback codes, then
captures additional warmup frames through at least eight frames beyond the
chosen ID. The first-frame option limits the step to IDs 0–64. Use a CIF
`sof` source in the plan; an ISP output event source is unsuitable for measuring
capture-side update timing.

The lower-level combined command accepts
`--exposure-step SENSOR_NODE SOF_ID INTEGRATION_CODE` before `--`. It checks the
active driver's exposure min/max/step before allocation and opens a distinct
sensor character device. A missed target SOF, missing step, failed control
operation or readback mismatch fails the probe. It does not restore the old
exposure afterward; accepted writes remain applied. This is an explicit single
hardware write, **not automatic AE**. Normal captures without this option keep
their existing behavior.

ARM driver tests verify a single SOF-selected write/readback before RX queueing
and rejection of out-of-range codes before streaming. Existing bridge failure
cases and full startup simulations pass. Four real probe runs also succeeded,
with one write each and matching raw/statistics frame IDs.

### Latency result: not established

The 3 ms → 30 ms probes at SOF IDs 4, 6 and 8 all showed measured AE brightness
rising from 3 to 4 near reported frame 6. A same-exposure 3 ms → 3 ms control at
SOF 8 showed the same rise. Therefore this dark-scene metric is confounded by
startup behavior; the rise cannot be attributed to the scheduled write, and
no exposure-change latency or physical application frame is claimed. Statistics
also omit some IDs. A stable illuminated scene or stronger raw measurement is
needed to isolate the effect. The last control run left exposure at 3 ms.
[Probe results](exposure-step-validation.json). Raw scene captures and detailed
logs stay local. Automatic feedback remains off.


### Dark purple pedestal correction

A subsequent controlled Gain0/Gain1/unity comparison isolated the dark purple
bias to the startup WB gain stage. The native linear prepare default is Gain1;
the development startup now uses it and records the choice in its report.
A fresh real startup/ISP/statistics capture succeeded with near-neutral chroma.
See [WB position evidence and limits](AWB.md#initial-gain-application-position--corrected).
Earlier purple captures and brightness figures are historical results of the
old Gain0 checkpoint; they are not the current corrected baseline. Do not
interpret this fix as automatic white balance or color qualification.


The latency probe was repeated after the Gain1 correction, using an explicit
local IQ variant with fixed initial gain 16× and both a same-exposure control
and a 3→30 ms shutter step at SOF 8. Both corrected AE-statistics series dropped
to zero after startup. Final image luma differed slightly (mean 11.01 versus
12.39), but the per-frame corrected metric was too quantized to measure a
transition. The latency result remains unestablished; this is recorded in the
existing probe report. No automatic controller or inferred timing was enabled.

## Bounded automatic-exposure capture (0.0.30-dev)

First establish the fixed first-frame capture above using your actual plan and
node inventory. The automatic command uses the same plan/IQ/node arguments,
with a required statistics node and a new output basename:

```sh
./bin/camera-probe auto-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE /tmp/auto-ae STATS_NODE > /tmp/auto-ae.log 2>&1
```

Replace the uppercase placeholders with verified paths; the template's device
numbers are not defaults. This programs sensor exposure/gain and submits ISP
parameters. It refuses active vendor camera processes. It captures 33 frames,
discarding the first 32, then saves the last image and associated metadata,
initial parameter/calibration artifacts, and the last statistics payload/report.
The output basename must be new. Keep the complete log: `automatic-ae-finished`
reports processed statistics, snapshot count, last SOF/timestamp, and errors.
A successful run reports automatic exposure, **not** automatic white balance;
WB is held at the quantized calibrated startup gains and republished per batch.

For the first hardware run, preserve the fixed-exposure image and this new
image from the same scene, together with both logs, output JSON, initial JSON,
and raw statistics. Compare brightness visually and inspect the observed sensor
control writes/last SOF; emulator success and driver QBUF/DQBUF do not prove
physical gain timing or optical convergence. Sensor settings may remain changed
after either success or failure; the normal development image can restore its
usual startup sequence without reflashing this kit.

Expected stop conditions include unknown statistics parameter IDs, duplicate or
regressing frame IDs, a full event/pending queue, pool exhaustion, driver errors,
or final statistics still awaiting SOF. Preserve the exact error and artifacts
rather than retrying with fabricated frame IDs or snapshots. The software uses
explicit 64-event/16-pending/128-snapshot bounds, and the run is intentionally
short. No startup files, kernel image or bootloader are replaced by this command.

The `.stats.raw.json` file describes the statistics worker's diagnostic
translation against its initial snapshot. The live AE owner separately selects
registered snapshots by each statistics parameter ID; the worker's
`controlsExposure:false` describes that diagnostic worker, not the automatic
command's owner.

### Physical checkpoint — 2026-10-27, 0.0.31-dev

Ran both commands on the SC3336/Luckfox hardware using the current ARM Rust
binary, the existing CIF/SOF plan, and the pinned SC3336 IQ file. Both captured
640×480 NV12 successfully, with no vendor camera processes detected before or
after capture. No boot files or services were changed. These runs used fixed
calibrated white balance; automatic white balance is still unfinished.

The fixed-startup image was nearly black (mean encoded Y 3.41, range 0–21).
The bounded automatic-exposure image showed a recognizable scene (mean Y
86.41, range 24–251). The automatic owner processed 22 statistics frames,
registered 22 parameter snapshots, and reached SOF 34 without an error.
Its 78 sensor-control writes all reported success. This is physical evidence
of useful capture and a brightness response, not proof of optical convergence,
exact exposure-to-frame latency, color accuracy, or vendor-free cold startup.
The tool continues to report `physicalApplicationVerified:false` and
`coldStartProven:false`.

Raw images, metadata, complete logs, initial parameter artifacts, statistics,
and RGB inspection previews are kept locally in the ignored directory
`dist/reverse-engineering/hardware-2026-10-27/` under basenames
`ss-20261027-fixed` and `ss-20261027-auto`. The previews use a simple NV12
conversion and are inspection aids, not a color qualification. Private scene
captures are not committed. The frozen 0.0.30-dev test kit remains unchanged.

A second bounded hardware run added `automatic-ae-statistics` log events from
the live owner, including parameter/exposure association, translated mean,
preprocessing error and proposed exposure. It again processed 22 statistics
frames and exited successfully. Mean Q8 increased from 0 to 7555; preprocessing
error fell from −1.0 to −0.03405. The last five decisions retained 30 ms,
gain 42.4453125 and ISP gain 1.0, with controller relative error 0. This supports
settling in this scene within the bounded run; it does not establish behavior
under changing illumination or physical frame timing. Some exposure lookups
used the preceding effective-map entry (`exactExposureLookup:false`), which
remains visible in the log rather than being labeled exact association.
The local log is `ss-20261027-ae-telemetry.log` in the same ignored directory.

## Offline AWB generation and explicit measurement capture

The current development build can generate a separate measurement-enabled
candidate using `make-initial-parameters IQ.json OUT.bin --awb-measurements
SDK.bin SAMPLE_SCALE`. It includes AE measurements and retains the existing
fixed white balance. The established first-frame and automatic-exposure commands retain their
AE-only setup. The separate bounded command below submits the AWB candidate.

See [AWB assembly scope](AWB.md#post-assembly-binding-and-first-complete-measurement-candidate)
for component comparisons and outstanding integration. Preserve the full SDK
snapshot with any future capture, since AWB translation needs its actual
parameter-ID association. Do not call a measurement-enabled capture automatic
white balance: persistent preprocessing/gain feedback/publication still needs
connection and hardware testing.


```sh
camera-probe awb-measurement-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SAMPLE_SCALE
```

Use verified endpoint paths and a new output basename. This command captures
nine image frames (discards eight), holds the initial parameter queue open,
collects statistics through teardown, and saves the SDK snapshot as
`OUT.awb-sdk.bin`. It translates the last statistics payload against that exact
initial parameter ID and saves `OUT.awb-translated.bin` plus a diagnostic JSON.
Missing/mismatched IDs or absent AWB measurements fail explicitly. The translated
statistics frame is not asserted to be the same frame as the saved image.
Fixed calibrated WB and fixed startup exposure are used; automatic WB/AE remain
off for this command. Sensor settings can remain applied after capture.

### Physical AWB checkpoint — 2026-10-27, 0.0.31-dev

The assembled payload captured successfully on SC3336/Luckfox with no RKAIQ
process running. The default 3 ms/1× startup returned six statistics buffers,
valid AWB flags and a 225-cell grid, but sparse white-pixel counts. A private
IQ variant changed only AE startup exposure/gain to 30 ms/8×; no source IQ or
boot files were changed. That capture produced nonzero Normal/Big measurements
in all four FAST windows, including approximately 14–15 thousand normalized
weighted counts in two windows. These counts are decoded Q10-normalized AWB
statistics, not a count of distinct image pixels. The image was recognizable;
a subsequent requested capture included readable, upside-down text.

For the default translated capture and the brighter capture, all **7680 bytes**
of the SDK frame matched the original ARM single-ISP translator on the actual
captured payload and saved SDK snapshot. Statistics frame 7 referenced initial
parameter ID 0; the checker verified that association instead of inventing one.
The original numerical translation executes locally under the reference harness;
no vendor camera process was launched on the board.

Local artifacts and previews are in ignored
`dist/reverse-engineering/hardware-2026-10-27/`, basenames
`ss-20261027-awb-measurement-01` through `-04`. Runs 02/03 preserve native
comparison reports; run 04 is the requested text scene. The exposure-only IQ
variant is private and uncommitted. To compare another captured translation:

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/awb-captured-translation.py OUT.stats.raw OUT.awb-sdk.bin OUT.awb-translated.bin --configuration-id 0 --report OUT.native-comparison.json
```

Replace ID 0 with the actual initial parameter ID if using another payload.
This proves physical measurement collection and captured-data translation for
this checkpoint. It does not prove automatic-WB convergence, persistent
controller initialization, color accuracy, exposure-to-frame latency or
vendor-free cold startup. Gain feedback/publication is still unfinished.

## Physical AWB statistics capture — 2026-10-27

The separate bounded command now submits the assembled AWB candidate while
keeping fixed calibrated white balance:

```sh
camera-probe awb-measurement-frame-sc3336 PLAN.json IQ.json PARAM_NODE IMAGE_NODE OUT STATS_NODE SAMPLE_SCALE
```

Use verified endpoints and a new output basename. It discards eight image
frames, saves the ninth, holds the initial parameter queue open, and collects
statistics through teardown. New outputs include `OUT.awb-sdk.bin` and
`OUT.awb-translated.bin/json`. Translation requires the last statistics payload
parameter ID to match the actual initial snapshot; it never substitutes an
image sequence or a guessed configuration. The statistics frame and saved image
are not asserted to be the same frame. Sample scale remains an explicit input;
these diagnostic captures used 1 and did not run the AWB controller.

The real SC3336 returned valid AWB measurements and 225 grid entries without a
vendor camera process. Default 3 ms/1× startup gave sparse counts. A private IQ
variant changed only startup exposure/gain to 30 ms/8×, yielding nonzero Normal/
Big measurements in all four FAST windows, including approximately 14–15
thousand Q10-normalized weighted counts in two windows. These are weighted
statistics, not a count of distinct image pixels. A subsequent requested image
included readable upside-down text. Sensor exposure/gain remain at the last
capture's programmed settings; no boot files or services were changed.

The default and brighter captures' full **7680-byte** translated SDK frames
matched the original ARM translator exactly, using actual captured bytes and
the saved SDK snapshot. Both statistics frames referenced initial parameter
ID 0 at frame 7. The original code executed locally under the reference harness;
no RKAIQ process ran on the board.

Artifacts and previews remain private in ignored
`dist/reverse-engineering/hardware-2026-10-27/`, basenames
`ss-20261027-awb-measurement-01` through `-04`. Runs 02/03 include native comparison
reports; run 04 contains the requested text scene. To check another capture:

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/awb-captured-translation.py OUT.stats.raw OUT.awb-sdk.bin OUT.awb-translated.bin --configuration-id 0 --report OUT.native-comparison.json
```

Use the actual initial parameter ID if it differs from 0. This supersedes the
preceding offline-only checkpoint for measurement collection and translation.
It does not prove automatic-WB convergence, persistent controller initialization,
color accuracy, exposure-to-frame latency or vendor-free cold startup. Automatic
WB gain feedback/publication remains unfinished.

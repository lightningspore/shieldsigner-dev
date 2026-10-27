# First camera session

Kit **0.0.29** includes the one-command fixed startup checkpoint documented at the end of this guide. The full matching IQ profile and actual device inventory are required; no vendor-free hardware frame has been verified.

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

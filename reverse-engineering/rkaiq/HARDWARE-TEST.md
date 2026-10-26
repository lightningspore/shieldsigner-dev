# First camera session

This kit is an **experimental partial reconstruction**. It supplies ten recovered Rust numerical routines and a camera diagnostic. It does not replace `librkaiq.so` or the existing image's startup/service scripts. No firmware flash is needed for these tests.

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

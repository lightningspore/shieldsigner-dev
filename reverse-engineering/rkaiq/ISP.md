# ISP startup reconstruction

The Rust replacement continues to use the Luckfox SDK's Linux ISP/sensor drivers and physical ISP hardware. The proprietary userspace RKAIQ library chooses calibrated parameters, configures the graph/queues, and runs the automatic control algorithms. Replacing that library requires all of those responsibilities; a frame captured from an already initialized pipeline does not establish independent startup.

## Current functional status (0.0.31-dev)

The SC3336/RV1106 Rust path now configures the graph and calibrated startup
parameters, owns image/raw/statistics/parameter queues, runs live AE and AWB,
and publishes RGB frames to a PiVideoStream-compatible Python adapter. The
installed Camera wrapper has passed opt-in managed start/read/stop, restart,
consumer-stall, duplicate-owner, early-cancellation and parent-exit tests.
A controlled clean reboot with vendor startup skipped passed the automatic
application path; original startup scripts were restored. See
[HARDWARE-TEST.md](HARDWARE-TEST.md#controlled-clean-reboot-with-live-aeawb-and-the-application-adapter)
and its checksummed hardware reports.

The next functional work is the application's scan/UI path and preview
handling, rather than more isolated routine counts. Physical power-cycle,
optical QR, color-chart/latency qualification, default application integration
and remaining variable AWB configuration policy remain open. The source is
not a complete RKAIQ ABI replacement. Optional HDR, multi-camera and unused
branches stay deferred unless the actual single-camera linear path needs them.

The remaining reconstruction sections below are implementation history; their
older untested/unfinished checkpoint statements do not describe current source.

## Live Linux configuration adapter

Development `camera-probe configure-pipeline PLAN.json` now executes real media/subdevice/video ioctls. It is in the development ARM build from `mise run camera:rust:arm`, not kit 0.0.28. It preflights the supplied sensor, ISP, optional raw TX/RX nodes, bridge pads and existing media links before its first mutation. Character-device aliases across pipeline roles are rejected. It reads the sensor's ACTIVE format and crop bounds, using the recovered full-sensor fallback when bounds are unsupported. This initial path supports one linear RAW10 Bayer camera, with at most one raw capture and one raw readback endpoint; it does not select optional scalers, HDR or shared-camera modes.

The explicit plan supplies device paths/links from the actual inventory. The adapter does not guess media entity IDs or cross-media connections. It preserves link flags while changing only enabled state, rejects conflicting immutable links and checks link readback. Optional bridge pads receive the sensor format. Raw TX/RX formats use the appropriate capture/output buffer type and native `FIELD_NONE`, and dimensions/pixel format are checked after setting/readback.

For `direct-isp`, the existing recovered `setupPipelineFmtIsp` core runs against live methods. For `cif`, the raw formats use the crop dimensions before the recovered CIF pad operations. CIF forwards the driver's adjusted sink selection into the source-pad request except for its pad number; direct ISP resets target/origin/requested dimensions as the original direct path does. The adapter preserves those differences. Where the native RAW10 width predicate requires high-aligned CSI memory, TX receives `RKCIF_CMD_SET_CSI_MEMORY_MODE` and RX receives `RKISP_CMD_SET_CSI_MEMORY_MODE`, both with mode 2. Full SC3336 width 2304 does not trigger that predicate.

Commands for the next hardware session:

```sh
./camera-probe list > inventory.json
# Create pipeline.json from the template using this board's actual inventory.
./camera-probe configure-pipeline pipeline.json --dry-run > pipeline-preflight.json
./camera-probe configure-pipeline pipeline.json > pipeline-configured.json
```

The [template](examples/pipeline-linear.template.json) deliberately contains placeholder device paths. Populate `raw_tx`, `raw_rx`, `bridges` and `links` where the real route needs them. Empty arrays mean no such operations are requested, not automatic discovery. Each bridge has `device` and a `pads` array. Each link has `media`, `source`, `source_pad`, `sink`, `sink_pad`, and boolean `enabled`; source/sink IDs must be present in that media graph. Put competing-link disables before required-link enables.

Dry run performs reads/preflight only and cannot establish that a later set ioctl will succeed. Apply produces an operation trace with ioctl numbers, returned formats/selections and errors. Accepted changes remain if a subsequent operation fails. The command refuses active known vendor camera processes, closes its device handles when it exits, and does not start streaming or own persistent capture/parameter queues.

`mise run camera:rust:startup-check` independently compiles the ARM kernel ABI constants, compares 14 focused CIF pad/error/adjustment traces with the original routine, and executes the actual static ARM command under Linux emulation. Invalid endpoints fail the first sensor read with no mutations; six malformed/bounded-plan checks fail before device I/O. The existing 1,000-case direct-ISP regression remains unchanged/passing. [Development validation](live-pipeline-validation.json).

This implements the live link/format portion of startup. **It is not a complete camera-start command.** The next required pieces are sufficient calibrated initial ISP parameters and persistent queue/stream orchestration. Positive real ioctls, cold startup and image/QR quality remain hardware checks.

## Recovered ISP pad setup

`isp_pipeline::setup` reconstructs `CamHwIsp20::setupPipelineFmtIsp`, ELF `0x2319c` (Ghidra `0x3319c`). The hardware prepare method invokes the higher-level `setupPipelineFmt` before entering prepared state. This pad helper is one part of prepare, not the complete initialization procedure.

| Order | Native operation | Record behavior |
| --- | --- | --- |
| 1 | Set raw TX format | Skipped for shared CIF unless this is its first capture owner |
| 2 | Set raw RX format | Always called |
| 3 | Optional scaler format | Calls pixel-format-to-bpp helper, then scaler with input selection |
| 4 | Get ISP ACTIVE format, pad 0 | Device response supplies existing bus-format fields |
| 5 | Set pad 0 format | Replaces width/height/bus-code from sensor; preserves other returned bytes |
| 6 | Set ACTIVE crop, pad 0 | Copies input rectangle, zeroes flags/reserved fields initially |
| 7 | Set ACTIVE crop, pad 2 | Resets target/origin, restores requested width/height; preserves other fields returned by the preceding call |
| 8 | Get ISP ACTIVE format, pad 2 | Gets the source format independently |
| 9 | Set pad 2 format | Uses width/height returned by the source-crop call; preserves other source-format fields |

Driver-adjusted crop responses matter. The native method passes mutable records to device methods. Rust preserves those mutations rather than assuming the requested source dimensions were accepted. Sink width/height/code and source width/height changes are byte copies; the helper does not invent color-space values. The first nonzero ISP-device result stops subsequent calls and is returned, including a positive nonzero result. Raw-stream and scaler return values are not checked by this native helper. This behavior is recovered, not a recommendation for the final service's error policy.

The Rust backend trait exposes these operations explicitly. The live adapter above now supplies real device methods; `numeric-fixture` separately supplies controlled driver records for reference comparisons. Kernel UAPI cross-compilation independently checks 88-byte format/64-byte selection layouts, field offsets, ACTIVE/CROP constants and get/set ioctl numbers.

`mise run camera:rust:isp-pipeline` executes the original ARM method and compares normalized call traces, every byte passed to set-format/selection/scaler methods and return status across 1,000 cases. Shared-CIF flags, optional scaler, all six ISP-call failure positions, positive/negative failures and adjusted driver selections are covered. Original context, input selection and sensor format must remain unchanged. Device methods, raw-stream helpers, bpp lookup and scaler are **recorded boundary stubs**, not recovered implementations proved by this test. Uninitialized bytes of get-format requests beyond which/pad are excluded. [Reference report](isp-pipeline-equivalence.json).

## Initial parameter buffer is a separate requirement

The pinned open kernel sources establish the following:

- `rkisp_params_vb2_queue_setup` establishes first-parameter state, with a separate `first_cfg_params` branch.
- When `first_params` is set, `rkisp_params_vb2_buf_queue` copies the first submitted buffer through `save_first_param`, marks `is_first_cfg`, completes that buffer and wakes `sync_onoff`. It returns before the normal per-frame parameter-list enqueue.
- ISP32 `rkisp_save_first_param_v32` copies that configuration into the saved ISP32 parameter record and allocates internal buffers required by its enabled modules.
- `rkisp_params_first_cfg_v32` checks update masks and applies measurement/other-module configuration and enables. Empty configuration/update masks produce a missing-initial-IQ warning; formats alone do not supply calibrated IQ settings.

Sources: [parameter queue](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/platform/rockchip/isp/isp_params.c), [ISP32 configuration](https://github.com/LuckfoxTECH/luckfox-pico/blob/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/sysdrv/source/kernel/drivers/media/platform/rockchip/isp/isp_params_v32.c). Both downloads are SHA-pinned in `artifacts.json` and cached through `camera:re:prepare`.

These observations identify a required startup mechanism. They do not yet establish a complete userspace queue/stream order for our service, nor prove that a zeroed or partial parameter buffer will produce useful images.

## Remaining startup work

The native Ghidra exports now include hardware `init`, `prepare`, `start`, `setupPipelineFmt`, CIF/ISP format helpers and parameter submission. With the live format/link adapter implemented, the next work is sufficient calibrated initial module configuration, persistent parameter/capture queue ownership and stream order, then synchronization/restart/cleanup. AWB/gain parameter serializers and statistics capture already exist separately; they do not constitute full initialization. Real hardware must validate cold boot without a vendor bootstrap, frame quality, exposure/WB response and restart behavior.

For focused exports, `ExportRkaiq.java` accepts an optional second argument containing a Java full-match symbol regex. Its default selection remains unchanged. Exported pseudocode stays in ignored tool caches and is not distributed in the test kit.

## Black-level parameter block

`isp_black_level::apply` reconstructs `Isp32Params::convertAiqBlcToIsp32Params`, ELF `0x2d58c` (Ghidra `0x3d58c`). This converts an already selected algorithm result into the full 44-byte `isp32_bls_cfg` at parameter offset `0x7ae`, then copies that block into explicit cached storage. It does not select/interpolate the calibration or submit a buffer.

The native routine always marks black-level configuration and enable-update masks (bit 1). If the input main enable is true, it sets the module enable bit. If false, it **preserves** the old enable bit rather than clearing it. It zeroes automatic/window selection, sample count and both measurement windows, copies signed R/Gr/Gb/B fixed offsets unchanged, and copies stage-1 enable. These semantics must not be replaced by a conventional enable/disable setter.

With zero optical-black predgain, signed stage-1 offsets are copied unchanged, including negative values. With nonzero predgain, each signed channel is multiplied in f32, converted to signed integer by truncation, then clipped to 0–32767. The optical-black offset is clipped to 0–511, predgain is converted to Q8 and clipped to 0–65535, and maximum is clipped to 0–1048575. The input optical-black enable boolean is not read by this converter. The Rust checked API rejects nonfinite predgain before changing the record or cache.

`mise run camera:rust:isp-black-level` compares all three u64 masks, every byte of the block and cache against 1,000 executions of the original ARM converter. Both native and Rust harnesses verify preservation of unrelated bytes in the 11,145-byte parameter record; native context and source-input preservation are also checked. The corpus includes zero/negative/large/fractional gain, f32 extrema and subnormal gain, signed channel extremes, clipping boundaries, every enable combination and two C++ virtual-base offsets. This converter runs without algorithm/device stubs. [Reference report](isp-black-level-equivalence.json).

The exact SDK `AblcProc_V32_s` input declaration is SHA-pinned and independently cross-compiled for ARM to check its 32-byte layout and all used offsets. Kernel header assertions check the BLS block size, offset, member offsets and mask. This establishes serialization fidelity, not calibrated image quality or complete initial IQ configuration. Measurement configuration and other ISP modules still need reconstruction/integration before independent startup is available. Demosaic conversion and automatic tuning are covered below.

## Demosaic hardware controls

`isp_demosaic::quantize` reconstructs `AdebayerGetProcResult`, ELF `0x115880` (Ghidra `0x125880`). `SelectedParameters` exposes the SDK's selected tuning values as named Rust fields. They can also be decoded from its checked 132-byte value record. This stage consumes already selected values. Automatic selection and explicit-scene JSON input are implemented below; frame-state integration remains unfinished. The hardware ISP still performs the actual Bayer-to-RGB processing.

Quantization preserves signed filter coefficients and copies discrete controls/offsets into a 112-byte hardware record. Edge/alpha scales use Q10; weight slope uses Q7. Rounding adds signed 0.5 in **f64 after f32 arithmetic**, then truncates to signed i32. The inverse bilateral sigma conversion truncates directly without that half-step rounding. Byte/halfword narrowing preserves the original wrapping behavior rather than substituting clipping. The chroma normalization combines a rounded inverse-strength term with the narrowed weight slope using wrapping 32-bit multiplication, then derives its shift from `log(product)/ln(2)-7`, limited below at zero. The exact recovered constants are used, including 78715.2890625 and 55659.7265625, rather than recomputed approximations.

The returned hardware record retains the cached update flag and padding. After returning that value, the cached record has only its update flag cleared, matching the native `memcpy`-then-clear sequence. This helper does not set the flag when tuning changes; the outer processing state must do that. Checked Rust rejects nonfinite fields, nonpositive inverse-filter inputs and nonpositive wrapped normalization products before any cache mutation. A rejected input therefore cannot leave a partially updated record.

`isp_demosaic::apply` reconstructs `convertAiqAdebayerToIsp32Params`, ELF `0x2ca90` (Ghidra `0x3ca90`). A false update flag leaves **every** parameter byte unchanged. An enabled update sets bit 35 in all three masks. A disabled update sets enable-update, clears the module enable bit, and preserves the previous configuration-update mask. Both active-update branches copy the full 57-byte packed block at `0x1282`. Signed i32 filter coefficients narrow to their low byte, and all unrelated parameter bytes are preserved.

`mise run camera:rust:isp-demosaic` checks 1,000 selected-value/hardware/cache cases followed by 1,000 independent hardware/kernel-packing cases. The original RKAIQ instructions execute under Unicorn; its `log` dependency executes the pinned SDK uClibc **ARM code**, with no imported runtime calls reached. Only standard `memcpy` is modeled. The harness passes double arguments through D registers after its register reset; existing single-float argument behavior is unchanged. Integer output equality is the claim, not universal equality of the Rust/native logarithms.

The corpus checks every hardware/cache byte, all three parameter masks and the entire kernel block, plus preservation of unrelated context/parameter bytes. It covers update/enable combinations, coefficient narrowing, signed rounding ties, saturating float-to-i32 conversions, powers-of-two normalization and positive products after native multiplication wraps. [Reference report](isp-demosaic-equivalence.json). Cross-compiled verbatim SDK declarations independently verify both value layouts and all used offsets; pinned kernel assertions verify the 57-byte packed block and module mask. These controls still require the chosen scene’s calibrated inputs, other initial ISP modules and live queue submission before independent camera startup can be claimed.

## Automatic demosaic tuning

`demosaic_selection::Calibration` represents all four 13-entry ISO tables and static coefficients from the pinned SDK `CalibDbV2_Debayer_Tuning_t` declaration. With the diagnostic feature, `Calibration::from_value` loads **one explicitly selected** scene’s `debayer_v2.param` object. It requires every field, exact array lengths, integer-valued bounded integer entries and finite f32 values. It does not choose a scene, invent missing defaults or parse the native binary IQ format.

`Calibration::select(iso)` reconstructs the automatic branch of `AdebayerProcess`, ELF `0x1157a0`, and its full `AdebayerSelectParam` call at `0x115028`. It copies the scene’s enable/static coefficients and independently selects green interpolation, green direction weights, green filtering and chroma filtering. Each group uses its **own ISO grid**. All named selected fields are recomputed, so cold initialization does not require fabricated previous tuning; `SelectedParameters::write_record` separately preserves caller-owned SDK record padding.

Native selection chooses the first knot strictly greater than `(iso as f32)`, with endpoint behavior below/above the table. For an interior interval, it truncates both f32 knots to i32 **before** forming the interpolation numerator and denominator. Fractional knots therefore do not behave like conventional floating-knot interpolation. Float values use fused multiply/add; integer controls add signed 0.5 in f64 after that f32 operation, truncate, then narrow to the SDK field width. The checked API rejects nonfinite, negative or greater-than-16777216 knots and any pair that is not strictly increasing both as floats and after integer truncation. Degenerate denominators are rejected rather than executing the original invalid numerical path.

`mise run camera:rust:demosaic-selection` compares 1,000 cases from Rust JSON loading through selection, hardware quantization and kernel packing against original ARM executions. Nine hundred cases use varied synthetic tables with independent fractional grids, wide coefficient/control values and changing float tuning. One hundred use directed ISO points below/at/above every knot, interval midpoints and the upper endpoint of the actual pinned SC3336 profile at `/main_scene/0/sub_scene/0/scene_isp32/debayer_v2/param`. Exact selected bytes, hardware/cache bytes, three masks and the complete packed block are compared, including preserved padding/unrelated context. [Report](demosaic-selection-equivalence.json).

The oracle independently packs the public SDK calibration record from the supplied JSON, executes native automatic `Process`/`SelectParam`, verifies that no other context is changed, then feeds the selected result to the already verified native hardware conversion. Its logarithm executes the pinned uClibc ARM code. The original native JSON/BIN parser is **not** executed by this suite. Cross-compiling the verbatim SDK declarations verifies the 968-byte table record, each group size and every consumed field offset independently of Rust and the Python packer.

The kit contains the functional SC3336 demosaic subset with the source URL/hash and explicit scene pointer. This is SDK reference data, not physical camera/lens qualification. Unit checks cover the nonstandard fractional-knot weighting and rejection of missing, truncated, fractional-integer, overflowing and integer-collapsed tables. The numerical selector still builds without JSON/std.

This completes the recovered automatic tuning-to-register path for this demosaic module’s checked inputs. It does **not** complete the outer frame/update-state controller, manual-mode lifecycle, initial configuration for the remaining ISP modules, queue submission or independent camera startup. Selection does not set the hardware update flag; the recovered outer processing state must decide when to publish changed results.

## Parameter queue connection

The recovered metadata queue core and bounded Linux submission diagnostic are now documented in [PARAMETERS.md](PARAMETERS.md). They accept a fully assembled kernel parameter record; they do not supply the remaining initial module configuration or persistent camera-service backend. Driver dequeue can acknowledge a saved first configuration before frame application. Successful hardware transport and independent startup are still unverified.

## Exposure measurement configuration

The selected AE grid/histogram result-to-kernel branches are now reconstructed with exact four-channel routing and cached records. [AE measurement configuration](AE.md#measurement-parameter-configuration). The [AWB measurement converter](AWB.md) also reconstructs selected regions, thresholds, transforms, windows and grid weights. These supply parts of the initial parameter record; calibrated selection policy, the AWB algorithm and remaining module/service integration remain unfinished.

## CIF raw readback: remaining first-frame dependency

Development `capture-with-parameters` now retains the parameter queue while
image capture runs. This resolves that resource lifetime only; it does not
replace the CIF raw bridge.

Ghidra exports of the pinned original establish that the nonshared path starts
RawStreamCapUnit followed by RawStreamProcUnit. The latter maintains pending
and in-flight raw buffers. Its `trigger_isp_readback` (ELF 0x35cf0) obtains a
matching RX buffer for each raw exposure, transfers the source buffer handle
(USERPTR, DMA-BUF, or a conditional MMAP copy), and queues RX before issuing
`RKISP_CMD_TRIGGER_READ_BACK` to the ISP subdevice. A failed RX QBUF suppresses
the trigger. Thus opening raw nodes or STREAMON alone does not implement the
native per-frame path. A TX buffer must remain owned until RX completes, then
be returned to TX; independent immediate requeue would risk overwriting data
still consumed by the ISP.

The new Rust `raw_readback::linear_trigger` encodes the 28-byte linear trigger:
SOF nanoseconds, source timestamp converted from microseconds, frame ID,
readback times and `T_START_X1`. It preserves the observed signed times rules
and wrapping 64-bit timestamp conversion. The original ioctl literal at ELF
0x362a4 is 0x401c56c0. Independent ARM compilation of pinned kernel headers checks
the ioctl, every field offset, size and mode. Two Rust tests cover times and
full-width timestamp edge cases. **This helper has not yet been differentially
executed against the whole native trigger routine**, whose C++ queues and
optional raw-dump path still need explicit boundaries.

Next implementation is the persistent one-exposure TX→RX buffer bridge with
RX-completion ownership, frame ID/timestamp propagation, per-frame trigger,
backpressure and cleanup. Integrate it around the combined image capture before
claiming CIF startup. Shared-CIF, HDR, optional raw dumps and multi-ISP support
remain outside this minimum linear path. Positive hardware capture and QR
quality remain unverified.

Development follow-up: `capture-cif-with-parameters` now integrates a persistent
single-plane RAW10 DMA-BUF bridge around image capture. It exports TX buffers,
imports them into matching RX indices, triggers readback after successful RX
QBUF, and returns each TX index only after RX completion. See
[hardware command and explicit limitations](HARDWARE-TEST.md#development-linear-cif-dma-buf-bridge).
This implements the live bridge mechanism described above, but its positive
hardware path, outer controller synchronization and whole-routine native
queue equivalence remain unverified. It does not add automatic 3A.

The raw bridge now subscribes to ISP FRAME_SYNC events before streaming and
matches payload frame IDs to raw sequences. Ghidra `RKSofEventStream` (ELF
0x32658) reads frame ID at event byte 8 and converts signed old-time seconds/
nanoseconds at bytes 80/84. The delivery sequence at byte 76 is unrelated.
`match_sof_timestamp_map` (ELF 0x34d8c) clamps signed-negative IDs to zero before
lookup; the caller initializes the missing timestamp to zero. Rust uses those
fields/rules with a bounded 64-entry cache and reports hits/misses. Independent
ARM header assertions verify event size, every consumed offset and ioctls.
Live delivery order, misses and SOF timing still require hardware measurement;
this does not establish full native ordered-map/controller equivalence.

Development `first-frame-sc3336` now connects graph preflight/configuration,
profile startup parameters, active-descriptor exposure conversion, driver-range
checks, sensor writes and combined CIF/image capture in one command. See
[the first-frame invocation](HARDWARE-TEST.md#one-command-fixed-first-frame-startup-development).
It retains explicit device inventory and rejects existing outputs. This is a
fixed first-frame checkpoint; full positive startup, QR image quality and the
automatic controller remain unverified/unfinished.


## RGB preview quantization matches ISP output

The pinned IQ's CSM uses BT.601 coefficients with full-range output, zero Y/C
offsets, and CGC ratio/limit disabled. The kernel's `isp_csm_config` enables
full Y/C range; `isp_cgc_config` reports full quantization unless `yuv_limit`
is set. The device reports NV12 quantization 1 (full). The initial application
converter incorrectly used limited-range math, expanding 16..235 and clipping
valid full-range values. It now uses driver-reported quantization for the RGB
inverse and records color metadata in capture JSON and an
`application-rgb-conversion` event.

The supported full-range Q8 inverse is R=Y+359*Cr/256,
G=Y-88*Cb/256-183*Cr/256, B=Y+454*Cb/256, with chroma centered at 128,
rounding and output clipping. Limited range retains the existing 298/409/100/
208/516 coefficients and Y offset 16. V4L2 YUV default quantization maps to
limited except JPEG, as defined by the pinned UAPI. Unsupported encoding/range
metadata is rejected; high-level RGB startup also checks the actual serialized
BT.601 CSM coefficients, zero offsets and unscaled CGC. This avoids silently
decoding an arbitrary profile matrix as BT.601.

The host test compares 92,352 full/limited sample combinations with independent
floating-point equations within one level per RGB channel; it also covers
single/multiplanar metadata offsets and invalid profile/encoding/range cases.
Real run 26 passes full-range RGB delivery through the installed Camera wrapper,
stalled-reader recovery and 396 live AE/AWB statistics frames. Its final
statistics still match all 7,680 original ARM translation bytes. A changed CSM
profile is rejected on ARM before acquisition. See
`rgb-colorimetry-hardware-validation.json`. Private previews stay local. These
checks validate range handling, not physical color calibration or optical QR.

## Application scan/preview handoff

The opt-in launcher now installs the pinned application's Camera module with
only the Rust adapter import and complete-canvas preview rotation changed in
memory. Raw decoder input remains the original unrotated 640×480 RGB image;
ScanScreen independently asks for its rotated display preview. Expanding that
preview avoids lost edges/black borders and enables Pillow's fast right-angle
transpose. Four rotations of a real camera frame preserve every source pixel.

Hardware integration run 29 also passes the installed DecodeQR with 16 generated
edge/rotation fixtures and rejects a changed Camera source. These are synthetic
QR pixels through actual application methods, not optical QR evidence. The
real captured scene contained text and yielded no QR. The launcher imports the
real main.py and passes `--help`, but full UI rendering/buttons remain untested.
See HARDWARE-TEST.md and `application-integration-hardware-validation.json`.

### Persistent automatic linear demosaic frame gate (0.0.33 development)

`demosaic_runtime::State` reconstructs the linear color-frame branch of the
algorithm's `processing` callback, ELF `0x114a2c` (Ghidra `0x124a2c`). The
`g_RkIspAlgoDescAdebayer` descriptor identifies this callback despite the binary
containing many generic `processing` symbols. The Ghidra exporter now accepts
an optional exact entry address after the name regex to avoid exporting every
unrelated callback. Decompiled vendor code remains local and uncommitted.

The callback multiplies analogue, sensor-digital and ISP gains in f32 order,
then multiplies by 50 and truncates to integer ISO. Unlike AWB's metadata path,
it does not clamp each gain to unity. Missing exposure falls back to ISO 50.
An integer ISO change, pending cached update, or explicit reconfiguration runs
the recovered selector and quantizer. Reconfiguration is consumed; unchanged
frames publish no new result. The returned hardware update flag is preserved
while the cached flag is cleared by the recovered quantizer. The Rust state
commits after successful selection/quantization; nonfinite/negative gain inputs
are rejected rather than sent into unchecked native float conversion.

[Full persistent-callback comparison](demosaic-frame-equivalence.json) executes
256 frames against the actual original callback and its real selection and
quantization functions: 76 updates and 180 no-op frames. Every returned/cache
byte, integer ISO and reconfiguration flag matches. Directed inputs include
repeated values, same-truncated-ISO gain changes, sub-unity gain, changed gain
products, missing exposure and forced reconfiguration. Native uClibc `log`
executes; diagnostic logging alone is a modeled no-op. The same Rust replay
executes on the physical Luckfox CPU with identical output, with no vendor
library loaded there. This replay makes no camera/ISP writes.

Rebuild host `numeric-fixture` and ARM binaries with mise, then run:
`mise run camera:rust:demosaic-frames -- --adb SERIAL --report LOCAL.json`.
The explicit SDK demosaic subset/header and pinned original library/runtime
are required locally. HDR, monochrome and manual-mode lifecycle remain outside
this automatic-color API. Live queues still retain startup demosaic tuning;
connecting this verified frame gate to the associated exposure and atomic
parameter enqueue is the next implementation step. This is a component
checkpoint, not a claim that live ISO-dependent ISP tuning is finished.

### Live ISO-dependent demosaic batches (0.0.33 development)

The automatic SC3336 owner now connects the verified frame gate to actual ISP
parameter submission. `Runtime::effective_exposure` is shared by gain conversion
and demosaic tuning, selecting the scheduler-associated record for the processing
frame; the latest proposed AE exposure is not substituted. The three real gains
feed the recovered demosaic callback's unclamped ISO calculation.

Each proposal stages its own state/cache and merges the packed demosaic block
with WB/exposure gain and optional AWB measurement changes in one runtime
parameter batch. The owner marks its frame ID, successfully enqueues it, then
commits the tuning state and retained effective snapshot. Pool exhaustion or
QBUF failure preserves the old ISO, reconfiguration flag and all hardware-cache
bytes. An ARM simulated queue-exhaustion/retry case verifies that invariant.
Both AE-only and AE/AWB automatic factories enable this integration; fixed
first-frame capture remains an explicit calibrated startup checkpoint.

[Live evidence](demosaic-live-validation.json) covers two actual 192-image runs,
starting dim (3 ms/1×) and bright (24 ms/4×). Each processes 128 AE/AWB
statistics frames, submits 127 parameter batches and retains at most two
snapshots. The dim run submits 15 demosaic updates across ISO 50–164; the
bright run submits 12 across ISO 184–304, including both increasing and
decreasing transitions. All 27 returned 112-byte hardware records and 57-byte
packed ISP blocks match the original full callback and converter instructions.
The three demosaic mask bits are checked independently in the native converter.

Final sixteen-sample brightness means are 42.863 and 46.590, both inside the
calibrated target-45 ±10% band. The dim run's final exact-snapshot AWB translation
still matches all 7,680 native bytes. All 85 library/five Unix tests, the
no-default-features build, ARM build and six simulated full capture scenarios
pass, including the new failed-enqueue/retry check.

Run `scripts/demosaic-live-check.py LOCAL-OWNER.log --report LOCAL.json` through
uv with pyelftools/unicorn to repeat the original-ARM comparison. Records are
logged only after successful QBUF; driver completion is ownership evidence, and
shutdown may cancel final queued proposals. This does not prove that every
proposal appeared in pixels, settle the observed physical gain-delay exception,
or qualify optical QR/color accuracy, optional modes or full native service
equivalence. Frozen 0.0.32-dev remains unchanged.

The subsequent [actual scan-loop run](scan-demosaic-hardware-validation.json)
also passes with live demosaic, including independent comparison of all
fifteen submitted tuning records, concurrent real decoding/preview, clean
shutdown and the default no-scene-image behavior. It measures increased
userspace write-dispatch latency under scan load without claiming physical
sensor application timing.

### Selected-profile coverage audit (0.0.33 frozen startup)

[Reproducible audit](profile-module-audit.json) compares the pinned full IQ's
explicit enable flags with the actual `frame.initial.bin` retained from the
0.0.33 clean-boot hardware run. It resolves the ISP32→ISP3X→ISP2X UAPI aliases
from the pinned headers and verifies each bit before inspecting the captured
three masks. IQ/startup/header hashes identify the inputs.

Eight selected blocks are configured enabled in the profile but explicitly
disabled by our startup enable-update request:

| Block | Function | Rust startup |
|---|---|---|
| CCM | Calibrated RGB color correction, distinct from implemented RGB→YUV CSM | Disabled |
| LSC | Spatial lens shading correction; calibration must match optics | Disabled |
| DPCC | Defect/hot-pixel correction | Disabled |
| BAYNR | Spatial Bayer noise reduction | Disabled |
| BAY3D | Temporal Bayer noise reduction | Disabled |
| YNR | Luma noise reduction | Disabled |
| CNR | Chroma noise reduction | Disabled |
| SHARP | Sharpening | Disabled |

These are **implementation gaps for full supplied-profile parity**, not proof
that every block is necessary to decode a QR. Profile flags alone do not prove
the vendor daemon enabled those modules on this hardware; startup parameter
requests are not independent register readback. This selected-block check is
not a complete inventory of all IQ sections. BLS has independently controlled
internal stages, so its outer enable bit must not be used to label all
black-level processing disabled. Current BLC, demosaic, WB/gain, gamma, CSM/CGC
and measurement configuration retain their separately documented evidence.

The current path is a tested functional subset, not full vendor image-quality
parity. Optical QR and physical scene/low-light checks should guide the order
of remaining image-quality work; no block should be enabled with invented
settings or without hardware testing and memory-budget checks. The existing
DPCC interpolation component, for example, is not a completed DPCC live block.

Reproduce with `uv run --python 3.13 python
reverse-engineering/rkaiq/scripts/profile-module-audit.py PRIVATE-IQ
CAPTURE.initial.bin --report LOCAL.json`. The default UAPI directory is the
pinned local kernel-uapi/linux snapshot; `--uapi` may supply another explicit
copy. This audit makes no device changes and stores no full IQ or scene pixels
in the tracked report.

### DPCC selected-result serializer (0.0.34 development)

`isp_dpcc::apply` reconstructs the DPCC case in the complete ISP32
`convert3aResultsToIspCfg` dispatcher (ELF `0x304c4`, type ID 6). The API takes
a 192-byte selected-result input window; this branch reads only through byte
188, skips source enable/padding fields, widens two u8 values to u16, and
serializes the full 186-byte kernel block at `0x7da`. ARM-target C assertions
against the pinned UAPI independently verify its size/offset, point-table
offset 153 and module mask bit 0. This does not assert an independently
recovered complete SDK result declaration.

Native always sets enable-update and configuration-update bit 0. A nonzero
result enable also sets module-enable bit 0; a zero enable leaves the previous
module-enable bit untouched. The Rust converter preserves that asymmetry, not
an invented automatic disable operation. Unrelated parameters and mask bits
are preserved. Source padding and trailing bytes are ignored.

[Original-ARM comparison](isp-dpcc-equivalence.json) checks 1,000 deterministic
cases against the full original dispatcher, comparing every one of the 11,145
output bytes. Inputs vary prior masks, all selected-result bytes and zero/one/255
enable values. The controlled C++ typed-proxy cast is the oracle boundary;
actual conversion instructions execute. Host output and execution of the Rust
fixture on the physical Luckfox are identical. Replay uses no camera devices
and does not enable DPCC. The 85 library/five Unix tests, no-default-features
build, static ARM build and new UAPI layout assertions pass.

Rebuild host numeric-fixture and ARM binaries through mise, then run
`mise run camera:rust:isp-dpcc -- --adb SERIAL --report LOCAL.json`. The script
uses the development numeric binary at
`/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture`. Its temporary
reference input is stored on persistent board storage and removed afterward.
No vendor library is deployed to or loaded on the board.

Calibrated selection/AdpccProcess, frame-state decisions and live parameter
submission still need to be connected. The existing scalar interpolation and
this serializer are components, not a completed DPCC implementation. DPCC
remains explicitly disabled in the runnable 0.0.33 frozen kit and current live
path. That archive and its hardware qualification remain unchanged.

### DPCC automatic expert ISO selection (0.0.34 development)

`dpcc_selection::select` reconstructs `Expert_mode_select_basic_params_by_ISO`
(ELF `0x11b6e0`) and its full basic-configuration copy helper (`0x11b3c4`).
The 13-row input table has 108-byte rows: signed ISO, 103 consumed configuration
bytes and one trailing padding byte. Select the lower row in each half-open
ISO interval, clamp below/above the grid, and copy exactly 103 bytes into the
selected result. There is no interpolation in this branch. All later result
bytes, including basic padding/BPT/PDAF fields, remain untouched. Rust rejects
non-increasing grids before output mutation; a unit case verifies atomicity.

The pinned SC3336 profile has `Fast_mode_en=0`, so automatic processing uses
this expert branch. Its grid includes the close points 1500/1507/1510. PDAF and
sensor-side automatic DPCC are disabled in that profile; their disabled result
field initialization still requires explicit verification rather than assumed
values. No Fast/HDR/manual implementation is claimed by this explicit-ISO API.

[Native comparison](dpcc-selection-equivalence.json) checks 1,000 full 192-byte
outputs, unchanged input tables, padding and unrelated result preservation.
Nine hundred cases use varied strictly increasing signed grids, while one
hundred use the actual profile ISO grid with synthetic configuration values.
Samples cover exact knots, ±1 neighbors and i32 extremes. Original selector and
copy instructions execute directly with no helper stubs. The same Rust cases
run identically on the physical Luckfox CPU. The 86 library/five Unix tests,
no-default-features build and static ARM build pass.

Build host numeric-fixture and ARM binaries with mise, then run
`mise run camera:rust:dpcc-selection -- --adb SERIAL --report LOCAL.json`.
The physical replay uses the development 0.0.34 numeric binary and persistent
temporary reference input, removed afterward. It makes no camera/ISP writes.
Full JSON→expert-table initialization, BPT/PDAF assembly, processing/frame
lifecycle and successful live enqueue remain next work; the runnable camera
continues to leave DPCC disabled. The 0.0.33 frozen kit is unchanged.

### DPCC expert table from the selected IQ object (0.0.34 development)

`dpcc_calibration::expert_table` loads an explicitly supplied `DpccTuningPara`
object, requires expert mode (`Fast_mode_en=0`), validates boolean/byte fields,
13-element arrays and strictly increasing signed ISO knots, and constructs
all thirteen 108-byte rows. The native initializer is
`dpcc_expert_mode_basic_params_init` (ELF `0x11ac20`). Each row retains the
103 basic fields used by the verified selector, with fresh padding zeroed.
The RK/RG/RND/RO/LC/PG method enables are duplicated for the two hardware
color groups exactly as the native initializer does. Thresholds and limits
come from the supplied calibration arrays; no default thresholds are invented.

Five additional SDK headers are pinned by commit URL/SHA in `artifacts.json`
and fetched into ignored cache by the existing preparation tool. Independent
ARM-target C compilation verifies the actual SDK layout: expert offset 40,
ISO offset 48, first set offset 308, expert size 1204, row size 108, basic
configuration size 103, full result size 192, BPT offset 104 and PDAF offset
128. This now independently verifies the complete result size that the earlier
serializer used as its bounded input window.

[Native initializer comparison](dpcc-calibration-equivalence.json) checks every
byte of all 1,404 table bytes for the actual SC3336 profile plus 199 varied
calibrations. The Python reference packs the public SDK field declaration
independently of Rust, then executes the entire native initializer. Only
unused Fast-mode pointer descriptors/preceding padding are zero-filled input
boundaries; the expert initializer does not read them. Host and physical
Luckfox Rust execution are identical. The 86 library/five Unix tests,
no-default-features/static ARM builds and SDK layout checks pass.

Build host numeric-fixture and ARM binaries with mise, then run
`mise run camera:rust:dpcc-calibration -- --adb SERIAL --report LOCAL.json`.
The pinned original library, SDK headers and full IQ file remain local
prerequisites. Raw vendor/decompiled code, full IQ data and camera images
are not added to git. No vendor library is loaded on the Luckfox for replay.

This closes expert-table construction, not full DPCC processing. BPT/PDAF
assembly, complete automatic-processing composition and live frame/enqueue
integration remain next; no speculative zero/default peripheral fields have
been enabled on the camera. The frozen 0.0.33 kit is unchanged.

### Complete automatic DPCC result assembly (0.0.34 development)

`dpcc_calibration::Automatic` composes the verified expert table/selection with
the remaining output fields for this explicit profile: automatic expert mode,
PDAF disabled, and sensor-side automatic DPCC disabled. Unsupported modes are
rejected rather than silently falling back. `pdaf_fields` reconstructs
`dpcc_pdaf_params_init` (ELF `0x11afc4`): point-enable bytes become booleans,
x/y points keep native ordering, signed i32 offsets/counts narrow to u16,
and fresh allocation padding is zero. Disabled PDAF does not mean its
configuration fields can be invented or omitted.

The original `AdpccInit` (ELF `0x11cacc`) zeroes its full context before running
the actual calibration initializers. The automatic BPT cache at context
`0x5e8` remains zero; the full-constructor comparison verifies it, replacing
the earlier unverified zero-default assumption. `AdpccProcess` (ELF `0x11cc1c`)
copies all 24 BPT bytes and 62 PDAF bytes after expert selection. Rust preserves
result padding at byte 103 and bytes 190–191 and commits the complete result
only after selection succeeds. Public SDK C assertions independently verify
full IQ size 1352, BPT size 24, PDAF size 62 and result size 192.

[Whole-init/process evidence](dpcc-automatic-equivalence.json) compares every
byte of 200 complete 192-byte results against actual original `AdpccInit` and
`AdpccProcess` execution. Forty-one cases use the actual profile at ISO-grid
boundaries/neighbors and i32 extremes; 159 vary expert and disabled-PDAF
configuration, including negative/overflowing-to-u16 offsets and non-boolean
point-enable bytes. Prior result padding is randomized. Host and physical
Luckfox Rust replay are identical. The original allocator is modeled as one
controlled context and the native IQ-module lookup receives an independently
SDK-packed object; original memset/initializers/process execute. Diagnostic
logging is a no-op boundary. Native SDK JSON parsing is not claimed.

The 87 library/five Unix tests, no-default-features/static ARM builds and
expanded SDK layout assertions pass. Run
`mise run camera:rust:dpcc-automatic -- --adb SERIAL --report LOCAL.json` after
building host numeric-fixture and ARM tools. Reference input lives temporarily
on persistent board storage and is removed afterward. This replay makes no
ISP writes and loads no vendor library on the board.

Outer per-frame update/reconfiguration policy and transactional live enqueue
remain next. DPCC is still disabled in the live path and frozen 0.0.33 kit;
this result is complete supported-mode output assembly, not live defect-pixel
correction or optical quality qualification.

### Persistent DPCC and live submission (0.0.34 development)

`dpcc_runtime::State::process` reconstructs the automatic linear color-frame
callback gate at ELF `0x11a67c` (Ghidra `0x12a67c`). ISO uses native f32
`(analogue * (sensorDigital * ispDigital)) * 50`, truncated to i32. Missing
exposure means ISO 50. A fresh context starts at ISO zero; changed integer ISO
or a reconfiguration flag triggers processing. Unchanged ISO leaves every
cached result byte untouched. The supported mode excludes HDR, monochrome,
Fast mode, enabled PDAF and sensor-side automatic DPCC.

[Persistent native/physical CPU comparison](dpcc-frame-equivalence.json) checks
256 frames: 86 updates and 170 no-ops, including reconfiguration, repeated ISO,
sub-unity gains and missing exposure. All 192 result bytes, ISO and flag match
the actual original callback. Run `mise run camera:rust:dpcc-frames` after
building the fixture tools; `--adb SERIAL` adds physical CPU replay.

The startup builder now enables DPCC from the selected profile. Runtime uses
the same effective exposure association as demosaic/gain and includes DPCC in
their transactional parameter batch. Result/cache/ISO/snapshot state commits
only after successful QBUF. Simulated acquisition/QBUF failures verify unchanged
DPCC state and a successful retry. No independent physical gain timing is
inferred from the effective-map label.

The first live attempt exhausted the parameter pool after about 150 image
frames. The production owner now waits at most 250 ms for a validated DQBUF
completion when every slot is in flight, preserving EAGAIN ownership and
stopping the wait if capture has ended. It does not retry arbitrary driver or
QBUF failures. Simulated EAGAIN/completion and cancellation tests cover that
path. A subsequent 600-image run passed without needing this wait; live
recovery under queue pressure is therefore not yet proven.

[Live comparison](dpcc-live-validation.json) checks all fifteen submitted
192-byte results and 186-byte packed blocks against the original full callback
and ISP32 converter. Startup DPCC is enabled and matches the first runtime
result. The run processed 400 AE/AWB statistics frames and accepted 399 batches,
retaining at most two snapshots. Final AWB translation matches all 7,680 bytes.
This is accepted-submission and functional capture evidence, not optical
quality, defect-removal efficacy or per-frame register readback. The frozen
0.0.33 kit remains unchanged and has DPCC disabled.

### CCM register conversion (0.0.34 development)

`isp_ccm::apply` reconstructs the complete
`Isp32Params::convertAiqCcmToIsp32Params` routine (ELF `0x2d0cc`, Ghidra
`0x3d0cc`). It accepts an explicit 156-byte SDK-layout record and writes the
79-byte packed kernel CCM block at `0x12bb`. ARM-target C assertions against
pinned kernel headers check its size, offset, matrix/curve/enhancement offsets
and module bit 8. SDK input layout is recovered from the converter's accesses;
the public SDK declaration is now independently compiled for ARM32
([layout evidence](#ccm-sdk-layouts-and-static-calibration-fields-0034-development)).

The 3×3 matrix subtracts identity on its diagonal, multiplies by 128 and rounds
half steps away from zero before narrowing to signed 16-bit fields. Offsets
use the same rounding without scaling. Luma coefficients, eighteen alpha-curve
values and bounds use positive-only truncation with native low-bit narrowing;
the enhancement ratio additionally scales by 1024. The high-Y disable field
is the source byte XOR one, not normalized boolean negation. Update masks gain
bit 8; enabled input sets that enable bit, while disabled input preserves any
previous enable bit. Other bytes and mask bits remain unchanged.

[Original/physical ARM comparison](isp-ccm-equivalence.json) checks all 11,145
parameter bytes across 1,000 deterministic cases with random prior contents,
positive/negative values, half steps, zeros, narrowing, identity matrices and
non-boolean control bytes. Original machine code executes directly, with no
C++ proxy or reconstructed numerical substitute. Rust deliberately rejects
non-finite inputs or magnitudes over 1,000,000 before changing any bytes; behavior
outside this domain is not claimed. An atomic-failure test covers invalid input.

Build the host numeric fixture and ARM tools, then run
`mise run camera:rust:isp-ccm -- --adb SERIAL --report LOCAL.json`.
Physical replay executes Rust numerical conversion only; it does not load the
vendor library or write ISP registers. This closes register conversion, not
calibrated CCM matrix selection, temporal damping or live controller integration.
CCM remains disabled on the live camera until those inputs are verified.

### CCM saturation selection and interpolation (0.0.34 development)

`ccm_selection::select` reconstructs `SatSelectCcmProfiles` (ELF `0xfd278`),
`SatInterpolateMatrices` (`0xfd2e6`) and `SatInterpolateOffset` (`0xfd32e`).
Input is an explicit nonempty list of finite profiles, strictly descending by
saturation. At or beyond an endpoint, native status −21 means clamp/copy that
endpoint. Interior selection returns status zero and a neighboring pair;
an exact interior knot retains a two-profile bracket rather than becoming a
clamped singleton. Rust exposes both indices and clamp status.

The native high-profile weight is `(lowSat − sample)/(lowSat − highSat)`.
Each coefficient/offset first multiplies the low value by the complementary
weight, then uses `vfma.f32` for the high value/weight addition. Ghidra's plain
multiply/add expression hides that fused rounding; a first unfused Rust attempt
failed exact-bit comparison and was corrected with `libm::fmaf` after checking
ARM instructions. All nine matrix and three offset floats are compared by bits.

[Native and physical CPU evidence](ccm-selection-equivalence.json) covers 1,000
varied lists/samples plus 35 cases using all seven selected-profile illuminant
matrix pairs at endpoints, midpoint and outside bounds. The original full
selector and interpolation routines execute without algorithm stubs. Invalid
empty/duplicate/non-finite input is explicitly rejected, without claiming the
native routine safely handles malformed grids. The 89 library/five Unix tests,
no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-selection -- --adb SERIAL --report LOCAL.json`
after building host/ARM numeric fixtures. Full IQ is a local prerequisite and
is not committed. This step does not yet select the illuminant, derive saturation
from calibrated gain, apply damping or drive the live CCM controller. The actual
profile has illuminant blending disabled; its nearest-illuminant path remains
next. Physical CPU replay makes no ISP writes.

### Nearest CCM illuminant (0.0.34 development)

`ccm_illuminant::estimate` reconstructs complete
`illuminant_index_estimation_ccm` (ELF `0xfd394`, Ghidra `0x10d394`), the
selected profile's non-blended illuminant path. It compares current R/B gains
to each calibration's R/B pair with unweighted squared distance. Native first
rounds the blue squared difference, then executes `vfma.f32` for red squared
plus blue squared; Rust preserves that with `libm::fmaf`. A strict less-than
comparison preserves the earliest candidate on ties.

The initial best distance is exactly 9,999,999, not infinity. Native initializes
the output index to zero and returns −1 if no candidate beats that threshold
(including empty input); Rust exposes `matched: false` and index zero. Callers
must not mistake that index for a successful selection. Non-finite input is
explicitly rejected instead of inheriting unordered native comparisons.

[Native/physical CPU evidence](ccm-illuminant-equivalence.json) checks 1,013
cases: 1,000 varied inputs including empty, very distant, duplicate and tied
candidates, plus all seven selected-profile calibrations and six neighboring
midpoints. The actual complete native selector executes; only its diagnostic
logging call is suppressed. All chosen indices and match/no-match status agree.
The 90 library/five Unix tests, no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-illuminant -- --adb SERIAL --report LOCAL.json`
after building host and ARM fixtures. Full IQ remains a local prerequisite.
This does not yet implement gain-to-saturation mapping, the persistent
`selectCCM` update policy, damping or live CCM submission. No ISP writes occur
in CPU replay and live CCM remains disabled.

### Persistent non-blended CCM selection (0.0.34 development)

`ccm_runtime::State::process` reconstructs the full numerical/cache path of
`selectCCM` (ELF `0xfe000`, Ghidra `0x10e000`), joining nearest-illuminant
selection, the four-knot sensor-gain→saturation interpolation, descending
matrix-profile selection and fused matrix/offset interpolation. Its explicit
calibration records correspond to the native illuminant records; the calibrated
name buffers are fixed 25-byte NUL-terminated strings. The public API supports
up to nine illuminants and five profiles each, matching native context slots.
The initial implementation limited this to seven; public SDK layout verification
subsequently corrected the capacity to nine (the selected profile uses seven).
The existing verified saturation interpolation functions are reused, eliminating
duplicate arithmetic in `ccm_selection`.

The native context flags at `0x55f` and `0x560` are supplied explicitly as
`force` and `pending`; this step does not invent their surrounding lifecycle.
With both clear, the same illuminant and an absolute saturation delta no greater
than double-precision `1e-5` cause an early return, preserving the caller's
update flag and all cached bytes. Otherwise saturation/illuminant and profile
names advance. Forced updates, changed saturation or changed profile names
publish a matrix/offset result. Same-name/same-saturation paths retain cached
matrix values. String copies preserve bytes after the terminating NUL, as the
native `strcpy` does. Malformed selected calibration is rejected before committing
state or the caller's flag; this safe API boundary is not claimed native behavior.

[Whole native call-tree evidence](ccm-runtime-equivalence.json) compares 100
persistent sequences of 28 frames (2,800 frames), including ten sequences using
the selected profile's actual numerical calibrations. Profile names are short
synthetic labels; full IQ and the raw vendor code remain local prerequisites.
Repeated frames, gain changes, illuminant changes, forced/pending flags and
near-epsilon saturation changes compare every matrix/offset float bit,
saturation bits, illuminant index, both complete 25-byte name caches and the
update flag. Original `selectCCM` and all its numerical callees execute; ordinary
libc string/memory functions are controlled boundaries, not algorithm stubs.
Host and physical Luckfox Rust replay agree. The 91 library/five Unix tests,
no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-runtime -- --adb SERIAL --report LOCAL.json`
after building host/ARM numeric fixtures. This is persistent selection, not
native constructor/JSON loading, outer-frame flag ownership, temporal damping
or live CCM integration. Physical CPU replay makes no ISP writes; the live
camera still leaves CCM disabled until the remaining stages are verified.

### CCM temporal damping and convergence (0.0.34 development)

`ccm_damping::State::process` reconstructs the complete CCM `Damping` routine
(ELF `0xfd6f8`, Ghidra `0x10d6f8`). The library contains another function with
the same name for LUT3D; the reference resolves the exact CCM address explicitly.
For each of nine matrix values and three offsets, native first rounds
`target * (1 − damping)`, then performs fused `previous * damping + product`.
Rust preserves this operation order with `libm::fmaf`.

Native reports convergence only when every blended value differs from its
corresponding target by at most double-precision `1e-5`, after an f32 subtraction
and absolute value. Matrix and offset differences both count. The cache retains
the actual blended values even when converged; no snap-to-target is introduced.
All twelve values are updated even if an earlier coefficient already proves
non-convergence. Rust rejects non-finite input and damping outside [0,1] before
modifying the cache; these explicit safe API limits are not claims about native
handling of malformed arguments.

[Whole-native/physical CPU evidence](ccm-damping-equivalence.json) compares 100
persistent 32-frame sequences, 3,200 frames total. It includes zero/full damping,
intermediate factors, target changes and small positive/negative perturbations
near the convergence threshold. Every output float bit and convergence flag
matches the original entire routine, with no numerical or external-call stubs.
The 92 library/five Unix tests, no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-damping -- --adb SERIAL --report LOCAL.json`
after building host and ARM fixtures. Physical replay does not load the vendor
library or write ISP registers. The surrounding `AccmAutoConfig` chooses the
factor based on frame count, calibration, existing convergence and incoming
AWB damping. That ownership, additional saturation/luma transforms and live CCM
submission remain separate; current live capture still leaves CCM disabled.

### CCM saturation adjustment (0.0.34 development)

`ccm_saturation::apply` reconstructs complete `Saturationadjust` (ELF
`0xfd7e0`, Ghidra `0x10d7e0`). This transforms an already selected matrix;
it does not select an illuminant or choose calibrated alpha/saturation.
Alpha below double-precision `1e-5` leaves all bytes untouched. Otherwise
native first mixes matrix deviations from identity with alpha, transforms
columns to luma/chroma, scales chroma by `(saturation − 50)/50 + 1`, transforms
back, and removes the alpha mixing. Saturation 50 still executes that round
trip; Rust does not replace it with a mathematically tempting no-op.

The actual code mixes f32 and f64, explicit rounding between stages, and
fused multiply-add/subtract instructions. The forward transform uses the
binary's constants 0.299/0.587/0.114, −0.1687/−0.3313/0.5 and
0.5/−0.4187/−0.0813. The inverse uses 1.402, 0.34414, 0.71414 and 1.772,
plus native f32 zero terms. Rust uses `libm::fma`/`fmaf` in the recovered
instruction order, including those zero operations and identity-diagonal
handling, rather than a generic matrix library with different rounding.

[Native/physical ARM evidence](ccm-saturation-equivalence.json) compares all
36 output bytes across 1,000 identity/random matrices, neutral/end/intermediate
saturations and alpha values below/at/above the cutoff. Complete original
machine code executes, with no numerical substitutes. Rust accepts finite
matrices, alpha in [0,1] and saturation in [0,100]; invalid input is rejected
before modifying the matrix. Native out-of-domain behavior is not claimed.
The 93 library/five Unix tests, no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-saturation -- --adb SERIAL --report LOCAL.json`
after building host/ARM fixtures. Physical CPU replay makes no ISP writes and
does not load the vendor library. Calibrated alpha/saturation ownership,
luma-curve generation, outer scheduling and live CCM submission remain
separate; live capture continues to leave CCM disabled.

### Symmetric CCM luma curve (0.0.34 development)

`ccm_luma::symmetric` reconstructs complete `YAlpSymAutoCfg` (ELF `0xfe250`,
Ghidra `0x10e250`), the selected profile's symmetric mode. Each calibration row
is an ISO plus seventeen f32 alpha values. ARM instructions establish two
floating arguments (previous interpolation weight in s0, current ISO in s1),
plus count/table/previous-upper-index/force in r0–r3 and output/flag on the stack.
Ghidra's inferred signature obscures those float arguments.

Below the first ISO, native uses upper index one with weight zero; above the
last ISO, it uses the last index and weight one. Interior samples use the first
strictly greater ISO (last index at the final knot). The selected interval must
have span at least double-precision `1e-5`. Recalculation occurs when weight
changes by more than double-precision `0.01`, the upper index changes, or force
is set. The caller owns the prior index/weight; the routine does not advance
those arguments itself.

Each alpha is `floorf(fma(upper, weight, lower * (1 − weight)) + 0.5)`, with
native f32 rounding at every indicated stage. Native sums absolute f32 changes
across all seventeen values and copies the entire curve only if that sum exceeds
one. An exact change of one is suppressed. Rust preserves both gates and returns
whether publication happened, leaving prior curve bytes intact otherwise.
Malformed/non-finite input is explicitly rejected before modification.

[Native/physical CPU evidence](ccm-luma-equivalence.json) compares 1,003 cases,
including 100 using the selected profile's actual thirteen-row calibration,
endpoint/interior samples, caller cache/force combinations and explicit summed
changes of zero/one/two. All 68 output bytes and update flags match. The original
whole routine executes and its 16,711 floor calls execute the pinned ARM uClibc
`floorf` body in an isolated reference runtime; host math is not substituted.
The 94 library/five Unix tests, no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-luma -- --adb SERIAL --report LOCAL.json` after
building host/ARM fixtures. Physical replay does not load the vendor library
or write ISP registers. Asymmetric curves, calibration loading/ABI assertions,
outer flag/weight ownership and joined live CCM remain separate. The selected
profile sets asymmetric mode off; live CCM still remains disabled pending the
remaining integration and validation.

### CCM SDK layouts and static calibration fields (0.0.34 development)

Four public headers from the pinned Luckfox SDK commit are now provenance-pinned
in `artifacts.json`: `ccm_head.h` and the ACCM algorithm, internal and hardware
headers. Raw files remain in the ignored local header cache. ARM32 C assertions
compile the public declarations and verify complete IQ size 2164, result size
156, illuminant size 56, matrix-profile size 60 and symmetric-luma row size 72.
Assertions cover all consumed result fields and static IQ offsets. They also
establish native capacity of nine illuminants/five profiles each; runtime
selection's initial seven-illuminant limit was corrected and nine-illuminant
persistent native/physical replay added. The selected profile uses seven.

`ccm_calibration::static_fields` reconstructs `ConfigHwbyCalib` (ELF `0xfecd0`,
Ghidra `0x10ecd0`) from the explicit selected `ccm_calib_v2` JSON object. It sets
asymmetric/high-Y flags, left/right bounds, RGB→luma coefficients and three
u8 enhancement coefficients. Symmetric mode duplicates the bound and sets the
eighteenth alpha point to 1024; asymmetric mode preserves that point, forces
high-Y enabled and loads independent bounds. All unrelated fields and padding,
including enable/matrix/offsets/other alpha points/enhancement ratio, are retained.
This supports static fields in either layout, not asymmetric curve processing.

[Native/physical CPU evidence](ccm-calibration-equivalence.json) compares all
156 result bytes for the actual profile and 199 varied calibrations, both static
layouts and randomized prior results. Original `ConfigHwbyCalib` executes with
no algorithm substitutes. Input contains independently SDK-packed consumed
fields; native JSON parsing and the full constructor are not executed. Rust
validates every consumed field before mutation; malformed JSON preserves the
whole result. The 95 library/five Unix tests, no-default-features/static ARM
builds and expanded SDK layout checks pass.

Run `mise run camera:rust:ccm-calibration -- --adb SERIAL --report LOCAL.json`
after building host/ARM fixtures. This is the static portion of calibration
loading. Owned illuminant/profile tables, full constructor/outer-frame state,
joined automatic configuration and live CCM remain unfinished. CPU replay
makes no ISP writes; full IQ and raw vendor assets are not committed.

### Owned CCM calibration tables (0.0.34 development)

`ccm_calibration::Automatic::from_value` now loads the explicitly selected
symmetric/non-blended `ccm_calib_v2` object into owned tables: up to nine
illuminants, their gain→saturation curves and up to five named matrix profiles,
thirteen symmetric luma rows, nine-knot alpha-scale/enhancement curves, control
tolerances, enable/damping/enhancement flags, and the static result fields.
`views` borrows the owned illuminant/profile data for the verified selector.
No native pointers or full vendor JSON object are retained in the numerical path.

The native `pCcmMatrixAll_init` (ELF `0xfdc04`) resolves each `matrixUsed` name
through complete `CamCalibDbGetCcmProfileByName` (`0xfdba8`), then stable-sorts
profiles descending by saturation. Rust follows that binding/order rather than
assuming JSON order. Counts, finite arrays, increasing gain/ISO grids, NUL-free
1–24-byte names, unique matrix names, resolvable references and strictly descending
resolved saturations are validated. Duplicate/malformed inputs fail explicitly;
this is a safe supported-input boundary, not a claim of native malformed-input
semantics. Asymmetric or blended-illuminant profiles remain unsupported here.

[Native binding/physical CPU evidence](ccm-tables-equivalence.json) checks the
actual complete selected profile plus 31 varied/shuffled versions. Native full
name lookup/sort and static configuration run; every resolved name and profile
float bit matches. All loaded control/curve fields are independently mapped from
JSON and compared by f32 bits; their downstream algorithms have separate native
evidence. Libc string/memory helpers are explicit controlled boundaries.
The native JSON parser/full constructor are not executed. Full IQ/fixture
contents remain local and are not committed.

The 96 library/five Unix tests, no-default-features and static ARM builds pass.
Run `mise run camera:rust:ccm-tables -- --adb SERIAL --report LOCAL.json` after
building host/ARM fixtures. Physical replay loads only the Rust fixture program,
not the vendor library, and makes no ISP writes. The next integration is the
outer automatic CCM state and result publication; live CCM remains disabled.

### CCM input deadband (0.0.34 development)

`ccm_input::filter` reconstructs complete `JudgeCcmRes3aConverge` (ELF
`0xfe1dc`, Ghidra `0x10e1dc`). Its mutable records are `[sensor gain, red WB
gain, blue WB gain]`: a stored baseline and current proposed inputs. A gain
change no greater than the absolute gain tolerance replaces current gain with
the held baseline. A greater change advances the baseline to current gain and
sets the change flag. White balance uses the analogous radial R/B tolerance,
comparing squared distance with tolerance squared. The blue squared difference
is rounded first and red squared is fused into it, matching `vfma.f32`.
At equality the prior inputs are retained. Either significant component sets
the return flag, while gain/WB baseline updates remain independent.

This is the outer controller's input hold/update gate, not a test of final
matrix convergence. `AccmConfig` invokes it before deciding whether selection
and automatic configuration need to run. The selected profile's WB tolerance
is zero; the implementation does not invent a larger noise threshold.

[Complete native/physical CPU evidence](ccm-input-equivalence.json) checks 100
persistent 32-frame sequences (3,200 frames), including identical inputs,
tolerance boundaries, radial R/B changes and the actual .2/0 tolerance pair.
All 24 baseline/current record bytes and the change flag agree. The original
entire gate executes with no numerical/external stubs. Rust rejects non-finite
records and negative/non-finite tolerances before modifying either record.
The 97 library/five Unix tests, no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-input -- --adb SERIAL --report LOCAL.json` after
building host/ARM fixtures. Physical replay makes no ISP writes. Joined
`AccmConfig`/`AccmAutoConfig`, constructor-owned defaults/flags and live CCM
submission remain next; the camera still leaves CCM disabled.

### Joined automatic CCM configuration (0.0.34 development)

`ccm_automatic::State` joins the supported numerical/state behavior of complete
`AccmConfig` (ELF `0xff10c`) and `AccmAutoConfig` (`0xfed30`). Input filtering,
selection, alpha scaling, symmetric luma publication, saturation adjustment,
full-result damping and enhancement updates now run as one persistent controller.
The supported profile is symmetric/non-blended, with constructor-default user
inhibition zero and user saturation 50; arbitrary user adjustment attributes,
manual mode and full native ABI ownership are outside this API.

`State::new` explicitly reproduces the relevant `ConfigbyCalib` result/defaults:
first-row alpha curve, static bounds/coefficients, initial enhancement flag/ratio,
unit input/baseline records, zero target matrix/cache, and alpha cache one.
Native constructor saturation cache starts at 100 while its user saturation
curve is 50; this distinction is retained. This initialization boundary is
explicit: the whole native constructor/JSON parser is not executed in this test.

Frame controls remain explicit: native active byte `0x55c`, attribute/reconfigure
flags, gray mode, and caller-owned prior-publication flag `0x560`. Small inputs
are held by the verified deadband. When input/attributes change or damping has
not converged, automatic configuration runs. Damping is zero until frame count
reaches two and when calibration/active state disables it. Luma is scaled and
static fields restored in native order; enhancement changes and ongoing damping
can publish without a new selected matrix. Whole-frame state is staged and
committed only after all supported stages succeed; a late invalid-alpha failure
test verifies no partial commit after input/selection work.

[Full native call-tree/physical CPU evidence](ccm-automatic-equivalence.json)
compares 32 persistent 24-frame sequences (768 frames). The original complete
`ConfigbyCalib`, `AccmConfig` and `AccmAutoConfig` execute with their numerical
callees; only libc string/memory boundaries are modeled, and original ARM uClibc
`floorf` executes. Every 156-byte result, selected names/matrix/offset cache,
saturation/illuminant, baseline/current inputs, alpha/saturation caches,
convergence, frame count, input-change and publication flag matches. Cases cover
held/changed inputs, startup/active flags, reconfiguration/attributes, gray and
disabled output, damping disabled/enabled, varied alpha scales, enhancement
curves and WB tolerances. Raw IQ and constructed fixtures remain ignored.

The 98 library/five Unix tests, no-default-features and static ARM builds pass.
Run `mise run camera:rust:ccm-automatic -- --adb SERIAL --report LOCAL.json`
after building host/ARM fixtures. This qualifies joined configuration under
explicit initialization/control boundaries, not outer callback integration,
physical ISP writes, image quality or a full RKAIQ replacement. Native full
constructor defaults/callback ownership and transactional camera submission
remain to be closed before enabling live CCM.

### Native CCM constructor proof (0.0.34 development)

[Full-constructor evidence](ccm-initialized-equivalence.json) replaces the
previous manually seeded initialization boundary with actual complete `AccmInit`
execution (ELF `0xff36c`). The reference selects ISP32 in the native hardware
version global and supplies a scene-root pointer whose native module-table
entry resolves to the independently packed CCM SDK object. The original lookup,
name comparisons, context memset, calibration/name-table initialization and
constructor default writes all execute. No module-lookup or initializer function
is replaced. Only one controlled allocation of the native 0x564-byte context
and ordinary libc string/memory helpers are modeled.

All selected initial result/cache/control fields match Rust `State::new` for
32 profile variations, before any frame runs. They then remain exact through
768 automatic controller frames. This checks full 156-byte results and every
state key listed in the report, including saturation initialization at 100,
unit current/baseline inputs, zero selection cache, convergence/frame/publication
state and alpha cache. Original uClibc `floorf` executes for subsequent curves.
Host and physical Luckfox Rust replay agree. The 98 library/five Unix tests,
no-default-features and static ARM builds pass.

Run `mise run camera:rust:ccm-initialized -- --adb SERIAL --report LOCAL.json`
after building host/ARM fixtures. The native JSON parser is not executed;
independent SDK input packing remains explicit. This does not claim byte-for-byte
native context/ABI compatibility: pointer/metadata/manual-attribute storage and
unconsumed state are not represented by the Rust controller. Symmetric,
non-blended profiles and default user adjustments remain the supported path.
Callback ownership and live transactional submission remain next. Physical CPU
replay loads no vendor library and makes no ISP writes.

### Complete CCM callback and publication (0.0.34 development)

`ccm_frame::State::process` reconstructs the supported complete CCM `processing`
callback at ELF `0xfd126` (Ghidra `0x10d126`). Its identity is verified through
`g_RkIspAlgoDescAccm` at ELF `0x1a7fdc`: descriptor offset 36 points to Thumb
`0xfd127`. Other same-named callbacks exist; `0xff59c` is gamma and is not this
CCM routine. Public SDK ARM C assertions now independently verify the 32-byte
`accm_sw_info_t` and its damping/gray/AWB-convergence/prepare/CCM-convergence offsets.
The typed API excludes arbitrary padding and unused metadata, not native ABI
compatibility.

Native marks publication on software-gray/current-gray transitions, writes
current gray and *pre-process* CCM convergence back to input software information,
then calls `AccmConfig`. It copies the complete 156-byte result only when an
update is requested, preserving output bytes otherwise, and always clears the
internal publication flag afterward. The Rust wrapper retains constructor
reconfiguration for the first call and owns attribute/reconfiguration flag
consumption. All typed state/input changes are staged until supported processing
succeeds; output is copied only on publication.

The callback comparison uncovered a controller gap that earlier direct tests
did not expose: with publication already pending, unchanged names/saturation
can bypass the selector's ordinary early exit, return a clamped pair without
publishing a matrix, and retain native status −21. Native `AccmAutoConfig` stops
that pass, even though its outer callback may still publish the old result.
Rust previously discarded selector status and continued alpha/damping work.
`ccm_runtime` now returns native status and `ccm_automatic` preserves this early
exit. A focused unit regression and explicit native-status comparisons were
added; the existing 2,800-frame selection replay now includes eighteen −21 cases.

[Whole-callback evidence](ccm-frame-equivalence.json) executes the real descriptor
callback after complete native `AccmInit`, including actual ISP32 module lookup.
Across 32 sequences/768 frames, all output/result bytes, input gray/convergence
mutations, selected caches, current/baseline inputs and controller state match.
There are 550 publications and 218 no-update cases, with publication cleared
after every call. Sequence seven/frame eight retains the discovered gray-return
regression. Original uClibc `floorf` executes; only one context allocation and
ordinary libc string/memory boundaries are modeled. Host and physical Luckfox
CPU replay agree. The 99 library/five Unix tests, no-default-features/static ARM
builds and expanded SDK layouts pass.

Run `mise run camera:rust:ccm-frames -- --adb SERIAL --report LOCAL.json` after
building host/ARM fixtures. The supported path remains symmetric/non-blended
with default user adjustments. Native JSON parsing, arbitrary raw SDK ABI,
manual/HDR/multicamera modes and live camera submission are not qualified by this
result. CPU replay makes no ISP writes. Transactional integration and real
capture verification are next; live CCM remains disabled until then.

### Transactional live CCM (0.0.34 development)

The startup builder now generates and packs its first CCM result from the
selected calibration, requested initial gain and seeded WB ratios. Diagnostic
WB overrides regenerate CCM too. The event owner retains that seeded state
only on a successfully started parameter pipeline, so runtime begins after
the startup result rather than restarting the controller's frame count.

Live inputs follow the linear `RkAiqAccmHandleInt::processing` value mapping
(ELF `0x64318`): `(analogue × sensor-digital) × ISP-digital`, R/Gr and B/Gb.
This multiplication order differs from DPCC's recovered order. The pinned BLC
guard requires unity optical-black pre-gain, so no extra gain factor is added.
Native `awbProcessing` publishes the base IIR coefficient from context `0x3484`;
`Session::ccm_damping` exposes that verified AWB state. Both gain and coefficient
are retained under their exact statistics frame, preventing later AWB processing
from replacing an older queued frame's CCM inputs. AE inputs use the same
explicit effective-exposure association as gain/demosaic/DPCC, without claiming
independent physical timing proof.

CCM processing/output and all state changes are staged with the ordinary ISP
batch. Accepted QBUF commits state, the output cache and packed snapshot; failed
acquisition/enqueue preserves them, including frame count and pending tuning.
The six ARM simulated startup scenarios now explicitly gate transactional CCM
failure/retry coverage. A true no-hardware-update step can commit its internal
state without QBUF; any CCM publication requests its module update in the batch.
Logs record every committed step and distinguish update from held output.

[Live camera evidence](ccm-live-validation.json) covers a 192-image run, a
600-image run and the installed application scan workload. All 640 runtime CCM
results and three startup results match full original construction/callback
execution; all 148 runtime packed updates match original conversion. The longer
run processed 400 AE/AWB statistics frames and accepted 399 batches, with 38 CCM
updates and 361 held results. Snapshot retention peaks at two and no parameter
pool waiting occurs. Both finite runs retain native DPCC/demosaic equivalence;
final AWB translations match all 7,680 bytes. The app scan adds 114 accepted
batches, twelve real decoder-input frames and 28 headless preview renders,
with clean owner exit. Those counts are not successful optical decodes.

Run `mise run camera:rust:ccm-live-check -- LOCAL_CAPTURE_BASE --report LOCAL.json`
with the pinned original library/runtime and IQ prerequisites. Only hashes and
metadata are committed; scene images, full IQ and raw vendor code remain ignored.
The [current startup audit](profile-module-audit-0.0.34-ccm.json) independently
confirms CCM/DPCC enabled and six remaining profile gaps: LSC, BAYNR, BAY3D, YNR,
CNR and SHARP. The frozen 0.0.33 kit and its audit remain unchanged. Current
CCM qualification is warm capture on the previously verified driver-only boot;
physical register timing, calibrated color quality, successful optical QR and
an exact new-package cold boot remain separate.

### LSC selected-result serialization (0.0.34 development)

`isp_lsc::apply` reconstructs the LSC result-type-10 case inside complete
`Isp32Params::convert3aResultsToIspCfg` (ELF `0x304c4`). It accepts the public
SDK's 2442-byte `rk_aiq_lsc_cfg_t` and writes the 2449-byte packed kernel
`isp3x_lsc_cfg` at offset `0x894`. ARM-target C assertions independently compile
both declarations and verify sizes, plane/geometry/enable offsets and module
bit 4. Three public ALSC headers are provenance-pinned in `artifacts.json`;
raw header downloads remain in the ignored local cache.

The SDK has four 17×17 planes, 289 u16 entries each. The kernel has 290 entries
per plane. Native copies the first 289, preserving the previous kernel value
in slot 290. When enabled, it clamps **all 290**, including that retained slot,
to 8191. When disabled, it does not clamp. In either case it copies four
sixteen-entry gradient/size tables and sets `sector_16x16` to one. SDK trailing
padding and unrelated parameter bytes remain untouched.

Native always sets enable-update bit 4. Enabled results set both module-enable
and configuration-update bit 4; disabled results clear both, unlike the DPCC/CCM
enable-mask asymmetry. The serializer also updates the original converter
context's cached enabled byte (offset `0x68` at the controlled base offset);
Rust represents that state explicitly rather than claiming a native C++ layout.

[Full native dispatcher/physical CPU evidence](isp-lsc-equivalence.json) checks
1,000 cases, comparing every one of the 11,145 output parameter bytes and cached
enable state. Random prior contents/masks, non-boolean enable bytes, explicit
8190/8191/8192/65535 table boundaries and retained-slot values cover both paths.
The full original dispatcher branch executes; only the valid typed C++
`dynamic_cast` is controlled. Original result bytes and all other converter
context bytes are independently checked unchanged. Host and physical Luckfox
Rust replay agree; SDK/kernel layout checks, 99 library/five Unix tests,
no-default-features and static ARM builds pass.

Run `mise run camera:rust:isp-lsc -- --adb SERIAL --report LOCAL.json` after
building host/ARM fixture tools. This is conversion of an explicit result,
not calibrated LSC selection, geometry, damping, OTP handling or `AlscConfig`.
Physical CPU replay makes no ISP writes and loads no vendor library on the
board. Live LSC remains disabled until the remaining input/controller path is
verified; the existing live CCM binary and frozen 0.0.33 archive are unchanged.

### LSC sector gradients (0.0.34 development)

`lsc_geometry::gradients` reconstructs the positive-sector calculation in
complete `AlscManualGrad` (ELF `0x119018`, Ghidra `0x129018`). For sixteen
positive u16 lengths on each axis, native calculates `32768 / length + 0.5`
in f64, then truncates to the u16 gradient. The numerator and precision were
checked in the original instructions/data, rather than inferred from the
register width. Rust rejects zero on either axis before producing output;
it does not reproduce native partial writes on an invalid later sector.

[Native/physical CPU evidence](lsc-gradients-equivalence.json) checks all 32
output u16 values in 1,000 cases. One uses the selected profile's actual
sixteen x/y sectors for its `2304x1296` calibration; the others vary positive
u16 lengths, with explicit 1/2/3, powers/neighbors and 65535 values. Original
entire `AlscManualGrad` executes with no algorithm/math substitutes, and every
context byte outside the gradient arrays is checked unchanged. Host and
physical Luckfox Rust replay agree. The 100 library/five Unix tests,
no-default-features and static ARM builds pass.

Run `mise run camera:rust:lsc-gradients -- --adb SERIAL --report LOCAL.json`
after building host/ARM fixtures. This closes inverse-gradient math, not the
automatic selection/copying of resolution geometry. The profile's sector sums
are 2304×1296; the VGA image output must not be substituted without verifying
which sensor/ISP input crop the LSC stage actually covers. Automatic table and
resolution selection, temporal state and live LSC remain unfinished. CPU replay
makes no ISP writes and the current camera path still has LSC disabled.

### LSC illuminant history (0.0.34 development)

`lsc_illuminant::State` reconstructs the nearest-illuminant estimator (ELF
`0x118498`) and the history used by `UpdateDominateIlluList` /
`StableIlluEstimation` (`0x118528` / `0x118576`). The estimator uses f32 deltas,
fused red-square accumulation and a rounded square root, with strict `<`
comparison against an initial 9,999,999 distance. Replacing this with squared
distances can change rounded ties. Until fifteen successful observations,
native selects the nearest illuminant. Once full, it chooses the most frequent
index in the last fifteen observations; equal counts favor the lowest index.
A no-match result leaves the output index and history unchanged.

[Native/physical CPU evidence](lsc-illuminant-equivalence.json) covers 104
persistent sequences / 6,624 frames, including ten sequences using the selected
IQ profile's seven WB pairs, exact distance ties, mode ties, window turnover,
empty groups and failed matches interleaved with successful observations.
All three complete original routines execute, including native linked-list
updates, with original uClibc `sqrtf`. The oracle models allocation/free and
suppresses diagnostic logging; it checks the whole ordered history and each
backward link as well as both nearest and stable selection. Host and physical
Luckfox Rust agree on every output. All 101 library/five Unix tests,
no-default-features and static ARM builds pass.

Run `mise run camera:rust:lsc-illuminant -- --adb SERIAL --report LOCAL.json`
after host/ARM fixture builds. Rust supports finite gains and SDK groups of up
to seven illuminants; reset history when replacing calibration. This closes
illuminant history only: resolution/table selection, vignetting interpolation,
damping, OTP and live integration still need verification. CPU replay makes
no ISP writes; the live camera keeps LSC disabled.

### LSC target table selection (0.0.34 development)

`lsc_tables::select` stably sorts up to five profiles by descending vignetting,
clamps to the highest/lowest endpoint outside the range, and blends adjacent
profiles inside it. Equal sort keys retain their input order. The selected
profile's gain/vignetting curve uses the existing recovered interpolation.
For a blend, native computes an f32 weight, independently truncates both
`weight * 65536` and `(1 - weight) * 65536`, and rounds the integer weighted
sum with `+32768` before shifting. Computing one integer weight as the
complement of the other can change output. All four 17×17 planes retain their
SDK order: red, green-red, green-blue, blue.

[Native/physical CPU evidence](lsc-tables-equivalence.json) covers 319 complete
four-plane targets: 63 gain samples across all seven illuminants from the
selected board profile, plus 256 varied cases with 1–5 profiles, shuffled
input order, duplicate vignetting keys, endpoints, interior samples and full
u16 grid values. The full original `OrderLscProfilesByVignetting` and
`AlscAutoConfig` execute. Every interpolated vignetting bit, selected high/low
profile index and all 2,312 grid bytes match Rust on host and physical Luckfox.
The oracle also verifies native no-OTP output equals its target with damping
inactive on frame zero. All 101 library/five Unix tests, no-default-features
and static ARM builds pass.

Run `mise run camera:rust:lsc-tables -- --adb SERIAL --report LOCAL.json` after
host/ARM fixture builds. The oracle directly constructs the SDK pointer graph
and forces a fresh target; constructor/parser, name lookup, persistent cache
and temporal damping are separate. Modeled allocation/free, string operations
and suppressed logging form the boundaries; native selection, interpolation
and grid loops execute without algorithm substitutes. Live LSC stays disabled;
physical CPU replay makes no ISP writes.

### LSC no-OTP damping (0.0.34 development)

`lsc_damping::process` reconstructs the no-OTP temporal update inside complete
`AlscAutoConfig`. It truncates the previous-grid coefficient times 65536,
uses its integer complement for the new target, and rounds every weighted
u16 sum with `+32768` before shifting. The coefficient is zero when calibration
damping is disabled or native frame count is below two. Supported coefficients
are finite values in `[0,1]`.

Native convergence observes only the first and last samples across the four
planes: both `abs((previous - target)/(previous + target))` must be strictly
below f32 `0.015`. When they are, the entire output snaps to the target,
including middle samples that might still differ greatly. Zero/zero yields
NaN and does not count as convergence. Rust preserves this observed behavior.

[Native/physical CPU evidence](lsc-damping-equivalence.json) compares all
2,312 output grid bytes and the convergence flag for 16 sequences / 512
frames. Previous native output feeds the next input. Cases include actual
calibration grids, target changes, factors 0/0.25/0.5/0.9/0.99/1, startup-frame
and enable gates, strict-threshold neighbors, mismatched middle samples,
zero endpoints and u16 extremes. There are 251 converged and 261 unconverged
results, with no mismatches on host or physical Luckfox. All 101 library/five
Unix tests, no-default-features and static ARM builds pass.

Run `mise run camera:rust:lsc-damping -- --adb SERIAL --report LOCAL.json`
after host/ARM fixture builds. The oracle executes full native automatic
configuration with a constructed one-profile calibration, forced fresh target
and supplied previous grid. Persistent target-cache decisions, constructor,
processing callback and OTP handling remain separate. CPU replay makes no
ISP writes; live LSC is still disabled.

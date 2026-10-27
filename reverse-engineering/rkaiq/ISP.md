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

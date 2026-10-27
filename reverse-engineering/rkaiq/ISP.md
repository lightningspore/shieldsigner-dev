# ISP startup reconstruction

The Rust replacement continues to use the Luckfox SDK's Linux ISP/sensor drivers and physical ISP hardware. The proprietary userspace RKAIQ library chooses calibrated parameters, configures the graph/queues, and runs the automatic control algorithms. Replacing that library requires all of those responsibilities; a frame captured from an already initialized pipeline does not establish independent startup.

## Current implementation priority

The next deliverable is one runnable SC3336/RV1106 camera path, rather than another release containing isolated routines. The first hardware checkpoint is a usable frame after starting with the vendor camera/bootstrap services disabled. Then verify the application's QR capture and the exposure/white-balance behavior required to make it reliable. This is a staged checkpoint toward the Rust replacement, not a redefinition of completion as fixed controls or vendor-assisted capture.

The immediate bottlenecks are the live media/format backend, a sufficient calibrated initial ISP parameter record, and persistent ownership/order of the parameter and capture queues. Connect those before extending optional algorithm modes or adding broader equivalence corpora. Reuse the recovered algorithms needed by the actual single-camera linear path. HDR, multiple cameras/ISPs, unused tuning branches and optional image-quality features are deferred unless the functional path demonstrates a dependency on them.

The live Linux format/link adapter is now implemented below, with positive device operation still untested. The kit still does not generate a sufficient initial parameter record, and capture may depend on earlier vendor initialization. The existing numerical results remain useful validation, but additional passing routine counts do not satisfy this hardware checkpoint. Development after kit 0.0.28 is being assembled toward the runnable camera milestone rather than released as another standalone-routine kit.

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
hardware path, SOF-map/controller synchronization and whole-routine native
queue equivalence remain unverified. It does not add automatic 3A.

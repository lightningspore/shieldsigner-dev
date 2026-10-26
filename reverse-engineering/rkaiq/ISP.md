# ISP startup reconstruction

The Rust replacement continues to use the Luckfox SDK's Linux ISP/sensor drivers and physical ISP hardware. The proprietary userspace RKAIQ library chooses calibrated parameters, configures the graph/queues, and runs the automatic control algorithms. Replacing that library requires all of those responsibilities; a frame captured from an already initialized pipeline does not establish independent startup.

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

The Rust backend trait exposes these operations explicitly. **There is no live backend for this helper yet.** `numeric-fixture` supplies controlled driver records and records each call. Kernel UAPI cross-compilation independently checks 88-byte format/64-byte selection layouts, field offsets, ACTIVE/CROP constants and get/set ioctl numbers.

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

The native Ghidra exports now include hardware `init`, `prepare`, `start`, `setupPipelineFmt`, CIF/ISP format helpers and parameter submission. The next implementation work is to connect the format/link setup to real device adapters, recover calibrated initial module configuration, implement parameter queue ownership/lifetime, synchronize it with statistics/image streams, and reproduce restart/cleanup. AWB/gain parameter serializers and statistics capture already exist separately; they do not constitute full initialization. Real hardware must then validate cold boot without a vendor bootstrap, frame quality, exposure/WB response and restart behavior.

For focused exports, `ExportRkaiq.java` accepts an optional second argument containing a Java full-match symbol regex. Its default selection remains unchanged. Exported pseudocode stays in ignored tool caches and is not distributed in the test kit.

## Black-level parameter block

`isp_black_level::apply` reconstructs `Isp32Params::convertAiqBlcToIsp32Params`, ELF `0x2d58c` (Ghidra `0x3d58c`). This converts an already selected algorithm result into the full 44-byte `isp32_bls_cfg` at parameter offset `0x7ae`, then copies that block into explicit cached storage. It does not select/interpolate the calibration or submit a buffer.

The native routine always marks black-level configuration and enable-update masks (bit 1). If the input main enable is true, it sets the module enable bit. If false, it **preserves** the old enable bit rather than clearing it. It zeroes automatic/window selection, sample count and both measurement windows, copies signed R/Gr/Gb/B fixed offsets unchanged, and copies stage-1 enable. These semantics must not be replaced by a conventional enable/disable setter.

With zero optical-black predgain, signed stage-1 offsets are copied unchanged, including negative values. With nonzero predgain, each signed channel is multiplied in f32, converted to signed integer by truncation, then clipped to 0–32767. The optical-black offset is clipped to 0–511, predgain is converted to Q8 and clipped to 0–65535, and maximum is clipped to 0–1048575. The input optical-black enable boolean is not read by this converter. The Rust checked API rejects nonfinite predgain before changing the record or cache.

`mise run camera:rust:isp-black-level` compares all three u64 masks, every byte of the block and cache against 1,000 executions of the original ARM converter. Both native and Rust harnesses verify preservation of unrelated bytes in the 11,145-byte parameter record; native context and source-input preservation are also checked. The corpus includes zero/negative/large/fractional gain, f32 extrema and subnormal gain, signed channel extremes, clipping boundaries, every enable combination and two C++ virtual-base offsets. This converter runs without algorithm/device stubs. [Reference report](isp-black-level-equivalence.json).

The exact SDK `AblcProc_V32_s` input declaration is SHA-pinned and independently cross-compiled for ARM to check its 32-byte layout and all used offsets. Kernel header assertions check the BLS block size, offset, member offsets and mask. This establishes serialization fidelity, not calibrated image quality or complete initial IQ configuration. Demosaic, measurement configuration and other ISP modules still need reconstruction/integration before independent startup is available.

## Demosaic hardware controls

`isp_demosaic::quantize` reconstructs `AdebayerGetProcResult`, ELF `0x115880` (Ghidra `0x125880`). `SelectedParameters` exposes the SDK's selected tuning values as named Rust fields. They can also be decoded from its checked 132-byte value record. This stage consumes already selected values; the automatic ISO-dependent table selector, IQ loading and frame-state integration remain unfinished. The hardware ISP still performs the actual Bayer-to-RGB processing.

Quantization preserves signed filter coefficients and copies discrete controls/offsets into a 112-byte hardware record. Edge/alpha scales use Q10; weight slope uses Q7. Rounding adds signed 0.5 in **f64 after f32 arithmetic**, then truncates to signed i32. The inverse bilateral sigma conversion truncates directly without that half-step rounding. Byte/halfword narrowing preserves the original wrapping behavior rather than substituting clipping. The chroma normalization combines a rounded inverse-strength term with the narrowed weight slope using wrapping 32-bit multiplication, then derives its shift from `log(product)/ln(2)-7`, limited below at zero. The exact recovered constants are used, including 78715.2890625 and 55659.7265625, rather than recomputed approximations.

The returned hardware record retains the cached update flag and padding. After returning that value, the cached record has only its update flag cleared, matching the native `memcpy`-then-clear sequence. This helper does not set the flag when tuning changes; the outer processing state must do that. Checked Rust rejects nonfinite fields, nonpositive inverse-filter inputs and nonpositive wrapped normalization products before any cache mutation. A rejected input therefore cannot leave a partially updated record.

`isp_demosaic::apply` reconstructs `convertAiqAdebayerToIsp32Params`, ELF `0x2ca90` (Ghidra `0x3ca90`). A false update flag leaves **every** parameter byte unchanged. An enabled update sets bit 35 in all three masks. A disabled update sets enable-update, clears the module enable bit, and preserves the previous configuration-update mask. Both active-update branches copy the full 57-byte packed block at `0x1282`. Signed i32 filter coefficients narrow to their low byte, and all unrelated parameter bytes are preserved.

`mise run camera:rust:isp-demosaic` checks 1,000 selected-value/hardware/cache cases followed by 1,000 independent hardware/kernel-packing cases. The original RKAIQ instructions execute under Unicorn; its `log` dependency executes the pinned SDK uClibc **ARM code**, with no imported runtime calls reached. Only standard `memcpy` is modeled. The harness passes double arguments through D registers after its register reset; existing single-float argument behavior is unchanged. Integer output equality is the claim, not universal equality of the Rust/native logarithms.

The corpus checks every hardware/cache byte, all three parameter masks and the entire kernel block, plus preservation of unrelated context/parameter bytes. It covers update/enable combinations, coefficient narrowing, signed rounding ties, saturating float-to-i32 conversions, powers-of-two normalization and positive products after native multiplication wraps. [Reference report](isp-demosaic-equivalence.json). Cross-compiled verbatim SDK declarations independently verify both value layouts and all used offsets; pinned kernel assertions verify the 57-byte packed block and module mask. These controls still require calibrated inputs, other initial ISP modules and live queue submission before independent camera startup can be claimed.

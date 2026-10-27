# RKAIQ → Rust reconstruction

**Status: partial numerical reconstruction and camera-test tools. This is not a replacement `librkaiq.so`, and the existing image is unchanged.** The active objective is a Rust implementation of the camera-processing path used by ShieldSigner. A clean-boot hardware session has now produced a recognizable 640×480 ISP frame and valid AE statistics; automatic 3A and application integration remain unfinished.

**Current priority: a runnable single-camera path.** Connect live graph/format setup, calibrated initial parameters and persistent queues before expanding optional algorithms or releasing more isolated routine kits. The next functional checkpoint is a usable SC3336 frame without vendor bootstrap, followed by the application's QR capture and required exposure/white-balance behavior. [Critical path and current blockers](ISP.md#current-implementation-priority).

## What is implemented

- Ten recovered numerical routines in [`firmware/rkaiq-rs`](../../firmware/rkaiq-rs): scalar interpolation, saturation color-matrix interpolation, saturation-offset interpolation, 9×9×9 RGB LUT blending, defect-pixel calibration interpolation, the multiplicative gain-quantization branch, and the full linear/two-frame/three-frame gain-register conversion, ISO calibration selection, ISP32 white-balance gain serialization, and exposure digital-gain application.
- **9,050 deterministic comparisons, zero mismatches** between compiled Rust and actual instructions from the pinned ARM library under Unicorn. Float results are compared as exact IEEE-754 output bits; LUT outputs compare all 2,187 u16 entries. [Report](numeric-equivalence.json).
- A **standalone, statically linked ARMv7 Linux `camera-probe`**. It inventories video nodes, supported formats and media entities, reports active vendor camera processes, and supports bounded single-/multi-plane MMAP frame capture.
- A Rust **`frame-preview`** converter for uncalibrated grayscale inspection of supported YUV/luma/Bayer captures. Bayer preview uses simple 2×2 binning, not the vendor ISP algorithm.
- A static ARM `numeric-fixture` executable and reference corpus for checking the recovered routines on the actual processor.

The probe uses Linux's existing V4L2/media interfaces and does not call or link RKAIQ. Development can now configure explicitly supplied media links and formats, but **does not yet supply complete calibrated ISP startup, an exposure/white-balance loop, or a replacement camera service**. Capturing from a graph previously initialized by the vendor is a useful diagnostic, not proof of an independent cold-start implementation.

A recovered Rust service controller also matches **100 original-daemon event traces** for initialization call order, stream subscriptions, and alternating start/stop filtering. Its processing backend is still incomplete: this is not a working substitute for the camera daemon. See [LIFECYCLE.md](LIFECYCLE.md). `camera-probe events` observes real driver events without configuring the ISP.

The sensor binding selector also matches **1,000 controlled inventories** against the original instructions. It preserves ISP/CIF path precedence, name exceptions and media-probe outcomes. The live media inventory now reads pads/links and reports enabled entity-level sensor paths within each media device; full cross-media inventory construction is not implemented by this selector. See [DISCOVERY.md](DISCOVERY.md).

A borrowed full-ISP32 statistics decoder now exposes AE grids/histograms and AWB blocks/light sums/luma histogram. **100 AWB buffer comparisons** match the original translator; AE raw field layout is checked against kernel headers. `capture-statistics` reads the existing metadata queue with bounded MMAP capture and strict format checks. Real queue operation still needs hardware validation; this does not implement the exposure or white-balance algorithms. See [STATISTICS.md](STATISTICS.md).

The AE0 5×5 correction helper now matches **1,000 original-ARM cases** across all six selection branches and both luma ranges, including signed correction, clipping and weighted means. This helper consumes calibration/gain/weight inputs; the complete automatic exposure controller remains unfinished. See [AE.md](AE.md).

AE histogram correction also matches **1,000 original-ARM cases**, covering 64/256 bins, R/G/B/luma modes and bypass. It retains native intermediate narrowing, bin-center selection and u32 count wrapping.

Large 15×15 AE grid correction and four RGB subwindow sums now match **1,000 original-ARM full-record comparisons**, including preserved window-channel fields and weighted means.

The linear sensor-write sequencer matches **1,000 original-ARM traces**, including write failures and cached frame-length side effects. A Linux write adapter now backs the explicit `apply-linear` command; actual camera operation remains unvalidated. See [SENSOR.md](SENSOR.md).

`exposure::convert` now reconstructs gain and shutter register conversion, with **1,000 resulting-code comparisons** against original RKAIQ plus the pinned SDK uClibc math instructions. It covers linear/HDR timing, DCG ratios, gain-band/fallback and logarithmic models. Calibration must still be supplied; live writes require the separate explicit `apply-linear` command.

Sensor descriptor construction now matches **1,000 original-ARM cases**, including timing minima, pixel-clock fallback, format mapping and optional-query failures. `camera-probe sensor-info` adds a read-only driver adapter for hardware validation.

The IQ JSON exposure subset is now loaded into the recovered converter. **100 SDK-profile integration cases** match native RKAIQ/uClibc results, and the offline planner passes ten input/error checks. `camera-probe exposure-plan` combines an IQ profile and saved sensor descriptor without opening a camera device. See [CALIBRATION.md](CALIBRATION.md).

`camera-probe apply-linear` now provides manual driver control writes through the recovered sequencer, records each write and partial failures, and queries control readback/ranges. It does not run AE or initialize the camera pipeline.

The histogram-driven `ClmExecute` exposure solver is now reconstructed, including tail-bin extrapolation, iterative clipped-brightness prediction, relative-growth cap and saturation-flag behavior. This is the inner proposal stage; outer AE integration, routes, limit application and synchronized control remain unfinished.

History-based `AecDynamicDamp` now matches **1,000 original-ARM cases**, including the 9×9 rule surface, custom mode, ring wrap, linear/HDR diagnostic writes and disabled behavior. This returns a damping coefficient; it does not complete the outer controller or independent ISP startup. See [AE.md](AE.md).

The ISP pad-format/crop setup sequence now matches **1,000 original-ARM traces**, including shared-CIF behavior, optional scaler calls, complete record preservation, adjusted crop responses and first-error returns. That reference suite uses recorded device boundaries; the live development adapter is described below. The first-parameter-buffer startup dependency is confirmed in the pinned kernel source. See [ISP.md](ISP.md).

Development now includes a [live Linux link/format adapter](ISP.md#live-linux-configuration-adapter), exposed as `camera-probe configure-pipeline`. It operates on an explicit current-graph plan, with real ioctls and readback for single-camera RAW10 startup. Kit 0.0.29 now connects a fixed first-frame startup command, `first-frame-sc3336`, including profile-derived initial exposure, parameter generation, persistent queues, linear raw DMA-BUF bridging and SOF timestamp matching. It requires a full matching IQ file and explicit device plan. Successful vendor-free capture and QR quality remain hardware checks; automatic 3A remains unfinished.

The ISP32 black-level converter now matches **1,000 original-ARM cases** for the complete BLS parameter block, masks and cache. Calibration selection and live parameter submission remain separate work. See [ISP.md](ISP.md#black-level-parameter-block).

Demosaic hardware quantization and kernel parameter packing now match **2,000 original-ARM cases**, including original uClibc logarithm execution, complete output/cache records and enable/update behavior. The hardware ISP performs pixel demosaicing; these Rust functions prepare its controls. Automatic ISO selection is implemented separately below; live submission remains unfinished. See [ISP.md](ISP.md#demosaic-hardware-controls).

Automatic demosaic tuning now loads an explicit scene’s `debayer_v2.param` JSON, selects four independent ISO curves and feeds the verified hardware/kernel conversion. **1,000 complete reference cases** match native automatic `AdebayerProcess`/`AdebayerSelectParam` and conversion results, including 100 SDK SC3336 profile cases. This does not supply the outer frame/update-state controller or live ISP queues. See [ISP.md](ISP.md#automatic-demosaic-tuning).

The metadata parameter queue core now matches **1,000 native ARM lifecycle/state traces**. `camera-probe submit-parameters` adds a bounded Linux MMAP adapter for a supplied complete kernel record, and node inventory now shows metadata-output formats. Successful device submission, full initial IQ assembly and persistent processing integration remain unfinished. See [PARAMETERS.md](PARAMETERS.md).

AE grid and histogram measurement parameter conversion now matches **2,000 native ARM cases**, including four-channel routing, complete kernel blocks/caches and the native enable-mask behavior. These functions consume selected windows/weights; selection policy and complete initial IQ remain unfinished. See [AE.md](AE.md#measurement-parameter-configuration).

AWB measurement parameter conversion also matches **2,000 native ARM cases**, covering detection regions, transforms, thresholds, windows, exclusion flags, grid weights, masks and preservation. This is configuration packing; automatic white-balance decisions and calibrated startup remain unfinished. See [AWB.md](AWB.md).

Six AWB gain/temporal routines now match **6,000 native ARM cases**, including weighted-statistics conversion, normalization, mixture, adaptive damping and the complete temporal gain stage. Integer-to-float reference conversion executes the SDK GCC runtime's original instructions. Illumination classification, full calibrated AWB policy and live publication remain unfinished. See [AWB.md](AWB.md#gain-calculation-and-temporal-damping).

AWB illumination probabilities and their weighted output gain now match **2,000 complete native sequences**: selected-region white-point filtering, gain distance, brightness, per-light curves, combined probabilities and channel accumulation/normalization. The preparation stage below supplies selected counts/gains from full SDK frames; calibrated input construction and the outer controller remain unfinished. See [AWB.md](AWB.md#illumination-probabilities-and-weighted-gain).

Complete SDK AWB measurement preparation now matches **500 native sequences across 1,144 frames**, including the original stability gate, time-share completeness, per-light pregain adjustment, grid conversion, exclusion aggregation and histograms. **124 sequences include fast group −1**, preserving its native history/histogram behavior. Live frame/configuration association, calibration loading, outer AWB policy and startup remain unfinished. The [full translation added in development](AWB.md#driver-to-sdk-translation-in-development) follows kit 0.0.28 and is not a new camera release.

## Exact originals

The [artifact manifest](artifacts.json) pins the SDK commit, download URLs and SHA-256 for `librkaiq.so` and `rkaiq_3A_server`. Originals remain in ignored `.tools/reverse-engineering/rkaiq-original/`; they are not included in the test kit or committed. The image's OS and SDK revisions are the existing documented build pins.

The daemon links `librkaiq.so` and imports these seven RKAIQ entry points:

- `rk_aiq_uapi2_sysctl_getBindedSnsEntNmByVd`
- `rk_aiq_uapi2_sysctl_init`
- `rk_aiq_uapi2_sysctl_prepare`
- `rk_aiq_uapi2_sysctl_start`
- `rk_aiq_uapi2_sysctl_stop`
- `rk_aiq_uapi2_sysctl_setListenStrmStatus`
- `rk_aiq_uapi2_sysctl_setMulCamConc`

Those initialization/stream-management obligations remain open. Additional calls from the application's temporary `rkipc` bootstrap also need to be removed or independently implemented before claiming a fully independent camera stack.

## Ghidra workflow

Ghidra **12.2**, its publisher's archive checksum, and Java **25** are pinned. The official archive has no Mac ARM decompiler executable, so setup builds its included native C++ decompiler with the pinned archive's own source. Ghidra projects live under `dist/reverse-engineering/ghidra-projects/`: Ghidra rejects project paths containing a dot-prefixed directory, so `.tools/` cannot hold the projects themselves.

`ExportRkaiq.java` exports the analyzed function inventory and selected pseudocode to ignored cache. The library has 6,854 defined ELF function symbols (including aliases and C++ support functions); Ghidra's function manager reports 6,584 analyzed functions. These are different counts, not a percentage-complete metric. The daemon's 46 implementation functions have been decompiled. No debug-type information is present; inferred types are checked against instructions and the SDK's public headers where needed.

REA **6.8.0** was checked from the official `morluto/rea` project. Its Ghidra provider accepts 12.1.x and rejects 12.2. This investigation therefore uses Ghidra directly rather than claiming REA analysis that did not run. No agent-wide REA configuration was changed.

## What the first comparisons caught

Ghidra's C output renders fused `VFMA.f32` instructions as ordinary multiply/add expressions. A direct Rust translation produced 149 mismatches in the first 412-case trial. Instruction inspection established the required fused rounding; the reconstruction uses pure-Rust `libm::fmaf` and now matches the corpus exactly.

Other verified details:

- Scalar interpolation compares the f32 interval against an exact **f64 0.001** threshold.
- Matrix and offset interpolation allow extrapolation and preserve the original multiply/FMA operation order.
- LUT blending truncates alpha to Q7, computes integer weighted sums, and shifts by 7 without rounding-to-nearest.
- Defect-pixel interpolation promotes the interpolated f32 to f64 **before** adding 0.5 and converting to integer.
- Gain quantization scales in f32, then adds ±0.5 in f64. The checked API covers nonnegative fractional-bit counts 0–30; the binary's alternate negative-shift mode is not reconstructed.

The safe Rust APIs reject some invalid inputs instead of reproducing invalid pointers, unsorted tables, or undefined caller behavior. The test corpus is finite and seeded; it is not an exhaustive proof over every floating-point value. Unicorn executes the original numeric instructions with FPSCR=0 and stubs only the standard memory-copy/set operations; it is not an emulator for the entire camera subsystem.

The gain-register conversion also matches all 13 control bytes and three u32 gains across 1,000 linear/HDR cases. The original binary ignores its fourth float argument; the harness checks this with two different values for each case. See [FUNCTIONS.md](FUNCTIONS.md) for addresses and individual contracts.

## Reproduce

Use mise from the repository root. Setup dependencies if absent:

```sh
mise install java@temurin-25.0.5+8.0.LTS rust@1.93.1 zig@0.15.2
mise exec rust@1.93.1 -- rustup target add --toolchain 1.93.1 armv7-unknown-linux-musleabihf
mise run camera:re:prepare
mise run camera:re:analyze
mise run camera:rust:layout
mise run camera:rust:test
mise run camera:rust:lifecycle
mise run camera:rust:binding
mise run camera:rust:statistics
mise run camera:rust:ae-grid
mise run camera:rust:ae-big-grid
mise run camera:rust:sensor-linear
mise run camera:rust:sensor-descriptor
mise run camera:rust:exposure
mise run camera:rust:iq-calibration
mise run camera:rust:ae-histogram
mise run camera:rust:ae-decision
mise run camera:rust:ae-damping
mise run camera:rust:isp-pipeline
mise run camera:rust:isp-black-level
mise run camera:rust:isp-demosaic
mise run camera:rust:demosaic-selection
mise run camera:rust:parameter-queue
mise run camera:rust:ae-measurement
mise run camera:rust:arm
mise run camera:rust:smoke
mise run camera:rust:package
```

The library's core numerical code uses `no_std` plus pure-Rust `libm`. Diagnostics use standard Rust, open-source libc bindings and JSON, statically linked with musl so they can run on the uClibc-based Luckfox image without loading a second dynamic C runtime or the vendor ISP library. This diagnostic binary is not a uClibc ABI-compatible shared-library replacement.

The probe explicitly uses the kernel's ARM32, long-sized V4L2 timestamp layout, rather than musl's 64-bit userspace `time_t`. Compile-time assertions check ARM32 buffer/format/plane sizes (68/204/60 bytes) and the ioctl request numbers against the pinned Linux 5.10 ABI. Actual ioctl behavior remains a real-camera test.

[HARDWARE-TEST.md](HARDWARE-TEST.md) explains the next session and how to report results. Numerical emulation, ARM-container execution and mesh-/board checks do not establish live camera operation.

## Remaining implementation

1. Recover the exact single-camera initialization and stream-event lifecycle; reproduce sensor/media graph setup without temporary vendor `rkipc`.
2. Finish the full ISP32 parameter/statistics queue integration and remaining ISP/3A IQ-file sections needed by the selected sensor.
3. Reconstruct the required exposure/gain loop and sensor-control behavior, then the minimal image-processing configuration needed for reliable QR capture.
4. Integrate the recovered processing blocks, with tests for each behavior against the pinned binary. Add register/parameter packing and state-machine coverage.
5. Provide the required RKAIQ API surface or replace its callers, then verify startup, frame delivery, exposure transitions, shutdown and restart on real hardware.

The completed numeric routines and diagnostic tools are an initial milestone toward this objective. They do not close the remaining implementation above.


### First physical ISP capture

On 2026-10-26, the Rust first-frame path saved a recognizable 640×480 NV12
image and valid AE statistics on a Luckfox Pico/SC3336 after rebooting without
vendor application startup. Only the camera kernel drivers were loaded;
`rkipc`, RKAIQ userspace and the Rockit module were not started in that observed
boot. The original startup script was restored and checksum-verified.
[Recorded hardware result](hardware-first-frame-validation.json) and
[reproduction details](HARDWARE-TEST.md#clean-boot-isp-capture-milestone) describe
the scope. This demonstrates a physical ISP frame, not a complete replacement
camera service: fixed exposure/WB, missing SOF matches, frame association,
automatic control, QR quality and application integration remain open.


Development follow-up: the fixed startup white-balance seed now uses the native
linear **Gain1** position. This removes the purple black-level bias observed
in earlier captures; [native and hardware evidence](AWB.md#initial-gain-application-position--corrected)
records the correction. Automatic white balance and broader color accuracy
remain unfinished.

### Profile-bound ordinary AE session

The Rust `ae_session::Session` now joins profile preparation, the SDK's initial
publication phase and successive ordinary linear AE frames. Its comparison runs
complete native `AePreProcess`/`AeProcessing` wrappers rather than stopping
preprocessing at the earlier checkpoint. [Session evidence and boundaries](AE.md#profile-bound-session-through-complete-sdk-frame-wrappers)
cover the retained controller/publication state and remaining optional modes.
Exposure association is still an explicit input; no live sensor/ISP control or
complete AE/AWB camera-service qualification is implied.

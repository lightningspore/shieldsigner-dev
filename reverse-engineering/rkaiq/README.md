# RKAIQ → Rust reconstruction

**Status: experimental runnable Rust SC3336 camera path, with live automatic
exposure/white balance and opt-in SeedSigner integration.** It uses Linux's
existing open kernel camera drivers and does not link or call RKAIQ. It is not
a drop-in `librkaiq.so`, and installed application/boot files are unchanged by
the launcher. Complete qualification of the requested replacement remains open.

## Current deliverable and work rules

**NOW:** the full SC3336 ISP group runs together on hardware: CCM, LSC,
DPCC, BAYNR, BAY3D, YNR, CNR and SHARP, plus demosaic and live AE/AWB.
The 600-image default-all capture passed native comparisons for all nine
modules and final AWB translation. [Combined evidence](combined-isp-hardware-validation.json).

**DELIVERED:** [0.0.35 development kit](../../dist/reverse-engineering/rkaiq-camera-test-0.0.35-dev.zip),
including the desktop live-camera dashboard. All 535 manifest files were
verified after installation on the Luckfox.
[Installation verification](kit-0.0.35-dev-installation-verification.json).
Its exact camera binary passed the installed application's process-local
integration check: 73 received real frames, complete preview rotations and
clean shutdown. [Application evidence](application-integration-hardware-validation.json).
The frozen archive remains unchanged after publication.

**NEXT:** qualify actual optical QR scanning, physical lighting/color response,
LCD/buttons and cold startup of the exact full-group kit. Review joined-native
AWB controller coverage against the normal pinned profile before adding any
new policy. Earlier isolated-CNR startup failures remain historical evidence;
they do not describe the default complete-group build. The full objective
remains the vendor-free fixed-camera replacement.

Work procedure:

1. Choose one user-visible outcome and its pass/fail condition before editing.
2. For the current batch, port the full remaining blocks concurrently, then
   test them together on hardware as requested by the user. Use offline native
   settings to diagnose failures; avoid long pre-integration synthetic suites.
3. State each experiment's hypothesis, expected observation and next decision.
   Change one variable and preserve the working baseline. Avoid speculative
   register/configuration changes without a causal reason.
4. After two failed hypotheses or 30 minutes without narrowing the cause,
   write the findings and reassess the diagnostic approach. Do not silently
   continue a chain of guesses or drop the unresolved requirement.
5. Port one functional block through to a hardware result. Use focused native
   comparisons to resolve fidelity questions; expand numerical coverage for
   actual boundary risks rather than treating test counts as the deliverable.
6. Test changed behavior on hardware each iteration. Run the broader existing
   regression suite at integration, repeating it only for a relevant change or
   failure. Preserve exact binary hashes and compact evidence.
7. Report outcome, remaining fault, changed files and next decision. Routine
   checks need one sentence; they are not separate progress milestones.
8. Track implementation, live operation and qualification separately. The
   eight-block profile audit is a partial backlog, not overall feature coverage.
   Keep the complete remaining requirements below; do not invent an overall
   percentage or redefine completion around the working subset.

This procedure replaces the earlier tendency to finish extensive numerical
work before checking a block's hardware viability. Firmware is unchanged by
this workflow update.

The independently initialized path has been exercised after a controlled clean
reboot without vendor camera startup. It configures the supplied media graph,
loads the supported calibration subset, streams VGA RGB frames, runs persistent
AE/AWB, and owns sensor/ISP queues through shutdown. The actual application
Camera adapter and installed scan/preview loops have received real frames.
The default application has not been switched over permanently.

Recent hardware evidence:

- [Opposite-start exposure convergence](ae-startup-convergence-validation.json):
  dim and bright starts both settle inside the calibrated 10% target band.
- [Repeated ownership](camera-restart-hardware-validation.json): process/socket
  cleanup and zero allocated CMA after each of ten measured stop cycles.
- [Installed scan-loop composition](scan-loop-hardware-validation.json): actual
  decoder and preview code run concurrently; display/cancel boundaries are software.
- [Physical shutter delay](exposure-step-latency-validation.json): six captures
  support two frames. [Gain transitions](gain-step-latency-validation.json)
  retain one four-frame settling exception among thirteen captures.
- [Post-convergence AWB replay](awb-scene-sequence-validation.json): resumes,
  corrects and settles under transformed captured statistics; this is not an
  optical lighting-change test or full joined-native-controller comparison.

[HARDWARE-TEST.md](HARDWARE-TEST.md) is the runnable procedure. The current
0.0.35 kit is summarized above. Earlier 0.0.31–0.0.34 kits retain their own
build-specific evidence, including controlled clean-reboot results; those do
not qualify cold startup of the newest full-group executable. Preserve the
single-camera critical path before optional HDR/multi-camera/tuning modes.

The component records below are historical implementation checkpoints.
Their original “unfinished” statements are superseded where the current
hardware results above establish later composition.

Development 0.0.33-dev connects recovered ISO-dependent demosaic frame tuning
to live, atomic ISP batches; [two hardware runs and original comparisons](demosaic-live-validation.json) pass.
It also omits the final scene-image dump during normal app
streaming; explicit diagnostic image saving remains available.
[Hardware behavior and scope](stream-image-artifact-validation.json).

## What is implemented

- Ten recovered numerical routines in [`firmware/rkaiq-rs`](../../firmware/rkaiq-rs): scalar interpolation, saturation color-matrix interpolation, saturation-offset interpolation, 9×9×9 RGB LUT blending, defect-pixel calibration interpolation, the multiplicative gain-quantization branch, and the full linear/two-frame/three-frame gain-register conversion, ISO calibration selection, ISP32 white-balance gain serialization, and exposure digital-gain application.
- **9,050 deterministic comparisons, zero mismatches** between compiled Rust and actual instructions from the pinned ARM library under Unicorn. Float results are compared as exact IEEE-754 output bits; LUT outputs compare all 2,187 u16 entries. [Report](numeric-equivalence.json).
- A **standalone, statically linked ARMv7 Linux `camera-probe`**. It inventories video nodes, supported formats and media entities, reports active vendor camera processes, and supports bounded single-/multi-plane MMAP frame capture.
- A Rust **`frame-preview`** converter for uncalibrated grayscale inspection of supported YUV/luma/Bayer captures. Bayer preview uses simple 2×2 binning, not the vendor ISP algorithm.
- A static ARM `numeric-fixture` executable and reference corpus for checking the recovered routines on the actual processor.

The component records below describe their original comparison scopes. Later live
composition and hardware evidence are summarized above and in HARDWARE-TEST.md;
an isolated numerical comparison must not be read as complete service qualification.

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

## Remaining implementation and qualification

The explicit-plan SC3336 path now replaces its application camera caller rather
than implementing the full RKAIQ ABI. Graph setup, persistent parameter/statistics
queues, automatic exposure/white balance, app frame delivery and restart have
real hardware evidence. These do not imply that every optional IQ section or
vendor algorithm is implemented.

The [selected-profile audit](profile-module-audit.json) also identifies enabled
profile blocks that frozen 0.0.33 startup explicitly disables: CCM, LSC, DPCC,
spatial and temporal Bayer noise reduction, YNR, CNR and sharpening. Current
0.0.34 development enables DPCC, CCM, LSC and BAYNR with native comparison and live capture
([CCM evidence](ccm-live-validation.json),
[LSC evidence](lsc-live-validation.json),
[BAYNR evidence](baynr-live-validation.json),
[current startup audit](profile-module-audit-0.0.34-baynr.json),
[DPCC details](ISP.md#persistent-dpcc-and-live-submission-0034-development)).
The other four blocks (BAY3D, YNR, CNR and SHARP) remain
implementation gaps for full profile parity, separate from the physical tests
below. A working QR subset is not complete vendor image-quality equivalence.

Still open:

1. Successful optical decoding of a known public QR through the physical camera.
2. Physical lighting/color changes and broader image quality, including the
   observed variable sensor-gain settling and its exposure-association implications.
3. Actual LCD/buttons and complete application interaction; current scan-loop
   tests substitute the display and cancellation boundaries.
4. Physical power-cycle testing and a reviewed permanent startup choice;
   controlled reboot and opt-in launch have been tested separately.
5. Complete joined-native AWB controller equivalence and any remaining policy
   required by this fixed profile. Existing comparisons cover many components
   and the live composition, with narrower oracle scopes stated explicitly.
6. Freeze a new kit containing the current development path and repeat controlled
   reboot/application and remaining physical qualification with those exact bytes.
   Frozen 0.0.33 has neither live DPCC, CCM nor LSC and remains unchanged.

Optional modes remain outside the current single-camera priority unless the
actual QR capture path needs them. No completion claim follows from passing
numerical or simulated-device tests alone.


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

`Session::step_statistics` additionally joins raw ISP32 translation to explicit
parameter-snapshot IDs and effective-exposure lookup. [Raw-buffer comparison](AE.md#raw-isp-statistics-parameter-ids-and-exposure-map-association)
checks the native composition and rejection of missing metadata/changed timing.
The caller still owns the complete parameter snapshots and reported exposure map.

The ordinary sensor submission path now preserves native per-record metadata and
replaces pending batches by their first-entry markers. [Submission/SOF comparison](AE.md#exposure-submission-and-sof-handoff)
checks native queuing, dequeue/effective-map behavior and linear control traces
with modeled device callbacks. Live coordination and physical timing remain open.

`ae_runtime::Runtime` now owns the session and scheduler together: statistics
consume the scheduler's own reported exposure map, AE submits its next batch,
and SOFs drive the recovered writer through a caller-provided backend.
[Persistent runtime comparison](AE.md#persistent-ae-runtime-with-scheduler-produced-association)
covers the combined native data flow. Initial sensor programming, live capture,
ISP gain updates, physical timing and AWB remain external or incomplete.

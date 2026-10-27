# AE measurement correction

`ae::correct_lite_grid` reconstructs `RkCam::calcAecLiteWinStatsV32`, ELF `0x85f00` (Ghidra `0x95f00`). Here **Lite means the 5×5 AE0 measurement grid**, not the different ISP32-lite hardware. This helper is used by the full-ISP32 resource translator.

It accepts 25 packed RGB measurements, 25 byte weights, signed black-level and gain records, channel selection and luma range. It mutates a four-channel output record and separate weighted-mean value. It does not calculate an exposure time, sensor gain or automatic-exposure convergence state.

For each RGB channel, correction is `(sample × signed_gain) / 256 - signed_black_level`. Integer division truncates toward zero. The red/blue result is clipped to 0–1023 and green to 0–4095. Both records use the SDK's eight-byte signed `isp2x_bls_fixed_val` layout; the second green field is unused by this helper.

| Selection | Original value | Changed fields | Mean source |
| --- | --- | --- | --- |
| RGB plus luma | default branch; checked Rust maps 0 | all four arrays | clipped RGB-derived luma |
| Luma | 1 | luma only | luma from corrected values before RGB clipping |
| Red | 2 | red only | red shifted right 2 |
| Green | 4 | green only | green shifted right 4 |
| Blue | 8 | blue only | blue shifted right 2 |
| RGB | 14 | red, green, blue | mean is untouched |

Unwritten arrays retain their prior bytes. Luma-only differs from RGB-plus-luma near clipping boundaries because it uses unbounded corrected values, shifts them arithmetically and then computes luma. Both branches round luma and clip it to 0–255.

Full-range coefficients are R=0.299, G=0.587, B=0.114, offset=0. Limited range uses R=0.25, G=0.5, B=0.1094, offset=16. These are the actual pinned f32 constants, not substituted textbook values. The instruction order is green multiply, fused red add, fused blue add, then offset. Rust uses explicit fused operations and `libm::roundf`.

The weighted mean is `roundf((sum(weight × selected_8bit_value) as f32 × 256) / sum_weights as f32)` and is stored as u16. Zero total weight is rejected before any mutation when a mean is required. RGB-only accepts zero weights and preserves both the luma array and prior mean. This is a checked-API difference from executing the original zero-divisor path.

## Verification

`camera:rust:ae-grid` executes the original helper's ARM instructions for 1,000 deterministic cases and compares all 100 output u16 words plus the mean. The corpus covers all twelve mode/range combinations, ordinary and extreme signed gain/black values, saturation and preservation of existing output fields. [Report](ae-grid-equivalence.json).

Its imported standard `roundf` is modeled explicitly with ties away from zero; it is not an unreported vendor algorithm stub. The remaining calculations, pointer writes and float conversions execute in the original instructions. Kernel headers independently verify the signed BLS record layout. Host tests verify zero-weight rejection is atomic and RGB-only preserves the mean/luma fields; ARM emulation repeats the entire corpus using the compiled Rust fixture runner.

Full translator configuration/state, calibrated weights, exposure selection and sensor programming remain unfinished. Do not feed guessed gains, black levels or weights into a live control loop and describe it as the upstream algorithm. The measurement decoder and this helper are separate APIs until those inputs and synchronization are reconstructed.

## Histogram correction

`ae_histogram::correct` reconstructs `calcAecHistBinStatsV32`, ELF `0x86a68` (Ghidra `0x96a68`). It handles 64- and 256-bin histograms, R/G/B and luma modes, and the original bypass copy. Its mode numbers differ from grid channel selection: histogram red=2, green=3, blue=4; other native values enter the luma branch. The Rust enum makes that distinction explicit.

The caller provides optical-black offsets separately for red/blue and green, plus signed BLS and gain records. Correction maps source bins into destination bins, merging counts with wrapping u32 addition. A 64-bin source represents the 8-bit bin centers `4*i+2`; its remapped 8-bit index is limited to 254 before truncating division by four. A 256-bin source uses `i` and limits its remapped index to 255.

The original narrows some products and weighted offsets to signed or unsigned 16-bit values before mapping. Those operations are reproduced explicitly. The luma branch computes its divisor from signed gain-dependent divisions with constants 7655, 15027 and 2919, rather than replacing it with a floating-point ratio. Native rounding uses half the integer divisor. Bypass does not inspect calibration values. Invalid divisors or out-of-range negative destinations return an error **before** changing output.

`camera:rust:ae-histogram` compares every output counter in 1,000 deterministic original-ARM runs. All sixteen mode/size/bypass combinations are included, with both ordinary and larger corrections, full-width input counts that exercise wrapping, and bypass cases with zero gains. Standard `__aeabi_idiv` is an explicit truncating signed-division stub; the original bin-mapping instructions still execute. [Report](ae-histogram-equivalence.json). The compiled ARM Rust runner repeats the complete corpus under Docker emulation. Host tests cover atomic rejection and bypass behavior.

This helper redistributes measured histogram counts; it does not choose sensor exposure or establish a calibrated control loop. Native invalid-pointer/out-of-bounds behavior and zero-divisor paths are outside the checked API.

## Large AE grids and subwindows

`ae::correct_big_grid` reconstructs `calcAecBigWinStatsV32`, ELF `0x86444` (Ghidra `0x96444`). It applies the same six channel-selection branches and luma ranges to 225 cells, and always corrects four subwindow RGB sums. AE0 and big-grid correction share the recovered cell calculation; both original-reference corpora run after changes to that calculation.

The native output record is 1,928 bytes: four 225-element u16 arrays, four four-element window-channel arrays that this function leaves untouched, then four u64 sums per color. `camera:rust:layout` extracts the actual record declaration and array-count macros from the pinned SDK header, cross-compiles them for ARM, and checks size and offsets independently of the Rust serializer.

For subwindow sums, red/blue use a quarter of the supplied pixel count and clip to `0x1fffffff`. Green uses half the pixel count and clips to `0xffffffff`. Grid cells use `black.green_red`, while green **sums** use `black.green_blue`. Gain scaling uses a signed 64-bit multiplication followed by a **logical** right shift by eight. The black-level×pixel term wraps at 32 bits and is then subtracted as unsigned. Those native operations have unusual results for negative/extreme inputs; replacing them with straightforward signed subtraction would fail the reference comparison. Rust preserves the pinned behavior and final saturation.

All branches update sums, including RGB-only mode, which still leaves the prior weighted mean and luma cells intact. The untouched window-channel arrays are preserved in every branch. Zero mean-weight rejection happens before any grid/sum mutation.

`camera:rust:ae-big-grid` compares all 1,928 output bytes and the mean for 1,000 deterministic original-ARM runs across all twelve channel/range combinations. Cases include signed gain and black-level boundaries, small/large pixel counts, saturation and preservation of prior output bytes. The standard `roundf` stub is shared with AE0's harness; other processing runs as original ARM instructions. [Report](ae-big-grid-equivalence.json). The compiled ARM Rust runner repeats the complete corpus. This still does not implement calibrated exposure decisions or the full resource-translator state machine.

## Histogram-driven exposure proposal

`ae_decision::solve` reconstructs the inner `ClmExecute` solver, ELF `0xb6968` (Ghidra `0xc6968`), and `ClmCalcHistTriangle` behavior. It accepts the histogram, target/measured brightness, current exposure, tolerance and exposure bounds. The result is a proposed exposure scalar plus the native saturation flag. The native outer code later splits that scalar through `EcmExecute` into time/gain components (and optionally iris); it is not a direct shutter-time-in-seconds command. **The outer AE controller is still incomplete; this is not a runnable automatic exposure loop.**

If relative target/measured error is within the configured percentage, it returns the current exposure and preserves the prior saturation flag without processing the histogram. Otherwise it copies the source bins except the terminal bin and sums them with native u32 arithmetic. A rising terminal bin is replaced by the original integer triangle extrapolation, extending into a fixed 768-bin workspace. The denominator excludes the source terminal count and adds only replacement-triangle counts when present. This detail is intentionally preserved rather than replaced with a conventional histogram mean.

Brightness prediction normalizes by `256/bin_count`, clips bin centers at `bin_count-0.5`, and accumulates with fused f32 operations. The measured/histogram-mean ratio is computed in f64 then narrowed to f32, matching the instructions. Iteration adjusts exposure from predicted clipped brightness, with a 1% relative-error test and a 51-iteration limit. Crossing a supplied exposure bound **stops** iteration; it does not clamp the result to that bound. The final proposal is capped only at 40 times the input exposure in this helper. Saturation uses the original strict f64 comparison between the terminal count and 95% of the working total. Near-target early returns leave the old flag unchanged.

The checked Rust API supports the 64/256-bin domains used by the reconstructed measurement path, rejects invalid active floating inputs and protects against a zero-width extrapolation divisor. It does not emulate invalid pointers or arbitrary native workspace sizes. A dark histogram can reach the relative-growth cap; that is reference behavior, not proof that a proposed setting is physically valid for a sensor/frame interval.

`camera:rust:ae-decision` executes the complete original solver and triangle code under Unicorn, compares exact resulting f32 bits and the saturation flag, and checks that input histograms and unrelated context bytes are preserved. Histograms include empty, dark/central/terminal peaks, rising distributions, random distributions and zero-previous-bin tail extrapolation. The original iteration-count distribution is recorded as evidence of the executed paths. One intentionally beyond-normal-brightness target forces the full 51-iteration bound; it is a boundary test, not a physical camera recommendation. Standard unsigned division is explicitly implemented by the harness; logging is discarded. [Report](ae-decision-equivalence.json). Compiled ARM Rust fixtures replay the same corpus.

This stage still needs calibrated histogram/mean inputs, outer damping, route selection, exposure/gain splitting, limit enforcement, delay handling and synchronized sensor/ISP application. No automatic-control command has been enabled from this solver.

## History-based exposure damping

`ae_damping::calculate` reconstructs the `AecDynamicDamp` wrapper (ELF `0xa4024`) and active core (`0xa3ab8`). Disabled operation preserves the supplied coefficient without examining inactive history/calibration fields. Active operation reads a ten-slot history ring at `frame_count % 10`, walks nine consecutive differences with weights 10 through 2, and divides the fused accumulation by 54. The current history value is normalized by `scale / 100`; the trend by 0.03. Both are clipped to [-4, 4]. The recovered constants and nine interpolation knots (-4 through 4) were read directly from the pinned ELF.

A 9×9 rule surface uses the configured coefficient, two intermediate values, and unity. Default intermediate values are `(coefficient+2)/3` and `fmaf(coefficient,2,1)/3`. Native mode 2 substitutes a configured middle value and scale, with the other intermediate `(coefficient+middle)*0.5`. Bilinear interpolation preserves the original fused multiply/add order. This is the upstream history-based algorithm, not an added smoothing filter.

The original writes raw trend, normalized trend and normalized current into the **oldest visited slot**, `(frame_count+1)%10`, after walking the ring. The Rust result exposes these diagnostics and their slot explicitly. The harness checks both linear and three-channel HDR storage layouts, and verifies that every unrelated context byte remains unchanged. The wrapper's null-pointer return of 8.0 is not exposed through the checked Rust API. Active inputs must be finite, the effective scale positive, and the frame counter within nonnegative signed-i32 range.

`camera:rust:ae-damping` compares exact coefficient and diagnostic f32 bits in 1,000 native ARM executions. It covers the full 17×17 knot/half-knot lattice in both rule modes, disabled operation, history wrap, large/alternating histories and all HDR channel indices. Standard signed division/remainder for nonnegative frame counters is modeled explicitly; logging is discarded. [Report](ae-damping-equivalence.json). The compiled ARM Rust executable replays the same fixture corpus.

The outer controller still has to combine this coefficient with the proposed and current exposure, enforce limits, split time/gain, honor delays and apply synchronized sensor/ISP updates. ISP configuration and independent cold startup also remain unfinished. Damping equivalence is not proof of complete camera operation.

## Measurement parameter configuration

`isp_ae_measurement` reconstructs result types 1 (AE measurement) and 2 (histogram measurement) inside `Isp32Params::convert3aResultsToIspCfg`, ELF `0x304c4`. The safe Rust APIs consume typed selected-result records and write the packed kernel blocks plus explicit cache storage. They do not reconstruct the entire dispatcher, select measurement windows/weights or publish results to a live queue.

The ISP32 SDK supplies three configurations for four hardware channels. The native mapping is intentionally preserved:

| Kernel block | Supplied SDK configuration | Bytes |
| --- | --- | --- |
| RAWAE0 | `rawae0` | 10 |
| RAWAE1 | `rawae1` | 46 |
| RAWAE2 | `rawae1` again | 46 |
| RAWAE3 | `rawae3` | 46 |
| RAWHIST0 | `rawhist0` | 41 |
| RAWHIST1 | `rawhist1` | 242 |
| RAWHIST2 | `rawhist3` | 242 |
| RAWHIST3 | `rawhist3` again | 242 |

All source-selection, raw window-mode, subwindow flags, coordinates, coefficients and weight bytes are copied without clipping or invented defaults. `window_mode` corresponds to the SDK `wnd_num` enum; it is not a literal number of windows. Windows use unsigned 16-bit horizontal/vertical offsets and dimensions. Big AE has four subwindows; lite/big histograms carry 25/225 byte weights respectively. Physical geometry and valid hardware mode selection remain the outer controller's responsibility.

These dispatcher branches always OR their masks into enable-update, enables and configuration-update. They do **not** consult the source `*_meas_en`/`*_meas_update` booleans. The histogram branch also does not consult its source `ae_swap`/`ae_sel` fields. This is behavior at the selected-result publication stage, not an enable/disable API. Replacing it with conventional flag gating would diverge from the pinned binary.

The AE mask is `0x003c4000`, including RAWAE0–3 and the inherited YUVAE bit. The histogram mask is `0x07800008`, including RAWHIST0–3 and the inherited SIHST bit. These are parameter-module masks, not the validity-bit masks in captured statistics. The extra bits are retained exactly; these branches do not write separate YUVAE/SIHST payload blocks. All unrelated bits/parameter bytes remain unchanged.

AE occupies 148 contiguous bytes at `0x41b`, mirrored into the native cache beginning at virtual-base-relative `0x468`. Histograms occupy 767 bytes at `0x4af`, mirrored at `0x4fc`. Rust exposes those caches as fixed byte arrays without requiring the original C++ object layout. The input SDK records are 104-byte `rk_aiq_ae_meas_params_t` and 529-byte `rk_aiq_hist_meas_params_t` with `ISP_HW_V32` enabled. The checked decoders reject malformed bool values; window/control values are not qualified merely by successful decoding.

`mise run camera:rust:ae-measurement` executes both original dispatcher branches for 1,000 cases each. It compares all three masks, every kernel/cache byte, source preservation and unrelated context/parameter preservation, across both source flag values, multi-ISP hint values and two virtual-base offsets. Random and zero/maximum patterns exercise routing/preservation; they are not camera recommendations. The typed-result cast is a controlled boundary returning the supplied valid SDK record; standard memcpy is explicit. Other dispatcher result types, failed casts and full polymorphic result ownership are outside this suite. [Report](ae-measurement-equivalence.json).

Cross-compiling verbatim SDK declarations with their packed leaf-record rules and `ISP_HW_V32` independently checks every consumed input offset and record size. Kernel header assertions verify all eight output block locations/sizes and the complete masks. ARM executable replay repeats the reference corpus. This verifies selected-result serialization; AWB measurement configuration, calibrated window/weight selection, synchronized control and complete initial IQ/startup remain unfinished. No new complete parameter file suitable for hardware submission is supplied by these fixtures.

## Measurement geometry recovered in 0.0.30-dev

`ae_geometry::configure` reconstructs `AecHwConfig` (ELF 0xa7730) over the
contiguous 104-byte selected AE and 529-byte selected histogram records. It
sets the native source selectors, derives input/tone-mapped windows from
sensor dimensions and calibrated fractions, and initializes hardware histogram
weights to one. It preserves all other selected fields. This uniform hardware
weight initialization is distinct from the profile's center-weighted AE policy;
it does not establish where later policy weights are applied.

The native linear branch selects sources 1/1/3; accepted modes 0x11/0x12 select
0/0/0 and reuse the input window for the final measurement. Fraction products
are truncated to signed integers, nonpositive products become zero and positive
results narrow to u16. Rust rejects invalid modes/nonfinite or oversized checked
inputs before mutation. Source selectors mirrored into native context fields
are explicit return values instead of private C++ memory access.

The focused original-ARM suite covers 120 cases, comparing all 633 selected
bytes, mirrored selectors and preservation of other context bytes. ARM Linux
replay executes the same cases with the Rust binary:

```sh
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-geometry.py --arm
```

[Equivalence report](ae-geometry-equivalence.json). Default measurement-record
construction, remaining calibration/control selection and startup measurement
publication are still required before live statistics can drive the recovered
AE solver. This helper is deliberately not enabled in the fixed first-frame
command yet, which continues to disable measurement blocks and automatic 3A.

### Native selected-record defaults

`ae_geometry::defaults` now reconstructs the 633-byte seed created by `AecInit`
(ELF 0xa861c) before calibration is applied. The implementation writes the
recovered control/window/coefficient constants into zeroed SDK records rather
than embedding an opaque memory dump. The reference executes the original
allocation, stack construction and record copies, captures the seed on entry
to `AecCalibConfig`, and models only zero allocation and that calibration
boundary. All 633 bytes match on host and ARM replay.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-defaults.py --arm
```

[Default-record report](ae-defaults-equivalence.json). The geometry suite also
uses these independently captured native defaults in 60 of its 120 cases,
checking default construction plus geometry composition. This is still the
pre-calibration seed: `AecCalibConfig`/`AecUpdateConfig` selection and the live
measurement/statistics controller are not replaced by these defaults. The
fixed first-frame capture command continues to leave automatic 3A disabled.

### Calibration grid weighting

`ae_weights` reconstructs `AecSetMeanLumaGridWeights.constprop.9` (ELF 0xa6e64)
and `AecGridWeight15x15to5x5` (ELF 0xa6bf0). The 225-cell path copies the
calibration grid; the 25-cell path averages each 3×3 block with integer division
by nine and writes only the first 25 destination bytes. It preserves the other
200 bytes, as does the original wrapper. This is software weighted-mean input,
not the uniform histogram-weight initialization performed by `AecHwConfig`.

The reference executes the original selector and reduction instructions with
explicit allocation/free and imported integer-division boundaries. It compares
all 225 destination bytes for 120 cases, including both grid sizes with the
pinned SC3336 profile, zero/max patterns and random grids. Run ARM replay with:

```sh
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-weights.py --arm
```

[Weight-selection report](ae-weights-equivalence.json). An all-zero profile grid
is still passed through by this helper: the outer `AecUpdateConfig` detects that
case and chooses its own built-in fallback before calling this function. That
fallback, overrides, histogram-mode policy and live statistics/AE integration
remain unfinished. The first-frame command still does not enable automatic 3A.

### Profile binding and selected measurement configuration

`ae_configuration` composes the recovered defaults and geometry with the linear
measurement subset of `AecUpdateConfig` (ELF 0xa9068), under update mask 0x80.
It normalizes histogram/raw/Y-range modes, derives the channel mask from the
calibration-side seed, writes the native range offset and RGB coefficients,
and publishes the nonzero 225-cell software grid into histograms 1 and 3 for
linear source selection 1. The profile loader consumes the SC3336 enabled-auto,
Y-histogram/Y-raw/full-range subset of `ae_calib.CommCtrl` explicitly. It rejects
unsupported profile modes, all-zero grids and windows needing calibration
correction rather than substituting a guessed policy.

The original-ARM reference executes `AecHwConfig` and then `AecUpdateConfig`
through normal return, requiring status zero. Forty selector/range/mask patterns
plus one full-profile JSON binding compare all 633 selected bytes and normalized
policy values. The complete private AE context is not compared. Nonmeasurement
state is synthetic zero state with positive timing placeholders, so this remains
a selected-record comparison rather than full calibration/controller parity. The channel-mask seed comes from calibration bytes copied into
the context, not a previous engine mask. The reference uses explicit allocation,
comparison and imported integer-division boundaries.

```sh
mise exec rust@1.93.1 -- cargo build --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-configuration.py --arm
```

[Selected-record equivalence report](ae-configuration-equivalence.json). This is not a
claim that the remainder of `AecUpdateConfig` or subsequent AE processing has
been reconstructed. The selected records can now be packed by the optional offline
`make-initial-parameters --ae-measurements` path. The first-frame command still
does not publish them or run statistics feedback. Full measurement publication, statistics
association, exposure route/limit selection, delay scheduling and live feedback
remain required work. Automatic exposure is still disabled in capture.

### Persistent measurement collection in development

The optional statistics-node argument to `first-frame-sc3336` now selects the
measurement-enabled startup record and keeps a statistics queue open around
camera capture. It records raw measurements and frame/parameter IDs from the
same live session, with an explicit readiness barrier and bounded header history.
See [the command and limitations](HARDWARE-TEST.md#persistent-statistics-with-first-frame-capture-0030-dev).
The ARM userspace simulator exercises both variants and checks the lifecycle.
Actual measurements and exposure/frame association remain unverified. No AE
solver, limit/delay policy or feedback sensor writes have been enabled yet.

## Primary linear statistics translation

`ae_translation::measure_linear` now connects full driver statistics and an
explicit ISP parameter snapshot to the primary linear/source-1/full-range AE
input: the corrected 225-cell grid/subwindow sums, Q8 weighted mean and 256-bin
histogram. It requires both AE1 and histogram1 validity bits. Unsupported source,
histogram mode or range-coefficient configurations are rejected. It reconstructs
native BLS1/predgain correction, optical-black offsets, first-position WB-gain
clamping and signed rounding before invoking the recovered grid/histogram code.

The original reference executes `translateAecStatsV32` (ELF 0x86e54) through
normal return, including the actual native grid and histogram bodies. Thirty-two
cases compare the entire 1,928-byte primary grid record, weighted mean and
histogram, plus invalid-mask bypass. Cases use the SC3336 startup parameters and
bounded variations of BLS1, OB offsets/predgain and WB gains. Object access,
single-ISP selection and the run-flag result are controlled boundaries; integer
division and imported `roundf` are explicitly modeled. The output starts zeroed.
Cached output reuse, HDR, other source swaps, AF/iris and complete SDK/context
state are outside this minimum path.

```sh
mise exec rust@1.93.1 -- cargo build --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-linear-translation.py --arm
```

[Translation report](ae-linear-translation-equivalence.json). Independent ARM
kernel-header assertions verify AE1 grid, subwindow-sum and histogram offsets.
The persistent statistics report now includes corrected mean brightness and
histogram count from the **initial submitted snapshot**, with association still
explicitly unverified. Invalid validity flags/configuration produce diagnostic
status rather than exposure writes. This supplies measurement input, not the
outer target selection, sensor-limit policy, delay scheduling or feedback loop.

## Dynamic linear brightness target

`ae_target::select` reconstructs the dynamic-setpoint branch in `AecPreProcess`
(ELF 0xb33d0). It selects from `LinearAeCtrl.DySetpoint` using the native current
exposure product (analogue gain × integration time × ISP digital gain), with
inclusive interval tests and the original multiply/divide/add order. Values
outside the curve clamp to its endpoints. Native `Evbias` uses a percentage
factor `1 + abs(bias)/100`: negative bias divides the target and nonnegative bias
multiplies it. Nonempty-curve targets clamp to 1–255. An empty curve follows the
native early default zero branch; the single-point exact-knot behavior is also
preserved instead of replaced with the shared interpolation helper.

The original-ARM reference executes the actual preprocessing branch through its
store at context +0x130, using the recovered by-value exposure-info ABI and an
explicit run-flag boundary. It checks the resulting exposure product as well as
target bits. Eighty-eight cases cover the pinned profile, interpolation/bias/
clamp boundaries, empty/single-point curves, randomized finite curves and full
profile binding. It deliberately stops at that store: the rest of preprocessing,
flicker, backlight/overexposure policy and the full controller are outside this
comparison. [Reference report](ae-target-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-target.py --arm
```

The measurement-enabled initial report and persistent statistics sidecar now
include `initialTargetLuma` (45 for the pinned SC3336 initial settings). This is
an initial configuration diagnostic, not a claim that target/exposure/frame
association is verified. There are still no feedback exposure writes; the next
required controller stages include state association, damping, exposure-route
selection, limit/flicker rules and frame-delay scheduling.

## Linear exposure route splitting

`ae_route::split` reconstructs non-iris `EcmExecuteAuto` (ELF 0xb5bcc) and its
`EcmExecuteBrief2` helper (0xb57a4). It consumes explicit runtime limits and a
mutable route of time/combined gain/ISP gain. It adjusts time knots using the
native flicker quantum and line-based tolerance, selects the first route knot
with strictly greater total exposure, and follows the native same-time,
same-gain and fixed-ISP interpolation branches. It preserves native time/gain
quantization fallbacks and redistribution when combined gain exceeds its limit.
The routine mutates route times in-place; gain/ISP arrays stay unchanged.

The tolerance calculation mixes f32 and f64 in the original: coefficient × 1.5
and line length use f64, while pixel-clock × 1,000,000 is rounded to f32 first.
The residual uses the native fused multiply/subtract. Using an ordinary
interpolation helper or rounding every time to the nearest quantum would change
results. `from_profile` binds equal-length TimeDot/GainDot/IspDGainDot arrays and
their declared counts from the SC3336 route without inventing runtime limits.

The original reference executes the complete native automatic route and brief
interpolation bodies through normal return. Ninety-one comparisons cover the
SC3336 route, varying time/gain/ISP segments, 50/60 Hz-style quantums, gain/time
limits, endpoint requests, time-knot mutation and profile binding. It checks all
returned float bits, iris output zero and preservation of context/gain arrays.
Imported floor/ceil/round functions are explicit mathematical boundaries.
[Route equivalence report](ae-route-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-route.py --arm
```

This implements a required actuator-decision stage, but does not choose the
runtime limits/quantum/tolerance values. Those inputs are controlled explicitly
in the comparison. The checked API excludes iris and simultaneous three-variable
intervals, which the native interpolation helper rejects. Outer `EcmExecute`
caching, frame/exposure association, remaining limit/flicker policy and delayed
sensor scheduling remain unfinished. No live feedback writes are enabled.

## Runtime flicker quantum selection

`ae_flicker::select` reconstructs the quantum-selection fields of
`AecUpdateConfig` (ELF 0xa9068). With flicker enabled, selector 1 chooses 0.01 s
and selector 2 chooses 1/120 s, with the other value stored as the alternate.
Selector 3 uses a detected **period in seconds**, compared to the double-precision
0.01 and 1/120 constants within f32 epsilon. Zero/negligible detection defaults
to 50 Hz timing; an unrecognized nonzero period preserves the prior quantum pair.
With flicker disabled, the quantum is the absolute native line-time/coefficient
expression, the frequency field becomes zero and the alternate is preserved.

The full native configuration call is executed through normal return for 57
cases, checking frequency and both quantum fields, including prior-state
preservation and detection-tolerance boundaries. Calibration timing and prior
state are injected explicitly; allocation/comparison/division and imported
rounding functions are controlled boundaries. This does not compare every
private context field or recover the period estimator.
[Equivalence report](ae-flicker-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-flicker.py --arm
```

The pinned SC3336 measurement-enabled initial report now identifies its fixed
50 Hz `routeTimeQuantumSeconds` using this recovered selector. **A route quantum
is not a minimum shutter time.** The existing 3 ms initial exposure is retained.
Fixed-frame shutter bounds are reconstructed below; runtime state association
and delayed feedback writes are still unfinished.


## Fixed-frame linear shutter limits

`ae_shutter::fixed_frame` reconstructs the physical and selected time bounds from
`AecUpdateConfig` (ELF 0xa9068). It retains the native fused maximum-register
calculation, calibration minimum-register conversion, route endpoints,
zero-means-fallback overrides, conflicting-bound reconciliation and flicker
rounding. Explicit minimum mode (native selector 1) replaces the route minimum
with the greater of physical minimum and flicker quantum.

The pinned SC3336 coefficients are `[0, 0, 1, 0.5]`, minimum register 1 and
maximum-register factors `[1, 8]`. The second maximum-register factor is also
the route floor-tolerance coefficient: **8**, not the time-conversion factor 1.
Runtime frame length, line length and pixel clock must come from the active
sensor. Driver exposure-control bounds still gate sensor writes separately.

Thirty-six cases compare all four float results bit-for-bit with the original
configuration function through normal return, then replay on the ARM Rust
binary. Cases cover two frame lengths, route bounds, enabled/disabled flicker,
explicit-minimum mode, conflicting overrides and alternate coefficients. Two
cases bind the complete pinned SC3336 IQ profile through `SensorCalibration`,
`RuntimeTiming` and the parsed route using `ae_shutter::from_calibration`; this
binding leaves flicker and override policy explicit.
The harness supplies runtime state and models allocation, math and diagnostic
output; this is not complete private-context equivalence.
[Equivalence report](ae-shutter-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-shutter.py --arm
```

FPS selection, variable-frame-rate/HDR policy, gain/DCG bounds, calibration enum
binding and feedback scheduling remain separate work. These limits are not yet
wired into automatic sensor writes. Real camera image quality remains untested.


## Linear sensor and ISP gain limits

`ae_gain_limits::linear` reconstructs the DCG-disabled, nonzero-calibration
branch of `AecUpdateConfig` (ELF 0xa9068). Physical sensor gain bounds multiply
analogue and sensor-digital ranges. Route endpoints are clamped against those
physical bounds; ISP gain endpoints are clamped against their separate range.
When overrides are enabled, each nonzero override replaces its route endpoint;
zero keeps the route endpoint. If a selected minimum exceeds its selected
maximum, the minimum collapses to the maximum, preserving native behavior.

For the pinned SC3336 ranges, physical sensor gain is 1 through approximately
778.24 (48.64 × 16), while the profile route ends at 512. These real-valued
limits are distinct from register codes. Sensor register conversion, driver
control limits and ISP digital-gain publication still need their existing
separate checks.

The native reference executes the complete configuration function through
normal return. Thirty-six cases compare six float fields bit-for-bit: physical
sensor min/max, selected sensor min/max and selected ISP min/max. They cover
three physical-range sets, three route-range sets, zero-valued and nonzero
overrides, and conflicting overrides. Host and static ARM replay both pass.
[Equivalence report](ae-gain-limits-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-gain-limits.py --arm
```

This checked API rejects zero/negative physical or route endpoints, nonfinite
inputs, reversed ranges and multiplication overflow. Native invalid-calibration
fallbacks, DCG/HDR, iris and complete private configuration state are outside
its scope. It does not enable feedback sensor writes or establish exposure
frame scheduling. Together with the recovered shutter bounds, it supplies
another input needed by the native route splitter.


## Cached automatic route dispatch

`ae_route::split_cached` reconstructs the successful non-iris automatic branch
of `EcmExecute` (ELF 0xb65cc), calling the existing recovered route splitter.
It compares the relative change from the last dispatched aggregate exposure
with the runtime threshold. A force flag bypasses the cache. Recalculation
updates cached gain, ISP gain, time and aggregate exposure, then clears force;
a cache hit preserves both route knots and cached state.

The native unordered floating-point comparison matters: zero previous exposure
and zero request produce 0/0, and native code **recomputes**. The implementation
uses a negated strict comparison to preserve that behavior; replacing it with
an ordinary `>=` or `<=` comparison would change the first dispatch.

Ninety-six cases execute native `EcmExecute`, `EcmExecuteDirect` and the actual
automatic route/interpolation bodies through normal return. They compare
outputs, route-time mutation, cached aggregate exposure, force clearing and
preservation of all other context bytes. Cases cover zero previous exposure,
zero requests, threshold boundaries, cache hits and forced updates.
[Equivalence report](ae-route-cache-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-route-cache.py --arm
```

Manual/iris modes and native publication of partial results after a direct
error remain excluded. The Rust checked API returns its route error without
updating the cache. Runtime threshold/configuration selection, outer brightness
control, damping application and delayed sensor writes remain separate work;
this does not enable automatic exposure on hardware.


## Brightness-transition delay gate

`ae_delay::linear` reconstructs the complete linear branch of native
`AecCheckDelay` (ELF 0xa13b8). Disabled policy or a changed mode resets both
counters and marks a transition. Stable error direction resets the counters
without marking a transition. A new direction tracks positive/negative start
frames independently, compares the current error with 0.98 times its reference
error, clears the opposite counter and returns whether the selected delay has
not yet elapsed. The native linear counter caps at 255; its frame arithmetic
and byte narrowing are preserved.

The native return and all modified state bytes match in 1,000 comparisons,
including zero errors/frame IDs, direction changes, disabled/mode-reset paths,
0.98 boundary values, byte thresholds and signed-frame wrap behavior. The
reference also checks that unrelated context bytes remain unchanged. Host and
ARM replay pass. [Equivalence report](ae-delay-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-delay.py --arm
```

This is a hold gate inside brightness control, **not** the sensor's physical
register-to-frame delay. Its policy flags, error history and frame IDs still
need to be supplied by the surrounding controller. HDR, full damping/brightness
integration, frame/parameter/exposure history and live automatic writes remain
unfinished.


## Histogram-to-damped-exposure prefix

`ae_brightness::standard` now joins the recovered histogram solver to the
standard linear prefix of `AecClmExecute` (ELF 0xa40c8). It computes signed
relative brightness error, applies the selected tolerance deadband, chooses
under/over-target fixed damping, applies the native saturation/FPS damping cap
on the over-target path, blends old exposure with the solver request and
clamps to aggregate exposure bounds.

The blend follows the actual ARM instructions: first round
`damping * oldExposure`, then use a fused multiply-add for
`(1 - damping) * requestedExposure + roundedOldTerm`. A generic unfused blend
would change float bits. Native saturation limits the damping coefficient to
`0.05 * min(fps / 30, 1)` on the applicable branch.

The native reference executes the real `AecClmExecute` prefix and its actual
`ClmExecute` call, stopping at ELF 0xa4446 immediately before environment
history processing. It compares candidate exposure, signed relative error and
saturation state in 160 cases. Inputs cover histogram shapes, zero/dark/bright
measurements, tolerance boundaries, fixed damping extremes and multiple frame
rates. Host and ARM replay pass.
[Equivalence report](ae-brightness-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-brightness.py --arm
```

This API covers standard histogram mode with environment compensation and
dynamic damping disabled. Alternate policy/tolerance modes, environment-history
correction, transition holding, route dispatch and sensor scheduling are not
included in this prefix. The output must not yet be treated as a complete live
AE command. The separately recovered dynamic damping and delay routines remain
to be integrated with their native context/history population.


## Environment-history exposure correction

`ae_environment::adjust` reconstructs the complete linear branch of
`AecClmExpChkForEnv` (ELF 0xa379c). It selects current/previous records from a
five-entry ring. The frame offset is clamped to at least one; when it is below
the queued-exposure count, that queued value from the previous record is the
reference, otherwise the previously published exposure is used. Matching error
directions constrain the candidate toward that reference; direction reversal
leaves the candidate unchanged. The initial-history path clears priming and
queued count and stores the current exposure as the held value.

Six hundred native comparisons cover distinct ring slots/queued entries,
positive/negative/zero errors, priming, zero through six queued exposures and
frame offsets before/within/beyond the queue. Candidate float bits and all
context changes match; unrelated bytes are checked for preservation. Host and
ARM replay pass. [Equivalence report](ae-environment-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-environment.py --arm
```

The history records and queue count are explicit inputs. Their producer
functions and association with actual sensor/ISP frames still need integration;
this helper does not itself establish that association or schedule sensor
writes. HDR is excluded, and the checked API rejects nonfinite history,
queue counts above six and negative/out-of-range ring indices.


## Producing the environment history

The same module now reconstructs both linear history writers:
`record_current` follows `AecCurInfoSetForEnv` (ELF 0xa0f2c), writing frame ID,
current aggregate exposure and signed brightness error to `index % 5`.
`publish` follows non-iris `AecClmExpSetForEnv` (ELF 0xae428), writing the
selected aggregate exposure, queue count and up to six queued real exposure
products in the native order `(gain * time) * ispGain`. The sensor's
separate digital field is not multiplied here, matching this native routine.
Unused queue slots retain their old values. Neither routine advances the ring.

One hundred forty comparisons execute both original routines through normal
return for 20 ring indices and queue lengths zero through six. They compare
all 220 bytes of the five native records, including untouched fields/tail
entries, and verify preservation of the rest of the native context. Host and
ARM replay pass. The existing 600 correction cases also pass with the expanded
record type. [Writer equivalence report](ae-history-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-history.py --arm
```

The checked publisher rejects nonfinite/overflowed products and more than six
queue entries before changing history. HDR and iris remain excluded. These
writers supply the record format required by the recovered correction, but
ring advancement, queued exposures and association to real captured frames
must still come from the surrounding controller; automatic writes remain off.


## Connected standard linear control step

`ae_controller::step` connects the reconstructed pieces in the order used by
`AecClmExecute` (ELF 0xa40c8): histogram solve and fixed directional damping,
current-history write, environment correction, transition-delay gate,
error-direction/held-exposure handling, cached automatic route dispatch and
publication of the resulting time/gain/ISP-gain aggregate. It carries the
native error/cache/delay/history state between calls. Queue-history publication
remains a separate call after the surrounding controller supplies its queue.

The comparison now executes the **complete native brightness-control call
through normal return**, including the original subordinate numerical/control
routines. The connected corpus now covers 1,280 cases comparing resulting gain, ISP gain, shutter,
aggregate exposure, relative/previous/reference errors, environment/hold state,
delay counters, cache, all 220 history bytes and route-time mutation. Other
native context bytes are checked for preservation. Cases exercise bright/dark
measurements, deadband boundaries, priming, error reversal, holds, mode resets,
cache/force and saturation/FPS effects. Host and ARM replay pass.
[Connected-controller report](ae-controller-equivalence.json).

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-controller.py --arm
```

The checked branch uses standard linear histogram policy, fixed or dynamic
damping, a uniform supplied tolerance and non-iris successful route paths.
Alternate control modes and native error-path partial publication are excluded. The harness models integer division/remainder and imported rounding.
This verifies the connected algorithm branch, not a running camera service.

The caller must still supply the applied exposure corresponding to the
statistics, calibrated/runtime limits and policies, frame/synchronization IDs,
ring advancement and queued real exposures. Sensor conversion/control writes,
ISP digital-gain publication, actual delay association and automatic white
balance remain to be connected and tested. No live automatic writes are
enabled by this addition; errors can leave intermediate algorithm state
changed, so callers must not publish a failed step as a successful decision.


### Dynamic damping connected

The pinned SC3336 `AecSpeed.DyDamp` enables dynamic damping. The connected
controller now accepts its explicit policy/history through
`ae_brightness::Dynamic` and runs the recovered `ae_damping::calculate` before
the saturation/FPS cap and fused exposure blend. The standard fixed wrapper
remains available. Dynamic output includes the native diagnostic slot, trend,
normalized trend and normalized current error.

The complete native-call corpus now contains 640 cases: each prior controller
scenario runs with no dynamic call, an inner-disabled call, automatic rules,
and custom rules. Native coefficient effects, all three diagnostic writes and
preservation of unrelated context bytes are checked together with the rest of
the controller. Host and ARM replay pass; the original 160 fixed-prefix cases
also still pass. The history producer is connected below; live statistics input,
calibration/policy binding, exposure association and actual sensor/ISP updates
remain caller/integration work.


## Native preprocessing error history

`ae_preprocess::record_error` reconstructs the standard linear history write
in `AecPreProcess` (ELF 0xb33d0). Active processing stores
`(measured - selectedTarget) / selectedTarget` at `frame % 10` and publishes
that error. It does **not** apply the brightness-controller tolerance deadband
to this history. When the native run decision skips processing, it copies the
previous ring entry to the current slot and publishes the copied value.

Four hundred twenty cases execute native preprocessing to the current-error
publication checkpoint, comparing all ten history values and current error
across ring wraps, active/skipped processing, and dark/target/bright readings.
The run-flag decision is controlled and the selected target curve is fixed at
45 to isolate the history stage. Native target selection itself remains covered
by its separate profile/interpolation comparison. Host and ARM replay pass.
[History publication report](ae-preprocess-history-equivalence.json).

`ae_controller::step_with_history` connects the active history write to the
existing controller, supplying the updated ring to dynamic damping. The
connected corpus now has 1,280 cases: the 640 fixed/dynamic controller scenarios
each run with explicit prior history and with native preprocessing/history
publication followed by the complete native control call. It checks all ten
history values as well as controller outputs, cache, delay/environment records
and damping diagnostics. The preprocessing comparison stops at its documented
checkpoint; the control call executes through normal return.

```sh
mise exec rust@1.93.1 -- cargo build --locked --release --manifest-path firmware/rkaiq-rs/Cargo.toml --bin numeric-fixture
mise run camera:rust:arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-preprocess-history.py --arm
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-controller.py --arm
```

The active helper requires the caller to establish the run decision and select
the target first. Skipped frames update history through `record_error(run=false)`;
this addition does not claim the surrounding skipped-frame output policy.
Environment-compensated history, alternate luma modes, HDR, complete run-flag
selection and live sensor/statistics association remain outside this stage.
The native error history is now produced by Rust, but this does not enable
live automatic writes or complete the camera service.

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

Eight hundred forty cases execute native preprocessing to the current-error
publication checkpoint, comparing all ten history values and current error
across ring wraps, active/skipped processing, and dark/target/bright readings.
Half control the run decision; half execute the native run decision with
explicitly seeded previous/current Q8 means and flags. The target curve is fixed
at 45 to isolate the history stage. Native target selection itself remains covered
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


## Native process/skip decision

`ae_run_flag::select` reconstructs the complete `AecGetRunFlag` function
(ELF 0xb31f0), including its single-channel branch and accumulating channel
branch. The change ratio is the absolute difference divided by the previous
Q8 mean (denominator one if it was zero). The native operation divides in
double precision, rounds to float, then compares that result against a double
`0.03` literal. The exact threshold therefore matters at boundary samples.

Disabled gating returns one. Otherwise the result depends on the change test,
per-channel unchanged-sample flags and overrides. Raw nonzero flag bytes are
preserved rather than normalized to a boolean. Field names retain their context
offsets because the surrounding calibration and flag lifecycle have not yet
been recovered; these are not user-facing operating-mode labels.

The full native function returns normally in 3,091 comparison cases. They cover
zero/maximum Q8 means, 3% boundaries, raw flag bytes, zero through three channels,
mixed unchanged/changed channels and override precedence. Every context and
sample byte is checked for preservation. The native null-context return is
separately checked; Rust uses non-null typed inputs.
[Process/skip comparison](ae-run-flag-equivalence.json).

The history oracle also now connects the real native run decision to the
preprocessing history checkpoint in 420 of its 840 cases. The Rust fixture
connects `select` to `record_error` for those same inputs. Maintaining previous
means and flags over a real stream, and handling the rest of skipped-frame
output publication, remain integration work. No live automatic writes are
introduced.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-run-flag.py --arm
```

## Ordinary linear caller bookkeeping

`ae_run::linear` connects the ordinary statistics-present, automatic linear
`AecRun` caller (ELF 0xb0d1c) to the recovered control body. This supplies two
state lifecycle rules previously left to the caller:

- Copy the last aggregate output into the environment held-exposure field
  before testing the process/skip flag, including on skipped frames.
- On a processed frame, increment the five-entry history index **before** the
  control call, then publish current linear/HDR mean fields and all three Q8
  means as previous samples. A skipped frame preserves the index and samples.

The process decision's unchanged-sample flag at `+0x23cf` is the already
recovered delay state's `changed` flag. Its override at `+0x3d3c` is the
route-cache `force` flag. These identities follow the actual writer addresses;
the gating-enable writer at `+0x4fb9` is recovered in the next section.

Six hundred forty comparisons execute native `AecRun` through normal return,
including the real `AecClmExecute` and subordinate numerical routines, and
compare outputs, complete history records, cache, damping diagnostics, index
and previous samples. Process/skip cases cover fixed/dynamic damping, priming,
route forcing and transition-delay state. Unrelated context bytes must remain
unchanged. Host and ARM replay are required by the published report.
[Caller comparison](ae-run-equivalence.json).

DCG and register-value conversion are explicit successful no-op boundaries in
this comparison; it checks their call counts (two on processed frames, zero on
skipped frames), without claiming conversion or driver-write equivalence.
Preprocessing supplies the run flag and measurements. Manual, missing-statistics,
HDR and iris branches are excluded. The Rust wrapper returns `None` for skip so
the caller retains its output. It only handles successful control paths; callers
must not publish partially updated state after an error. Native signed index
overflow is outside the accepted Rust numerical domain.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-run.py --arm
```

## Linear convergence flags

`ae_convergence::linear` recovers the flag-publication branch of
`AecGetProcResults` (ELF 0xb1e70). It compares the effective preprocessing
exposure against both the newly proposed output and the prior published
exposure. Time and gain **register codes** must agree exactly. Each ISP gain
comparison subtracts in float, then compares the promoted absolute difference
against the reference gain times the double literal `0.001`.

Agreement writes one to both `+0x4fb8` (dynamic damping enable) and `+0x4fb9`
(process gating enable). Disagreement clears only `+0x4fb9`; dynamic damping
enable retains its previous byte. This sticky behavior is intentional and
matters after the first converged frame. The Rust helper preserves raw flag
bytes on branches where the original does not overwrite them.

The native oracle executes result processing through that flag store and
compares both bytes across 894 cases, including sensor-code mismatches, zero
gain, exact/near tolerance boundaries, random gains and preexisting raw flag
values. All unrelated context bytes are checked for preservation. This is a
checkpoint comparison, not a claim that all result packaging has been ported.
[Convergence comparison](ae-convergence-equivalence.json).

Effective, proposed and prior-published records remain explicit inputs. Their
publication and real frame association must be established before this helper
can safely close the hardware feedback loop. The accepted domain is finite,
nonnegative ISP gains in linear mode.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-convergence.py --arm
```

## Connected standard frame step

`ae_frame::linear` connects the recovered stages in their native order:
process/skip selection from the previous Q8 mean, delay-change flag, route-force
flag and convergence gating byte; active target selection; active/skipped
error-history publication; dynamic-history/enable binding; then the automatic
linear caller and brightness controller. A skipped frame retains the target,
copies the previous error-history slot, preserves previous samples and control
index, and returns no new control output. The caller retains its last output.

The active branch derives mean brightness directly from Q8 statistics and uses
`ae_target::select` for its target. Dynamic damping receives the updated history
and the sticky damping-enable flag, while the delay gate receives the convergence
gating flag. These flags are no longer independent fabricated decisions in the
connected wrapper. Policy, target curves, limits and correctly associated current
exposure remain explicit inputs.

The connected comparison executes real native `AecGetRunFlag` inside standard
preprocessing, stops at the current-error checkpoint, then executes native
`AecRun` through normal return including its real brightness controller. Six
hundred forty cases compare the connected Rust result, all ten error-history
entries, all five control-history records, delay/cache/damping state, index and
previous mean samples. The corpus includes real processed and skipped paths;
the report records their counts. The fixed target curve is 45 for this comparison;
variable target interpolation remains covered separately.
[Connected frame comparison](ae-frame-equivalence.json).

Conversion is still an explicit successful no-op boundary in this oracle, and
result publication/convergence updating requires associated converted exposure
records from the caller. Environment-compensated history, HDR, iris, manual
modes, full preprocessing side effects, runtime calibration binding and live
sensor writes remain outside this frame step. This does not establish physical
exposure latency or complete the AE/AWB camera service.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-run.py --frame --arm
```

## Converted intermediate exposure queue

`ae_conversion_queue::linear` ports the ordinary automatic, non-iris,
DCG-disabled `AecRegValueConvertion` caller (ELF 0xaf0b0), including its real
sensor/ISP converter. It first converts the proposed output. It then selects
a starting aggregate exposure from the previous publication: the frame delta
is signed/wrapping and clamped to at least one; if that index is below the
published count, the selected point's product is `(gain * ISP gain) * time`.
Otherwise the held aggregate exposure is used. This multiplication order differs
from some other native aggregate writers and is preserved.

For each requested intermediate step, the function interpolates in logarithmic
exposure space, routes the result through the direct automatic route, selects
disabled DCG (`-1`), and performs the complete register correction and ISP
compensation loop. Its published aggregate is recomputed from the corrected
real point as `(gain * time) * ISP gain`. The target aggregate remains an explicit
input, matching the native caller's separate aggregate field. Zero through five
intermediate slots are supported; the final exposure is returned separately.

270 comparisons execute the complete native caller through normal return,
including real automatic routing, native disabled-DCG selection, register
conversion and inverse mapping. They compare the converted final exposure,
every populated intermediate aggregate/point/code/DCG/iris slot, mutated route
time knots, and preservation of unrelated context. Cases cover all six queue
lengths, negative/zero/positive frame differences, empty/short/full prior queues,
and increasing/decreasing/equal aggregate transitions.
[Conversion queue comparison](ae-conversion-queue-equivalence.json).

The native oracle executes pinned uClibc logarithm, power and rounding code as
needed. Allocation/free and integer division are explicit boundary models.
Policy, actual exposure association and prior publication are supplied inputs;
result packaging and subsequent history/publication updates remain external.
The checked Rust wrapper rejects manual modes and oversized queues. It does not
enable live automatic sensor writes.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-conversion-queue.py --arm
```

## Linear exposure publication selection

`ae_publication::select` recovers the linear queue-selection part of
`AecGetProcResults` (ELF 0xb1e70). Input records retain the native 244-byte
layout. Equality uses the first **48 bytes**, so floating-point bit patterns,
DCG and register-code fields all participate; this is not approximate numeric
equality. `pack` provides the ordinary non-iris fixed-timing record layout.

If the final proposed key matches the previous final key, frame-length and
iris metadata are checked separately to decide whether a one-record update is
needed. Otherwise the prior queue reference uses the clamped frame difference
minus one (different from the conversion queue's starting-point index), initial
matching proposals are skipped, and subsequent adjacent duplicate keys are
removed. A remaining transition updates the synchronized frame and the last
record's iris-change byte.

The native scratch-copy operation retains the first 48 bytes, auxiliary bytes
192 through 227, and frame length at bytes 232 through 235. It leaves line
length and pixel clock zero in those selected scratch records. The port
preserves that behavior rather than filling metadata the binary did not copy.
Zero-count results also have distinct native branches: an unchanged final
record retains the previous-final fallback, while a transition whose every
proposal matches the selected old-queue key returns zeroed scratch/final records.

630 comparisons execute native result processing through normal return,
including its CIS feature and environment-history publication calls. They
compare the complete six-record output area, count, synchronized frame and
final record, covering one through six proposals, short/full prior queues,
frame differences, duplicate patterns, same-final metadata changes, and the
all-matching transition branch. The comparison does **not** claim equivalence
for the other result fields or context side effects.
[Publication selection comparison](ae-publication-equivalence.json).

Fixed frame-length mode and explicit prior/proposed records are used. Iris
metadata differences test selection policy, not iris hardware support. `memcmp`
and integer division are modeled boundaries. Binding converted records to
this selector and publishing its history/state updates remain integration
work; no live sensor writes are enabled.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-publication.py --arm
```

## Connected exposure-publication state

`ae_publication::finish` connects selection to the recovered state updates in
native result processing. It updates convergence from the effective exposure,
newly proposed final exposure and previous final exposure **before** selection.
It saves the selected queue only when the synchronized frame equals the current
frame, then publishes the native aggregate and the saved queue into the current
five-entry environment-history slot. Finally it saves the returned final record
and last-result frame. A zero output count therefore does not necessarily mean
the stored publication queue is cleared.

The 636-case connected comparison checks all output queue bytes plus both convergence
flags, stored queue/count, prior-final replacement, last-result frame and all
220 environment-history bytes against complete native `AecGetProcResults`
execution. The corpus covers all five history slots and raw prior enable flags,
matching/mismatching effective sensor codes and ISP gain, and empty/short/full
prior queues. Empty queues are accepted for the same-final-key branch. Standalone selection
rejects a new transition with no prior queue; connected publication can use an
explicit `empty_reference` record for the native context region preceding the
queue, as described below.
[Connected publication state report](ae-publication-state-equivalence.json).

The comparison still does not qualify other ISP result fields, CIS flags or
unlisted context bytes. Proposed records, history index and effective exposure
remain explicit inputs. Converted-record assembly, full frame orchestration and
physical exposure association remain integration work. Callers must discard
partially updated state on errors.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-publication.py --state --arm
```

## Joined conversion, record assembly and publication

`ae_result::linear` joins corrected queue conversion, native record assembly,
convergence, publication selection and saved exposure/history state. It decodes
the prior published records for the conversion base, converts the proposed
point and intermediate points, packs the corrected results with timing derived
from calibration, then invokes `ae_publication::finish` on those records.
The aggregate requested by the controller remains separate from the corrected
physical point, matching the native fields and history writer.

300 comparisons execute the complete native register/queue converter followed
by complete native result publication **on the same context without resetting
it between stages**. They compare final/intermediate points and sensor codes,
route changes, selected 244-byte records, count/synchronized frame, convergence
flags, saved publication, previous-final replacement, last-result frame and all
five environment-history records. Thirty cases use an exact native-converted
prior-final record to exercise unchanged-final/converged publication, alongside
270 transition cases spanning queue lengths zero through five and frame deltas.
[Joined result comparison](ae-result-equivalence.json).

The wrapper accepts the controller's proposed point, aggregate and associated
effective exposure as inputs. It does not yet invoke preprocessing or the
brightness controller itself. Other ISP result fields, CIS flags, physical
exposure association and hardware writes remain outside this scope. Fixed
timing, automatic routing and the ordinary non-iris/DCG-disabled SC3336 path
are the checked domain. Partial state after an error must be discarded.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-result.py --arm
```


## Joined standard linear frame pipeline

`ae_pipeline::linear` now joins standard preprocessing/history, run/skip selection,
brightness control, sensor/ISP conversion, intermediate records, convergence,
publication and exposure-history updates. Processed frames replace the retained
converted proposals. Skipped frames keep those converted proposals and the
requested aggregate, while still running result publication and its state updates.
They do not run conversion again.

The integration preserves a native alias: controller environment queued-count
and publisher saved-count are the **same** context field (`+0x5574`). The wrapper
synchronizes its typed views before/after each owning stage. Priming can clear
this count before conversion and publication, so treating the copies as independent
state produces a different pipeline even when each individual helper passes.

When publication has no saved entries, the native selector reads the 244-byte
region at context `+0x4ec8`, immediately preceding the queue. Connected state
carries those explicitly initialized bytes as `empty_reference`; Rust performs
no underflow memory access and does not invent a reference exposure. The joined
frame corpus seeds this region to zero, matching its native initialized context.
Six additional publication-state cases check both matching and differing explicit
reference keys with an empty saved queue.

192 host/ARM comparisons execute native preprocessing to its current-error
checkpoint, then complete native `AecRun` **with real DCG-disabled selection,
register conversion and intermediate queue generation**, then complete native
result publication, all on the same context. The corpus has 160 processed and
32 skipped frames across intermediate counts zero/two/four/five, fixed/dynamic damping,
priming, held transitions, saturation and route forcing. It compares listed
controller/cache/delay/convergence/history/sample state, converted final codes
and real point, requested aggregate, route knots, complete selected/saved queues
and previous-final records.
[Joined frame pipeline report](ae-pipeline-equivalence.json).

This is still an explicitly initialized, single-frame corpus. It does not prove
multi-frame sequence equivalence, full preprocessing side effects, runtime/profile
binding, physical applied-exposure association, AWB service completion or live
feedback behavior. Target is fixed at 45 in this corpus; limits/timing/policy are
explicit. Other ISP result fields, CIS flags and unlisted native bytes remain
outside the comparison. The module performs no hardware writes, and callers
must discard partial state after any failure.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-pipeline.py --arm
```

## Persistent multi-frame pipeline comparison

The pipeline fixture now initializes state once per sequence and retains it
across frames. The native oracle likewise retains its context, route arrays,
converted proposals and publication/history state; it does not rebuild them
between frame calls. Every frame still runs the native preprocessing checkpoint,
complete automatic caller/conversion, and complete result publisher.

36 sequences of 32 frames compare 1,152 frame results, including 1,052 processed
and 100 skipped frames. Twelve bind actual profile damping/tolerances, frame delays, dynamic mode and fixed FPS. Intermediate counts zero/two/five, dynamic damping on/off
and priming on/off are covered. The comparisons include all the outputs and
listed state from the single-frame corpus on **every** step, crossing the
five-record control-history and ten-entry error-history ring boundaries.
[Persistent sequence report](ae-pipeline-sequence-equivalence.json).

Twelve sequences supply an explicit exposure scalar and zero sensor codes
as in the earlier fixture. The other twenty-four supply the previous converted point,
ISP gain and codes as the next preprocessing exposure-info record. Rust derives
those inputs independently from its retained converted proposals, and the native
oracle reads its own converted context fields and passes the actual by-value
sensor-info ABI. These cases exercise convergence and skipped frames later in
the sequence as well as initial skips. Statistics follow a prescribed dark,
target and bright pattern; they are not synthesized from an optical model.

This establishes the tested state transitions, not real exposure latency or
physical frame association. Feeding the previous proposal back as an explicit
input is an idealized test strategy, not a claim that hardware applies it one
frame later. Target45, runtime policy, linear non-iris/DCG-disabled scope and
preprocessing checkpoint limitations remain. Runtime initialization/calibration
binding, full preprocessing side effects, complete AWB and live feedback still
need work.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-pipeline-sequence.py --arm
```

## Profile tolerance and damping selectors

`ae_policy::Calibration::from_scene` reads `ToleranceIn`/`ToleranceOut` from
`LinearAeCtrl` and all four damping coefficients from `CommCtrl.AecSpeed`.
`select` binds them to the standard control inputs: gating disabled uses
`ToleranceIn`, gating enabled uses `ToleranceOut`. Native context `+0x23ce`
selects the alternate coefficient pair. The ordinary pair is `DampUnder` /
`DampOver`; the alternate under/over pair is `DampBright2Dark` /
`DampDark2Bright`, matching the native context accesses rather than inferring
behavior from the field names.

The pinned profile therefore uses 10% versus 15% tolerance, with regular
under/over damping 0.45/0.15. Its alternate coefficients happen to be identical,
so the comparison also deliberately substitutes distinct values to distinguish
all selector branches. The producer of `+0x23ce` remains an explicit runtime
input; this helper does not claim to reconstruct that producer or `SmoothEn`
handling, dynamic-mode/slow parameters, delay calibration or FPS selection.

256 comparisons execute complete native `AecClmExecute`, checking control
outputs and the existing full controller/history/cache/delay/damping diagnostic
comparison. Half use the actual profile; half change tolerances and all four
damping values. The recovered context slots are seeded explicitly, so this is
not a claim of complete native calibration-loader equivalence.
[Policy selector comparison](ae-policy-equivalence.json).

The persistent pipeline corpus additionally includes twelve sequences using
these actual profile coefficients and selecting tolerance from the live
convergence state on each frame. The other runtime limits and policy remain
explicit. The JSON loader rejects missing/nonfinite values, negative tolerances
and damping outside zero through one.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-policy.py --arm
```

## Profile transition-delay binding

`ae_delay_calibration::Calibration` reads `CommCtrl.AecDelay` and binds its
black/white values to the negative/positive transition counters used by
`AecCheckDelay`. These are controller transition delays, **not** sensor
register-application latency or the sensor's separate time/gain/DCG delays.

The pinned SDK [`aec_head.h`](https://raw.githubusercontent.com/LuckfoxTECH/luckfox-pico/0b5c1f30ca6333b7ec5af70d26511da9ef8d39af/media/isp/release_camera_engine_rkaiq_rv1106_arm-rockchip830-linux-uclibcgnueabihf/include/rkaiq/iq_parser_v2/aec_head.h)
defines `DELAY_TYPE_FRAME=0` and `DELAY_TYPE_TIME=1`. Its hash is now pinned in
`artifacts.json`. Frame mode copies both bytes directly. Time mode computes the
runtime period as `((frameLength * lineLength) / pixelClockMHz) / 1_000_000`,
then converts each byte using `(value / 30) / period + 0.5` before truncation.
The final native byte store wraps values above 255; Rust preserves this for
finite, bounded inputs instead of silently saturating them. Extreme values
outside the checked signed-conversion domain are rejected.

120 comparisons execute complete native `AecUpdateConfig` through normal return,
checking both delay bytes and confirming the selected timing values. Cases cover
both modes, four frame lengths, three clock/line geometries, zero and asymmetric
delays, and values that wrap at high frame rates.
[Delay calibration comparison](ae-delay-calibration-equivalence.json).
The inherited configuration oracle explicitly supplies runtime/configuration
inputs and models allocation, comparison, division, rounding and diagnostics;
it does not establish full private-context or calibration-loader equivalence.

The actual profile uses frame mode with black/white delay two. Its twelve
persistent profile-policy sequences now pass those counts into the controller
alongside the previously bound tolerances and damping coefficients. Time mode
is qualified separately at the configuration binding level; the persistent
pipeline corpus currently exercises the profile's frame mode only.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-delay-calibration.py --arm
```

## Profile dynamic-damping binding

`ae_dynamic_calibration::Calibration` binds `CommCtrl.AecSpeed.DyDamp` to the
recovered controller. `DyDampEn` decides whether the dynamic routine is called;
the separate runtime convergence byte decides whether the routine changes its
input coefficient. Those enables are intentionally independent.

The pinned SDK `rk_aiq_comm.h` defines AUTO as 1 and MANUAL as 2; its hash is
now included in `artifacts.json`. Native mode 2 replaces the default scale and
middle coefficient with profile `SlowRange` and `SlowDamp`. AUTO uses the
recovered default rule. The checked loader accepts those two named modes and
validates enable/value fields; manual scale zero is rejected because the
recovered numerical path requires a positive scale.

256 comparisons execute complete native brightness control and compare its
outputs, full controller/history/cache/delay state and damping diagnostics.
They cover profile call-enable on/off, runtime enable on/off, AUTO/MANUAL,
and distinct manual scales/middle values. Sixty-four cases retain the actual
profile's enabled/AUTO parameters; other cases deliberately exercise variants.
[Dynamic calibration comparison](ae-dynamic-calibration-equivalence.json).

The twelve persistent profile-policy sequences now bind the actual profile's
enabled/AUTO dynamic configuration as well as tolerances, damping coefficients
and frame delays. The runtime enable still evolves through recovered publication
convergence, not a calibration constant. Native context slots are supplied from
the profile in the oracle, so full native calibration-loader equivalence is
not claimed. FPS selection, initialization and physical frame association
remain separate work.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-dynamic-calibration.py --arm
```

## FPS configuration selection

`ae_fps::Calibration` binds `CommCtrl.AecFrameRateMode` to the recovered
`AecUpdateConfig` selection. Cached baseline frame length/FPS, current timing
and minimum FPS are explicit inputs; the baseline-refresh owner is not inferred.
Fixed mode updates the active frame length. Variable mode updates its separate
frame-limit field while preserving the current active frame length during
configuration. The effective controller FPS is recomputed from active timing as
`((pixelClockMHz * 1_000_000) / frameLength) / lineLength`.

A zero request selects the cached baseline frame length; the selected-request
field remains zero. A request above the cached maximum uses the baseline.
A supported nonzero request is raised to the configured minimum FPS and its
frame length is rounded using the native operation order. The opposite mode's
selected-request field remains unchanged. No extra re-clamp is inserted when
minimum FPS exceeds the cached maximum; the native branch behavior is retained.

90 comparisons execute complete native configuration through normal return,
comparing active frame length, effective FPS, variable frame limit and both
selected-request fields. They cover fixed/variable modes, zero/low/high requests,
minimum-FPS clamping and different current timing geometries, while confirming
the supplied baseline remains unchanged.
[FPS selection comparison](ae-fps-equivalence.json).

The pinned profile uses fixed mode with `FpsValue: 0`; with the fixture's cached
baseline 1360 lines, 2800 pixels/line and 114.24 MHz, this yields 30 FPS. The twelve
profile-policy pipeline sequences now bind that FPS selection too. Their native
pipeline context uses the configuration-tested baseline rate; the separate
configuration comparison exercises the full selection branches. Actual runtime
baseline initialization/refresh and variable-VTS evolution remain external.
This helper performs no sensor VBLANK writes and does not qualify exposure
application latency.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-fps.py --arm
```

## Cached FPS baseline refresh

`ae_fps::refresh_baseline` ports the timing-stage write predicate and all four
cached fields: frame length, pixel clock, line length and derived FPS. At that
native stage a refresh occurs when `(updateMask & 0xfbff) == 0`; the test is not
simply whether bit `0x400` is present. It returns a replacement baseline when
the native stage writes one, or `None` when existing cache values must remain.
The caller then uses its cached frame/FPS for the previously recovered selection.

108 comparisons execute complete native configuration through normal return
across masks `0x80`, `0x400`, `0x480`, `0x10400`, `0x100400` and `0x40080`.
They compare all baseline fields and the resulting active frame/FPS, variable
frame limit and selected rates. This checks refresh versus preservation,
high-bit behavior, different timing, fixed/variable modes and request handling.
[Baseline refresh comparison](ae-fps-refresh-equivalence.json).

This helper represents the predicate **once configuration reaches the timing
stage**, not complete outer update-mask dispatch. The original incomplete synthetic zero-mask probe returned a configuration
error without establishing a refreshed baseline. The complete profile-record
comparison below now qualifies successful zero-mask configuration. Full
`AecInit`/`AecCalibConfig` integration remains separate. The oracle
uses explicit prior cache and valid timing; unrelated context and hardware
VBLANK writes remain outside this comparison.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-fps-refresh.py --arm
```


## Complete profile records and successful zero-mask configuration

The earlier zero-mask error came from missing linear dynamic-setpoint array
lengths. `scripts/ae_profile_layout.py` now builds the complete AE and sensor
records from the pinned SDK headers and profile. It uses explicit 32-bit
emulated pointers, checks dynamic lengths, requires known fields/declarations,
and zero-fills unused fixed-table storage. It supplies 41 pointed arrays.
The AE record is 0x1c20 bytes and the sensor record 0x10c bytes; together they
end at configuration offset 0x1d2c, before the measurement seed/runtime records.

The tool generates C from the literal pinned headers and verifies 354 structure
size/field-offset assertions with the ARM compiler through mise/Zig. This checks
the Python packet layout against the target compiler rather than relying on
host pointer sizes. Generated C/object files stay in ignored `dist` storage.

32 complete native `AecUpdateConfig(mask=0)` calls now **return success** using
these records. Their selected FPS/baseline, tolerance/damping, transition delays,
smoothing counts, initial exposure, dynamic configuration, gating reset, control
index reset and all five cleared control-history records match the composed
Rust bindings on host and ARM. Control history and gating/index fields are
seeded with nondefault values before the call to verify their reset behavior.
The corpus varies smoothing, sensor time/gain delays, frame lengths and initial
shutter values. [Zero-mask configuration comparison](ae-zero-config-equivalence.json).

`ae_smoothing` recovers the intermediate-count producer: disabled smoothing
sets both counts to zero; enabled smoothing selects the maximum time/gain update
delay plus two, with native byte conversion and a maximum of five. The checked
profile loader accepts the SDK's zero-through-ten sensor-delay range. For this
profile the resulting linear count is **four**, not an arbitrary test setting.
The separate HDR count is compared as configuration data; HDR operation is not
qualified by this test.

Native initialization/reset uses signed `-1` for the control-history index.
`ae_run::linear` now permits that initial sentinel to wrap to zero on the first
active frame, while retaining the checked domain for ordinary indices. The
joined frame corpus includes sentinel-start cases and intermediate count four.
A fresh native configuration clears processing gating, so its first frame is
processed rather than attempting publication with an unadvanced sentinel index.

This is successful complete **configuration execution with selected binding
comparisons**, not complete Rust engine initialization or full private-context
equivalence. The native JSON parser is not executed. Runtime geometry remains
explicit. The measurement seed comes from real native initialization, while configuration
still uses a separate explicitly initialized context. Remaining Rust runtime state
construction, AWB and physical exposure association still require work. No hardware
writes are enabled.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-zero-config.py --arm
```

## Native initialization and Rust activation lifecycle

The new [initialization oracle](scripts/ae-initialization.py) executes the actual
`AecInit` and `AecCalibConfig` bodies. Their calibration call is no longer
replaced by a no-op in this oracle. It supplies header-derived AE (7,200 bytes),
sensor (268 bytes) and lens-module (16 bytes) records. The pinned module header
adds seven ARM compiler layout assertions, bringing the total to 354.

Eight profile variants return successfully. Each constructor allocates the
0x5998-byte engine and 0x25a4-byte configuration plus 41 owned table copies.
The comparison checks all fixed copied bytes, pointer ownership, allocation
sizes and pointed data, and confirms that source records/tables remain intact.
`malloc` storage is poisoned to catch uninitialized copies; `calloc` is zeroed.
The one explicit sensor-record exception is its first four bytes: native
calibration leaves resolution zero instead of copying the profile resolution.
Runtime image geometry must be supplied during preparation.

Only allocation, profile-module lookup and memory primitives are modeled here.
The ELF contains duplicate local symbols for the module accessor; the harness
now resolves the AE instance explicitly at mapped address 0x000b6b5c and rejects
ambiguous name-only resolution. The modeled accessor supplies `ae_calib`,
`sensor_calib` and `module_calib`; the binary performs the actual copies.

`ae_lifecycle` ports `AecStart` (ELF 0xa7618) and `AecStop` (ELF 0xa76a4).
Initialization sets numeric state 1. Start changes it to 3, enabling the
histogram controller; stop changes it to 2. Start rejects existing states 3/4,
stop rejects state 4, and both return native error 8 for a null context.
Other numeric states retain the binary's permissive predicates. Repeated calls,
null contexts and boundary/unknown states are checked across 266 sequences and
1,002 calls on host and ARM, including eight sequences on genuinely constructed
native contexts. Each native call is also checked for mutations outside the
four-byte lifecycle field. [Recorded comparison](ae-initialization-equivalence.json).

The zero-mask configuration oracle now obtains its measurement seed from this
real constructor instead of the earlier calibration-no-op checkpoint harness.
Its configuration call still uses a separate explicit context. The next oracle
below joins native construction and preparation, with selected Rust startup
binding checks. The complete Rust constructor, remaining controller state and
live AE/AWB coordination remain unfinished. Starting this algorithm state does
not start a camera stream.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-initialization.py --arm
```

## Joined native preparation and Rust startup exposure

`scripts/ae-preparation.py` now invokes the real `AePrepare` on the actual engine
and configuration returned by native `AecInit`/`AecCalibConfig`. No engine fields
are patched at the update/route/conversion boundaries. For fresh linear mask-zero
preparation it runs `AecStop`, `AecHwConfig`, `AecUpdateConfig`, `AecStart` and
`AecInitEcm`, returning success. Sensor timing, dimensions and the complete
header-derived profile are explicit inputs. The original uClibc `ceilf`,
`floorf`, `roundf` and `powf` execute as ARM instructions; allocation, module
lookup, memory primitives, integer division and diagnostic logging remain
explicit harness boundaries.

`ae_startup::profile::linear` composes the recovered fixed-FPS, flicker, shutter,
gain-limit, smoothing and register-conversion ports into fresh startup state.
It takes the IQ profile and runtime sensor timing. The numerical core remains
`no_std`; JSON binding is under the diagnostics feature. The binder requires
positive initial gain, automatic linear operation and disabled iris/DCG.
Variable-rate and reprepare/update-mask behavior remain separate work.

Two native details affect startup fidelity:

- Fresh automatic configuration sets ISP gain to unity despite the profile's
  `InitIspDGainValue`. It clamps initial shutter/gain to the selected limits
  before register conversion. Requested/held aggregate exposure remains the
  preconversion value; smoothing history uses converted gain times shutter.
- Iris control being disabled does not zero all iris metadata. Configuration
  selects/quantizes the initial iris gain against the PIris table, and startup
  copies that integer into its smoothing history. The calculated table index
  goes into a stack temporary during configuration; context offset 0x2024 stays
  zero when iris is disabled, so the corresponding history field also stays
  zero. The comparison caught this distinction; no iris actuator is enabled.

The default SC3336 profile at 1,360 lines, 2,800 pixels/line and 114.24 MHz starts
with a requested 3 ms / 1× exposure. Native preparation and Rust produce shutter
code **122**, gain code **128**, and a smoothing count of **four**. No sensor
write is performed by this test.

The [preparation comparison](ae-preparation-equivalence.json) records **108** fresh
initialization/preparation cases across initial exposure, requested FPS,
frame length, smoothing delays, dimensions and iris metadata, plus clamp/flicker
edges. Each case compares 63 words: active timing/FPS, selected limits,
requested/held exposure, converted exposure/codes, count and all 45 words of
startup smoothing history. Native execution also verifies running state 3,
control index -1 and an empty publication queue after preparation.

This establishes native construction through preparation and matching selected
Rust startup outputs. The session below now connects the tested ordinary subset
to first-frame preprocessing and control/publication. Full private-context
construction, SOF scheduling and physical exposure association remain separate.
Live AE/AWB and hardware writes remain disabled.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-preparation.py --arm
```

## Profile-bound session through complete SDK frame wrappers

`ae_session::Session` now creates the prepared ordinary linear state from the
IQ profile and runtime timing, then accepts associated exposure records and
translated statistics for successive frames. It composes the existing target,
policy, damping, delay, histogram controller, routing, conversion and publication
ports. No synthetic controller history or constant target is supplied by the
new fixture: target curves, tolerances, alternate damping and smoothing derive
from the actual profile and runtime state.

The native SDK has an essential **initial publication phase** between preparation
and image frames. `AePreProcess(init=true)` publishes the starting exposure;
`AeProcessing(init=true)` calls `AecRun` without statistics, advances the control
index from -1 to zero, records the pre-frame history and publishes the initial
exposure queue. The first actual image frame then advances to index one. Calling
`AecRun` on statistics immediately after preparation omits this history and can
select minimum exposure even at a matching mean/target. `ae_startup::publish_initial`
reproduces the actual initialization phase rather than setting a guessed priming
flag. The native `rk_aiq_uapi_ae_setAOV` setter controls the separate 0x5994 flag;
ordinary startup does not require enabling that optional path.

The new oracle runs real `AePrepare`, the initial SDK wrapper calls, then full
`AePreProcess` and `AeProcessing` for each frame on the same allocated native
context. This includes normal returns from `AecPreProcess`, `AecGetPreResults`,
`AecGetEnvLgt`, `AecRun` and `AecGetProcResults`; preprocessing is not stopped at
the older current-error checkpoint. The standard preprocessing side effects now
include the full effective-exposure record, Q8/auxiliary means, exposure-normalized
brightness and proximity to minimum/maximum exposure. The recovered
`AecGetEnvLgt` state also produces the previously explicit alternate-damping flag.
It preserves the binary's multiplication order and float 5% change threshold.

Joining real initialization revealed result-state details hidden by fresh
synthetic contexts:

- Final exposure records retain PIris step/gain metadata even with iris disabled.
  Normal intermediate direct-route records use zero iris gain. This differs from
  the initially seeded smoothing history, which retains the configured iris gain.
- Native result buffers persist across frame calls. Only `max(count, 1)` records
  are overwritten, so unused queue entries retain earlier values. The session
  models this caller buffer separately from publication selection scratch data.
- The native empty-queue reference overlaps measurement data and live convergence/
  exposure-limit flags. Its defined bytes derive from the configured measurement
  record and are kept consistent with the session's runtime flags.

[Session comparison](ae-session-equivalence.json) passes **eight sessions and
128 complete frames** on host and ARM: 109 controller runs and 19 skips, with
zero mismatches. It records complete wrapper calls and native math functions. It compares initialized state
and every subsequent frame: listed controller/queue/sample fields, target/error
history, full exposure-info bytes, complete publication records and retained tails,
all five environment-history records, route times and standard preprocessing state.
The corpus changes scene brightness, initial exposure, smoothing enable/delays and
geometry. Effective exposure is explicitly replayed from the previous native
proposal as a common input; it is an idealized association, not measured sensor
application latency.

This session currently requires the profile's enabled automatic linear mode,
translated raw-statistics mean, fixed FPS and zero algorithm run interval.
Backlight/overexposure, lux estimation, automatic flicker estimation, HDR, active
iris and DCG still need their remaining orchestration. Other ISP/pre-result
structures and unlisted private context bytes are outside the new comparison.
Allocation/module lookup, memory primitives, integer division and logs remain
modeled boundaries; pinned native uClibc math executes as ARM instructions.
Camera statistics association, sensor/ISP writes, AWB and application integration
remain open. This is a software session, not a claim of a complete camera service.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-session.py --arm
```

## Raw ISP statistics, parameter IDs and exposure-map association

`ae_session::Session::step_statistics` now accepts a raw full-ISP32 statistics
buffer, complete parameter snapshots keyed by ID, and the sensor scheduler's
reported effective-exposure map. It reads the frame/parameter IDs from the
buffer, selects an exact parameter snapshot, applies the recovered effective-
exposure lookup, translates the grid/histogram with the snapshot's BLS/WB
corrections and weights, then runs the persistent AE session. The output includes
the selected IDs, exact/fallback exposure-match status, corrected Q8 mean and AE
control/publication results. No sensor or ISP write is performed.

The parameter-ID lookup is an explicit Rust integration rule, not a claim that
the vendor parameter-cache algorithm has been ported. Callers must supply the
complete accumulated ISP state for that ID; individual partial update buffers
are insufficient. Missing parameter or exposure metadata returns an error.
Missing AE/histogram validity bits returns `None`. These paths leave session
state unchanged. Effective-exposure selection uses the already recovered native
map behavior and reports whether the frame matched exactly. A reported map entry
still does not prove when the physical sensor applied its exposure.

The qualified routing remains source 1, full-range luma with the native auxiliary
source selection 3. In this configuration the SDK translator produces its primary
Q8 mean in channel zero and leaves the other mean channels zero; the composed
native test verifies those fields rather than inventing auxiliary measurements.
Additional driver validity bits are permitted: the real captured mask **0x5d80**
is included in the corpus. The older translator oracle incorrectly treated any
mask other than the two required bits as invalid in its assertion; that harness
assertion now tests required-bit inclusion, matching the native translator.

The session is still prepared for fixed timing. Effective-exposure records must
carry a matching frame length; conflicting nonzero line length or pixel clock
also requires reconfiguration. Native publication can leave the latter two fields
zero, and the sensor submission path preserves those zeros. The session now
accepts them and retains its prepare-time timing rather than inventing descriptor
values. The raw-session corpus uses actual native published records with these
zero fields. Changed frame length is rejected before controller state changes,
because native reprepare/timing-update orchestration is not yet joined. This
matters when long exposures change VBLANK; callers must not reinterpret those
frames with a stale 1,360-line configuration.

[Raw-session comparison](ae-raw-session-equivalence.json) passes on host and ARM
with zero mismatches. It composes real native
`translateAecStats`, `getEffectiveExpParams` lookup and full AE SDK wrappers on
persistent contexts. Four sequences cover 68 input buffers: 52 valid frames,
four missing-measurement buffers, four missing parameter snapshots, four empty
exposure maps and four changed-timing records. The valid frames exercise exact
and fallback exposure matches, two different parameter snapshots, changed WB
correction, initial exposure and smoothing. Native full state snapshots from
the earlier session test are compared after every input, including rejected
inputs. The explicit two-frame exposure-map example is test data, not a measured
sensor latency. Existing translator object/run-flag and map ownership/container
boundaries remain modeled; their numerical and lookup bodies execute natively.

Live snapshot accumulation, parameter-cache behavior, SOF-driven exposure-map
updates, physical frame/exposure association, driver writes and AWB remain open.
The raw-buffer entry point connects those explicit inputs to the verified AE
session; it does not establish a live automatic camera loop.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-raw-session.py --arm
```

## Exposure submission and SOF handoff

`SensorHw::setExposureParams` (ELF 0x3c474) does more than append the latest
publication queue. The ordinary, already-initialized path first removes pending
intermediate entries from earlier batches, keeping each batch's first-entry
marker. It then appends the new batch, marking only its first entry. A zero-count
submission leaves pending entries untouched. `sensor_scheduler::enqueue_batch`
now reproduces that replacement policy; single-entry `enqueue` remains available.

`sensor_submission::assemble` reproduces the queued 244-byte exposure snapshot:
start with the complete main exposure record, replace bytes 0–191 from the
selected queue entry, replace the frame-length word at byte 232 and replace
byte 240. All remaining fields retain the main record's values. This includes
iris metadata, line length and pixel clock; the setter does not invent or
restore descriptor timing. Tracing `RkAiqAeHandleInt::processing` and
`genIspResult` also found no timing-restoration step in that path. Native
publication's zero line-length/clock fields can therefore reach cached exposure
records. The fixed-timing session now accepts those zeros and uses its existing
prepare-time timing, while still rejecting changed frame length and conflicting
nonzero timing values. The raw-buffer corpus now uses actual published records
instead of filling in timing fields from the native engine context.

The caller can submit a publication result with its main/final record and its
active record prefix to `sensor_submission::submit`. This composes the exact
copy policy with pending-batch replacement. `linear_controls` extracts the native
frame-length, DCG, analogue/digital gain and integration codes for the recovered
`sensor::program_linear` writer. These helpers do not open a device or perform
I/O themselves. A SOF callback can use that writer with an explicit backend.

[Submission comparison](sensor-submission-equivalence.json) passes on host and
ARM with zero mismatches. It runs the actual native setter and `handle_sof` on the same sensor context across 12 sequences,
96 submissions and 64 SOFs. It compares every queued exposure byte and first-entry
marker, pending order after dequeue, current snapshot, reported effective-map
entries and sensor-control traces/status. The actual native linear writer runs
in a separate isolated emulator with descriptor/ioctl callbacks, including
injected failures. As in the native scheduler, a failed writer can still update
the reported effective map; that map must not be treated as proof of physical
application. The native input-count reset and DPCC side-payload copy are also
asserted; DPCC serialization/execution is outside the Rust submission payload API.

Pool allocation, smart-pointer lifetime, C++ list links/map slots, locks, delete,
DPCC execution and logs remain modeled boundaries. Native copy/removal/append,
SOF and sensor-writer bodies execute. Rust has an explicit 32-entry pending
capacity and rejects oversized batches before mutation; native partial mutations
on allocation failure are not emulated. Startup immediate programming, custom
I2C/test modes, split gain/DCG, full native ownership, live SOF coordination,
ISP gain programming and physical latency qualification remain unfinished.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/sensor-submission.py --arm
```

## Persistent AE runtime with scheduler-produced association

`ae_runtime::Runtime` now owns both `ae_session::Session` and the ordinary
`sensor_scheduler::Scheduler`. `step_statistics` obtains effective exposures
from that scheduler's current map, runs raw translation and AE, and submits the
resulting publication batch back into the same scheduler. `on_sof` dequeues a
pending exposure and calls `sensor::program_linear` through an explicit backend.
The runtime returns both native scheduling status and the backend's original
error. It preserves native reported-map updates after write failures; callers
must not interpret those entries as verified physical application.

This removes the manually supplied per-frame exposure maps from the combined
fixture. `Session::scheduling_delays` binds the actual IQ time/gain/DCG delay
fields through the recovered delay policy. Unsupported split combinations are
rejected by the ordinary scheduler. The corpus exercises declared time/gain
delays zero, one and two, plus smoothing enabled/disabled; these remain calibration
inputs rather than measured sensor latencies.

Construction takes an explicit initial effective exposure after creating the
prepared AE session. It does **not** program the sensor at startup. The event
owner must have initialized the sensor and must order SOF/statistics callbacks;
there is no implicit thread, device discovery or live capture in this module.
Complete parameter snapshots remain caller-owned and selected by recorded ID.
Controller or submission errors can leave partial state and require discarding
the runtime. Missing measurements submit no new batch.

[Runtime comparison](ae-runtime-equivalence.json) passes on host and ARM with
zero mismatches. It connects the actual native
stages across independent emulator contexts: raw statistics translation, native
effective-exposure lookup, complete SDK AE wrappers, exposure submission,
`handle_sof` and the native linear sensor writer. The records submitted by AE
become the native sensor queue; only actual native SOF calls create subsequent
map entries. Those map entries feed the next statistics association. Explicit
byte exchange represents recovered object interfaces; full C++ ownership and
concurrency are not emulated.

Four persistent sequences cover 139 events: 56 valid statistics frames, four
invalid measurements, four missing parameter IDs and 75 SOFs. They produce
53 attempted writes, including two injected failures, and exercise exact/fallback
exposure lookup, missed/duplicate SOFs and queue draining after statistics stop.
After every event the test compares listed AE/preprocessing/publication state,
pending batches and markers, current exposure, the complete reported effective
map, control traces and status. Synthetic raw scenes vary independently of the
exposure, so this demonstrates event-loop/data-flow equivalence, not optical
closed-loop convergence.

The numerical/native components retain their documented boundaries: translator
object access/run gating, C++ ownership and containers, descriptor/ioctl callbacks,
DPCC and logging. The runtime is fixed-rate ordinary linear/source-1; startup
immediate sensor programming, live event collection, parameter accumulation,
ISP digital-gain updates, timing reconfiguration, AWB and physical latency
qualification remain unfinished. No hardware has been changed by this test.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/ae-runtime.py --arm
```

### ISP digital-gain converter boundary

`isp32::apply_exposure_digital_gain` reconstructs the pinned
`Isp32Params::convertAiqExpIspDgainToIsp32Params` (ELF `0x2d860`).
The converter scales the three bank-0 AWB register groups from the immutable
unscaled AWB cache; bank 1 stays untouched. The multiplication rounds to f32
before promotion to f64, addition of 0.5, truncation and saturation at 65535.
It sets only AWB's configuration-update bit, preserving both enable masks.

Finite linear gains at or below unity leave the entire parameter buffer alone;
HDR clamps each of its three gains to at least unity and leaves the buffer alone
when all three are unity. Nonfinite inputs are rejected atomically by the Rust
API. In particular, applying gain 1 to a reused, previously boosted buffer does
**not** restore the unscaled gains. Caller buffer restoration and ordering with
AWB updates must be recovered before connecting this converter to the runtime.

The numeric differential corpus includes 1,000 native converter calls across
linear and both nonzero working modes, signed virtual-base offsets -16/0/32,
negative/subunity/unity/next-after-unity gains, full-range cached u16 gains and
maximum finite f32 gains. It checks parameter preservation outside the gain
words and configuration mask, and preservation of the complete converter
context. Host and ARM Rust replay match the original instructions exactly.
This is converter evidence, not yet proof of live ISP update timing.

### Ordered white-balance and exposure gain results

`isp32::apply_gain_results` composes optional white-balance and exposure results
in that order, preserving both the output buffer and the independent unscaled
WB cache across calls. Both inputs are validated before either output changes.
It deliberately leaves result inclusion, frame IDs and buffer reuse to callers.

Ghidra traces establish the ordering: `CamHwIsp20::setIspConfig` (ELF `0x2a944`)
gets effective sensor exposure for the result-list frame and appends that result
to the list. `Isp20Params::merge_isp_results` (ELF `0x3178c`) walks the list in
order. `Isp32Params::convert3aResultsToIspCfg` (ELF `0x304c4`) case 4 invokes the
WB converter with update=true; case 0 invokes the exposure converter using the
sensor's effective exposure record. Thus a WB result in that list precedes the
appended exposure scaling. The merge function itself does not restore a base
AWB record before conversion.

The native AWB result publisher (ELF `0x5ce20`) uses update/synchronization flags
and can copy the last WB result into a new parameter item. The manager gating described below
shows that an item is not unconditionally forwarded; this does not prove
that WB restoration happens every frame. We retain the converter's literal
unity no-op behavior rather than invent a restoration policy.

`isp-gain-results.py` executes the original two converters in six persistent
sequences (60 events), covering both WB positions, all three working modes,
changed WB, repeated exposure boosts, unity without WB, WB followed by unity,
subunity requests, WB-only and empty batches. It compares all 11,145 parameter
bytes and the 32-byte cache after every event against host and ARM Rust.
The sequence demonstrates both nonaccumulating boosts from the cache and the
need for an explicit WB result to reset a previously boosted output.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/isp-gain-results.py --arm
```

### AWB publication and manager inclusion

`awb_publication::publish` recovers `RkAiqAwbHandleInt::genIspResult` (ELF
`0x5ce20`) for the ordinary pair of allocated gain/configuration items. It owns
20-byte WB-gain and 1,204-byte measurement-configuration payloads, their frame,
synchronization and update fields, independent latest-result caches, and the
two publisher synchronization IDs. It does not calculate AWB gains.

A fresh controller result assigns the current frame as the item's and
publisher's synchronization ID, marks the item updated, stores it as latest,
and clears the controller change flag. Without a fresh result, the publisher
either clears the item's update flag when synchronization matches or copies
the latest payload into an older item and marks it updated. If the latest item
is absent, it still assigns the synchronization ID but clears the update flag.
Initial publication gives items frame 0 while retaining the input frame for
synchronization. Bypass skips the complete operation only for algorithm ID 0.

One unusual native detail is preserved and tested: gain freshness compares the
publisher's gain synchronization ID against the **configuration item's** sync
field, rather than the gain item's field. The gain and configuration IDs can
therefore differ. The Rust implementation does not silently correct that
cross-item comparison.

Ghidra's `RkAiqManager::applyAnalyzerResult` (ELF `0x8e108`) shows the subsequent
manager gate: gain (FullParams offset `0x40`, result type 4) and configuration
(offset `0x38`, type 3) are included only when their item is present and either
its update flag is set or publication is forced. Equality between the full
parameter frame ID and the manager's field at `0x9c` also forces publication.
When included, the manager assigns the full-parameter frame to the proxy and
clears the payload's update flag. Thus an unchanged WB gain is not an automatic
per-frame restoration operation. This manager behavior is currently static
binary evidence; its list dispatch is not part of the publisher oracle.

`awb-publication.py` executes the original complete publisher in 256 cases,
covering both change flags, independent missing/present latest caches, equal
and unequal sync IDs, mismatched gain-item IDs, initial mode, bypass with
algorithm IDs 0/1, and frames 0/12/UINT32_MAX. It compares complete payloads,
latest payloads and all typed output fields against host and ARM Rust.
Smart-pointer assignment is adapted to explicit pointer-pair copying; logging
is intercepted. The numerical AWB controller, reference-count lifetime behavior,
parameter-pool reuse and live ISP submission remain unfinished.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/awb-publication.py --arm
```

### Single-ISP effective metadata

`isp_effective::copy_metadata` reconstructs the ordinary single-ISP copy path in
`CamHwIsp32::updateEffParams` (ELF `0x39700`). An existing effective-map record
receives the converter's 1,938-byte AE cache at `0xae2c`, 44-byte black-level
cache at `0xb5be`, and **unscaled** 32-byte WB cache at `0xb5ea`. If a latest AWB
measurement configuration exists, its 1,204-byte payload is copied to `0xb60c`;
otherwise those destination bytes stay unchanged. The two bytes at `0xb60a`
and all other fields are preserved.

These are metadata caches, distinct from the optionally scaled register output
in the queued ISP parameter buffer. The native routine obtains the frame from
that buffer, looks up/creates an effective-map item, and makes these copies.
The Rust helper takes an existing record explicitly; it does not yet implement
map allocation, retention, lookup, or frame association. Native split-ISP mode
also accumulates selected register snapshots using module-update masks and
prior effective records; that separate branch is not represented by this helper.

`isp-effective.py` executes the original routine with its single-ISP flag
explicitly selected. Sixteen cases vary all four caches, presence of the AWB
configuration, and frames 0/1/31/UINT32_MAX. Host and ARM Rust match the entire
47,808-byte effective record, including every preserved byte. Adapters supply
map slots, previous-record lookup failure, dynamic casts and locks; they do not
replace the native copy instructions. No queued parameter buffer restoration
occurs in this path, so it does not resolve the outstanding parameter-pool reuse
question.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/isp-effective.py --arm
```

### Runtime ISP gain association

`ae_runtime::Runtime::apply_isp_gain_results` now joins the recovered ISP gain
conversion to the same scheduler-generated effective-exposure map used for AE
statistics association. It selects exposure by the ISP batch's requested frame,
including native exact/fallback and UINT32_MAX-to-frame-0 lookup semantics,
reads ISP digital gain from that selected record, then merges optional WB and
exposure gain results in native order. It returns the selected exposure frame
and exact/fallback classification. It does not use the most recent proposed AE
exposure, which can differ from the exposure scheduled for that frame.

The caller supplies the existing parameter buffer and unscaled WB cache. Batch
mask reset, frame assignment, WB result inclusion, parameter-pool ownership and
actual driver submission remain caller responsibilities. Invalid gain inputs
leave the buffer and cache unchanged through the checked converter. This method
does not change controller or sensor scheduling state.

The persistent native/Rust runtime oracle has been extended from 139 to **211
events across four sequences**, retaining the statistics/submission/SOF checks
and adding **72 ISP gain batches**. Fifty-three select exact effective exposures
and 19 select native fallbacks; nine batches use gains above unity. One sequence
explicitly seeds the initial effective sensor record with ISP gain 2 to exercise
boosted-to-unity transitions independently of controller proposals. Optional WB
results occur every third frame, and UINT32_MAX requests exercise normalized
lookup. Before each batch the fixture clears the three header masks, matching
the native batch boundary; the remaining parameter payload is reused.

Independent native converter contexts receive the actual SOF-produced effective
records and execute the original WB and exposure converter bodies. Complete
11,145-byte output buffers and 32-byte caches, selected frame IDs, controller
snapshots and sensor maps match host and ARM Rust after each event. Synthetic
scenes remain independent of exposure, and result-list inclusion is explicit
fixture input. This proves the joined data flow, not optical convergence, WB
controller behavior, full setIspConfig execution, or live ISP submission.

### Capture-worker AE event transport

The first-frame capture implementation now has an internal observed path that
feeds a bounded `SyncSender<CameraAeEvent>` from its existing raw and statistics
workers. SOF events contain the parsed driver frame ID and nanosecond timestamp;
statistics events own a complete copied payload. The statistics worker requeues
its driver buffer before emission, so an event consumer cannot retain mapped
capture-buffer memory. The raw bridge continues its normal SOF timestamp cache
and raw readback after emitting the event.

Emission is nonblocking. A full or disconnected channel fails the emitting
worker instead of silently dropping input or blocking the raw/statistics queue.
This is transport policy for the Rust adapter, not a recovered vendor scheduling
policy. Events preserve channel arrival order; cross-worker arrival order is
not proof of sensor/ISP chronology. The event owner must still associate frame
IDs and handle statistics arriving before a corresponding SOF.

The four ARM startup scenarios now run this observed capture path and check
SOF timestamps plus every emitted statistics payload and frame/parameter ID.
The number of received statistics events equals the worker's captured count.
The same ARM suite exercises channel overflow and receiver disconnection as
explicit errors. Device syscalls and mappings remain simulated; these tests
verify actual worker orchestration and owned message transport, not camera
pixels or physical exposure timing.

The existing CLI still selects the fixed initial-exposure path. The observed
entry point is internal; it does not yet create the continuous AE event owner,
issue automatic sensor writes, or submit dynamic parameters during capture.

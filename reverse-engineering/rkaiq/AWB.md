# AWB measurement configuration

`isp_awb_measurement::Measurement::apply` reconstructs the pinned library's `RkCam::Isp32Params::convertAiqAwbToIsp32Params` at ELF `0x2b71c` (Ghidra `0x3b71c`). It converts an existing SDK v32 AWB measurement configuration into the kernel ISP32 record. It does not select white-balance gains, derive calibrated detection regions, or implement the AWB algorithm.

The input is the exact 1,204-byte little-endian `rk_aiq_awb_stat_cfg_v32_t` value record. `camera:rust:layout` extracts its public SDK declarations and compiles ARM C assertions independently of Rust. Header SHA pins live in `artifacts.json`. The packed kernel AWB block is 807 bytes at `0xf4` of the 11,145-byte full parameter record; its final eight bytes hold the black-level values.

| SDK input group | Byte offset | Conversion |
| --- | --- | --- |
| Enables, source and measurement controls | `0x0`–`0x3e` | Copy/narrow controls; special source selector routing |
| Main window, channel limits, inverse pregains | `0x40`–`0x5e` | Reorder into kernel fields |
| Overexposure value | `0x60` | Use low 16 bits for both threshold and nonzero enable check |
| RGB-to-YUV transform | `0x64` | Reorder matrix/offset coefficients |
| Four 3D YUV regions | `0x7c` | Curves, points, vectors and distance controls |
| Four UV regions | `0xfc` | Coordinates and 32-bit inverse slopes |
| RGB-to-XY transform | `0x18c` | Weights and rotation coefficients |
| Four XY regions | `0x1a4` | Normal and special bounds, narrowed to 16 bits |
| Four additional pixel windows | `0x264` | Convert offsets/sizes into offsets/end coordinates |
| Seven exclusion regions | `0x284` | Pack flags, narrow bounds and inclusion weights |
| Nine-point luma-weight curve | `0x348` | Copy coordinates and weights |
| Histogram region type | `0x35c` | Narrow enum to byte |
| 225 grid weights | `0x360` | Copy complete grid |
| Block-statistics controls | `0x444`–`0x44c` | Narrow enum selectors and copy enable |

`update=false` preserves the complete output. On update, `awbEnable=true` ORs bit 22 into all three module masks; `awbEnable=false` preserves those masks but still writes configuration. It does not disable the module by clearing a bit.

Source mode 3 selects the BNR path. Mode 4 selects the DRC path and preserves the previous BNR selector byte. Other modes clear both path flags and copy the source selector. This stale-byte behavior is retained because the native instructions do it.

The additional-window endpoint additions wrap at 16 bits. Exclusion flags use `excludeEnable[0] + 2*excludeEnable[1]`; measurement-enable flags exist in the kernel mapping for only the first four regions. Wide integer fields narrow to their low bytes without saturation. The native converter ignores write-to-DDR input controls, the small XY bounds and software metadata, and leaves kernel fields without assignments untouched. The Rust copy table names its kernel destination fields so offsets remain reviewable.

`mise run camera:rust:awb-measurement` executes 2,000 deterministic cases against the original ARM library under Unicorn. It compares all three masks and the entire AWB block, and checks preservation of unrelated output, input and context bytes. Cases cover enable/update combinations, source modes 0–5/255, low-16-bit overexposure boundaries, zero/full/random patterns, seven exclusion regions, wrapping windows and every grid weight. [Reference report](awb-measurement-equivalence.json).

This proves the tested converter behavior, not valid sensor geometry, calibrated detection, an automatic white-balance loop, complete initial ISP parameters or successful hardware application. The existing AWB statistics decoder and gain writer remain separate pieces that need algorithm/controller integration.

## Gain calculation and temporal damping

`awb_gain` reconstructs six original gain-stage functions. The channel order is R, Gr, Gb, B.

| Native function | ELF entry | Rust API |
| --- | --- | --- |
| `AwbGainCalbyRgainBgain` | `0xca7cc` | `ratios` |
| `AwbCalGainForDiffIllumAndDiffXYType2` | `0xc99d8` | `statistics_gain` |
| `AwbGainNormal` | `0xca030` | `normalize` |
| `AwbGainMixture` | `0xca080` | `mixture` |
| `AwbCalDampFactor` | `0xc9f2c` | `DampingParameters::adapt` |
| `AwbCalDampGain` | `0xca0e0` | `damp` |

The statistics helper consumes the algorithm's signed 64-bit `WpNo`, `RgainValue` and `BgainValue` record. These are accumulated gain statistics for a selected illumination/XY region, **not the raw sensor's R/G/B sums**. For a nonzero weighted count it rounds each integer to f32, computes red/count and blue/count and sets both greens to one. A zero count produces four zero gains. The wrapper normalizes these gains and computes `(WpNo + 512) >> 10`, retaining native signed wrapping and arithmetic-shift behavior. Public SDK declarations independently verify the 24-byte, eight-byte-aligned by-value record and the 20-byte gain-result record.

Normalization searches for a divisor starting at **5.0**, replacing it with each smaller/equal channel. It divides only when the resulting value is greater than the double constant `1e-5`. All gains above five are therefore divided by five, rather than by their minimum. Zero, negative and sufficiently small minima leave the record unchanged. Mixture computes `first*weight + second*(1-weight)` with the native rounded product/FMA ordering, then normalizes.

The base damping coefficient moves down by one configured step when variance is greater than its threshold, or up by one step otherwise, followed by the original ordered lower/upper comparisons. This leaf consumes an already computed variance; the recovered brightness-history estimator is described below. The surrounding calibrated policy is still separate.

Temporal damping first checks the **previous red channel alone** against the double constant `1e-5`. Below it, the new gains remain unchanged and both coefficient fields reset to zero. Otherwise it finds the maximum absolute channel difference and scales the base coefficient using this native curve:

| Maximum channel difference | Multiplier |
| --- | --- |
| 0.01 or below | 0 |
| 0.05 | 0.5 |
| 0.10 | 0.7 |
| 0.15 | 0.9 |
| 0.30 or above | 1 |

Intermediate values use the recovered `interpolate` function. The threshold comparison uses double `0.3`, while the final table knot is f32 `0.3`. The effective coefficient weights the **previous gains**: each output is an FMA of previous×effective into the separately rounded candidate×(1−effective). This routine does not normalize again and does not advance the previous-frame record. The native outer caller performs that history copy later.

`mise run camera:rust:awb-gain` checks **6,000 cases**, 1,000 per original function, including all resulting f32 bits, signed count rounding and preservation of unrelated temporal-context bytes. The corpus covers the normalization divisor cap, zero count, signed i64 extrema, integer-to-float boundaries, curve knots, invalid previous-gain sentinel and coefficient clamps. The reference executes the original SDK `libgcc_s.so.1`'s `__aeabi_l2f` instructions in a separate Unicorn instance; it does not substitute a Python float conversion. Its archive/member hashes are pinned, and no imported calls are reached inside that runtime helper. The distributed Rust tools do not include or link this vendor runtime. [Reference report](awb-gain-equivalence.json).

The native call path `AwbCalAwbGain → AwbCalGainByWbMode` places these stages among illumination probabilities, spatial/temporal histories, clipping, gain adjustments, convergence and color-temperature calculations. The probability and weighted-output stages are reconstructed below; the other surrounding stages, calibration loading and publication into the live service remain unfinished. These functions must not be connected directly to raw RGB averages as a substitute for the original AWB algorithm.

## Illumination probabilities and weighted gain

`awb_probability` now reconstructs the probability stages named above, followed by one native weighted-output path. It accepts explicit selected-XY white-point counts and per-illumination gains, calibrated reference gains/light kinds/prior curves, current gains, brightness and thresholds. It does not construct those inputs from raw ISP statistics or load their calibration yet.

| Native function | ELF entry | Behavior |
| --- | --- | --- |
| `AwbCalWpNoProbablity` | `0xc62a8` | Filter selected-region counts, calculate count probabilities and retained count |
| `AwbCalDisProbablity` | `0xc5f18` | Distance probabilities in R/Gr and B/Gb gain space |
| `AwbCalLVProbablity` | `0xc60d8` | Brightness probabilities by light kind |
| `AwbCalLgtlWeit` | `0xc6458` | Interpolated per-light prior weights |
| `AwbCalTotalProbablity` | `0xc6588` | Call the three preceding stages and combine their results with count probabilities |
| `AwbCalGainTotal` | `0xc696c` | Weighted per-channel accumulation and normalization |

`calculate` runs the count filter followed by the complete native probability sequence; `weighted_gain` consumes its output and the supplied per-illumination gains. This is the original combination of these functions, not the full native outer mode-selection/controller path.

The count filter excludes a light only when its share of the original total is at or below the relative threshold **and** its count is at or below the unsigned-truncated absolute threshold. Remaining counts are summed at 64 bits and converted to f32 for division; only the low 32 bits of the retained sum are published into the native context. A probability sum at or below double `1e-5` falls back to uniform count probabilities. The Rust value API uses explicit counts instead of the native context's selected-XY offset/stride and temporary allocation.

Distance weighting uses squared distance between reference/current R/Gr and B/Gb ratios, with an FMA for the two squared terms. It assigns one below the near threshold, a linear decline between near/far thresholds, and zero at/above the far threshold, then normalizes. A current gain product at/below double `1e-5`, frame zero or `FASTAWBACT` mode produces uniform distance probabilities.

Brightness weighting uses all four native unsigned thresholds. Below either of the first two it uses 0.5; beyond the fourth it uses f32 0.99; between the third and fourth it rises from 0.5 using **f32 differences followed by double arithmetic and a final f32 conversion**. Light kinds 1, 2 and 3 select `1−ramp`, `max(ramp,1−ramp)` and `ramp`. An unknown kind preserves its old luma field and does not contribute to the normalization denominator, although its field is subsequently divided by that denominator. The value API therefore accepts the previous per-light luma field explicitly. It does not silently clamp or replace this behavior. Fast mode assigns uniform brightness probabilities.

Per-light prior curves use the recovered native interpolation function. A prior sum strictly greater than double `1e-5` is normalized. Otherwise the original computes **integer `1 / light_count`**: this produces zero for more than one light. Fast mode assigns prior weights of one. The combined probability is the sequential product of brightness, distance, count probability and prior. At/below the epsilon it falls back to normalized count probabilities, then uniform probabilities if their sum is also too small.

Finally, weighted-gain accumulation starts four channels at zero, traverses lights in native order, uses an FMA for each probability×gain addition, and calls the recovered normalization routine. No arbitrary gray-world estimate replaces the selected-region or per-illumination stages.

`mise run camera:rust:awb-probability` compares **2,000 complete original-ARM sequences**. The original total-probability routine calls its own original subroutines without algorithm stubs, followed by the original gain accumulator and normalizer. Every sequence compares all five f32 fields per light, the retained-count low word and all four final gain bits. It also verifies input/calibration preservation and every unrelated context/result byte. Cases cover 1–8 and 255 lights, four XY record selections, fast/frame-zero/invalid-gain fallbacks, rejected/all-zero counts, unsigned thresholds, near/far boundaries, prior epsilon/fallbacks, unknown light kinds and brightness rounding above `2^24`.

The reference executes the pinned GCC runtime's signed integer-to-float conversion and integer division instructions. Bounded `strcmp` semantics and successful single `malloc`/`free` are explicit standard-library boundaries; allocation failures and arbitrary invalid native pointers are outside the Rust value API. The shared `awb_reference.py` executor is also used by the earlier 6,000-case gain suite, which is rerun after its refactor. [Probability reference report](awb-probability-equivalence.json).

The checked API requires 1–255 lights, equal output lengths, finite inputs, nonempty increasing prior tables and nonzero reference green denominators. Errors during calculation can leave intermediate output fields changed; this API does not promise atomic mutation on invalid arithmetic inputs. These tests establish arithmetic/state equivalence in the stated corpus, not physical calibration or a functioning independent camera service. The SDK measurement preparation below supplies selected counts/gains. Calibration loading, illumination classification, spatial/temporal policy, gain adjustments, convergence, full calibrated initialization and live publication remain unfinished.

## Measurement preparation and time-share state

`awb_preparation::prepare` reconstructs complete `PrepareMeasureResult`, ELF `0xc3180` (Ghidra `0xd3180`), including its call to `IsMeasureResultStable4`, ELF `0xc2f90`. The API owns no vendor pointers: mutable light records, seen flags, totals, grid cells and other caches are explicit borrowed buffers/typed state. `Frame` borrows the exact **7,680-byte SDK full-V32 record**. The driver-to-SDK producer is documented in the development section below; live frame/configuration association remains unfinished.

The pinned SDK declarations are compiled independently for ARM in `camera:rust:layout`. They verify the full frame size and these source offsets:

| SDK field | Offset |
| --- | --- |
| Four light results, each containing two weighted-statistics records | `0x0` |
| Four second white-point counts | `0xc0` |
| 225 block results | `0xd0` |
| Four exclusion-region results | `0x1cf0` |
| Eight histogram bins | `0x1d50` |
| 108-byte measurement-effect metadata | `0x1d70` |
| Global block RGB sum | `0x1de0` |

Effect metadata supplies the grid mode, up to four physical-light-to-cache mappings, signed time-share group, 64-byte configuration signature and R/Gr/Gb/B pregains. The checked API supports 1–255 total cached lights and 1–4 time-share groups, bounded terminated signatures, valid group indices and the special **fast group −1**. Finite curves/pregains and nonzero current red/blue pregains are required. Invalid arithmetic may leave intermediate state changed; this API does not promise rollback.

The stability helper calculates `[G/R, 1, 1, G/B]` from the signed global sums when R and B are positive, or four zeros otherwise. It compares only red/blue differences against every group's previous gains and records a stability bit mask. Any unstable group sets `update=true`; an inherited true flag is retained. When update is true it stores the new gains in the current history slot, mapping group −1 to slot zero. If update remains false, the outer preparation routine returns after this gate and preserves all other caches.

On update, a changed configuration signature clears the seen-light flags and all four signature slots. Each physical light's two SDK weighted-statistics records are converted by the previously recovered gain helper and written to its mapped **172-byte light cache**; their rounded counts narrow to the native low 32 bits. The second count and four pregains are cached too. Unwritten cache fields retain their previous bytes. An out-of-range nonnegative mapped light index clears seen flags and stops that mapping loop, preserving earlier writes exactly as native code does.

Fast mode uses the low byte of the configured fast-light count, stores its signature in slot zero and declares the result complete. Normal mode requires matching configuration signatures across groups and every seen-light flag. Incomplete measurements still update grid/exclusion/histogram caches; they do not perform the complete-set count summation/pregain adjustment.

For a complete set, preparation sums the two region counts with u32 wrapping and adjusts cached red/blue gains by `gain × stored_pregain / current_pregain`, preserving separate f32 multiply/divide rounding. It copies the current pregains into the prior-gain record. Native clearing uses only `active_light_count` total slots even though it adds two region totals: **with one active light, the prior second total is retained and incremented**. This behavior is preserved.

Grid mode zero converts each block's signed 64-bit RGB sums using the **signed low 32 bits** of its count as divisor, then multiplies by `1/256`. A zero low count preserves the old cell; the high count word is ignored by this native path. Other modes clear grid-valid flags without changing cell values.

Preparation clears seven 52-byte exclusion records and fills the first four from the SDK data. Their gain divisor uses the native wrapping 64-bit count shifted left by eight. Regions with configured kind 3 contribute interpolated weights to an FMA accumulation of their unsigned low-word counts. Above double `1e-5`, their gains are combined with the original product/division/FMA order and normalized; the aggregate count uses native unsigned float conversion. The remaining cleared fields stay zero.

The current group's histogram cache is replaced, and a complete set rebuilds the eight-bin aggregate from all configured groups with u32 wrapping. **Fast group −1 writes the incoming histogram into the aggregate immediately before native code clears/rebuilds it from the existing group caches**, so that incoming histogram is not retained there. The Rust API preserves this aliasing outcome without exposing an out-of-bounds pointer.

`mise run camera:rust:awb-preparation` compares **500 sequences and 1,144 frames**, using persistent one-/two-/four-frame caches. **124 sequences include fast group −1.** The native original preparation routine calls its own original stability, gain-conversion, normalization and interpolation code. The reference checks every represented state byte, every unrelated context/strategy byte, all input/calibration bytes, complete and incomplete sets, inherited/stability update gates, signature changes, invalid light mappings, one-light total behavior, zero grid counts, exclusion mixes and histogram wrapping. SDK GCC integer conversion executes as original ARM instructions. Successful bounded allocation/free, string copying/comparison and standard memory operations are explicit harness boundaries; vendor logging/debug formatting is outside the value API. [Reference report](awb-preparation-equivalence.json).

The caller resets its incoming update flag before each test frame; the surrounding `AwbPreProcV32` brightness/variance/scheduling policy is not reconstructed by this suite. Calibration construction, per-illumination/spatial strategy, convergence and live publication remain unfinished. Numeric replay still does not prove independent camera startup or image quality.

## Driver-to-SDK translation in development

`awb_translation::translate` implements the full single-ISP RV1106 value path of `translateAwbStats`, ELF `0x8818c`. It joins the existing driver decoder to the 7,680-byte SDK frame consumed by preparation: configured light sums and second counts, 225 block records, exclusion results, expanded histogram, global RGB sums, debug descriptor and measurement-effect metadata. Global `WpNo` remains zero, matching native code. Inactive light entries and the three effect-padding bytes remain untouched.

`Configuration::from_measurement` reads the selected 1,204-byte AWB measurement record, including its software-only group, mappings, signature and pregain fields. It preserves opaque float/signature bit patterns during translation. This is an explicit supplied snapshot, as in the original translator; the API does not assume it has been applied to the incoming driver's `params_id`. Queue/configuration correlation remains integration work.

Missing input preserves all destination fields. Input without the AWB-valid bit clears only the validity flag. Successful translation marks frame information valid, copies the frame ID into both frame/proxy fields and obtains the debug descriptor only for native debug type 2. `Outcome::native_status` returns the original zero/one status while retaining the bypass reason in the Rust enum.

`mise run camera:rust:awb-translation` compares all SDK bytes and conditional fields against 1,000 native executions, including both driver payload lengths, 0–4 physical lights, missing/invalid input and debug modes. It checks preservation of unrelated native object/proxy bytes, the configuration/context, source statistics and retained-owner reference count. Object access and the single-ISP predicate are controlled boundaries; vendor logging is discarded. [Reference report](awb-translation-equivalence.json).

This development work follows kit 0.0.28 and is not a new camera-test release. The next release is prioritized around the runnable camera path described in [ISP.md](ISP.md#current-implementation-priority), rather than another standalone-routine kit. Live startup, calibrated initialization, configuration association and the surrounding controller remain unfinished.


## Initial gain application position — corrected

The first-frame checkpoint originally placed the fixed D50 gains in Gain0.
Hardware comparison showed a purple black-level pedestal: at 3 ms/1× in the
dark scene, average NV12 chroma was approximately U=149.45, V=149.44 (neutral
is 128). Changing only the 32-byte AWB gain block to Gain1 gave U=129.05,
V=128.83; a unity-gain control gave U=128.63, V=128.63. The fresh corrected
startup capture gave U=127.68, V=129.35. This isolates gain placement as the
cause of the observed dark purple bias; it does not establish full color
accuracy, CCM tuning or automatic WB.
[Hardware comparison](awb-position-hardware-validation.json).

Ghidra `AwbPrepareV32` (ELF 0xc3a4c) publishes context field 0x3644 as
`working_mode == 0`. The pinned AWB header defines Gain0=0 and Gain1=1;
`awbProcessing` copies that field to the output `applyPosition`. Executing the
native prepare publication checkpoint confirms mode zero selects **Gain1**.
The checked helper `isp32::awb_prepare_position` now supplies that default to
linear startup; the initial report records `whiteBalanceApplyPosition: Gain1`.
[Position equivalence report](awb-prepare-position-equivalence.json).

Ten host/ARM cases check the position store for linear and other mode values.
Calibration update is an explicit success boundary and a controlled
preconfigured context bypasses prior geometry/bit-depth setup. This is not
full prepare equivalence or the later reconfiguration policy. The existing
native gain serializer already supported both positions and is unchanged.

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python reverse-engineering/rkaiq/scripts/awb-prepare-position.py --arm
```

Parameter assembly/mask checks, malformed-profile guards, static ARM preflight,
full startup simulations, library/no-std checks and primary AE translation
comparisons pass after the correction. Development base parameter SHA-256 is
`b5e031ec216f3a007d6b9b6c21bcd6b726d7edda0a6b98913016b66fe91ef2cd`;
measurement-enabled parameter SHA-256 is
`2ffab69fcf67ac36ea58c446352acbcc6fcdb51079ae0afdf0377adce29cdebc`.
Frozen prior kits retain their original parameters and limitations. Automatic
AWB, illuminated-scene color testing and complete result policy remain open.

## Standard measurement-history stability gate

`awb_stability::State::measure` reconstructs `IsMeasureResultStable4` (ELF
`0xc2f90`), called by standard `AwbPreProcV32` through `PrepareMeasureResult`.
This is separate from the exported `awbProcessing` at ELF `0x10f848`, whose
context and calls are the surround-view implementation; that symbol must not
be assumed to be the ordinary single-camera controller entry point.

The gate consumes signed 64-bit block red/green/blue sums. If red and blue are
both positive, it forms `[green/red, 1, 1, green/blue]`, rounding each i64 to f32
before division. Otherwise it uses four zeros. For each selected history entry,
red and blue differences must both be at most the configured threshold to set
its bit in the match mask. Green history fields do not participate in comparison.
The match mask is reset each call. Any mismatch sets the update request, while
all matches **retain** the incoming request rather than clearing it. An active
request stores the new four-channel ratios in the metadata-selected slot;
slot -1 aliases zero. An inactive request leaves all history records untouched.

The typed Rust boundary provides eight storage slots, accepts comparison count
0..8 and slot -1..7, and rejects nonfinite thresholds/history and out-of-storage
requests before mutation. These are checked storage bounds, not a claim that
every calibration time-share mode is supported. The outer preprocessor seeds
the incoming request from its own context flags and policies; the gate alone
does not decide whether the full AWB algorithm runs or gains are published.

`mise run camera:rust:awb-stability` checks 1,024 cases on host and ARM Rust
against original ARM instructions. Cases vary all counts/slots, incoming request,
exact and changed history, threshold equality/negative thresholds, zero/negative
sums and integer rounding boundaries through signed i64 maxima. It compares the
complete eight-entry history as exact f32 bits, the mask and update flag, and
checks preservation of all unrelated context bytes. The original libgcc
`__aeabi_l2f` instructions execute for integer conversion (1,935 calls), and
logging is an explicit intercepted boundary. [Reference report](awb-stability-equivalence.json).

Development is now `0.0.31-dev`; the previously delivered `0.0.30-dev` hardware
kit remains frozen. The ordinary AWB controller still needs calibrated region
selection, history/variance policy, classification and publication integration.
The automatic capture command continues to use fixed calibrated white balance.

## Brightness history and relative variance

`awb_luma_history::History` reconstructs `UpdateLvValueList` (ELF `0xc9e54`)
and `CalculateVarianceLuma` (ELF `0xc9ea4`), called together by standard
`AwbPreProcV32` before its stability/update decision and gain damping.

A nonzero target length appends while the current list is shorter, otherwise
reuses its oldest entry at the tail. Lowering the target therefore does not
truncate existing history. Target zero leaves the list alone. The update API
accepts a signed i32 brightness value, but variance reads its stored bits as
u32, preserving the native signed/unsigned distinction.

Variance first accumulates ordered u32-to-f32 values and divides by the count
for the mean. It then accumulates squared relative deviations `(value/mean-1)`
using a fused f32 multiply-add, and divides by count. Empty history returns
zero; a nonempty all-zero history yields the native ARM quiet NaN
`0x7fc00000`. The implementation preserves that result instead of manufacturing
zero variability for missing/zero brightness data. Disassembly confirms the
native `vfma.f32` instruction used for accumulation.

The pinned native list implementation corrupts a singleton list when its target
is one: the head's next pointer becomes the head while its previous pointer
still names the node, and that node points to itself. The oracle explicitly
checks those resulting pointers. The checked Rust API rejects this case, along
with negative or out-of-capacity targets, before mutation. It uses owned
const-generic bounded storage rather than reproducing C allocator/link corruption.

The native/Rust corpus covers 64 persistent sequences, 1,536 updates and 1,600
variance calculations, including changing targets, node reuse, zero/equal and
widely differing histories, signed inputs, unsigned extrema and exact NaN bits.
Three singleton/target-1 cases are redirected to a safe target for sequence
continuation; their native corruption is audited separately. Host and ARM Rust
match list order, append-versus-reuse behavior and every variance bit. Native
allocation uses an explicit 12-byte-node allocator adapter; native update and
variance instructions execute unchanged. [Reference report](awb-luma-history-equivalence.json).

This supplies the estimator needed by AWB preprocessing and existing damping,
not the complete brightness interpolation, calibrated classification or AWB
controller. The automatic capture command still holds calibrated WB fixed.

## Standard preprocessor brightness, thresholds and cadence

`awb_preprocess::State::derive` recovers the numerical prefix of standard
`AwbPreProcV32` (ELF `0xc4698`), returning a continuation decision before
metadata/history/classification processing. It synchronizes requested mode,
seeds the update request from the previous flag, and forces update when smart
running is disabled or its countdown is positive. Native mode 1 bypasses these
numerics and clears the request without reading exposure/calibration inputs.

Brightness uses the selected AE value multiplied by **1000 in f32**, then
promoted to f64 for `+0.5` before unsigned conversion; the unrounded scaled f32
is retained separately. Missing AE input uses the configured u32 fallback.
Choices 0/1 select those channels; choices >=2 select channel 0 in working mode
0 and channel 1 otherwise. An enabled, valid override replaces both brightness
forms. The prefix interpolates three smart-run thresholds at unrounded
brightness and the run interval at the rounded integer brightness.

The effective sample area follows the native operation order:
`((sample_scale * width) / block_width) * height / block_height`, each stage in
f32. Two brightness-dependent point thresholds multiply that area and divide
by **100000 in f32**, then use promoted-f64 half rounding for their u32 outputs.
Two additional region thresholds use the same scaling without integer rounding.
The Rust API accepts explicit curve data; JSON-to-SDK calibration loading is
still separate. Zero block dimensions, invalid curves and UINT32_MAX intervals
are rejected before committing the derived state.

The cadence gate continues when the frame counter is at most the interval or
is divisible by `interval+1`. Otherwise it increments the counter with u32
wrapping and skips. A continuing prefix does not increment the counter here;
that occurs later in the native metadata/gain path. The Rust decision names
`Ready`, `IntervalSkip` and `ModeBypass` describe this boundary, not a completed
AWB processing result.

`mise run camera:rust:awb-preprocess` compares 768 cases against the original
complete preprocessor using its null-metadata exit: 256 mode bypasses, 131
interval skips and 381 continuations that reach the missing-metadata branch.
Host and ARM Rust match all exact f32/rounded output words, mode/update flags,
counter behavior and unrelated context/configuration preservation. Native
interpolation executes unchanged; 322 unsigned divide/modulo calls execute
isolated pinned libgcc instructions. Logging is intercepted. Cases cover
fallback, channel/working-mode selection, overrides, signed scales, threshold
interpolation and counter/rounding boundaries. [Reference report](awb-preprocess-equivalence.json).

The non-null metadata continuation is now joined through complete measurement
preparation in the later section below. Calibrated final gain selection remains
separate; this numerical prefix alone does not enable automatic WB in capture.

## Joined preprocessing through measurement entry

`awb_environment::classify` recovers `AwbCalLV` (ELF `0xc9f68`). Its two outputs
are independent: a five-level category uses strict comparisons against four
thresholds, while an environment index scans consecutive interval boundaries.
If no interval matches, the last interval index remains selected, even for a
value below the first boundary. With no intervals, the incoming index is
preserved. The API retains the numeric categories rather than inventing semantic
names for unconfirmed enum values.

`awb_preprocess::State::derive_measurements` now joins numerical derivation,
environment classification, rolling brightness history and relative variance.
On a continuing frame it updates those fields, derives brightness stability,
and combines the existing update request with variance and two convergence
flags. Mode/interval bypasses leave metadata/history untouched. Checked failures
commit neither numerical state nor metadata/history.

The native stability flag here is **not** an ordinary `variance <= threshold`
comparison. ARM instructions implement `!(variance > threshold)`, so unordered
NaN variance is marked stable. The separate update request uses the ordered
`variance > threshold` result, the negation of both convergence flags being set,
and the previous request. Rust preserves these distinct conditions, including
the NaN produced by nonempty all-zero brightness history. This differs from
the earlier measurement-ratio history gate; both feed the remaining classifier.

`mise run camera:rust:awb-preprocess-history` runs 512 joined comparisons,
including 261 native continuations reaching `PrepareMeasureResult`. The
original preprocessor, interpolation, environment classification, list update
and FMA variance bodies execute together. Execution stops at the **first
instruction** of `PrepareMeasureResult`, before classification or gain work;
it does not substitute a classifier and claim full controller equivalence.
The oracle compares all derived numeric bits, complete list values, category
outputs, stability/update flags and preservation outside the known state fields.
Host and ARM match exactly. Cases include empty/zero history, changing history
lengths, threshold equality, out-of-range environment lookup and convergence
flag combinations. The 768-case numerical-prefix regression also still passes.
[Joined reference report](awb-preprocess-history-equivalence.json).

Native node allocation and logging remain explicit boundaries. Calibration
curves and starting histories are synthetic and supplied explicitly; full IQ
initialization, the measurement classifier and later gain/publishing stages
remain unfinished. The frozen camera kit continues using fixed calibrated WB.

## Outer preprocessing through complete measurement preparation

`awb_preprocess::State::prepare_frame` joins the new numerical/environment/luma
history prefix to the existing complete `awb_preparation::prepare` implementation.
It supplies the derived stability threshold and unrounded brightness to that
routine, shares the update flag across both representations, and preserves
mode/interval bypass behavior. Its output includes prepared time-share light
records, counts, grid, exclusions and histograms, ready for the remaining gain
strategy. Arithmetic errors inside measurement preparation retain that API's
partial-mutation semantics; discard the session after such an error.

The measurement stability implementation is now shared with `awb_stability`
instead of duplicated. The existing preparation API keeps its original checked
1–4-group boundary; the standalone gate's broader storage corpus is not used
to expand supported time-share modes implicitly.

`mise run camera:rust:awb-prepared-frame` compares **64 persistent sequences /
512 frames** against the original standard preprocessor through the return from
its full native `PrepareMeasureResult` call. All numerical prefix, environment,
brightness-list and measurement helper bodies execute natively together.
Execution stops at mapped caller PC `0xd4ae0` (ELF `0xc4ae0`), before final gain
selection, countdown changes, counter advancement and ISP reconfiguration.
The incoming frame counter is supplied explicitly each frame; its outer
lifecycle is not claimed by this test.

Host and ARM Rust compare complete represented measurement-cache bytes plus
prefix flags, brightness, environment and rolling-history/variance bits. Cases
cover interval skips, one-/two-/four-group state, FASTAWBACT including group -1,
changing names/light maps, incomplete sets, zero/equal histories, grid handling,
exclusion weights and histogram state. Native strings/allocation/logging are
explicit bounded adapters, as in the earlier preparation suite. The original
500-sequence measurement-preparation regression is also retained after sharing
the stability code. [Joined reference report](awb-prepared-frame-equivalence.json).

The next gap is the caller's calibrated `AwbCalAwbGain` path and its subsequent
hardware/publication policy, followed by complete IQ initialization and live AWB
integration. The automatic-exposure kit remains fixed-WB and unchanged.

## Gain-mode XY region selection

`awb_xy_selection::State::select` now implements the beginning of
`AwbCalGainByWbMode` (ELF `0xc72b8`): Normal count filtering, Big fallback,
Exclusion proposal, rolling region-history stabilization, and white-point kind
classification. It shares the existing probability implementation's extracted
`count_probabilities` routine. Errors leave both state and output unchanged.

Recovered details matter here: Normal/Big vote ties choose Big; Exclusion must
strictly beat both. Unknown history entries receive no votes. NaN variance enters
voting through the native unsigned ARM branch, unlike the earlier brightness
stability gate. White-point kind compares the stored count words as signed i32.
If stabilization changes the proposed region to Exclusion, its aggregate count
replaces the retained count without recalculating per-light probabilities. If an
Exclusion proposal stays unchanged, the retained count remains the preceding Big
filter's count. The Rust implementation preserves this distinction.

`mise run camera:rust:awb-xy-selection` compares **768 cases**, with zero
mismatches on host and ARM. The oracle executes the original gain-mode prefix,
count-filter, history-list, stabilization and classifier bodies, stopping
immediately after native `AwbCalWPType` returns. It checks region/count/kind,
history, exact per-light probability bits, unrelated-memory preservation and
allocation balance. Inputs include full-width counts, signed thresholds,
NaN variance, ties, disabled/short/full histories and up to 255 lights.
[Reference report](awb-xy-selection-equivalence.json).

This covers the complete-measurement branch with calibration mode 1. The direct
Exclusion/calibration-mode-0 gain branch, subsequent gain strategies and complete
outer AWB integration remain unfinished. Calibration and starting state are
explicit inputs; allocation and logging use bounded adapters. The existing
2,000-case probability regression still matches native code after sharing the
count filter. These comparisons establish software behavior, not camera quality.

## Spatial calibration and statistics blend

`awb_gain::spatial` reconstructs `AwbCalGainInSpatial` (ELF `0xc66d0`) for
each illumination. Below the low brightness threshold it copies the low gain;
above the high threshold it copies the high gain. Between thresholds it blends
using the original normalized mixture. Endpoint copies are deliberately not
normalized. Thresholds compare as u32 before conversion to f32. If their f32
width is below 0.0001, the interpolation ratio is 1, including distinct large
integer thresholds which round to the same float. Reversed thresholds preserve
native branch order.

`awb_gain::spatial_statistics` reconstructs
`AwbCalGainBySpatialMulStatistics` (ELF `0xc67a8`). Its weight is the selected
calibration byte divided by 100; values above 100 extrapolate without clamping.
The native routine replaces the per-light statistics gain at result offset
`0x64`, preserves the spatial gain at `0x84`, and stores the weight at `0x98`.
The Rust value API returns the replacement statistics gain and weight explicitly.

`mise run camera:rust:awb-spatial` compares both native routines consecutively
against host and ARM Rust: **1,024 cases / 6,348 illumination results**, exact
intermediate/final gain and weight bits, and unrelated-memory preservation.
Coverage includes 0–8 and 255 lights, four calibration groups, threshold
boundaries, equal/reversed/float-collapsed thresholds, zero gains, endpoint gains
above 5, and percentages from 0 through 255. The native mixture and normalization
bodies execute without replacement.
[Reference report](awb-spatial-equivalence.json).

These are components of the high-count strategy, not its complete controller.
Calibration, brightness and measured gains are explicit inputs. Temporal gain
construction, full high/low orchestration, calibration initialization and live
AWB integration remain unfinished. The frozen fixed-WB camera kit is unchanged.

## Temporal gain sources and brightness blend

Ghidra exports of `AwbCalGainInTemporalGain2` (ELF `0xc5d3c`) and
`AwbCalGainInTemporalGain` (`0xc5d5c`) establish two different sources: the first
copies configured default gains directly, while the second averages gain-list
entries with calibration-byte weights in list order. Empty history uses the
same default. `awb_gain::temporal_history` implements the latter; callers of the
first use the configured gain directly. Weighted accumulation uses native FMA
order and divides by the signed wrapping weight sum without normalization.
Rust rejects missing weights and nonfinite results, including a nonempty list
with all zero weights. Empty history does not read unused weights.

`awb_gain::temporal_blend` reconstructs `AwbCalGainTotalMulTemp` (ELF `0xc6860`).
Its 16-point brightness curve uses u32 comparisons to select endpoints or an
interval, then f32 interpolation with an FMA. Widths below 0.001 retain the lower
percentage. It preserves native interval scanning for unordered input rather
than sorting calibration. The percentage is not clamped: each channel computes
`fma(temporal, percentage, (100 - percentage) * current) / 100`, then the complete
gain is normalized. The returned weight remains the raw percentage.

`mise run camera:rust:awb-temporal` compares **1,024 cases** on host and ARM
against each original temporal source followed by the complete original blend.
It verifies exact intermediate/final gain and weight bits and unrelated-memory
preservation. Cases cover 0–16 history entries, zero individual weights, default
copies, endpoint/equal/unordered knots, full-width brightness, float-collapsed
large knots, zero gains and percentage extrapolation.
[Reference report](awb-temporal-equivalence.json).

History insertion/eviction and complete high/low gain orchestration remain
unfinished, as do calibration loading and live AWB integration. This stage does
not change the frozen fixed-WB camera kit or establish camera image quality.

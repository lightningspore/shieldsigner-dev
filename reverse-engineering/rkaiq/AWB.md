# AWB measurement configuration

Current reconstruction includes measurement conversion/preparation, region
selection, probabilities, and high/low gain strategies including single-color
classification and confidence. These are verified value-level components;
complete calibrated outer AWB and live frame integration remain unfinished.
The sections below describe each stage and its reference-test boundary.

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

## Complete high-count gain strategy

`awb_high_gain::calculate` now joins the full value-level call chain of
`AwbCalGainWpTypeHigh` (ELF `0xc6a20`). For each illumination it copies the
selected-region gain, optionally mixes extra-region statistics, derives the
spatial gain, and blends spatial/statistical results unless the mode is
`FASTAWBACT`. It then combines illuminations using their precomputed total
probabilities, loads the configured temporal default and applies the recovered
brightness-dependent temporal blend. The native final gain is copied to both
current-gain and high-strategy-result fields; the value API returns that gain.

Extra-region weight is `extra_count / selected_count` after u32-to-f32 rounding,
capped at 1. Disabled extra mixing or zero selected count preserves the previous
extra weight, while still replacing the statistic gain with the selected gain.
FASTAWBACT similarly preserves the previous spatial weight, but still calculates
the spatial gain. The API accepts prior per-light result values so these native
preservation rules remain visible. All output is staged until every numerical
operation succeeds. A late-invalid-probability unit test checks atomic failure.
The light-order weighted accumulator is shared with `awb_probability`.

`mise run camera:rust:awb-high-gain` invokes the original high-count function
once per case and lets its full native numerical call tree return normally.
**1,024 cases / 6,866 illumination results** match host and ARM Rust exactly:
current/stored gain, temporal source and raw percentage, per-light statistics
and spatial gains, both mixture weights, and unrelated-memory preservation.
Coverage includes normal/FASTAWBACT, XY selections 0/1/3, four calibration groups,
up to 255 lights, zero/full-width counts, extra-weight clamping, preserved fields,
zero probabilities/gains and spatial/temporal boundary behavior. Only bounded
`strcmp` and logging are adapters; numerical and strategy helpers run natively.
[Reference report](awb-high-gain-equivalence.json).

This completes the high-count strategy for explicit finite calibration,
selected-region measurements and total probabilities. It does not complete the
low-count strategy, caller's high/low interpolation, postprocessing, IQ loading,
outer frame lifecycle or live AWB integration. The camera kit remains fixed-WB.

## Low-count strategy without single-color processing

`awb_low_gain::State::calculate_without_single_color` reconstructs the
single-color-disabled branches of `AwbCalGainWpTypeLow` (ELF `0xc6a90`). This
restriction is explicit in the API: the pinned SC3336 IQ enables
`singleColorProces` in `AWB_SGC_CALL_INITIAL` mode, so its enabled branch remains
required work rather than an optional improvement to this implementation.

When the retained count is sufficient (unsigned comparison), the native routine
only updates color history and preserves all gain results. Otherwise a nonempty
gain history supplies its last entry, marks previous-gain usage and updates the
temporal and low-strategy results. With no gain history, brightness selects the
configured temporal default, a spatially weighted illumination gain, or a blend
between them. The middle blend uses the native rounded product plus FMA, without
the normalization performed by `AwbGainMixture`. Only fields written by the
chosen branch change; previous-use flags and other gain caches can remain stale.
Outputs and owned history are staged until success.

The two brightness thresholds first compare as u32. Distinct large integer
thresholds can then collapse to the same f32 value; native interpolation clamps
to its first endpoint before testing span. The value API handles that case
before calling the shared interpolation helper, whose general checked interface
requires increasing knots.

`mise run camera:rust:awb-low-gain` compares **1,024 cases** against a complete
return from the original low-count routine with single-color disabled:
532 sufficient-count, 128 history-fallback, 109 temporal, 194 spatial and 61
blended cases. Host and ARM compare all represented gain fields, prior-use flag,
per-light gains/weights, updated color-list contents and links, allocation
balance, and unrelated-memory preservation. Input gain-list nodes are preserved.
Original numerical/list helpers execute; memory copy, allocation and logging
are explicit adapters. The corpus covers unsigned count boundaries, 1–255
lights, empty/nonempty histories, zero probabilities, equal/reversed and
float-collapsed brightness thresholds, and append/rotate/no-op list updates.
[Reference report](awb-low-gain-equivalence.json).

The enabled single-color processing/manager branch is the next missing part of
this low-count strategy. Complete high/low orchestration, postprocessing,
calibration loading, frame lifecycle and live integration remain unfinished.

## Single-color confidence manager and color temperature

`awb_single_color::color_temperature` reconstructs `AwbCalCCTandCCRIByGain`
(ELF `0xca840`). It uses the two calibrated lines and R/Gr, B/Gb ratios to
calculate CCT and CCRI with the original rounded products and FMAs. Invalid lines,
Gr/Gb below the double-precision 1e-5 threshold, or a second-line B coefficient
whose magnitude is below that threshold produce the native invalid/zero result.
Line validity is checked before reading inactive numerical inputs.

`awb_single_color::confidence` reconstructs the complete
`AwbSingleColorManager` (ELF `0xcbaf0`), including its original CCT helper:
brightness and white-point-density curves supply two weights; the result's mean
color distance selects three distance weights; calculated CCT blends those into
a third factor; the signed neighborhood-disagreement count supplies the fourth.
The final weight multiplies those factors in native f32 order without clamping.

The manager constructs its three CCT values in reverse calibration memory order:
tables at offsets 0xa4, 0x8c, 0x74 correspond to ascending CCT knots at 0x68.
The Rust calibration type documents its memory-order arrays. Native interpolation
also accepts repeated endpoints: the pinned IQ's density curve repeats its final
knot. This module checks nondecreasing curves and preserves native endpoint and
interval selection, rather than passing them through the general strict-knot
interpolation API or rewriting the calibration.

`mise run camera:rust:awb-single-color` compares **2,048 cases**, 1,024 per
function, on host and ARM. Both original functions return normally with all
numerical/interpolation helper bodies intact; logging is the only adapter.
Checks include exact CCT/CCRI/confidence bits, native validity/return codes,
preserved output padding and unchanged gains/configuration/statistics. Cases
cover invalid lines, green/line denominator boundaries, signed full-width
disagreement counts, interpolation endpoints, repeated/all-equal knots, and
unclamped negative/greater-than-one weights.
[Reference report](awb-single-color-equivalence.json).

The manager consumes explicit result statistics. The preceding 15×15 grid color
classifier, its candidate/history construction, and enabled low-count
orchestration remain unfinished and required by the pinned IQ. This manager
alone does not enable live single-color AWB or change the frozen camera kit.

## Single-color classifier color transforms

`awb_color` implements the native `rgb2xyz` (ELF `0xcbce8`), Lab transfer
`f(float)` (`0xcbda0`), `xyz2lab` (`0xcbdf0`) and `lab2lch` (`0xcbeb4`) routines
used for every grid/candidate pair in single-color classification. RGB-to-XYZ
uses the recovered double coefficients and FMA order. XYZ-to-Lab divides X and Z
by double white-point constants, rounds to float before transfer, and uses the
original float arithmetic for L*, a* and b*.

The nonlinear transfer is not a cube root: its exponent is the rounded float
1/3. In the pinned uClibc, `powf`, `sqrtf` and `atan2f` promote their arguments,
run double math, then round the result to float. Rust mirrors those wrappers
with its standalone `libm` double routines. LCh chroma starts from the original
float square/FMA sum. Hue uses the recovered float divisor (one float step below
the usual rounded pi), float division and multiplication by 180; negative angles
remain negative rather than being wrapped into a full turn.

`mise run camera:rust:awb-color` compares **5,120 cases**, 1,024 per individual
stage and 1,024 joined RGB-to-LCh cases, on host and ARM. The oracle executes
the original RKAIQ bodies and the actual pinned uClibc ARM `powf`, `sqrtf` and
`atan2f` bodies in isolated emulators, passing their result bits back to RKAIQ.
It does not substitute Python/host math. All output bits and output padding
match. The corpus includes transfer boundaries, primary/neutral colors, signed
zeros, all hue quadrants, subnormal square inputs, and finite negative/above-one
RGB/XYZ inputs. Runtime SHA-256 is checked against the existing artifact pin.
[Reference report](awb-color-equivalence.json).

This establishes exact output equivalence for the tested corpus, not universal
double-math equality for every input. The classifier's grid matching,
neighborhood rejection, candidate votes/history and enabled low-count integration
remain unfinished. The fixed-WB camera kit is unchanged.

## Complete single-color grid classifier

`awb_single_color_grid::State::process` reconstructs the complete value path of
`AwbSingleColorProcess2` (ELF `0xcb208`), through normal return. For each of 225
grid cells it applies candidate red/blue gains, clamps only the upper red/blue
values to 1, converts RGB through the recovered color transforms, and finds the
nearest calibrated color/candidate pair. Distance uses the original weighted
chroma/hue arithmetic and FMA, including signed hue and native hue wrapping.
Strict improvements replace a winner; ties keep the earlier candidate/color.

The second pass computes each selected candidate's CCT and interpolates the
color's distance threshold. A cell is accepted only when it passes that threshold
and all four neighbor color labels agree. Missing edge neighbors refer to the
cell itself. Rejection does not change the labels used by later cells. The
routine counts accepted cells by candidate and color, preserves float summation
order for their mean distance, chooses first-index vote winners, updates the
candidate history and applies its majority vote. The reported peak vote count
and color remain from the current grid, even when history changes the selected
gain. No accepted cells means invalid/unity gain, indices/votes -1 and distance
9999; history remains unchanged. Unused count-array tails retain prior values.

An optional prior gain becomes an additional candidate only when both green
channels are strictly above the native double 1e-5 threshold. The checked API
supports up to 14 available candidates and 14 colors and requires history indices
to refer to available candidates. It rejects native out-of-range/uninitialized
index domains and the corrupting singleton target-1 list update. Detection and
history are published together only on success; a unit test checks rejection
after numerical processing leaves the entire prior detection intact.

`mise run camera:rust:awb-single-color-grid` compares **48 complete grids /
10,800 cells** on host and ARM: 23 valid and 25 empty detections. The original
classifier, list, CCT/color and pinned uClibc math bodies all execute. Only bounded
allocation, standard memory and logging are adapters. It checks all represented
result words/count tails, output gains, history contents/links and unchanged
calibration, candidate, optional-prior and by-value grid inputs. Cases include
uniform, split and noisy grids, candidate/color ties, optional valid/invalid
priors, history voting, no-op/append/rotate updates and 14-candidate boundaries.
The native function retains two candidate scratch allocations on return; the
oracle accounts for those separately from history nodes, while Rust uses owned
bounded scratch. [Reference report](awb-single-color-grid-equivalence.json).

The next required step is joining this classifier and confidence manager into
the enabled low-count strategy. IQ initialization, full gain postprocessing,
frame lifecycle and live AWB integration remain unfinished.

## Enabled single-color low-count orchestration

`awb_low_single_color::State::calculate` joins the low-count temporal/spatial
core, single-color grid classifier and confidence manager through a complete
return from `AwbCalGainWpTypeLow` (ELF `0xc6a90`). Its enable flag is explicitly
true; disabled profiles retain `calculate_without_single_color`. Modes 0, 1 and
2 follow the recovered caller policy rather than replacing classification with
an independent gain estimate.

Mode 2 bypasses the sufficient-count early return. With empty gain history,
single-color processing runs only for a valid grid in the intermediate
brightness range. An accepted result replaces the current gain and sets its
weight to 1, preserving the older spatial weight; rejection retains the
temporal/spatial blend and clears single-color weight. A nonempty gain history
allows single-color processing when the grid is valid and mode is at least 1.
Mode 2 supplies no optional prior; other active modes may use the first gain of
the high-count history list as an additional classifier candidate.

After classification, invalid detections fall back to the last ordinary gain
history entry and clear single-color weight. A valid mode-1 detection with a
positive estimated red gain above 1e-5 blends detected and estimated gains using
the computed confidence, including native normalization. Otherwise confidence
chooses either the detected gain at weight 1 or the ordinary history fallback
at weight 0. Successful detections preserve temporal-result/previous-use fields
when native code does not write them. Sufficient-count shortcuts and missing-grid
paths likewise preserve inactive single-color results.

State includes the classifier result and its gain buffer, confidence weight,
shared color history and low-strategy caches. All state and per-light outputs
commit atomically. A unit test forces confidence failure after classification
and spatial processing and verifies the old detection, history, gain caches and
per-light outputs all remain intact. Calibration/list inputs remain explicit;
callers supply the same candidate count/history target to both representations
of the shared native single-color configuration.

`mise run camera:rust:awb-low-single-color` compares **64 complete native calls**
on host and ARM, including **34 classifier calls** with their original
confidence/color/math helpers. Coverage crosses modes 0–2, empty/nonempty gain
history, valid/missing grids, sufficient-count bypass, valid/empty detections,
confidence acceptance/rejection, optional high-history candidates, estimated-gain
mixtures, cache preservation and history updates. The oracle shares the existing
disabled low-count harness with explicit enabled setup; that original
1,024-case regression remains unchanged. Standard memory, allocation and logging
are adapters; strategy and all numerical bodies execute original ARM code.
[Reference report](awb-low-single-color-equivalence.json).

This joins the previously missing enabled low-count branch required by the
pinned IQ. It still needs calibration initialization, integration with the
caller’s high/low interpolation and gain postprocessing, complete frame
lifecycle and live AWB submission. The frozen camera kit remains fixed-WB.

## Gain history, freeze gate and convergence

`awb_gain_history` reconstructs `UpdateWbGainList` (ELF `0xc9c2e`),
`IsWbGainConverged` (`0xc9cb0`) and `IsUpdateWbGain` (`0xc9e24`). Owned bounded
gain storage replaces native intrusive nodes. Updating appends while below the
target, otherwise replaces the oldest gain and moves it to the tail. Reducing a
target does not shrink history, and target 0 is a no-op. Unlike the scalar-luma
helper, the native gain helper explicitly avoids relinking a singleton and
supports target-1 replacement; Rust preserves that behavior.

Convergence requires at least three samples, counting the optional proposed
gain. It averages channel gains in list order, then accumulates absolute
deviations for **existing history entries only**, divided by that same sample
count. The proposal affects the mean and denominator but contributes no direct
deviation term. Any channel whose deviation is greater than or equal to the
threshold makes the result unconverged. This asymmetry is recovered behavior,
not a rewritten statistical estimator.

The update gate accepts gains while history is shorter than the requested
target. Otherwise it tests convergence including the proposal and updates only
if unconverged. `History::select` joins that gate with native list behavior: an
accepted gain updates history; a frozen proposal uses the existing tail gain.
The later caller convergence check uses no proposal and twice its configured
threshold. The Rust API rejects negative/out-of-capacity update targets and
nonfinite active numerical inputs without changing history.

`mise run camera:rust:awb-gain-history` compares **64 persistent sequences /
1,024 events** on host and ARM: 788 updates, 236 frozen proposals and 299
post-update convergence results. Each event executes the original gate,
conditional original list update and original convergence helper. It checks
exact selected gain/list bits, list links, allocation counts, input padding and
immutable gate/convergence memory. Cases cover empty/short/full histories,
target 0, singleton replacement, reduced targets, stable/changing gains, zero
thresholds and a directed proposal-only deviation case. Allocation and logging
are explicit adapters. [Reference report](awb-gain-history-equivalence.json).

Clipping/adjustment, caller high/low composition, post-damping convergence,
calibration loading and live AWB integration remain unfinished.

## Gain adjustment lookup tables

`awb_gain_adjust::shift` reconstructs `AwbCtShift3` (ELF `0xca340`): two
row-major 9×11 output tables share ascending or descending coordinate axes.
Lookup computes four weights with the native subtractions/divisions and the
original rounded-product/FMA order. For inputs outside either axis, it looks up
the edge and restores that input's offset beyond the edge to its output
coordinate. This preserves the recovered translation outside the table.

`awb_gain_adjust::State::adjust` joins the complete `AwbGainAdjust3`
(`0xcad70`) call tree. Temperature mode uses the forward CCT/CCRI conversion,
table adjustment and inverse gain conversion. Other modes use R/Gr and B/Gb
coordinates and write `[adjusted R, 1, 1, adjusted B]` without normalization;
insufficient green denominators leave all state unchanged. A caller-selected
sample chooses one table or interpolates between two sample levels. A sample
span below the double 1e-5 threshold selects the lower output. Temperature mode
updates before/after coordinate caches; ratio mode preserves them. State commits
only on success.

The original endpoint index can point at the last axis element while its
bilinear expression still reads an adjacent element. This crosses from the X
axis into Y, or from Y into the first mapped table. Equal cross-boundary values
produce a zero denominator and NaN even for otherwise strict monotonic axes.
Rust detects that domain and returns `DegenerateRange`, preserving gain/caches.
For finite endpoint results it uses the last bounded cell, avoiding the native
zero-weight out-of-array reads. Temporary validity/padding words copied into
native diagnostic caches can be uninitialized on a two-table interpolation;
the value API represents their defined coordinate floats only.

`mise run camera:rust:awb-gain-adjust` runs **2,048 cases** on host and ARM:
**1,945 finite native results match exactly**, and **103 native NaN cases are
rejected explicitly**. The complete original table/index/interpolation/CCT and
normalization bodies execute; standard memory copy and logging are adapters.
Coverage includes both axis directions, endpoints/interior/outside values,
temperature/ratio modes, sample selectors, 1–4 levels, repeated level samples,
tiny spans, invalid lines and green-denominator boundaries. It compares gain
and defined cache coordinate bits, output padding and unrelated memory. The
native undefined validity/padding cache words are excluded explicitly. A unit
test checks endpoint rejection leaves gain and caches intact.
[Reference report](awb-gain-adjust-equivalence.json).

The pinned IQ currently disables `wbGainAdjust`; this recovers its optional
enable path without changing that profile. Full caller composition, remaining
postprocessing, calibration loading and live AWB integration remain unfinished.

## Common gain processing through final metadata

`awb_postprocess::State::finish` joins the common tail of `AwbCalGainByWbMode`
(ELF `0xc72b8`) after strategy gain selection. It records the raw proposal,
applies the history update/freeze gate, calculates history convergence, and runs
optional clipping, adjustment and gain offsets in native order. Disabled stages
preserve their caches. `awb_gain::offset` applies all four offsets only when all
resulting channels are nonnegative; one rejected channel preserves the whole
gain, while the caller still copies that gain into its offset-result cache.

The tail damps the processed proposal against the prior-frame gain and preserves
the recovered coefficient reset/effective-coefficient rules. It then compares
damped versus undamped channels. History convergence is cleared if any delta is
greater than or equal to the configured convergence threshold. A second native
flag at context `0x3346`, represented as `damping_stable`, starts true and is
cleared by its separate threshold at config `0x4ac`. The API names the measured
condition without claiming the flag's full outer publication policy.

Finally, the tail updates a separate output-gain history, computes current
CCT/CCRI, stably sorts illumination indices by descending probability and emits
four ranked illumination CCT/CCRI records. Equal probabilities retain input
order. Native code always indexes four ranked entries; the checked API requires
4–255 metadata lights. The previous-frame gain stays unchanged here because
`AwbCalAwbGain` advances it later. All caches, histories, flags and metadata
commit together only on success. A late-invalid-probability unit test confirms
that even completed damping/history work cannot partially publish state.

`mise run camera:rust:awb-postprocess` compares **256 full original gain-mode
calls** on host and ARM, including all eight clipping/adjustment/offset enable
combinations, frozen/updated gain history, target 0/singleton/rotation, zero
previous gains, coefficient and threshold boundaries, invalid CCT lines,
probability ties and up to 255 lights. Native calls enter the incomplete-
measurement fallback, which normalizes the explicit proposal, then run the
entire common processing tail through normal return. No numerical/policy helper
is replaced. Standard allocation, memory copy and logging are adapters.

The comparison covers exact gain/cache/coordinate/coefficient bits, both linked
histories, stability flags, current and four ranked temperature records,
metadata padding, allocation balance and unrelated-memory preservation. As in
the adjustment suite, undefined temporary adjustment validity cache words are
excluded while their defined coordinate values are compared.
[Reference report](awb-postprocess-equivalence.json).

This does not yet join the complete-measurement region/probability/high/low
strategy prefix to the tail. That composition, calibration initialization,
wrapper frame lifecycle and live AWB integration remain unfinished.

## Composed gain-mode controller

`awb_gain_controller::State::process` now connects region selection, total
probabilities, high/low strategies, their caller policy and common processing.
Its input is prepared per-light measurements and explicit calibration. A
separate `awb_probability::total_probabilities` entry preserves the white-point
distribution chosen by the region controller instead of filtering counts again.
The original combined count/probability API retains its existing behavior.

The controller computes white-point density in native f32 order as retained
count divided by the two supplied measurement divisors, multiplied by 100000.
It handles incomplete-measurement normalized fallback and mode-0 direct
Exclusion aggregate gains. The latter preserves the prior white-point kind
because native code skips classification there. Other complete-measurement
branches reset spatial weights, compute total probabilities, and run high/low
strategies against the same represented state.

High/low mixing uses the retained count and two count thresholds, or weight 0
in mode 2. It uses the native product/FMA without adding normalization. The
high-result history updates only when density is strictly above its threshold.
Mode 1 retains either the high gain when density exceeds its threshold, or the
mixed gain when single-color weight exceeds its separate threshold; otherwise
the estimated gain stays unchanged. Low-strategy history references the raw
gain list before the common tail updates it. Candidate history and estimated
gain likewise reach single-color classification before caller retention changes.
The enabled single-color route is wired to its existing checked API.

The common tail consumes final per-light gains/probabilities for ranked
metadata. Its current gain is synchronized back to the low-state representation
only after completion. Region, scalar/gain histories, probability/result arrays,
strategy caches, retained gains, diagnostic flags and common-tail state publish
together on success. These remain value-level representations, not a recovered
complete calibration loader or outer frame/session lifecycle.

`mise run camera:rust:awb-gain-controller` compares **192 calls** through the
entire original `AwbCalGainByWbMode` (ELF `0xc72b8`) on host and ARM. It covers
complete/incomplete measurements, modes 0–2, ordinary Normal/Big regions, mode-0
direct Exclusion fallback, rolling selection, normal/FASTAWBACT probabilities,
high/low gain/history policy, offsets, final processing and ranked metadata.
All numerical/policy bodies execute natively; standard allocation, memory,
strings and logging are explicit adapters. Every represented per-light value,
gain/cache/coefficient/flag, both common histories, selection/color/high-result
histories and unrelated bytes are compared. The existing 2,000-case probability
and 256-case postprocessing suites remain regressions after sharing their APIs.
[Reference report](awb-gain-controller-equivalence.json).

This initial joined corpus disables single-color and optional clipping/adjustment,
which have their own complete native comparisons. Enabled single-color still
needs a whole-controller comparison, and ordinary mode-1/2 Exclusion prepared-data
mapping needs a joined audit. Complete calibration initialization, preprocessing-
to-controller composition, wrapper lifecycle and live integration remain unfinished.

## Single-color inside the whole gain controller

`mise run camera:rust:awb-gain-controller-single-color` now verifies the enabled
single-color route inside a complete original `AwbCalGainByWbMode` call. The
same reference harness supports `--single` and retains the original disabled
192-case regression. Rust fixture calibration parsing is shared with the
standalone enabled low-count suite.

**64 complete controller calls match on host and ARM**, including **24 actual
classifier executions** (19 valid and 5 empty detections). Directed sparse-count
cases reach modes 1 and 2 with both empty and existing raw gain history.
Coverage includes accepted/rejected confidence, estimated-gain mixtures,
missing grids, sufficient-count skips, optional high-history candidates,
history updates, gain mixing/retention and final processing. The check includes
the complete classifier record and its gain buffer, including preservation when
classification is skipped. Final single-color weights 0, 0.25 and 1 are
represented in the coverage report.

The original classifier/manager/color call trees execute within the original
controller. Their math imports run the pinned uClibc ARM bodies in an isolated
emulator; integer conversions run the pinned GCC runtime. Both runtime hashes
are verified. The corpus executes 84,375 native `powf`, 16,875 `sqrtf` and 16,875
`atan2f` calls. Native scratch allocations retained by classification are
accounted for separately from the three strategy histories and two common gain
histories. [Enabled controller report](awb-gain-controller-single-color-equivalence.json).

This closes the enabled single-color whole-controller comparison gap without a
production numerical change. Optional clipping/adjustment still have separate
complete comparisons, and ordinary mode-1/2 Exclusion prepared-data mapping
still needs a joined audit. Calibration initialization, preprocessing/controller
composition, wrapper lifecycle and live AWB integration remain unfinished.

## Gain clipping and inverse color-temperature conversion

`awb_single_color::gain_from_color_temperature` reconstructs
`AwbCalcWBgainbyCT` (ELF `0xca908`), the inverse of the forward CCT/CCRI helper.
Both calibrated line-valid flags and the second line's A/B magnitude thresholds
gate conversion. The input temperature-valid word is ignored by native code.
On conversion failure the supplied prior gain is preserved. Success constructs
red/blue gains with the original division/FMA order, sets both green gains to 1,
and applies native normalization. The checked API rejects nonfinite arithmetic,
including the native unchecked first-line B zero denominator.

`awb_gain_clip::clip` reconstructs `AwbGainClip` (ELF `0xca9c0`) through its
complete forward/clamp/inverse call tree. With valid forward CCT conversion,
daylight clipping raises the temperature floor only when unsigned brightness is
strictly above its threshold. Optional bounds clamp CCT to the table endpoints,
interpolate lower/upper tint limits, negate the lower curve, and apply both tint
comparisons in native order. Repeated/nondecreasing CCT knots are supported by
the shared curve helper, now accepting slices as well as fixed arrays.

The clipped flag preserves its incoming value and becomes true on any clamp.
Inverse conversion runs even when no bound was hit, so a round trip can change
gain bits while the clipped flag remains false. An inverse failure preserves the
original gain even if earlier clamps set the flag. An invalid forward result
returns the original gain/flag before reading inactive bounds. The caller still
decides whether to invoke clipping based on its enable flags.

`mise run camera:rust:awb-gain-clip` compares **2,048 cases**, 1,024 inverse
conversions and 1,024 full clipping calls, on host and ARM. Original forward,
interpolation, inverse and normalization bodies execute; only logging is adapted.
Checks cover exact gain bits, inverse status, clipped flag, output padding,
unrelated context and unchanged calibration/curves. Cases include line validity,
green and denominator thresholds, temperature/tint limits, daylight threshold
equality, repeated/single knots, inverted tint limits, inactive bounds and sticky
flags. The confidence-manager regression is retained after sharing slice-based
curves. [Reference report](awb-gain-clip-equivalence.json).

Gain adjustment LUTs, caller high/low composition, remaining postprocessing,
calibration loading and live AWB integration remain unfinished.

## Prepared-record boundary audit

`mise run camera:rust:awb-prepared-layout` executes the original
`AwbCalGainForDiffIllumination` (ELF `0xc5e10`) against contiguous prepared
records, with extra-region mixing disabled. All **16 cases** match exact copied
bits and preserve unrelated memory: regions 0–3 with 1, 4, 8 and 255 lights.
The library hash is verified before execution.
[Native layout evidence](awb-prepared-layout-audit.json).

Each prepared light occupies `0xac` bytes. Regions 0, 1 and 2 have count/gain
blocks at `region * 0x34`; the separate preparation gain occupies `0x9c..0xac`.
Passing region 3 to the native helper interprets the preparation gain's red bits
as a count. Its gain copy starts at `0xa0`, yielding preparation Gr, Gb, blue,
then **the next light's Normal count interpreted as float bits**. For the final
light, the fourth gain word lies beyond the final prepared record. The audit
sets that external word to `0x12345678` and observes it in the native output.
This is a read across a record boundary, not a fourth independent XY region.

`awb_preparation::LightRecord` correctly exposes only regions 0–2. The gain
controller's explicit fourth value slot must not be populated with an invented
per-light Exclusion measurement. Its prior isolated high-gain corpus seeded
selected gains directly, so that corpus alone did not validate a prepared-data
adapter. The joined controller corpus still covers Exclusion through the mode-0
aggregate bypass only. Native mode-1/2 Exclusion reachability with real IQ/state,
allocation trailing contents, and a deliberate safe replacement policy remain
to be established before connecting this branch. No production mapping or
fallback policy changed in this audit.

## SC3336 Exclusion reachability in INITIAL mode

The hash-pinned SC3336 IQ selects `AWB_SGC_CALL_INITIAL`. The SDK's pinned
`iq_parser_v2/awb_head.h` defines INITIAL=0, AUTO=1 and ALWAYS=2; this header is
now recorded in `artifacts.json` and checked by the directed audit. Its
`xyRegionStableSelection` thresholds for Big and Extra are both 216.
Thus the configured INITIAL mode satisfies the native `mode < 1` guard:
when region 3 is selected, it uses the global Exclusion aggregate and skips
per-light probability/high/low calculation. This holds independently of how
stabilization selected region 3. It is conditional on retaining INITIAL mode;
it does not establish safety for a runtime change to AUTO or ALWAYS.

`mise run camera:rust:awb-gain-controller-initial-exclusion` verifies **192
whole native controller calls** against Rust on host and ARM. Sparse Normal/Big
counts force Exclusion, using the pinned 216 thresholds and mode 0. A native
entry hook asserts that the selected-gain helper is never entered, and that
single-color classification is skipped. Exact output/state comparisons include
the common processing tail. The suite disables stabilization to isolate the
branch and uses synthetic state/calibration for remaining fields; it is not a
full IQ-initialized frame replay. The preexisting 192-case controller regression
also remains required. [Directed comparison report](awb-gain-controller-initial-exclusion-equivalence.json).

This establishes a route for connecting the pinned INITIAL-mode Exclusion
aggregate without inventing per-light region-3 gains. A future prepared-data
adapter must explicitly guard mode-1/2 Exclusion until its boundary-crossing
native behavior has a deliberate, documented resolution. Full IQ loading,
preprocessing/controller composition and live AWB remain unfinished.

## Prepared-light adapter

`awb_gain_controller::State::process_prepared` accepts the bounded
`awb_preparation::LightRecord` slice directly, alongside per-light calibration,
priors, frame aggregates and controller settings. It loads Normal, Big and
extra-region count/gain fields from each record's actual `0x34`-byte blocks.
The explicit arrays in the calibration-bearing `Light` arguments are ignored.
The existing value API remains available for isolated numerical comparisons.

After region selection, the prepared adapter returns
`InvalidInput::UnsupportedRegion` for Exclusion with mode >= 1, before committing
any controller or per-light output state. It neither reads adjacent record bytes
nor fabricates a fourth measurement. INITIAL-mode Exclusion continues through
the verified aggregate bypass. Incomplete measurements bypass region selection
and retain the normal fallback behavior, including when the prior region was
Exclusion in mode 1 or 2. All processing is staged, so errors leave caller state
and output unchanged.

The prepared-record comparison corpus poisons the ignored explicit count/gain
arrays with `u32::MAX` and NaNs, ensuring successful output actually comes from
the record adapter. It compares whole native controller outputs on host and ARM:
192 ordinary cases, 192 directed INITIAL-mode Exclusion cases, and 64 enabled
single-color cases. Each corpus also checks two explicit mode-1/2 Exclusion
rejections with unchanged state/output. Those rejection cases intentionally
have no native equivalence claim: native's unchecked cross-record read is the
reason for the checked API boundary. The records are fixture-encoded; this is
not yet a native-preprocessor-to-controller whole-frame comparison.

Run `camera:rust:awb-prepared-controller` for the first two corpora; the enabled
suite uses `awb-gain-controller.py --prepared --single --arm` after building the
host and ARM fixtures. Reports:
[ordinary](awb-prepared-controller-equivalence.json),
[INITIAL Exclusion](awb-prepared-controller-initial-equivalence.json),
[enabled single-color](awb-prepared-controller-single-color-equivalence.json).
Full IQ initialization, shared frame-state construction, outer lifecycle and
live AWB integration remain unfinished; the AUTO/ALWAYS Exclusion boundary is
an explicit unresolved requirement rather than a completed vendor replacement.

## Saved-site startup gain reuse

`awb_site::State::apply` reconstructs `runAvaSiteRec` (ELF `0xc7e70`), recovered
with Ghidra from the pinned library. `AwbCalAwbGain` calls this **after** the
complete gain-mode function and **before** copying current gain into previous
gain. It can replace the computed gain, so omitting it would change the result
of the outer wrapper. The pinned IQ enables recording and reuse, with a
three-frame limit, gain threshold 0.2 and sample threshold 2.

Disabled recording or an exhausted unsigned frame counter returns unchanged.
With reuse enabled, only frame 0 tests a match. Relative sample distance is
`abs(reference - current) / ((reference + current) * 0.5)` when that mean is
strictly above the original double 1e-5 constant; otherwise distance is zero.
Only a strict sample-threshold pass reaches the gain comparison. A missing
reference or current green-product <= 1e-5 supplies gain distance 10; otherwise
it sums absolute differences of R/Gr and B/Gb ratios. A strict gain-threshold
pass sets the persistent matched flag; failure preserves an existing true flag.

When reuse is enabled but no match exists, the function only advances the
counter. Otherwise it copies all four saved gain words if context +4 is false,
context +8 equals 1, and the saved reference is valid. The application meanings
of those two fields are still unresolved and the Rust API names them by their
stored predicates. In particular, disabling reuse does not by itself prevent
this final copy in native code. The counter advances once per active call,
including a call that finds no match. There is no reference-file access in this
helper: loading/saving `/tmp/avaSiteInfo` belongs elsewhere in initialization.

`mise run camera:rust:awb-site` compares 256 eight-event sequences plus eight
directed boundary cases (**2,056 calls**) on host and ARM. It verifies exact gain
bits, match flag, counter and preservation of unrelated context. Sequence state
is carried through native outputs and replayed as Rust inputs. Directed cases
include exact sample/gain thresholds, invalid reference, zero mean and zero
current green product. Logging is adapted; the original policy executes through
return. Two Rust checks cover nonfinite-ratio rollback and disabled-input
short-circuiting. [Comparison report](awb-site-equivalence.json).

The outer wrapper's per-frame reset literal at ELF `0xc8200` is **-1.0**,
verified from its bytes `00 00 80 bf`; its diagnostic weights must not be reset
to zero or unity during subsequent composition. Full reset/damping/tolerance
composition, saved-reference initialization and live AWB remain unfinished.

## Joined outer gain wrapper

`awb_wrapper::process` reconstructs the represented state transition of
`AwbCalAwbGain` (ELF `0xc803c`) with prepared light records. It stages controller
state, per-light results and saved-site state together, then:

1. Clears the classifier result and gain buffers, per-light numerical results,
   strategy diagnostics and optional-processing caches. Diagnostic weights reset
   to native **-1.0**, not zero. Histories, estimated gain, current/previous gain
   and adaptive coefficient retain their previous values at entry.
2. Adapts the damping coefficient with the shared variance and evaluates the
   tolerance curve at unsigned brightness converted to f32.
3. Runs the prepared-record controller through its complete strategy/common tail.
4. Applies saved-site startup reuse, then copies the resulting current gain to
   previous gain for the next frame.

The wrapper derives region stabilization variance, classifier brightness sample
and saved-site frame/sample from shared inputs, preventing contradictory copies
of those native context fields. Saved-site reuse happens after CCT/ranked-light
metadata calculation; it does not retroactively recompute that metadata or the
undamped/damped caches. The API preserves this original ordering. Diagnostic
strings and context fields outside the represented Rust state are not exposed.

`mise run camera:rust:awb-wrapper` executes the original outer function and all
its numerical/controller/site callees to return. The ordinary 192-case corpus
and enabled-single-color 64-case corpus compare exact represented state,
per-light results, histories, adaptive coefficient, tolerance, site state and
final/previous gains on host and ARM. Native entry tracing also counts real
saved-site gain replacements. Synthetic reference labels are empty; the oracle
checks that native clears the remaining label/unused bytes. Numerical bodies
are not replaced with a modeled controller. Memory, allocation, strings and
logging use the existing explicit adapters; classifier math runs pinned uClibc
ARM code.

Each corpus also verifies three checked failures leave controller state,
per-light output **and saved-site state** unchanged: unresolved mode-1/2
Exclusion plus a nonfinite saved-reference ratio discovered only after gain
calculation. Those checked failures do not claim native equivalence for unsafe
or nonfinite behavior. Optional clipping/adjustment remain verified in separate
suites, not enabled in these joined corpora. Records and calibration are still
fixture-built rather than produced by the full native preprocessor/IQ loader.
Reports: [ordinary wrapper](awb-wrapper-equivalence.json),
[enabled classifier wrapper](awb-wrapper-single-color-equivalence.json).

Remaining work includes full IQ/state initialization, preprocessor-to-wrapper
composition, outer processing/publication lifecycle, saved-reference persistence,
resolution of AUTO/ALWAYS Exclusion, and live automatic-WB qualification. This
wrapper is a joined stage, not a complete vendor-free camera claim.

## Post-preparation frame dispatch

`awb_dispatch::State::process` reconstructs the standard `AwbPreProcV32`
continuation beginning at ELF `0xc4ae0`, immediately after
`PrepareMeasureResult`. If update is false, it returns without gain calculation,
countdown change, frame increment or reconfiguration. A pending update decrements
only a positive signed countdown and always requests hardware reconfiguration.
With incomplete measurements, it leaves gain and frame counter unchanged.
With complete measurements, it calls the gain-wrapper callback, optionally
multiplies red and blue by their per-channel scale factors, then increments the
u32 frame counter with wrapping arithmetic. Green channels are unchanged.

The wrapper has already copied its unscaled output to previous gain before this
scaling. Dispatch does not overwrite that previous gain or recompute the
wrapper's CCT/other diagnostics. This ordering matters for the next frame's
damping. The dispatcher returns an explicit calculate/reconfigure action; the
actual hardware-configuration stage is not yet joined here.

`mise run camera:rust:awb-dispatch` compares **1,024 cases** on host and ARM:
all update/completeness/scaling combinations, negative/zero/positive and extreme
signed countdowns, frame wraparound, and zero/negative/unit/asymmetric scales.
It checks exact current/previous gain words, countdown/frame state, action flags
and unrelated context/configuration preservation. The oracle executes the
original continuation instructions with R4=context, R5=update offset `0x334a`
and a disabled logging context in R8. Gain calculation is an explicit callback
adapter supplying current and previous results; its full original-body numerical
comparison is the separate wrapper suite. Execution stops at hardware
reconfiguration entry or the common preprocessor epilogue. This evidence does
not claim a full native preprocessor-to-gain-wrapper comparison.
[Dispatch report](awb-dispatch-equivalence.json).

Rust rejects nonfinite scale inputs before invoking the gain callback. It stages
its countdown/frame and gain outputs on checked failures; callback-owned state
must also be staged by a joined session, since a finite scale can overflow only
after the callback produces gain. A regression verifies invalid input cannot
invoke the callback or change dispatch state. Complete IQ initialization,
shared session construction, hardware reconfiguration/publication and live AWB
qualification remain outstanding.

## Joined gain-frame continuation

`awb_gain_frame::State` owns dispatch counters, the gain controller and saved-site
state. Its `process` method connects post-preparation dispatch to the **real Rust
gain wrapper** and commits the whole transition together. The dispatch frame
counter supplies the wrapper's shared frame number. Current output receives
post-wrapper red/blue scaling; previous gain retains the unscaled wrapper result.
No-update and incomplete-measurement paths preserve controller/site/per-light
state, while pending incomplete updates still decrement a positive countdown
and request reconfiguration. Skipped paths do not inspect unused measurement or
calibration arrays.

A cloned session and staged per-light output address the callback ownership gap
in the lower-level dispatch API: a failure after the wrapper has calculated gain,
including finite-scale overflow, discards histories, saved-site updates, gain,
per-light output and counters together. This is checked behavior for the Rust
API, not a claim that the unchecked original library rolls back its writes.

`mise run camera:rust:awb-gain-frame` compares 192 ordinary and 64 enabled
single-color branch cases on host and ARM. The oracle starts at the original
post-preparation continuation and follows its original **gain-wrapper body and
all numerical/policy callees**, then output scaling and frame increment. It
stops at hardware-reconfiguration entry or the no-update epilogue; only logging,
allocation/memory/string adapters and pinned runtime imports are intercepted.
Gain calculation is no longer supplied by the dispatcher test's callback stub.

Across both corpora, 178 cases actually execute the wrapper; the remainder
exercise no-update/incomplete branches. There are 20 classifier executions and
eight genuine saved-site gain replacements, counted before output scaling.
Comparisons include current/previous gains, all represented controller caches,
metadata, per-light results, histories, saved-site state, tolerance, countdown,
frame counter and reconfiguration decisions. Eight checked-error cases verify
complete rollback: mode-1/2 Exclusion, late saved-reference arithmetic failure,
and overflow in final red scaling after a successful wrapper transition.
[Ordinary joined report](awb-gain-frame-equivalence.json),
[enabled classifier joined report](awb-gain-frame-single-color-equivalence.json).

This closes dispatch-to-wrapper composition. Inputs are still prepared fixture
records and explicit calibration. Raw preprocessing/IQ initialization, actual
hardware measurement reconfiguration, outer publication/lifecycle, saved-site
persistence, unsafe native Exclusion resolution and live qualification remain
unfinished. Passing this stage does not establish a complete frame pipeline.

## Loading single-color settings from SC3336 IQ

`awb_calibration::SingleColor::from_value` now owns the explicitly selected
`autoExtPara.singleColorProces` object. This diagnostics-feature loader uses
`serde_json` and allocated vectors; the numerical classifier/manager remain
allocation-free and available without diagnostics. It does not choose a scene
or silently supply missing calibration values.

The loader reads enable/mode, candidate names and red/blue gains, color labels
and LCh/temperature-distance tables, history size, alpha, diagnostic candidate,
acceptance/estimate/history thresholds, and every confidence-manager table.
INITIAL/AUTO/ALWAYS map to the SDK enum values 0/1/2. Native confidence memory
order is high/medium/low CCT tables; the existing manager retains its verified
reverse-order CCT interpolation behavior. Color result indices refer to table
positions; original external color labels are separately preserved as metadata.

Declared dynamic lengths must match arrays and the bounded numerical API's
1–14 candidate/color limits. Fixed arrays have exact lengths, numbers must fit
finite f32, integer/flag fields are checked, names must fit the native 20-byte
candidate name storage including termination, and confidence/color CCT knots
must be nondecreasing. Repeated density endpoints are accepted, as required by
the actual IQ. Singleton-history native hazards remain subject to the existing
checked runtime policy; loading a history target does not erase that boundary.
Calibrated line construction/validity remains external to this loader.

`mise run camera:rust:awb-iq-single-color` verifies the pinned IQ/binary/GCC/math
runtime hashes and uses the loaded object in **24 complete grid classifications
(5,400 cells) and 256 confidence-manager comparisons** on host and ARM. Nine
classifications are valid and 15 empty. The native reference uses the same IQ's
original color labels and numerical arrays; Rust's manual fixture calibration
is poisoned so a successful comparison must use the parser's owned data.
The suite also independently checks scalar flags/mode/metadata/threshold bits
and rejects ten malformed objects, including missing/unknown mode, inconsistent
lengths, fixed-array mismatch, descending knots, overflow, fractional history
size, invalid flag/name and alpha out of range.
[IQ-loaded comparison report](awb-iq-single-color-equivalence.json).

This loads the single-color subset only. Full seven-light calibration, remaining
preprocessor/wrapper settings, calibrated line construction, full initialization
and the raw-frame/session composition still need implementation. It does not
claim to replay the original IQ database parser or `AwbInitV32` in full, nor to
qualify live automatic white balance. The generic 2,048-case confidence/CCT
regression remains required after extending the fixture to use loaded settings.

## Loading the seven-light calibration

`awb_calibration::Lights::from_value` owns the explicitly selected `wb_v32`
scene's `autoPara.lightSources` table and resolves
`autoExtPara.lightSourceForFirstFrame` by name. All seven SC3336 lights are
loaded, including indoor/ambiguous/outdoor kind, unmodified four-channel
reference gain, sixteen spatial percentages, daylight thresholds and low/high
gains, prior brightness/weight curves, and UV/XY/rotated-YUV detection geometry.
The latter is retained for future hardware configuration rather than applied
by this loader.

Ghidra's `UpdateAwbCalibV2Para` (ELF `0xc1e18`) establishes the mapping into
native strategy records: reference gain `raw +0x18 -> strategy +0x80`, spatial
bytes `+0xb4 -> +0x68`, low threshold `+0xc4 -> +0x7c`, high threshold
`+0xc8 -> +0x78`, low gain `+0xcc -> +0xa0`, and high gain
`+0xdc -> +0x90`. The internal threshold order is therefore reversed relative
to JSON's `[low, high]`; the gain meaning is not reversed. The Rust adapter
names both endpoints explicitly and copies reference/gain words without
inventing normalization. Door kinds use the pinned SDK enum values 1/2/3.

`Illumination::probability` borrows the owned prior curve and reference data.
`controller_light` constructs the calibration-bearing input for the prepared
controller. Its count/gain placeholders are replaced by prepared measurements.
Environment/spatial-weight index and extra-region-enable remain explicit runtime
inputs, with index bounds checked; neither is guessed from static geometry.

The checked loader rejects inconsistent counts/prior lengths, missing or
unsupported enums, duplicate/invalid/overlong light names, absent first-frame
name, malformed fixed geometry, nonfinite/out-of-f32 values, noninteger/out-of-
range byte/u32 fields and nonincreasing prior knots. It preserves all sixteen
weight bytes and does not clamp their percentage values to 100. It chooses no
scene and defaults no missing calibration field.

`mise run camera:rust:awb-iq-lights` compares **128 probability/filter/weighted-
gain calls and 128 complete high-gain calls** using the actual seven-light IQ
on host and ARM. Cases cover all sixteen spatial indices, FAST/normal behavior,
daylight threshold boundaries, selected/extra-region mixes, varied counts and
prior samples. Manual reference/kind/prior and spatial-calibration fixture
values are poisoned to prove loaded settings are authoritative. Separate checks
compare parsed names/kinds/reference and every detection-geometry word, and
reject ten malformed scene objects. Binary/IQ/GCC hashes are verified.
[Seven-light comparison report](awb-iq-lights-equivalence.json).

This closes light-table loading, not full initialization. Shared global
preprocessing/controller settings, line derivation, runtime extra-range policy,
raw preprocessing-to-session composition, hardware reconfiguration/publication
and live qualification remain unfinished. The native IQ parser and complete
`AwbInitV32` have not been replayed by this test.

## Shared common-strategy initialization

`awb_calibration::Common::from_value` loads the selected `autoExtPara` fields
used by `JsonPara2SwParaCom` (ELF `0xc8450`), recovered with Ghidra. It owns
night gain, the two calibrated lines, clipping tables/daylight limit, remosaic
flags/sensor gain, night-history weights, brightness knots, probability
thresholds, damping/history/convergence controls, region stability controls and
initial smart-run/countdown constants. `Common::high` borrows/copies these into
the existing high-gain settings without inventing a second calibration table.

The native helper directly copies `lineRgBg` and `lineRgProjCCT` and sets both
valid flags to true. These writes replace the earlier `CalCCTLine` fitted output
in the full update path. The JSON coefficients therefore do not need a new fit
or normalization for this configuration stage; later numerical helpers still
apply their verified denominator/validity guards. Probability distance fields
are copied in low/high order, and its four brightness-threshold words initialize
to `[0, 0, outdoorLow, outdoorHigh]`. The history convergence field receives
`varThforUnDamp`; damped convergence receives `varThforDamp`.

Native startup smart-run values are exact f32 0.001/0.005/0.05 and countdown 20.
They are initial values, before per-frame smart-run interpolation. The helper
also initializes three strategy flags to zero, stores the opaque CCM reference,
and sets the environment interval count to 16. The bounded environment adapter described below now reconstructs this exact
native record layout before shared-session construction. The sixteen night percentages are copied by the enclosing
`UpdateAwbCalibV2Para`, **not** by this common helper. The owned loader reads them
from IQ; the oracle pre-seeds them as that caller does and checks preservation.

`mise run camera:rust:awb-iq-common` executes the **complete original common
initializer** for the pinned SC3336 object and 127 finite variations, comparing
all represented scalar/array/line/remosaic outputs on host and ARM. It checks
four successful native allocations and their returned contents, untouched
calibration inputs, remosaic padding and unrelated strategy bytes. Only bounded
successful allocation and standard memory are adapted. Eight malformed JSON
objects verify missing/nonempty/matching counts, byte limits, line shape,
finite damping, knot ordering and flags. [Common initialization report](awb-iq-common-equivalence.json).

The checked loader rejects empty adjustment-LUT declarations, as the native
helper requires a nonzero LUT count even when adjustment is disabled. It also
requires matching nonempty clipping tables and bounded nonempty history weights;
it does not reproduce native allocation failure/partial-write behavior. Loading
these common fields does not load dynamic preprocessing curves, adjustment LUT
contents or enable flags, full saved-site initialization, or complete IQ/session
lifecycle. Raw preprocessing composition, hardware reconfiguration/publication,
unsafe Exclusion resolution and live AWB qualification remain outstanding.

## Loading dynamic preprocessing curves

`awb_calibration::Preprocessing::from_value` owns the selected `autoExtPara`
smart-run, run-interval, tolerance, white-point count and region-selection
curves. Each group keeps its own knot vector and declared lengths; the groups
are not required to share a grid. It exposes a borrowed
`awb_preprocess::Calibration` and a checked tolerance lookup at unsigned
brightness converted to f32. The parsed smart-run enable flag supplies the
fixture/runtime input rather than a duplicate manual value.

The white-point group is deliberately exposed in **high, low** strategy order:
JSON's `high` pointer is raw +0x590 and feeds strategy +0x1b8, while `low` at
+0x588 feeds +0x1bc. Region outputs remain Big then Extra. Smart outputs remain
luma variance, algorithm gain difference and hardware gain difference. Input
arrays must be finite, nonempty, strictly increasing in knots and consistent
with every declared length. Inline run-interval/tolerance tables are bounded to
eight entries; missing fields receive no fallback defaults.

`mise run camera:rust:awb-iq-preprocess` verifies **192 native preprocessing
cases and 192 native tolerance interpolations** on host and ARM. The first 24
cases use the actual SC3336 curve objects; later cases independently vary each
group's grid, lengths and values. Manual fixture curves are zeroed, so equality
requires the loaded data. Mode bypass, interval skip and ready paths are all
represented. Ninety-six cases configure the existing environment/history
continuation, which executes only when preprocessing reaches its ready branch.
Checks include exact derived smart values, rounded/scaled count thresholds,
region thresholds, luma, interval/frame decisions, metadata history/classification
and preservation of curve input memory. Eight malformed inputs check dynamic
lengths, missing tables, knot order, float overflow, enable flags and inline
capacity. [Loaded preprocessing report](awb-iq-preprocess-equivalence.json).

The oracle executes the standard preprocessor until its metadata exit or entry
to `PrepareMeasureResult`; the measurement preparation body is covered by the
separate prepared-frame suite. This test does not yet execute a single complete
raw-statistics-to-gain session or hardware reconfiguration. Shared runtime state
construction, remaining optional IQ blocks/initialization, publication and live automatic-WB qualification remain unfinished.

## Initialized environment layout and missing-exposure fallback

`Common::environment` now supplies the exact bounded table expected by the
native brightness classifier. Common initialization sets strategy +0x164 to
16 intervals and stores sixteen brightness knots at +0x168. The classifier's
last pair also reads +0x1a8, the adjacent first division threshold. The owned
`environment_boundaries` array represents all **17 words** explicitly, including
that adjacent value, without an out-of-bounds read. Its final pair may descend;
this is intentional record layout rather than an ordered interpolation curve.
The classifier still assigns bucket 15 when no earlier interval matches. Passing
only the sixteen JSON knots to the existing slice API would incorrectly stop
at bucket 14 for high/unmatched brightness.

`Common::fallback_brightness` returns knot index 8. Native preprocessing reads
strategy +0x188 when exposure metadata is absent; that address is the element
at zero-based index 8 in the same matrix. A separately supplied fallback can agree
with isolated prefix tests yet disagree once common initialization populates the
record. The loaded preprocessing fixture now derives both its environment table
and missing-exposure fallback from `Common`, preserving their shared native
layout. Its deliberately different manual fallback is ignored in that path.

`mise run camera:rust:awb-iq-environment` executes 32 complete original common
initializations followed by **1,024 original brightness classifications** using
the initialized strategy memory directly. It covers every environment index
0–15, each brightness knot, all five-level threshold equalities/neighbors,
values below the first knot, the final bucket and `u32::MAX`. Exact levels,
environments, all 17 boundary words, output padding and unchanged configuration
are compared on host and ARM. [Initialized environment report](awb-iq-environment-equivalence.json).

The task also reruns the loaded preprocessing comparison using the corrected
common environment layout and fallback: 192 preprocessing/history branch cases
and 192 tolerance interpolations. This connects common settings to the loaded
prefix rather than checking the two settings blocks only in isolation.
It still stops before complete measurement preparation/gain processing;
full shared-session composition, remaining initialization blocks, hardware
reconfiguration/publication and live automatic-WB qualification remain unfinished.

## Scene-owned settings and optional postprocessing

`awb_calibration::Scene::from_value` now assembles one explicitly selected
`wb_v32` object from the validated light, single-color, common and preprocessing
loaders. It also owns optional clipping/adjustment/offset configuration and
saved-site policy/path metadata. It performs no file I/O and does not implicitly
select a scene, load saved-site contents or initialize persistent histories.

The optional loader validates all 9×11 adjustment LUTs, selectors, sample levels
and strictly ascending/descending axes, preserving the descending gain-mode Y
axis used by SC3336. LUT sample levels may repeat but may not descend. It loads
clipping/daylight/offset enable flags explicitly and preserves the four offset
words without normalization. ISO/LV and GAIN/CT selectors use the pinned SDK enum
mapping. Unknown selectors, wrong LUT shape/count, invalid axes, malformed flags
and invalid saved-site metadata return checked errors.

`Scene::with_post_settings` constructs borrowed settings inside their valid
lifetime and invokes a closure, avoiding self-referential configuration storage.
It supplies history length from the night-history weights, tolerance from the
loaded brightness curve, common convergence/line settings, optional clipping,
LUT selection/sample and offsets. Runtime brightness/luma/ISO and the current
smart-run damping threshold remain explicit inputs. Saved-site settings are
owned for the gain wrapper but are not applied by this postprocessing method.

The native JSON tint names are counterintuitive: the common initializer stores
`cri_bound_up` at strategy +0x378 and `cri_bound_low` at +0x37c; `AwbGainClip`
**negates +0x378 for its negative/lower limit**, then uses +0x37c as its positive/
upper limit. The scene adapter follows those instructions, rather than guessing
from the JSON labels. Asymmetric bound curves explicitly test this mapping.

`mise run camera:rust:awb-iq-scene-post` compares **128 complete native
postprocessing calls** on host and ARM, beginning at the original normalized
incomplete-measurement gain-mode path and returning normally. It covers all
64 combinations of bound/daylight/adjustment/offset enable flags, ISO/LV sample
selection and GAIN/CT adjustment modes, with two cases per combination. The
pinned disabled-optional scene is included; variations enable the optional
paths with one LUT each, asymmetric tint bounds and varying tolerance. Manual
fixture enable/history/tolerance/convergence values are poisoned so successful
comparison requires scene-owned settings. Exact gain/cache/history/convergence,
CCT and ranked metadata checks use the existing full native oracle. A scene
summary checks assembled light/candidate/mode and saved-site fields; eight
malformed scenes exercise the new validation boundaries.
[Scene postprocessing report](awb-iq-scene-post-equivalence.json).

The scene-driven gain-frame adapter described below now supplies the remaining
controller settings. Persistent-session initialization remains separate. Full persistent
initialization, raw preprocessing/measurement-to-gain composition, optional
multi-LUT whole-scene replay, saved-site persistence, hardware reconfiguration/
publication and live automatic-WB qualification remain unfinished.

## Scene-configured gain-frame processing

`Scene::process_gain_frame` now binds the loaded seven-light scene to the joined
gain-frame dispatcher and real gain wrapper. Scene settings supply light priors/
spatial gains, probability thresholds, region stabilization, night gain/weights,
low-count thresholds, enabled single-color classifier/confidence, optional
postprocessing, damping, tolerance and saved-site policy. Borrowed local settings
stay inside the call; persistent histories remain owned by `awb_gain_frame::State`.

`GainRuntime` supplies values that belong to preprocessing/session state: active
light count, derived numeric controls, variance, environment, FAST mode,
absolute count threshold, per-light extra-region flags, grid validity/data,
saved-reference inputs, ISO and output scale. The adapter uses the active prefix
of the scene/cache and rejects inconsistent active lengths. It does not require
all seven calibrated lights to be active. No-update/incomplete-measurement paths
preserve the earlier verified dispatch behavior without reading inactive tuning
or record arrays. Complete processing retains the gain-frame stage's atomic
rollback across controller, saved-site, outputs and counters.

The pinned region history target is 50, so the combined fixture now uses capacity
64 instead of 32. Its postprocessing initializer/output helpers support an
explicit capacity while preserving the old 32-entry standalone interface. The
scene's target is neither shortened nor disabled to make that fixture fit.

`mise run camera:rust:awb-iq-scene-gain` compares 64 original continuation calls
on host and ARM using the actual pinned scene calibration. The original wrapper,
probability/high/low/classifier/common processing/site functions execute through
output scaling and the hardware-reconfiguration request. The corpus includes
active prefixes of four and seven lights, all sixteen environment/spatial slots,
Normal/Big and mode-0 aggregate Exclusion, update/complete skips, valid accepted
and empty classifier results, saved-gain replacement and three calls whose region
history reaches the real 50-entry target. Four checked-error cases retain full
rollback, including unsupported AUTO/ALWAYS Exclusion and late site/scaling errors.
For the four-light prefix, unused trailing prepared records are poisoned with
nonfinite bit patterns to verify they are ignored.
[Scene gain-frame report](awb-iq-scene-gain-equivalence.json).

The native oracle seeds calibration fields from IQ using the already verified
ABI mappings; it does not run the entire calibration initializer. Diagnostics
use empty native light labels. Geometry/derived thresholds and starting state
are still explicit fixtures, not output from raw measurement preparation.
This closes scene-to-gain configuration, not persistent-session bootstrap,
raw preprocessing/measurement-to-gain composition, active-light scheduling,
saved-site persistence, hardware reconfiguration/publication or live automatic-WB
qualification. Those remain unfinished.

## Raw measurement preparation joined to scene gain processing

`Scene::prepare_gain_frame` now runs SDK-format measurement preparation and the
scene-configured gain frame as one transition. It stages every measurement
cache and commits it only after gain processing and output scaling succeed.
The active light prefix, complete flag, FAST mode, grid and pre-gain scale come
from the prepared frame/cache rather than duplicate caller values. Fresh
numeric preprocessing supplies the update flag, luma and stability threshold.

`mise run camera:rust:awb-iq-prepared-gain` compares 64 original ARM calls with
host and ARM Rust output, plus four atomic rejection cases. The native oracle
runs complete `PrepareMeasureResult` before the gain continuation; comparisons
include the full prepared cache, gain histories and output state. Cases cover
four/seven active lights, update/complete branches, Normal/Big and INITIAL-mode
aggregate Exclusion, saved-site replacement and valid/empty classifier results.
Empty-color inputs overwrite every grid cell so stale zero-count cells cannot
accidentally supply a valid color. The pinned INITIAL classifier has zero
single-color weight in this corpus; accepted weighted results remain covered
by the separate scene-gain suite rather than claimed here.
[Joined preparation report](awb-iq-prepared-gain-equivalence.json).

The input is SDK-format translated data with seeded session caches, not a live
ISP statistics payload. Numeric preprocessing, persistent initialization,
active-light scheduling, hardware reconfiguration/publication and live AWB
qualification remain unfinished. AUTO/ALWAYS Exclusion retains the documented
native cross-record-layout hazard and is rejected atomically. This connection
does not enable automatic white balance in the camera command.

### Driver parameter association for AWB translation

`awb_translation::translate_associated` now selects an effective measurement
snapshot by the driver's statistics parameter ID before invoking the existing
single-ISP translator. It rejects missing or duplicate matching IDs and invalid
measurement configurations before changing any destination field. It does not
fall back to a recent configuration or substitute the capture sequence number.
The event owner must still register and retain the effective measurement
snapshots; this API does not infer them from partial ISP parameter buffers.
A library test checks selection with differing configuration metadata and full
destination preservation on missing/duplicate associations. This is a software
association guarantee, not proof of physical sensor/ISP application timing.

## Physical-light measurement scheduling

`awb_measurement_schedule::configure` reconstructs `ConfigHwParaTimeShare`
(ELF 0xc9240). It advances/wraps the configured group, publishes physical light
indices and the mode signature, resets rotated-YUV slots, and copies selected calibrated
UV/XY/YUV regions into the 1204-byte SDK measurement record. Sentinel 15 leaves
its physical slot represented without copying a light. Detection overrides,
startup selector defaults and untouched trailing name/configuration bytes match
the native writes. Checked invalid groups, names and referenced regions are
rejected before the staged record is committed.

`mise run camera:rust:awb-measurement-schedule` compares all output bytes for
360 cases against the original ARM function, then replays host and ARM Rust.
It checks unchanged calibration/strategy input, one to four groups, zero to four
physical lights and region capacities, sentinels, rotated-YUV selection, startup/wrap and
all three detection-override states. A library regression checks a late invalid
light cannot leave a partially modified configuration.
[Measurement scheduling report](awb-measurement-schedule-equivalence.json).

Startup currently configures AE/histogram measurements only; AWB measurement
collection remains disabled. This scheduling port takes explicit calibrated
region records. IQ-to-region conversion, initial complete AWB measurement
assembly, early FAST configuration and the outer reconfiguration decision must
be connected before enabling live AWB. The existing fixed-WB camera command is
unchanged. This explains why a working gain algorithm alone cannot yet consume
live AWB statistics.


## Calibrated XY and rotated-YUV measurement regions

`awb_measurement_regions` reconstructs `JsonXyParaFixed3` (ELF 0xc8254)
and `JsonRtYuvParaFixed2` (ELF 0xc90d4). XY uses native signed Q10 rounding,
16-bit narrowing/sign extension, and preserves the two small-region ranges.
Rotated-YUV retains the original positive Q4 conversion, narrow wrapping line
vector subtraction, direct distance byte and preserved final padding byte.
Nonfinite/overflowing intermediate inputs are rejected before either output
record is changed.

`awb_calibration::MeasurementRegions::from_value` loads each selected scene
light's XY normal/big rectangles and rotated-YUV thresholds/line/distance into
these records. Missing or incorrectly sized arrays and inconsistent light
counts fail explicitly. The table layouts are rotated-YUV **32 bytes**, UV
polygon **36 bytes**, and XY **48 bytes**; scheduling API names now reflect
these SDK types. The previous byte-level scheduler tests already checked the
correct offsets, but its initial field names did not describe those types
correctly.

`mise run camera:rust:awb-measurement-regions` compares the complete records
with the original functions for all seven pinned SC3336 lights and 256 seeded
cases, including signed rounding boundaries, narrowing, negative inputs and
preserved fields. An additional case passes the actual selected IQ object
through the loader and compares all seven output pairs. Host and ARM replay
are required. [Region conversion report](awb-measurement-regions-equivalence.json).

UV polygon construction, full measurement startup assembly, early FAST
configuration and the outer update policy remain open. No live AWB enable or
color-accuracy claim follows from this conversion checkpoint.

## UV polygon calibration conversion

`awb_measurement_regions::uv` reconstructs the inline polygon loop in
`UpdateAwbCalibV2Para` (ELF 0xc240e–0xc24d2). Four Q4 U/V vertices become five
by repeating the first vertex. Each edge stores a signed Q10 inverse slope;
horizontal edges use the original `0x3ffff` sentinel. The instructions promote
the coordinate rounding and final slope rounding to double precision; the
Rust implementation preserves those promotions and native narrowing. Invalid
nonfinite/overflowing intermediate inputs leave the destination unchanged.

`MeasurementRegions::from_value` now loads UV polygons as well as XY and
rotated-YUV regions for every calibrated light. This supersedes the preceding
checkpoint's separate-UV limitation. `mise run camera:rust:awb-measurement-uv`
compares all 36 bytes for seven pinned SC3336 lights and 400 seeded cases,
including horizontal/closing edges, negative coordinates, narrowing and
rounding boundaries; it also checks all seven polygons through the IQ loader.
The task replays host and ARM Rust and reruns the XY/rotated-YUV loader suite.
[UV polygon report](awb-measurement-uv-equivalence.json).

The oracle executes the original instruction slice with explicitly seeded
registers, stack and calibration pointers, stopping before adjacent XY
conversion. It checks that calibration/source records remain unchanged; this
is not a full calibration-update initializer comparison. All three region
tables are now available, but complete measurement-record assembly (geometry,
selectors, transforms, thresholds, weights and initial group/FAST policy) and
live AWB statistics enable remain unfinished.

## Measurement color transforms

`awb_measurement_transforms` reconstructs `JsonXyParaFixed1` (ELF 0xc8210)
and `JsonRtYuvParaFixed1` (ELF 0xc9050), including their original fixed-point
helper behavior. RGB-to-XY uses unsigned Q12 weights masked to twelve bits and
signed Q12 rotation coefficients. Thus the native weight conversion maps 1.0
to zero rather than saturating to 4095; Rust preserves this behavior. The
rotated-YUV 3×4 transform uses signed Q9 coefficients and Q4 offsets; the last
row of the supplied 4×4 matrix is not consumed by the numerical converter.
Both converters stage output and reject nonfinite/overflowing intermediates.

`MeasurementTransforms::from_value` loads the selected scene's complete matrix
arrays and validates their shape. `mise run camera:rust:awb-measurement-transforms`
compares both 24-byte records for the pinned IQ scene and 256 seeded cases,
then checks the same scene through the IQ loader, on host and ARM. Original
native fixed-point helper bodies execute in the oracle. Signed half-step
rounding, wrapping and endpoint weight behavior are covered.
[Measurement transform report](awb-measurement-transforms-equivalence.json).
The full startup record still requires window/downsampling, threshold selection,
flags/weights and the initial group/FAST policy. This does not enable live AWB.

## Measurement window, downsampling and count geometry

`awb_measurement_geometry::derive` reconstructs the geometry portion of
`AwbPrepareV32`: full-frame/fixed fractional window selection and validation,
4×4/8×8 sampling, the native width-greater-than-2336 override to 8×8, optional
four-window conversion, sampled dimensions and both derived count thresholds.
The probability count threshold uses the native integer division/multiplication
order before conversion to float. The luma-weight enable threshold uses the
separate float geometry expression; these are distinct quantities.

`MeasurementGeometry::from_value` reads main-window mode, downscale mode,
`probCalcWp.wpNumPercTh` and
`wpDiffLumaWeight.wpDiffWeiEnableTh.wpDiffWeiNoTh`. Active ISP dimensions and
sample scale stay explicit runtime inputs. Additional windows remain explicit;
the v32 calibration scene does not contain the older `multiWindow` object.
`Geometry::apply` writes the SDK window/downscale fields and only writes extra
window fields when supplied, preserving all unrelated bytes.

`mise run camera:rust:awb-measurement-geometry` compares 256 geometry cases plus
one actual SC3336 IQ-loader case with native prepare through normal return.
It covers width-boundary behavior, cropped/rejected windows, downsample modes,
extra windows and count factors on host and ARM. Calibration update is an
explicit success boundary and preconfigured context bypasses preceding input
selector/bit-depth setup. Logging and integer division are explicit adapters;
this is not complete prepare initialization. Positive u16 dimensions and
nonoverflowing signed count arithmetic define the checked input domain.
[Geometry report](awb-measurement-geometry-equivalence.json).

Window/downsampling and count geometry now join the available region and
transform setup. Threshold-table interpolation, flags/weights, input selection,
initial group/FAST policy and whole-record assembly remain unfinished; live AWB
is still disabled.

## Brightness-dependent channel limits

`awb_measurement_limits::Limits::apply` reconstructs the eight channel-limit
interpolations and change detection inside `ReconfigHwParaV32` (ELF
0xc43c4–0xc45f8). Native order is R max/min, G max/min, B max/min and Y max/min.
The IQ loader scales every limit table by 16 before interpolation, validates
shared lengths/strictly increasing knots, and retains brightness as an explicit
runtime u32. Interpolated values are promoted to double for +0.5 rounding,
converted to unsigned and narrowed to 16 bits. Unrelated SDK bytes remain
unchanged; any checked error preserves the complete record.

`mise run camera:rust:awb-measurement-limits` compares 256 seeded cases and one
actual SC3336 IQ-loader case against the original instruction slice, including
eight original interpolation calls. Whole-record preservation and the native
unchanged/changed flag are checked; 52 cases retain identical thresholds.
Endpoint/interior samples, one-to-five-point tables, negative and narrowing
values are included. Host and ARM replay are required.
[Channel limit report](awb-measurement-limits-equivalence.json).

The oracle starts after the group/update gate and input-selector checks and
stops before luma-weight configuration. This closes limit selection, not the
outer update policy or complete hardware reconfiguration. Luma/block weighting,
input selection, initial group/FAST setup and whole-record assembly remain
unfinished; automatic WB is still disabled in the live camera command.

## Startup input source and bit depth

`awb_input_selection` reconstructs startup RawFixed/RawAuto/BayerNR/DRC source
selection plus `calcInputBitIs12Bit` (ELF 0xc1214) and
`calcInputRightShift212Bit` (ELF 0xc124e). Linear raw modes select frame zero;
HDR raw startup uses the configured frame. BayerNR/DRC select their pipeline
stage directly. DRC forces the existing LSC-bypass flag on; other sources
preserve that flag. Input-bit and right-shift decisions use the optional BLC
pre-gain and working mode. The original ordered `gain > 1` test treats NaN as
not high gain; Ghidra's apparent `gain <= 1` alternative would mis-handle it.
The Rust implementation follows executed instructions, with a regression test.

`MeasurementInput::from_value` loads the selected scene's `rawSelectPara` and
rejects unknown source names. The SC3336 scene selects BayerNR. Native helper
behavior and complete SDK record preservation are compared across 980 cases
plus one actual IQ-loader case by `mise run camera:rust:awb-input-selection`,
on host and ARM. Sources, raw selectors, linear/HDR mode ranges, absent/unity/
high BLC pre-gain, infinity and NaN are covered. The startup oracle runs native
prepare through apply-position publication, with calibration update an explicit
success boundary and geometry following the stop point.
[Input selection report](awb-input-selection-equivalence.json).

Checked startup rejects unsupported mode ranges and invalid HDR raw frames
before modifying the record. Exposure-dependent RawAuto reconfiguration is
still separate. Live AWB remains disabled pending weighting, initial group/FAST
policy, whole-record assembly and runtime integration.

## Complete luma-weight reconfiguration

`awb_measurement_weights::apply` reconstructs full `ReconfigLumaWeight` (ELF
0xc2c88) through its normal return, including `CalWeight` (0xc829a). It preserves
the first-three-frame and disabled gates, signed wrapping histogram sums,
preferred-bin count/brightness gates, ratio interpolation at each calibration
level, brightness interpolation and nine-byte weight quantization. Ratio spans
below native double `1e-5` retain the lower row. Temporal damping uses the
original FMA order and double final rounding. The returned flag means the
damped bytes equal the current target, not that the preceding output bytes
were unchanged. Histogram region selection resets even on the disabled path.
All checked errors preserve both the SDK record and the persistent float cache.

`MeasurementWeighting::from_value` loads the selected scene's luma levels,
ratio tables, preferred bins, cutoff, block-enable/weights and luma Y positions.
The loader retains startup fields for later whole-record assembly; loading it
does not itself enable measurement weighting. The runtime adapter binds the
loaded preferred bins/cutoff and takes frame, histogram, brightness, derived
minimum count and damping from the session.

`mise run camera:rust:awb-measurement-weights` compares 192 seeded calls plus
five SC3336 IQ-loader cases on host and ARM. The full original function executes
its numerical interpolation, ratio logic and FMA damping, with allocation and
memory operations as explicit adapters. Every SDK byte and float-cache word,
plus the target-reached flag, is compared; unrelated context/cache bytes must
remain unchanged. Cases cover disabled/startup/fallback behavior, zero-count
histograms, close ratio knots, one to four levels and damping endpoints.
[Complete weighting report](awb-measurement-weights-equivalence.json).

The pinned IQ disables luma weighting. Its five exercised loader cases
explicitly enable the record flags so the calibration logic is tested rather
than bypassed; the actual scene/camera setting is unchanged. Exclusion-region
include weights (`ConfigIncludeWei`) are a different function and remain open.
Whole-record startup assembly, initial group/FAST setup and live AWB integration
also remain unfinished. This closes the luma-weight calculation rather than
claiming a live automatic-WB camera run.

## Extra-region configuration and include weights

`MeasurementExclusions` now loads all seven `extraWpRange` entries, including
UV/XY domain, signed coordinates, source mode and weight curves. Its static
initializer constructs the zero-based SDK region records with native exclusion
flags and the first four physical measurement enables. Static region assembly
still needs verification as part of the complete startup record.

`awb_measurement_exclusions::apply_weights` reconstructs full `ConfigIncludeWei`
(ELF 0xc1d78), including seven interpolated weights, ×64 conversion, double
rounding and clamp to 63. A mode-3 entry reuses the preceding interpolated
mode-1 value, matching native rather than evaluating its own curve. If the
first entry is mode 3, native reads an uninitialized stack float; Rust rejects
that configuration atomically. All seven entries in the pinned SC3336 scene
are mode 1. This is distinct from the existing prepared-gain Exclusion-layout
hazard documented earlier.

`mise run camera:rust:awb-measurement-exclusions` compares the complete native
function through return in 128 seeded cases plus one actual IQ-loader case,
on host and ARM. Every SDK byte and unchanged calibration input is compared.
Cases include inherited mode-3 values, curve interpolation/endpoints, negative
weights and saturation. [Include-weight report](awb-measurement-exclusions-equivalence.json).
The comparison verifies include weights, not static region initialization or
whole startup composition.

The assembly audit now accounts for calibrated light regions, transforms,
geometry, input flags, limits, luma weights and extra-region data. Remaining
startup work includes the FAST initial light selection enabled by the actual
SC3336 scene, control/weight field composition and BLC/pre-gain metadata
binding. The existing time-share scheduler is not a substitute for native FAST
startup. Live AWB remains disabled while these pieces are connected.

## FAST startup light configuration

`awb_fast_configuration::configure` reconstructs full `ConfigHwParaFstFF`
(ELF 0xc94a4), including the original stable descending sort, adjacent-gap
selection, balanced/paired-gap grouping, calibrated normal/big bounding-window
merge and physical-slot compaction. It preserves native integer division and
three-entry group layout. FAST clears the rotated-YUV slots, publishes the
`FASTAWBACT` signature and physical indices, and leaves other metadata alone.
Manual mode copies the four integer normal/big windows while preserving their
small-region tail; automatic mode clears all four full XY records first.
Checked errors stage the record rather than partially modifying it.

`FastStart::from_value` loads `earlierAwbAct`; `apply` consumes the scene's
already converted XY records and explicit calibrated valid-light count. Disabled
FAST returns an explicit checked error so the caller must choose the normal
scheduler instead. The actual SC3336 scene enables automatic FAST. Its native
calibrated-light groups are `[4,3]`, `[2]`, `[6,1]`, `[0,5]`, producing four
physical measurement windows. These are group memberships, not GPIO/pin IDs.

`mise run camera:rust:awb-fast-configuration` compares full native function
returns and all 1204 SDK bytes in 258 host/ARM cases. A hook reads the original
group array before merge so matching overlapping bounds cannot hide incorrect
grouping. Coverage includes 163 balanced, 57 paired-gap and 38 manual calls,
valid-light-prefix compaction and preservation of unrelated input/calibration
bytes. Two cases join real SC3336 region conversion and scene loading (actual
automatic mode, plus an explicit manual variant).
[FAST configuration report](awb-fast-configuration-equivalence.json).

The automatic checked input domain is four to seven calibrated lights; memory,
strings, allocation, division and logging are explicit oracle adapters while
native sorting/grouping/merging bodies execute. This closes FAST selection,
not complete initialization. Next is binding these verified pieces into the
whole measurement record, including controls, weights and BLC/pre-gain metadata,
then connecting the live statistics and gain-publication path. Live automatic WB
remains disabled until that integration is tested.

## Post-assembly binding and first complete measurement candidate

`awb_measurement_binding::bind_gain1_linear` reconstructs the actual camera's
linear BayerNR/Gain1/no-OTP path through `AwbReCfgPregnBlc` (ELF 0xc5158).
It binds inverse gains, software pre-gain metadata, AWB/primary BLC contributions
and the overexposure threshold, preserving FMA and rounding order. Remosaic
inverse gains and optional software pre-gains are explicit inputs. Selected AWB
BLC offsets are explicit values; whole-scene assembly selects them at ISO times
optical-black pre-gain. Checked errors stage the complete measurement record.

`mise run camera:rust:awb-measurement-binding` compares full native returns and
all SDK bytes across 129 host/ARM cases. Native calibration interpolation runs
on constant tables supplying the selected offsets. Logging is an explicit
adapter. Other input/working-mode/apply-position and OTP branches remain open.
The current camera checkpoint binds BLC `[256,256,256,256]`, inverse gains
`[256,256,256]` and threshold **238**; leaving these fields zero would not match
upstream's post-initialization measurement configuration.
[Binding comparison](awb-measurement-binding-equivalence.json).

`initial_parameters::assemble_with_awb` now composes a complete candidate for
the selected FAST linear scene: initial controls, converted regions/transforms,
FAST grouping, weights, extra regions, first-entry channel limits, zero-sampled
include weights, geometry/input flags and post-assembly binding. It returns the
SDK snapshot together with the serialized ISP parameters and a scope report.
The primary BLC selection helper is shared with existing startup assembly;
known base and AE-only parameter hashes remain identical after that refactor.

Offline generation (new output paths required):

```sh
camera-probe make-initial-parameters IQ.json OUT.bin --awb-measurements SDK.bin SAMPLE_SCALE
```

Sample scale stays an explicit input. The local SC3336 candidate uses 1; its
value must be bound to the live session before count thresholds are qualified.
This command only writes files. It does not submit the payload, start capture,
change boot configuration or enable automatic WB. The existing first-frame and
automatic-exposure commands retain their established AE-only measurement setup.

`mise run camera:rust:awb-startup-assembly` verifies host/ARM deterministic
composition, payload dimensions, key bindings and isolation: compared with the
AE-only record, only AWB masks and the AWB measurement block change. AE and the
fixed calibrated WB gain block are byte-identical. The candidate is 11145 bytes
and its SDK snapshot is 1204 bytes. Full original startup-composition comparison
and hardware validation remain pending; component equivalence and these
integration checks do not prove those broader claims.
[Assembly validation](awb-startup-assembly-validation.json).

Local generated files are under ignored
`dist/reverse-engineering/awb-assembly-2026-10-27/`. No IQ source or binary
calibration payload is committed. Normal time-share/HDR/OTP composition and
persistent AWB/live gain publication still remain outside this candidate.


## First physical AWB measurement/translation checkpoint

The separate `awb-measurement-frame-sc3336` command now submits the assembled
FAST/linear candidate while retaining fixed calibrated white balance. It saves
the actual SDK snapshot and performs exact initial-ID association before
translating the last received statistics frame. It never substitutes the image
sequence or most-recent configuration when an ID is missing. The saved SDK
frame and JSON are diagnostics; normalized per-region gain ratios are not a
persistent automatic-WB result.

On the real SC3336, valid AWB statistics and all 225 grid cells were received
without a vendor camera process. A controlled 30 ms/8× exposure-only variant
produced nonzero measurements in all four FAST windows. The full 7680-byte
translation of captured statistics matched the original ARM translator exactly
at frame 7 / initial parameter ID 0. The new captured-data comparison script
uses the original object-access harness with an explicitly zeroed destination
frame; existing synthetic-reference behavior is unchanged by default.
See [hardware procedure and evidence](HARDWARE-TEST.md#physical-awb-checkpoint--2026-10-27-0031-dev).

This supersedes the preceding candidate's hardware-pending status for physical
measurement collection and translation only. Whole original startup-composition
comparison, persistent controller initialization/preprocessing, gain publication,
convergence/color qualification and vendor-free cold startup remain open.
Private scenes, complete statistics, SDK payloads and IQ variants remain local.

## Captured-data measurement checkpoint

`awb-measurement-frame-sc3336` now exercises the composed measurement payload
on the real camera with fixed white balance, preserving the exact SDK snapshot.
It translates received statistics only after matching the driver's parameter ID
to the single initial snapshot. Diagnostic per-region normalized gain ratios
are not a persistent AWB result or a hardware gain update.

Valid AWB flags, a 225-cell grid and nonzero measurements from all four FAST
windows were observed on SC3336 with the controlled 30 ms/8× startup variant.
All 7680 bytes of the resulting SDK statistics frame matched original ARM
translation of the actual captured payload/snapshot. The zero-destination option
in the reference harness is explicit; existing synthetic comparisons retain
their prior seeded destinations by default.
[Physical procedure, artifacts and limits](HARDWARE-TEST.md#physical-awb-statistics-capture--2026-10-27).

This establishes measurement collection and translation for this checkpoint.
Whole native startup composition, persistent preprocessing/controller state,
live gain publication, convergence/color qualification and vendor-free cold
startup remain open. Private images, statistics, SDK payloads and the exposure
IQ variant are not committed.


### Fresh automatic controller state (2026-10-27)

`Scene::initial_gain_state::<CAP>()` now constructs the gain controller from
empty histories and the calibrated first-frame reference gain. It computes
initial CCT/CCRI with the reconstructed native routine and rejects insufficient
history capacity. This replaces the seeded test state as the starting point for
future real-data controller execution; it does not activate live AWB.

`mise run camera:rust:awb-initial-gain-state` executes the original
`InitinalSwResParaCom2` to completion with explicit allocation/logging adapters.
For each of the seven pinned SC3336 light sources, it compares starting
current/previous gains, temperature, dispatcher fields, empty history heads,
and five scalar diagnostics. Host and ARM Rust match with zero differences;
see `awb-initial-gain-state-equivalence.json`. This is a projection of fresh
automatic, non-bypass initialization with remosaic disabled, not a comparison
of every context byte or complete camera startup. Calibration loading is
verified separately. Saved-site loading, numeric preprocessing and measurement
cache initialization remain required session work before live gain publication.

The latest physical text capture was saved locally as
`dist/reverse-engineering/hardware-2026-10-27/ss-20261027-awb-measurement-05.png`
and opened for inspection. The raw frame and private scene stay outside Git.
It uses 30 ms / 8x exposure and fixed calibrated white balance; readable text
does not establish automatic white-balance operation or color accuracy.


### Fresh measurement caches with captured data (2026-10-27)

`awb_preparation::State::fresh` now initializes caller-owned cache buffers from
the native zeroed-context / initial-software-result state. It validates lengths
before clearing any buffer. Initial active-light count remains an explicit
calibrated strategy input; FAST preparation selects the active prefix later.

`awb-captured-preparation.py TRANSLATED.bin --arm --report REPORT.json` replays
an already-associated private translated capture. It executes the original
software-result initializer and then the complete original
`PrepareMeasureResult`, comparing all 4,886 serialized bytes of preparation
state both before and after processing. Allocation/logging/string operations
are explicit adapters; integer-to-float conversion executes the pinned GCC ARM
runtime. The test supplies calibrated strategy bindings explicitly. It covers
this pinned seven-light scene's four FAST windows, group -1 and EXCLUDE extra
regions, rather than claiming arbitrary calibration or complete startup.

Both physical captures 02 (dark) and 03 (30 ms / 8x) match with zero differences
on host and ARM Rust. Their translation/parameter-association checks previously
passed independently. The comparisons include mode names, stability history,
seen flags, light records/counts, pre-gain, the 225-cell grid, exclusions and
histograms. Private inputs and detailed replay reports remain under ignored
`dist/reverse-engineering/hardware-2026-10-27/`.

Reproduce after building host numeric-fixture and `mise run camera:rust:arm`:

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python \
  reverse-engineering/rkaiq/scripts/awb-captured-preparation.py \
  dist/reverse-engineering/hardware-2026-10-27/ss-20261027-awb-measurement-03.awb-translated.bin \
  --arm --report dist/reverse-engineering/hardware-2026-10-27/ss-20261027-awb-measurement-03.preparation-comparison.json
```

This closes fresh measurement-cache initialization and captured-data preparation,
not the remaining numerical session setup or live gain publication. No hardware
settings were changed by these offline replays. All 85 library tests and the
no-default-features build pass after this change.


### Joined first-frame gain calculation and physical gain step (2026-10-27)

`awb-captured-gain.py` now runs the existing production numerical preprocessing,
metadata/history classification, fresh measurement preparation and complete
scene-configured gain wrapper together on one captured FAST frame. It requires
explicit input dimensions, sample scale and ISO. The current replay follows the
native missing-exposure-metadata branch (calibrated brightness fallback 2048),
with an absent saved-site reference and no software pre-gain override. These
are diagnostic runtime conditions, not a completed live metadata binding.

A new physical measurement capture 06 was replayed on the actual Luckfox ARM
CPU and on the host; their complete diagnostic JSON matched. The computed
first-frame gain was `[1.4864674, 1, 1, 1.7921165]`, compared with calibrated
startup `[1.52182, 1, 1, 1.71481]`. The replay used explicit sample scale 1 and
ISO 400; scale provenance and real exposure metadata still need binding for
continuous operation. The joined full replay has not yet been compared with a
single complete native startup/controller execution; component equivalence
checks and host/board agreement establish narrower evidence.

`camera-probe awb-gain-frame-sc3336` accepts an explicit four-channel diagnostic
gain, applies the verified ISP serializer to the otherwise unchanged initial
parameters, and captures measurements/image. Gain values must be finite,
positive and within the ISP Q8 range. Existing measurement-only/fixed/AE entry
points retain their behavior. On the real board, submitting capture 06's gain
produced `ss-20261027-awb-gain-step-01`: successful NV12 image and statistics,
no cleanup errors, readable text on visual inspection. Only initial parameter
bytes 4649 and 4651 changed relative to measurement capture 06 (the red/blue
gain words). Both captures' full 7,680-byte translations match original ARM
instructions with zero differences.

Reproduce the calculation (push the ARM numeric-fixture under the given name
first; the optional ADB comparison opens no camera devices):

```sh
uv run --python 3.13 python reverse-engineering/rkaiq/scripts/awb-captured-gain.py \
  .tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json \
  dist/reverse-engineering/hardware-2026-10-27/ss-20261027-awb-measurement-06.awb-translated.bin \
  --sample-scale 1 --iso 400 --width 2304 --height 1296 \
  --adb 0a523b8b23110ffc
```

The physical submission command on the board was:

```sh
/tmp/shieldsigner-camera-probe-awb-gain-step awb-gain-frame-sc3336 \
  /tmp/shieldsigner-pipeline-sof.json /tmp/sc3336-awb-30ms-8x.private.json \
  /dev/video20 /dev/video11 /tmp/ss-20261027-awb-gain-step-01 /dev/video19 \
  1 1.4864673614501953 1 1 1.7921165227890015
```

Use a new output basename for another capture. These steps prove a bounded
capture → Rust calculation on board → explicit ISP gain submission → capture
path. They do not enable persistent automatic WB. Continuous state ownership,
frame/parameter association during updates, exposure metadata and live gain
publication remain the next work. The image is an inspection aid, not a color
accuracy qualification. Hardware stayed at the requested 30 ms / 8x exposure;
no boot/kernel/service changes occurred. The 85 library tests and simulated
first-frame sequence checks also pass.


### Persistent session and first live AE + AWB runs (2026-10-27)

`awb_session::Session` now owns the numerical state, brightness metadata/history,
measurement caches, gain-controller histories and per-light results across
frames. `process` stages the entire mutable state and commits only on success.
Runtime ISO, exposure metadata, update requests and optional saved-site reference
remain explicit inputs. The numerical and gain dispatch counters share one
logical counter across ready/interval-skip transitions. The supported session
currently consumes four-window FAST linear translated records.

The replay fixture now calls this production session. Its first result exactly
matches the previous independently exercised first-frame replay. Sixty-four
updates of a captured frame match between the host and actual Luckfox CPU and
settle to a stable gain. A second 64-update replay injects a nonfinite pre-gain
after numerical preprocessing with a deliberately different exposure input;
every rejection leaves subsequent results identical to a clean reference
session on both machines. These are repeated-input state/rollback tests, not
64 distinct physical captures. Run with `awb-captured-gain.py --repeat 64
--check-rollback` plus the explicit runtime/file arguments from the previous
section.

`camera-probe auto-awb-frame-sc3336` now connects this session to the existing
single AE/sensor/parameter owner. The owner translates AWB with the exact
statistics parameter ID, registers the unchanged measurement SDK for every
successfully submitted gain-only parameter ID, and retains AWB gains by their
statistics frame. When several pending frames are released together, each
submission therefore receives its own frame's gain rather than the newest
calculation. AE digital gain and WB gain use the existing ordered serializer
and persistent parameter queue. Saved final translated data comes from the
owner's last processed AWB frame, not an initial-ID assumption.

Two physical live runs (`ss-20261027-live-awb-01` and `-02`) succeeded. Each
processed 22 AE/AWB frames, retained 22 registered parameter IDs, reached AWB
countdown zero and saved a 460,800-byte 640x480 NV12 image. Every observed AWB
parameter ID was registered. Final statistics and saved translation both name
frame 31 / parameter ID 30. Both full 7,680-byte translations match original
ARM instructions with zero differences. The final gains were approximately
`[1.42712, 1, 1, 1.90399]` and `[1.42723, 1, 1, 1.90639]`. Both previews show
readable text; this does not qualify color accuracy. See the committed
`awb-live-hardware-validation.json` for bounded evidence and limitations.
Private images, statistics, profiles and detailed logs remain ignored locally.

The actual command was:

```sh
/tmp/shieldsigner-camera-probe-live-awb auto-awb-frame-sc3336 \
  /tmp/shieldsigner-pipeline-sof.json /tmp/sc3336-awb-30ms-8x.private.json \
  /dev/video20 /dev/video11 /tmp/ss-20261027-live-awb-02 /dev/video19 1 400
```

Choose a fresh output basename for another run. The command starts with the
profile exposure, then enables the reconstructed AE and AWB gain loops for a
bounded capture. It makes no boot/kernel/service changes. An old-build archive
was copied back and SHA-256 verified before removing obsolete temporary board
binaries to free its 22.5 MB `/tmp`; all camera captures remain preserved.

**Remaining work:** AWB currently uses the recovered calibrated missing-exposure
fallback (brightness 2048), explicit ISO 400 and sample scale 1. Native exposure
metadata and sample-scale provenance still require binding. The measurement
configuration remains fixed FAST startup; normal scheduling and adaptive
measurement reconfiguration are not connected. Physical frame latency,
vendor-free cold startup, full joined native controller equivalence and a
continuous application camera service remain unqualified. This is a functioning
live diagnostic iteration, not the completed replacement library. The 85
library tests, no-default-features build, ARM build and existing simulated
first-frame/AE queue checks pass.


### Same-frame AE brightness binding (2026-10-27)

The live owner now supplies AWB's exposure-luma input from
`runtime.session.preprocessing.normalized_brightness` after processing the same
statistics frame through AE. It rejects a mismatched AE pre-result frame before
AWB processing. The offline replay still deliberately supports the missing-AE
fallback; the live path no longer uses that fallback.

The original binding is corroborated end to end:

- `AecGetPreResults` (ELF 0xb1cb8) copies context `+0x251c` into result word 12.
  This is the normalized-brightness field already compared with Rust's standard
  AE preprocessing in the full native AE session tests.
- `AePreProcess` passes its output `+4` to `AecGetPreResults`, placing that word
  at output byte offset `0x34`.
- `awbProcessing` (ELF 0x10f848) obtains the AE pre-result through its proxy and
  binds AWB context `+0x4c` to the returned result `+0x34`.
- `AwbPreProcV32` reads source element zero for this linear profile and multiplies
  by 1000, as the existing Rust numerical implementation does. The unused HDR
  element is not synthesized from a second image measurement.

The native AE session harness now additionally verifies output `+0x34` against
context `+0x251c` after each actual `AecGetPreResults` call. All 128 frames across
8 complete native AE sessions pass, along with the existing host/ARM Rust state
comparisons (zero differences). The wrapper's proxy/pointer mapping is static
Ghidra evidence, rather than a claim of full native AWB wrapper execution.

Physical live capture 03 passed with 22 AE/AWB updates. AWB brightness changed
from about 423.893 to 741.447 while AE adjusted exposure, instead of staying at
fallback 2048. Final gain was approximately `[1.429826, 1, 1, 1.903011]`.
The image remains readable. Its final frame 31 / parameter ID 30 translation
again matches all 7,680 bytes of the original routine. The same command and
runtime inputs as live captures 01/02 apply, with output basename
`/tmp/ss-20261027-live-awb-03`. Per-run executable hashes and source conditions
are recorded in `awb-live-hardware-validation.json`; earlier fallback runs
retain their original evidence rather than being relabeled.

ISO is still an explicit input, sample-scale provenance remains unresolved, and
measurement configuration remains fixed FAST startup. Binding those runtime
inputs and native measurement reconfiguration remains required; this change
does not establish complete startup/controller equivalence or cold-boot
independence. The 85 library tests and simulated capture/queue scenarios pass.


### Frame-associated dynamic ISO (2026-10-27)

`awb_exposure::linear_iso` now reconstructs the actual linear exposure-gain
binding inside `awbProcessing` (ELF 0x10f848). Each of analogue, sensor-digital
and ISP gain is accepted when >= 1, otherwise replaced with unity. Native f32
multiplications run in that order, followed by a 50x scale. The native scale
literal is 50.0, verified from the pinned library; this is ISO, not a unitless
gain. Rust rejects nonfinite input or overflow rather than passing them into
calibrated interpolation.

`mise run camera:rust:awb-linear-iso` executes the original wrapper from entry
to its completed linear ISO store (mapped checkpoint 0x11fa14, context +0x5c).
AE proxies are absent, logging is an explicit adapter, and execution stops
before statistics/controller/proxy processing. All 340 finite cases match on
host and ARM Rust; four checked nonfinite/overflow inputs are rejected. This
is prefix equivalence, not a complete wrapper claim. The older common-tail
reference fixture also now seeds ISO at +0x5c rather than the unused +0x58;
its existing 256 host/ARM comparisons still pass. The separate gain-adjustment
component already uses +0x5c.

The live owner reads real gain fields +4/+8/+12 from the exact exposure record
used by same-frame AE preprocessing and derives ISO with this helper. It no
longer accepts a manual ISO argument. The offline replay still accepts an
explicit diagnostic ISO input. The current live command is:

```sh
/tmp/shieldsigner-camera-probe-live-awb auto-awb-frame-sc3336 \
  /tmp/shieldsigner-pipeline-sof.json /tmp/sc3336-awb-30ms-8x.private.json \
  /dev/video20 /dev/video11 /tmp/ss-20261027-live-awb-04 /dev/video19 1
```

Earlier example commands containing trailing `400` describe the older builds
that produced their named captures. Use a fresh basename when running current
source. Camera capture 04 passed with 22 AE/AWB updates, dynamic ISO between
212.5 and 487.109375 (last 288.28125), final gain approximately
`[1.43155, 1, 1, 1.89875]`, and readable image output. Final frame 31 / parameter
ID 30 again matches all 7,680 translated bytes of original ARM code. Registered
parameter IDs and the saved raw/translated frame headers agree. The committed
hardware validation retains each run's own executable hash and runtime sources.

The source exposure record represents scheduler-associated settings, not proven
physical sensor latency. Fixed FAST measurement configuration, sample-scale
provenance, normal/adaptive measurement scheduling and continuous application
integration remain work. All 85 library tests, the no-default-features build,
ARM build and simulated capture/AE queue scenarios pass for this change.


### Normal time-share configuration and registered SDK snapshots (2026-10-27)

The live path now transitions from FAST startup to normal seven-light time
sharing. Native `ReconfigHwParaV32` calls `ConfigHwParaTimeShare` after a pending
measurement update; it does not keep FAST active until countdown zero. The
zero-reserved pinned strategy schedules physical lights `[0,1,2,3]` and
`[4,5,6]`. `awb_measurement_schedule::initialize` reconstructs fresh
`AwbTimeShareInit` for this ordinary zero-reserved policy. All 164 table bytes
match original ARM for 25 bounded combinations on host and ARM. Nonzero
reserved-light policy and more than four groups remain outside this factory.
The complete existing time-share record converter also still matches all
1,204 bytes in its 360 native comparisons.

`awb_session::Session` accepts FAST and normal records, uses the calibrated
normal group count (two here), and can configure the next normal measurement
record from the loaded UV/XY/rotated-YUV regions. The owner supplies an opaque
stable normal-cohort signature, rather than a wall-clock timestamp. That is
sufficient for this pinned profile's constant limit/weight tables; variable
configuration epochs and the remaining outer reconfiguration decision policy
are not yet connected. A pending normal record is retained by its source frame,
including when several statistics frames are released together. The owner
combines that record with AE/WB gain updates in one queued parameter batch.

Every successful QBUF registers both its full effective parameter snapshot and
its own SDK measurement record. Incoming AWB uses its exact driver-reported ID
against that history. The initial SDK is no longer reused to decode later
normal configurations. The final capture now also writes
`OUT.awb-effective-sdk.bin`, corresponding to the saved raw/translated frame;
`OUT.awb-sdk.bin` still records the initial FAST configuration. Use the effective
SDK for native comparisons of the final normal frame.

The first hardware attempt (capture 05) exposed a publication bug: the new
combined path omitted the runtime frame ID and ordinary-batch marker, so kernel
statistics retained ID zero while measurement registers changed. Its process
completed but its AWB interpretation is **not valid evidence**. The private
artifacts carry a `known-invalid.json` annotation and the committed validation
marks the run rejected. The fix shares `mark_runtime_parameter_frame` with the
existing gain-only path, setting both the ordinary high-mask bit and frame ID.

Hardware capture 06 passed after that fix. Its 22 AE/AWB events contain two FAST
frames followed by 20 normal frames spanning both four-light and three-light
groups. The first normal group holds the existing gain with `complete=false`;
normal gain calculation resumes after both groups arrive, with seven active
calibrated lights. Stable final frames hold the gain without recalculation.
Final gain is approximately `[1.437573, 1, 1, 1.833476]`; the saved 640x480 image
has readable text. Final frame 31 / parameter ID 30, using the **effective normal
SDK**, matches all 7,680 bytes of the original translator.

`awb-live-capture-check.py BASE --native-report REPORT.json` verifies changing
parameter IDs, registered IDs, FAST/normal group transitions, incomplete-cohort
holds, final raw header and effective SDK metadata. It accepts capture 06 and
rejects the retained zero-ID regression capture 05. These are complementary
protocol checks: native numerical equivalence alone cannot detect a caller
supplying the wrong configuration under a reused ID.

The live command syntax is unchanged from capture 04; use output basename
`/tmp/ss-20261027-live-awb-06` (or a fresh name). Compare the saved normal frame:

```sh
uv run --python 3.13 --with pyelftools==0.32 --with unicorn==2.1.4 python \
  reverse-engineering/rkaiq/scripts/awb-captured-translation.py \
  dist/reverse-engineering/hardware-2026-10-27/ss-20261027-live-awb-06.stats.raw \
  dist/reverse-engineering/hardware-2026-10-27/ss-20261027-live-awb-06.awb-effective-sdk.bin \
  dist/reverse-engineering/hardware-2026-10-27/ss-20261027-live-awb-06.awb-translated.bin \
  --configuration-id 30
```

Source invariants and remaining limits are retained in the committed hardware
validation. Sample-scale provenance, full variable reconfiguration policy,
physical latency/color qualification, cold startup and continuous application
integration remain work; this is not yet the completed replacement library.


### Single-camera scale and longer live capture (2026-10-27)

The sample-scale provenance is now resolved for this single-camera path.
The original single-camera `create_context` (ELF 0xbd5f4, mapped 0xcd5f4) calls
`AwbInitV32`, then writes **1** to context `+0x369c` and zero to `+0x3698`.
The separate camera-group creator copies a configured value instead. Generic
factory symbols are duplicated across algorithms, so the reference resolves
the single-camera symbol by its pinned entry rather than by name alone.

`awb_session::SINGLE_CAMERA_SAMPLE_SCALE` supplies that value automatically to
the live command. `mise run camera:rust:awb-single-camera-scale` runs the actual
single-camera factory through normal return, with module lookup and AwbInitV32
as explicit successful storage/calibration boundaries. Four initial fill patterns
verify the scale, single/group flag, returned pointer and preservation of all
other context bytes. Host/ARM Rust agree. This does not claim complete native
calibration initialization. The newly inspected single-camera processing
wrapper (ELF 0xbcdb8) also corroborates the existing AE pre-result `+0x34` and
linear analogue/digital/ISP gain bindings used by the live owner.

Current live syntax has **no sample-scale or ISO argument**:

```sh
/tmp/shieldsigner-camera-probe-live-awb auto-awb-frame-sc3336 \
  /tmp/shieldsigner-pipeline-sof.json /tmp/sc3336-awb-30ms-8x.private.json \
  /dev/video20 /dev/video11 /tmp/ss-20261027-live-awb-07 /dev/video19 \
  --frames 96
```

`--frames` is optional, defaults to 33 image dequeues, and accepts 33..96 for this
bounded diagnostic. Old chronological examples describe the binaries that
produced those older captures. Explicit scale inputs remain available for
component/offline experiments and the older measurement-only commands.

Physical capture 07 passed with 96 image dequeues (saved image sequence 95),
64 AE/AWB statistics frames and 62 normal time-share frames across both groups.
Final statistics were frame 94 / parameter ID 93; the final gain held at roughly
`[1.441269, 1, 1, 1.826460]`. The image contains readable text. No vendor camera
processes appeared in the before/after checks. The protocol checker passed,
and all 7,680 translated bytes match original ARM using the effective normal
SDK. Image sequence and statistics frame remain distinct; this does not prove
physical per-frame exposure latency or color accuracy.

The source build, 85 library tests, no-default-features build and simulated
capture/queue checks pass. Captures 01/02 were SHA-256 compared with their local
archives before removing only their temporary board copies to free `/tmp`.
No capture evidence was lost, and no boot/kernel/service changes occurred.

The remaining practical work includes sustained application streaming (current
event/snapshot histories still have bounded diagnostic limits), variable
measurement reconfiguration epochs and cold-start qualification. This longer
run is a checkpoint, not a completed replacement-library claim.


### Rolling snapshot ownership beyond short captures (2026-10-27)

The event owner no longer retains every historical ISP/SDK snapshot until the
128-entry diagnostic limit stops the run. Statistics admission enforces
nondecreasing parameter IDs within one stream epoch. Before publication, the
owner retires entries older than the last admitted parameter watermark, while
pinning exact IDs referenced by queued statistics, the last saved AWB record,
and the most recent submitted snapshot. AE parameter and AWB SDK histories use
the same retention predicate. Unknown or regressing IDs still fail explicitly;
no caller guesses the latest configuration for an older frame.

Successful submission also removes consumed frame-specific pending AWB gain
records. Recent sensor query/write and parameter-queue traces are bounded to
256 records, with the limits disclosed in the final diagnostic JSON. These
lists now mean recent traces rather than complete lifetime histories. The
128-entry snapshot safety cap remains for genuinely unretired/in-flight state;
it is not an arbitrary total-submission limit. This is an owned event-loop
retention policy, not a reconstruction of every native C++ map lifetime detail.

Adapter contract checks now cover retaining old IDs needed by queued statistics,
preserving snapshot payloads, rejecting regressing IDs before changing admitted
queue state, and retaining only the newest 256 diagnostic trace entries. Existing
queue-failure, duplicate-ID, cancellation, single-/multi-plane and startup
checks still pass. The capture checker accepts `--min-submissions 129` to require
actual successful publication past the former lifetime boundary and verify
bounded resident histories/traces.

Current live syntax accepts `--frames 33..3600`; the generic capture warmup
bound is 10,000. The actual hardware command for capture 08 was:

```sh
/tmp/shieldsigner-camera-probe-live-awb auto-awb-frame-sc3336 \
  /tmp/shieldsigner-pipeline-sof.json /tmp/sc3336-awb-30ms-8x.private.json \
  /dev/video20 /dev/video11 /tmp/ss-20261027-live-awb-08 /dev/video19 \
  --frames 600
```

It passed 600 image dequeues, saving image sequence 599, with **400 AE/AWB
statistics events, 399 successful parameter submissions, 398 retired snapshots,
and only two retained snapshots at peak and finish**. Both normal groups were
observed; final gains held around `[1.44263, 1, 1, 1.822668]`. The saved image
has readable text. Final frame 598 / parameter ID 597 matches all 7,680 translated
bytes of original ARM with its saved effective normal SDK. Protocol checking
with `--min-submissions 129` passes. The 85 library tests, no-default-features
build, ARM build and six existing simulated adapter scenarios also pass.

Private capture artifacts and detailed logs stay ignored locally. Temporary
board copies of capture 03 were removed only after comparing every file's
SHA-256 with the local archive. No boot/kernel/service changes occurred.

This removes the short-run ownership barrier. Continuous application frame
delivery, environmental/restart testing, variable measurement epochs and
cold-start qualification remain required work; no whole-process memory or
color/latency qualification is inferred from these bounded-history checks.

## Application frame delivery and graceful owner shutdown (2026-10-27)

The live owner now has an opt-in `stream-sc3336` command and a bounded Unix
socket transport. RGB conversion and delivery run outside capture/3A. A slow
reader is disconnected after an absolute two-second deadline; one queued frame
bounds backlog. The Python adapter matches PiVideoStream's start/read/stop
contract and returns Pillow images. The existing installed Camera wrapper was
exercised by a process-local override; no default app or boot files were edited.

Run 18, using the original full IQ profile, passed two reader sessions, a
consumer stall/reconnect, SIGINT cleanup and final capture checks. It processed
399 AE and AWB statistics frames with 398 parameter submissions and at most
three retained snapshots. Its final frame 597 / parameters ID 595 translates
identically across all 7,680 original ARM output bytes using the saved effective
normal SDK. Run 17 separately passed SIGTERM. Run 15 passed a 900-image bounded
capture with 600 AE/AWB frames and 599 submissions. No color or physical frame
latency equivalence is inferred.

Early integration attempts exposed actual board memory pressure: old test
artifacts occupied most of RAM-backed `/tmp`, and the kernel killed camera or
Python processes. Those attempts are not successful integration evidence.
Archived files were SHA-verified before deleting only our temporary board
copies; fresh outputs now go to SD. Saving PNGs during a timed reader test also
consumed enough CPU/time to overlap the end of a bounded capture, so the test
now saves them after capture. The full application wrapper currently supplies
about 3–4 distinct previews per second; performance still needs work.

Commands, transport format, memory requirements and remaining integration work
are in [HARDWARE-TEST.md](HARDWARE-TEST.md#live-frames-for-the-application-0031-dev-source).
Private images/raw statistics/logs remain ignored. Full UI/QR scanning,
app-owned lifetime, cold-start independence and variable configuration policy
remain required work toward a complete solution.

## Managed application lifetime (2026-10-27)

The application adapter can launch one Rust owner per camera session from an
explicit JSON path configuration, then stop/reap it when Camera stops. Startup
has a readiness acknowledgment after native signal/parent-death setup, and an
exclusive stream-owner lock is acquired before configuring the graph. A second
owner is rejected while the first continues. A Python parent exiting abruptly
causes the native owner to finish through its regular shutdown path.

Repeated hardware iterations covered two Camera sessions, competing-owner
rejection, immediate cancellation before any image, and parent exit without
adapter.stop(). The immediate cancellation initially failed with `No frame
saved`; capture, statistics and AWB now distinguish that explicit cancellation
from absent data during a requested acquisition. They do not manufacture empty
measurement evidence. Normal capture/control failures and cleanup failures
remain errors. See the managed-session instructions in HARDWARE-TEST.md.

This completes the opt-in application-owned lifetime path, not default UI
installation, scanning qualification, cold-start independence or remaining AWB
configuration policy. Test runs and artifacts remain separated from default
application/boot files.

Final-source managed run 22 passes missing-storage rejection, two independent
Camera-owned sessions, competing-owner rejection, immediate cancellation and
parent exit. Both normal sessions pass exact-ID control checks and independent
7,680-byte original ARM translation (zero mismatches); peak retained parameter
snapshots is two. First frames arrive in 0.74–0.76 s and owner stop/reap takes
0.30–0.32 s. The 85 library tests, three Unix transport tests, ARM build,
no-default-features build and six existing simulated adapter scenarios pass.
See `managed-camera-hardware-validation.json`.

## Live AWB without vendor application initialization after reboot

Controlled clean-reboot run 25 now covers the managed AE/AWB application path,
not only the earlier fixed-exposure capture. Both vendor and UI startup were
skipped for that boot with self-restoring, checksum-verified wrappers; camera
kernel drivers were loaded explicitly without Rockit/MCU or vendor userspace.
Two normal application sessions, owner exclusion, early cancellation and parent
exit pass. Both sessions retain at most two parameter snapshots and independently
match all 7,680 original ARM statistics translation bytes. The separate
`clean-reboot-camera-hardware-validation.json` records boot markers, hashes,
normal-group/control checks and scope.

A native-size default and stale V4L2 row stride initially exhausted CMA. The
continuous command now requests VGA explicitly, and explicit geometry changes
clear prior stride/extent fields before S_FMT. The successful final reboot test
required no manually prepared image format. Original startup scripts were
restored and backup hashes verified before capture; normal future boot behavior
is unchanged. This advances vendor-free userspace initialization for the pinned
linear SC3336 profile; physical power-cycle testing, default UI/scan integration,
color/latency qualification and remaining configuration policy are separate work.

## Post-convergence scene-change replay (0.0.32-dev)

A controlled 280-frame replay now exercises the production owned Session after
its startup countdown expires. The application request flag is set only for the
first frame. Stable measurements settle; changed aggregate color ratios wake
the measurement gate, gains move in the expected correction direction, restored
input recovers toward baseline, and a brightness metadata step wakes processing
again. Every stage finishes with 16 frames of held gains. No gain-policy change
was needed for this behavior.

| Controlled stage | Frames | Gain calculations | Final R gain | Final B gain |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 80 | 19 | 1.439914 | 1.817791 |
| R sums ×0.75 / B sums ×1.25 | 80 | 14 | 1.915241 | 1.456267 |
| Restore baseline records | 80 | 14 | 1.443802 | 1.814719 |
| Normalized brightness ×0.35 | 40 | 3 | 1.439914 | 1.817791 |

The color step scales accumulated white-point correction-gain sums inversely,
preserving their counts and configuration identity. These are deliberately
transformed statistics, with controlled brightness/ISO inputs. They establish
session response under those inputs; no physical room-lighting change or
optical scene response is claimed.

Host and the actual Luckfox ARM executable produce identical replay output.
The original ARM IsMeasureResultStable4 executes all 280 persistent gate
transitions independently: matched bits, update flag and f32 history bits have
zero mismatches. The native gate receives the preprocessing request flag from
the production Rust transition. This comparison covers the gate, not complete
joined-native-controller equivalence. Its source prefix reads the separate
configuration/request flag at context +0x3349 into output +0x334a; it does not
require carrying a previously calculated output flag forever.

The input pair came from live capture 33. Opt-in
`SHIELDSIGNER_AWB_SAMPLE_DIR` retains one raw-statistics / registered-SDK /
translated-frame trio per normal group, near the end of startup countdown.
A stable controller parks on one group, so collecting only after convergence
would miss its other cohort. Every saved SDK is selected by the statistics'
exact registered parameter ID. Both trios independently match all 7,680 original
ARM translation bytes. The 192-image live run also passes 128 AE/AWB statistics
frames, 127 submissions and at most two retained snapshots; its final statistics
translation matches as well. Private records remain ignored locally.

The new line-protocol command `awb-captured-sequence` supports bounded stages,
up to four records/stage, 1–128 cycles and at most 512 processed frames. It uses
the same production Session and exposes gate history/request metadata for the
oracle. Stage boundaries do not request a fresh update. Existing repeated-frame
replay remains supported.

Build host numeric-fixture with mise/Rust, cross-build with
`mise run camera:rust:arm`, then run `mise run camera:rust:awb-scene-sequence --
LOCAL-SAMPLES --adb SERIAL --board-binary ABSOLUTE-BOARD-NUMERIC-FIXTURE
--report LOCAL-REPLAY.json`. The script requires the pinned original binary,
GCC runtime and full IQ profile already used by the research environment.
Independent translation checks use `awb-captured-translation.py` with each
trio and its sidecar parametersId. The tracked
`awb-scene-sequence-validation.json` combines replay results with those sample
association checks and the separate live-capture validation.

The 85 library tests, five Unix transport tests, no-default-features build,
ARM build and six simulated adapter scenarios pass. The frozen 0.0.31-dev
kit remains unchanged; this is development source and diagnostic evidence.
Full hardware scene-change/gain-application timing and the remaining optical/UI
qualification are still open work.

### Joined native captured-input replay (development after 0.0.35 freeze)

`awb-joined-captured.py` now executes original `AwbPreProcV32`, measurement
preparation and the real native gain wrapper on paired hardware samples. It
initializes once and preserves the two-group cache across frames. This removes
the earlier substituted gain-wrapper boundary, while stopping before native
`ReconfigHwParaV32`. Native startup calibration/context construction is still
adapted, so this is a diagnostic comparison.

[The first four-frame replay](awb-joined-captured-diagnostic.json) matches
controller frames, countdown, completeness, active light count and calculation/
reconfiguration decisions. Three frames differ in exact gain bits. The next
step is to locate the first difference in prepared statistics, selected raw
gain or damping state. This does not yet establish a production Rust defect.
The frozen kit and running hardware remain unchanged. Paired samples are private
local files; their cyclic replay is not an optical scene-change experiment.

### First computed gain damping corrected (0.0.36-dev)

The joined replay isolated an actual initialization error: native damping uses
previous gain at context `0x352C`, initially zero, while `0x3578` is the separate
low-count gain seeded from calibration. Rust had seeded both from the initial
gain. The corrected state lets the first computed gain bypass damping, then
accumulates normal history. The initializer reference test now checks both
fields independently.

[Correction evidence](awb-damping-startup-correction.json): 16 replayed frames
match original gain bits, probabilities, density, damping and controller state
without modifying native history. The corrected executable also passed actual
application integration with 73 real frames and clean shutdown. Native hardware
reconfiguration remains the next joined comparison boundary.

### Joined gain and full measurement reconfiguration (0.0.36-dev)

`awb-joined-captured.py --hardware-reference --require-match` now continues
through the complete original `ReconfigHwParaV32`. The helper supplies its
hardware calibration pointers from the pinned IQ profile and an explicit
current SDK record, then carries the native side effects into the next frame.
The stable cohort name is explicit strategy input; a deterministic `timeString`
adapter handles native requests for a new name. No SDK output is patched.

[Sixteen-frame evidence](awb-joined-hardware-equivalence.json) matches the
joined gains/controller state and all 1,204 measurement-record bytes per frame.
The old stop-before-reconfiguration boundary is removed in this mode. The
calibration/context constructor remains adapted, and the two private captured
groups are replayed cyclically; this is not complete native initialization,
variable-policy coverage or an optical lighting-change experiment.

### Actual ordered startup trace (0.0.36-dev)

`SHIELDSIGNER_AWB_TRACE_DIR=/persistent/new-private-directory` retains the
first 32 successfully translated AWB inputs in owner processing order, with
raw statistics, translated frame, exact effective SDK record, ISO and same-frame
AE brightness. Each file uses exclusive creation; reuse a fresh directory.
The option is diagnostic and unset during normal streaming. Traces are private
and must stay outside Git. Storage writes can affect timing.

Replay with `awb-joined-captured.py --trace-dir DIRECTORY --hardware-reference
--require-match --report PRIVATE_REPORT`. Each input keeps its own AE values
and update request. There is no cyclic duplication.

[The first actual 32-frame trace](awb-ordered-trace-hardware-validation.json)
passes native gain/controller and complete next-record comparisons across
FAST and normal time sharing. All 32 actual live-owner gain vectors also match
the native replay bit for bit using exact frame/parameter associations. The
application received 70 real frames and stopped cleanly. This supersedes the
paired cyclic-input limitation for this trace, while retaining the adapted
native context-construction and optical/physical qualification limits.

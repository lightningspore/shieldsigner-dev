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

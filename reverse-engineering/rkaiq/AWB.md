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

The base damping coefficient moves down by one configured step when variance is greater than its threshold, or up by one step otherwise, followed by the original ordered lower/upper comparisons. This leaf consumes an already computed variance; the brightness-history/variance estimator is not implemented here.

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

The checked API requires 1–255 lights, equal output lengths, finite inputs, nonempty increasing prior tables and nonzero reference green denominators. Errors during calculation can leave intermediate output fields changed; this API does not promise atomic mutation on invalid arithmetic inputs. These tests establish arithmetic/state equivalence in the stated corpus, not physical calibration or a functioning independent camera service. The SDK measurement preparation below supplies selected counts/gains. Full upstream translation, calibration loading, illumination classification, spatial/temporal policy, gain adjustments, convergence, full calibrated initialization and live publication remain unfinished.

## Measurement preparation and time-share state

`awb_preparation::prepare` reconstructs complete `PrepareMeasureResult`, ELF `0xc3180` (Ghidra `0xd3180`), including its call to `IsMeasureResultStable4`, ELF `0xc2f90`. The API owns no vendor pointers: mutable light records, seen flags, totals, grid cells and other caches are explicit borrowed buffers/typed state. `Frame` borrows the exact **7,680-byte SDK full-V32 record**. The existing kernel statistics decoder is not yet a complete producer of this SDK record/configuration metadata.

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

The caller resets its incoming update flag before each test frame; the surrounding `AwbPreProcV32` brightness/variance/scheduling policy is not reconstructed by this suite. Full kernel-to-SDK translation, calibration construction, per-illumination/spatial strategy, convergence and live publication remain unfinished. Numeric replay still does not prove independent camera startup or image quality.

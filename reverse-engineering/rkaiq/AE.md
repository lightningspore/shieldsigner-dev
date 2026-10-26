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

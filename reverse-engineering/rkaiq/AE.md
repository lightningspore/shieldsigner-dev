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

AE1/2/3 big-grid correction, histogram redistribution, full translator configuration/state, calibrated weights, exposure selection and sensor programming remain unfinished. Do not feed guessed gains, black levels or weights into a live control loop and describe it as the upstream algorithm. The measurement decoder and this helper are separate APIs until those inputs and synchronization are reconstructed.

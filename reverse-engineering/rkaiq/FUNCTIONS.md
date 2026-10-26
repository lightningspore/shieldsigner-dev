# Reconstructed function contracts

All addresses below are **ELF virtual addresses with the Thumb bit cleared**, before Ghidra's 0x10000 image-base relocation. The exact library SHA is recorded in the numerical report. The current Rust routines are checked value APIs, not binary-ABI-compatible exports of the C++ names.

| Original function | ELF entry | Rust API | Checked cases |
| --- | --- | --- | --- |
| `interpolation(float const*, float const*, int, float, float*)` | `0x20630` | `interpolate` | 1,000 |
| `SatInterpolateMatrices` | `0xfd2e6` | `saturation_matrix` | 1,000 |
| `SatInterpolateOffset` | `0xfd32e` | `saturation_offsets` | 1,000 |
| `InterpLutbyAlp` | `0xfc8bc` | `blend_lut` | 50 complete LUTs × 2,187 values |
| `AdpccInterpolation(int, int*, int*)` | `0x11a984` | `defect_pixel_interpolate` | 1,000 |
| `gain_float_lim2_int(float, int, int)` | `0xe79d8` | `quantize_gain` | 1,000; multiplicative branch, 0–30 fractional bits |
| `gain_fix_transfer_v2` | `0xe7a68` | `gain::pack_gain_registers` | 1,000 full records; linear, two-frame HDR, three-frame HDR |

| `gain_select_params_by_ISO_V2` | `0xe784c` | `gain::select_gain_scales` | 1,000 calibration selections |
| `RkCam::Isp32Params::convertAiqAwbGainToIsp32Params` | `0x2b590` | `isp32::apply_awb_gain` | 1,000 complete parameter-buffer updates |

| `RkCam::Isp32Params::convertAiqExpIspDgainToIsp32Params` | `0x2d860` | `isp32::apply_exposure_digital_gain` | 1,000 complete parameter-buffer updates |

## Gain-record layout and behavior

The SDK's public `RK_GAIN_Fix_V2_s` header defines 13 one-byte controls followed by three u32 gains aligned at byte 16. The Rust serializer explicitly zeroes the three padding bytes; the original routine leaves them untouched, so reference outputs begin in zeroed storage. The compared record is 28 bytes.

Control-byte order is:

`sw_gain2ddr_mode`, `sw_gain2ddr_wr_en`, `sw_3dlut_gain_en`, `sw_dhaz_gain_en`, `sw_adrc_gain_en`, `sw_lsc_gain_en`, `sw_gain_module_free_mode`, `sw_gain_dmard_mode_en`, `sw_bayer3dnr_gain_en`, `sw_gain_mp_pipe_dis`, `sw_gain_gate_always_on`, `sw_mge_gain_en`, `sw_gain_en`.

The pinned function assigns `[0,0,1,1,1,1,0,0,1,0,0,1,1]`. It repeats the last active exposure for unused slots, calculates ISO×time exposure ratios and analog×digital gain ratios, quantizes to Q6, applies optional short/middle HDR scales, and limits the short channel to 262143 and the other two channels to 16383. Linear mode yields unity Q6 gains of 64. The fourth scalar argument and the input `isp_dgain[]` array are unused in this exact binary.

The Rust implementation rejects nonpositive active exposure/time/gain/ISO and nonfinite inputs instead of reproducing invalid/undefined calculations. Pointer checks, vendor logging and arbitrary invalid binary-call ABI behavior are outside the safe API. This record still needs to be mapped into the kernel full ISP32 parameter ABI before it can program the hardware.

## Corpus coverage

The fixed seed is in `numeric-equivalence.json`. It covers endpoint clamping, tight interpolation intervals around the 0.001 threshold, matrix extrapolation, calibration integer ranges, signed gain quantization including saturation, and LUT alpha endpoints/fractional coefficients. Calibration profiles use normal finite values. Ten function reconstructions and a finite corpus are not an exhaustive correctness or complete ISP claim.

The harness loads original ARM instructions, applies ELF relocations, enables VFP and runs each selected function to a bounded return sentinel. Standard memory copies/sets have explicit emulator implementations; all other unexpected imported calls fail the test. Gain register conversion executes its actual internal helper and reaches no imported dependency for the valid cases tested.

## ISO calibration selection

The selector integer-divides ISO and table knots by 50, with sample gain at least 1. Exact interior knots select the interval beginning there; out-of-range samples extrapolate. The checked API requires strictly increasing normalized knots. Interpolation uses fused multiply-add. The table enable flag is copied; row flags are unused. Returned indices replace the original context mutation.

## ISP32 white-balance parameter serialization

The SDK header defines the fifth input field as an application-position enum (gain bank 0 or 1), despite Ghidra inferring a float. Each color gain is multiplied by 256 in f32, then rounded using f64 +0.5, narrowed and limited to 2047. The checked API accepts finite gains from 0 through 255. Four groups of GB/GR/B/R words occupy 32 bytes: gain bank 1 first, then the three gain-bank-0 groups. The unused bank receives unity (256).

The exact pinned ARM kernel UAPI defines a packed 11,145-byte ISP32 parameter buffer, AWB gain record offset 4,645 (0x1225), and AWB module mask 1<<5. `camera:rust:layout` independently cross-compiles assertions against those headers. Updating sets that bit in all three masks and preserves unrelated bytes. `update=false` is a complete no-op. The Rust API exposes the original C++ cached record as a separate buffer. No parameter buffer is submitted to a live ISP yet.

## Exposure digital gain

The original consumes a by-value `RKAiqAecExpInfo_s` aggregate: two words arrive in r2/r3 and its remaining bytes on the ARM stack. Public AE headers place ISP digital gain at byte 12 in each 48-byte exposure record: linear offset 12, HDR offsets 60/108/156. The harness models this calling convention directly. A zero context working mode selects linear; any nonzero mode uses all three HDR slots.

Linear gain at or below 1 is a complete no-op. HDR gains below 1 become unity, and three unity gains are a no-op. Otherwise the three AWB-bank-0 groups are scaled from the cached record, using f32 multiplication followed by f64 +0.5 and saturation at 65535. Bank 1 and the cache remain unchanged. Only the configuration-update mask (byte 16) receives the AWB bit; enable/update-enable masks remain untouched. Repeated application therefore does not compound gain. Checked Rust rejects negative/nonfinite inputs before mutation. The corpus compares all affected bytes and asserts unrelated-buffer/cache preservation; it is not a live exposure-control loop.

## Dynamic exposure damping

`ae_damping::calculate` reconstructs `AecDynamicDamp`, ELF `0xa4024`, and its active core at `0xa3ab8`. The wrapper returns the supplied coefficient unchanged when disabled; a native null context returns 8.0, which is outside this checked value API. [Behavior and reference evidence](AE.md#history-based-exposure-damping).

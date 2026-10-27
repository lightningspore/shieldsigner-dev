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

## ISP pipeline pad setup

`isp_pipeline::setup` reconstructs `CamHwIsp20::setupPipelineFmtIsp`, ELF `0x2319c`. It preserves the native sequence and full UAPI records through an explicit backend. Device/raw-stream/scaler implementations remain outside this verified function. [Contract, driver evidence and missing startup work](ISP.md).

## Live link/format startup adapter

Development `camera-probe configure-pipeline` supplies real Linux device methods for the recovered ISP pad setup and the CIF pad sequence (ELF `0x22f90`). It configures explicit existing media links, optional bridge pads and one linear RAW10 TX/RX pair, including the native CSI high-alignment predicate/requests where needed. [Command, scope and hardware limitations](ISP.md#live-linux-configuration-adapter). [Focused CIF/ARM command validation](live-pipeline-validation.json). This is not full calibrated startup or persistent queue ownership.

## ISP black-level conversion

`isp_black_level::apply` reconstructs `Isp32Params::convertAiqBlcToIsp32Params`, ELF `0x2d58c`, including its complete 44-byte kernel block and cache. [Contract and evidence](ISP.md#black-level-parameter-block).

## ISP demosaic conversion

`isp_demosaic::quantize` reconstructs `AdebayerGetProcResult`, ELF `0x115880`, with explicit selected values/cached hardware storage. `isp_demosaic::apply` reconstructs `Isp32Params::convertAiqAdebayerToIsp32Params`, ELF `0x2ca90`, including all masks and the complete 57-byte kernel block. [Contracts, native runtime evidence and limits](ISP.md#demosaic-hardware-controls).

## Automatic demosaic tuning

`demosaic_selection::Calibration::select` reconstructs the automatic branch of `AdebayerProcess` (ELF `0x1157a0`) and its full `AdebayerSelectParam` call (`0x115028`). `Calibration::from_value` loads an explicit `debayer_v2.param` JSON object through the optional diagnostic feature. [Contracts, SDK profile comparisons and limits](ISP.md#automatic-demosaic-tuning).

## Metadata parameter queue

`parameter_queue::Queue` reconstructs metadata-output branches of native `V4l2Device` prepare/start/queue/dequeue/return/stop and uses the recovered buffer reset/request logic. The Linux diagnostic supplies a real MMAP/ioctl adapter; its positive hardware path is untested. [Entries, contracts, controlled boundaries and validation](PARAMETERS.md).

## AE measurement parameter configuration

`isp_ae_measurement::apply_ae` and `apply_histogram` reconstruct result types 1 and 2 inside `Isp32Params::convert3aResultsToIspCfg`, ELF `0x304c4` (Ghidra `0x404c4`). These are two dispatcher branches, not a reconstruction of the full dispatcher. [Routing, masks, cached records and reference evidence](AE.md#measurement-parameter-configuration).

## AWB measurement parameter configuration

`isp_awb_measurement::Measurement::apply` reconstructs `Isp32Params::convertAiqAwbToIsp32Params`, ELF `0x2b71c` (Ghidra `0x3b71c`). [SDK layout, native quirks and 2,000 original-ARM comparisons](AWB.md).

## AWB gain and temporal stages

`awb_gain` reconstructs six original routines for weighted-statistics gains, normalization, mixture, damping-coefficient adaptation and temporal gains. [Entries, precision, context effects and 6,000 native comparisons](AWB.md#gain-calculation-and-temporal-damping). These are stages of the AWB path; the surrounding classification, calibrated policy and service remain unfinished.

## AWB illumination probabilities

`awb_probability::calculate` reconstructs `AwbCalWpNoProbablity` followed by the complete `AwbCalTotalProbablity` call tree. `weighted_gain` reconstructs `AwbCalGainTotal`. [Six entries, retained counts, all per-light values and 2,000 full native sequences](AWB.md#illumination-probabilities-and-weighted-gain).

## AWB measurement preparation

`awb_preparation::prepare` reconstructs the numerical/cache behavior of complete `PrepareMeasureResult`, ELF `0xc3180`, including original `IsMeasureResultStable4`, ELF `0xc2f90`. `stability` also exposes that gate separately. [SDK frame ABI, persistent buffers, fast group −1 and 500 native sequences/1,144 frames](AWB.md#measurement-preparation-and-time-share-state). Outer `AwbPreProcV32` scheduling/strategy is not included in this API.

## Complete single-ISP AWB translation

`awb_translation::translate` reconstructs the full RV1106 single-ISP value path of `RkAiqResourceTranslatorV32::translateAwbStats`, ELF `0x8818c`, including metadata, global RGB sums, debug descriptor and conditional output flags. `Configuration::from_measurement` reads the selected 1,204-byte SDK measurement record. [1,000 native comparisons](awb-translation-equivalence.json). This development addition after kit 0.0.28 does not establish applied-configuration correlation, live startup, multi-ISP delegation or C++ object ownership.

`demosaic_runtime::State::process` reconstructs the persistent automatic linear
color-frame gate in the demosaic `processing` callback (ELF `0x114a2c`), including
integer ISO, reconfiguration consumption and cached update publication.
[Persistent callback evidence and live integration boundary](ISP.md#persistent-automatic-linear-demosaic-frame-gate-0033-development).

`isp_dpcc::apply` reconstructs the DPCC selected-result case (type ID 6) within
`Isp32Params::convert3aResultsToIspCfg`, ELF `0x304c4`. All 11,145 output bytes
match original ARM for 1,000 cases, with physical Luckfox CPU replay.
[Input window, native mask asymmetry and live integration boundary](ISP.md#dpcc-selected-result-serializer-0034-development).

`dpcc_selection::select` reconstructs automatic expert DPCC ISO row selection
(ELF `0x11b6e0`) and its 103-byte configuration copy (`0x11b3c4`).
[Original/physical ARM comparisons and profile-loading boundary](ISP.md#dpcc-automatic-expert-iso-selection-0034-development).

`dpcc_calibration::expert_table` reconstructs expert-table initialization
(ELF `0x11ac20`) from the explicit IQ JSON object.
[Public SDK layout checks and original/physical ARM comparison](ISP.md#dpcc-expert-table-from-the-selected-iq-object-0034-development).

`dpcc_calibration::Automatic` composes the supported expert DPCC result;
`pdaf_fields` reconstructs the PDAF initializer (ELF `0x11afc4`).
[Complete native AdpccInit/AdpccProcess comparison and live boundary](ISP.md#complete-automatic-dpcc-result-assembly-0034-development).

`dpcc_runtime::State::process` reconstructs the automatic linear color DPCC
frame callback gate (ELF `0x11a67c`), including native gain multiplication order,
integer ISO, reconfiguration and cached-result publication.
[Persistent callback and live transactional evidence](ISP.md#persistent-dpcc-and-live-submission-0034-development).

`isp_ccm::apply` reconstructs complete CCM register conversion,
`Isp32Params::convertAiqCcmToIsp32Params` (ELF `0x2d0cc`).
[Quantization, native mask behavior and comparison scope](ISP.md#ccm-register-conversion-0034-development).

`ccm_selection::select` reconstructs saturation profile selection
(`0xfd278`), matrix interpolation (`0xfd2e6`) and offset interpolation
(`0xfd32e`), preserving native fused rounding.
[Indices, clamp status, profile cases and native/physical CPU evidence](ISP.md#ccm-saturation-selection-and-interpolation-0034-development).

`ccm_illuminant::estimate` reconstructs complete nearest CCM illuminant
selection (`illuminant_index_estimation_ccm`, ELF `0xfd394`).
[Distance arithmetic, tie/no-match behavior and evidence](ISP.md#nearest-ccm-illuminant-0034-development).

`ccm_runtime::State::process` reconstructs the persistent non-blended
`selectCCM` call tree (ELF `0xfe000`), including gain-to-saturation mapping,
profile names, cached publication and early exits.
[State boundaries and full native sequence comparison](ISP.md#persistent-non-blended-ccm-selection-0034-development).

`ccm_damping::State::process` reconstructs the CCM `Damping` routine
(ELF `0xfd6f8`), including fused temporal blending and convergence.
[Exact routine identification and persistent native/physical CPU comparison](ISP.md#ccm-temporal-damping-and-convergence-0034-development).

`ccm_saturation::apply` reconstructs complete `Saturationadjust`
(ELF `0xfd7e0`), preserving mixed-precision fused color transforms.
[Arithmetic, domain and native/physical CPU evidence](ISP.md#ccm-saturation-adjustment-0034-development).

`ccm_luma::symmetric` reconstructs complete `YAlpSymAutoCfg`
(ELF `0xfe250`), including interpolation/cache gates and whole-curve publication.
[Verified ARM calling convention and native uClibc/physical CPU evidence](ISP.md#symmetric-ccm-luma-curve-0034-development).

`ccm_calibration::static_fields` reconstructs static result initialization by
`ConfigHwbyCalib` (ELF `0xfecd0`) from explicit IQ JSON fields.
[Public SDK ABI checks and native/physical CPU evidence](ISP.md#ccm-sdk-layouts-and-static-calibration-fields-0034-development).

`ccm_calibration::Automatic::from_value` loads owned supported CCM tables,
including native profile-name resolution/order from `pCcmMatrixAll_init`
(ELF `0xfdc04`) and `CamCalibDbGetCcmProfileByName` (`0xfdba8`).
[Validation boundaries and original/physical CPU table evidence](ISP.md#owned-ccm-calibration-tables-0034-development).

`ccm_input::filter` reconstructs complete `JudgeCcmRes3aConverge`
(ELF `0xfe1dc`), including independent input holds and baseline mutations.
[Meaning, fused distance and persistent native/physical CPU evidence](ISP.md#ccm-input-deadband-0034-development).

`ccm_automatic::State` composes supported complete `AccmConfig` (`0xff10c`)
and `AccmAutoConfig` (`0xfed30`) numerical/cache behavior.
[Explicit initialization, frame control and joined native/physical CPU comparison](ISP.md#joined-automatic-ccm-configuration-0034-development).

`ccm_automatic::State::new` now has comparison against full original
`AccmInit` (ELF `0xff36c`), including its real ISP32 calibration-module lookup.
[Construction boundaries, initial state and subsequent-frame evidence](ISP.md#native-ccm-constructor-proof-0034-development).

`ccm_frame::State::process` reconstructs the complete supported CCM descriptor
`processing` callback (ELF `0xfd126`), including input mutations, output-copy
ownership and flag clearing. The full callback comparison also closes the
native −21 selector-status early exit in joined automatic configuration.
[Descriptor identity, regression and native/physical CPU evidence](ISP.md#complete-ccm-callback-and-publication-0034-development).

`ccm_frame::State::seeded` and the camera event owner now integrate calibrated
startup and transactional live CCM. `awb_session::Session::ccm_damping` exposes
the native-published base IIR coefficient for exact-frame handoff.
[Live mapping, driver-failure behavior and camera/scan evidence](ISP.md#transactional-live-ccm-0034-development).

`isp_lsc::apply` reconstructs the LSC result-type-10 branch inside the full
ISP32 dispatcher (ELF `0x304c4`), including retained entries, clamping,
mask clearing and cached enable state.
[SDK/kernel layout and complete native/physical CPU evidence](ISP.md#lsc-selected-result-serialization-0034-development).

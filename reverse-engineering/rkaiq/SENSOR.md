# Sensor exposure programming

`sensor::program_linear` reconstructs `SensorHw::setLinearSensorExposure(RKAiqAecExpInfo_s*)`, ELF `0x3ac10` (Ghidra `0x4ac10`), in the pinned library. It operates on already converted sensor register/control codes. **The Linux backend is supplied by the diagnostic command described below. Descriptor reading and exposure-code conversion are separate recovered APIs described below.** The kit's fixture tests do not program a real device; the explicit `apply-linear` command does.

The recovered sequence is:

1. Read the sensor descriptor's `line_periods_per_field` and `sensor_output_height`.
2. Use the greater of the descriptor line count and the requested frame length. Set `V4L2_CID_VBLANK` to that frame length minus output height.
3. If a frame-length cache/mirror is active, update it after VBLANK succeeds.
4. If DCG mode is 0 or 1, send the conversion-gain ioctl. Other modes skip this operation.
5. Set analogue gain, including when its code is zero.
6. Set digital gain only when its code is nonzero.
7. Set coarse integration time through the exposure control only when its value is nonzero.

| Operation | Pinned identifier |
| --- | --- |
| VBLANK control | `0x009e0901` |
| Analogue gain control | `0x009e0903` |
| Digital gain control | `0x00980913` |
| Exposure control | `0x00980911` |
| Native control ioctl | `0xc008561c` |
| Conversion-gain ioctl | `0x400456c6` |

The native method exits at the first failed write, returning -9. Earlier successful writes are not rolled back. In particular, the frame-length cache retains its new value when a subsequent control fails. Rust returns the backend's typed error while preserving the same operation ordering and cache-update point. Descriptor retrieval errors are propagated explicitly; the original ignores that call's status. Native u32 subtraction and control-value bit patterns are preserved, so out-of-range values may reach the backend and must be rejected by the actual driver rather than silently clamped by this helper.

The native input fields are `LinearExp.exp_real_params.dcg_mode`, coarse integration, analogue and digital gain codes from `LinearExp.exp_sensor_params`, and the top-level frame length. This does not directly write I2C registers. The kernel sensor driver is responsible for interpreting V4L2 controls and programming the SC3336 or other supported device.

## Evidence

`camera:rust:sensor-linear` executes the original ARM method with explicit descriptor/ioctl callbacks and discarded logging. It compares complete write traces, returned status and frame-length cache state for 1,000 deterministic cases. Cases cover optional writes, both cache states, first-through-fifth write failures, absent failures, arithmetic boundaries and full-width control bit patterns. [Report](sensor-linear-equivalence.json).

Descriptor output is supplied at the offsets used by the original virtual call; this is not a verified native descriptor implementation. The Rust backend interface deliberately avoids copying C++ object/vtable layouts. ARM emulation repeats every fixture using the compiled Rust implementation. A host test verifies descriptor errors prevent all writes and preserve the mirror.

Remaining work includes loading the real-exposure-to-register calibration, validating the descriptor and write adapters on hardware, sensor-specific control support, frame-start scheduling/delays, HDR programming and integration with the actual AE loop. The manual `apply-linear` command is available for adapter validation, without an automatic-control loop.

## Real exposure to register codes

`exposure::convert` reconstructs `AeReal2RegConv`, ELF `0x43ce0` (Ghidra `0x53ce0`). It accepts explicit calibration, real gain, seconds, linear/HDR2/HDR3 timing mode and DCG mode, returning gain and integration-time codes. It does not load the sensor's calibration or write those codes.

When DCG mode is at least one, real gain is divided by the selected linear/HDR DCG ratio; otherwise the ratio is unity. Gain-band mode selects the first inclusive matching interval. A matching zero scale immediately triggers the original fallback rather than trying a later interval. Fallback uses scale 16, offset 0, exponent 1 and register range 16–255. These are recovered fallback constants, not a recommended SC3336 calibration.

Band conversion uses fused `scale × powf(gain,exponent) - offset`, adds 0.5 in f32, truncates to signed i32, reinterprets it as u32, then compares that unsigned value with the band's limits. Negative intermediate codes can therefore hit the maximum clamp rather than the minimum; the Rust port preserves that behavior. Logarithmic mode uses the original f32 sequence `log10f(gain) × 20 × 10 / 3 + 0.5`, with no gain-band clamp.

Integration time applies the four timing factors with the original fused operation order, then truncates to signed i32 and reinterprets it as u32 before converting back to float. It subtracts the selected timing offset, divides by the step, truncates to signed steps, and uses a fused multiply-add to align to that step/offset. The final unsigned code is limited by the selected minimum, with no upper clamp in this routine. Linear and two-/three-frame HDR select different timing rules; HDR uses a shared DCG ratio.

The checked API rejects nonfinite/invalid active timing inputs and malformed gain-band limits. It need not validate an unused DCG ratio when DCG is disabled. Calibration loading, valid sensor-specific limits and exposure/frame-delay decisions remain caller responsibilities.

### Math reference

`camera:rust:exposure` executes the original RKAIQ function and bridges its `powf`/`log10f` calls into **actual ARM instructions** from `libuClibc-1.0.31.so` in the pinned SDK's runtime archive. The archive and member hashes/URLs are recorded in `artifacts.json`; setup downloads them to ignored cache. The isolated runtime uses ARM variant-I TLS relocations/thread-pointer storage. No imported runtime function calls were needed by the tested math cases; this is not an emulation of a full Linux process or dynamic loader. Logging is discarded explicitly.

Rust uses pure-Rust `libm` math. The 1,000-case comparison checks final integer gain/time codes, not a claim that every transcendental float result is bit-identical for all inputs. Cases cover both gain models, all three timing modes, four DCG modes, first-inclusive interval selection, zero-scale fallback and negative pre-clamp gain codes. [Report](exposure-equivalence.json). The reference runtime is pinned SDK evidence, not a measured hash of libc on the eventual hardware image. Compiled ARM Rust fixtures repeat the entire comparison corpus without shipping or linking the vendor runtime. Its binary/archive are excluded from the kit.

## Descriptor construction and read-only adapter

`sensor_descriptor::read` reconstructs `SensorHw::get_sensor_descriptor`, ELF `0x3b0c4` (Ghidra `0x4b0c4`), and its format/blanking/pixel-rate/exposure helpers. It clears a 172-byte descriptor, reads active pad-0 width/height/media-bus format, then queries **minimum** HBLANK and VBLANK. Width plus minimum HBLANK and height plus minimum VBLANK narrow to u16 line/frame periods. These are descriptor minima, not necessarily the current timing.

The native frame-interval query computes FPS as denominator/numerator in f32. Pixel clock is `line_period × frame_period × FPS / 1,000,000`, preserving its operation order. If frame-interval querying fails, a pixel-rate extended-control query is required. The pinned native fallback converts the signed low 32 bits of that 64-bit value to f32 MHz; the Rust reconstruction preserves this behavior rather than silently widening it. It also narrows the minimum exposure to u16 and fixes the coarse-integration margin to 10.

Required query failures stop descriptor construction. Optional noise-switch and DCG-ratio failures only clear validity; both may be unsupported. Noise-switch payload words are `direct`, `up_thres`, `down_thres`, `div_coeff`; DCG words are `integer`, `decimal`, `div_coeff`. The raw payloads are retained without inventing physical interpretation or replacing missing calibration. Fifteen native media-bus-to-pixel-format mappings are preserved; unknown codes yield `0xffffffff`.

`camera:rust:sensor-descriptor` compares original ARM query order, status and the complete successful 172-byte record across 1,000 cases. Native descriptor helpers and format mapping execute directly; only ioctl responses/errno are simulated. Required failures compare status/trace and discard partial native output, matching the Rust API's absence of a returned descriptor. [Report](sensor-descriptor-equivalence.json). Both individually and jointly unsupported optional queries are covered. `camera:rust:layout` checks the read ioctl numbers, struct sizes, field offsets and pointer layout against pinned kernel headers.

`camera-probe sensor-info NODE` implements the read-only ARM32 Linux adapter, outputs parsed fields plus original descriptor bytes/query trace, and is included in the hardware guide. Device requests remain unvalidated until the real camera test. No write ioctl adapter or automatic loop has been added by this command.

## Linux write adapter and manual test command

`camera-probe apply-linear DEVICE FRAME_LINES ANALOGUE_CODE DIGITAL_CODE SHUTTER_CODE [DCG_MODE]` opens the sensor subdevice for read/write and feeds those explicit codes to the recovered sequencer. It reads a fresh descriptor first, refuses detected `rkaiq_3A_server`/`rkipc` processes, and rejects values that cannot be represented as nonnegative signed V4L2 control values. The default DCG mode is **-1 (skip)**. Only an explicit 0 or 1 requests the conversion-gain ioctl. The offline planner now reports -1 when the IQ profile says DCG is unsupported; both -1 and 0 disable DCG ratio normalization during arithmetic conversion.

The command does not start a sensor/image stream or initialize the ISP. It prints requested values, descriptor queries, each attempted write, failure details, accepted frame length and subsequent `VIDIOC_G_CTRL` readback plus control ranges. It exits nonzero on a write failure while preserving the JSON partial-write report. Later failed calls do not roll back earlier ones. Readback is kernel control state, not proof of I2C register contents or timing; a driver may cache controls while the device is powered down. Applications using the sensor must be stopped or coordinated separately; absence of the two known vendor process names is not exclusive-ownership proof.

The pinned SC3336 driver (`sc3336.c`, URL/hash in `artifacts.json`) registers `V4L2_CID_ANALOGUE_GAIN` from 128 to **99,614** and handles combined sensor gain through that control. It does not register a separate digital-gain control. The native sequencer's digital slot uses generic `V4L2_CID_GAIN`; leaving the explicit digital code at zero skips that operation, as required for this driver. The profile's maximum register value is 99,615, one count above the driver limit. The planner preserves native conversion and does not hide that mismatch; the driver can reject an out-of-range code. Conversion-gain writes are skipped by default because this reference profile disables DCG support.

The adapter uses a repr(C), eight-byte `v4l2_control` equivalent; read/write request numbers, control IDs and conversion-gain ioctl are cross-checked against pinned kernel headers. Existing 1,000-case native sensor sequencing tests continue to run. ARM smoke tests reject a nonsensor endpoint before any writes and reject invalid scalar/DCG arguments. No successful real sensor write is claimed by those tests. Sensor-specific limits, active streaming behavior, gain interpretation and before/after frames still need the hardware session.

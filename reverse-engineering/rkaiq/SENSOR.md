# Sensor exposure programming

`sensor::program_linear` reconstructs `SensorHw::setLinearSensorExposure(RKAiqAecExpInfo_s*)`, ELF `0x3ac10` (Ghidra `0x4ac10`), in the pinned library. It operates on already converted sensor register/control codes. **The live ioctl backend, descriptor reader and exposure-code conversion are not supplied by this function.** The kit's fixture tests do not program a real device.

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

Remaining work includes recovering real-exposure-to-register calibration, implementing/validating the live descriptor/ioctl adapter, sensor-specific control support, frame-start scheduling/delays, HDR programming and integration with the actual AE loop. No sensor-programming command has been added to `camera-probe` yet.

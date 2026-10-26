# Loading the exposure subset of IQ JSON

`calibration::SensorCalibration` parses the SDK JSON `sensor_calib` section into the recovered exposure converter's types. It is enabled with the diagnostic/JSON feature; numerical code still builds without JSON or std. This is **not** the full native IQ database, scene parser or binary-IQ loader.

The pinned SC3336 reference is `sc3336_CMK-OT2119-PC1_30IRC-F16.json`, SHA-256 `8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a`. Its exact SDK URL/hash and the public `sensorinfo_head.h` schema are in `artifacts.json`. Originals download to ignored cache. The kit contains a derived `sensor_calib`-only reference with attribution, not the original scene/color/noise tuning profile.

Parsed fields include:

- Sensor resolution; linear gain-band or nonlinear-DB model; seven-value gain bands and declared length.
- Four time-conversion factors; linear and HDR timing minima, step/offset rules; linear maximum-time factors retained as data.
- DCG support flags and ratios, including disabled zero ratios.
- Analogue, digital and ISP gain ranges; linear time/gain/DCG update delays.

The loader rejects malformed array lengths, gain-band bounds, unsupported model names, numeric overflow, missing required fields, invalid linear timing and inconsistent enabled DCG ratios. It preserves HDR zero timing records as supplied, rather than inventing values to make HDR run. The existing converter rejects an invalid active timing step if that mode is requested. Other IQ sections are intentionally not interpreted yet.

For this reference, resolution is 2304×1296, gain scaling is 128 with exponent 1, time factors are `[0,0,1,0.5]`, and the linear step/offset is `[1,0]` with minimum 1. Linear time and gain updates each have delay 2; DCG delay is 0. DCG support is disabled and HDR timing steps are zero. These settings are SDK evidence; selecting this file does not establish that all optics/module tuning or firmware limits are qualified for our physical camera.

## Offline planner

`camera-probe exposure-plan IQ.json SENSOR.json SECONDS GAIN [FRAME_LINES]` loads this subset and a saved `sensor-info` report, checks resolution agreement, and calculates **linear, DCG-normalization-disabled** register codes. Frame length defaults to the descriptor minimum and an explicit override cannot go below it. Runtime line length and clock come from the saved sensor information.

The report sets DCG mode to -1 (skip) when the profile disables DCG, otherwise 0. Neither applies a DCG ratio during conversion. The JSON report marks `writesSensor=false` and `automaticExposure=false`, exposes timing provenance, register codes, whether gain fallback was used, raw maximum-time factors, gain ranges and update delays. It does not silently turn a descriptor minimum into a claimed current-frame observation. It also does not apply the higher-level maximum-time policy, driver control limits, gain splitting, frame synchronization or automatic exposure decisions. The full ISP scene calibration and initialization remain unfinished.

Both ARM and native Mac executables support this offline command. The kit's `examples/synthetic-sensor-info.json` exists only for a demonstration and frontend validation. Use actual `sensor-info` output for hardware investigation; the planner does not open a device in either case.

## Verification

`mise run camera:rust:iq-calibration` independently maps the original SDK profile into the original `AeReal2RegConv` context and compares 100 requested exposures with the Rust JSON loader plus converter. Original RKAIQ and pinned uClibc math instructions execute under Unicorn. [Reference comparison](iq-calibration-equivalence.json).

The same task checks the command with ten cases: correct profile/synthetic descriptor, explicit frame length, resolution mismatch, too-short frame, incomplete gain row, f32 overflow, zero timing step, missing clock, nonfinite requested time and zero requested gain. These return structured output or clear errors rather than panics. [Frontend validation](iq-plan-validation.json).

`camera:rust:smoke` replays the complete IQ corpus using the compiled ARM executable and runs an offline exposure plan with the explicitly synthetic snapshot. No reference or frontend test here performs a live sensor write, proves calibration loading for other profiles, or validates an AE control loop.

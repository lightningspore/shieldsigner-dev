# Phase7 camera register evidence

The reference is the original Linux camera stack on the standard Luckfox Pico/RV1103. The target is the separate Pico Mini/RV1103 running original `no_std` Rust in RAM. No REF boot files or DUT storage were changed.

`src/camera/sc3336.rs` implements sensor reset, frame length, exposure, gain, orientation, pattern control and stream start/stop. `sensor_mode.rs` retains the observed analog/timing preset as register facts. `receiver.rs` names the VICAP RAW10 format, dimensions, stride, DMA slots, status handling, CSI lane/packet configuration and D-PHY profile. The normal build does not execute timestamped trace events. The optional `camera-replay` feature and ignored `build/phase-7-replay-baseline/` preserve the prior implementation for comparison.

The Phase7 diagnostic uses2304×1296 compact little-endian RAW10,3072-byte row stride and two4MB DMA slots at48/52MB. These slots map normal noncacheable memory. The camera clock mux matches REF's actual24MHz oscillator selection, despite the sensor mode's nominal27MHz declaration. Other I2C-only diagnostics retain their previously tested27MHz setup. No PLL is retuned.

Capture rejects receiver errors, simultaneous completion of both slots, repeated slot numbers, intervals above1.2seconds after the first frame, transfer timeouts, failed stream stop and unchanged DMA. The initial frame deadline is5seconds. Nine sensor controls are read back before stream-on;32 selected receiver/configuration readbacks match the captured REF state after explicit masks and intentional DMA/polling differences. This is selected-register evidence, not full-state equivalence or a natural-scene qualification.

## Snapshot coverage

Local generated `ref-dumps/idle.txt` and `streaming.txt` combine validated framed snapshots. Corresponding `*-full/manifest.json` files retain byte counts and SHA256 hashes; the framing also checks length and CRC. Streaming state receipts confirm the capture-enable bit and active runtime state for each block. Snapshots are taken across time, not atomically.

Complete declared resources were captured for CRU, GRF, PMU, PMU IOC/GPIO0, D-PHY, CSI0, VICAP and ISP. The main IOC resource declares0xff538000–0xff577fff. Reading reached0xff56ffff, then the userspace process raised an external-abort fault at0xff570000. The scan stopped, clock references were released and original REF capture passed afterward; kernel taint stayed4096, the historical out-of-tree-module flag. No reset or camera-device teardown occurred.

The captured IOC prefix is0x38000bytes. The remaining0x8000bytes are **not captured** and are not synthesized as zeros. `ref_range_snapshot.py` rejects a repeat full-IOC request. `audit_ioc_coverage.py` checks the pinned SDK's GPIO1–4 IOMUX bounds and drive/pull/Schmitt offsets against that prefix, plus GPIO0 fields against the separate PMU IOC page. All these source-known fields fit within captured regions. The largest source-known GPIO4 field is at IOC offset0x300a8; none of these pin-control fields require the faulting tail. This resolves coverage of the SDK-used pin controls while preserving the declared-resource gap as a limitation.

## Raw gate result

Named-driver run20261114T152545Z passed ten consecutive frames with clean status, correct sensor readbacks and32 selected REF configuration matches. The user-positioned printed carton label/barcodes and contrasting surrounding material are recognizable in the decoded raw preview. Phase7 is recorded in evidence/phase-7.json. Normal diagnostic settings now use8192 exposure lines at unity gain; the separate camera-low-light feature preserves the night profile. Bayer colour remains uncalibrated; this is not an ISP/3A qualification.

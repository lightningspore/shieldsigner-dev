# Luckfox Mini bare-metal bring-up

This folder contains the independent bare-metal bring-up of a Luckfox Pico Mini A/RV1103. The existing Linux camera implementation in `../firmware/rkaiq-rs/` remains the reference; its algorithm library already uses `#![no_std]` with Linux diagnostics behind a feature.

Start with [NOTES.md](NOTES.md) for the live state, [HISTORY.md](HISTORY.md) for chronological evidence, and [PLAN.txt](PLAN.txt) for the user-provided mission and phase gates.

- Base: plain `no_std` Rust with native MicroPython and UART/USB debugging.
- REF: known-good Linux board with SC3336 camera, reached by explicitly selected ADB serial.
- DUT: now boots the user-authorized spare4GB microSD; remove it for RAM-only maskrom downloads.
- REF boot partitions remain untouched. Only the user-provided spare DUT card was authorized and written; USB downloads remain RAM-only.
- Phase success requires real-device evidence; compilation alone never closes a gate.

All new source, helper tools, decisions and evidence for this effort belong here. `logs/phase-N/`, `ref-dumps/` and `.tools/` are ignored local artifacts. Tool downloads retain their original licenses. The new driver implementation will use original code; existing GPL drivers may be studied but are not copied into the permissive implementation. Closed DDR/USB blobs are used as supplied, without disassembly.

Run the read-only Phase 0 inventory with `mise run baremetal:doctor`. It saves fresh evidence under `logs/phase-0/`. It never loads code, flashes storage or changes REF settings.

Run `mise run baremetal:check` for host-only serial transport verification. It exercises the actual capture helper through a local pseudo-terminal; it does not contact REF or DUT and is not a hardware gate.

Build the original Rust RAM payload with `mise run baremetal:build`. The build uses the pinned rkbin checkout described in `stock-loader.json`, its unmodified DDR binary, and a Linux container for the supplied boot_merger. The resulting `build/hello-download.bin` replaces the USB plug stage with our code; the packager's other loader entries are not written to storage by `db`.

`tools/harness.py` captures UART before loading, optionally runs a build argv, and records raw bytes plus a JSON result under `logs/phase-N/`. REF's ADB requires a PTY, so the REF helper base64-frames serial bytes. The verified loader baud is **115,200**, superseding the plan's provisional 1,500,000.

The minimal payload accepts `R` on UART2 to trigger a warm reset back to maskrom. `tools/hello_gate.py` exercises ten consecutive hello/download/reset cycles. While the stock USB plug runs, `rkdeveloptool rd 3` also returns DUT to maskrom. These are software resets; a hung CPU may still need physical power cycling, and no controllable USB power hub is currently connected.

Completed phase receipts (including serial output and GPIO observations) are retained in `evidence/` for review in the repository. Full command logs and downloaded tools remain ignored local artifacts. Commit after each completed phase gate, as requested by the user.

Phase7 development captures raw SC3336 frames on DUT using original Rust sensor and receiver drivers. `mise run baremetal:camera:build` builds the real-camera diagnostic at unity gain/8192 exposure lines; `baremetal:camera:low-light:build` retains the long-exposure/high-gain night profile, and `baremetal:camera:pattern:build` enables the sensor's internal pattern. These overwrite the same download image: check the manifest before loading. Two4MB DMA slots at48/52MB are mapped normal noncacheable for this feature. Ten-frame status and a192×108 RGB preview return over UART; `tools/decode_camera_preview.py` converts a complete serial preview to PNG using Pillow through uv. See [CAMERA-REGISTERS.md](CAMERA-REGISTERS.md) for the driver structure, coverage and limitations.

**Phase7 passed** on the real DUT: a recognizable printed target, ten consecutive clean frames, sensor-control readback and selected REF register comparisons. The timestamped replay has been replaced in the normal build with named sensor/receiver operations. See [evidence/phase-7.json](evidence/phase-7.json) and [PHASE-7-STATUS.md](PHASE-7-STATUS.md). The bounded linear ISP/3A and MicroPython API gates also passed; standalone runtime SD boot now passes as described below.

Range snapshots cover complete CRU, GRF, PMU, D-PHY, CSI0, VICAP and ISP resources at idle and during raw streaming. IOC's readable prefix is retained with an explicit gap: the declared resource faults at0xff570000, and its remaining tail is unverified. Text dumps are generated locally as `ref-dumps/idle.txt` and `streaming.txt`; manifests/CRCs/checksums preserve coverage. REF capture passed after releasing the temporary clock references. Selected DUT readbacks match32 REF configuration registers with explicit masks and DMA/polling differences. See `compare_camera_readbacks.py` for the comparison scope; this is not full-state equivalence or Phase7 completion.

**Phase8 passed for the bounded SC3336 linear profile:**32 ISP/3A feedback frames,31 frame-IRQ parameter updates,186 gain readbacks,80 selected fixed-register matches and an inspected Linux/DUT colour comparison. See [PHASE-8-STATUS.md](PHASE-8-STATUS.md) and [evidence/phase-8.json](evidence/phase-8.json) for exact scope, convergence and limitations. Phase9 now passes the bounded MicroPython hardware/API gate, including two camera captures, GC and five RAM boots; see [PHASE-9-RUNTIME.md](PHASE-9-RUNTIME.md) and [evidence/phase-9.json](evidence/phase-9.json). Unbounded streaming and arbitrary ISP tuning are not qualified. Remaining work is tracked in [PROJECT-MILESTONES.md](PROJECT-MILESTONES.md).

Phase10 preparation is recorded in [PHASE-10-BOOT.md](PHASE-10-BOOT.md). **Power-on to a usable SeedSigner app has not been measured for the replacement runtime; the app is not ported yet.** The user reports at least about30s for the current boot/app path. A separate internal measurement is about13.1ms from bare-metal payload entry to initialized MicroPython, excluding ROM, DDR, storage loading and the app. It does not establish an end-to-end speedup. The2MiB image now boots the spare microSD and passes the real API/camera gate, with a5Hz onboard LED heartbeat. See [evidence/phase-10-sd-boot.json](evidence/phase-10-sd-boot.json). Cold power-on and first-frame timing remain open. The installed app reference inventory is in [APP-REFERENCE-INVENTORY.md](APP-REFERENCE-INVENTORY.md).

USB CDC debugging now passes on the wired DUT0 and additional DUT1, with
script upload, Ctrl-C, reopening and software reset. DUT1 releases its UART
pads for the attached bench LCD/buttons. See [USB-CONSOLE.md](USB-CONSOLE.md)
and [evidence/phase-11-usb.json](evidence/phase-11-usb.json).

The partial [app I/O checkpoint](PHASE-12-APP-IO.md) adds a frozen cooperative
button adapter, core Python features/large integers and bounded bench display
writes/readbacks. **Visible LCD output and the complete SeedSigner app remain
unverified.** The user is away; keep the3-device setup intact and continue
software work using USB recovery. Exact cold-power benchmarking is deferred.

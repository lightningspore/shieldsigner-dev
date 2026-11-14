# Luckfox Mini bare-metal bring-up

This folder contains the independent RAM-only bring-up of a Luckfox Pico Mini A/RV1103. The existing Linux camera implementation in `../firmware/rkaiq-rs/` remains the reference; its algorithm library already uses `#![no_std]` with Linux diagnostics behind a feature.

Start with [NOTES.md](NOTES.md) for the live state, [HISTORY.md](HISTORY.md) for chronological evidence, and [PLAN.txt](PLAN.txt) for the user-provided mission and phase gates.

- Base decision: plain `no_std` Rust, with a portable MicroPython integration later.
- REF: known-good Linux board with SC3336 camera, reached by explicitly selected ADB serial.
- DUT: no microSD, Rockchip maskrom; code downloads are RAM-only.
- No REF boot-partition writes, DUT flash writes, or SD installation without further user authorization.
- Phase success requires real-device evidence; compilation alone never closes a gate.

All new source, helper tools, decisions and evidence for this effort belong here. `logs/phase-N/`, `ref-dumps/` and `.tools/` are ignored local artifacts. Tool downloads retain their original licenses. The new driver implementation will use original code; existing GPL drivers may be studied but are not copied into the permissive implementation. Closed DDR/USB blobs are used as supplied, without disassembly.

Run the read-only Phase 0 inventory with `mise run baremetal:doctor`. It saves fresh evidence under `logs/phase-0/`. It never loads code, flashes storage or changes REF settings.

Run `mise run baremetal:check` for host-only serial transport verification. It exercises the actual capture helper through a local pseudo-terminal; it does not contact REF or DUT and is not a hardware gate.

Build the original Rust RAM payload with `mise run baremetal:build`. The build uses the pinned rkbin checkout described in `stock-loader.json`, its unmodified DDR binary, and a Linux container for the supplied boot_merger. The resulting `build/hello-download.bin` replaces the USB plug stage with our code; the packager's other loader entries are not written to storage by `db`.

`tools/harness.py` captures UART before loading, optionally runs a build argv, and records raw bytes plus a JSON result under `logs/phase-N/`. REF's ADB requires a PTY, so the REF helper base64-frames serial bytes. The verified loader baud is **115,200**, superseding the plan's provisional 1,500,000.

The minimal payload accepts `R` on UART2 to trigger a warm reset back to maskrom. `tools/hello_gate.py` exercises ten consecutive hello/download/reset cycles. While the stock USB plug runs, `rkdeveloptool rd 3` also returns DUT to maskrom. These are software resets; a hung CPU may still need physical power cycling, and no controllable USB power hub is currently connected.

Completed phase receipts (including serial output and GPIO observations) are retained in `evidence/` for review in the repository. Full command logs and downloaded tools remain ignored local artifacts. Commit after each completed phase gate, as requested by the user.

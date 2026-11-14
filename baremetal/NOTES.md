# Current bring-up state

Updated: 2026-11-13 (host local date). **Phases 0–5 passed on hardware. Phase 6 SPI loopback is next.**

## Devices and boundaries

- REF: **standard Luckfox Pico, RV1103** (user-confirmed), ADB `0a523b8b23110ffc`, Linux 5.10.160 `seedsigner-os`. Its live DT model string says Mini, but physical board identity is standard Pico. SC3336 camera detected as `0xcc41` at I²C bus4 address0x30. REF's own camera stays attached.
- DUT: **Pico Mini, RV1103**, former ADB `ec9eda0a3c175664`; USB `2207:110c`, location201. No microSD. RAM downloads only. User connected a **separate SC3336 camera** and confirmed DUT is powered back on; sensor ID was verified by our code.
- Host: macOS26.5.1 arm64, official rkdeveloptool commit `304f073752fd25c854e1bcf05d8e7f925b1f4e14`, GCC arm-none-eabi16.2.0, mise Rust1.93.1/armv7a-none-eabi, uv Python3.13. Tool checkouts live in `.tools/` (ignored).
- Never write REF boot partitions, flash DUT, or install/write DUT SD without further authorization. Do not infer later-phase hardware success from compilation or earlier gates.

## Wiring

Existing UART: REF UART3 → DUT UART2, **115,200 baud**, raw8N1. Red REF TX (`GPIO1_D0`, standard Pico header19) → DUT RX (`GPIO1_B3`, Mini header5). White REF RX (`GPIO1_D1`, standard Pico header20) ← DUT TX (`GPIO1_B2`, Mini header4). Brown common GND, exact REF ground pad unspecified. These paths are proven on hardware.

GPIO: blue REF **GP5/GPIO1_C4/header7** ↔ DUT **GPIO1_C4/header10** (DUT output → REF input). Orange REF **GP4/GPIO1_C5/header6** ↔ DUT **GPIO1_C5/header11** (REF output → DUT input). Linux GPIO52/53. All sixteen transitions passed. Test cleanup returned both DUT pins and REF pins to inputs. On REF GPIO52/53 remain exported through sysfs, input direction. Do not assume both boards share physical header numbering.

## REF runtime bridge

Display supervisor/frontend stopped with SIGTERM; all its periphery GPIO ownership released. Runtime status-only UART3 overlay `baremetal-uart3` enables `/dev/ttyS3`, MMIOff4d0000, GPIO1_D0/D1. Debugfs mounted for pin ownership checks. No startup files changed. Reboot clears this setup and restarts UI; re-check live process IDs and ownership before reapplying overlay.

Never call `S99seedsigner stop` (the script unconditionally starts the app). To restore UI: close captures, disable/remove only our UART3 overlay, then start `/start-seedsigner.sh`, or reboot REF.

## Passed gates and evidence

| Phase | Evidence | Result |
|---|---|---|
|0|`logs/phase-0/doctor-20261114T053121Z.json`|REF shell, UART opens, DUT maskrom, wiring confirmed|
|1|`logs/phase-1/20261114T054010Z/`|Readable stock DDR/USB loader banner at115200; RV1103,64MB DDR2,528MHz DDR|
|2|`logs/phase-2/hello-gate-20261114T054519Z.json`|Ten consecutive original Rust hello runs and automatic UART resets|
|3|`logs/phase-3/phase-3-gate.json`|96.45x cache speedup with equal checksum;1000 timer IRQs in1s;47/47 IRQ echo bytes;heap check|
|4|`logs/phase-4/gpio-gate-20261114T060114Z.json` and `20261114T060058Z/`|16/16 opposite-level transitions matched in both directions; GPIOs released afterward|

Ignored logs are local evidence. HISTORY.md retains attempts and corrections, including the initial wrong-baud diagnosis and REF model correction. PLAN.txt is the original user plan and retains its original two-Mini assumption; this file supersedes that hardware detail.

## Builds, recovery, CPU base

`mise run baremetal:build` builds minimal hello; `mise run baremetal:cpu:build` adds CPU base; GPIO build uses `uv run --python 3.13 python baremetal/tools/build_hello.py --features gpio-test`. All currently output `build/hello-download.bin`; inspect `hello-manifest.json` for features/hash. Phase2/3 baselines preserved under `build/phase-N-baseline/`. Source is original MIT Rust; vendor DDR blob unchanged, not disassembled; GPL drivers studied for register facts only.

Current DUT image before power-off: gpio-test, with CPU base, IRQ UART and commands0/1 for GPIO, Z to release GPIO, R to warm-reset. R via REF UART returns maskrom; stock usbplug supports `rkdeveloptool rd 3`. A stale USB device may still list Maskrom while payload runs—reset before repeated db. No actual USB power controller/hub is exposed; software reset cannot guarantee recovery from a hard hang.

CPU DDR map and register references: CPU-BASE.md. MMU maps64MB DDR cacheable and peripherals device; ACTLR.SMP enabled before cache maintenance. Heap4–8MB, monotonic/no reclaim yet. Provisional camera reservation48–64MB; DMA coherency and actual size remain Phase7 work.

## Latest result: Phase 5 passed

Original I²C4 combined register reads return SC3336 ID0xcc41 at address0x30/register0x3107 in polled and interrupt modes (GIC INTID54). Controller parent explicitly24MHz, SCL100kHz. Camera MCLK configured27MHz from detected GPLL1188MHz /2 ×1/22; GPIO3_C5 releases sensor power-down/reset. Live REF registers and pinmux were studied; REF camera remains untouched.

Hardware evidence `evidence/phase-5.json` and full local `logs/phase-5/20261114T060918Z/`. Wrong address0x31 NAKs correctly in polled and IRQ modes. Deliberately masking the I²C IRQ triggered a ~2ms timeout; cleanup was followed by a successful IRQ sensor read. This validates the software deadline and recovery path, not every possible physical bus fault.

DUT currently runs i2c-test, remains recoverable through UART R, and has its separate camera attached. Blue/orange GPIO lines remain inputs; REF GPIO52/53 are exported inputs. Next Phase6 needs a DUT MOSI-to-MISO jumper for SPI loopback; pin assignment/test code not yet prepared. Do not start Phase7 camera capture until Phase6 gate passes. User requested a commit after each completed phase; Phases0–4 checkpoint is33d0926.

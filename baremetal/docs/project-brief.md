# Project brief

This is the original scope and phase plan for the bare-metal effort (November
2026), lightly edited. Where scope later expanded, the change is noted
inline. For current state, see [status.md](status.md).

## Mission

Run the Luckfox Pico Mini (RV1103, one Cortex-A7, 64 MB DDR2) without Linux:
power-on to a MicroPython prompt in well under a second, with GPIO, I²C, SPI
and an ISP-processed camera image driven by the project's existing Rust 3A code
(`../../firmware/rkaiq-rs/`).

The project adds a plain `no_std` Rust base (chosen over Zephyr so the Rust
camera code could be reused directly), peripheral drivers, a replacement for
the V4L2/kernel layer under the camera code, MicroPython on top, and a fast
boot path.

Out of scope: the video encoder (MPP), the NPU (RKNN), Wi-Fi, Ethernet and USB host.

**Scope expansion after phase 9:** a standalone microSD boot, a USB console
in place of the UART bridge, and a full port of the SeedSigner app onto the
Mini PCB (LCD, buttons, camera). Smartcard support stays out of scope. See
[bringup/milestones.md](bringup/milestones.md).

## Bench setup

- **REF**: a Luckfox board running Buildroot Linux. It is the reference camera
  system, the UART bridge (REF UART3 ↔ DUT UART2, 115,200 baud) and the test
  partner for GPIO/I²C/SPI. Its storage is never modified.
- **DUT**: a Pico Mini with no SPI NAND, loaded through Rockchip maskrom over USB.
- Wiring is TX/RX/GND only, at 3.3 V logic. Power rails are never joined.
  Wiring details are in `devices.json`.

## Ground rules

1. **Proven on hardware.** A phase passes only when its gate runs on the
   real DUT. Evidence goes in `logs/phase-N/` and receipts in `evidence/`.
2. **The reference stays intact.** Never write REF's boot partitions.
3. **RAM-only DUT writes** unless persistent storage is explicitly approved.
   That approval was later given for a dedicated microSD card.
4. **Physical actions are batched**, such as replugging, moving the camera
   or rewiring. Everything else is decided and logged.
5. **Licensing.** GPL drivers (Linux, U-Boot, Luckfox SDK) are read for
   register layouts, and new code is written from that. Rockchip's closed
   blobs (DDR init, loaders) are used unmodified and never disassembled.
6. **Electrical safety.** All boards use 3.3 V logic. Never connect power
   rails between boards or drive a pin from both sides.
7. **Running log.** Keep `NOTES.md` and `HISTORY.md` current. Both now live in
   [journal/](journal/).
8. **One phase at a time.** Reference-capture work on REF may run in parallel.

## Phase plan and gates

| Phase | Goal | Gate | Outcome |
| --- | --- | --- | --- |
| 0 | Host and REF reachable | DUT listed in maskrom, REF shell works, REF UART opens | Passed |
| 1 | Test harness (`tools/harness.py`) | Stock loader/DDR banner captured | Passed. The loader baud is 115,200, not the assumed 1,500,000. |
| 2 | Hello from bare metal | Own `@@PASS hello` after DDR init, 10 runs in a row | Passed |
| 3 | CPU base: MMU, caches, timer, GIC | Cached loop ≥10× faster, timer within 1%, UART echo | Passed ([hardware/cpu-base.md](hardware/cpu-base.md)) |
| 4 | GPIO and pinmux | All 16 cross-board transitions match | Passed |
| 5 | I²C | Read the SC3336 chip ID | Passed |
| 6 | SPI | 4 KB loopback at three clock rates, zero errors | Passed |
| 7 | Camera raw capture | Recognisable raw image, 10 clean frames, then named drivers | Passed ([bringup/phase-07-camera.md](bringup/phase-07-camera.md)) |
| 8 | ISP with Rust 3A | YUV output, 3A converges, comparable to REF | Passed for the bounded linear profile ([bringup/phase-08-isp.md](bringup/phase-08-isp.md)) |
| 9 | MicroPython | REPL script: GPIO, sensor ID, SPI loopback, frame capture | Passed ([bringup/phase-09-runtime.md](bringup/phase-09-runtime.md)) |
| 10 | Fast boot | Measured power-on to REPL and to first frame | Standalone microSD boot passed. Cold timing not externally measured ([bringup/phase-10-boot.md](bringup/phase-10-boot.md)). |
| 11 | USB console *(added)* | CDC REPL, script upload, Ctrl-C, reopen, reset | Passed ([hardware/usb-console.md](hardware/usb-console.md)) |
| 12 | SeedSigner app *(added)* | Real workflows on the Mini PCB | In progress, mostly complete ([status.md](status.md)) |

## Main risks identified up front

| Risk | Mitigation used |
| --- | --- |
| `rkdeveloptool db` might not run arbitrary stage-2 code | Tested with a hello payload first. It works. |
| Camera clocks and power domains not set up by the loader | Replayed CRU/PMU writes, then diffed against REF register dumps |
| Cache/DMA coherency on frame buffers | Frame buffers are mapped non-cacheable |
| ISP parameter timing | Parameters are applied on the frame interrupt, as the kernel does |
| A hung DUT needs a manual replug | USB warm reset, later backed up by a hardware watchdog |
| Slow frame transfer over UART | Cropped or downscaled previews, then the USB console |

## Primary references

- The Luckfox Pico SDK kernel and U-Boot, for device trees and register maps
  (study only).
- rkbin, for the DDR init blob and `boot_merger` configurations.
- rkdeveloptool, for maskrom loading.
- The MicroPython porting guide, and the Zephyr Luckfox Pico Ultra bring-up for
  comparison.
- The REF board itself: live register dumps, dmesg and the device tree.

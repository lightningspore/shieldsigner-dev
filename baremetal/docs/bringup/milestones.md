# Milestones

After phase 9 passed, scope grew beyond the original brief
([project-brief.md](../project-brief.md)). These milestones track that larger
scope.

| # | Milestone | State |
| --- | --- | --- |
| 1 | **Standalone microSD boot.** The ROM loads the unchanged DDR init and the runtime directly, with no U-Boot. | Done. The runtime and later the full app boot from a dedicated card. A 5 Hz LED heartbeat confirms startup. See [phase-10-boot.md](phase-10-boot.md) and [phase-10-sd-boot](../../evidence/phase-10-sd-boot.json). |
| 2 | **USB debugging without UART wires.** A CDC REPL with script upload, Ctrl-C, reopen and reset. | Done on DUT0 and DUT1. DUT1 releases its UART pads for the PCB buttons. See [usb-console.md](../hardware/usb-console.md). |
| 3 | **SeedSigner app on MicroPython and the Mini PCB.** Original app source, native LVGL screens, real LCD, buttons and camera. | Most workflows are verified on the device. See [status.md](../status.md). |
| 4 | **Cold-boot timing.** Power-on to a usable main screen, and to camera readiness. | Open. Deferred so the app port could come first. |

## Timing baseline

The reference Linux image takes about 30 s from power-on to a usable app,
according to the operator. That figure is a reported baseline, not a project
measurement. The only internal measurement so far is about 13.1 ms from
payload entry to an initialized MicroPython. It excludes the ROM, DDR init,
storage loading and the app, so it does not show an end-to-end speedup. The
first app boot from microSD felt fast, but that is a subjective observation
and no timing was recorded
([phase-12-app-sd-quick-test](../../evidence/phase-12-app-sd-quick-test.json)).

## Constraints carried forward

- REF keeps its working Linux installation as the comparison and recovery
  system.
- Smartcard software is out of scope. The PCB hardware and connectors are kept.
- The bench device (DUT1) has the 240×240 LCD, the buttons and its own SC3336
  camera. No extra camera wiring is needed for app development.
- Physical actions are requested only when the next hardware step needs them.

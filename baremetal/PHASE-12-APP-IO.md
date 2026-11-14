# SeedSigner app I/O checkpoint

This is a partial app-port checkpoint. Frozen input code, native display writes,
register readbacks and Python guards pass on DUT1. A working SeedSigner app,
physical switch press/release qualification and visible LCD output are not yet
proved. Smartcard software is excluded by user instruction.

## Current bench and recovery

- REF: standard Luckfox Pico, original Linux/card and camera modules preserved,
  ADB0a523b8b23110ffc; UART3 bridges only DUT0.
- DUT0: original wired Mini A, USB location201, firmware USB serial
  `rv1103-dev-001`. Camera points toward DUT1. Keep the GPIO/SPI test wiring.
- DUT1: added Mini A without onboard flash, location101, serial `rv1103-dut1`,
  existing Linux-tested LCD/button board attached. Its runtime uses USB only;
  UART42/43 are released as inputs at Rust entry and its UART IRQ is disabled.
- Both targets are RAM-only during this checkpoint. No storage writes occurred.
  The spare SD still contains the previously verified5Hz diagnostic runtime.
- The user is away. Continue using software reset/download; do not require new
  wiring/aiming. `mise run baremetal:usb:dut1:reset` resets only the unique app
  USB identity; `baremetal:usb:dut1:ram:gate` checks location/build/hash before db.
  The reset helper now drains the output and leaves a short delivery interval
  before close. One undrained reset failed to reach maskrom, but a liveness
  script proved DUT1 still responsive; the drained retry recovered it. No CPU
  hang was proved. USB-only firmware also no longer waits on unused UART TX.

## Native bench240 contract

The explicit `bench-ui` feature includes USB-only operation. Other runtime
builds reject display initialization. It is not the main HOTHMI carrier profile.

| Function | Pins / contract |
| --- | --- |
| LCD | DC56, reset57; SPI0 CS48/SCK49/MOSI50; C3/MISO left untouched |
| Buttons, mask bits0..7 | Up58, Down53, Left59, Right54, Press52, Key155, Key243, Key342 |
| Input electrical setup | GPIO inputs and native-domain internal pullups; preserves DC/reset outputs |
| Pixels | RGB565 big-endian;240x240 canvas; exact buffer length and in-bounds rectangle required |
| Transfers | Derived200MHz source/divisor20 configures10MHz SPI; bounded polled TX-only FIFO; USB serviced between chunks |

`display.init('bench240')`, `fill(color)`, `blit(x,y,w,h,buffer)`, `buttons()` and
bounded `status()` readbacks are available. Full-screen fill clears the complete
240x320 ST7789 backing RAM before restoring bench orientation, so off-canvas
rows do not retain stale pixels. The write-only frame counter is length minus1.
The full known-good bench porch/power/gamma register values are explicit.

`software_spi=True` selects a slow GPIO SPI diagnostic on the same three bus
pads (approximately100kHz or slower). It leaves unrelated pads alone. It is not
an app performance result. Default hardware operation remains selected.

Registers on DUT1 prove DC/reset output direction, button input directions,
GPIO muxes, native pulls, SPI mux and divisor. Six invalid profile/color/window/
buffer calls were rejected on the real interpreter, including a very large
coordinate. These checks do not prove electrical continuity or screen contents.

## Frozen app input and Python runtime

`app/seedsigner_port/buttons.py` is an original cooperative adapter matching the
reference key names and10ms debounce/225ms first repeat/250ms subsequent repeat.
It supports polling, waiting with a service callback, raw level checks and
injected clock/input tests. Inputs held at startup/reset are suppressed until a
stable release. DUT1 reports mask64 (Key2 low) across200 samples with no changes;
its physical cause is unknown. Startup suppression passed with that real level.
Synthetic edges prove the algorithm, not physical switch operation.

The modules are frozen as bytecode with the pinned MicroPython1.27.0 compiler
and micropython-lib6ae440a8a144233e6e703f6759b7e7a0afaa37a4. Build receipts
include app source hashes and the host compiler hash. Core built-ins, MPZ large
integers, slicing/formatting and source-line tracebacks are enabled. Frozen
imports work without a filesystem. Filesystem stat/open remains unavailable;
no host files or implicit package downloads are used by the runtime. Memory
layout and the1MiB image/stack guard are preserved.

`mise run baremetal:app:bench:build` builds DUT1.
`mise run baremetal:app:buttons:gate` imports and exercises the frozen adapter on
that target, including32-bit timer wrap,256-bit arithmetic, held-key suppression
and display guards.19 host tests pass. The expanded core's full GPIO/I2C/SPI/
two-camera/settings/GC gate also passed on wired DUT0. The fixture gate rejects
USB-only DUT1 before any GPIO output or loopback test.

## Optical evidence and remaining work

Camera observer scripts on DUT0 capture real640x480 NV12 and export validated
RGB previews. Independent captures have different pixel hashes. Views saved in
ignored logs include `phase-11/lcd-observed-pattern.png`, `lcd-observed-white.png`,
`lcd-observed-full-init.png`, `lcd-observed-software-spi.png`, a256x256 detail
crop and `phase-12/lcd-observed-full-ram-red.png`.

No recognizable quadrant/white/red fill is visible in the available view. It
is close, oblique and cropped; whether it shows the panel face adequately is
uncertain. Do not infer either successful LCD operation or a proved hardware
fault from a successful SPI write. Hardware SPI, full initialization, backing-
RAM fill and slow GPIO SPI were tried with register readbacks; optical gate
remains open. Do not blindly try the carrier pin map, which drives different
button nets. Keep working on independent app software while the user is away.

The actual SeedSigner controller/views, native rendering/asset adapters,
camera/QR workflows and signing/models still need porting and validation.
DUT1 also answered the SC3336 probe and captured a real frame195651Z (a separate carton scene). A post-capture LCD reinitialization/fill/readback succeeded, so camera and display writes can be exercised locally while DUT0 remains the external observer.
A hardware screen demo, input adapter or frozen import is not app completion.
Cold-power benchmarking remains deferred by the user. Standalone USB/app SD
packaging, real app boot/navigation and camera preview readiness remain open.

Checkpoint receipt: [evidence/phase-12-app-io.json](evidence/phase-12-app-io.json).


## Local native camera adapter checkpoint

`display.blit_nv12(frame)` accepts the camera's read-only640x480 NV12 buffer,
center-crops480x480 and downsamples to240x240 using integer BT.601 RGB565.
It uses a480-byte row buffer, with USB servicing between SPI chunks and no
Rust frame allocation. Two captures on DUT1 passed without LCD reinitialization:
233/232ms native conversion plus SPI submission; capture itself remained about
5.26s. These are bounded operations, not continuous preview FPS or app startup.
The GPIO/mux/divisor readbacks stayed unchanged and Rust heap usage returned
to baseline. Two color/crop/bounds host tests and19 bring-up tests pass.
Receipt: [evidence/phase-12-camera-blit.json](evidence/phase-12-camera-blit.json).
The panel's visible output is still unconfirmed.

The existing locked SeedSigner LVGL screen corpus now cross-compiles to a
542-object archive with the local official Arm C++/newlib toolchain. See
[ui/README.md](ui/README.md). This is build preparation only: the archive is
not linked into either running firmware, and no native screen/controller pass
is claimed. Next are runtime allocation/constructors/unwind support, image and
stack layout validation, a MicroPython interface and real app screen tests.

# Phase 12: app I/O checkpoint

Current: the operator-confirmed Mini PCB now has visibly working LCD output,
a displayed local-camera capture and all eight physical switches verified.
See [MINI-PCB-IO.md](../hardware/mini-pcb-io.md) and
[evidence/phase-12-mini-pcb.json](../../evidence/phase-12-mini-pcb.json).
The earlier GPIO56/57 bench profile was for a different board; its LCD-negative
results are superseded. Full app startup and continuous preview remain open.

## Current bench and recovery

- REF: standard Luckfox Pico, original Linux/card and camera modules preserved,
  ADB0a523b8b23110ffc; UART3 bridges only DUT0.
- DUT0: original wired Mini A, USB location 201, firmware USB serial
  `rv1103-dev-001`. Camera points toward DUT1. Keep the GPIO/SPI test wiring.
- DUT1: added Mini A without onboard flash, location 101, serial `rv1103-dut1`,
  existing Linux-tested LCD/button board attached. Its runtime uses USB only;
  UART42/43 are released as inputs at Rust entry and its UART IRQ is disabled.
- Both targets are RAM-only during this checkpoint. No storage writes occurred.
  The spare SD still contains the previously verified5Hz diagnostic runtime.
- The operator is away. Continue using software reset/download; do not require new
  wiring/aiming. `mise run baremetal:usb:dut1:reset` resets only the unique app
  USB identity; `baremetal:usb:dut1:ram:gate` checks location/build/hash before db.
  The reset helper now drains the output and leaves a short delivery interval
  before close. One undrained reset failed to reach maskrom, but a liveness
  script proved DUT1 still responsive; the drained retry recovered it. No CPU
  hang was proved. USB-only firmware also no longer waits on unused UART TX.

## Historical separate bench240 contract (not this PCB)

The explicit `bench-ui` feature includes USB-only operation. Other runtime
builds reject display initialization. It is not the main HOTHMI carrier profile.

| Function | Pins / contract |
| --- | --- |
| LCD | DC56, reset 57; SPI0 CS48/SCK49/MOSI50; C3/MISO left untouched |
| Buttons, mask bits 0..7 | Up58, Down53, Left59, Right54, Press52, Key155, Key243, Key342 |
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
reference key names and 10ms debounce/225ms first repeat/250ms subsequent repeat.
It supports polling, waiting with a service callback, raw level checks and
injected clock/input tests. Inputs held at startup/reset are suppressed until a
stable release. DUT1 reports mask 64 (Key2 low) across 200 samples with no changes;
its physical cause is unknown. Startup suppression passed with that real level.
Synthetic edges prove the algorithm, not physical switch operation.

The modules are frozen as bytecode with the pinned MicroPython1.27.0 compiler
and micropython-lib6ae440a8a144233e6e703f6759b7e7a0afaa37a4. Build receipts
include app source hashes and the host compiler hash. Core built-ins, MPZ large
integers, slicing/formatting and source-line tracebacks are enabled. Frozen
imports work without a filesystem. Filesystem stat/open remains unavailable;
no host files or implicit package downloads are used by the runtime. Memory
layout and the 1MiB image/stack guard are preserved.

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
`lcd-observed-full-init.png`, `lcd-observed-software-spi.png`, a 256x256 detail
crop and `phase-12/lcd-observed-full-ram-red.png`.

No recognizable quadrant/white/red fill is visible in the available view. It
is close, oblique and cropped; whether it shows the panel face adequately is
uncertain. Do not infer either successful LCD operation or a proved hardware
fault from a successful SPI write. Hardware SPI, full initialization, backing-
RAM fill and slow GPIO SPI were tried with register readbacks; optical gate
remains open. Do not blindly try the carrier pin map, which drives different
button nets. Keep working on independent app software while the operator is away.

The actual SeedSigner controller/views, native rendering/asset adapters,
camera/QR workflows and signing/models still need porting and validation.
DUT1 also answered the SC3336 probe and captured a real frame195651Z (a separate carton scene). A post-capture LCD reinitialization/fill/readback succeeded, so camera and display writes can be exercised locally while DUT0 remains the external observer.
A hardware screen demo, input adapter or frozen import is not app completion.
Cold-power benchmarking remains deferred by project decision. Standalone USB/app SD
packaging, real app boot/navigation and camera preview readiness remain open.

Checkpoint receipt: [evidence/phase-12-app-io.json](../../evidence/phase-12-app-io.json).


## Local native camera adapter checkpoint

`display.blit_nv12(frame)` accepts the camera's read-only640x480 NV12 buffer,
center-crops480x480 and downsamples to 240x240 using integer BT.601 RGB565.
It uses a480-byte row buffer, with USB servicing between SPI chunks and no
Rust frame allocation. Two captures on DUT1 passed without LCD reinitialization:
233/232ms native conversion plus SPI submission; capture itself remained about
5.26s. These are bounded operations, not continuous preview FPS or app startup.
The GPIO/mux/divisor readbacks stayed unchanged and Rust heap usage returned
to baseline. Two color/crop/bounds host tests and 19 bring-up tests pass.
Receipt: [evidence/phase-12-camera-blit.json](../../evidence/phase-12-camera-blit.json).
The panel's visible output is still unconfirmed.

The existing locked SeedSigner LVGL screen corpus now cross-compiles to a
542-object archive with the local official Arm C++/newlib toolchain. See
[ui/README.md](../../ui/README.md). This is build preparation only: the archive is
not linked into either running firmware, and no native screen/controller pass
is claimed. Next are runtime allocation/constructors/unwind support, image and
stack layout validation, a MicroPython interface and real app screen tests.


## Genuine Home renderer on wired DUT0

The native screen library is now linked and exercised on actual DUT0, with a
headless framebuffer so its original GPIO fixture stays usable. The exported
frame was decoded and visually inspected: Home title, power icon, Scan/Seeds/
Tools/Settings icons and labels, and orange selection highlight are correct.
Real keypad callbacks select Scan and Seeds. Malformed JSON and missing-title
exceptions return to Python, followed by successful renders. Twenty error/
render/GC cycles preserve the42015-byte native heap baseline; the complete
GPIO/I2C/SPI/two-camera/settings/GC gate also passes with the larger image and
relocated stacks. Home render measured 11ms after UI initialization; this is not
power-to-app timing. See [ui/README.md](../../ui/README.md) and
[evidence/phase-12-native-ui.json](../../evidence/phase-12-native-ui.json).

DUT1 still runs the prior bench-ui camera/blit image. Physical LCD rendering,
real button edges and the complete app/controller remain open. The next step
is the combined app-ui build on DUT1, retaining its USB-only recovery identity
and released UART/button pads, then actual controller/view integration.


## Native renderer and cooperative adapter on DUT1

DUT1 now runs `app-ui` with its unique USB identity and released UART/button
pads. The final Home framebuffer matches DUT0 byte for byte; native rendering
plus SPI submission took 194ms in this gate. The frozen cooperative adapter
suppressed the stable physical mask 64, routed injected accepted edges to the
real Seeds callback, captured/submitted a local camera image and restored Home
without LCD reinit. Native heap returned to42015 bytes; all UART mux/output/IER/
IRQ readbacks remained zero. Twenty-two host tests pass. The ST7789 inversion
baseline now matches the installed driver's normal-color policy (INVON0x21).

No recognizable Home is visible in the external observer image, including after
that correction. Physical output is still an open gate, not a qualified LCD or
proved hardware fault. Continue app/controller software while the operator is away.
The wired DUT0 harness now rejects an app/DUT1 profile before enumeration/load;
use the explicit target build/loader sequence. Final receipts and exact source/
image/log hashes are in [evidence/phase-12-dut1-native-ui.json](../../evidence/phase-12-dut1-native-ui.json).
DUT0 still runs the prior38bf1ed headless UI runtime; its camera remains the
observer. Shared build artifacts now contain DUT1's app-ui image, not DUT0's.


## Original navigation and broader native registry on DUT0

DUT0 now runs the43-builder native registry; `ui.screens()` exposes exact names.
Actual list Down/Enter, top-nav Back, 2-tile grid Right/Enter and Home restore
passed, with five post-warmup cycles preserving one53300-byte native heap baseline.
The first font-cache warmup is recorded separately; it is not treated as a leak
or hidden by a moving baseline. The actual passphrase keyboard returns255ASCII/
254UTF8 bytes exactly and explicitly rejects256-byte results instead of silently
truncating. Wider text and pending-event/lifecycle policies remain port limits.
Full GPIO/I2C/SPI/two-camera/settings/GC also passed on this final image.

The original complete Destination/BackStack classes are now frozen, with source
pins/hashes and narrow type/dataclass transformations. Three differential host
tests compare against original CPython classes; actual frozen route/redirect/
equality/redaction/backstack tests pass on DUT0. Total25 host tests pass.
This does not port the full Controller or replace production Views with fixtures.
See [app/README.md](../../app/README.md), [ui/README.md](../../ui/README.md) and
[evidence/phase-12-navigation-registry.json](../../evidence/phase-12-navigation-registry.json).
DUT1 remains on54bfdca's prior Home-only app-ui image; shared build artifacts now
contain the final wiredDUT0 native-ui image. The physical LCD gate stays open.


## Basic app screen argument/result adapters

The frozen backend now accepts the original three basic Screen class names and
argument dictionaries, instead of requiring hand-written native JSON. Inherited
field defaults come from pinned original dataclasses; config parity is compared
to the existing Linux adapter. Button options/icons/colors, translation opt-out,
layout/scroll defaults and original#FF9F0A selection color are preserved. Actual
renderer selection/back callbacks pass through the validated result adapter on
DUT0. Specialized contracts, configured hold actions and custom button styling
remain explicit errors, and raw renders cannot reuse a stale button-count validator.
Twenty-nine host tests pass. Current shared artifacts/DUT0 image include this
adapter, boot204642Z / gate 204714.964041Z. DUT1 remains unchanged54bfdca.
The full Controller/View dependency graph and startup are still incomplete;
physical LCD/buttons and standalone app boot remain open. Receipt:
[evidence/phase-12-screen-contracts.json](../../evidence/phase-12-screen-contracts.json).


## Original settings schema/parser dependency

The native app freeze now includes the original60-entry settings schema and
SettingsQR parser, with reproducible provenance and explicit English-only asset
capability. All 60 device-exported public entries match the source-derived schema;
32 host tests pass, including comparison against original app classes. Actual
double precision and 30 parser/GC cycles pass on finalDUT0 image, followed by the
basic-screen and complete GPIO/I2C/SPI/two-camera/settings/GC regression gates.
Minimal diagnostic and native app builds both compile; float-bearing schema
code is excluded from the diagnostic freeze. Finalboot205505Z, schema205541Z,
screen205544.153536Z and camera205544.787006Z receipts are linked in
[evidence/phase-12-settings-schema.json](../../evidence/phase-12-settings-schema.json).

This is not the full Settings service: no user settings are read or applied,
and original numeric-bound metadata still needs its actual setter enforcement.
Platform options in the schema do not qualify unsupported native hardware;
persistence/device-side effects, full Controller startup, models/crypto/QR and
physical LCD/buttons remain open. DUT1 stays on54bfdca; shared artifacts/current
DUT0 now contain the final double-enabled native-ui image. No storage writes.

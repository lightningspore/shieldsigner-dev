# Native screen runtime

The genuine locked SeedSigner LVGL Home screen runs on wired DUT0 behind
`native-ui`, using a headless framebuffer. DUT1 now runs `app-ui`, which
submits the same native pixels to the explicit bench LCD backend. Its visible
panel output remains unconfirmed.
The C ABI bridge now registers all43 locked native screen builders; `ui.screens()`
returns their names. Unknown names fail explicitly. Registration does not qualify
each screen/configuration or its wallet workflow. There is no replacement wallet flow.

Run `mise run baremetal:cxx:setup`, then `mise run baremetal:ui:library:build`.
The complete official Arm14.3.rel1 Darwin arm64 toolchain is checksum-pinned in
`../cxx-toolchain.json` and extracted into ignored `.tools/`; it does not replace
system compilers or the existing MicroPython C toolchain. Other host architectures
need a separately pinned official bundle.

The build verifies the application/screens/LVGL commits against
`../../firmware/lvgl-app/sources.lock.json`, copies the screen sources into a
disposable build directory, and applies the existing Linux port's patch series.
Shared native helper headers, branding generation and the original font/image
sources are reused. Source caches remain unchanged. Output is
`../build/ui/libsignerui.a` plus `manifest.json`; generated sources, objects,
logs and the toolchain stay local. The archive is recreated on every build to
avoid retaining stale hash-named members.

The bridge uses LVGL partial RGB565 rendering, hardware-mode keypad events and
screen callbacks. C++ exceptions are caught at its callable C boundaries.
`syscalls.c` is a freestanding newlib ABI adapter: stdout/stderr use the existing
console, unavailable file/time services return errors, and `_sbrk` fails.
The runtime now uses the existing reclaiming Rust heap for C allocation,
including newlib reentrant calls. It invokes global constructors after heap/MMU
initialization and preserves ARM exception/unwind metadata. The GNU bare-metal
runtime requires `--target2=rel`; LLD's default GOT-relative relocation caused
an instruction abort on malformed JSON. The change is consistent with the
[LLVM bare-metal linker fix](https://reviews.llvm.org/D149458), and real hardware
now catches malformed JSON/missing-title errors and continues rendering.

`mise run baremetal:ui:build` builds the wired target. `baremetal:ui:gate`
checks real Home rendering, read-only framebuffer, Scan and Seeds selection
callbacks and error recovery, then exports the240x240 RGB565 frame. Decode it
with `uv run --with pillow==11.3.0 python baremetal/tools/decode_ui_frame.py
<serial.bin> <output.png>`. `baremetal:ui:stress:gate` checks20 error/render/GC
cycles. All passed on DUT0, followed by the full GPIO/I2C/SPI/two-camera gate.
The inspected framebuffer has the real Home grid, icons, labels and selection.
Receipt: [../evidence/phase-12-native-ui.json](../evidence/phase-12-native-ui.json).

The1,486,708-byte raw image and BSS end0x00177618 stay below the4MiB Rust heap.
Native UI moves SVC/IRQ stacks to27–28/29–30MiB with unmapped26/28MiB guard
sections. Rust heap4–16MiB, Python GC16–24MiB and camera/USB DMA48–64MiB
remain unchanged. The115200-byte shadow frame starts at32MiB. Baseline builds
retain their original linker/stack layout. IRQ handlers do not allocate.

`ui` provides init/render/key/tick/event/status and a read-only framebuffer view.
Rendering copies bounded rectangles to the shadow frame; `app-ui` additionally
selects the explicit bench LCD backend. DUT1 passed its native screen/callback
gate, local camera conversion/blit and Home restore without LCD reinit, plus
actual UART-pad/IRQ release readbacks. Physical switch edges and recognizable
optical output are still unverified. The current wired build registers43 builders;
DUT1 still runs the earlier Home-only build. The actual frozen
controller/view adapters, other screens, models/crypto/QR and standalone app
boot still need work. This is a renderer milestone, not a running full app.

First use the wired DUT0 build with UART recovery; its UI test backend must not
drive the attached GPIO/loopback fixture. DUT1 uses the explicit bench profile
and keeps UART pads released. A compiled archive is not a hardware pass.

Upstream attribution is preserved in the pinned source trees and existing
`firmware/lvgl-app` source/asset notices. SeedSigner and LVGL carry their upstream
MIT notices; generated branding retains its existing provenance. The official
Arm bundle includes GCC/newlib/libstdc++ third-party licenses and runtime
exceptions: retain the applicable notices when distributing linked binaries.
No toolchain binary is committed here.


The frozen `seedsigner_port.native_ui.ScreenSession` accepts upstream builder
names and configuration dicts, serializes with pinned MicroPython's actual JSON
module and services native timers plus cooperative debounced input. It suppresses
keys held across screen transitions; accepted navigation/repeat events emit
complete keypad pulses. It does not implement wallet View routing or replace
unsupported screens. Long-hold and app lifecycle policies still need integration.
Run `baremetal:ui:dut1:build`, reset DUT1, then `baremetal:usb:dut1:ram:gate`
and `baremetal:ui:dut1:gate`. The wired harness rejects DUT1/app images before
any enumeration/download, protecting the original GPIO fixture from an accidental
LCD-pin build. Receipt: [../evidence/phase-12-dut1-native-ui.json](../evidence/phase-12-dut1-native-ui.json).


## Registry and original navigation checkpoint

The generated native registry now matches the existing Linux host's43 builder
names and is recorded in the build manifest/cache key. The current `native-ui`
image runs on wired DUT0; DUT1 remains on its prior Home-only `app-ui` image.
`baremetal:ui:registry:gate` verifies actual list Down/Enter, top-nav Back,
2-tile grid Right/Enter and repeated transitions back to Home. Native font caches
warm on the first cycle; five subsequent identical cycles must preserve one
fixed absolute heap baseline. The final gate stabilizes at53300bytes after the
text-widget checks. This does not qualify every registered screen or workflow.

`baremetal:ui:text:gate` drives the actual passphrase keyboard with PUBLIC test
strings:255ASCII bytes and127 two-byte accented characters return exactly;
256-byte results raise instead of silently truncating. Consumed event text is
cleared through volatile writes. The current255-byte event-text bound remains
an explicit port limitation, and the single pending-event slot, long-hold,
full lifecycle and View result mapping need review before wider app workflows.
This is not signing/seed/passphrase workflow qualification.

Original Destination/BackStack classes are frozen with reproducible provenance;
see [../app/README.md](../app/README.md). Full Controller/Views, settings/model/
crypto/storage/QR dependencies and startup integration remain outstanding.
Receipt: [../evidence/phase-12-navigation-registry.json](../evidence/phase-12-navigation-registry.json).


The higher-level frozen adapter now maps three reviewed original app screen
classes (Home, ordinary lists and large-button grids) to native configurations
using extracted original defaults. This is narrower than the43 native builders;
unknown specialized Screen contracts and configured hold/styling semantics reject
explicitly. The new hardware gate takes class-style arguments and ButtonOption
objects through the real renderer and returns validated choice/back codes. See
[../app/README.md](../app/README.md) and
[../evidence/phase-12-screen-contracts.json](../evidence/phase-12-screen-contracts.json).

# Native screen runtime

The genuine locked SeedSigner LVGL Home screen runs on wired DUT0 behind
`native-ui`, using a headless framebuffer. DUT1 still runs the prior bench-ui
image; physical LCD rendering is the next gate.
The staged C ABI bridge initially registers the genuine `main_menu_screen` only;
unsupported screen names fail explicitly. There is no replacement wallet flow.

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
selects the explicit bench LCD backend. That combined feature has not yet been
loaded or validated. Registry support is currently Home only; the actual frozen
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

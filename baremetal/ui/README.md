# Native screen-library preparation

This is a build-only port of the existing locked SeedSigner LVGL screen library.
It is not yet linked into the RV1103 runtime. Neither board runs these screens.
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
Before loading this code, the runtime still needs:

- Real reclaiming C allocation, including newlib reentrant entry points.
- Global constructors, libstdc++/newlib linkage and preserved ARM unwind tables.
- Measured image/BSS size and validated stack/heap/camera/USB memory separation.
- Rust flush/fatal callbacks and a MicroPython UI interface.
- Actual frame rendering/navigation gates, then app controller integration.

First use the wired DUT0 build with UART recovery; its UI test backend must not
drive the attached GPIO/loopback fixture. DUT1 uses the explicit bench profile
and keeps UART pads released. A compiled archive is not a hardware pass.

Upstream attribution is preserved in the pinned source trees and existing
`firmware/lvgl-app` source/asset notices. SeedSigner and LVGL carry their upstream
MIT notices; generated branding retains its existing provenance. The official
Arm bundle includes GCC/newlib/libstdc++ third-party licenses and runtime
exceptions: retain the applicable notices when distributing linked binaries.
No toolchain binary is committed here.

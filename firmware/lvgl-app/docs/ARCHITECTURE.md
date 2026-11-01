# Current architecture

[Overview](../README.md) · [Build](BUILD.md) · [Divergences](../DIVERGENCES.md)

The application remains CPython 3.12 on Linux. `python/app.py` starts the pinned
original application with reviewed process-local adaptations. Its Controller,
Views, models, wallet derivation, parsers and signing code retain authority over
application behavior. Original sources are checked before adaptation.

| Layer | Responsibility | Main sources |
|---|---|---|
| Application bridge | Startup, class/result contracts, settings separation, lifecycle | `python/app.py`, `screen_bridge.py`, `contracts.py`, `guards.py` |
| Python runtime | Map supported screen calls to typed native messages; handle results | `python/runtime.py`, `transport.py`, `renderer_bridge.py` |
| Native renderer | LVGL widgets, input focus, partial rendering and protocol handling | `native/host.cpp`, pinned LVGL screen library, `patches/` |
| Camera/QR | Camera ownership, preview delivery and binary QR decoding | `python/camera_scan.py`, Rust camera runtime in `firmware/rkaiq-rs` and native ZXing-C++ worker |
| Hardware boundary | Display/button integration and bounded native I/O | `python/luckfox.py`, installed Rust LCD/frontend helpers |
| Packaging | Hashes, native ABI, checked bytecode, inactive overlay and provenance | `package.py`, `image_stage.py`, `attach_image_bundle.py` |

Python and the native renderer communicate over framed pipes. Messages carry
bounded rectangles and typed events instead of Python drawing each widget into a
full PIL framebuffer. LVGL uses a 9,600-byte partial draw buffer. This avoids a
mandatory full-screen LVGL buffer, but does not eliminate every image allocation.

The scan adapter keeps the existing camera owner, readiness/retry rules,
latest-frame pacing and shutdown behavior. Its native QR reader feeds decoded
bytes to the original application decoder. Preview pixels and a valid camera
frame are different from successful QR parsing; tests distinguish those paths.

Workers are started when needed and joined/stopped at lifecycle boundaries.
Process count and thread count change with the workload; a Home observation is
not a camera-scanning topology. The Python interpreter, native LVGL process,
camera owner and QR worker each have their own memory accounting. See
[Memory](MEMORY.md) before adding their figures together.

The image selects LVGL through a supervised launcher and keeps a PIL rollback
launcher. Interactive development uses separate settings and refuses competing
owners. Temporary hardware checks deploy a verified bundle without flashing;
that is distinct from the installed image launching normally after boot.

Sources are pinned separately for the application, portable screens, LVGL and
reference projects. The portable screen library is reused without adopting the
MicroPython application or the Raspberry Pi camera stack. Current source pins
and every local patch are linked in [Divergences](../DIVERGENCES.md).

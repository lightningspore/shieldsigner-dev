# SeedSigner MicroPython port code

Work in progress; this is not yet the complete SeedSigner application.

`seedsigner_port/buttons.py` is an original MIT cooperative adapter for the
installed SeedSigner button names and10/225/250ms timing contract. It polls the
explicit bench240 backend, suppresses keys held at startup/reset until released,
and supports an injected clock/input for semantic tests. The real hardware
currently reports Key2 low; its cause and physical press/release tests remain
open. Tests using injected edges do not qualify the switches.

The port modules are frozen into the runtime using the pinned MicroPython
manifest/mpy-cross toolchain. The runtime permits frozen imports; filesystem
stat/open remains unavailable until an actual SD filesystem driver exists.
Core built-ins, arbitrary-size integers and source-line tracebacks are enabled.
No CPython threading, Pillow, Linux driver, smartcard or signing fallback is
implemented here. Existing wallet/controller/views and cryptographic flows
still need their actual port and validation.

Reference contract: REF snapshot seedsigner/hardware/buttons.py (installed
lvgl-dev.cb6170a37a5a,3cf861a-dirty). Upstream SeedSigner is MIT, copyright2021
SeedSigner; its notice is retained in LICENSE.SeedSigner. Original source
snapshot/provenance is documented in ../APP-REFERENCE-INVENTORY.md.


`seedsigner_port/native_ui.py` now provides the cooperative in-process screen
backend: `ScreenSession.show(builder, config_dict)`, `poll()`, `wait(timeout_ms)`
and `run(...)`. It uses the real frozen MicroPython JSON module and native LVGL
API. The real renderer currently registers Home only. Accepted debounced button
events become complete native key pulses; held keys are suppressed across screen
handoffs. An override propagates the existing1000 contract. Real DUT1 proved the
frozen import, stable held-input suppression, an injected accepted edge reaching
the actual Seeds callback, local camera blit and Home restore without LCD reinit.
Injected edges do not prove a physical switch. Long-hold, lifecycle, other screen
contracts and actual Controller/View/model/crypto/QR work remain outstanding.

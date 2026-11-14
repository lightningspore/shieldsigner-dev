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
API. The current wired renderer registers43 native builders; the previously
tested DUT1 build still registers Home only. Accepted debounced button
events become complete native key pulses; held keys are suppressed across screen
handoffs. An override propagates the existing1000 contract. Real DUT1 proved the
frozen import, stable held-input suppression, an injected accepted edge reaching
the actual Seeds callback, local camera blit and Home restore without LCD reinit.
Injected edges do not prove a physical switch. Long-hold, lifecycle, other screen
contracts and actual Controller/View/model/crypto/QR work remain outstanding.


`seedsigner_port/navigation.py` contains the original application's complete
`Destination` and `BackStack` classes, prepared by
`mise run baremetal:app:navigation:prepare` from the locked application checkout.
The generator removes type annotations and the runtime dataclass dependency,
writes the equivalent four-argument Destination constructor, and changes the
BackStack base from `list[Destination]` to `list`. The routing, redirect, equality,
None/empty-args normalization and recursive sensitive-value redaction methods
are preserved. `navigation-provenance.json` records source pins, original class/
file hashes, transformations and generated output hash; do not hand-edit output.
Upstream MIT attribution remains in the file and LICENSE.SeedSigner.

Host tests compare against the actual original CPython/dataclass classes without
importing the full app. `baremetal:app:navigation:gate` verifies the frozen classes
on DUT0 with explicit test View fixtures. No production View is substituted.
These classes currently live in the port namespace; the actual Controller/View
imports still need to be integrated consistently. Full Controller.start(), real
settings/storage/models/crypto/QR and native screen configuration/result adapters
remain incomplete. The native registry is broader than those reviewed adapters.


`screen_contracts.py` now adapts the reviewed ButtonListScreen, LargeButtonScreen
and MainMenuScreen argument dictionaries to genuine native builders, and validates
selection/back/power results. Original inherited field defaults are extracted
from pinned app dataclasses into `screen_defaults.py` by
`baremetal:app:screens:prepare`, with `screen-defaults-provenance.json` recording
source hashes. Host differential tests execute the existing Linux contract helpers
and original selected dataclass fields to compare configs independently of the
port. Original#FF9F0A selection color, layout flags, icons/colors, translation
opt-out and scroll defaults are preserved. NUL text rejects explicitly.

`ScreenSession.show_screen(Screen_cls, kwargs)` / `screen_result(event)` /
`run_screen(Screen_cls, kwargs, timeout_ms=None)` provide the app-facing boundary.
Raw-builder renders clear the adapted result count to prevent stale validation.
The actual Controller/View methods are not wired to it yet. Unsupported Screen
subclasses, explicit button-class styling and configured long-hold actions raise
UnmigratedScreen; they never render a generic substitute. Only English identity
translation is used by default; callers may inject a translator, but full locale
asset lifecycle is not integrated. Twenty-nine host tests and the frozen real-
renderer gate pass. Test View/screen/input classes in gate scripts are fixtures,
not production app replacements. Physical switches and full app remain unverified.
Receipt: [../evidence/phase-12-screen-contracts.json](../evidence/phase-12-screen-contracts.json).


`settings_schema.py` now contains the original60-entry SettingsConstants/
SettingsEntry/SettingsDefinition schema and SettingsQR parser. Regenerate with
`baremetal:app:settings:prepare`; `settings-schema-provenance.json` records pins,
class/file hashes and transformations. Original translation-marker behavior is
retained. Linux GPIO probing is replaced with explicit real-hardware metadata;
language discovery reports only the English assets actually frozen, with no
filesystem emulation. SettingsEntry uses an explicit dataclass-equivalent
constructor, rich comparison fallback and repr. Original lookup/default-copy/
serialization methods and numeric-bound metadata are preserved.

The parser is extracted as `SettingsQR.parse_settingsqr`, with logging removed
and real double conversion retained. It does not apply settings: raw free-entry
values such as out-of-range PBKDF2 iterations must still be checked by the actual
setter before use. The Settings singleton/update/setter/platform side effects,
persistence and Controller integration remain unported. Schema device options
are upstream metadata, not a promise that native drivers support every option;
smartcard metadata does not implement card software. No user settings are loaded.

Native app builds now enable actual MicroPython double precision and link the
existing pinned libm runtime; the schema is frozen only in those builds because
its original constants include floats. The minimal diagnostic freeze excludes
it and remains buildable. `BM_NATIVE_UI` in the host build environment chooses
the explicit freeze list; host manifest `os` use does not add a runtime OS stub.
The device exported all60 public default entries, which compare exactly to the
source-derived schema. Thirty parser/GC cycles preserve native heap baseline;
real double arithmetic, malformed-input fixtures, screen and two-camera regression
gates pass.32 host tests compare the schema/parser with original app classes.
Receipt: [../evidence/phase-12-settings-schema.json](../evidence/phase-12-settings-schema.json).


The native RAM Settings singleton now retains the original validation/update/
getter algorithms, including PBKDF2 integer/floor/ceiling checks. A separate
settings_platform policy provides fixed current-device defaults and explicit
unavailable-action errors before bulk updates can partially change data. Card
interfaces are empty, persistence is disabled, and no file/thread/locale service
is emulated. `object.__new__(cls)` is explicit because MicroPython does not
inherit that attribute onto user classes. The native hardware identity is
mini-pcb240. Source method hashes/transforms are in settings-store-provenance.json.
36 host tests and real DUT0/DUT1 RAM settings gates pass. This is not complete
Controller startup, persistence or hardware-setting application.

The corrected connected-board profile and physical LCD/input evidence are in
[../MINI-PCB-IO.md](../MINI-PCB-IO.md). Prior Home-only builds with DC56/RST57
were for another fixture and do not describe the connected board.

Original DecodeQR classes and ScanScreen loop now have native preparation/gates;
see [SCAN-PORT.md](../SCAN-PORT.md) for source provenance, verified scope and
remaining crypto/UR/Controller/visual integration. This is not general Scan readiness.

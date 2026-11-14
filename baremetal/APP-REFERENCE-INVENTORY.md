# Installed app reference inventory

Read-only snapshot of REF `/opt/src`, taken during Phase10 reference work.
No app port or app hardware gate has started. Analysis runs on the Mac without
importing/executing the app or reading user settings, seeds or saved sessions.

REF runs CPython3.12.10. Its installed version identifies fork `lightningspore`,
name `lvgl-dev.cb6170a37a5a`, source marker `3cf861a-dirty`, timestamp
`2026-10-30T13:25:23+00:00`. That marker is not a reproducible clean commit;
the ignored snapshot and per-file SHA256 inventory preserve the observed source.
There are113 Python files totaling2,904,054bytes. Source plus resources/cache
files pulled by ADB total10,941,184bytes; cached bytecode is not analyzed.

`tools/ref_app_inventory.py <snapshot-of-opt-src>` parses source with the host
Python AST. It records imports per file, hashes and syntax counts; it does not
assume that every optional desktop import is needed on RV1103. Full output stays
local at `logs/phase-10/ref-app-inventory.json` and the snapshot at
`.tools/ref-app-source/`. No third-party source was added to the repository.

The initial REF-side AST/metadata attempt exceeded its small Linux memory budget
and the OOM killer killed that Python helper. It produced no valid inventory.
Do not repeat source analysis on REF. Original camera modules remain loaded,
ADB remains reachable, kernel taint remains4096, and the original Rust capture
subsequently saved3,981,312bytes successfully. Receipt:
`logs/phase-10/ref-camera-health.json`. Its disposable raw buffer was removed
from REF's RAM filesystem after checking the result.

## Porting work identified

| Area | Observed reference code | Required follow-through |
| --- | --- | --- |
| Python runtime |656 annotated assignments,142 dataclass decorators; enum, typing, pathlib, logging, threading imports | Audit actual executed paths; enable or port necessary APIs and use an explicit scheduling model. Current minimal MicroPython build is insufficient. |
| Display/UI |Pillow image/canvas code, periphery SPI/GPIO display implementations; ILI9341 and ST7789 variants | Match the actual PCB/LCD and preserve navigation/screens using native rendering support. Remove the test loopback before PCB reconnection. |
| Buttons |periphery GPIO and optional pygame backend | Implement the PCB's real input pin map, pull configuration, debounce and repeat behavior. Current Pin52/53 test API does not cover them. |
| Camera/QR |PIL conversion, optional picamera/OpenCV backends, pyzbar/qrcode/UR-related modules | Bind proven Rust ISP/3A to the app's frame contract, add efficient preview/conversion/QR decoding, and verify real scanning workflows. Current capture is a bounded32-frame acquisition. |
| Signing/crypto |embit, hashlib/HMAC, cryptography/Cryptodome, mnemonic/shamir and other optional crypto imports | Preserve supported workflows and formats with real implementations; verify against established vectors and reference outputs. Placeholder signing is not an acceptable port. |
| Smart cards |keycard, pysatochip, smartcard, smartpgp and related helper/view code | Inventory supported card transports and preserve intended functions while replacing Linux-only I/O. Keep the PCB's existing smart-card hardware/connector. |
| Assets/storage |Fonts, localization, image resources and file-based configuration | Provide app/assets storage and loading on microSD, with provenance/licenses preserved. The experimental raw boot image has no filesystem yet. |

Observed installed package directory names include embit0.8.0, Pillow11.0.0,
qrcode8.0, PyQRCode1.2.1, mnemonic0.20, shamir-mnemonic0.3.1,
python-periphery2.4.1, cryptography43.0.3 and pycryptodomex3.23.0. Presence is not
proof that every package is exercised; do not infer the final MicroPython
dependency set solely from this inventory.

Next implementation remains gated by the plan order: finish standalone boot,
then convenient USB debugging, then port and qualify the app on the real PCB.
The working Linux source/card remains the comparison and recovery reference.

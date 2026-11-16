# Optional foreground app startup

`app-autostart` inherits the complete DUT1 `app-ui` profile and runs the frozen
`seedsigner_boot.py` entry after interpreter initialization. That entry starts the
original Controller: native splash, development warning acknowledgment, then Home.
The warning remains required. USB Ctrl-C interrupts the app and returns to the
normal development REPL. The wrapper stops its camera stream and blanks the LVGL
root on exit, including exceptions. It records only entry count, running flag,
exit type and last native builder name, never exception payloads.

This is a development convenience, not a production security boundary. The
existing warning about USB Python and unqualified entropy still applies. Exiting
to the development REPL is not a whole-memory wipe. This adds no SD writes,
filesystem loading, entropy qualification or cold power timing result.

Use `mise run baremetal:app:autostart:dut1:build` for the optional image. Ordinary
`baremetal:ui:dut1:build` keeps its existing REPL entry. Never load either LCD
profile onto DUT0 while its SPI jumper is installed. The generic REF/DUT0 harness
rejects the optional app profile as it does other LCD profiles.

The default `baremetal:usb:dut1:ram:gate` waits for the native splash and interrupts
the automatic app to check clean USB recovery, blank pixels, camera stopped and
UART disabled. GPIO43 is intentionally an LCD backlight output, so its DDR bit is
0x800 after UI initialization; the UART pin mux, IRQ and IER remain disabled.
`baremetal:app:boot:dut1:gate` then runs the same entry with native key events to
acknowledge the original warning and reach Home. This does not qualify physical
button presses.

After those gates pass, reset DUT1 and use
`mise run baremetal:app:autostart:dut1:ram` to load the same image and leave the
foreground app running for use. This final command verifies only selected RAM
download and USB enumeration; it deliberately skips the interrupting console
gate. From a recovered REPL, restart with:

```python
from seedsigner_port.boot import run

run()
```

`@@REPL_READY` is emitted when the prompt becomes available after the automatic
app returns. The internal interpreter-ready timing hook still occurs immediately
after `mp_init`; it does not measure a usable app, ROM/DDR or cold power startup.
Live preview interruption warms the instruction widgets before its native heap
baseline; first-use glyph caches are retained by LVGL independently of the scan
surface. Camera frames are not exported by that test.

See `evidence/phase-12-app-autostart.json` for exact hardware evidence and scope.

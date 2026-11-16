# Original Views and Controller on the native runtime

`mise run baremetal:app:views:prepare` generates original application View bodies
and the Controller from the pinned SeedSigner source. Per-file source/output
hashes live in `app/views-provenance.json` and `app/controller-provenance.json`.
The existing canonical original Destination/BackStack types remain shared.
Upstream attribution and licensing are retained.

The generated classes preserve business decisions and return actual Destinations.
Class definitions resolve lazily so optional base classes and feature providers
are loaded only when used. Local feature imports also resolve on use; an unused
PSBT or smartcard provider cannot prevent loading a seed. Missing providers raise
FeatureUnavailable. Source annotations are removed, dataclass View constructors
are explicit, and f-strings become equivalent format calls accepted by the pinned
MicroPython compiler. Payload logging calls are removed. This is not a general
CPython compatibility layer or a claim that every frozen View is operational.

The Controller preserves the original foreground destination dispatch, redirects,
Home state clearing, history unwinding/deduplication, error routing and cleanup.
Reviewed native boundaries replace Linux startup, background import, hardware
monitor threads, traceback formatting and camera ownership. Storage initializes
synchronously. No fake thread, RNG-health, filesystem or battery service is
provided. Smartcard application navigation remains outside the requested scope.
The original built-in advisory block constants remain; no file refresh is implied.

The native renderer shares actual PCB button input and upstream LVGL screen/event
builders. Reviewed contracts now include seed finalization/options/selection and
status/warning/error screens alongside the existing basic screens. Warning default
buttons retain actual ButtonOption objects. SeedOptions includes the fingerprint
icon/color set by the original screen's post-init, which the Linux contract had
omitted. Host differential tests check other mappings against that adapter and
actual source field defaults.

Foreground polling checks the actual monotonic inactivity clock against the
original wipe setting and button activity. Expiration runs the original cleanup,
then unwinds Python through the scanner's camera finally blocks before returning
Home. The real native LVGL toast and screensaver services own their timers; scan
preview temporarily disables the LVGL screensaver while direct NV12 drawing owns
the display. Delayed toast scheduling/suspension remain explicitly unavailable.

Error location comes from actual MicroPython traceback metadata via
`machine.exception_location(exception)`. It returns the innermost file, line and
block, or None, without printing exception data. Native sys.exc_info supports the
original Controller's exception-sensitive final cleanup. The firmware's existing
sys.print_exception ignores its optional stream when stdfiles are disabled, so
it is deliberately not used for capture or error routing.

Production entry from the USB Python prompt is:

```python
from seedsigner_port.controller import Controller

Controller.get_instance().start()
```

This runs the original opening splash and development warning, then the original
Home View. USB interrupt remains available; camera ownership is released by Python
finally blocks. The image is still a development image: USB Python access and
unqualified entropy are reported by the warning. No automatic startup/SD update
is included in this checkpoint.

Native gates exercise three different scopes:

- `baremetal:app:views:dut1:gate`: public numeric SeedQR pixels through actual
  native ZXing, original DecodeQR/ScanView, SeedFinalizeView and SeedOptionsView,
  actual native key events and Controller history back to Home. Stored seed FP
  is genuinely derived as 73c5da0a. The public seed is discarded after the test.
- `baremetal:app:views:error-idle:dut1:gate`: an explicit missing provider reaches
  the original system error screen and Home. Inactivity during a real SC3336
  preview wipes stored/pending public seed aliases and unwinds the actual native
  camera stream before Home, with a native wipe notification.
- `baremetal:app:views:startup:dut1:gate`: actual splash timer completion and
  development-warning acknowledgment reach Home.

The first gate injects pixels and native key pulses, never selected return values;
it does not prove optical capture of the printed QR. The idle gate forces elapsed
activity time rather than waiting a minute; real source cleanup and camera APIs
run. Startup gate time includes intentional animation/warning processing and is
not a cold boot benchmark. Remaining work includes optical decode, other original
menus/screens, passphrase entry, UR/compact/encrypted flows, entropy qualification
and full app startup from SD. Frozen class availability does not close those gaps.

Follow-on: [PASSPHRASE-UI.md](passphrase-ui.md) records the later native
passphrase entry/review integration and its separate accept/edit/discard/skip
hardware gates, including the remaining glyph and long-text review limits.

Follow-on: [MNEMONIC-ENTRY.md](mnemonic-entry.md) records the native manual BIP39
entry adapter and its original View/key-event gates. Paged passphrase review is
recorded separately in [REVIEW-PAGES.md](review-pages.md).

Follow-on: [BACKUP-WORDS.md](backup-words.md) records native word backup review,
quiz verification and the guarded original pagination fix for partial pages.

Follow-on: [QR-EXPORT.md](qr-export.md) records original standard/compact SeedQR
encoding, exact matrix parity and native transcription-screen gates.

Follow-on: [APP-BOOT.md](../bringup/app-boot.md) records the optional `app-autostart`
DUT1 RAM profile and frozen foreground entry. Automatic splash/warning launch
and USB interruption are tested separately from native key acknowledgment/Home.
This does not update the SD card or establish cold power-to-app timing.

Follow-on: [XPUB-EXPORT.md](xpub-export.md) records original xpub helper/encoder
checks and static export through native details/QR screens. Singlesig currently
reaches the original address-verification prompt; its camera/search flow remains
a separate unfinished gate. Animated/UR display remains explicitly unavailable.

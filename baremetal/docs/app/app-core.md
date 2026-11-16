# Original app storage and native service boundary

The pinned SeedSigner application remains the source of storage and model
behavior. `mise run baremetal:app:core:prepare` regenerates whole SeedStorage,
EncryptedQRStorage, Singleton/ConfigurableSingleton, GUI/icon constants, the
nine original ButtonOption fields and release-key cache clearing helpers.
`app/app-core-provenance.json` records source and output hashes. Upstream MIT
attribution is retained. EncryptedQRStorage only stores an opaque value; it does
not implement or qualify encryption.

The source adapter strips type annotations, resolves imports through the existing
explicit dependency boundary, and removes payload-bearing logging calls.
Unavailable providers propagate before broad parse handlers. Native singleton
allocation uses object.__new__; ButtonOption's dataclass constructor/equality
are explicit. This is a reviewed subset of dataclass behavior, not a general
dataclasses implementation. Optional workflows remain unavailable until their
actual platform boundaries are ported.

`clock.py` supplies monotonic elapsed seconds and second-based sleep using the
real native 32-bit millisecond clock/sleep API. It unwraps rollover when called
at least once per complete counter cycle; it supplies no wall-clock time.
HardwareButtons adds shared activity tracking to the existing actual PCB input
and debounce adapter. The English translation boundary returns the original
English text; the settings platform continues to reject other locales.

The native UI exposes actual upstream foreground LVGL overlay controls:

| Call | Operation |
| --- | --- |
| ui.overlays(0, milliseconds) | Set screensaver timeout; zero disables |
| ui.overlays(1) / (2) | Show / dismiss screensaver |
| ui.overlays(3) | Record display activity |
| ui.overlays(4) | Query screensaver activity |
| ui.overlays(5) / (6) | Dismiss / query toast |
| ui.toast(text, icon, outline_rgb, text_rgb, duration_ms) | Show toast, replacing previous; zero duration stays until dismissed |

All calls run on the foreground LVGL loop; tick/poll must continue for timers.
No fake thread objects are introduced. Toasts dismiss the screensaver, and the
upstream input handler consumes its wake press. Text is bounded to 255 UTF-8
bytes and icons to 15, with embedded NUL rejected. RGB values must fit 24 bits.

The native gate uses only public BIP39/SLIP39 fixtures. It checks actual seed
fingerprints, pending conversion, deduplication, wipe aliases, opaque storage,
button equality, singleton identity, key-cache clearing, timer-driven overlay
expiry and wake handling. This checkpoint does not yet connect the full
original Controller/View navigation, qualify entropy or prove optical QR decode.

Follow-on: [VIEWS-PORT.md](views.md) records the later original Controller/View
integration and its separate native flow, error/idle and startup evidence.

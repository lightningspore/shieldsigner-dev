> Historical notebook preserved during repository cleanup. Entries describe their own checkpoint; see the [current overview](../../README.md) for present status.

# LVGL migration divergences

Current artifact organization is documented in
[Firmware artifacts](../../../../docs/FIRMWARE-ARTIFACTS.md). The cleanup relocates
generated inputs/outputs, adds shared path helpers and verifies frozen image
provenance; it changes no wallet or device behavior and preserves upstream pins.
The user has booted `lvgl-dev.cb6170a37a5a` and confirmed UI/camera scanning.
The entries below retain chronological implementation evidence and may describe
earlier isolation or acceptance states; consult the README for current status.

This applies only to the isolated experimental frontend. The installed wallet
app, views/models, production camera library and current image are unchanged.
Pinned upstream revisions are in `sources.lock.json`.

| Change | Reason and exact scope | Evidence / remaining work |
|---|---|---|
| Native screen host instead of Pi CPython or MicroPython bindings | Reuse all portable upstream C/C++ screens on ARMv7/musl without importing Pi libcamera or switching Python runtimes. Private framed pipes carry bounded rectangles and typed events. | 43 fixtures render on Mini; lifecycle/error unit tests. Not yet full wallet integration. |
| Partial RGB565 draw buffer | A 9,600-byte LVGL buffer replaces a mandatory full-screen LVGL draw buffer in the Pi reference. Display initialization/GPIO policy remains in the reviewed installed driver. | Fixtures and actual Settings flow rendered on the LCD. Full app performance remains to measure. |
| `patches/scaffold-capacity.patch` | Increase explicit list bound from 32 to 128. The fork's Advanced menu has 43 settings plus actions and otherwise fails before rendering. All entries keep their original order/index; no truncation. Adds 384 bytes to a 32-bit scaffold's fixed pointer array. | Actual Advanced menu, deep-row selection and restored scroll offset tested on Mini/LCD. Bound remains enforced. |
| `patches/keyboard-key3-save.patch` | Preserve original generic keyboard KEY3 Save from keyboard and top-nav focus. Upstream's in-grid CHECK remains available. Empty input cannot submit. No entropy or wallet logic changes. | PBKDF2/BIP85/account/derivation direct-call tests; empty save, top-nav Save and Back tests; exact dice/coin auto-complete strings. |
| Immediate keypad edge delivery | A key message calls `lv_indev_read` immediately. Coalesced press/release messages must not collapse to only the final released state while SPI output delays a timer iteration. LVGL still owns navigation. | On-board native key and direct-entry tests; physical button responsiveness remains to measure. |
| Scroll state at the View boundary | Preserve the two pinned View consumers of `self.screen.buttons[0].scroll_y`. The host reads the pinned scaffold's tallest direct scrollable child. Zero initial offset keeps selected-row auto-scroll; positive offsets are restored. | Original Settings views change a test-only setting and navigate back; deep row beyond the 32-item bound returns its positive scroll offset and selected attribute. |
| Process-local constructor bridge | Reviewed classes keep their class identity and dataclass argument initialization, while PIL widget construction/display is bypassed. Direct `.display()` callers use the same native runtime as View dispatch. | Unit tests and actual direct-call keyboard tests. Unknown direct subclasses retain their original methods and are an explicit remaining migration gap; unsupported View calls fail before construction. |
| Generic keyboard Save trims text | Original generic keyboard Save returns `.strip()`. That is applied only to the generic keyboard adapter family with Save enabled. | Public whitespace fixture passes. Passphrase screens are not in this family and must preserve exact text plus Back's dictionary response when ported. |

All patches apply with `git apply --check` to a disposable build copy. The
verified upstream checkouts are kept clean. The binary/source hashes and scoped
receipts are stored in `validation/`; they are not a full-app qualification.

Known remaining parity work includes fork-specific screen content, controller
startup/notices, toast/screensaver/wipe interactions, battery indicator and
very-long-press display switching, language/font packs, callback-driven screens,
camera/QR/entropy ownership and full seed/PSBT/smartcard workflows.

## Passphrase checkpoint

The host returns a dedicated `passphrase_result` event rather than treating
passphrase text as a generic keyboard result. Save returns `{"passphrase": text}`;
Back returns the current textarea contents plus `is_back_button: true`, matching
the original fork's Screen contract. Text is not trimmed or normalized by the
frontend; original Seed models still own BIP39 normalization/derivation.

`patches/passphrase-nav-aux.patch` forwards KEY1/KEY2/KEY3 from top-nav focus to
the same side-panel handler used at keyboard focus, preserving the original
fork's global mode-switch and Save behavior. The upstream portable keyboard
layout is reused, including its combined symbols layout.

The typed Back event reads the unique active passphrase textarea. A missing
widget is an explicit error, not an empty passphrase. The source tree stays
unchanged; this is host glue. Initial screen acknowledgement now follows the
first render and keypad reset, so input cannot race an unfinished screen load.
Named app colors (e.g. Discard's `red`, fingerprint icons' `blue`) are converted
to RGB hex before sending configuration to LVGL.

Hardware tests preserve empty input, leading/trailing spaces, composed/decomposed
Unicode, CR/LF and all printable ASCII. Original add/review/finalize Views and
Seed models run with injected View dependencies, followed by Back/discard. No
persistent settings are written. This is not full Controller qualification.

Embedded NUL input now uses the isolated raw-buffer adapter described in the
NUL compatibility checkpoint below. Historical rejection notes later in this
file describe earlier checkpoints, not the current entry contract.

## ScanScreen adapter

The port keeps the installed NativeVideoStream ownership, readiness, retry,
latest-frame/pacing and shutdown implementation. QR uses RustTransportQrReader
with the same pinned worker digest; preview uses the existing PreviewRenderer.
Calling `decoder.add_data(reader.decode(native_frame))` on a non-None payload
is equivalent to the original `DecodeQR.add_image` sequence. Empty bytes are
not treated as a missed frame. Original model QR-type and assembly decisions
remain untouched, including how duplicate UR fragments report their status.

The portable camera overlay is composed over a native LVGL image. The host
centers the rotated preview within the 240x240 canvas, matching the original
no-crop fit policy. RGB preview bodies are bounded to 129,600 bytes, with a
3-second partial-message deadline and a single acknowledged frame in flight.
RGB -> BGR storage adaptation is internal to the LVGL host, not an ISP change.
The receive buffer and image buffer are cleared as frames/scan sessions end.

The UI host's input pump also runs during preview acknowledgement waits. Camera
reads and QR calls retain their existing bounded waits. Cancellation and terminal
COMPLETE/INVALID statuses follow the original ScanScreen return contract (False
for Back; None for terminal decode). Finally closes the QR client, stops the
managed stream and clears the native preview even when acquisition/decoding/model
processing fails. Unit failure cases cover that cleanup; actual three-cycle
camera/LCD tests verify exit 0 and DMA zero on cancellation.

Full ScanView routing/availability, known optical fixtures, entropy capture,
whole-app resource comparison and Controller-level recovery remain separate
acceptance gates. No camera/QR/crypto source is modified in the installed image.

The Scan adapter is not an image-entropy adapter. Entropy capture/mixing and RGB
still contracts remain in the existing application/native integration and must
be migrated separately; preview pixels are not substituted for entropy inputs.

### Transaction approval and QR output checkpoint (2026-10-30)

`tests/psbt_signing_flow.py` temporarily deploys the original
`PSBTFinalizeView` with dependency initialization injected and the public
`NORMAL-1_p2wpkh` corpus fixture (abandon/about seed). On the Luckfox LCD,
scripted keypad events verified that Back preserves the exact unsigned bytes;
approval adds one signature through the original parser/root/signing code.
The signed, pre-trim transaction finalizes, and the exported trimmed model
retains identical partial signatures. Upstream intentionally removes UTXO
metadata when trimming; finalization therefore tests the original signed model.
The native loading adapter replaces only the drawing thread lifecycle.
This does not yet qualify the entire review/navigation/export flow or physical
button operation.

The six PSBT screen adapters retain integer amounts, full addresses, change
verification state, high-fee markers, RBF and locktime text. Approval opens in
read-first mode rather than automatically focusing a potentially offscreen
button. OP_RETURN with invalid UTF-8 or NUL displays complete hex; empty data
is explicitly labeled. Amount formatting is reused from pinned upstream,
with its MIT attribution under `licenses/`.

`tests/qr_output_flow.py` passed exact rendered-pixel decoding for compact seed,
numeric seed and address QR output, and reconstructed a public animated PSBT.
It also checked brightness persistence once on exit and Left/Right return
contracts. This is native ZXing decoding of transmitted LCD pixels, not an
optical camera scan. The combined `psbt_signing_flow.py` now also passes original Math, Recipient,
Change verification, Finalize and SignedQRDisplay Views in sequence. Native
ZXing recovered the exact signed trimmed PSBT from ten rendered QR frames.
Back preserved the unsigned bytes before this sequence. See
`validation/psbt-signing-arm.json`. This covers one public native-segwit
transaction; overview/risk-warning routing, other transaction policies and
full Controller lifecycle still need qualification.


### Xpub details checkpoint (2026-10-30)

`SeedExportXpubDetailsScreen` now uses pinned upstream's dedicated LVGL builder,
including its warning edges. The adapter forwards the exact fingerprint, full
xpub and derivation, localized field captions and the original custom button
label. Missing security fields fail explicitly. Original View derivation and
native loading passed on the Luckfox LCD for accounts 0 and 7, each with Back
and Export; export returned the original QR View destination with the expected
account path. See `tests/xpub_flow.py` and `validation/xpub-arm.json`.
The test now continues both approved accounts through the original static
xpub QR View. ZXing recovered exact encoder bytes from transmitted LCD pixels,
including the expected fingerprint and account origin. The destination was the
original address-verification prompt. Animated UR/Specter xpub formats, optical
scanning and address-search threads remain separate integration requirements.


### Address search checkpoint (2026-10-30)

The dedicated upstream address-verification screen receives the original address,
script/signature/network labels and action buttons. The isolated runtime polls
`SeedAddressVerificationScreen._run_callback` itself, preserving success before
batch exhaustion. Original counters and search workers remain in Python;
progress text updates the native widget at most ten times per second, replacing
only the original drawing thread. Counters never enter serialized configuration.

On the Luckfox LCD, the original single-signature brute-force worker found both
receive and change index 7 for the public seed, and both workers joined cleanly.
Batch exhaustion returned Back. Enter-only Cancel passed three consecutive
repeats, and the complete original single-signature search View then routed to
its success View and MainMenu, with the original worker stopped. An earlier
Enter-only timeout was not reproduced in isolation or these repeats; no root
cause or physical-button qualification is claimed. Skip 10 and expanded/multisig
search remain unqualified.

`address-success-details.patch` adds host-provided derivation/script text and
the fork's non-standard-path warning to the dedicated upstream success builder.
Without this extension that builder would omit those original screen fields.
The read-first scroll layout retains access to these additional details before
OK. Contract tests cover non-standard warning propagation; the hardware flow
covers the standard native-segwit change address. See `tests/address_search_flow.py` and its validation receipt.


### Original Controller checkpoint (2026-10-30)

`renderer_bridge.py` installs before the original Controller configures itself.
It preserves the reviewed display handle/inversion setting and Renderer class,
but allocates no PIL canvas/draw object. Remaining PIL show-image/pan calls fail
explicitly. Native clear handles orderly shutdown. Only the 240x240 ST7789 is
accepted; other configurations fail rather than silently using wrong geometry.
The process-local adapter restores original methods/singleton on teardown.

`controller_flow.py` passed the actual Controller configure/start loop and
unmodified View initialization on the Luckfox LCD: Home -> Settings -> Back ->
Home. Both mandatory storage models initialized. The original wipe and RNG
workers started and stopped/joined; no health or entropy algorithms changed.
A debounced Runtime activity callback invokes the original hardware button
`update_last_input_time`, including held-key activity every 250 ms. The hardware
test verified the timestamp advances. It disabled the inactivity wipe, skipped
startup interstitials and avoided boot-counter MMIO explicitly; these behaviors
are therefore NOT qualified by this checkpoint. Screensaver, override/wipe
interruption, toast/battery overlays and full startup still need integration.

Metadata-only /proc snapshots are in `validation/controller-arm.json`:
Python RSS was about 23.3-23.8 MiB (5-6 threads, peak about 24.5 MiB); native
LVGL RSS reached about 0.85 MiB (one thread) during this short menu sequence.
These are process RSS snapshots including shared pages, not private-memory totals
or a matched comparison with the original app. They exclude camera/signing and
do not establish sustained CPU/frame-rate behavior or total RAM savings.


### Wipe interruption and native notifications (2026-10-30)

`lifecycle.py` wraps the original Controller wipe callback without changing its
seed/session-clearing code. Once the callback completes, a single interruption
unwinds the active View through its cleanup. Controller error routing recognizes
only this interruption, reaps/restarts the native process (discarding all old
widget/QR data), and returns to Home with cleared history. Other errors retain
original routing. This adapter is currently installed explicitly in the test,
not yet a production launcher. Native toast rendering uses pinned upstream's
overlay manager and original toast content/severity/conditions; per-toast tokens
prevent an old notification from dismissing its replacement. Screensaver timeout
remains disabled pending policy integration and qualification.

The seed-screen hardware test passed: original Seed.wipe zeroed the retained
public seed buffer, storage emptied, the native process was replaced, and the
seed View did not resume. The test simulates the timer callback after 500 ms;
it does not validate elapsed inactivity policy. Original Controller currently
logs the intentional interruption traceback before handing it to the adapter.
See `validation/wipe-arm.json`.

The live-camera variant FAILED, so camera wipe is NOT qualified. After one frame,
the QR worker exited zero but camera owner exited one. Owner diagnostics reported
an AE event queue overflow and an ISP parameter pool remaining full for 250 ms.
The system also logged swap write errors; memory/scheduling pressure is a lead,
not a proven cause. This test starts directly in the scan View, so first-use
imports during wipe also need separating from normal Home->Scan behavior.
See `validation/wipe-camera-failure-arm.json`. No passing receipt was manufactured.

That failure exposed error masking: cleanup acknowledgement waits polled for
new lifecycle interruptions and could overwrite the original camera error.
Camera and QR cleanup now await only their shutdown ACK, with a unit test proving
a late lifecycle event cannot mask the primary QR-worker timeout. A fresh live
camera run is still needed after this change. Image packaging/flashing remains
gated on resolving and qualifying these lifecycle paths.


### Camera wipe follow-up: retain the working startup policy (2026-10-30)

The early LVGL Controller tests omitted the working image's optional-import
policy. `startup_policy.py` now reuses `install_small_ram_profile` and
`install_lazy_scan_views` from the existing shared integration, validating its
SHA-256 before import and its actual imported path. The shared module itself
retains its original app-source guards. Both SeedStorage and EncryptedQRStorage
initializers remain mandatory; optional smartcard/SLIP39 destinations still
resolve the original classes on demand. The helper does not copy wallet routing
or edit installed files. A unit gate checks the packaging source still matches
the pinned shared module.

Two Home->Scan->wipe->Home runs with this policy passed, as did a direct
Scan->wipe->Home run. Each delivered two physical-camera frames, camera owner
exit zero and QR worker exit zero; the original seed buffer was zeroed and the
native renderer replaced. The corrected Home->Scan baseline WITHOUT the policy
failed in the camera owner and routed the original ErrorScreen. All runs used
the same board and current adapters, but cache/zram residency and scheduling were
not controlled, so this does not isolate exact bytes saved or prove a single
cause for the earlier ISP timeout. It does establish that omitting the working
startup policy is not an acceptable LVGL launch configuration.

Receipts: `wipe-camera-small-ram-arm.json`,
`wipe-camera-direct-small-ram-arm.json` and
`wipe-camera-baseline-home-failure-arm.json` under `validation/`. Post-baseline
DMA inspection returned zero objects/bytes. Earlier failed receipts are retained.
These are short cleanup tests with a simulated timer callback, not an inactivity
soak, sustained frame-rate/CPU comparison, or optical decoding qualification.
The shared policy is explicitly installed by the tests; the production LVGL
launcher is still pending. Screensaver, startup interstitials and broader screen
coverage remain acceptance requirements.

The Home input test was also corrected to start its scripted press clock at the
first input poll, after screen readiness, rather than before a potentially slow
screen build. The previous Home timeout was a test stimulus error and supplies
no evidence of a native navigation defect.


### Native screensaver checkpoint (2026-10-30)

`screensaver_bridge.py` installs a Controller-facing facade over pinned native
screensaver ownership. The original `is_screensaver_running` property reads that
facade; notification/shutdown paths can stop it without constructing a PIL logo
or copying a framebuffer. Native state-change packets update a dedicated cached
boolean and do not enter the screen-result queue. Explicit state queries also
refresh that boolean, so a state acknowledgement is a real synchronization point.
The original Controller timeout-reset method still updates its hardware input
clock and now also resets LVGL's idle clock. Runtime View dispatch carries
`is_screensaver_allowed` into each generic screen configuration. Existing native
camera/QR opt-outs remain in place. A renderer restart after wipe reapplies the
configured timeout, and the facade always observes the current native process.

`screensaver-controller-entry.patch` adds explicit activation to the upstream
manager. Forced activation does not immediately expire against a fresh idle
clock; the native keypad handler dismisses it through the same save/restore
path, with the saved group's held-key latch consuming the wake input. Idle
activation continues to use upstream's dispatcher. This is a local extension
of the pinned screen library, not a fork of wallet/controller business logic.
Touch dismissal for forced activation is not qualified; the target uses GPIO
buttons. Animation and the bundled SeedSigner logo are upstream's implementation;
SD-card custom logo loading remains unimplemented in the isolated frontend.

On the Luckfox LCD, automatic and explicit activation both restored the exact
public-menu RGB565 bytes. The held wake key did not select Continue; a later
fresh press did. A View with screensaver disabled stayed out of the saver for
more than twice the accelerated timeout. See `validation/screensaver-arm.json`.
This uses 600 ms instead of the normal two minutes, scripted input, one public
menu and original View initialization; it is not a full idle soak or physical
button/combined wipe qualification. No wallet pixels were saved.

Early test failures sampled an expired saver as the baseline and later acted
on a delayed state transition while SPI pixels were still draining. The test
now stops/resets the saver and awaits an explicit native state ACK before
starting its clock. Public-only failure captures confirmed the menu itself
restored correctly. The explicit-activation expiry issue was fixed separately;
these different observations are not conflated into a native wake-key defect.


### Real startup interstitials and fork branding (2026-10-30)

The non-dataclass OpeningSplashScreen gets an explicit constructor/display
adapter in `startup_splash.py`, avoiding LogoScreen/PIL allocations. The original
OpeningSplashView and Controller startup decisions remain active. Version is the
original Controller.VERSION; the original partner-logo setting and forced
boolean override are honored. The native splash is nondismissible, completes by
the pinned library's timed 1101 event, and returns None as the original View
expects. It disables the screensaver and clears on completion/interruption.
Upstream fade/slide timing is retained rather than reproducing PIL's frame-count
fade; timed holds remain the library defaults. No startup warning is bypassed.

Pinned upstream splash assets assumed SeedSigner plus HRF. The fork instead uses
ShieldSigner plus the SeedSigner attribution logo. `zz-fork-branding.patch`
selects generated descriptors for those original app PNGs, and the localized
caption remains "An unofficial fork of:". The same ShieldSigner bitmap is used
by the native screensaver. `assets.py` crops black-only margins, preserves native
image dimensions, and uses the pinned upstream RGB565 converter. Pillow 11.3.0
is build-host-only; manifests record exact source hashes/crops. No copied PNG or
vendor binary enters this source tree. The original app's MIT attribution is
retained under licenses and original checkouts; distributable asset packaging
must preserve those licenses. SD custom logos are still a parity gap.

Default status/warning action index zero no longer pre-scrolls past overflowing
copy: it uses upstream read-first navigation. Nonzero explicit selections remain
honored. This changes navigation presentation, not confirmation results or
warning policy; tests preserve exact copy and selected return semantics.

The original Controller startup ran without skip_startup_interstitials and
passed OpeningSplashScreen -> actual WarningScreen (live hardening probes) ->
Home -> Settings -> Home on the LCD. Mandatory stores and original wipe/RNG
workers initialized and joined; View initialization stayed original, and no PIL
canvas was allocated. The working small-RAM import policy was applied. The test marks the boot
failover counter already cleared to avoid MMIO writes, so that original boot
counter action is not exercised. The public splash framebuffer was visually reviewed: ShieldSigner logo, full build
version and SeedSigner attribution fit. No wallet image was captured. See
`validation/controller-startup-arm.json` and `startup-branding-build.json`.
The native rebuild was byte-identical in the same workspace/toolchain; this is
not cross-machine reproducibility, a cold boot, physical-button acceptance,
full startup fault injection or complete wallet coverage.

Inventory now scans all application top-level Screen classes rather than only
gui/screens: 87 classes / 966 static View calls, adding LogoScreen,
OpeningSplashScreen and ScreensaverScreen. The earlier 84 count omitted those
three; this is an inventory correction, not three additional completed flows.


### SeedQR transcription checkpoint (2026-10-30)

`transcription.py` maps the original format, whole QR, zoom, optional confirmation
and word-backup-test prompt arguments. Standard/Compact/Encrypted descriptions
follow the original flag combinations; the all-options case remains a plain
list rather than inventing compact/encrypted explanatory text. Confirmation and
Back return contracts remain original. Native zoom reports its generic Back
sentinel on any click; the runtime explicitly maps that to the original zoom
screen's None return, so the View proceeds to optional confirmation.

Hand transcription requires the exact same module pattern in whole and zoomed
views. The adapter therefore generates the matrix with the SAME Python qrcode
library/settings as the original QR helper (version 1 with fit, ECC L,
add_data optimization and automatic mask). It packs the boolean matrix into the
pinned qrcodegen buffer layout and passes it through private IPC. No Pillow QR
image is constructed by the adapter; the original Views still call the original
QR.qrsize helper, whose small PIL allocation is not yet removed. No wallet,
checksum or entropy algorithm is replaced. Unlike selecting one native encoder
mode, this retains Python's mixed numeric/byte segmentation as well.

`transcription-matrix.patch` lets the pinned native whole/zoom builders draw
that supplied matrix, validates template/module size (21/25/29/33), and preserves
the existing native-only corpus encode path when no matrix is provided. Zoom
allocation/encoding failures now raise instead of showing a misleading white
field. Buffer allocation failures clean up before throwing. Format rows can hide
the compact description when the original screen did not offer that format.

The original format -> dire warning -> whole QR -> zoom -> optional Done Views
passed on the Luckfox LCD for 12/24-word Standard and Compact public BIP39 seeds.
Native ZXing decoded the transmitted whole-QR pixels to the exact original
encoder bytes. Arrow panning and the zoom completion route ran; Back from whole
QR returned BackStack and the seed stayed unchanged. Exact zone-label/zoom pixel
geometry was not measured by this test. Eight malformed matrix/template requests
were rejected by the actual native process, which then built a recovery menu.
See `validation/transcription-arm.json` and `transcription-protocol-arm.json`.

The test injects View dependencies/keypad and uses public fixtures only. It does
NOT qualify optical scans, the scan-to-confirm comparison route, auxiliary-button
exits, encrypted transcription, all template geometries or the newly mapped
word-backup-test prompt flow. Those remain required. Matrices/seed payloads are
never logged or written to disk by these tests.


### Backup quiz and scan confirmation checkpoint (2026-10-30)

The original word-backup prompt/quiz/mistake/retry/success Views passed on the
Luckfox LCD: one pending 12-word public seed and one already-stored 24-word
public seed. All 36 words were confirmed exactly once, with one intentionally
wrong answer in each case (38 quiz prompts total). Wrong answers did not advance
the confirmed list; retry retained the original word index. Prompt Review/Skip
returned the original destinations. The pending None sentinel survived the quiz
and success path, then the original finalize View stored the seed. No RNG or
answer checking was replaced: the test observes the generated PUBLIC choice
labels solely to select a keypad row. View dependency initialization and keypad
are injected; BIP85/SLIP39 and the full Controller quiz loop remain unqualified.
See `validation/backup-quiz-arm.json`.

The original SeedQR confirmation Scan View also passed matching seed, different
seed, non-seed QR and Cancel cases. Public synthetic NV12 frames went through
real native FrameReceiver, preview, ZXing and original DecodeQR. Only the physical
camera source was substituted. The original seed-comparison branches selected
Success/WrongSeed/InvalidQR/BackStack, and the actual success/error result screens
returned to SeedOptions or review. Every QR worker exited zero and the synthetic
source stopped, with the seed unchanged. This is not optical-camera qualification.
See `validation/seedqr-confirmation-arm.json` and `tests/synthetic_frames.py`.

An early quiz assertion shared the mutable confirmed-list object with the View;
it was corrected to snapshot expectations independently. That failure did not
identify an app state mutation bug. The final test also checks the last selected
word index was not previously confirmed.


### Encrypted-backup text entry checkpoint (2026-10-30)

`encrypted_contracts.py` reuses the pinned native passphrase keyboard for the
original ScanTypeEncryptionKeyScreen and SeedEncryptedQRMnemonicIDScreen. Native
Save/Back events are explicitly mapped to encryptionkey/mnemonic_id dictionaries,
including the original is_back_button flag. Text is not stripped, normalized or
otherwise transformed. Original/default titles and custom-title translation are
retained. Embedded-NUL entry remains an explicit unsupported case rather than
silently truncating a C string. The public-data Decrypt/QR-type menus and the
transcription-mode explanation have explicit simple-list adapters; only their
contracts are unit checked at this stage.

The LCD test passed five public Save fixtures per editor (empty, significant
spaces, combining Unicode, CRLF and printable ASCII), plus Back retaining current
text. Original export entry Views routed to their original review destinations;
nonempty Back routed through original discard dialogs to BackStack. Seed data
stayed unchanged. No encryption/decryption algorithm or entropy source ran in
this test. Review screens, visual Unicode glyph completeness, scanned-key append,
empty-key policy, and complete encrypt/decrypt/ID flows remain unqualified.
See `validation/encrypted-entry-arm.json`.

One initial 100 ms scripted Save pulse timed out. The identical sequence passed
before an input change; no root cause for that specific timeout is asserted.
Inspection separately found that Runtime discarded a press seen low only once
when the next poll occurred after release. Runtime now emits one complete tap
when the sampled interval meets its debounce threshold, following the original
GPIO check_for_low release fallback. Subthreshold bounce is ignored, and the
new-screen release gate still rejects carried holds. Unit tests reproduce the
one-low-sample gap, bounce and held-key handoff, and final entry hardware checks
pass after the change. This does not recover a pulse never sampled at all, or
establish real GPIO short-click latency. The failed receipt is retained under
`validation/encrypted-entry-initial-timeout-arm.json`.


### Encrypted-backup review presentation (2026-10-30)

The encryption-key and mnemonic-ID review adapters use the pinned native
button-list screen with a scrolling body. They retain the entire original value
rather than the Python screen's three-line fitted/truncated presentation. Focus
starts in the body so an overflowing value is shown before action buttons.
Native button indices and Back still reach the original Views. ASCII-space
markers reuse the pinned passphrase screen's draw/delete callbacks: all spaces
for encryption keys, and leading/trailing/doubled spaces for mnemonic IDs.
Empty input is displayed as `(empty)` without changing the value passed onward.
The proportional body font and scrolling layout are presentation divergences;
Unicode glyph coverage, wrapped-space visibility and optical readability require
separate visual qualification. Embedded NUL remains explicitly unsupported.

`tests/encrypted_review_flow.py` runs the original review/export encryption Views
and original decrypt View with public fixtures, unchanged KDF iteration settings
and time delta. It selects AES-ECB solely to exercise the existing no-camera-IV
branch, not as a new encryption recommendation. Camera-derived IV modes remain
pending. Export text must be converted to UTF-8 bytes at the simulated scan
boundary, exactly as a QR reader returns bytes. An initial diagnostic omitted
that conversion and failed parsing; its runner log is retained under
`dist/lvgl-app/checks/encrypted-review-20261030T171519813458Z.*`.
No keys, encrypted payloads or seed pixels are written to diagnostic receipts.


The subsequent rendered-QR round trip passed on the Luckfox LCD. Original
transcription-mode selection and fullscreen export Views produced a native QR;
native ZXing decoded the transmitted RGB565 framebuffer into exact expected
bytes. Those decoded bytes then entered the original decrypt View: a wrong key
was rejected, and the correct key restored the exact public mnemonic. The QR
framebuffer was black on exit and the runner found no remaining owners. Receipt:
`validation/encrypted-qr-roundtrip-arm.json`. This covers AES-ECB only and uses
scripted keys plus injected View dependencies; optical scanning, physical input,
full Controller integration and other encryption modes remain unqualified.


### Encrypted QR manual-transcription implementation (2026-10-30)

The original encrypted whole/zoom Screen classes now adapt to the pinned native
whole/zoom builders, carrying the exact original Python-generated QR matrix.
The whole screen keeps its encrypted title and Begin NxN action. Zoom keeps
original return-None semantics, navigation, no screensaver, and the encrypted
five-module virtual border (ordinary SeedQR retains four). Native border values
are validated before context allocation; only the two original values are
accepted. The implementation still supports only original template sizes
21/25/29/33. Fullscreen export is unaffected. Hardware acceptance of this new
branch is recorded separately from the earlier fullscreen crypto round trip.


Encrypted manual transcription now has an original-View LCD checkpoint:
`validation/encrypted-transcription-arm.json`. A real original-model encrypted
29x29 payload decoded exactly from the whole-QR framebuffer, zoom navigation
returned to SeedOptions with cleared history, and original decrypt recovered the
public mnemonic. Input is scripted, View dependencies are injected, and optical
scanning and other encryption modes remain pending.

The pinned native zoom builder omitted the 33x33 alignment registration block
handled by the original Python QR helper. A small source patch adds its original
24,24 position. The actual native framebuffer regression failed before the fix
(white circle corner) and passed after (solid black square corner), for both
four- and five-module borders. Invalid borders reject and the native process
recovers. See `validation/transcription-registration-arm.json` for exact scope
and retained failing-baseline reference. This is a rendered-pixel geometry check,
not complete 33x33 optical/transcription qualification.


### Message-signing screen implementation (2026-10-30)

Both original signing confirmation Screen classes now use their pinned native
counterparts. Address derivation and signature generation remain in original
Views/helpers. The message screen's original constructor computed PIL pages and
mutated Controller.sign_message_data. Its replacement creates one complete
scrolling page in `paged_message`, matching the pinned native screen's documented
scrolling presentation while retaining the original View's Next/Back/page-loop
contract. Existing cached pages are honored individually. Exact message text is
never trimmed, normalized or modified for signing. Embedded NUL review explicitly
fails rather than silently hiding a C-string suffix. Unicode font completeness
and visual readability still need qualification.

`message_contracts.prepare` performs this narrow presentation initialization
before direct Screen display; no original wallet or signature method is replaced.
Native address confirmation keeps the original full path/address and Sign message
button. Native address-body vertical centering is an upstream layout difference.
The native review scrolls content before enabling its action by default. The
original Satochip branches remain in the Views and require separate hardware
qualification; implementing these screens does not qualify smartcard signing.


Message signing now has a scoped original-View LCD checkpoint:
`validation/message-signing-arm.json`, rerunnable with
`mise run lvgl:app:hardware message-signing`. Short Unicode and long scrolling
public messages passed review, address Back without data loss, original signing,
cryptographic signature verification using the derived public key, byte-exact
native ZXing decode of the rendered signature QR, and original exit cleanup.
First-page Back clears original signing state. It uses a preselected public seed
and one mainnet native-segwit derivation; no optical, full Controller, smartcard,
or all-policy qualification is claimed. The original app and pinned native source
checkouts remain clean. An initial harness error expanded a None destination
argument; the harness now uses the same empty-argument handling as Controller,
and the failed receipt is retained. Current host suite: 74 tests pass.


### Wallet descriptor screen implementation (2026-10-30)

`descriptor_contracts.py` maps LoadMultisigWalletDescriptorScreen to the pinned
native list and MultisigWalletDescriptorScreen to the pinned descriptor builder.
The original load explanation, back policy, available actions, computed policy,
and complete fingerprint list are preserved. Invalid or missing values fail
explicitly before native rendering rather than silently omitting signing keys.
No descriptor parser, normalization, key ordering, PSBT classification or resume
routing is replaced. Both adapters start with review content before actions.
The descriptor builder receives a small optional read-first navigation patch;
other callers retain the upstream default. Native overflow navigation provides
scrolling for longer lists, whose full visual readability needs qualification.

The hardware diagnostic uses public seed-derived xpubs in a 2-of-3 descriptor.
Only the physical camera source is replaced with synthetic NV12 input; native
receiver, preview, ZXing, original ScanWalletDescriptorView and original parsing
are exercised. View dependencies and keys are injected. Resume routes are checked
at destination boundaries and do not by themselves qualify complete multisig
transaction signing or address verification. Smartcard loading remains pending.


The descriptor hardware checkpoint passed; see `validation/descriptor-arm.json`
and rerun with `mise run lvgl:app:hardware descriptor`. A public 2-of-3 descriptor
traversed actual native receive/preview/ZXing and original parsing, preserving all
three fingerprints and normalizing distinct receive/change branches. Original
LCD review/OK retained the descriptor, Back cleared it, and load Cancel retained
its original Home/BackStack routing. PSBT resume checked both parser-restart and
change-detail destinations; verify-address resume checked its destination and
flow reset. Native QR exited cleanly and the runner found no remaining owners.
These are destination checks, not complete multisig signing/address acceptance.
The physical camera and button input were simulated. Current host suite: 76 pass.


### Address explorer screen implementation (2026-10-30)

Both explorer Screen classes now adapt to their pinned native builders. Original
ToolsAddressExplorer Views still derive, cache, page and encode addresses. The
adapter preserves the seed fingerprint and original settings-derived script-name
(or custom-path display), or the original descriptor policy name. List requests
carry full unmodified addresses, page start, selection and initial scroll offset.
Runtime validates N address rows plus the original Next action; native-generated
labels do not accidentally reduce the allowed response count to zero.

The native list deliberately differs from Python's symmetric head/tail truncation:
it uses upstream's prefix-aware truncation and formatted full-address focus
reveal. It uses an overflowing non-bottom list instead of Python's bottom list.
These are existing pinned upstream presentation differences; full addresses and
QR bytes remain unchanged. The source View still rejects unimplemented custom
address derivation; rendering its context does not implement that derivation.

The hardware diagnostic checks seed-native-segwit and public 2-of-3 descriptor
receive/change branches, Next paging, index 17 selection, independently derived
addresses, native rendered QR decoding, unchanged cached pages, return destination
selection/scroll arguments, and original SeedOptions Back cleanup. Exact visual
scroll restoration and every supported script/network remain separate acceptance
gaps. Keys and View initialization are injected; this is not full Controller or
optical qualification.


The first explorer LCD run timed out on the initial source-choice press before
address paging. Its receipt is retained at
`dist/lvgl-app/checks/explorer-20261030T173227782001Z.json`. The diagnostic was
changed from 100 ms presses after a 150 ms initial delay to 220 ms presses with
130 ms releases after a 500 ms delay, with page-stage logging. This is a test
input pacing change; the failure alone does not establish an app input cause or
qualify physical-button latency.


The address explorer LCD check passed all four seed/descriptor receive/change
cases. See `validation/explorer-arm.json` and rerun with
`mise run lvgl:app:hardware explorer`. Original Views generated/cached 20 addresses,
paged to index 17, matched independently derived addresses, and exported byte-exact
QRs decoded by native ZXing. Original QR return selection/scroll arguments, cached
page contents, list Back, and SeedOptions Back cleanup passed. This does not prove
exact visual scroll restoration, optical input or every script/network. Longer
scripted press/release timing passed after the initial pulse timeout; real GPIO
latency and that timeout's cause remain unqualified. Current host suite: 78 pass.


### Final-word calculation screen implementation (2026-10-30)

`final_word_contracts.py` adapts the original build-final-word explanation to the
pinned list and the calculation/result Screen classes to their pinned specialized
builders. Original Views and mnemonic_generation still supply selected entropy
bits, checksum bits, corrected word, pending mnemonic conversion and destinations.
The adapter validates supported lengths/binary strings but calculates no entropy
or checksum. It retains the original input and final-word captions, checksum
highlight information, 12th/24th titles, fingerprint, and Load/Discard buttons.

The pinned calculation builder has documented presentation differences: its bit
font is 22px instead of Python's 20px, and its post-load overlay labels miss the
upstream RTL/shaped-locale load pass. These remain explicit multilingual acceptance
gaps, not claims of full visual parity. The separate native result screen reuses
the original-style final-word/fingerprint arrangement. NUL text is rejected.

The hardware diagnostic initializes public pending-mnemonic fixtures and exercises
original zero, coin-bit and selected-word calculation branches for 12/24 words.
Coin-bit input is provided to the original calculation View, not collected from
a coin keyboard in this diagnostic. It independently derives expected BIP39
mnemonics from fixed public entropy bytes. Load/Discard destination checks do not
by themselves qualify the subsequent finalize/discard execution.


Final-word LCD checks passed all six 12/24-word zero/coin-bit/selected-word public
cases. See `validation/final-word-arm.json` and rerun with
`mise run lvgl:app:hardware final-word`. Original checksum calculation produced
exact independently derived BIP39 mnemonics/entropy; original pending-seed
conversion and Load/Discard destinations passed. Result Back preserved the
pending mnemonic. This does not qualify coin-keyboard collection or execution of
the destination finalize/discard Views, which retain separate acceptance scopes.
Current host suite: 80 tests pass. The installed app/image remains unchanged.


### Coin-entry acceptance diagnostic (2026-10-30)

`tests/coin_flow.py` drives the actual pinned native keyboard through original
ToolsCalcFinalWordCoinFlipsView. It cancels after one entered bit, then enters a
wrong leading zero, moves DOWN to the native Delete control row, deletes it, and
enters a fixed alternating public sequence. Exact 7/3-bit results feed original
checksum calculation, independently compared to BIP39 entropy. The first draft
incorrectly navigated Delete as an inline value-row key; its periodic sequence
could accidentally match without deleting. That run was deliberately interrupted
and must not be treated as a deletion test. Its failed/interrupt receipt is
retained at `dist/lvgl-app/checks/coin-20261030T174208307200Z.json`.
This diagnostic uses public scripted inputs, not measured physical coin entropy.


Coin-entry LCD acceptance passed for 12/24 words. See `validation/coin-arm.json`
and rerun with `mise run lvgl:app:hardware coin`. The actual native keyboard
canceled partial input without mutation, deleted an intentionally wrong leading
bit, and returned exact mixed seven/three-bit sequences to the original Views.
Original checksum results matched independent BIP39 entropy/mnemonics. The
12-word Load path executed original finalization and stored exactly one matching
seed; the 24-word Discard path executed original discard and cleared pending
storage. These close the corresponding earlier fixture-injection/destination-only
gaps for these cases. Real coin entropy, physical GPIO input, full Controller
integration and every policy remain unqualified. Installed app/image unchanged.


### Camera entropy acquisition preparation (2026-10-30)

`python/entropy_source.py` prepares the pinned original
ToolsImageEntropyLivePreviewScreen._run acquisition loop for native presentation.
It parses the original method and replaces exactly three renderer-lock drawing
blocks plus its font allocation, routing the first display block to a native
preview callback. Pool admission, variation checks, sample conversion/resizing,
SHA256 deduplication, moving window, full-pool capture gate, release-before-capture,
final camera read and normal camera stop stay in the original method AST. Original
source guards must run before installation; structural checks additionally reject
changed drawing boundaries or any remaining renderer access. RNG health gating
and entropy mixing stay in the original Views and are not part of this transform.

`tests/test_entropy_source.py` runs both the transformed and unmodified original
loops with identical synthetic camera/button dependencies (original drawing is
stubbed only in the comparison). Results match byte-for-byte and acquisition
counts/stops match for changing frames, held capture, frozen frames and flat
frames. Flat/frozen input never fills the pool. Unexpected presentation structure
is rejected. Initial test expectations had an off-by-one frame window and a
mutation aimed at an earlier class; corrected assertions now match the original
loop. Current host suite: 84 pass.

This is preparation for the complete camera-entropy UI. These screens remain
unmigrated in coverage: native preview/entropy indicator, final-image review,
Camera backend integration, held-key handoff, failure/wipe cleanup, original
entropy processing through the full flow and physical-camera acceptance remain
pending. No camera-entropy hardware qualification or boot image is claimed by
these host tests. No images, entropy samples or derived seeds are saved.


### Native camera entropy presentation implementation (2026-10-30)

The two camera-entropy Screen classes now dispatch to `image_entropy.py`.
Live acquisition executes the guarded original loop from entropy_source, with
native preview, pool progress and a colored Shannon-status caption. The caption
uses the original grayscale/BILINEAR sample, original Shannon helper, original
3.5/4.5 thresholds and approximately one-second cadence. The colored text replaces
the original indicator ellipse; this is presentation only, not an entropy gate.
Review retains original left-reshoot/right-or-click-accept and release-before-input
behavior. Original Views retain RNG refusal, preview-pool length enforcement,
final-image contrast/crop preparation, mixing, quality checks and seed creation.

Display images currently fit inside the existing 240x180 RGB preview transport,
centered in the 240x240 screen, rather than the original full-square preview.
Only a display copy is resized/letterboxed; stored frames and final pixels are
untouched. PIL remains for original image/sample operations and display scaling,
not screen text/control drawing. Full-square presentation, physical-button latency,
visual review and matched memory/CPU acceptance remain pending.

`entropy_camera.py` uses the existing integration's guarded camera-source transform
in a private module, leaving the original Camera singleton/module registry intact.
It verifies the shared integration hash, retains original Camera conversion and
rotation semantics, and selects the existing Rust frontend only during stream
construction, restoring the prior environment afterward. This private adapter
requires actual-camera hardware validation; synthetic-source checks bypass it.
Camera stop and native clear run in finally blocks on normal return, cancel,
exceptions and lifecycle interruption. Combined wipe/fault qualification remains
pending. No images, pool bytes or generated seed values are logged or saved.


The full-resolution synthetic camera-entropy LCD flow passed:
`validation/image-entropy-synthetic-arm.json`, rerunnable with
`mise run lvgl:app:hardware image-entropy --timeout 360`. Original RNG refusal
ran before camera startup; five compact preview samples and a separate full-res
final image survived capture, reshoot/accept preserved final pixels, and the
original mixer/system RNG produced a valid pending 12-word seed. Original Views
cleared image references. The native host and diagnostic exited cleanly.

This is NOT acceptable performance yet. Earlier hardware attempts timed out or
failed preview initialization while swap was exhausted and the kernel reported
swap write errors; see `validation/image-entropy-initial-failures-arm.json`.
An unused 4,385,552-byte /tmp/lvgl-demo binary was owner-checked, archived locally,
SHA256 verified, and its RAM-backed temporary copy removed. MemAvailable rose
from 27,044 to 31,328 KiB in that cleanup snapshot. Archive/metadata remain ignored
under `dist/lvgl-app/temporary-archive/`. The unchanged full-resolution fixture
subsequently passed, but its long runtime is not a controlled causal or matched
latency result. An unnecessary test-local reshoot-image reference remains to be
released in the next diagnostic revision. The final attempted stop saw no process
because the test had already exited successfully; it did not interrupt this pass.

Physical-camera/private-adapter acceptance, memory/latency fixes and measurement,
full-square presentation, physical input and combined lifecycle failure/wipe tests
remain pending. Current host suite: 84 pass. No boot image was built or flashed.


### Instrumented entropy diagnostic checkpoint (2026-10-30)

The next full-resolution synthetic run passed in 58.522 seconds, including 23.636
seconds before app-import/setup completion. Median display-image round trip was
0.327 seconds (maximum 0.570, 20 updates). That interval includes display-copy
scaling, IPC, native rendering and SPI acknowledgement, not GPIO response or
full-stream FPS. Pixel-sink calls totaled 11.211 seconds across 5,188,360 bytes;
these run on the reader thread and overlap other work, so timings must not be
subtracted as exclusive categories. Metadata and exact hashes are in
`validation/image-entropy-resources-arm.json`.

Python VmHWM reached 30,444 KiB (29.7 MiB), with VmSwap reaching 11,388 KiB at a
sampled acquisition stage. System SwapFree reached 4 KiB in that sample. Two Python
threads were present (main/output reader); this synthetic test has no Rust camera
owner. RSS includes shared/file pages and excludes swapped pages. These are
Python-only observations, not total frontend/ISP/DMA memory, PSS or an original-app
comparison. Capture/seed correctness and cleanup remained passing, but memory and
responsiveness acceptance remains open. Reducing working-set/import cost is the
next performance task.

The harness now releases its old reshoot-image local immediately after checking
pixel preservation, retains 640x480 inputs, records fault/swap counters and stage
elapsed time, and measures display/pixel-write durations without logging images
or seed values. It also registers SIGUSR1 stack-only diagnostic dumps for future
stall inspection. The faster run is not an isolated measure of that reference
change: prior temporary-storage cleanup and cache/swap state also differ. The
original camera-entropy implementation and frame/mixer rules were unchanged.
Host suite remains 84 passing tests. Installed app/image unchanged; no flashing.


### Import-cost and compatibility inventory (2026-10-30)

`mise run lvgl:app:hardware import-profile --import-profile` records staged /proc
metadata and Python importtime without starting the LCD, wallet or camera. The
runner still checks deployed source hashes and termination, and labels profiling
in its receipt. `validation/import-profile-arm.json` preserves module additions,
code-symbol binding metadata and verified matching source hashes for tools/GPG/
smartcard/password/microSD Views; no symbol values or wallet data are exported.

The first staged profile measured about 7.1 seconds and 59 new modules in the Tools
phase, after Seed Views were already loaded. Smartcard/GPG modules had roughly
1.8/1.5 seconds self import time respectively. These figures include profiling
and source compilation and are not controlled feature-memory savings; cumulative
importtime rows overlap and must not be added. The next profile also inventories
404 non-dunder Tools bindings and its re-export modules. Star imports plus explicit
compatibility aliases mean a lazy-loader change must preserve original identities,
internal routes and external imports, not merely hide modules until a benchmark
passes. No production import behavior changed at this checkpoint.

Checked-hash bytecode caching is the next low-risk experiment: retain the same
module graph and validate source hashes while measuring source-compilation cost.
The current hardware runner intentionally uses -B and a fresh cache prefix, so
its startup measurements do not represent a precompiled boot image. Persistent
cache placement must avoid RAM-backed /tmp and remain isolated from installed
app files. Image builds, matched memory measurements and full acceptance remain
outstanding. Host suite: 84 pass; no flashing.


### Checked-hash bytecode experiment (2026-10-30)

The optional hardware-runner flag `--bytecode-cache` prepares checked-hash CPython
bytecode under `/userdata/shieldsigner-lvgl-bytecode`, outside installed sources
and RAM-backed /tmp. `python/bytecode_cache.py` compiles app, camera-adapter and
diagnostic Python sources only when missing, stale or truncated; it verifies
magic, checked-hash flags, source hash and code-object decoding. The runtime keeps
-B (no automatic cache writes) and selects that prefix, so checked source caches
can be read without silently creating timestamp caches. Source hashes are checked
by CPython on import. No module imports, View logic or feature routes are removed.

Tests cover a same-size/same-mtime edit, including actual Python loader execution
of the new value before cache repair, reuse, truncated-cache repair, isolated
placement and refusal without an explicit prefix. Current suite: 86 pass.

The first prepared cache held 213 source files, 3,760,539 bytes, and cost 15.797
seconds to build. Cached import-only profiling took 11.099 seconds versus 19.433
in its uncached reference; all recorded export binding kind/origin/qualname
metadata matched. This is not cross-process object identity proof. See
`validation/checked-bytecode-import-arm.json`.

The complete 640x480 synthetic entropy fixture then passed with caching:
40.841 seconds total and 13.727 seconds through import/setup, versus the prior
58.522 / 23.636 seconds. Python VmHWM was 27,576 KiB (26.9 MiB), versus 30,444 KiB.
Exact swap/preview counters and preparation cost are in
`validation/checked-bytecode-entropy-arm.json`. Cache/system state is not controlled,
so these are observed run differences, not isolated causal savings or total-system
memory. Full camera/RNG/controller and physical-button acceptance remain pending.
A reproducible image must generate bytecode with the target Python magic/version
and stable source paths; this on-board development cache is not that image artifact.

Example: `mise run lvgl:app:hardware image-entropy --bytecode-cache --timeout 360`.
Default checks retain their fresh-prefix behavior. Cache preparation is separate
from the timed diagnostic, and both are recorded. Installed app/image unchanged;
no flashing.


### Physical entropy-camera checkpoint (2026-10-30)

The private adapter now starts through `entropy_camera.start`, selecting the
same default owner.json as scan, honoring explicit config, and restoring the
previous frontend/config environment on success or failure. Missing config fails
before startup. An initial test had no owner config and waited for a socket
without launching an owner; checks/entropy-camera-20261030T182851017901Z retains
that failure. Two real-camera read/reopen/stop cycles passed after the fix:
`validation/entropy-camera-arm.json`. No pixels were saved or wallet generated.
Rerun: `mise run lvgl:app:hardware entropy-camera --bytecode-cache`.

Combined LCD/native entropy acquisition FAILED with the owner error
`ISP parameter pool remained full for 250 ms`. Owner metrics also showed queue
buildup and page faults; causality is not isolated. DMA was zero after failure
and no owners remained. Keep this flow unqualified; see
`validation/image-entropy-physical-failure-arm.json`. No capture threshold or
firmware deadline was weakened. The diagnostic injects RNG-health status and
View initialization and never generates a wallet or saves physical camera pixels.

At 88 files, deployment reached ADB's shell-command length limit. Remote SHA256
checks now batch at most 16 paths and verify every digest. A regression checks
all 88 paths across six calls. That preflight failure did not execute a camera
test. Environment-restoration/missing-config tests also pass; host suite: 89.
Installed app/image unchanged; no flashing.


### Physical entropy integration resolution checkpoint (2026-10-30)

The current default physical diagnostic passed capture of five distinct compact
samples, original full-RGB final capture/review, reshoot, reopen/cancel, owner exit
zero and zero DMA buffers after both cycles. Receipt:
`validation/image-entropy-physical-arm.json`. RNG-health status and View
initialization remain injected, keys scripted, and no wallet is generated or
physical pixels exported. This is basic bounded integration, not a full Controller,
real RNG-monitor, long-soak, multilingual or performance acceptance claim. Swap
pressure remains significant in the recorded snapshots.

Controls are preserved in `validation/camera-entropy-controls-arm.json`: ordinary
scan passed, Tools-preloaded scan passed, and two duration-controlled 30-second
loaded scan cycles displayed 73/75 frames and cleaned up. The soak intentionally
ignores incidental QR completion; it does not qualify optical payload decoding.
A no-image-update entropy control still failed and narrowed investigation beyond
frame presentation alone. Earlier error/timing metadata is automatically captured
from new owner logs before small-RAM log rotation, excluding image payload fields.

The decisive diagnostic correction was removing `unittest.mock` (and its asyncio
import graph) from the physical harness. It now uses `diagnostic_scope.attribute`,
which restores exact function identity on success/failure. Earlier snapshots
showed 11+ MiB Python swap and exhausted system swap, with multi-second image
updates. Original RGB reads passed in a control after this change, then passed
again as the default. These are observed staged results, not isolated byte savings
or proof that all real-memory pressure is solved. No app feature, entropy gate,
firmware queue size or ISP deadline was weakened.

The method-only AST adapter remains: it parses only guarded original _run source
and replaces the same three drawing blocks/font allocation, leaving both camera
reads and all collection rules original. Host tracemalloc peak was 586,215 bytes
versus 4,570,766 for whole-module parsing; this is not measured ARM RSS savings.
Experimental grayscale/pairing operations were byte checked on target but were
unnecessary for the final passing path, so they were moved to
`tests/experimental_entropy_samples.py` and removed from production dispatch.
The final synthetic original-mixer regression also passed; historical intermediate
receipts retain their exact earlier source hashes. Current suite: 93 tests pass.

Full physical seed creation with real health monitoring, lifecycle fault/wipe
integration, matched total-system performance and all other remaining migration
requirements still precede image assembly and flashing.


### Final entropy image fallback: private Rust Camera dependency

`python/entropy_fallback.py` lazily transforms only the Camera import in the
pinned `ToolsImageEntropyFinalImageView.run` method. The file path and SHA are
guarded before installation; the canonical application Camera module/singleton
and application files stay unchanged. The private three-method facade starts
the same guarded Rust backend used by entropy preview. Original ten-read retry
limit, delays, finally-stop, contrast/crop of a display copy, and accept/reshoot
routes remain upstream code. Uninstall restores both View initialization and
the original method. Host tests cover lazy installation, changed-source rejection,
restoration, ten empty reads, startup/read exceptions and exactly-once stop.

Physical camera/LCD fallback capture passed reshoot (5.937 s) and accept (4.595 s),
with owner exit 0 and zero DMA buffers after each. This is scripted input with
injected View dependencies, not full Controller/RNG or optical entropy qualification.
See `validation/entropy-fallback-arm.json`. Host suite now has 97 passing tests.
Image assembly and flashing remain gated on the full migration requirements.


### Real Controller entropy integration: failing qualification

`mise run lvgl:app:hardware controller-entropy-cancel --bytecode-cache` now
exercises original Controller/View initialization, mandatory storage initialization,
real RNG monitor/health gate, and original entropy acquisition under LVGL.
It uses a temporary settings path, disabled inactivity timer, scripted input,
and the existing guarded small-RAM policy. It does not inject RNG health or
replace View initialization. Boot-failover MMIO clearing is bypassed in the test.

Two runs failed before cancellation could complete. The instrumented run reached
one preview with no collected pool frames, then the Rust owner reported full AE
event queue and 250 ms ISP parameter slot timeout. Python grew from 24,480 KiB
RSS / 152 KiB swap just after Controller initialization to 17,016 KiB RSS /
10,980 KiB swap during acquisition; system swap-free fell to 204 KiB. Sampled
Python major faults rose from 63 to 583. A separate live system observation
showed swap-free reaching zero. These indicate severe memory pressure; a causal
fix is not yet established. No device owners remained after the test.

Evidence: `validation/controller-entropy-failure-arm.json`. Full Controller
entropy functionality remains a release blocker even though isolated capture
and final-image fallback checks passed. Preserve this failure when optimizing
imports or image buffers; do not weaken RNG or entropy collection rules to pass.


### Rejected memory experiment: pre-camera garbage collection

A diagnostic-only `controller-entropy-gc` case runs the same real Controller
path, adding a single explicit `gc.collect()` immediately before camera start.
It collected only 14 objects in 0.227 seconds and still failed before the first
preview. Python RSS moved from 24,828 to 25,740 KiB while VmSwap fell from
1,768 to 740 KiB and major faults rose from 94 to 403: this is page-in activity,
not evidence of meaningful heap recovery. No production collection call was
added. See `validation/controller-entropy-gc-experiment-arm.json`.

A candidate Pillow font-probe optimization was also not applied: import-profile
evidence shows `PIL._imagingft` already loaded by normal screen imports, so
skipping the Controller's later RAQM probe would not remove that dependency.
The next optimization must address retained imports/buffers rather than claim
that garbage collection or removing that log probe solves the pressure.


### Deferred screen module dispatch installation

`screen_bridge.install_modules` replaces the eager imports of six screen modules
with an exact-name import hook. Already-loaded modules are patched immediately;
others retain their original Python loader and are patched after execution.
Original class identities, dataclass fields/constructors, wallet Views and module
exports are preserved. Hash and path checks guard each deferred screen import.
Only supported classes defined by that module are patched; imported base classes
are handled by their own defining module. Uninstall removes the finder and
restores patches in reverse order. Two host tests cover deferred loading, exact
identity/fields, source rejection before execution, and restoration.

This avoids loading unrelated screen families during dispatch setup. It does
not solve the real Controller entropy failure: the corresponding hardware test
still failed before its first preview, with Python using about 10 MiB swap.
Do not claim a measured memory saving from this change. Evidence is retained in
`validation/lazy-screens-camera-failure-arm.json`; host suite is 99 tests.

The post-change physical-LCD startup regression passed original splash/warning →
Home → settings → Home with real Controller and worker cleanup. See
`validation/lazy-screens-startup-arm.json`. This is temporary deployment and
scripted input, not cold-boot qualification.


### RAM-backed diagnostic bundle removed

Moved the temporary Python/test bundle from `/tmp/shieldsigner-lvgl-app` to
`/userdata/shieldsigner-lvgl-app`. Its old RAM-backed files occupied about 820 KiB;
all current deployed sources are verified against local bundle hashes. An initial
attempt to run the native host from `/userdata` correctly failed due to that
filesystem's `noexec` mount. It was returned to `/tmp`; no mount flags or installed
files were changed. The runner records source and executable paths in receipts.

The original-sampling real Controller regression still failed after one preview.
Its last pixel snapshot showed 10,152 KiB Python swap and 1,936 KiB system swap-free.
This is not a matched causal memory-saving measurement and not a successful
camera fix. See `validation/userdata-bundle-camera-failure-arm.json`.

A separate luma sample representation experiment, without preview/sample pairing,
also failed under real Controller load. No luma substitution was enabled in
production. Its first attempt had a diagnostic function-name collision caught
before Controller startup; the corrected run is preserved separately in
`validation/controller-entropy-luma-experiment-arm.json`.


### Corrected Controller diagnostic camera profile

The earlier `--small-ram` Controller diagnostic enabled optional-import policy
but omitted `SHIELDSIGNER_SMALL_RAM=1`. The SDK uses that separate environment
flag to choose NV12 instead of RGB transport, reduced preview, and bounded
owner logs. Consequently the prior failures are valid evidence for the larger
RGB path, not proof that the intended NV12 path fails. The missing test setup
was an error; memory pressure alone was not an established root cause.

`startup_policy.install` now explicitly enables that camera environment after
its guarded shared policy succeeds, keeping the two parts together. Unit tests
verify successful selection and that rejected integration sources do not change
the caller's environment. The real Controller diagnostic asserts NV12 after
start and records the actual backend and owner cleanup. Original two reads,
full-resolution RGB final image, RNG gate and sampling/mixing code stay unchanged.

Corrected physical camera/LCD runs passed capture/cancel → Home (3 preview frames,
2 pool frames), and capture → review → accept → mnemonic length. Both used the
real Controller/View initialization and real health/wipe workers; all camera
owners exited and DMA buffers were released. See
`validation/controller-entropy-cancel-arm.json` and
`validation/controller-entropy-review-arm.json`. Scripted keys and temporary
settings are still test substitutions; these are not cold-boot, manual-button,
full seed creation or automatic inactivity-wipe qualification.


### Physical Controller entropy → original mixer → pending seed

`mise run lvgl:app:hardware controller-entropy-generate --bytecode-cache` passed
physical camera capture with the original five-sample pool, native final review,
12-word choice, original `_derive_camera_entropy_bytes` and mnemonic/Seed
construction, reaching the original seed warning. The real Controller's RNG
monitor and original mixer health checks were active. No health result or
crypto/entropy output was injected. The test verified a nonempty 12-word pending
seed and cleared controller image references, then called the original
`clear_pending_seed`, verifying the held seed-byte buffer was zeroed and the
seed's words/bytes cleared. No seed words or pixels were logged or persisted.

Evidence: `validation/controller-entropy-generate-arm.json`. This single run
does not qualify every word length, seed-word review/finalization, backup quiz,
manual input, automatic wipe during acquisition, or long-running performance.
The successful prior review run still sampled 11,584 KiB Python swap; memory and
responsiveness remain acceptance work. No image assembly or flashing occurred.


### Expected wipe unwind and original timer qualification

The original Controller's broad error handler printed an expected
`WipeInterrupted` traceback before calling the LVGL lifecycle handler. The new
`quiet_wipe_route` transform adds only a dedicated catch immediately before that
broad handler, forwarding to the same `handle_exception` call without printing
an expected-control-flow traceback. The pinned Controller file hash and handler
shape are checked; installation/restoration is process-local. Unexpected errors
still take the original traceback/error route. Host tests verify that distinction
and reject an unreviewed Controller without modifying it.

The strict runner initially rejected an otherwise successful explicit entropy
wipe because of that traceback. After the route change, both explicit and
original-worker timer tests passed. A public test seed was wiped, acquisition
was interrupted after pool entry, the camera owner exited 0, DMA buffers returned
to zero, the old native process exited, a new process started and the original
Controller returned Home. The timer test sets the original five-minute setting
and injects an expired `last_input_time`; the unmodified polling worker detects
it and calls the original wipe policy. This is not five-minute wall-clock soak
or manual-input qualification. Evidence: `validation/entropy-wipe-arm.json` and
`validation/entropy-wipe-timer-arm.json`. Host suite: 101 tests.


### Settings QR import presentation

Added explicit `SettingsQRReviewScreen` and `SettingsQRConfirmationScreen`
contracts. Review uses the pinned upstream `button_list_screen`, showing the
quoted, untranslated user configuration name and localized warning as a single
scrollable text block, with fixed Apply/Cancel actions and no Back button. This
changes the original separate TextArea positioning but preserves all text and
confirmation choices. Confirmation reuses the pinned upstream
`settings_qr_confirmation_screen` with config name, host-localized status and
Home action. Neither contract parses or applies settings.

Physical-LCD checks passed both Cancel (whole settings dictionary unchanged)
and Apply (denomination changes to sats after confirmation only), using the
original `SettingsIngestSettingsQRView` parser and `_apply_settings` method.
Persistent settings were disabled and no settings file was written. No display
driver/inversion switch, persistence write, optical scanning or full Controller
route was exercised. Evidence: `validation/settingsqr-arm.json`. Three host
contract tests cover action/content mapping, upstream confirmation reuse and
invalid input rejection; suite now has 104 passing tests.


### SettingsQR through original Controller and native QR pipeline

The later SettingsQR qualification removes the earlier injected View
initialization. Original Controller storage initialization, RNG and wipe workers
run with the explicit small-RAM startup policy. Cancel preserves the whole
settings dictionary; Apply changes the selected denomination only after review,
shows confirmation and returns Home through original routing.

The complete scan-route variant supplies a public synthetic NV12 frame via the
existing `synthetic_frames.Source` seam, scoped with the lightweight diagnostic
attribute context (no unittest.mock on target). Actual FrameReceiver, Rust QR
worker, original DecodeQR, ScanView classification and SettingsIngestSettingsQRView
run unchanged. It passes Scan → review → Apply → confirmation → Home; source
and QR worker are stopped and no owners remain. Synthetic pixels do not prove
optical acquisition. Persistence remains disabled and driver/inversion switching
was not exercised. Evidence: `validation/controller-settingsqr-scan-arm.json`,
`validation/controller-settingsqr-apply-arm.json`, and
`validation/controller-settingsqr-cancel-arm.json`.


### Restart, Loader and unplug message contracts

Added explicit ResetScreen, RebootToLoaderScreen and PowerOffNotRequiredScreen
contracts with the pinned original titles/body text and nav flags. Reset and
Loader share upstream `reset_screen`, which accepts host text/title; the unplug
message uses upstream `power_off_not_required_screen`. No body choices are
added to these informational screens. Reset/Loader have no Back or Power nav;
unplug has Back. Original View/system-action implementations are unchanged.

Physical-LCD presentation checks passed both noninteractive messages with a
bounded diagnostic exit, without invoking RestartView/RebootToLoaderView or
OS commands. Original PowerOffView (injected dependency initialization) returned
BackStackView via native Back selection. The test did not restart the installed
app, reboot into Loader or change boot services. Actual restart launcher and
post-flash boot acceptance remain open. Evidence:
`validation/power-presentation-arm.json`. Two host contract tests verify builders,
nav constraints and message content; suite is 106 passing tests.


### Text QR screen adapters

Added six explicit Text QR contracts: text entry, review, mode selection, whole
transcription QR, zoom and optional scan-confirmation prompt. Text entry reuses
the pinned upstream passphrase keyboard and maps its result to the original
`textToEncode`/`is_back_button` contract, preserving whitespace and Unicode.
No trimming or escape interpretation is added: the original ToolsTextQRTextEntryView
still interprets literal Unicode escapes. Embedded NUL display/entry is explicitly
unsupported. The original review's fitted text layout becomes a scrollable
read-first text block with optional visible-space markers; payload text remains
unchanged. Mode/confirmation messages retain original content.

Whole/zoom transcription reuse upstream seed transcription builders, using
original Python qrcode matrices, a Text QR title, and original five-module zoom
border/initial block coordinates. No wallet/encoding/View implementation was
copied. Direct constructors continue through the reviewed screen import hook.

The physical-LCD test passed four exact Save fixtures, Back with exact edited
text, original nonempty-Back discard navigation, original literal Unicode-escape
conversion, review → generate → mode → whole QR → zoom → Done. Initial test
importing gpg_views directly failed due to upstream circular imports; using the
normal tools_views re-export path fixed test setup without modifying upstream.
Evidence: `validation/textqr-arm.json`. This test injects View initialization and
keys, uses a short public 21-module payload, and does not qualify fullscreen,
optical scan confirmation, all sizes or combined Controller navigation.
Three new host tests bring the suite to 109 passing tests.


### TextQR full-screen pixels and confirmation outcomes

Added a public-fixture hardware diagnostic, without production View changes.
Original ToolsTextQRFullScreenModeView/GenericStaticQrEncoder rendered three
payloads through upstream LVGL QR output. Actual Rust QR decoding of transmitted
LCD RGB565 pixels returned exact original UTF-8 bytes for whitespace, composed/
decomposed Unicode with CRLF, and a longer text payload. The pixel buffer was
black after each original View exit and its destination returned to Text QR.

Original ToolsTranscribeTextQRConfirmScanView, native FrameReceiver, Rust QR
worker and original DecodeQR handled exact match → success/TextQR, mismatch →
warning/BackStack, and cancellation → warning/BackStack. Camera sources were
public synthetic NV12 fixtures; each source stopped and QR worker exited 0.
The controller dependency supplies only the screensaver-reset callback. View
initialization and buttons remain diagnostic substitutions. This is not optical
or full Controller qualification and does not cover all transcription matrices.

The initial diagnostic attempt omitted the SDK Python directory and failed
before execution; adding the same explicit SDK path used by existing camera
checks fixed setup. Passing evidence:
`validation/textqr-output-confirm-arm.json`. Host suite remains 109 tests.


### System Info and Version presentation

VersionScreen reuses pinned upstream `version_screen`; original View values
(version, optional fork/commit, datetime) are passed through, with the exact
original `%Y-%m-%d %H:%M:%S UTC` timestamp format. SystemInfoScreen uses a
scrollable upstream button-list text body, retaining original row ordering,
labels and optional firmware/source/build rows instead of fixed TextArea
positions. Device identifier strings are displayed but not stored in receipts.

Both original Views passed real Controller/View initialization, physical-LCD
rendering, scripted Back to Settings and health-worker cleanup. The System Info
run used actual device data. Version initially failed because the installed
image has no version.json. The later Version check supplied public metadata
through a temporary override of the original VersionUtils file-path method.
It retained original JSON/version/release logic, with no fake Version singleton
or app-file changes. On-device version helper SHA matched the pinned checkout
and is now included in source guards. Correct generated version.json remains
a required image-packaging deliverable.

The lightweight diagnostic attribute helper now restores raw class descriptors
and inherited attribute ownership, with a new regression test. This avoids
leaving a bound-method replacement when overriding a classmethod. Evidence:
`validation/controller-system-info-arm.json` and
`validation/controller-version-arm.json`. Host suite: 112 passing tests.


### Memory Info live label updates

MemoryInfoScreen retains original ROWS, translated labels, `_build_lines`,
`helpers.system_memory` sampler/formatter, and two-second REFRESH_INTERVAL.
The helper is now source guarded. Presentation changes from per-row PIL
TextAreas plus UpdateThread to one scrollable upstream button-list text label
refreshed on the existing LVGL runtime loop. No new refresh thread is created.
Only changed formatted text is sent; no memory accounting semantics are changed.

The native `info_text` operation requires an explicitly enabled live-info
button-list label and bounds text to 4,096 bytes with no NUL. New screen/clear
commands invalidate the label pointer. Updating the existing label retains
focus and restores its scrolling ancestor's offset, including when its screen
is underneath an overlay. The operation never rebuilds the screen.

Physical-LCD original Controller/View check passed six samples, one changed
label update, return to Hardware Settings and worker cleanup. The separate ARM
protocol fixture proves unchanged selection and nonzero scroll across an update,
rejects three malformed updates plus inactive updates, and recovers to a valid
screen. It does not qualify every locale, overlay timing or long-running soak.
Evidence: `validation/controller-memory-info-arm.json` and
`validation/live-info-protocol-arm.json`. Host suite: 115 passing tests.

The post-change startup regression also passed splash/warning → Home → Settings
→ Home on the new native binary (`validation/live-info-startup-regression-arm.json`).
All these runs remain temporary deployment; no boot image or microSD was changed.


### Battery Info live presentation

Added a BatteryInfoScreen contract using the existing upstream button-list live
label and original placeholder rows. `battery_info.sample` calls the original
BatteryHat API, preserving enabled/detected checks, voltage/power precision,
milliamp-to-amp conversion (including sign), percent precision and curve fallback.
A host regression compiles the pinned original UpdateThread.run and compares
its resulting rows with this adapter for detected and absent-sensor cases.
No charging/calibration decisions or hardware API implementations were changed.

The original five-second polling cadence runs on the existing UI loop instead
of a PIL drawing thread; changed text updates in place. Original BatteryInfoView
still gates on `is_enabled`. Physical-LCD real Controller tests passed both the
real no-compatible-monitor warning and positive values with a public API fixture
substituted after Controller initialization. Both returned to Hardware Settings
and cleaned up their workers. This board has no compatible battery monitor;
the positive receipt does not qualify real I2C reads, read latency, charging or
calibration. Slow sensor API reads may affect UI responsiveness and need physical
qualification. Evidence: `validation/controller-battery-absent-arm.json` and
`validation/controller-battery-fixture-arm.json`. Four host tests bring the suite
to 119 passing tests.


### Hardening paged report

HardeningTestScreen now maps to the existing upstream button-list paged-text
adapter, with its original Test Hardening title, page count, exact preformatted
report page and More/Done actions. Paged text now enables the existing native
read-first navigation behavior rather than focusing its action while text may
be overflowing. The original HardeningTestView probes, verdict, report formatting,
PIL-based page splitting and report reuse remain unchanged; the original helper
is source guarded. No check result is injected, suppressed or reclassified.

Physical-LCD real Controller testing traversed all five original report pages
in order with the same cached report object and returned Advanced Settings.
Only scripted input, temporary settings, small-RAM startup and the existing
boot-counter test bypass were used. Report details/host identifiers were not
persisted in the receipt. The test proves presentation/navigation, not that this
development image is hardened. Evidence: `validation/controller-hardening-arm.json`.
Two additional host tests verify paging/actions and invalid-index rejection;
suite: 121 passing tests.


### Network Info fixed-width paging and visual correction

ToolsNetworkInfoScreen reuses the paged button-list adapter with its original
Network Info title, Next/Done labels, exact View-split page text and read-first
navigation. A local upstream patch adds optional `text_monospace`: the original
pinned Inconsolata-Regular TTF is embedded by assets.py, then LVGL TinyTTF creates
a single cached 16 px native font. Body fallback remains available; Latin network
text is left aligned with explicit line spacing. No command/parser/View routing
implementation is replaced in production. Font bytes/provenance stay generated
under dist and their hash is recorded; eventual image license closure must
preserve original font attribution/terms.

An initial bitmap-font navigation pass was rejected on visual review: Unscii's
16 px variant had 16 px advances and the generic BODY_FONT-based tight-spacing
calculation caused row overlap. Replacing it with the original TTF at 16 px and
overriding spacing corrected the public LCD capture. No blanket readability
claim is made for every locale or arbitrary network output. The public capture
is kept only under ignored dist; identifiers from actual networks are not saved.

Original last-page Done returns BackStack. The initial test assumed menu exit
and timed out cycling pages. The corrected test explicitly checks forward page
order and the original backward path, failing immediately on unexpected repeats.
This preserves upstream routing rather than silently changing its semantics.
Historical receipts are `validation/network-initial-navigation-failure-arm.json`
and `validation/network-rejected-layout-arm.json`; current passing receipts are
`validation/controller-network-fixture-arm.json` and
`validation/controller-network-absent-arm.json`. Positive command output is a
public fixture; the actual image lacks /usr/bin/network-info and its Unavailable
route also passed. Host suite: 122 passing tests.

The native lv_conf.h guard now uses LVGL's expected LV_CONF_H name. This removes
the repeated false include-check warning without changing configured behavior;
the corrected font build completed with no such warnings.

The resulting native binary also passed original startup splash/warning → Home
→ Settings → Home (`validation/network-font-startup-regression-arm.json`).
No boot image was assembled and no microSD was flashed.


### Battery calibration presentation and private camera

Added intro/start contracts with original text, centered Next/Start actions and
Back. Running calibration keeps the pinned original `_run` and helpers; an AST
transform replaces exactly one renderer-lock drawing block with a native-label
update and rejects unexpected remaining renderer access. It does not replace
logging, elapsed/charging calculations, one-minute CSV cadence, file deletion,
return codes or camera-start-failure policy. The four running values appear in
the upstream live-info body beneath a calibration header instead of the original
full-canvas PIL positions. Screensaver is disabled for the running any-input-to-
cancel screen. Original hardware override state and LVGL wipe checks are polled.

Camera dependency is a private guarded Rust Camera instance. The shared start
helper now forwards explicit kwargs so the original calibration request
(320×240, 30 fps, rgb) reaches the existing camera/profile adapter unchanged;
the hardware profile remains responsible for actual transport/resolution.
The original try/finally controls camera stop. Each native status update waits
for its acknowledgement, avoiding an unbounded stream of queued ACK events.

Host tests compare the adapted loop against the unmodified original for button
cancel, 30-second charging abort, startup failure, rendered values, camera calls,
cleanup and CSV bytes. A 63-second simulated-time case verifies exact writes
at timestamps 0 and 60. These are model tests, not electrical measurements.

Physical-LCD/camera checks passed setup Back routes and cancellation, then real
Controller setup → run → cancel → Home with eight received frames. A further
real-Controller run using positive-current metadata aborted after 32.595 seconds
including startup, with 437 frames and 56 acknowledged display updates. Temporary
logs were removed, owners exited 0 and DMA buffers returned to zero. Battery and
card metadata were fixtures; real charging detection, full depletion, curve
generation and actual-media log processing are not qualified. Receipts:
`validation/calibration-arm.json`, `validation/controller-calibration-arm.json`,
`validation/controller-calibration-charging-arm.json`. Host suite: 125 tests pass.


### Donation screen attribution

DonateScreen maps directly to pinned upstream `donate_screen`. Original
SeedSigner funding paragraph, percent formatting, URL, title and Back behavior
are preserved. Original DonateView and Controller navigation passed on the LCD
with scripted input, returning Settings and cleaning up workers. No new donation
address, QR payload, payment flow or browser action was introduced. Evidence:
`validation/controller-donate-arm.json`. Host suite: 126 passing tests.


### I/O Test and wipe input ownership

IOTestScreen reuses pinned upstream io_test_screen chrome, all five D-pad/click
indicators and three auxiliary keys. KEY1 captures, KEY2 clears, KEY3 exits.
The original capture profile list, ten-read retry loops and camera-stop finally
blocks are extracted from the pinned method with a structure-checked AST adapter.
Requests remain 640×480/12/bgr, 480×480/6/bgr, 1280×720/4/bgr, then
320×240/12/bgr; the existing Rust camera adapter selects actual transport.
The camera is private and created lazily. Presentation applies original contrast
processing but center-crops to a 240×240 square for the upstream camera plane,
instead of the fork's body-fit placement. This is a field-of-view/layout divergence;
it does not change entropy, wallet or QR inputs. Still pixels use bounded RGB565
IPC and are not saved by these diagnostics. Clear hides the native still plane.

Wipe interruption crosses the original broad Exception retry handlers using a
private BaseException wrapper, then rethrows the original lifecycle interruption.
The active profile's finally still stops its camera before Controller resumes.
Native input reset also consumes the original GPIO override flag, matching the
old wait_for entry behavior. This includes a second override set by Home's wipe
toast; leaving it set could cancel subsequent calibration immediately.

ARM protocol validation passed red-plane byte order, indicators, auxiliary keys,
Clear and malformed/inactive commands (validation/io-protocol-arm.json).
Physical camera/LCD checks passed capture → clear → reopen → exit through the
original Controller, and wipe during the first capture profile with zero captures,
seed cleared, camera exit 0, native restart and Home. Wipe evidence is
validation/io-wipe-arm.json; entropy wipe regression after the shared input fix is
validation/io-input-entropy-wipe-regression-arm.json. Inputs are scripted, not
physical button tests; no optical or long-duration qualification is claimed.

An initial I/O wipe diagnostic missed its scripted input during initialization;
its timeout is not a passing cleanup test. The script now starts key timing at
the first input poll and fails promptly if capture never starts. A later run
caught the lingering Home-toast override; both observations drove the fixes above.
The runner's hard-timeout path still needs qualification: subprocess.run kills
the local ADB session before remote cleanup and ps argv may be truncated. Normal
completion and injected wipe cleanup passing do not qualify hard-timeout cleanup.
Host suite: 131 passing tests. No boot image assembled or microSD flashed.


### Diagnostic timeout runner correction

The runner now uses Popen.wait so the local ADB session remains attached during
remote SIGINT cleanup. Owner identity uses exact NUL-delimited /proc/PID/cmdline
arguments instead of the truncated ps command column; substring matches and
unrelated Python scripts are rejected. Processes disappearing during inspection
are tolerated. The local ADB process is terminated only after the cleanup grace
period, and remaining remote owners still fail the receipt; no remote force-kill
was added. Host tests cover truncated ps metadata, exact script matching and an
owner exiting during observation. Host suite: 132 passing tests. Hardware timeout
qualification is separate from these host checks.

Intentional 25-second physical calibration timeout exercised the corrected runner: exact remote diagnostic interrupted, KeyboardInterrupt unwound, no live Python/native/camera owners remained. A subsequent DMA probe reported zero objects/bytes. The receipt deliberately remains passed:false because a timed-out calibration is not successful functional validation. Evidence: validation/calibration-intentional-timeout-arm.json. Other timeout phases and transport loss remain unqualified.


### Large-button grid adapter

LargeButtonScreen now maps to pinned upstream power_options_screen, which already
uses the shared LargeButtonScreen grid geometry for two and four buttons. Original
localized labels, optional icons, initial selection, title and navigation flags
are passed through. Other button counts reject as in the original screen. Optional
long_press_key remains explicitly unsupported and raises UnmigratedScreen; this
adapter does not silently turn a configured long hold into selection. Custom font
and selected-color parity still require review. Host suite: 133 passing tests.
The actual Luckfox power menu has three actions and keeps the original ButtonList
route; this adapter does not execute restart, shutdown or loader commands.

Initial physical grid test caught Left from first-column tile staying in body instead of original Back. Evidence: validation/grid-back-navigation-failure-arm.json. grid-back-navigation.patch adds original first-column Left-to-Back and Right-from-Back restoration to the shared upstream grid navigation. Rebuild and hardware regression remain required; this failure is not an accepted navigation divergence.

Grid hardware rerun passed two-tile right selection, four-tile down/right selection and first-column Left → Back, alongside original reset/loader presentation and PowerOff Back. No system action executed. Evidence: validation/large-grid-arm.json. Right-from-Back restoration still needs a dedicated flow check.

Coverage audit additionally found Home callbacks are not yet migrated: MainMenuScreen.__post_init__ normally enables Luckfox KEY3 five-second Loader recovery, and _run_callback handles directional display switching. The current bridge bypasses those PIL constructors/callbacks. Existing Home navigation receipts do not qualify recovery holds, display switching, or the Home battery indicator thread. These remain explicit migration gates, along with generic LargeButtonScreen configured long press.

Shared grid patch also passed original Controller startup splash/warning → Home → Settings → Home with physical LCD and scripted input (validation/grid-startup-regression-arm.json). The original installed wallet files and boot image remain unchanged.


### Grid tap-versus-hold migration

The runtime now arbitrates configured LargeButtonScreen holds before sending
selection to LVGL: a debounced short press sends one tap on release; a continuous
hold returns the configured original code at its threshold without selecting a
tile first. Lifecycle checks and activity updates continue during the hold. Policy
is scoped to each Runtime.run invocation and cleared on all exits. Invalid key,
threshold or return-code contracts fail explicitly.

Home reads the original Luckfox profile allowlist, HardwareButtonsConstants.KEY3,
MainMenuScreen.VERY_LONG_PRESS_MS and RET_CODE__REBOOT_TO_LOADER to restore its
profile-specific recovery hold without constructing PIL widgets. The runtime
returns the code only; original Controller routing owns the resulting action.
Directional display switching and the Home battery indicator remain separate
unmigrated callbacks. Generic custom style parity remains open. Host suite: 137
passing tests; hardware short/long hold qualification is recorded separately.

Physical-LCD scripted checks passed .3-second KEY3 taps selecting index 0 and 5.3-second holds returning the original Loader code for both generic LargeButtonScreen and Luckfox MainMenuScreen. Native grid and power-presentation regression also passed. No Controller Loader dispatch/reboot was executed. Evidence: validation/grid-hold-arm.json.

Initial hold implementation passed original startup splash/warning → Home → Settings → Home (validation/grid-hold-startup-arm.json). A follow-up protects screensaver wake: a hold begun while the saver is active goes through native wake-consumption and cannot become a Loader action until release and a fresh press. Active recovery holds send native activity pulses to prevent saver activation during the gesture. Host suite: 138 tests; physical combined wake-hold check pending.

Combined screensaver wake/hold first hardware check failed its assertion (validation/grid-wake-hold-initial-failure-arm.json). Cause not yet established; follow-up waits for observed active screensaver and records result/timing. Do not treat host wake tests or earlier short/long hold success as combined wake-hold qualification.

Follow-up wake diagnostic established saver was never observed active (validation/grid-wake-disabled-saver-failure-arm.json). overlay_manager screensaver_dispatch dismisses explicitly shown savers when timeout is zero; the diagnostic had left it disabled. Corrected test enables a 600 ms timeout and waits for automatic activation before KEY3. This setup error does not establish production gesture correctness; rerun required.

Corrected combined hardware run passed: automatic saver activation at accelerated 600 ms, 5.3-second KEY3 wake hold consumed without selection/Loader return, then fresh tap selects normally. Generic and Home short-tap/five-second recovery-hold cases also passed in the same run. Evidence: validation/grid-wake-hold-arm.json. Inputs are scripted and no reboot executed; physical GPIO and normal-duration idle/soak remain separate gates.


### Home battery metadata and indicator

Home now polls original BatteryHat on the UI loop once per second, with no extra
thread. Original percent truncation, positive-current charging sign, unknown
percent, and 75/50/25 icon thresholds are retained. Once shown, loss of detection
keeps an unknown indicator; disabling monitoring skips updates, as the original
UpdateThread does. Before first detection no widget is visible. Only changes are
sent to native rendering. No battery measurement or calibration algorithms change.

Native rendering uses LVGL battery/charging symbols instead of PIL FontAwesome,
14 px at the upper-left edge to keep the grid/title usable. This differs from
original larger glyph/position and remains subject to visual review. Low percent
uses pinned ERROR_COLOR (#FF1B0A) on the icon only and normal text #FCFCFC. The
label pair belongs to the saved Home root even when first detection occurs under
screensaver; pointers reset before scene replacement. Malformed/inactive updates
reject. Sensor fixtures and native framebuffer checks do not prove physical I2C,
charging or battery accuracy. Host suite: 141 passing tests.

Final-color native ARM protocol passed (validation/home-battery-protocol-arm.json): initial absent unchanged, first detection during saver survives dismissal, low icon exact RGB565 color, charging differs from percent, unknown/hide, malformed/inactive rejection. Initial test looked for little-endian output but display packets are byte-swapped for SPI; correcting that assertion resolved it before matching pinned colors. No physical battery claim.

Real Controller startup regression also passed splash/warning → Home → Settings → Home with physical LCD and actual absent/disabled BatteryHat path (validation/home-battery-startup-arm.json). Original workers cleaned up; no sensor metadata injected. Visible-indicator visual review, positive real-Controller fixture and actual battery/I2C remain unqualified.


Positive-metadata original-Controller qualification now passed Home → Settings →
Home with scripted input and physical LCD. Fixture values exercised truncated 12%,
80% plus positive-current charging, and unknown percent. Three public framebuffer
captures were visually reviewed: red low icon/12%, white full icon/charging bolt,
and white empty icon/--%, with no Home-title or tile overlap. Evidence:
validation/controller-home-battery-arm.json. Fixture initialization returns false
and is_alive returns false: it supplies presentation metadata without real sensor
initialization, worker startup, curve processing or discharge-log access. Two
initial diagnostic failures were missing fixture initialization/thread-status
methods; their failed receipts are preserved separately. Original Controller,
View initialization, wallet workers and navigation were retained. Actual battery
sensor, charging electrical accuracy, and long-duration overlay behavior remain
unqualified. Public captures stay under ignored dist/lvgl-app/review/home-battery.


### Isolated application entry assembly

New python/app.py invokes guarded original main.py rather than copying its CLI,
logging setup, testing-build option or initial I/O route. Source guards now cover
../main.py; installed and pinned originals matched SHA256
53cac0bf03376c04673c0b03e569454fa815f60bd64a9568b11fe01b2322b8f4.
The entry requires separate settings, checks competing Python/native/camera owners
without stopping them, and composes runtime, Renderer, screens, toasts, lifecycle
and Controller screensaver adapters in process-local contexts. Original Controller
startup still owns wallet/business/entropy decisions. Worker shutdown is joined
before adapter/device teardown; this lifecycle is not yet hardware qualified.

Read-only actual-board --check passed source/settings/executable preflight without
hardware or Controller imports, Settings singleton creation or settings writes
(validation/app-entry-check-arm.json). Host tests cover original CLI forwarding
and exact competing-owner refusal including excluding the current process.
Host suite: 144 passing tests. Full interactive entry, boot-counter policy during
temporary use, shutdown/signals, native artifact provenance and image/service
packaging remain gates. No production launcher installed or image flashed.


Entry shutdown now attempts every distinct worker's stop and join even if another
worker fails, skips unstarted/dead workers, and reports incomplete shutdown.
Host tests verify all stop attempts precede joins, duplicate-worker identities are
handled once, unstarted workers aren't joined, and a failed sibling doesn't skip
later cleanup. Host suite: 146 passing tests. This is not proof of every hardware
or process-loss shutdown path.


### Cancellable original microSD watcher

Actual entry test found original MicroSD.run blocked in open(FIFO_PATH), so the
inherited stop flag did not release it and entry shutdown correctly failed
(validation/app-entry-microsd-shutdown-failure-arm.json). New guarded lifecycle
adapter replaces exactly the original FIFO-open/read block with a nonblocking
reader that checks the original keep_running flag with at most 100 ms select
waits. The initial storage-state handling, FIFO setup, event payload, settings
callback, original toast construction and loop cadence remain original AST code.
No synthetic card action is sent to unblock shutdown. Partial messages on stop
are discarded; input is bounded at 4096 bytes, above normal mdev action messages.
The process-local method patch is restored after worker teardown and installed
source files are not edited. hardware/microsd.py is now source guarded.

Real FIFO host tests passed empty-writer cancellation and complete chunked writer
message delivery, plus unexpected source-block rejection. Host suite: 149 passing
tests. Hardware entry rerun and actual insert/remove hotplug remain distinct
qualification requirements.

Actual entry rerun passed original main --iotest → I/O Exit → Settings Back → Home on physical LCD with scripted buttons, followed by diagnostic StopFlow. Native process exited, original wallet workers stopped, microSD watcher joined and original settings hash unchanged (validation/app-entry-flow-arm.json). Boot-counter MMIO was suppressed in a test-only screen hook; entry itself retains original boot behavior. This is not normal boot, signal shutdown, physical-button/card-hotplug or reboot qualification.


### Entry SIGTERM unwinding

The isolated entry installs a scoped SIGTERM handler before acquiring hardware.
The first TERM raises KeyboardInterrupt through original Controller's deliberate
exit path; later TERM requests during cleanup are ignored so teardown can finish.
The prior signal handler is restored on context exit. SIGINT and other signal
policies are unchanged. Host handler test verifies one interrupt, repeated-request
behavior and prior-handler restoration. Host suite: 150 tests.

Actual entry on physical LCD passed TERM during idle I/O screen, then native,
microSD and original wallet worker cleanup, with original settings unchanged
(validation/app-entry-sigterm-arm.json). Expected interruption is caught by the
diagnostic; this receipt does not qualify standalone process exit status, service
manager behavior, early-startup signals, or arbitrary repeated signal sequences.

First fixed-delay TERM camera diagnostic failed its compound stream-state assertion; no remaining owner processes were found, but this did not prove interruption after an active frame. Evidence: validation/app-entry-sigterm-camera-initial-failure-arm.json. Follow-up waits for frames_received > 0 before TERM, with a bounded diagnostic wait and explicit stream-state failure details.

Bounded first-frame TERM rerun passed actual isolated entry during physical camera capture: stream received a frame before TERM, original capture finally stopped owner with exit 0, DMA returned to zero, native/microSD/wallet workers finished and original settings stayed unchanged (validation/app-entry-sigterm-camera-arm.json). No service-manager, standalone exit-status or every-phase signal claim; no image flashed.


MicroSD host parity now executes both the unmodified pinned original run method
and transformed method with the same fixture dependencies. Initial inserted and
removed states, FIFO recreation, complete add/remove messages including newline,
settings-before-toast callback order, loop cadence and FIFO setup failure agree.
Cancellation stops without generating a toast or extra settings callback. Host
suite: 151 passing tests. These fixture comparisons do not establish physical
mount detection or mdev delivery on actual card insertion/removal.

ARM private-FIFO check passed the transformed pinned watcher with complete chunked add/remove writer messages, initial storage callback, original settings/toast event order, no fabricated shutdown event, stopped/joined worker and restored original method (validation/microsd-events-arm.json). Storage/toast endpoints were fixtures; actual card/mdev/mount changes remain unqualified.


### Multisig signing fixture preflight

Added a public regtest 2-of-3 fixture copied from pinned original
 tests/psbt_testing_util.py (source SHA recorded in tests/multisig_fixture.py).
Three explicitly public upstream mnemonic vectors derive the original BIP48
regtest accounts and sortedmulti descriptor. Original base input and recipient/
change output literals are reused, avoiding invented transaction policy.
The fixture is for tests only and must never receive funds.

Actual ARM model preflight passed original PSBTParser multisig recognition, one
input/two outputs, zero initial signatures, one signer insufficient, second signer
finalizes, and unchanged transaction outputs (validation/multisig-model-arm.json).
This model result does not qualify any frontend or full Controller route. The
LVGL review/Back/partial-signature/export check is a separate test.


Multisig frontend checkpoint passed physical LCD with scripted input and original
PSBTMathView → recipient → descriptor-verified change → Finalize → signed QR
Views. Back preserved unsigned bytes. Approval added exactly one ECDSA signature,
verified against the original PSBT sighash. One signature cannot finalize 2-of-3.
A validation-only copy accepted the second public cosigner, both signatures
verified, and finalized with unchanged outputs. App export remained the original
one-signature partial PSBT; actual ZXing reconstructed exact exported bytes from
rendered QR pixels (validation/multisig-signing-arm.json).

View dependency initialization and matching descriptor were injected/preloaded;
this is not full Controller, optical capture, descriptor loading/verification UX,
seed selection, mismatched-wallet refusal or all multisig policy qualification.
Only explicitly public test keys were used. No wallet/crypto code changed or
production image flashed.


### Original Controller multisig signing checkpoint

Original Controller and View initialization now passed a combined physical-LCD
regtest 2-of-3 route: Overview → Math → recipient → descriptor-verified change →
Finalize → signed QR → Home route. Diagnostic stops at Home before rendering it.
Original Overview constructs the parser from the preloaded public transaction,
selected public seed and matching descriptor. No View initialization is replaced.
The app's one signature verifies against its PSBT sighash; actual ZXing recovers
exact signed partial-PSBT bytes from native pixels. MainMenuView clears original
psbt/parser/selected-transaction-seed fields; wallet and microSD workers finish.
Evidence: validation/controller-multisig-arm.json.

Public seed/descriptor/transaction are preloaded; original seed selection,
descriptor scan/loading, initial PSBT scan, mismatched-wallet and other policy
branches remain separate gates. Stage snapshots record Python/native RSS, swap,
threads, faults and system memory. They exclude the separate QR-reader process
and are not a matched baseline, peak-total-memory measurement or performance
claim. Original boot-counter MMIO is suppressed only in the diagnostic.

Original Controller final-approval Back also passed: exact unsigned bytes unchanged, zero signatures, no export, Home route reached and original transaction fields cleared (validation/controller-multisig-cancel-arm.json). This scoped test starts at Finalize with the parser preloaded and does not qualify every earlier cancellation point.


Original Controller signer selection now passed before the multisig review/sign/
export route (validation/controller-multisig-select-seed-arm.json). Two public
seeds were loaded through original SeedStorage pending/finalize APIs: one unrelated
and one matching cosigner. psbt_seed starts None. Original PSBTSelectSeedView marks
the unrelated fingerprint with (?) and scripted navigation selects the matching
second row, then original Overview/parser/review/signing/QR/Home routing proceeds.
Signature verifies, exact partial PSBT is recovered by ZXing from rendered pixels,
transaction fields clear and both stored seeds remain loaded until diagnostic
cleanup wipes the public test objects. View initialization and wallet/crypto
methods are unchanged. This qualifies existing-loaded-seed selection, not mnemonic
entry/seed scanning, descriptor loading, initial PSBT scanning or physical buttons.

Combined Controller descriptor-route first diagnostic stalled with immediate Select on the read-first load-descriptor menu, then entered original error handling. Failed receipt: validation/controller-multisig-descriptor-menu-failure-arm.json. The corrected script uses the earlier qualified scroll-to-actions/Scan selection and adds current screen to input deadlines plus screen sequence in failures. No production UI or wallet routing change was made for this diagnostic correction.

The initial menu-scroll correction assumed two actions, matching the older isolated descriptor test where smartcards were disabled. Real Controller settings add SeedKeeper, so that script chose it. The exact owned diagnostic was interrupted with SIGINT and cleaned up (validation/controller-multisig-descriptor-option-failure-arm.json). Corrected navigation uses actual button count to select first Scan action; no feature is disabled and original menu/routing stay unchanged.


Combined original Controller descriptor flow now passed
(validation/controller-multisig-descriptor-arm.json). Initial descriptor is None;
original loaded-seed selection and transaction review reach unverified change.
Original load menu selects Scan using actual button count, including enabled
smartcard options. Original ScanWalletDescriptorView receives synthetic NV12
through the actual FrameReceiver and native ZXing worker, parses the public BIP48
regtest descriptor and displays original descriptor review. Return resumes original
change verification: recorded states are exactly [False, True]. Signing and exact
partial-PSBT QR export then pass, followed by Home routing and state/worker cleanup.

No View initialization or wallet/parser/crypto logic is replaced. Synthetic camera
source is diagnostic-only and stops before completion. Physical LCD/input script
are used; optical descriptor capture, initial PSBT scan, seed import, mismatched
wallet/refusal and other script/threshold policies remain separate requirements.


Initial PSBT input diagnostic started ScanPSBTView directly without Home history.
Scan's original skip_current_view route then encountered empty back_stack; this
was not patched in Controller. Failed evidence:
validation/controller-multisig-scan-history-failure-arm.json. Corrected diagnostic
starts at original Home and selects Scan, providing normal navigation history.
Public animated UR PSBT input uses a new lazy synthetic fixture source: each
payload generates one NV12 frame at read time, releasing it after receiver read,
instead of retaining N full-size images. Only test infrastructure changes; original
camera production path and QR/wallet logic are unchanged. Screen-stage metadata
is now emitted without transaction payloads for live diagnostic progress.


### Combined Home-to-multisig scan/sign/export

Original Controller now passed Home → Scan → signer selection → Overview → Math
→ recipient → unverified change → descriptor load/scan/review → verified change
→ Finalize → signed QR → Home route on physical LCD with scripted input.
Neither transaction nor descriptor starts loaded. Animated public UR PSBT frames
and public descriptor frames use synthetic NV12 with actual FrameReceiver/native
ZXing and unmodified original ScanView/parser. Parsed PSBT serialization matches
input exactly. Original storage contains two preloaded public seeds; original UI
marks unrelated seed and selects matching cosigner. Change verification records
[False, True]. Original signing produces a verified signature, and ZXing recovers
exact exported partial-PSBT bytes from rendered QR pixels. Original Home clears
transaction state; sources stop and workers finish. Evidence:
validation/controller-multisig-scan-arm.json.

Final Home rendering is stopped by diagnostic after the original Home View clears
state; initial Home was actually rendered and Scan chosen. This is not optical
camera/lighting qualification or seed import. All policy/refusal variants,
matched resources/latency/soak, remaining settings/hardware functions and image/
boot gates remain open. Snapshot memory includes synthetic-fixture overhead and
omits separate QR-reader snapshots; it cannot establish production total RAM.


### Descriptor mismatch branch

Original Controller/View initialization passed overview/math/recipient review with
a public 2-of-3 parser and deliberately mismatched stored 3-of-3 descriptor.
Original PSBTChangeDetailsView verification rendered Descriptor mismatch /
Descriptor cleared on the physical LCD, cleared the stored descriptor and routed
back to unverified change configuration. Zero signatures, no export, exact unsigned
PSBT bytes preserved; workers cleaned up. Evidence:
validation/controller-multisig-mismatch-arm.json.

The parser was preloaded with correct fixture metadata, then stored descriptor
changed, specifically testing the existing change-verification mismatch branch.
Diagnostic stops before rendering the subsequent unverified page or selecting
reload/skip. This does not claim parser mismatch refusal, optical scanning,
all descriptor mismatches, recovery reload or prohibition of signing after the
original explicit skip-verification option. No wallet/parser policy changes.


### Original Controller Compact SeedQR import

Public 12-word BIP39 import passed from empty storage through original Controller:
initial Home → Scan → SeedFinalize → SeedOptions → Home route. Synthetic raw
Compact SeedQR entropy goes through actual FrameReceiver/native ZXing and original
ScanView. Before Done, pending mnemonic and displayed fingerprint match while
finalized storage remains empty. Original Done finalizes pending seed; options
Back retains exactly the imported seed and its bytes equal reference BIP39 output.
View initialization is original; source stops, wallet/microSD workers finish and
diagnostic cleanup wipes public seed objects. Evidence:
validation/controller-seed-scan-12-arm.json. Physical LCD/scripted input; final
Home rendering is stopped after original routing. Optical capture, manual entry,
passphrases, non-BIP39 formats and other word lengths remain separate gates.

The same original-Controller Compact SeedQR import path also passed for public 24-word BIP39 entropy, including exact resulting seed bytes and original pending/finalized storage transitions (validation/controller-seed-scan-24-arm.json). This extends the scoped result to 12 and 24 words; it does not generalize to optical capture or other seed formats/import methods.


### First paired renderer resource benchmark

New frontend_resources.py uses original Controller/View initialization and the
same scripted GPIO read replacement in both PIL and LVGL modes, with original
settings title asserted. First Home idles eight seconds, then Down/Right selects
Settings and Back returns Home. Original source pins, small-RAM policy, temporary
settings and microSD cancellation helper are common; boot-counter MMIO is bypassed
only in the diagnostic. Both runs passed and exact bundle hashes agree.
Per-process RSS/anonymous RSS/swap/threads/ticks and system metadata are retained.
Evidence: validation/resources-lvgl-arm.json, validation/resources-pil-arm.json,
validation/frontend-idle-comparison.json; summary table in README.

One warm-device pair does not demonstrate lower memory: median Python RSS
24,768 KiB LVGL versus 24,900 KiB PIL, with additional native RSS 1,520 KiB.
Median swap 40 versus 344 KiB, and Python anonymous RSS 14,864 versus 14,436 KiB.
Process idle CPU over the sampled window is 11.170% Python + 1.167% native versus
7.503% PIL Python of one core. This is evidence to investigate polling, not a
production CPU guarantee. Script/sampling overhead is included, caches/system
pressure may differ, no camera is started, and RSS is not total physical memory.
Matched cold startup, repeat ordering, input latency, camera/signing loads and
soak remain unqualified. No installed app or image was changed/flashed.


### Idle input bookkeeping

ARM cProfile found repeated idle poll_input per-key maps, empty event queue
get/exception work and substantial scripted-GPIO callback overhead. Added early
return only after lifecycle/hardware reads and release gate, with no active key,
current key or pending debounce map. Pending short presses/releases therefore
still use the original input loop. Empty event queue is checked before get;
producer races can delay consumption until the next unchanged 10 ms poll but do
not drop events. Main UI monitors continue before input polling. Host regression
suite passes 152 tests, including a new idle-lifecycle check.

The unprofiled second warm pair measured LVGL Python 8.179% + native 0.835% of
one core, versus PIL Python 7.673%. Earlier LVGL was 12.337% combined. Both second
runs share exact bundle hashes; comparisons to earlier pair include changed
harness/profile-switch code and uncontrolled warm cache/system pressure, so do
not assign a precise causal saving. RSS/swap stay separate and no memory win is
claimed. Evidence: validation/profile-lvgl-idle-arm.json,
validation/frontend-idle-comparison-input-fastpath.json and associated receipts.

Physical LCD scripted input regression passed after the idle fast path: grid selection/Back, generic/Home short taps and five-second holds, screensaver wake-hold consumption and fresh tap, plus power presentation/Back. Evidence: validation/input-fastpath-holds-arm.json. No actual reboot or physical button claim.


### Temporary settings destination identity

The isolated entry now rejects original settings by both resolved path and
existing-file identity, including hard links, plus symlinks and non-regular
existing destinations. A separate existing regular file or new file under an
existing directory remains accepted without preflight writes. Host filesystem
tests verify public original/separate marker bytes unchanged; suite: 154 tests.
Actual-board read-only preflight passed after this change without hardware or
Controller import, Settings singleton creation or writes
(validation/app-entry-settings-isolation-arm.json). This is static path/identity
validation, not a concurrent-filesystem race claim or full entry-flow re-test.


### Combined transaction with signer import from empty storage

Original Controller now passed the full combined public-fixture route starting
at Home with zero stored/pending seeds and no PSBT/descriptor loaded. Scan loads
animated UR PSBT; original Select Signer chooses Scan a seed based on actual menu
items, original Compact SeedQR scan creates pending signer, original SeedFinalize
Done stores it, and original resume_main_flow routing returns to transaction
Overview without a test-selected seed assignment. Transaction review, descriptor
load/scan/review, change verification [False, True], signing and exact partial-PSBT
QR export then pass, followed by Home route and transaction-state clearing. One
imported public cosigner remains stored until diagnostic wipe. Original View
initialization, wallet/storage/parser/crypto behavior are retained. Evidence:
validation/controller-multisig-import-signer-arm.json.

Three inputs are synthetic NV12 through actual FrameReceiver/ZXing/original scan
Views; physical LCD and scripted buttons are used. All sources stop and workers
finish. Final Home rendering is stopped after original state clearing. This does
not qualify optical capture, manual or passphrase/non-BIP39 import, every policy,
matched total resources/latency/soak or image/boot acceptance. No production app,
wallet policy or image is changed/flashed by this test.


### Entry native build-manifest check

Previously the runner verified native binary identity but direct app entry only
checked that a path was executable. app.check now requires build target
arm-linux-musleabihf, nonempty input metadata and a matching binary SHA256, using
64 KiB reads. CLI --native-manifest overrides default BINARY.manifest.json.
The temporary runner stages the actual build-manifest sidecar and compares parsed
contents against its already-validated local manifest before running diagnostics.

Host tests reject changed bytes, wrong target and malformed/empty metadata; suite
155 passing. Board preflight accepts the genuine artifact and rejects a private
small dummy executable against the genuine hash, without hardware/Controller
imports, Settings creation or writes (validation/app-entry-native-manifest-arm.json).
No signature/authentication claim, new boot service, app installation or flashing.
Full interactive entry with this check remains a separate release regression.


### Entry regression and pending settings at exit

Actual original-main entry passed manifest verification plus I/O → Settings →
Home routing and cleanup (validation/app-entry-manifest-flow-arm.json). Source
review then found this entry's teardown did not flush original Settings' deferred
daemon save. The isolated entry now invokes original Settings.flush_save after
worker-stop attempts, even if worker cleanup raises. Original persistence gating,
locking, synchronous write and fsync remain in the guarded settings model.

Actual-board test schedules a public denomination change at diagnostic exit,
sets the deferred delay to 30 seconds only in the test, confirms timer pending
and no isolated file yet, then exits original Controller. Entry flush clears the
timer and writes expected JSON to the separate temporary settings destination.
Original settings hash is unchanged; worker/native cleanup passes. Evidence:
validation/app-entry-settings-flush-arm.json. Value change is injected at exit;
this does not qualify settings selection UI persistence, storage failures,
service stop exit status, all signal phases or power-loss durability. Host suite
still 155 passing tests. No existing launcher/image modified or microSD flashed.


### Original settings selection UI persistence/reload

Actual isolated original-main --iotest entry now passes I/O Exit → Settings →
Persistent settings Enabled → Back → Denomination sats → Back → Home with
physical LCD and scripted buttons. Test derives row/option indices from original
SettingsDefinition/menu data and checks initial values differ. Original
SettingsEntryUpdateSelectionView performs the changes and its checked re-entry
states are observed; no value setter is injected for this case. Four selection
screen visits occur, followed by ordinary Back navigation.

Deferred save delay is 60 seconds only in the diagnostic. At Home the timer is
still pending and no isolated file exists; original entry flush writes enabled
persistence and sats denomination. A diagnostic fresh Settings singleton reads
both values back from that file. Original settings hash is unchanged and workers/
native process finish. Evidence: validation/app-entry-settings-ui-arm.json.
Temporary file/same-process fresh-model reload do not establish reboot recovery,
SD/power-loss durability, every setting type, absent-storage/error paths, or
physical button input. No wallet policy, existing app/image or flash changed.


### Native viewport foundation for display switching

Audit confirmed isolated Renderer still requires 240×240 while original settings
and Home directional recovery support more configurations. First implementation
step adds NativeHost keyword geometry (240×240 default, upstream-supported
320×240) and bounded host CLI arguments. Native display/profile initialization
uses selected dimensions; buffer capacity accommodates width 320 but effective
render buffer stays exactly width×20 rows. Transport frame size/rectangle bounds
use the selected viewport; default protocol/argument behavior stays unchanged.
Unsupported sizes reject before client process spawn and before native LVGL init.

156 host tests pass. ARM protocol passed full-viewport painting/bounds and grid
Down/Right/Enter index 3 for both sizes (validation/display-geometry-arm.json).
No physical display is opened in that test. Application Renderer/hardware resize,
settings/recovery integration, all other builder geometry and preview/QR/I/O
scaling remain open. Upstream set_display currently has no 128×128 profile; that
original display-recovery option needs additional work rather than pretending
320×240 support completes display migration. No app settings behavior or existing
image is changed by this native-only foundation.

Default 240×240 rebuilt host also passed original Controller startup splash/warning → Home/menu/back → Home on the connected physical LCD with scripted input (validation/display-geometry-default-startup-arm.json). Wider physical panel/settings/recovery qualification remains open.


### Runtime display handoff

Runtime now tracks viewport and provides reconfigure_display: validate supported
size before stopping owner, close/join native pixel reader before hardware
callback, start matching native host, retain screensaver timeout and reset input
release/debounce state. Hardware callback failure propagates with old writer
closed and no new writer started. No automatic rollback claim. Wipe recovery now
passes tracked dimensions when recreating native host instead of defaulting to
240; fake diagnostic runtimes without geometry retain existing default behavior.

159 host tests pass, including close/configure/start ordering, unsupported size
keeping existing owner, failed callback not starting new writer, and input reset.
Actual ARM process handoff 240→320→240 passed full-viewport rendering, old PID
reaping before callback and new PID creation (validation/display-handoff-arm.json).
Hardware callback is a fixture with no SPI/GPIO: original settings/recovery
integration and physical wider-panel qualification remain open. Wipe at a wider
viewport needs its own qualification. No existing image changed/flashed.


### Renderer/ST7789 geometry wiring

Renderer.initialize_display now accepts st7789_240x240 and st7789_320x240,
keeping original Settings/inversion selection. Geometry change invokes runtime
handoff, then LuckfoxHardware.configure_display closes old LCD resources and
constructs the existing original ST7789 driver at the new dimensions. Existing
SPI/GPIO/init/inversion code is reused, not copied. Same geometry only updates
inversion. Partial new-driver initialization failure closes its resources and
propagates. Renderer canvas/disp/display-size metadata follows actual selected
geometry with canvas/draw remaining None. Other configurations, including 128×128,
are still explicit unsupported cases; no menu options were hidden.

160 host tests pass, including Renderer metadata/handoff order. ARM actual native
host plus original Settings model and fake LCD passed 240→320→240 with complete
viewport painting and old process stopped before callback
(validation/renderer-geometry-arm.json). Physical connected 240×240 default
startup/menu/back also passed after driver changes
(validation/renderer-geometry-default-startup-arm.json). Real 320×240 panel,
settings-selection UI resize, failure recovery/rollback, Home directional display
recovery and per-flow preview/QR/I/O geometry remain open. No existing image or
settings file modified; nothing flashed.


### Original display-selection UI and SPI audit

Original Controller/View initialization now passed Hardware settings → display
selection 240→320→240 → Back to settings, with real native processes and fake
LCD (validation/renderer-settings-ui-arm.json). Model, Renderer, native geometry
and old-process handoff agree. First diagnostic incorrectly started at leaf
selection without parent history and failed skip_current_view; corrected test
uses Hardware settings, with no Controller patch (failed history receipt retained).

Physical wider-panel readiness is NOT established. Review of pinned ST7789.py
SetWindows shows high bytes hardcoded zero for start/end X/Y, truncating coordinates
above 255. The isolated pixel adapter currently calls that method; it needs a
16-bit coordinate fix before 320-wide SPI is qualified. Planned change belongs in
the isolated adapter, preserving pinned original driver files and initialization.

Also correct the earlier assumption about 128×128: original Renderer uses a
240×240 logical canvas and downscales for ST7735. Preserving that contract avoids
needing a native 128×128 profile. ST7735 hardware/scaling integration remains open;
absence of an upstream native profile alone is not a blocker for that approach.
No existing image changed or flashed.


### Isolated 16-bit ST7789 rectangle writer

LuckfoxHardware pixel delivery now uses its own bounded CASET/RASET writer with
full high/low bytes for inclusive start/end coordinates, then RAMWR. It reuses
original driver's command/data/SPI chunk transfer methods and initialization;
pinned ST7789.py remains unmodified. Native RGB565 rectangle length is checked
before any window commands. This corrects inherited zero-high-byte truncation
for columns >=256. For 240×240 the complete command byte sequence matches the
original driver. Driver source hash is now guarded; installed and pinned files
matched 2d208968bfaad3b5aaaf4de18aca3aa44c786d2dd6a297a33919b9cea720255d.

163 host tests pass, including exact wide partial-window bytes, default byte
parity and invalid rectangles writing nothing. Actual ARM native 320×240 → real
transport → real pixel adapter → fake SPI endpoint passed full column 319 and
payload/window bounds (validation/display-spi-pipeline-arm.json). Connected
physical 240×240 startup/menu/back passed after the fix
(validation/display-window-default-startup-arm.json). No actual 320-wide panel,
electrical bus capture, offsets/rotation or all-flow wider-display qualification
is claimed. Original application files/image unchanged; nothing flashed.


### Completed-frame signal for ST7735 downscaling

Original Renderer._resize_for_display uses Image.LANCZOS after completing its
240×240 logical canvas. LVGL emits partial RGB565 rectangles, so resizing each
rectangle independently would break filtering at boundaries and perform repeated
full-panel writes. First prerequisite adds a native frame_complete control marker
only on lv_display_flush_is_last, after that frame's pixel packets. NativeHost
consumes this marker outside the ACK queue and invokes optional frame_sink on its
reader thread; default discovers frame_complete on a bound pixel-sink owner.
Callbacks must not reenter the transport. Default consumers without callback
simply ignore markers. Existing pixel/control framing and handshake remain.

165 host tests pass, including ACK ordering and callback failure poisoning.
Actual ARM scene/full-frame and incremental-focus completion passed with callback
fixture and no display (validation/frame-completion-arm.json). This is a
prerequisite, not completed ST7735 support: frame accumulation, LANCZOS conversion,
original ST7735 driver wiring, retained-buffer wiping and hardware qualification
remain open. No pinned driver or existing image changed/flashed.

Connected 240×240 original Controller startup/menu/back regression also passed after native frame markers were added (validation/frame-completion-startup-arm.json). ST7735 work remains separate.


### Retained logical-canvas scaler

New display_scaler.FrameScaler retains a 115,200-byte 240×240 RGB565 canvas,
validates/copies partial rectangles and performs one 128×128 LANCZOS conversion
when complete() is called with dirty data. Clean completion returns None. Native
big-endian words are byte-swapped for Pillow's BGR;16 RGB decoder; resized images
are returned for the original driver's show_image and not retained by scaler.
Explicit wipe() zeros its owned buffer in place and clears dirty state. This does
not claim erasure of all transient Python/Pillow copies, nor automatic lifecycle
integration yet. It is not allocated on current production 240×240 path.

Host task pins Pillow 11.3.0 for real scaler tests (target already has Pillow
11.0.0, unchanged). 169 tests pass: full/partial color and LANCZOS results,
incremental preservation, invalid writes and in-place buffer wipe. ARM native
frames/transport/callback passed exact comparison to pinned original Renderer
resize method on the same decoded RGB565 input, including incremental focus
update and explicit wipe after close (validation/display-scaler-pipeline-arm.json).
This is not pixel parity to original 24-bit PIL drawing before quantization.
ST7735 driver wiring, close/wipe hooks and physical/optical qualification remain
open. No existing application/image changed or flashed.


### ST7735 driver/scaler and owner cleanup integration

Renderer accepts st7735_128x128 while preserving original logical canvas 240×240,
display size 128×128, display_type st7735 and needs-resize metadata. Physical
geometry difference triggers quiesced runtime handoff even when logical viewport
stays 240. LuckfoxHardware instantiates pinned original ST7735 driver, retains
FrameScaler only in that mode, copies native partial rectangles into it, and on
completed frame calls original driver.show_image with a 128×128 LANCZOS image.
Returned image closes after transmission. Original driver initialization,
inversion, offsets and SPI conversion remain untouched. ST7789 modes retain
direct partial writes and no scaler allocation. ST7735 source hash is guarded;
installed and pinned match 59b10c5b7831c67e4da2f8adb89fe6598c201f35d9229471488c8cbaf445639e.

NativeHost discovers optional frame_reset on bound pixel owner and calls it once
after process/reader stop. Hardware zeros its owned accumulator there, on mode
replacement and on hardware close. No claim of zeroing transient Pillow/immutable
copies or cleanup under every fault. Closed Runtime cannot reconfigure/resurrect
a new native owner. 171 host tests pass including cleanup ordering/idempotence
and closed-runtime refusal.

ARM real native/scaler/hardware adapter with fake LCD classes passed ST7789 →
ST7735 → ST7789 → ST7735. Original Settings/Renderer metadata agrees; completed
images are 128×128, previous owners/displays close, old buffer zeroes before drop,
and final retained buffer zeroes automatically on host close. Evidence:
validation/st7735-integration-arm.json. Driver classes only are fixtures; physical
128×128 panel, electrical init/rotation/colors, settings-selection UI in that mode,
optical decoding and actual wipe/fault sequences remain open. No pinned app/image
changed or flashed.

Physical connected 240×240 default startup/menu/back also passed after scaler/owner cleanup integration (validation/st7735-default-startup-arm.json). No physical 128×128 claim.


### Original ST7735 settings-selection round trip

Original Controller/View initialization now passed Hardware settings → Display
configuration → ST7735 128×128 → ST7789 240×240 → Back to settings on ARM, using
actual native host, scaler and LuckfoxHardware adapter with LCD driver classes
replaced by fixtures. Logical widths stay [240,240,240]; physical targets are
[[240,240],[128,128],[240,240]]. Completed scaled frames reach driver.show_image,
old host is reaped before driver change, retained old buffer is zero before
release, and final hardware/scaler state is restored to ST7789/no accumulator.
Original settings View performs selections; no value changes are injected after
initial fixture setup. Evidence: validation/st7735-settings-ui-arm.json.

Original button GPIO is initialized by Controller, inputs remain scripted and no
physical LCD is accessed. Isolated settings persist disabled and no file is
written. This does not qualify ST7735 electrical/rotation/colors, optical QR,
Home display-recovery gestures, or every wipe/failure path. No image flashed.

### Home directional display recovery

The LVGL Home loop now invokes the pinned original MainMenuScreen._run_callback
on a constructor-free instance carrying its input and configured Renderer. This
retains upstream's five-second threshold, direction-to-display map, Settings
mutation, Renderer.initialize_display call and return code 1002; MainMenuView
therefore performs its original Home rerender. No PIL screen constructor runs.
The existing Home battery poll remains active. During the native screensaver,
the callback receives no direction, resetting its hold timer. Render-only tests
without a configured Renderer skip recovery instead of initializing hardware.

Host tests execute the pinned callback with a controlled clock: threshold,
same-configuration suppression, release reset, saver reset, and wide/small/square
switches pass. This is software evidence; actual five-second physical gestures,
wake timing and alternate LCD hardware remain unqualified.

After integration, all 174 host tests pass. ARM power-presentation regression
also passes (validation/home-recovery-key-regression-arm.json): KEY3 tap/hold,
screensaver wake consumption and grid navigation. That render-only fixture has
no configured Renderer and intentionally does not exercise directional display
switches. No system reboot, installed-launcher change or flash was performed.

The subsequent home-display-recovery ARM case exercises the actual original
Controller/MainMenuView and pinned callback with configured LVGL Renderer.
Scripted Right/Down/Up holds each last at least five seconds and return 1002;
original Controller rerenders Home at physical targets 240x240 → 320x240 →
128x128 → 240x240, logical widths 240 → 320 → 240 → 240. The fourth Home renders
before the test ends. Actual native processes and LuckfoxHardware/scaler are
used; only LCD drivers are fixtures. Each old native process is reaped before
driver change and the old scaler buffer is zeroed. Workers and owners clean up,
isolated settings remain unpersisted. Evidence:
validation/home-display-recovery-arm.json. This closes software integration of
directional recovery; physical button gestures, wake timing and alternate LCD
electrical/optical behavior remain outside this test's scope.

Display acquisition now publishes the new LCD/scaler only after both driver
initialization and the optional ST7735 accumulator allocation succeed. A failed
allocation closes the new driver, leaves lcd/scaler unset and permits normal
cleanup, rather than retaining an initialized LCD without its required scaler.
The old display is already closed, so this is failure cleanup, not rollback.
An injected MemoryError host test verifies close order and cleared state; all
175 host tests pass. This change is local only while interactive board testing
runs, and still needs ARM regression before it is deployed.

### LVGL dependency policy

The isolated entry installs dependency_policy before original startup imports.
An exact-path/hash-guarded loader omits only decode_qr.py's two legacy optional
backend import blocks (pyzbar/zbar and OpenCV/NumPy). It retains all original
decoder classes and payload parsing code, then routes scanner availability to
the configured native executable and compatibility extract_qr_data to the
existing RustTransportQrReader. That compatibility client is lazy, returns
unaltered binary bytes and closes its worker after each extraction; the primary
LVGL live scanner continues using its existing managed Rust camera/QR path.
No wallet formats, cryptography, entropy sampling or add_data logic changes.

The same guarded policy moves helpers/qr.py's image-rendering imports into the
three original image methods that use them. Constructing an encoder/QR helper
therefore avoids importing qrcode's styled-Pillow renderer. Bitmap method bodies
remain unchanged after those inserted imports, and legacy rendering works when
explicitly called. This is process-lifetime import policy; removing the finder
does not hot-reload already imported modules. Installed application files and
packages are untouched.

Host tests confirm decoder class AST preservation, no rendering imports during
QR helper construction, binary compatibility output/worker cleanup, and source
shape rejection. Nine real qrcode 8.2/Pillow 11.3.0 rendering comparisons across
three styles and three public payloads match dimensions/mode/pixels exactly.
The initial 178 host tests pass. ARM dependency-closure now passes fresh imports
and three real ZXing round trips, including every byte value. The complete
public multisig Controller flow also passes under the policy, verifying the
signature, export bytes and cleanup. Evidence: dependency-closure-arm.json and
dependency-wallet-flow-arm.json. Matched resource pairs pass, without proving
an overall memory saving. Current unit suite is 182 passes under Python 3.12.

This removes these backends from the LVGL import path, not the installed OS.
Some optional libraries may already be absent, so their removal need not save
RAM. qrcode remains required for transcription matrices; Pillow remains required
for original camera/entropy image contracts, ST7735 scaling and legacy module
imports. No memory-saving or final image dependency-closure claim is made yet.

Fresh host-process integration also loads the real original QR helper through
the guarded finder without importing qrcode or Pillow. The real DecodeQR module
loads without legacy backends and preserves Unicode, spaces and line breaks in
three public text payloads through unchanged add_data/get_text methods. This
used embit 0.8.0, shamir-mnemonic 0.3.0 and the app's pinned urtypes commit.
The user authorized further diagnostics; the prepared wallet and corrected
resource harnesses subsequently passed on ARM as described above.

### Status fidelity and local native regression

Argument review found LargeIconStatusScreen was mapped to the native success
variant, ignoring caller icon/color overrides. It also passed an empty button
list when original __post_init__ would supply OK. The adapter now selects the
custom variant, supplies the original OK fallback for empty status lists, and
transmits status_icon_size=0 as hidden-icon configuration. The native patch
honors caller icon/color across status variants while retaining warning-border
defaults; hidden icons reserve no flex space or icon-to-body gap. Arbitrary
positive icon sizes remain profile-sized.

Host pixels/input confirm custom magenta icons for generic status and warnings,
zero icon pixels when hidden, and selecting the default action in all four
combinations. Unit suite: 179 passes. ARM native build passes but is undeployed.

New mise tasks lvgl:app:build:host and lvgl:app:test:host exercise the renderer
locally without device access. Host linking omits ARM-only static/strip/GC flags;
ARM retains them. All eight public protocol cases pass: status, frame ordering,
viewport geometry, preview, live labels, transcription rejection/recovery, I/O
and Home battery ownership. The runner verifies native input/hash provenance
and records script/Python hashes. Evidence: validation/native-protocol-host.json.
These checks enable progress while a user tests the board; they do not replace
ARM/physical validation.

The local corpus runner additionally renders all 43 pinned upstream screen
fixtures and passes button-index navigation (validation/native-corpus-host.json).
This is rendering smoke coverage, not complete View/locale coverage.

### Camera-derived encryption IV adapter

SeedEncryptedQRnonECBModeView still imported the stock camera despite LVGL's
managed camera pipeline. The existing entropy_fallback lazy hook now also
recognizes that exact original class in hash-guarded seed_views.py. It changes
only its Camera import to the same private guarded Rust camera facade used by
the final-image fallback. Original preview/cancel routes, full-frame reads,
one-second startup delay, ten-read retry limit, finally-stop, review crop,
SHA256(entropy_image.tobytes()) and KEF IV-length lookup remain original code.
No hashing, IV selection, entropy or cipher implementation is replaced.

Host parity executes original and adapted methods across CBC/CTR/GCM/CBC-v1,
each with accept, menu Cancel/Back, preview Back, review Back, empty capture,
start failure and read failure: 32 scenario pairs match. Acceptance independently
checks the exact SHA256 prefix using the pinned KEF table; failed captures stop
once and preserve the ten-read limit. Lazy installation, source rejection and
restoration are tested for both target View classes. All 182 host tests pass.
These initial host checks were followed by the ARM checks below; no boot image
or flash qualification is implied.

Prepared controller-camera-iv hardware cases now cover CBC/CTR/GCM acceptance
and preview/review cancellation. They use original Controller/View initialization,
physical camera/LCD, scoped input/hash observers and public seed/key fixtures.
No images, IV bytes or keys are recorded. CBC capture and both preview/review
cancellation cases now pass on ARM. The initial diagnostic missed direct
Screen.display calls; observing Runtime.run fixed its carry-over held input.

Runtime staging is implemented independently from OS/image activation. The
stager verifies current native inputs and static ARM ELF, copies production
adapters/guards/pins/notices and creates a foreground launcher with separate
settings. Diagnostic-only helpers are excluded. Every file/mode/checksum is
verified; unexpected/missing files and changed content are rejected. The
63-file, 1,759,380-byte stage is deterministic across two outputs and corruption
rejection passed (validation/runtime-stage-host.json). Release/license readiness
remain false; original app/camera dependencies, font notice closure, version.json
and service/image integration remain outstanding. No files were installed.

### Preview ingestion and SPI transaction cost

The native loop slept 5 ms after every 4 KiB stdin read, imposing approximately
32 sleeps on a 129,600-byte preview. It now sleeps only after a non-ready read;
LVGL timers still run on every loop iteration and idle cadence is unchanged.
Public headless round-trip median changes from 195.3 ms to 6.5 ms. This is an IPC
measurement, not a camera speedup factor. All nine host protocol/corpus cases
and 182 Python 3.12 tests pass. Evidence: preview-ingest-host-comparison.json.

The pixel adapter additionally batches each axis's four window-parameter bytes
into one SPI transfer, with unchanged command/parameter/pixel bytes and full
16-bit coordinates. GPIO initialization/inversion and pixel chunking remain the
original driver policy. Unit wire-sequence tests and the real native 320-column
fake-SPI pipeline pass. Physical preview medians measure 136.9 ms before and
131.5 ms after batching (single runs, not an isolated universal speedup claim).
Evidence: display-batched-spi-pipeline-arm.json and
preview-throughput-batched-spi-arm.json. The initial timing probe omitted the
application import path and failed before device acquisition; the path was fixed.

Instrumented Controller camera runs progress from 28 cycles before the ingestion
fix to 45 / 3.39 completion fps after it, then 49 / 3.78 fps with coordinate
batching. Stage counters locate most residual waiting in preview acknowledgement.
The /proc sampler adds substantial overhead, so these are workload observations,
not production FPS. The unsampled tools-loaded camera case subsequently passes
startup cancellation and two 30-second scans/reopens at 4.847 and 4.846 completion
fps, with owner exit 0 and zero DMA buffers after each cycle. It uses scripted
buttons and suppresses incidental QR completion; it does not qualify an optical
test vector or original Controller lifecycle. Evidence:
camera-fast-preview-soak-arm.json. This is a bounded 60-second run, not long soak.

The two matched resource pairs remain in frontend-camera-comparison.json and
frontend-camera-fast-input-comparison.json, with original/PIL and LVGL raw
receipts. They do not establish a total-memory win; source/bundle matching is
enforced separately for each pair and later code changes are not pooled into it.

### Complete camera-encrypted QR flow and matrix-only dimensions

Original Controller/View camera capture → review → mnemonic-ID selection →
original encryption → displayed QR → SeedOptions route passes for CBC, CTR and
GCM. The displayed pixels decode through native ZXing to the exact encoder bytes.
Original decrypt Views reject a wrong key and recover the exact public mnemonic
with the correct key; pending storage is cleared afterward. CBC uses the original
16-byte image-hash prefix, CTR/GCM the original 12-byte prefix. Both cancellation
stages also pass, releasing owners/DMA. Decryption is tested through original
Views after the Controller export run, not an optical camera rescan. Legacy
CBC-v1 is not covered by these three modern-mode checks. Evidence:
controller-camera-encrypted-{cbc,ctr,gcm}-arm.json and
controller-camera-iv-cancel-{preview,review}-arm.json.

This route still called QR.qrsize, which needlessly constructed a styled bitmap.
The guarded helper transform now keeps original QR construction/data insertion,
calls make(fit=True) and returns modules_count, preserving dimension decisions
without creating an image. Six dimension cases match original bitmap dimensions
under target qrcode 7.3.1, including empty/numeric/Unicode/binary/large payloads.
All three ARM round trips confirm no legacy decoder or styled-renderer imports.
All 183 Python 3.12 tests pass. The isolated original-main entry regression also
passes (app-entry-current-arm.json). No installed app files or image changed.

### Pinned locale asset build: runtime work remains

The upstream screens CI pins language-packs commit a9e39dabf60e093bb3d1494eb4728f83342c878b;
it is now recorded in sources.lock.json. locale-builder.lock.json pins the GHCR
builder by digest/platform and original translation gitlink
708961a4163b1bd43eb15c4a26713649c63f6ccd. The builder uses that original .po set,
not the pack producer's different translation fork. Original gettext ownership
is retained; output catalogs do not replace application catalogs.

build_locales.py runs offline in the pinned container after image acquisition,
with read-only sources and separate cached CMake/tool output keyed by input pins.
It selects the nine font locales present in the original 22-locale catalog set,
indexes required manifest/fonts/runs/endonym_240 assets, verifies upstream hashes
and rejects missing/oversized/changed files. Debug runs.json and other image
heights are not runtime inputs. Two builds produce identical file hashes;
cache reuse and corrupted-font rejection pass. Runtime input total: 32 files,
705,899 bytes (validation/locale-assets-host.json).

Native locale loading/picker integration is still absent. The upstream builder
also reports one unshapeable Hindi and three Thai templates; do not claim those
render correctly merely because packs build. The new source pin invalidates the
current native input manifest, so rebuild before further hardware deployment.

### Locale runtime provider and original settings adapter

The native host now exposes a private locale command using upstream
ss_register_pack_manifest/ss_load_locale and the shared picker image provider.
Each asset read is capped at 512 KiB, opens directory/file components without
following symlinks and rejects traversal; the transient read buffer is released
after font loading or screen building. The upstream loader retains font ownership
and retires previous fonts until the old screen is deleted. No new shaping engine
or translation implementation is introduced.

Optional app --locale-root enables indexed size/SHA-256 preflight with chunked
hash reads. Runtime synchronizes LANGUAGE on locale/host changes, including host
replacement after display recovery. Original gettext/catalogs and Settings still
own translation and persistence. The language settings screen uses upstream's
native locale picker only after checking the original button order; non-Latin
endonyms use pre-rendered 240-height images instead of retaining nine font sets.
This remains opt-in pending Controller/physical visual acceptance and packaging.

Desktop checks load/swap all 22 catalog locales, render nine image rows, reject
traversal and clear the screen. All nine existing native regression cases and
183 Python tests pass after this change. This does not resolve the four upstream
Hindi/Thai shaping-template gaps or establish translated-screen visual parity.

The ARM provider/picker probe passed with physical LCD output and clean owner
exit (validation/locale-native-arm.json). The original Controller and original
LocaleSelectionView also pass Japanese → Persian → English, displaying original
translated settings between selections, preserving the original View initializer
and separate test settings (validation/controller-locale-arm.json). The adapter
matches both the raw and original-gettext-translated Language heading because
LocaleSelectionView translates its display_name before passing screen arguments.
These tests use scripted input and do not establish visual translation parity.

The repeated ARM locale probe samples native /proc/PID/status immediately after
each public fixture screen. Native RSS ranges 1,500–1,848 KiB, with one thread
and zero swap throughout; returning to English yields 1,564 KiB RSS. Hindi is
the highest sampled case. These are point samples for this small public fixture,
not peak allocation, whole-app memory, an isolated language delta, or a leak/soak
qualification. The receipt retains all per-language samples. All 188 Python tests
pass, including locale asset corruption/symlink rejection and host-replacement
resynchronization tests.

### Closed-set shaping supplement and locale-enabled inactive payload

The four unsupported templates have finite original value domains, so an
isolated offline supplement expands their complete formatted text before the
upstream font/run compiler: Hindi final-word (12,7)/(24,3); Thai transaction
verification warnings × change/self-transfer; Thai change label × btc/sats.
See original tools_screens.py:468, psbt_views.py:1355/1358 and
psbt_screens.py:608, plus the existing guarded final-word/PSBT contracts. Eight
whole-string variants retain the original translated characters and line breaks.
No runtime formatting, gettext catalog or wallet semantics change. The producer's
normal whole-string HarfBuzz shaping, subset glyph IDs and binary run format are
reused, avoiding a new dynamic shaper or relaxed shape-safety rules.

locale_supplement.py is mounted read-only into the pinned offline builder and
its SHA is included in asset provenance. Missing expected templates or remaining
placeholders fail closed. All eight generated variants have plain runs with no
missing-glyph IDs. All 21 compiled catalogs compare byte-for-byte equal with the
unsupplemented build. Two asset builds produce identical indexed files; unsupported
template count is now zero. The native probe renders all eight variants with the
physical LCD and clean exit. Evidence: validation/locale-supplement-host.json and
locale-supplement-arm.json. This is not a full translated-screen visual review.

package.py --locale-root DIRECTORY copies only the 32 indexed runtime assets and
index, enables --locale-root in its foreground launcher, and verifies the copied
assets. Two inactive stages match exactly (97 files, 2,532,613 payload bytes at
this checkpoint). Debug JSON, supplemental test fixtures and extra endonym heights
are excluded. The launcher passes shell syntax validation. No service, installed
application, bootable image or microSD changed. License closure, full-flow gates
and image integration remain unfinished. All 192 Python tests pass.

### Partial mnemonic pages (BIP-85 and SLIP-39)

Review of the original SeedWordsView found num_pages=int(len(mnemonic)/4).
That omits words 17–18 for an 18-word mnemonic and word 33 for a 33-word share.
Both original SeedWordsScreen and upstream native seed_words_screen also default
to page_index*len(current_page)+1, which misnumbers a final partial page.

The isolated word_pagination.py hook source-verifies the pinned seed_views.py,
replaces only that single page-count expression with ceiling division, and
restores the original method on uninstall. Original word slicing, navigation,
quiz, seed derivation, storage and entropy logic remain intact. The screen
adapter supplies start_number=page_index*4+1 to the upstream builder. The source
hash and exact AST expression are checked before replacing the method. This is
an intentional display correctness divergence from the pinned original app.

Host checks verify every word appears once and numbering remains continuous for
12,18,20,24,33-word sets; changed source shapes fail closed. All 194 Python tests
pass. Full original-Controller BIP85 checks now pass for all three 12/18/24-word
branches: existing parent → number-of-words selection → native index-0 entry →
review every word → original randomized backup quiz → pending child → finalize →
stored child options. All quiz answers are checked by original Views, without RNG
or answer-check replacements. The derived mnemonic matches a separate HMAC-SHA512
expansion of the hardened BIP85 path, and stored child seed bytes match PBKDF2.
Parent words remain unchanged; original settings are not written; owners exit
cleanly. Evidence: validation/controller-bip85-{12,18,24}-arm.json.

These tests cover public index 0 and scripted keys on the physical LCD, not
physical-button qualification, every index/error route, or the SLIP39 full flow.
The installed source file is never changed. The current inactive payload is
now dist/lvgl-app/runtime-bip85-current (98 files, 2,535,011 bytes), verified with
locale assets and the pagination hook. It remains releaseReady=false; no OS image
or flashing occurred. COVERAGE.md now links these exact scoped receipts rather
than treating every screen as entirely flow-unverified.

### SLIP39 recovery and inherited wipe contract

The first full 33-word fixture scanned two public 2-of-2 shares through synthetic
NV12, real native ZXing and original ScanSlip39ShareQRView. It recovered the exact
32-byte test secret, finalized storage, reviewed all 33 words of each share and
completed both original randomized quizzes. Final cleanup then failed: the pinned
Slip39Seed constructor never initializes _mnemonic/_passphrase, but its wipe()
delegates to Seed.wipe(), which reads both. The runner correctly rejected the
run despite its then-premature success print; the original failure receipt is
validation/controller-slip39-33-initial-wipe-failure-arm.json.

slip39_lifecycle.py now lazily source-verifies models/seed.py and wraps only the
original Slip39Seed initializer to establish those two empty inherited fields.
The original constructor, shares, normalization, combine/derive, passphrase and
wipe methods remain untouched. Class identity and lazy module loading are retained;
uninstall restores the constructor. This is a lifecycle bug correction specific
to the pinned model, not a replacement secret-clearing algorithm. The source on
the installed image is unchanged.

The test now emits success only after its finally cleanup succeeds, calls the
original wipe twice and checks the original sensitive fields are cleared. All
196 host tests pass, including initialization-failure safety and parent wipe
compatibility. Full 33-word hardware rerun passed. A public dummy-word
render also confirms last-page label 9/9 and word number 33 fit correctly; no
wallet frame was captured (dist/lvgl-app/public-word-33.png).


Both original-Controller recovery branches now pass: 20-word shares recover the
exact 16-byte public secret, and 33-word shares recover the exact 32-byte secret.
Each scans two 2-of-2 shares through synthetic NV12 → real Rust ZXing → original
ScanSlip39ShareQRView/storage/combine → finalization. Both shares are then fully
reviewed and quizzed (40/66 original randomized answers). The 20-word check also
uses original Discard seed → confirmation → Home and verifies empty storage and
cleared model fields. Both tests successfully call the original wipe twice and
exit without remaining owners. Evidence: validation/controller-slip39-{20,33}-arm.json.
These are scripted-key, physical-LCD checks; optical inputs, multi-group policies,
manual entry, generation/regeneration and passphrase branches remain separate
acceptance work. The ordinary mnemonic/SLIP39 wordlist and crypto are unchanged.

### Added runtime notices and reproducible metadata audit

The initial stager retained LVGL library notices and the original app MIT notice,
but omitted native C++/libc and embedded font notices. It now retains nlohmann
JSON 3.11.3 MIT (with its bundled header's additional SPDX copyright recorded),
Apache-2.0, pinned LVGL Montserrat/FontAwesome notices and Zig 0.15.2's MIT, musl,
libc++, libc++abi and libunwind terms. Names/copyright/license records and SHA256
for 27 original font files are retained as context, not a claim that all 27 faces
are embedded in the native host. The original app Open Sans metadata declares
Apache-2.0; newer locale-pack Open Sans declares OFL-1.1. No blanket font license
is inferred. Complete OFL terms accompany the separate per-font copyrights.

font_metadata.py runs in the pinned font-builder Docker image, offline and with
read-only input mounts. audit_licenses.py reproduces the metadata, checks copied
compiler notices against the actual pinned Zig installation, and snapshots all
retained notice hashes/source pins. mise run lvgl:app:notices updates the audit.
The stager rejects stale notice snapshots; its verifier checks inner notice
consistency in addition to whole-file manifest integrity. Two inactive stages
match exactly (111 files, 2,647,350 bytes). Deliberately corrupting a notice and
updating its outer manifest hash still fails the inner notice check. Evidence:
validation/notice-audit-host.json and notice-stage-host.json.

licenseClosureVerified stays false. The pinned screen-core tree has no top-level
license grant, and the GitHub repository license endpoint returned 404; custom
seedsigner-icons.otf also lacks embedded copyright/license records. This audit
does not invent grants for either, or qualify the original OS/Python/camera
runtime's full dependency notice closure. Development/testing can continue while
those specific provenance/terms are established. No app executable, installed
service, bootable image or microSD changed. Current inactive payload:
dist/lvgl-app/runtime-notices-current. Runtime acceptance gates remain open.

### Legacy encrypted QR compatibility and ADB argument boundaries

The first legacy CBC diagnostic failed before execution because adb shell flattened
AES-CBC v1 into two arguments. hardware_check.py now sends one shlex-quoted remote
command, preserving spaced/literal arguments; the regression models ADB's join
followed by remote-shell parsing. No encryption/runtime policy changed.

A legacy mode label alone also proved insufficient evidence: original KEF version
selection excludes unsafe padding for zero-ending entropy, so the old all-abandon
public fixture can select a newer padded format. Legacy tests now use a public
non-zero-ending entropy fixture and assert the unwrapped exported version after
native QR pixel decoding. CBC-v1 confirms actual format 1, using physical camera
capture/review and the original full-image SHA256-derived 16-byte IV. ECB-v1
confirms actual format 0 through its original no-camera/None-IV route. Both pass
QR export, exact native pixel decoding, wrong-key rejection and exact original
mnemonic recovery; streams/DMA/worker cleanup pass. These are explicitly selected
legacy diagnostic modes, not newly exposed settings/UI choices. Evidence:
validation/controller-camera-encrypted-cbc-v1-arm.json and
validation/controller-encrypted-ecb-v1-arm.json.

Export/IV steps run through the original Controller and Views on the physical
LCD with scripted keys. Decryption is the original decrypt Views after export,
not an optical rescan or a separate full Controller import run. Nothing changes
KEF, KDF iteration bounds, AES/authentication, entropy acquisition or seed storage.
The modern ECB Controller run also passes, confirming naturally selected padded
version 6 and Base43 text export in the same fixture
(validation/controller-encrypted-ecb-arm.json). All 201 Python tests pass. Legacy ECB observes no image hashes; CBC hashes add diagnostic
overhead. The original IV/CBC/CTR/GCM evidence remains scoped to its recorded build.

### Large-grid selected-color field

LargeButtonScreen.button_selected_color was previously discarded by contracts.py.
The adapter now forwards it for large grids and MainMenuScreen. A shared private
native helper parses it before constructing widgets and retains per-widget
color state, removed on LV_EVENT_DELETE. The patch reuses upstream grid geometry
and navigation; it adds the color to upstream button_set_active's manually painted
selection path and the focused/focus-key/pressed styles. Default #FF9F0A matches
both pinned Python and native constants; other button types keep their original
accent fallback. No action routing, layout or wallet behavior changes.

The initial style-only implementation failed the public pixel test because the
upstream navigation repaint overwrote it. The final helper participates in that
actual repaint path. Nine desktop pixel cases pass: 2/4-button generic grids and
four-button Home × default/cyan/purple; Right then Select remains index 1. Invalid
color is rejected before allocating a screen. All nine existing native regression
cases and all 202 Python tests pass. Physical-LCD pixel/navigation check also passed all nine cases using original
screen classes and ButtonOption data, with clean owner exit
(validation/grid-color-arm.json).
This does not finish arbitrary custom font/style parity.

### Current resource pairs, both run orders (English scope; no smartcard work)

Repeated the fixed Home → live camera → cancel → Home measurement as LVGL/PIL
then PIL/LVGL. All four runs have identical deployed Python/test bundle, native
binary and build manifest; receipt hash/owner/source-mutation checks pass. The
original settings file is untouched. Both pairs are retained in
validation/frontend-camera-current-order-{a,b}.json, with the combined report in
frontend-camera-current-reversed-orders.json and four original ARM receipts.

LVGL scanning Python RSS medians range 16.0–16.8 MiB, swap 4.5–4.8 MiB; UI RSS
1.4–1.7 MiB. PIL Python is 17.2–17.5 MiB RSS and 6.3 MiB swap. LVGL camera-owner
RSS is 7.4–7.6 MiB versus PIL 5.3–5.4 MiB plus 1.8–1.9 MiB camera-owner swap.
QR RSS is about 0.8 MiB in both. System MemAvailable is 7.8–8.8 MiB with LVGL,
9.0–9.1 MiB with PIL. These are process/window medians and separate swap figures,
not additive totals or an isolated attribution of the difference. No overall
memory win is established. Both orders agree on that practical conclusion while
the free-memory difference varies with run order/system pressure.

Home LVGL Python RSS is 22.0–23.5 MiB plus native UI 1.6 MiB. Scanning thread
counts are Python 8, native UI 1, camera 5, QR 1. Live DMA is 3.8 MiB in both
frontends and returns to zero; pipeline owners exit on cancellation. The runs
include benchmark sampling/script overhead and do not qualify production CPU,
cold-start, optical decoding, or a longer lifecycle soak. No runtime optimization
or app/OS installation was made during this measurement step.

### Inactive image selector, original memory policy and truthful identity

Prepared an offline image overlay only. It contains the English-only runtime
without locale assets, a selector at usr/bin/shieldsigner-launch, the exact saved
PIL launcher and opt/src/seedsigner/version.json. No S99/start supervisor rewrite
is needed: the same supervisor owns whichever frontend the selector execs.
Default routing is PIL for this unqualified draft. A userdata rollback marker
wins over default/environment LVGL selection. Failure returns to the existing
supervisor rather than spawning a second frontend and masking a crash.

Read-only inspection of the working image found setup the old generic runtime
launcher lacked: ulimit -l 4096, zram enablement, small-RAM policy and camera code
locking. service/base-launcher-pil.sh retains that reviewed 917-byte launcher,
with a SHA lock. The selector's LVGL branch reuses the exact pre-exec setup; PIL
runs its original copy and performs its own setup. No device service was changed.

image_stage.py prepares/verifies immutable draft files, native/runtime provenance,
rollback bytes/modes and shell syntax. The original version-file readers accept
the generated development name, actual base commit with dirty flag, and explicit
SOURCE_DATE_EPOCH timestamp. The tested epoch is the base commit timestamp;
wall-clock build time is not inferred. The full runtime snapshot hash distinguishes
uncommitted frontend content. It does not claim a release version or qualified OS.

Host stub tests cover default/explicit selection, memory setup order, spaced/literal
arguments, persistent rollback priority, invalid selection and failing LVGL exit
status. Two drafts match exactly; altered rollback bytes fail verification. All
208 Python tests pass. Evidence: validation/image-overlay-draft-host.json. Draft
payload: 81 files / 1,924,302 bytes, not the size of a bootable Linux image. Latest
runtime is dist/lvgl-app/runtime-english-current; draft is image-overlay-draft-b.
No target rootfs, installed app, microSD or OS image was written. Target boot,
service/lifecycle qualification and actual builder hook-up remain unfinished.

### Current original-main TERM and extended camera reopen qualification

The current app-entry-sigterm-camera case passes with physical LCD and real camera,
waiting for active capture (three frames observed) before SIGTERM. Original-main
execution unwinds through the existing termination handler; camera owner exits
zero, native/worker processes stop and original settings remain untouched. Exact
receipt: validation/app-entry-sigterm-camera-current-arm.json. This tests the
foreground app entry, not an installed init service or cold boot.

camera-long-soak extends the prior 30-second repeats to startup cancellation plus
three 90-second live sessions, with Tools imported and the production dependency/
small-RAM policy installed before original decoder imports. It records post-close
process metadata, checks repeated live-session thread counts and rejects legacy
QR backend/styled-bitmap imports. Incidental QR completion is suppressed solely
to keep duration fixed; payloads and images are never logged/saved.

All sessions pass: 432/440/443 processed previews at 4.898/4.916/4.937 completions
per second. After each close, DMA is zero and camera owner exits zero. Post-close
Python thread count remains 2 in this direct fixture. Anonymous RSS plus swap is
19,788 KiB after each full session; RSS alone falls 12,536 → 11,708 → 10,080 KiB
while swap rises 10,372 → 11,736 → 11,892 KiB. The stable combined private-page
observation is more informative than calling falling RSS a memory improvement.
It does not prove whole-app/unbounded leak freedom, optical decode correctness,
normal physical-button behavior or cold graph startup. Evidence:
validation/camera-long-soak-arm.json and camera-long-soak-summary.json.

No production runtime code changed in this iteration; the English runtime/image
drafts remain as previously staged. All 208 host tests pass. Original app/service,
OS image and microSD remain unchanged. English-only/no-smartcard scope persists.

### Guarded staged-rootfs application and optional SDK hook

overlay_apply.py is a standalone stdlib-only helper inside the immutable draft.
Preflight rejects live roots, unexpected camera startup receipt/launcher, mismatched
44-file app source guards and unsafe destinations before any copy. Copied files
use temporary siblings and atomic replacement. A failed copy invalidates the
disposable rootfs; it must not proceed to packing. A copied overlay is verified
against its plan, file modes and saved rollback launcher. Mac /var temporary-path
aliases exposed a root normalization bug; canonical-root handling and an explicit
alias regression now cover it while destination symlink escapes remain rejected.

As with the existing LCD/zram profiles, the helper first validates the current
camera startup hashes/modes, then extends that receipt with the new layer and
records its previous receipt hash. Current camera frontend/startup verifiers and
memory-policy lines still pass in the disposable rootfs fixture. No acceptance
rules are weakened. Default frontend stays PIL for this unqualified draft.

configure-os-camera.py adds optional application/verification when a combined
camera bundle contains lvgl-overlay/overlay-apply.py. Installation follows the
camera/LCD/zram profiles and precedes rootfs hardening/packing. Existing old hook
layouts are accepted for clean restoration. verify-os-image.py separately verifies
the LVGL layer in unpacked rootfs. attach_image_bundle.py adds the verified draft
to a frozen compatible camera/LCD/zram bundle, preserving existing payload hashes;
it refuses probe-only/wrong profiles or an already-layered bundle. No OS build is
started by these preparation tools.

Pinned OS hook generation/shell syntax and legacy layout recognition pass. The
real 81-file English draft applies to a disposable rootfs with pinned source files,
retains the supervisor/rollback bytes and composes with frozen camera frontend/
startup verifiers. All 215 host tests pass. Evidence: validation/overlay-apply-host.json,
lvgl-sdk-hooks-host.json and camera-base-bundle-device-match.json. The frozen
camera/QR executable hashes match the board exactly; LCD binding source inputs
match its receipt, without claiming rebuilt binary identity. Combined bundle:
dist/os/image-bundles/lvgl-english-draft-current. Draft:
dist/lvgl-app/image-overlay-sdk-current. Full SDK compile/packing and actual boot
remain unqualified. No installed app/service, OS image or microSD was changed.


## NUL compatibility checkpoint

`native/nul_text.h` and `patches/passphrase-nul.patch` preserve complete NUL-bearing
input outside LVGL C-string widgets. The visible representation escapes NUL and
backslash; edits operate on raw UTF-8 codepoints, never parse the display string.
Ordinary inputs retain upstream widget behavior. Passphrase and encrypted-key/ID
contracts mark this display mode and escape review text without changing the
value returned to original business logic. No KDF or crypto implementation changes.

All 215 host unit tests pass. Physical LCD entry tests cover exact Save/Back,
NUL/Unicode deletion, insertion, and left/right movement (`validation/nul-entry-arm.json`).
Original passphrase add/review/finalize and fingerprint fixtures pass with NUL
(`validation/nul-passphrase-flow-arm.json`); View initialization is injected, so
this is not full Controller qualification or an optical test. Current raw buffers
are overwritten on widget deletion; this does not guarantee erasure of allocator
history or intermediate copies. Encrypted entry contracts have host coverage,
not a new end-to-end encrypted NUL-payload hardware qualification.

The full public-fixture Controller scan/import, transaction review, multisig
descriptor verification, signing and QR-export regression also passes after this
change (`validation/dependency-wallet-flow-nul-current-arm.json`). It validates
the existing transaction fixtures, not every NUL-bearing encrypted QR path.
The refreshed English-only inactive runtime and SDK camera bundle verify locally;
no bootable image was built and no installed app or SD card was changed.

## Full Controller passphrase checkpoint

The public fixture in `tests/controller_passphrase.py` begins with empty storage,
imports a compact SeedQR, chooses Scan Passphrase, reviews the resulting text,
opens the original edit View, saves, reviews/finalizes and returns Home. It retains
original View initialization and verifies seed bytes against independent hashlib
PBKDF2 with BIP39 NFKD inputs. NUL, literal backslash-zero, whitespace and Unicode
are included. Display text follows original NFC while storage follows NFKD.
The initial fixture incorrectly expected NFKD in the edit-screen arguments and
failed; its receipt is retained. The corrected fixture passes on the physical LCD
(`validation/controller-passphrase-arm.json`). Camera frames and buttons are
synthetic; the receiver, ZXing, DecodeQR, Views and Controller are original.
No entropy, crypto, wallet model or installed app code was changed.

## Scoped physical SPI response measurement

`tests/input_latency.py` measures IPC key dispatch to first completed SPI frame
for 24 alternating Home navigation inputs and 24 button-list inputs. It calls the
normal hardware completion callback before recording the timestamp and requires
every input to yield a frame within three seconds. Home median/p95/max were
37.3/114.4/116.8 ms; list 7.4/97.6/122.2 ms. No pixels are saved. GPIO polling,
optical response, Controller/model work and camera load are outside this scope.
Receipt: `validation/input-latency-arm.json`. The initial runner lacked `/opt/src`
in its diagnostic sys.path and failed before acquiring the LCD; the corrected
diagnostic uses the same source paths as other hardware fixtures. Production
code was unchanged.

## Full Controller singlesig address checkpoint

`tests/controller_address.py` starts with empty storage, imports a compact SeedQR,
finalizes and returns Home, scans a native-segwit address, selects the imported
seed, runs the original search worker/screen and success screen, then returns
Home retaining the exact BIP39 seed. Physical LCD cases pass for receive index 7
and change index 7 (`validation/controller-address-{receive,change}-arm.json`).
Addresses are constructed directly with embit HD derivation and P2WPKH rather
than the app address helper. Controller and View initialization are original;
NV12 source frames and buttons are synthetic, so optical capture is not qualified.
Other script types, expanded search, mismatched-address and cancellation branches
are not established by these two receipts. The initial fixture expected the generic
ButtonListScreen where upstream uses SeedSelectSeedScreen; only the diagnostic
expectation was corrected. Production app and installed image are unchanged.

## Full Controller static wallet export checkpoint

`tests/controller_wallet_export.py` imports a seed from empty storage, selects
Export xpub, accepts the original privacy warning, checks the displayed fingerprint,
account-zero path and native-segwit zpub against direct embit derivation, then
decodes physical-output QR pixels with the existing Rust ZXing worker. The bytes
must exactly equal the independently constructed origin/xpub string. It then
scans the matching receive address and requires the original address worker to
verify index 7 before Wallet Export success and Home. Original View initialization
and Controller navigation are preserved. Settings deliberately select single sig,
native segwit, static QR and no account prompt; this does not qualify other export
formats/accounts. Camera input and buttons are synthetic; LCD output is physical.
No pixels or payloads are saved. Receipt: `validation/controller-wallet-export-arm.json`.
The documented Proxmox container is reachable/running and has no current Docker
build; no new OS build was launched during these checks.

## First LVGL-default image build

After the functional/current-flow, resources, lifecycle and input checkpoints,
a fresh English runtime was staged twice with byte-identical manifests. The
LVGL-default image overlay also reproduced byte-identically with fixed source
epoch 1793366723. It retains the reviewed base launcher as `.pil` for explicit
rollback and uses the existing supervisor. Development variant preserves ADB.
The original pinned app remains in the rootfs because wallet/business logic is
retained; LVGL is the selected frontend. The old PIL frontend is available only
through explicit rollback/override, not a competing process or masked fallback.

The build was launched through `mise run os:remote:build` with the immutable
combined bundle. Actual launcher PID and Docker build activity were observed.
No build, packed-image, boot or flash success is inferred from that launch.
Source-date epoch is fixed base-commit metadata, not an asserted wall-clock
completion time. Pre-build hashes are saved in
`validation/image-candidate-01-staging-host.json`.

Packed-image readback now has an optional LVGL userspace-QEMU smoke alongside
the existing Python/AES/QR and Rust LCD/frontend checks. It uses the extracted
ARM Python, source guards, native manifest and renderer, verifies menu selection
and exact NUL-bearing passphrase return, clears the renderer and checks that no
settings file was written. It acquires no devices and cannot qualify boot, GPIO,
SPI or camera. The generated Python scripts parse locally; execution awaits the
packed candidate image. The verifier was transferred separately to the documented
builder and does not change the SDK build already running.

## Memory goal: remove unnecessary eager imports

The user replaced the image-migration goal with memory reduction through removal
of unnecessary code/imports, without rewriting working functionality. The first
cleanup moves shamir_mnemonic and aezeed imports from Seed module scope to their
original consuming methods, and the SLIP39 generator import into its View method.
An additional guarded package initializer exposes the exact original SLIP39
exports on demand. This is needed because unchanged secure_delete deliberately
imports the SLIP39 wordlist to protect shared string IDs. Wordlists and wiping
protection are retained. The installed initializer's code/constant/name/flag
signature must match reviewed shamir-mnemonic 0.3.0; unknown versions fail clearly.

Import-only measurements are overlapping dependency chains, not individual
algorithm sizes: Pillow core adds 1,964 KiB private anonymous RAM, Pillow plus
GUI helpers 2,296 KiB, Seed import chain 4,772 KiB, GUI components 5,668 KiB, and
seed-screen import chain 7,836 KiB. These values must not be summed. No wallets
or devices were created in those fresh-process tests. Home/Settings audits
showed empty font caches and unloaded optional crypto/card/image-decoder stacks.
The first warm before/after Home/Settings pair observed 236/428 KiB less private
anonymous RAM plus swap; this does not isolate run-order/allocator variation.
Evidence: validation/dependency-{import-cost-arm,removal-first-pair}.json.

The optimized SLIP39 20-word recovery, both share reviews/quizzes and discard
passes on hardware: `validation/dependency-slip39-recovery-arm.json`. The initial
run failed because a synthetic compile filename broke inspect.getsource in the
existing partial-word-page adapter; seed Views now retain their original filename
and original AST line positions. The failed receipt is retained separately.

Font cleanup removes the completely unused ImageFont import from keyboard.py
and moves component ImageFont imports into their existing consuming functions.
The get_font return annotation becomes its equivalent forward string to avoid
loading the optional engine during class definition. Algorithms and font metrics
are unchanged, with the original implementation loaded on first use. Two new
source guards cover these exact pinned GUI files. Home/Settings hardware runs
pass; Pillow module counts fall by one, from 17/22 to 16/21. The latest private
anonymous RAM plus swap is 14,688/16,620 KiB versus the original pair's
15,008/16,848 KiB (320/228 KiB difference). Variation against the preceding
SLIP-only run prevents isolating an additional font-import RAM saving. Do not
claim these as additive or guaranteed production savings. Evidence:
`validation/dependency-font-audit-arm.json`.

All 221 host tests and the full Controller scan/import → transaction review →
descriptor verification → sign → QR-export hardware regression pass after
optional/font import cleanup. Receipt:
`validation/dependency-cleanup-wallet-flow-arm.json`. This establishes the
existing public fixtures, not universal feature coverage or an isolated RAM win.

## Pillow/startup dependency cleanup and prepared imports

The import policy now moves Pillow imports into their existing consuming
functions and preserves image type hints as forward references. Two image helper
defaults retain exactly Resampling.NEAREST's integer value zero; all image/math
bodies remain original. It removes only the unused Controller RAQM warning probe,
unused Settings ScanScreen import and imports proven to be used solely in type
annotations (descriptor, PSBT/parser, BaseQrEncoder, EncryptedQRCode). Optional
BIP32/BIP85 imports move into original consuming methods. The screen/lifecycle
import loaders compose with the policy instead of bypassing it. Recompiled entropy
methods rebind their original Pillow imports locally, preserving the original IV
and acquisition algorithms. Camera-encrypted CBC roundtrip passed, including
full-image IV hash agreement, native pixel decoding, wrong-key rejection and
original mnemonic recovery. Real-camera scan cleanup and full transaction flow
also passed at their scoped checkpoints. SLIP39 recovery/quiz/discard passed after
loader composition. Source/receipt hashes identify the exact incremental versions.

The first broad import deferral still loaded Pillow and increased private startup
memory. That regression receipt is retained. Tracing found Controller's local
RAQM probe and Camera's top-level image import. After removing/defering these,
Pillow was absent at Home/Settings, but temporary AST compilation still consumed
heap. Import edits are now compiled during preparation in a separate process.
`import_cache.py` checks Python magic, source and policy hashes, artifact hashes
and the expected compilation filename. Normal runtime bundles include deterministic
Python 3.12 code caches. Missing/stale/other-root caches use the guarded development
fallback; corrupt artifacts fail. Cache paths are separate from original Python
bytecode, so the original app never reads transformed modules accidentally.

Warm observations: private anonymous RAM plus swap fell from 15,008 to 11,436 KiB
at Home and from 16,848 to 11,500 KiB in Settings. These are 3.49/5.22 MiB reductions,
not total-system physical-RAM attribution or guaranteed scanning/signing savings.
Home/Settings have zero loaded PIL/UR/Cryptodome/PGP/card modules. No fonts are
cached in those states. Evidence: `validation/memory-cleanup-summary.json` and
`validation/memory-cleanup-*-arm.json`. All 228 host tests pass. Fresh current
runtime stages have identical manifests. Package payload grows by roughly 0.9 MiB
for precompiled import edits; runtime avoids the AST/compiler scratch heap.
The original working app, wallet data, settings and SD image remain untouched.

## Remove the native scan path's unused Pillow import

`stream_imports.py` verifies the exact installed managed-stream source digest
against the pinned helper before moving its single Pillow import into
`_frame_from_payload`. NativeVideoStream inherits ownership/lifecycle code from
this helper, but bypasses that legacy image conversion. No transport, frame,
owner, preview, QR or entropy algorithm is replaced. Method source line positions
are preserved. Installed camera files remain unchanged. The import edit is
precompiled through the existing cache preparation; the cache fingerprint now
includes this import adapter, and package verification checks its original source
digest and compiled bytes.

A diagnostic-only eager baseline unregisters this import finder before camera
modules load, retaining all other current policies. It and the deferred/prepared
run process 56 previews each and cleanly stop camera/QR/DMA ownership. Their steady
Python private anonymous RAM plus swap medians are 15,346 and 14,898 KiB (448 KiB
lower); Pillow module count is 11 versus zero. These are warm observations, not
isolated allocator attribution or guaranteed total-system savings. The initial
on-demand compilation version saved only about 0.3 MiB; preparing that code
outside the wallet process improved the observed difference to about 0.4 MiB.

All 230 host tests pass, including original RGB and NV12 Y-plane conversion
pixels and rejection of unknown helper revisions. The first test fixture lacked
its width/height attributes; supplying the original constructor contract fixed
that fixture without changing runtime behavior. Full real-camera CBC encryption
roundtrip passes after cleanup, including original full-image IV hash, rendered
QR decode, wrong-key rejection and exact mnemonic recovery. Receipts and hashes:
`validation/stream-import-memory-summary.json`, `stream-import-*-arm.json`.
A fresh verified runtime is staged at `dist/lvgl-app/runtime-memory-stream-01`.
No OS build, flash or installation was performed for this memory change.

## Wallet Views: defer unused backup/card/QR imports

The existing guarded import adapter now relocates the seed Views' BitBox02,
Passport and Tapsigner backup imports, QR encoder imports, and smartcard helper
imports into their original consuming methods. Descriptor is used only as a type
hint and becomes a forward reference. No backup/decryption, signing, wallet
control-flow or entropy implementation is replaced. Original package/function
objects resolve through ordinary Python imports when needed. Helpers and optional
hardware implementations are retained; smartcard hardware was not exercised.

A host AST comparison verifies every original View class body after normalizing
only the injected imports and equivalent type hints. All 231 host tests pass.
The fresh import-only View graph drops from 14,124 to 10,088 KiB private anonymous
RAM plus swap (4,036 KiB / 3.94 MiB lower). Before cleanup it loaded 9 Cryptodome,
11 pysatochip, 34 smartcard, 16 ecdsa and 17 urtypes modules; afterward those
counts are zero in this workload. No seed, key, wallet or hardware is created
by that import diagnostic.

The full Controller public transaction regression passes unchanged input bytes,
original change verification, signature checking, exact exported QR bytes and
cleanup. Its review/signing private-memory observations are roughly 19,036 versus
17,196 KiB (1.80 MiB lower); before/after workloads have other incremental code
changes and allocator/run-order variation, so this is not isolated attribution.
These numbers must not be added to the cold import saving. A wrapper now runs
the original complete wallet-export/address-handshake fixture under the current
policy; it passes, including independent xpub/QR bytes and address index 7.

Evidence: `validation/wallet-optional-import-memory-summary.json` and the
associated before/after/transaction/export receipts. Prepared runtime staging is
`dist/lvgl-app/runtime-memory-wallet-01`. Original installed application, working
image and settings remain unchanged; no OS build or flash was performed.

## QR parser imports become on-demand

The guarded decoder import policy now relocates its urtypes, URDecoder, strict
PSBT framing/parser, and embit imports into the original consuming methods.
No type detection, payload parsing, framing/refusal, QR extraction or signing
algorithm is replaced. The host test removes only injected imports before
comparing every original decoder class AST; class logic remains identical.
All 231 host tests pass.

An ARM direct-data fixture first verifies that construction leaves UR types,
URDecoder and PSBTParser unloaded. Original parsers then pass compact and numeric
12/24-word SeedQR, base64/base43 PSBT, reversed animated UR PSBT with a duplicate
fragment, exact payload reserialization, unreadable bytes yielding None, and
duplicate-key PSBT refusal. The first refusal fixture incorrectly expected
truncated garbage to raise a policy refusal; upstream deliberately treats it as
unreadable. Both original outcomes are now checked; the failed fixture receipt
is retained. Full Controller transaction scan/review/sign/export also passes.

Warm steady-scan private anonymous RAM plus swap observations are 14,898 versus
14,250 KiB (648 KiB / 0.63 MiB lower). The new run processes 58 previews, exits
the owner zero and clears DMA. No production FPS or isolated allocation claim
is made from these diagnostic runs. Native binaries and frame processing are
unchanged. Evidence: `validation/parser-import-memory-summary.json` and
`validation/parser-import-*-arm.json`. Current verified staging is
`dist/lvgl-app/runtime-memory-parser-01`; installed app/image/settings unchanged.


## Tools import cleanup

Tools retains the original view definitions, circular imports and wildcard
reexports. Reviewed image, card and helper backend imports move into their
existing consuming methods. Grouped imports are split so a coin metadata helper
needed by a class definition does not also load unrelated smartcard backends.
Imports required for base classes, class metadata, function defaults or shadowed
names remain at module scope. Optional try/except handlers move intact.
Method adapters retain these imports when recompiling original entropy methods.

The fresh-process Tools import adds 8,628 KiB private anonymous RAM versus
13,596 KiB before this cleanup: 4,968 KiB (4.85 MiB) less. Pillow, Cryptodome,
pysatochip, smartcard and ecdsa remain unloaded; UR types still load through the
original QR encoder base-class dependency. This is an import-only measurement,
not an established saving in every running workflow. See
`validation/tools-import-memory-summary.json`. All 234 host tests pass, including
structural comparisons of original function/class logic across seven modules.
Hardware camera entropy generation passes with the cleanup installed: real RNG
health gate, preview/capture, 12-word seed generation and wipe, camera owner exit
0 and zero remaining DMA buffers. Evidence: `validation/tools-import-entropy-arm.json`.
No image has been built or flashed for this cleanup.


Tools coin-flip hardware validation also passes for 12 and 24 words: keyboard
edit/backspace/cancel, exact original checksum calculation, finalize and discard.
Evidence: `validation/tools-import-coin-arm.json`. The verified runtime bundle is
`dist/lvgl-app/runtime-memory-tools-01` (108 files, 3,718,059 payload bytes,
releaseReady=false, serviceInstalled=false). Prepared import caches add disk
bytes; their size is not a claim of RAM usage. This checkpoint does not complete
the memory goal. A remaining import candidate is the original QR encoder module:
its base class is needed at definition time, while its UR backend imports need
not be loaded until a fountain/UR export is used. No encoder changes are included
in this checkpoint.

Reproduce this checkpoint with:

```sh
mise run lvgl:app:hardware tools-import-cost --bytecode-cache --timeout 150
mise run lvgl:app:hardware dependency-entropy-generate --bytecode-cache --timeout 150
mise run lvgl:app:hardware dependency-coin --bytecode-cache --timeout 150
mise run lvgl:app:bundle --output dist/lvgl-app/runtime-memory-tools-02
```

Use a new bundle directory; these commands perform temporary diagnostics and
package verification, not image installation or flashing.


## QR encoder optional imports

The original QR encoder class hierarchy and encoding algorithms are retained.
UR/CBOR/PSBT backend imports move into existing consuming methods; PSBT/Seed
annotations become forward strings. Two duplicate, unused bip32/NETWORKS import
pairs disappear. Static/base encoders therefore do not load UR types. No external
application module uses the removed backend aliases as encoder module exports.

Tools import-only private anonymous RAM falls a further 240 KiB, from an 8,628
KiB import delta to 8,388 KiB. All measured UR module counts are now zero in that
import test. These figures describe overlapping fresh-process import chains;
they are not additive to every Home/scan saving. See
`validation/encoder-import-memory-summary.json`.

234 host tests pass, including structural equivalence of every encoder method
apart from imports and forward annotations. On the ARM board, 23 differential
cases exactly match the pinned original source: numeric/compact 12/24-word seed
QR, generic static/string, static/Specter/UR xpub for mainnet/testnet and single
sig/multisig, and PSBT/binary/text UR at all three densities. Fountain sequencing,
current part, completion and restart match; PSBT and binary UR payloads round
trip exactly, including NUL and 0xff bytes. Static exports leave the UR backend
unloaded. Evidence: `validation/encoder-import-payloads-arm.json`. This is a
public-fixture encoder check, not a physical camera/display qualification.


The encoder cleanup also passes the full original Controller public-wallet
export flow: scanned seed import, xpub export, ZXing decoding of displayed pixels,
scanned-address verification and return to Home with workers stopped. Receipt:
`validation/encoder-import-wallet-export-arm.json`. Display hardware was used;
QR inputs were synthetic public fixtures, so this is not optical qualification.


## Release disposable inspected source text

The LVGL adapters inspect original methods to compile reviewed, small changes.
Python's inspection machinery was retaining every line of the complete source
files after those methods were extracted. A shared source reader now releases
only the matching real-file `linecache` entry after extraction, including an
extraction failure. The same exact method source is returned and real files can
be reread on demand. Generated adapter entries stay registered for subsequent
introspection/tracebacks. This changes no screen, encoding, entropy or wallet
algorithm. Seven existing adapters use the reader.

An isolated ARM test of the five original files used by these adapters retained
646,768 bytes (about 632 KiB) in source-text cache entries. With eviction on read,
no entries remain. Private anonymous RAM plus swap increased by 572 KiB in the
retaining test versus 300 KiB with eviction, a 272 KiB smaller increase in this
pair of fresh-process observations. Clearing the cache only at the end did not
return equivalent RAM to the OS; Python retained allocator arenas. Therefore
632 KiB is eliminated object retention, not a guaranteed 632 KiB RSS reduction.
These results are not a complete running-app attribution. See
`validation/source-cache-memory-summary.json` and its before/after receipts.

All 237 host tests pass, including exact/repeated extraction, retention of
generated source and cleanup on error. Real camera preview/capture, seed
creation/wiping and clean camera teardown pass under both the encoder and cache
changes: `validation/source-cache-entropy-arm.json`. No image has been flashed.
The verified runtime bundle is `dist/lvgl-app/runtime-memory-source-cache-01`
(110 files, 3,742,791 payload bytes; releaseReady=false, serviceInstalled=false).

```sh
mise run lvgl:app:hardware encoder-payloads --bytecode-cache --timeout 100
mise run lvgl:app:hardware source-cache-cost --bytecode-cache --timeout 100
mise run lvgl:app:hardware source-cache-eviction --bytecode-cache --timeout 100
mise run lvgl:app:hardware dependency-entropy-generate --bytecode-cache --timeout 150
mise run lvgl:app:hardware app-entry-flow --bytecode-cache --timeout 150
```


The actual isolated `app.run()` / original `main()` path also passes after source
cache cleanup: I/O screen, Settings list, Home and complete worker/native exit,
with original settings unchanged. Evidence:
`validation/source-cache-app-entry-arm.json`. This checks the startup lifecycle
and I/O extraction integration in addition to the camera entropy fixture.

The memory goal remains active. This checkpoint establishes the optional-encoder
and disposable-source-cache removals, not an exhaustive completion claim. Next
verification should measure current Home/scan residency and audit remaining eager
modules before choosing another change; do not add the separate import-only and
cache-object numbers together as a total saving. Image build/flash remains last.


## Defer legacy Decimal rendering

The original `BtcAmount.__post_init__` is the sole consumer of Decimal in GUI
components. It now imports Decimal locally alongside its existing deferred PIL
imports. Every original arithmetic/rendering statement remains unchanged; LVGL's
existing amount formatter continues to operate without importing the legacy
Decimal backend. If the original renderer is used, its Decimal import resolves
on demand. No wallet arithmetic, fee calculation or signing code changes.

The warm Home/real-camera scan pair observes 11,586 → 11,184 KiB private anonymous
RAM plus swap at Home, and 14,120 → 13,732 KiB during scanning (medians excluding
the first three seconds of each phase). Reductions are 402/388 KiB. Both camera
runs processed 57 frames with native ZXing and clean owner exit 0. Decimal and
its native extension remain unloaded after the cleanup. These are sequential
observations with allocator/run-order variation; do not add them to overlapping
import-only figures or call them total system memory. Evidence:
`validation/decimal-import-memory-summary.json` and before/after ARM receipts.

239 host tests pass, including unchanged original amount-renderer logic and
on-demand Decimal arithmetic. The full original Controller multisig fixture also
passes: seed/PSBT/descriptor import, amount/fee and recipient/change review,
change verification, verified signature and exact exported QR bytes. Receipt:
`validation/decimal-import-wallet-flow-arm.json`. Verified runtime bundle:
`dist/lvgl-app/runtime-memory-decimal-01`. No installation or flash occurred.


## Remove unused startup helpers

The unused Controller `datetime` import and unused screensaver `Version` import
are removed under the pinned source guards. Neither alias has runtime consumers.
The decoder imports its original datetime and Aezeed checksum helpers in the
existing consuming methods. All original decoder classes/method bodies and
screensaver definitions are structurally unchanged apart from local imports and
forward image annotations. Settings' explicit Version import is retained, so
version functionality still loads its original implementation when used.

241 host tests pass. Latest warm Home/scan private anonymous RAM plus swap is
11,024/13,464 KiB, versus the preceding 11,184/13,732 KiB checkpoint (160/268 KiB
less). Both scan runs processed 57 frames and shut down cleanly. Home/scan leave
datetime, Version and Aezeed unloaded; they are not removed from the image.
The ARM payload test verifies valid time parsing, fractional seconds, invalid
dates returning None, 12/24-word compact/numeric QR, PSBT and animated UR parsing,
plus original unreadable/malformed input behavior. It checks optional helpers
are absent immediately after decoder construction. See
`validation/startup-helper-memory-summary.json` and
`validation/startup-helper-payloads-arm.json`.

Current verified staging is `dist/lvgl-app/runtime-memory-startup-helpers-01`
(110 files, 3,742,825 payload bytes; releaseReady=false, serviceInstalled=false).
No image build/flash or installation was performed. Reproduce with the existing
`dependency-camera-audit` and `decoder-payloads` hardware cases, using
`--bytecode-cache`, then stage a new directory via `lvgl:app:bundle`.


## Native preview memory cleanup

Two resource-lifecycle changes retain the original renderer, preview pixels,
protocol and wiping behavior. The static preview buffer is already zeroed by
BSS initialization. Screen cleanup now wipes it only after an actual preview
frame has made it dirty, and preview startup reuses that zeroed buffer. This
avoids making unused preview pages private merely by entering another screen.
Every received frame marks the buffer dirty; stopping still wipes the entire
buffer. Its size, RGB/BGR conversion and orientation handling are unchanged.

After successful clear/scan_stop, the native input string releases its enlarged
capacity with shrink_to_fit. Queued command contents remain intact. Capacity
can grow again for the next preview; no input bytes, command limits or framing
are removed. The board's current C++ implementation demonstrably releases the
allocation; the C++ standard does not guarantee every implementation will shrink.

The real-camera pair observes native private Home RAM at 216 → 92 KiB (124 KiB
less), with active preview at 356 KiB in both runs. Both processed 57 frames and
exited the owner cleanly. In the synthetic preview test, native private RAM falls
from 336 to 204 KiB on stop after releasing the input capacity (132 KiB); this
is not an additional guaranteed saving during active preview. Python stayed at
11,024 KiB at Home and varied 13,464 → 13,588 KiB scanning across these native-only
runs. Do not attribute that Python variation to native changes or add RSS values
as total physical RAM. Evidence: `validation/native-preview-memory-summary.json`.

ARM preview tests pass initial black pixels, both orientations, RGB order, raw
binary newlines, Back, black on stop and three clean restarts. A new scan queued
behind clear survives capacity release. Invalid/truncated previews still fail
boundedly with children reaped and reader threads joined. The desktop build also
passes all nine native protocol groups, including the public screen corpus.
241 Python host tests pass. See `validation/native-preview-{after-release-arm,faults-arm,camera-arm,host}.json`.

Current verified runtime staging: `dist/lvgl-app/runtime-memory-native-preview-01`
(110 files, 3,743,017 payload bytes; releaseReady=false, serviceInstalled=false).
Only the isolated native renderer was rebuilt. No OS image or installed app was
changed or flashed. Reproduce with:

```sh
mise run lvgl:app:build
mise run lvgl:app:hardware preview-protocol --timeout 60
mise run lvgl:app:hardware preview-faults --timeout 30
mise run lvgl:app:hardware dependency-camera-audit --bytecode-cache --timeout 100
mise run lvgl:app:build:host
mise run lvgl:app:test:host
```


## Repeated-use memory audit

The current production dependency policy passes startup cancellation followed by
five real-camera sessions with Tools loaded. Each closes the camera owner with
exit 0, leaves zero DMA objects and returns to two Python threads in this scoped
fixture (it does not start the full Controller's monitor workers). Live sessions
processed 36/38/38/38/37 frames. Post-close Python private anonymous RAM plus swap
is 13,360–13,376 KiB, a 16 KiB range; native private memory settles at 204–208 KiB.
The test deliberately retains metadata snapshots, so small growth is not an
isolated leak attribution. No camera QR values or images are saved.

The export fixture checks compact-binary/numeric/address QR, animated PSBT,
brightness persistence timing and Back behavior against actual ZXing decoding of
rendered pixels. Five additional exports then show Python private memory at
10,424–10,432 KiB (8 KiB range), native fixed at 80 KiB, and two Python threads.
Frames clear to black on exit and original settings are not persisted. These
are two different diagnostic processes/workloads, not an end-to-end total or an
indefinite-duration leak bound.

Diagnostic gc.collect after each close freed small object cycles but did not
reduce the observed private memory in either fixture. Forced collection was not
added to production: these observations do not justify a workaround. No material
accumulating leak was observed in these tested cycles.

A follow-up import trace finds typing used by original app annotations and by
shamir-mnemonic 0.3.0 wordlist/utils annotations. Its fresh-process marginal
private cost is 208 KiB in a separate import-only test; this must not be added to
the other process or cache figures. It remains installed/loaded. Removing it
would require reviewing all remaining annotation consumers, including the
sourceless third-party modules; do not unload it or weaken protected wordlist
handling merely to reduce the module count. No such change is made here.

Evidence: `validation/retention-memory-summary.json`, camera/export receipts,
and `validation/retention-typing-{imports,cost}-arm.json`. Fresh staging at
`dist/lvgl-app/runtime-memory-retention-audit-01` has a byte-identical runtime
manifest to `runtime-memory-native-preview-01`: this checkpoint adds diagnostics
and evidence, with no shipped behavior change. No OS image, app install or flash.

```sh
mise run lvgl:app:hardware camera-memory-cycles --bytecode-cache --timeout 150
mise run lvgl:app:hardware qr-export-memory-cycles --bytecode-cache --timeout 150
mise run lvgl:app:hardware typing-import-audit --bytecode-cache --timeout 100
mise run lvgl:app:hardware typing-import-cost --timeout 60
```


## Package ordinary checked-hash source bytecode

The frozen-runtime hardware mode now verifies the exact staged native binary,
Python sources, guards and import-cache bytes before temporary deployment.
It can also ignore ordinary caches for a source-compilation control. Normal
compiled source caches are copied to the diagnostic cache prefix; only LVGL
lookup paths are rebased to the temporary directory, preserving artifact bytes.
CPython's standard loader fixes cached filenames to the matching actual source
path. Tests verify that relocation and same-size/same-mtime stale-source fallback.
The tool removes its own staged caches and does not install or modify /opt/src.

The no-normal-cache control measures Home/scan at 12,308/14,084 KiB private
anonymous RAM plus swap. The shipped ordinary cache measures 11,012/13,576 KiB,
reducing the observed values by 1,296/508 KiB. Both process 57 previews and stop
cleanly. Warm actual-entry default/prepared-prefix controls both reached Home
at 11,068 KiB; those controls alone did not expose the first-boot difference.
All are scoped process observations, not a total-system or reboot qualification.
Evidence: `validation/packaged-source-cache-memory-summary.json`.

The stager compiles unchanged pinned app sources, production LVGL helpers and
camera adapters to checked-hash CPython 3.12 bytecode with fixed target filenames.
It excludes already transformed modules, direct entry scripts and diagnostic
sources. No upstream imports or code execute during compilation. The ordinary
cache contains 142 entries and adds 1,726,498 staged bytes. The launcher selects
/usr/lib/shieldsigner-lvgl/bytecode with -X while keeping -B. The verifier rejects
a launcher which fails to select a declared cache, even if its manifest's generic
file hashes are updated. Sources and app algorithms are unchanged by this step.

Final verified runtime: `dist/lvgl-app/runtime-memory-cleanup-final`, 253 files,
5,469,515 bytes. It is byte-identical to `runtime-memory-source-bytecode-02`, which
passes real camera/RNG seed creation/wiping and full Controller public transaction
review/change verification/signature/export. Final Settings UI updates, delayed
save and reload also pass with original settings unchanged. 245 host tests pass.
`validation/memory-cleanup-acceptance.json` records completion of the memory goal;
full migration/image/production acceptance is not asserted. No OS build or flash.

```sh
mise run lvgl:app:bundle --output NEW_DIRECTORY
mise run lvgl:app:hardware dependency-camera-audit --runtime-bundle NEW_DIRECTORY --timeout 100
mise run lvgl:app:hardware dependency-entropy-generate --runtime-bundle NEW_DIRECTORY --timeout 150
mise run lvgl:app:hardware dependency-wallet-flow --runtime-bundle NEW_DIRECTORY --timeout 180
mise run lvgl:app:hardware app-entry-settings-ui --runtime-bundle NEW_DIRECTORY --timeout 150
```

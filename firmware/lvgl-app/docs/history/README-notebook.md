> Historical notebook preserved during repository cleanup. Entries describe their own checkpoint; see the [current overview](../../README.md) for present status.

# ShieldSigner LVGL migration

This codebase is isolated from the installed wallet application and the earlier
`firmware/lvgl-demo` experiment. It reuses pinned SeedSigner LVGL screen sources
without copying the MicroPython application or the Raspberry Pi camera stack.
The pinned ShieldSigner views/models remain authoritative for wallet behavior.
**Development image built and verified; the user confirmed boot, usable UI and
camera scanning. Real-wallet end-to-end acceptance remains pending.**

## Current flashable development image

`dist/firmware/images/lvgl-dev.cb6170a37a5a/shieldsigner-lvgl-dev-cb6170a37a5a.img.xz`

Use `mise run firmware:where` to locate the current image and
`mise run firmware:verify` to check its files and frozen provenance. See the
[artifact layout](../../../../docs/FIRMWARE-ARTIFACTS.md) and
[repository cleanup plan](../../../../docs/REPO-CLEANUP-PLAN.md) for source, cache,
staging and image locations. Historical checkpoint paths below are retained as
evidence; compatibility aliases keep them usable during the transition.

This includes `runtime-memory-cleanup-final`, selects LVGL by default and retains
ADB plus the base-fork display/button pinout and Rust camera/QR runtime. The SDK
build finished successfully. Packed readback verifies the Mini DTB, 12 MiB CMA,
all overlay/source-cache bytes and launchers; packed ARM Python, crypto, Rust
LCD/frontend and LVGL menu/NUL-passphrase userspace smoke tests pass.

The compressed image is 64,329,836 bytes and expands to 363,778,048 bytes. It may
be selected directly in Etcher; raw-device tools must use the decompressed `.img`
alongside it. `SHA256SUMS` and the verification JSON are in that directory. No SD
card was connected when prepared. The user later flashed it and confirmed boot,
UI operation and camera scanning. Userspace QEMU and readback checks are separate
from those physical observations.

[Build receipt](../../validation/image-memory-cleanup-built.json) ·
[Packed verification](../../validation/image-memory-cleanup-packed.json).

## Memory cleanup acceptance

Verified runtime: `dist/firmware/staging/lvgl-dev.cb6170a37a5a/runtime`.
Its manifest is byte-identical to the hardware-tested source-bytecode candidate.
This completes the memory cleanup of the existing port; the broader LVGL
migration and OS-image release remain separate work. No installation or flashing
was performed.

Latest board observations for Python private anonymous RAM plus swap:

| Workload | Observed Python memory |
|---|---:|
| Home | 11,012 KiB (10.75 MiB) |
| Live scanning | 13,576 KiB (13.26 MiB) |
| Settings UI, separate startup fixture | 10,860–10,880 KiB |
| Transaction flow, maximum sampled value | 16,704 KiB (16.31 MiB) |

Home/scan are medians after each phase's first three seconds. These values
exclude camera/QR/native processes and are not total-device RAM or universal
peaks. Sequential measurements retain run-order/allocator effects. Native Home
private memory separately fell from 216 to 92 KiB; preview input capacity release
returns 132 KiB after stopping. Separate workload/import/cache figures overlap
and must not be added together.

A first-boot source-compilation simulation exposed a packaging gap: the old
launcher had only transformed-module caches, while earlier tests prepared normal
source bytecode too. The final bundle includes checked-hash Python 3.12 bytecode
for 142 unchanged app/LVGL/camera sources and selects its read-only prefix under
/usr/lib. With no ordinary source caches, Home/scan measured 12,308/14,084 KiB;
with the shipped cache they measured 11,012/13,576 KiB (1,296/508 KiB lower).
Both runs processed 57 real previews and exited the camera owner cleanly.
This simulates source-compilation behavior, not a physical reboot. The cache adds
1,726,498 staged bytes (about 1.65 MiB of file storage); final payload is 5,469,515
bytes across 253 files. Entry scripts and already transformed sources are not
duplicated in the ordinary cache. Sources are compiled without executing them.

The launcher retains -B, so imports do not write caches. CPython checks source
hashes, including same-size/same-mtime changes, and uses source when a cache is
stale. Build-time checks cover target filenames, ABI/header hashes, artifact
integrity, duplicate/unsafe paths and actual launcher cache selection. This is
packaging of unchanged code, not a wallet/UI rewrite.

All **245 host tests pass**. The native build passes all nine desktop protocol
groups. The packaged runtime passes real-camera scanning, camera/RNG seed
generation and wiping, full Controller transaction import/review/sign/export,
Settings updates/reload and shutdown with original settings unchanged. Repeated
camera/export tests show no material accumulating leak over their tested cycles;
forcing GC did not improve their private-memory readings and was not added.

Home and empty scanning leave PIL, qrcode, UR types, optional crypto/card stacks,
NumPy/OpenCV, Decimal, date/version helpers and Aezeed unloaded. Required shared
wordlists/wipe protection, original class metadata and feature backends are
retained. Pillow remains needed for original still-image/entropy and optional
scaling consumers. Removing those remaining dependencies or changing wallet
algorithms would exceed this cleanup's no-rewrite constraint. No smartcard or
translation feature work was introduced.

[Acceptance audit](../../validation/memory-cleanup-acceptance.json),
[packaged-cache comparison](../../validation/packaged-source-cache-memory-summary.json),
[retention tests](../../validation/retention-memory-summary.json),
[native buffer evidence](../../validation/native-preview-memory-summary.json), and
[earlier cleanup](../../validation/memory-cleanup-summary.json) contain exact receipts.
The chronological checkpoints below describe earlier states, not current builds.

Regenerate with `mise run lvgl:app:bundle --output NEW_DIRECTORY`. Prefer testing
a frozen candidate with `--runtime-bundle NEW_DIRECTORY`; it verifies cache and
source provenance and avoids compiling edits on the board for each run.
`--fresh-normal-cache` deliberately ignores ordinary bytecode for comparison.
The old OS candidate is inactive; image build and flashing remain later steps.

## Wallet View import cleanup

Wallet Views no longer load foreign-backup decoders, smartcard helpers, ECDSA or
all QR encoders merely to define the View classes. Imports now live in the
original methods that consume them; descriptor type hints are forward references.
Original View control flow, calculations, decoders and cryptographic functions
are unchanged. A structural host check verifies all class bodies after accounting
for the moved imports and type hints.

A fresh-process wallet-View import falls from 14,124 to 10,088 KiB of private
anonymous RAM plus swap (3.94 MiB lower). The eager chain previously loaded
Cryptodome, pysatochip, smartcard, ecdsa and urtypes; these remain unloaded after
that import now. This is not the complete running-wallet footprint.

In the public full Controller transaction scenario, review/signing observations
fell from about 19,036 to 17,196 KiB (1.80 MiB lower). These warm observations
include other incremental cleanup changes and are not isolated allocation
attribution. Do not add this saving to the cold-import result. Transaction input,
change verification, signature, QR export and cleanup passed. The full Controller
wallet-export/address handshake also passes under the import policy, so the
original encoders are verified to load when needed. All 231 host tests pass.
[Evidence and exact checkpoints](../../validation/wallet-optional-import-memory-summary.json).

Wallet-import checkpoint staging: `dist/lvgl-app/runtime-memory-wallet-01`. No installed
files, settings, firmware or SD card were changed.

## Defer QR payload parsers until data is available

Constructing DecodeQR no longer imports UR types, the animated UR decoder,
PSBT framing/parser helpers, or elliptic-curve/HD-key modules solely for possible
future payloads. Their imports now sit in the original methods that use them.
The existing structural test confirms original decoder class logic is unchanged
apart from imports. Public data checks pass compact/numeric SeedQR for 12/24
words, base64/base43 PSBT, reversed/duplicated animated UR PSBT, unreadable data
returning None, and duplicate-key PSBT refusal. The full original Controller
transaction review/sign/export regression also passes.

The steady scanning observation dropped from 14,898 to 14,250 KiB private
anonymous RAM plus swap (648 KiB / 0.63 MiB lower). The live camera processed 58
previews and exited cleanly; DMA returned to zero. UR types remain unloaded while
waiting for a QR, alongside Pillow and optional cipher/card stacks. These warm
observations are not isolated or total-system allocation attribution. All 231
host tests pass. [Evidence](../../validation/parser-import-memory-summary.json).
Parser-import checkpoint bundle: `dist/lvgl-app/runtime-memory-parser-01`.

## Historical image candidate (inactive)

Before the current memory task, an LVGL-default development image build was
launched on the documented Proxmox builder; its completion is not asserted here. Runtime and integration staging each reproduced identical manifests;
the LVGL payload contains English assets only and preserves the reviewed Rust
camera/QR setup and existing supervisor. ADB remains available for acceptance.
Version: `lvgl-dev.66f593cee5e8` (base repository revision marked dirty; runtime
identity is the exact staged manifest digest). The fixed source-date epoch is
the base revision timestamp, not the time the image finished building.

Staging commands (fresh output directories required):

```sh
mise run lvgl:app:bundle --output dist/lvgl-app/runtime-image-candidate-01
mise run lvgl:app:image-draft --runtime dist/lvgl-app/runtime-image-candidate-01 --output dist/lvgl-app/image-candidate-01 --source-date-epoch 1793366723 --default-frontend lvgl
mise run lvgl:app:image-attach --camera dist/os/image-bundles/native-frontend-cf4c428-02 --draft dist/lvgl-app/image-candidate-01 --output dist/os/image-bundles/lvgl-candidate-01
mise run os:remote:build --host YOUR_CONFIGURED_SSH_BUILDER --variant dev --bundle dist/os/image-bundles/lvgl-candidate-01 --name lvgl-candidate-01
```

Evidence: [staging receipt](../../validation/image-candidate-01-staging-host.json).
Build launch alone proves neither a valid image nor a successful boot. Packed
rootfs/provenance checks, image reproducibility, pre-flash documentation and
post-flash acceptance remain outstanding. The installed app/card are unchanged.

## Latest validated checkpoint

Original Controller now passes Home → PSBT scan → signer import from empty seed
storage → finalization → transaction review → descriptor scan/review → change
verification → signing → QR export → Home route. Neither seed storage, transaction
nor descriptor starts loaded. The LCD is physical; inputs are synthetic through
the actual receiver/ZXing/original ScanViews. Input/export bytes, signature,
imported-seed retention and transaction/worker cleanup passed
(`validation/controller-multisig-import-signer-arm.json`). Original View
initialization and wallet/crypto behavior are retained. Separate loaded-seed,
cancellation, descriptor-mismatch and 12/24-word import checks also pass.

Optical capture, other seed-import methods and policy branches, remaining app
behavior, matched resources/latency/soak and image/boot acceptance remain open.
No LVGL image has been flashed.

The original Controller also passes empty storage → seed QR import → passphrase
QR scan → review → edit/save → review/finalize → seed options → Home. The public
passphrase includes NUL, literal backslash-zero, spaces and composed/decomposed
Unicode. Final seed bytes match independently calculated BIP39 PBKDF2 bytes;
original NFC display and NFKD storage behavior is preserved. Inputs pass through
the real receiver/ZXing and original ScanViews with synthetic NV12 frames; this
is physical LCD acceptance, not optical capture. Evidence:
[Controller passphrase receipt](../../validation/controller-passphrase-arm.json).

Full Controller address verification passes for native-segwit receive/change
index 7 after importing a seed from empty storage. The static wallet export route
also passes privacy warning, independently checked xpub details, ZXing decoding
of displayed QR pixels, and a scanned receive-address handshake before returning
Home. These tests use synthetic input frames, original workers/Views/Controller
and a physical LCD. Evidence: validation/controller-address-{receive,change}-arm.json
and [wallet export receipt](../../validation/controller-wallet-export-arm.json).

## Current scope

Per user direction, the current migration targets English only. Translation,
non-English font and locale visual acceptance work is deferred. Existing language
experiments/evidence remain historical; they are not required for this milestone.
Smartcard work is also excluded per user direction. Prioritize English wallet
flows, resources/lifecycle checks and a testable image.

## Dependency cleanup in progress

Fresh Home/Settings snapshots show empty font caches and no loaded PGP,
cryptography, smartcard, OpenCV, NumPy or zbar packages. Pillow and the original
GUI modules remain loaded. Removing the unloaded packages would save image
space rather than RAM in those states.

The first cleanup relocates optional Seed/View imports and defers SLIP39 package
exports until requested. Original secure-delete wordlist ID protection remains
unchanged: the wordlist still loads, while recovery code waits until needed.
Original package bytecode is checked against the reviewed 0.3.0 initializer
before using lazy exports. Original functions and cryptographic behavior remain. Full original Controller
SLIP39 recovery/share review/quiz/discard passes with this cleanup
(`validation/dependency-slip39-recovery-arm.json`).
One warm before/after pair shows private anonymous RAM plus swap lower by 236 KiB
at Home and 428 KiB in Settings. This is a small initial observation, not a final
or isolated allocation-saving claim. See
[first dependency pair](../../validation/dependency-removal-first-pair.json).
The keyboard's unused ImageFont import is removed; component font imports now
happen only inside the original functions that need them. Home/Settings pass
with one fewer Pillow module loaded. The current warm run is 320/228 KiB below
the original Home/Settings private-memory observations, with enough run variation
that the incremental font saving is not isolated. No large RAM win is claimed.
The inactive image candidate predates these changes and is not a current memory
optimization deliverable. No additional image build or flash is requested by the
current memory-reduction goal.

## Current memory measurements

Two matching warm-device pairs were run in both orders (LVGL → PIL, PIL → LVGL)
with the same code/binary, original Controller, physical LCD and real camera.
Each run idles eight seconds, scans for fifteen seconds, cancels and returns Home.
These ranges are the two runs' process medians, in MiB:

| During scanning | LVGL | Original PIL |
|---|---:|---:|
| Python RSS | 16.0–16.8 | 17.2–17.5 |
| Python swap | 4.5–4.8 | 6.3 |
| Native UI RSS | 1.4–1.7 | — |
| Camera process RSS | 7.4–7.6 | 5.3–5.4 |
| Camera process swap | 0 | 1.8–1.9 |
| QR process RSS | 0.8 | 0.8 |
| System MemAvailable | 7.8–8.8 | 9.0–9.1 |

LVGL Home Python RSS is 22.0–23.5 MiB, plus 1.6 MiB for the UI process. Linux
reports about 45 MiB total RAM. Scanning has 8 Python threads, 1 native UI thread,
5 camera-owner threads and 1 QR thread. Both frontends use a separate 3.8 MiB DMA
allocation while the camera runs; DMA returns to zero and owners exit on cancel.

There is still no demonstrated overall memory win. RSS must not be added blindly
across shared mappings, and lower Python RSS partly reflects swap. The LVGL runs
have slightly less system memory available during scanning. Run order changes the
size of that difference, so these are observations rather than an isolated
allocation regression. CPU measurements include substantial diagnostic sampling
and scripted-GPIO overhead; this is not production CPU, cold-start or leak-soak
qualification. No pixels/payloads are saved. Evidence:
[reversed-order resource report](../../validation/frontend-camera-current-reversed-orders.json).

## Current LCD response measurement

A temporary native-host test sends 24 alternating navigation keys on each of Home
and a button list, measuring Python IPC dispatch to the first completed physical
SPI frame. Home median/p95/max: 37.3/114.4/116.8 ms. Button list:
7.4/97.6/122.2 ms. The measurement includes IPC, native scheduling/rendering,
rectangle transport and SPI writes. It excludes GPIO polling/debounce, optical
panel response, wallet/Controller processing and camera load. It is not an
end-to-end physical-button latency claim or comparison with the previous frontend.
The test uses public labels and saves no pixels. Evidence:
[LCD dispatch timing receipt](../../validation/input-latency-arm.json).

## Current shutdown and camera reopen check

The current original-main entry passed SIGTERM after three live camera frames:
Python unwound, camera owner exit code was zero, native UI and original workers
stopped, and original settings stayed unchanged. Evidence:
validation/app-entry-sigterm-camera-current-arm.json.

A production-import-policy camera check then passed startup cancellation plus
three 90-second real-camera sessions with physical LCD output. Sessions processed
432/440/443 previews at 4.90/4.92/4.94 completed previews/sec. Each close returned
DMA to zero and the camera owner exited zero. The direct fixture retained two
Python threads after each close. Post-close anonymous RSS plus swap was exactly
19,788 KiB (19.3 MiB) after each full session; RSS declined as more pages moved to
swap. This supports bounded memory for these repeats, not absence of all leaks.

This is a direct camera/QR/LVGL lifecycle test with Tools imported, not a full
Controller memory measurement or optical known-vector test. QR completion is
suppressed so an incidental code cannot shorten the timed sessions; no pixels or
QR values are saved. See validation/camera-long-soak-{arm,summary}.json. All 215
host tests pass. Neither installed app nor image was changed.

## Remaining release gates

The goal remains a complete frontend migration and reproducible bootable image.
The following work is required before building that image; flashing stays last:

1. Close in-scope functional gaps: remaining encryption compatibility,
   generic grid styling and English text-entry edge cases.
   Exercise original Controller routes and refusals, not just screen fixtures.
2. Run larger acceptance scenarios spanning seed creation/import, passphrases,
   wallet export/address verification, transaction review/signing/cancellation,
   settings, wipe and camera reopen. Keep public fixtures and explicit scope.
3. Complete matching live-camera resource pairs, repeat with reversed order,
   measure responsiveness/FPS and run a longer lifecycle soak. Include Python,
   native UI, camera/QR processes, swap, system availability and DMA separately.
4. Prepare image/service integration, dependency and license closure, truthful
   version provenance, native artifact checks, startup/shutdown and rollback
   behavior. Validate the staged payload before building a bootable artifact.
5. Build and verify the image reproducibly only after the preceding gates pass;
   flash as the final implementation step, then verify boot and acceptance.

Interactive testing uses a temporary ADB-launched app with separate settings;
it is not a release image or completed boot acceptance. Do not redeploy files or
run a competing hardware diagnostic while that session is active.

## Inactive runtime staging

`mise run lvgl:app:bundle --output NEW_DIRECTORY` stages the current static ARM
renderer, production Python adapters, source guards/pins, native build manifest,
available notices and a foreground launcher. The directory must be new; the
stager never installs files, enables a service, changes settings or builds an OS.
`mise run lvgl:app:bundle --verify DIRECTORY` checks all files, modes, checksums,
native provenance and extra/missing files. The payload requires the existing
`/opt/src` application and `/usr/lib/shieldsigner-camera` runtime. It is not a
standalone image or an estimate of complete image size.

Initial local staging in `dist/lvgl-app/runtime-stage-20261030` contains 63 files,
1,759,380 payload bytes. A second stage has an identical manifest; deliberate
file modification is rejected. The launcher passes shell syntax checks and uses
separate `/userdata/shieldsigner-lvgl-settings.json`. Release readiness and
license closure remain explicitly false, and no service is installed. Complete
dependency/font notice closure, final version.json provenance, service policy
and ARM acceptance are required before image integration.
Evidence: `validation/runtime-stage-host.json`.

Unit tests explicitly use Python 3.12 (matching the board's interpreter series):
`mise run lvgl:app:test` passes 183 tests with Pillow 11.3.0 and qrcode 7.3.1.
This does not qualify the board's native Python extensions.

Prepared physical camera-IV cases are controller-camera-iv-cbc/ctr/gcm and
controller-camera-iv-cancel-preview/review via `lvgl:app:hardware`. They exercise
original Controller/View initialization and the new private-camera binding,
compare the incoming IV to the captured full-image hash, and check camera/DMA
cleanup. They stop at mnemonic-ID selection and are not full encryption-roundtrip
tests. These cases now pass on ARM, including both cancellation stages. Extended
controller-camera-encrypted-cbc/ctr/gcm cases continue through original encryption
Views and QR export, decode displayed pixels with native ZXing, then check
original decrypt Views for wrong-key rejection and exact mnemonic recovery.
All three camera-IV modern modes pass; strict legacy-format checks are documented
below. Evidence:
validation/controller-camera-encrypted-{cbc,ctr,gcm}-arm.json.

## BIP-85 complete-flow checkpoint and partial word pages

Original Controller BIP85 12/18/24-word child creation passes on the physical LCD:
word-count selection, index-0 keypad entry, review of every word, original backup
quiz, pending child and finalized storage. Parent words remain unchanged; the
HMAC entropy and final BIP39 seed bytes match independent calculations. Evidence:
validation/controller-bip85-{12,18,24}-arm.json. These use public test seeds and
scripted buttons, and do not qualify every index/error path or physical buttons.

The pinned original word review rounded its page count down, hiding the final two
words for 18-word seeds and word 33 for long SLIP39 shares. The isolated guarded
word_pagination.py hook corrects only the display page count; the adapter supplies
continuous word numbering on partial pages. Derivation/storage/entropy behavior
is unchanged. Host coverage includes 12/18/20/24/33 words; full SLIP39 acceptance
is scoped separately below. All 194 Python tests pass.

BIP85 checkpoint payload: dist/lvgl-app/runtime-bip85-current, including
locale assets and the pagination fix. No boot service, OS build or flashing.

## SLIP39 recovery checkpoint

Original Controller recovery passes for 20- and 33-word 2-of-2 shares, using the
real Rust QR decoder with public synthetic NV12 frames. Both recover the exact
public test secret, finalize storage, review every share word and complete both
original backup quizzes. The 20-word run also passes Discard seed → Home with
empty storage. Scanner owners stop and original wipe completes twice. Evidence:
validation/controller-slip39-{20,33}-arm.json. Optical input, manual entry,
multi-group/passphrase policies and share generation/regeneration remain open.

Testing exposed an upstream inherited-wipe initialization bug. The isolated lazy
slip39_lifecycle.py adapter initializes two empty parent fields before the original
constructor; parsing, derivation, passphrase and wipe implementations are unchanged.
The failed initial run is retained, and tests emit success only after cleanup.
See DIVERGENCES.md for the exact scope and source guards. All 200 Python tests
pass, including lazy/already-loaded model installation, constructor restoration
and source-tamper rejection.

SLIP39 checkpoint payload: dist/lvgl-app/runtime-slip39-current (99 files,
2,537,565 bytes), verified with locale assets and both lifecycle/page fixes.
It is not a bootable image or active service; nothing has been flashed.

## Runtime notice inventory

`mise run lvgl:app:notices` reproduces metadata from 27 pinned source font files
in the digest-pinned offline font-builder image, verifies retained compiler/runtime
notices against Zig 0.15.2, and updates validation/notice-audit-host.json. Both
Apache-2.0 and OFL-1.1 font terms are retained: the original application's Open Sans
files and the newer locale-pack faces declare different licenses. Original font
copyright/name/license records and source-file hashes are saved without guessing
which absent terms apply. See licenses/README.txt for provenance and scope.

The stager includes the notice inventory and rejects stale notice/source pins;
verification checks notice files against that inventory as well as the outer
manifest. Two stages match exactly; a changed notice with a rehashed outer
manifest is rejected (validation/notice-stage-host.json). Latest inactive stage:
dist/lvgl-app/runtime-notices-current, 111 files / 2,647,350 bytes. App executables
are unchanged by this notice-only step.

License closure remains explicitly false: the pinned LVGL screens core has no
top-level grant, and seedsigner-icons.otf has no embedded copyright/license name
records. Applicable terms/provenance for those remain open. Original OS/application
and camera-runtime dependencies are separate image-level notice work. This stage
is neither a release-ready image nor an installed service; nothing was flashed.

## Legacy encrypted-QR compatibility

Strict format checks pass on the physical LCD for legacy CBC (actual KEF version
1) and legacy ECB (version 0). CBC uses the real camera and original image-hash
16-byte IV; ECB uses the original no-camera/None-IV route. Original Controller
export, exact native ZXing decoding of displayed pixels, wrong-key rejection and
original mnemonic recovery pass. Decryption is through original Views after
export, not an optical rescan/full Controller import. Legacy modes are selected
explicitly by diagnostics; no additional encryption settings are exposed.

The mode label alone is insufficient proof: original KEF may select a newer padded
format for zero-ending entropy. The diagnostic now asserts actual decoded version
numbers and uses a suitable public fixture for legacy formats. Modern ECB also
passes with its naturally selected padded version 6 and Base43 text export. See
validation/controller-camera-encrypted-cbc-v1-arm.json and
validation/controller-encrypted-ecb{,-v1}-arm.json. All 201 Python tests pass.

The harness now quotes the remote ADB command so spaced mode names remain one
argument. No app encryption, entropy policy or production runtime code changed.
That test-only step retained dist/lvgl-app/runtime-notices-current.

## Large-grid selection style

The original selected-button color is now forwarded for generic large grids and
Home, including upstream's manual selection repaint and focus/pressed states.
Default styling stays #FF9F0A. Nine pixel/navigation cases pass on desktop and the
physical LCD using original screen classes: 2/4-button grids and Home, each with
default/cyan/purple selection. Right → Select still returns index 1. Malformed
colors are rejected before widget construction; per-widget color state is removed
when widgets are deleted. Evidence: validation/grid-color-arm.json and
native-grid-color-host.json. Arbitrary custom font parity remains separate.

All 202 Python tests and the nine existing native regression cases pass. That
style checkpoint payload is dist/lvgl-app/runtime-grid-current.
No installed app, OS image or microSD changed.

## Inactive English image-overlay draft

Latest English-only runtime: dist/lvgl-app/runtime-english-current (78 files,
1,922,031 payload bytes). No locale assets are included. An offline overlay draft
is at dist/lvgl-app/image-overlay-draft-b (81 payload files, 1,924,302 bytes).
It does not install anything, build an OS or flash a card. Default routing remains
the existing PIL launcher until final activation is explicitly staged.

The selector preserves the existing S99/start-seedsigner supervisor. Its LVGL
branch keeps the reviewed working-image prefix: zram setup, locked-memory limit,
small-RAM/code-lock policy and camera module/environment setup before Python.
The original launcher is retained byte-for-byte as shieldsigner-launch.pil.
/userdata/shieldsigner-lvgl.rollback always selects it; a failed LVGL exec is not
masked by launching a competing frontend. Host tests cover routing, setup,
argument forwarding, rollback priority and failure behavior. Device boot/service
acceptance remains pending; these tests use stubs and never run target setup on
the workstation.

The draft stages original-reader-compatible version.json with a lvgl-dev payload
identity, actual base Git commit plus dirty marker, and explicit SOURCE_DATE_EPOCH.
The demonstrated epoch 1793366723 is the base commit time, not a claim of wall-clock
image creation. Full runtime hashes/native provenance are retained. Two drafts
match byte-for-byte; modified rollback scripts are rejected. All 208 host tests
pass, including the original version-file readers. Evidence:
validation/image-overlay-draft-host.json.

Reproduce or verify without any image build:

```sh
mise run lvgl:app:image-draft --runtime dist/lvgl-app/runtime-english-current \
  --output dist/lvgl-app/image-overlay-new --source-date-epoch 1793366723
mise run lvgl:app:image-draft --verify dist/lvgl-app/image-overlay-draft-b
```

Final activation, buildroot hook-up, current-flow/soak gates and boot acceptance
remain required. Flashing is still the last implementation step.

## Guarded SDK/rootfs integration hook

The image draft now carries standalone overlay-apply.py for the Linux builder.
It refuses a live root, validates the reviewed launcher and all 44 original-app
source hashes before writes, rejects unsafe/symlink destinations, and verifies
copied contents/modes and rollback bytes afterward. Existing camera startup
hashes/modes must pass first. The hook then extends that same receipt with the
new verified files and overlay lineage, following the existing LCD/zram pattern;
it does not relax the camera verifier.

The optional SDK hook runs after camera/LCD/zram installation and before rootfs
hardening/packing; packed-image verification checks the layer again. Camera-only
bundles remain unchanged. Pinned OS generated scripts pass shell syntax and legacy
hook recognition checks. A disposable rootfs test uses the real 81-file draft,
44 pinned source guards, frozen camera frontend/startup checks and original memory
policy lines. Unit fixtures also reject changed sources/launchers, copied-file
tampering and destination symlinks. All 215 host tests pass.

Current draft: dist/lvgl-app/image-overlay-sdk-current. Combined frozen camera
bundle: dist/os/image-bundles/lvgl-english-draft-current. The camera-probe and QR
executables match the connected device exactly; Rust LCD source inputs match its
build receipt (the binding is rebuilt by the SDK, not claimed binary-identical).
Both drafts still default to PIL. No SDK compile, OS image, device install or
flashing has been performed.

```sh
mise run lvgl:app:image-attach \
  --camera dist/os/image-bundles/native-frontend-cf4c428-02 \
  --draft dist/lvgl-app/image-overlay-sdk-current \
  --output dist/os/image-bundles/lvgl-english-next
```

Evidence: validation/overlay-apply-host.json, lvgl-sdk-hooks-host.json and
camera-base-bundle-device-match.json. Full SDK packing, current-flow completion,
activation and physical boot acceptance remain separate gates.

## Locale assets and runtime language support

`mise run lvgl:app:locales` builds the pinned upstream producer in its pinned
Docker image using the original app's exact translation gitlink. It builds
offline after image acquisition, keeps sources read-only and caches toolchain
outputs by input pins. Unchanged assets are verified/reused. `--verify DIRECTORY`
verifies an existing runtime asset index without a build.

Current output: dist/lvgl-app/locale-assets/88b3d0f48862f452. It covers 22 catalog
locales including English, with nine font locales: 32 required runtime files,
709,846 bytes. Repeated builds have identical runtime file hashes
(validation/locale-supplement-host.json); the original corrupt-font rejection
check is retained in validation/locale-assets-host.json. Catalogs remain original-app-owned.
Debug glyph JSON and unused endonym heights are not required runtime assets.

Enable the native loader/picker with `app.py --locale-root DIRECTORY` alongside
normal launch arguments. Python verifies indexed sizes/hashes using bounded reads;
the native host reuses upstream font/run ownership and picker image loading.
Original Settings/gettext retain language selection, translations and persistence.
The loader resynchronizes after a native-host replacement. This is optional until
language acceptance and runtime packaging are finished.

`tests/locale_native.py BINARY DIRECTORY` exercises all 22 locale switches and nine
picker image rows on desktop. `mise run lvgl:app:hardware locale-native
--bytecode-cache` repeats it with the physical LCD after staging assets under
/userdata/shieldsigner-lvgl-locales; validation/locale-native-arm.json records a
clean pass. The original Controller language-flow test also passes Japanese →
Persian → English (validation/controller-locale-arm.json). Native RSS point
samples in the public locale probe range 1,500–1,848 KiB, with one thread and
zero swap; these are not whole-app or peak memory figures. Neither test
establishes translated-screen visual parity. The original producer rejected one Hindi and three Thai templates. The offline
closed-set supplement now shapes all eight possible formatted variants using the
unchanged translations. See validation/locale-supplement-{host,arm}.json: all
variants have complete glyph runs and rendered on the physical LCD; all 21
compiled catalogs remain byte-for-byte unchanged. This resolves those inventory
gaps, while broader translated-screen visual acceptance remains open.
Native inputs were rebuilt after adding the language source pin. No OS image has
been built or flashed.

## Earlier entropy checkpoint

Physical camera entropy capture/review/reshoot/cancel now passes with the original
RGB sampling reads and collection rules (`validation/image-entropy-physical-arm.json`).
The physical diagnostic uses lightweight scoped attribute swaps instead of
`unittest.mock`; its earlier test-only memory footprint contributed to misleading
integration failures. Experimental grayscale/pairing code is test-only and inactive.
The original final-image fallback also passes physical capture → review → reshoot
and capture → review → accept, with camera exit 0 and zero remaining DMA buffers
(`validation/entropy-fallback-arm.json`). Its guarded, process-local dependency
substitution preserves upstream retry/cleanup behavior.
Host suite: **183 passing tests**. Memory/latency, real Controller/RNG/wipe integration,
remaining screen/flow coverage, image packaging and final boot acceptance are still
open. Real-Controller entropy capture/cancel and capture/review/accept now pass
(`validation/controller-entropy-cancel-arm.json` and
`validation/controller-entropy-review-arm.json`). Earlier failing runs omitted
`SHIELDSIGNER_SMALL_RAM=1` and exercised the larger RGB camera transport;
they did not qualify the intended NV12 configuration. The shared LVGL startup
policy now enables both its import policy and the small-RAM camera environment.
The original mixer and 12-word pending-seed creation also passed, followed by
original storage wipe (`validation/controller-entropy-generate-arm.json`).
This stops before word review/finalization; lifecycle, other word lengths and
performance qualification remain open. The successful review run still sampled
11,584 KiB Python swap, so functional success does not mean memory is resolved.
No LVGL image has been flashed.

## Architecture

- `sources.lock.json` pins the current wallet app, reusable C/C++ screens, LVGL,
  and upstream binding/app references. `sources.py` fetches verified clean source
  checkouts into ignored `dist/lvgl-app`. Upstream attribution/licenses remain
  in the source checkouts and must accompany distributable binaries.
- `native/host.cpp` runs the upstream screen corpus on ARMv7/Linux/musl. It owns
  LVGL, fonts, layout and keypad state; it contains no wallet/crypto logic and
  makes no GPIO/SPI/camera requests.
- `python/transport.py` runs the native process with private anonymous pipes.
  Bounded binary RGB565 rectangles and typed JSON results are framed on stdout;
  requests are bounded JSON lines on stdin. No network listener or disk queue,
  no logged request/response values. Reader failure poisons the client.
- `python/contracts.py` explicitly maps original screen classes/arguments to
  native configuration and preserves selection indices, Back/Power sentinels,
  exact words and text results. It resolves dataclass defaults without calling
  PIL screen constructors. Unreviewed specialized screens are rejected.
- `python/runtime.py` provides opt-in, source-guarded View dispatch and debounced
  input/result handling; `python/luckfox.py` reuses the installed display/input
  policy. These adapters are not yet installed in the normal application.
  The next validation connects these contracts to the original app's View dispatch,
  reviewed display/input interfaces and existing Rust camera/QR adapters.
  Reviewed direct Screen constructions now use the constructor bridge as well;
  unreviewed classes remain an explicit gap.

`COVERAGE.md` lists 87 top-level Screen classes and candidate name matches. These matches are not
semantic validation. 966 statically resolved view calls were inventoried;
branches with dynamic calls, screen-specific preprocessing, threads/callbacks,
and classes outside the screen directory still require explicit review.

## Commands

```
mise run lvgl:app:inventory
mise run lvgl:app:build
mise run lvgl:app:test
```

The cross-build uses mise Zig 0.15.2 and LVGL 9.5.0. Build inputs are clean exact
commits; compiled objects are cached under ignored dist. `--host` builds a native
workstation host into a separate directory for off-device testing. Neither
build command deploys, modifies installed app files, builds an OS or flashes.

## Verified so far (2026-10-30)

The stripped static ARM native host is 1,415,812 bytes at the initial checkpoint.
All 43 public upstream fixture screens rendered on the connected Luckfox Mini
using a no-GPIO pixel sink. An injected Enter/release traversed LVGL keypad
navigation and returned `button_selected` index 0. The native host and transport
were shut down after the test. Local receipt:
`dist/lvgl-app/native-smoke-arm.json`. This proves native construction/rendering
and one input contract, not wallet integration or physical-display correctness.

Fifteen initial adapter/runtime/transport tests verify no PIL screen construction, menu ordering,
settings check indices/help, exact seed words/page numbers, Back/Power results,
text preservation, debounce and rejection of unreviewed signing screens. IPC
error tests cover malformed rectangles, failed display writes, oversized requests
and child/thread cleanup. Thirteen adapters also passed on-board smoke tests
using the original installed screen classes and all four exact-source guards.

## Remaining acceptance gates

1. Complete explicit adapters for every reachable screen, including fork-specific
   smartcard/encrypted-QR/BIP85/SLIP39/hardening flows. Track inheritance, derived
   titles/defaults, callbacks, cancellation, language/font selection and direct
   `.display()` calls. Do not silently drop screen-specific fields.
2. Integrate View/Screen dispatch in the isolated application launch path while
   leaving views/models, crypto and entropy policy unchanged. Remove obsolete
   PIL rendering allocation/imports only when all callers are accounted for.
3. Use the reviewed ST7789 initialization/inversion/10 MHz mapping and buttons.
   Integrate native camera preview plus full-resolution Rust ZXing decoding,
   animated/binary QR display, and entropy capture with bounded ownership and
   cleanup. No substitute camera/entropy algorithm.
4. Exercise full public-fixture seed creation/recovery, passphrases, addresses,
   settings, QR input/output, multisig/PSBT review/signing/cancel flows on host
   and physical Mini. Never equate screen fixture rendering with flow coverage.
5. Measure matched startup/menu/Scan/signing memory, threads, CPU, UI latency,
   sustained rendering/QR rates, cancellation, reconnect/failure paths and DMA
   cleanup. Include native buffers and Python allocations; no blanket RAM claims.
6. Document source pins, upstream/local differences, licenses, evidence and
   remaining limits. Produce/rebuild and inspect the exact bootable image.
7. **Flash last**, after all feasible pre-flash validation and documentation.
   Then perform cold-boot and physical acceptance checks. The working image
   remains unchanged during development; temporary test deployment is allowed.

No goal acceptance requirement is waived by this checkpoint.

### Known behavior gaps at this checkpoint

The initial menu adapter does not yet implement the fork's battery indicator or
very-long-press display switching. Status/custom-icon behavior, app callbacks,
loading/toast/screensaver ownership and direct Screen constructions still need
parity review. `COVERAGE.md` marks adapters as flow-unverified even when their
native configuration rendered successfully. Do not use this checkpoint's
partial dispatch as a fully migrated wallet application.

## Settings and text-entry checkpoint

The real original `SettingsMenuView` / `SettingsEntryUpdateSelectionView` and
Settings model now pass a six-step LVGL flow on the Mini and actual LCD:
select Bitcoin network, update a temporary model to Testnet, Back to the parent,
Back to General, select a deep Advanced row and restore its scroll position.
The test substitutes only View dependency initialization (no full Controller),
uses scripted keys through Runtime/LVGL, and redirects settings persistence to
an ephemeral path. No persistent settings are written. It does not prove
physical-button operation or the full Controller lifecycle.

The registered constructor bridge also handles direct `.display()` calls.
On-board tests passed PBKDF2/BIP85/account/derivation entry, KEY3 Save from both
keyboard and top-nav, ignored empty Save, Back's 1000 sentinel, generic Save
whitespace trimming, and exact dice/coin auto-complete outputs. These are public
UI input tests; seed-generation/entropy mixing remains in original models and
requires end-to-end testing next.

Local commands for these scoped checks (after temporary staging) are in
`tests/settings_flow.py` and `tests/keyboard_flow.py`. The native transport and
23 host unit tests cover input, constructor identity/restoration and failures.
Local additions and their rationale: [DIVERGENCES.md](../../DIVERGENCES.md).

Flashing remains the last step. This checkpoint is not a release image.

### Public seed recovery checkpoint

`tests/seed_recovery_flow.py` exercises the original SeedMnemonicEntryView and
SeedFinalizeView with real SeedStorage/Seed models, through LVGL KEY2 acceptance
and Done on the LCD. The public BIP39 abandon/about vector is prefilled, all 12
words are reviewed/accepted, checksum validation and seed derivation stay in the
unchanged model, and the finalized seed has fingerprint `73c5da0a`. Cancelling
word one clears the pending mnemonic and leaves the finalized test seed intact.
Test material is wiped on exit; no settings are persisted.

This is the prefilled review/edit route, not a test of typing every letter. The
View dependency initializer is still injected for these isolated flows; the
production Controller's startup, timers and notifications are not yet covered.
The full migration, passphrase response contracts, camera/QR and signing remain
open. Normal installed app/image files have not been modified or flashed.

### Passphrase checkpoint

`tests/passphrase_flow.py` passes on the LCD: Save/Back preserve exact spaces,
Unicode, CR/LF, printable ASCII and empty text; Save works from top-nav focus;
the unchanged add/review/finalize Views and Seed model retain the expected
fingerprint; Back/discard clears the passphrase. No generic keyboard trimming
is applied to passphrases. Embedded NUL is preserved through a raw shadow buffer; NUL-bearing values
show `\0` for NUL and `\\` for backslash, with a title explaining the display
mode. Save/Back and UTF-8 cursor/edit operations pass the physical-LCD fixture
([receipt](../../validation/nul-entry-arm.json)). The original add/review/finalize
Views and Seed fingerprint check also pass with a NUL-bearing public passphrase
([receipt](../../validation/nul-passphrase-flow-arm.json)); this fixture injects View
dependencies and does not establish full Controller coverage.

Controller integration must also clear/restart the native UI host on the
original inactivity wipe: temporary model wiping alone does not qualify the
lifetime of native widget text. This remains part of the Controller acceptance
gate, alongside wipe timers, toast ownership and screensaver behavior.

### Camera/QR ScanScreen checkpoint

`python/camera_scan.py` now routes the original ScanScreen through the installed
managed Rust camera receiver and persistent Rust ZXing worker. The original
DecodeQR consumes the full-resolution byte result exactly as its `add_image()`
method does. Preview-only resize/rotation stays in the existing native renderer;
the native LVGL host centers its 240x180 / 180x240 RGB output without cropping
and reuses upstream camera overlay widgets and Back handling.

Binary preview messages have fixed geometry/size bounds, serialized header/pixel
writes, explicit acknowledgement, and a 3-second incomplete-body deadline.
There is one preview in flight. No JSON/base64 pixel expansion or disk transport.
Ordinary RGB bytes are converted to LVGL's BGR byte storage, independently checked
with a color fixture. Preview buffers are cleared on stop, the overlay is deleted,
and the LCD returns to black. `native/live_preview.h` owns this host-only glue.

Hardware checks:

- Three real-camera cycles passed: startup cancellation and two live preview /
  native QR attempts. Each returned camera exit 0, closed its QR worker and left
  zero DMA objects. No QR happened to decode from the physical scene; this is
  lifecycle/preview evidence, not known-code optical qualification.
- Six public synthetic-input cases passed through native NV12 reception,
  full-resolution ZXing, original DecodeQR and LVGL on the LCD: 16/32-byte
  CompactSeedQR, every byte value, a Bitcoin address, Unicode passphrase text,
  and reverse-order/duplicate animated UR PSBT fragments. Recovered bytes and
  decoder statuses match direct original-model input. The all-byte payload is
  correctly classified INVALID by the app; its QR bytes still match exactly.
- Preview transport passed both orientations, RGB color order, binary bodies
  containing newlines, native Back and black-on-stop. Invalid sizes fail before
  accepting pixels; incomplete input exits after about 3 seconds, with child
  and reader thread reaped.

The physical camera is injected only in the synthetic fixture test; production
ScanScreen always uses the installed managed owner config. Tests save no camera
images or camera-derived QR payloads. Source/backend injection is diagnostic-only.

This does not yet qualify the complete original ScanView destination routing,
known optical code capture, image-entropy capture, animated QR *output*, full
Controller integration, or matched performance/memory. Non-fullscreen Scan
render rectangles and other display resolutions remain unsupported by this
initial host. The current target is the connected 240x240 ST7789 Mini.

## Transaction and QR checkpoint (2026-10-30)

The isolated original `PSBTMathView`, recipient and change-detail Views,
`PSBTFinalizeView` and `PSBTSignedQRDisplayView` passed a combined Luckfox LCD
run with the public `NORMAL-1_p2wpkh` fixture. Back preserved exact unsigned
bytes; approval added one signature; the pre-trim signed model finalized;
ZXing reconstructed the exact trimmed signed PSBT from rendered QR pixels.
Loading indicators used native LVGL. View dependency initialization and button
input were injected; this is not full Controller or optical qualification.
The test and durable receipt are `tests/psbt_signing_flow.py` and
`validation/psbt-signing-arm.json`. No private seed or transaction data is saved.

The generated coverage table deliberately labels adapters “flow unverified”:
that conservative aggregate label does not encode individual fixture results.
Read the validation receipts for the specific paths and limits actually tested.


The original Controller configure/start loop now has a temporary hardware test,
`tests/controller_flow.py`, with native rendering and unmodified View dependency
initialization. Its Home/Settings/Home result, storage/worker checks and initial
resource snapshots are in `validation/controller-arm.json`. This explicitly
skips startup interstitials and does not qualify wipe interruption, screensaver,
toasts or battery overlays; it is not yet a production launch path.


Controller/camera tests must retain the working image's small-RAM startup policy.
`python/startup_policy.py` reuses and hash-checks that shared dependency before
Controller initialization. Three short live-camera wipe runs passed with it;
the baseline without it failed. See the camera-wipe follow-up in DIVERGENCES.md
for exact scopes and receipts. Do not omit this policy in image packaging.


Native screensaver activation, wake-key consumption, exact public-menu pixel
restoration and per-View opt-out passed an accelerated hardware test. Controller
state/reset/stop operations use `python/screensaver_bridge.py`; the scoped result
is `validation/screensaver-arm.json`. Custom SD logos, normal-duration soak,
physical button testing and combined wipe/screensaver testing remain pending.


The complete original startup interstitial path now passes on the LCD: native
opening splash, the real development-build warning, Home, Settings and Home.
See `validation/controller-startup-arm.json`. `assets.py` uses Pillow 11.3.0 on
the **build host** and the pinned upstream converter to generate native RGB565
assets from the pinned app's ShieldSigner/SeedSigner PNGs. This adds no target
Pillow rendering requirement. Branding provenance and the identical repeat-build
hash are in `validation/startup-branding-build.json`; original source licenses
must accompany packaged assets. SD-card custom logos remain unimplemented.
`render_rgb565.py` renders deliberately captured public test buffers for visual
review without adding a host Pillow runtime requirement to that diagnostic.


SeedQR format/warning/whole/zoom/optional-Done Views now pass four public-fixture
LCD cases (12/24 words, Standard/Compact). Whole/zoom drawing shares the original
Python QR matrix, preserving its segmentation and mask without PIL rendering.
Eight malformed-matrix requests were rejected and native menu recovery passed.
See the transcription validation receipts; actual scan confirmation, encrypted
transcription and full word-backup verification still need qualification.


Backup verification now has scoped LCD checks for the complete 12/24-word quiz
(including wrong-answer retry and pending-seed finalization) and four SeedQR
scan-confirmation outcomes. Scan confirmation uses synthetic NV12 input through
real native receiver/ZXing and original comparison logic; optical qualification
is still pending. See `validation/backup-quiz-arm.json` and
`validation/seedqr-confirmation-arm.json`.

## Verified temporary hardware runner

After stopping the ordinary app and building, run one public-fixture check:

```
mise run lvgl:app:build
mise run lvgl:app:hardware seedqr-confirmation
mise run lvgl:app:hardware transcription-protocol
```

Available cases are listed by
`mise exec -- uv run python firmware/lvgl-app/hardware_check.py --help`. The runner selects a single connected
ADB board or accepts `--serial`; it refuses existing Python/camera/native owners.
It never stops the normal app, installs a boot service, or flashes anything.
The build now emits a native input/hash manifest. The runner rejects stale
artifacts, verifies native and Python/test hashes after pushing to /tmp, uses a
fresh bytecode-cache prefix, and records exact deployed source hashes. A check
passes only with one `passed: true` receipt, clean command termination, no Python
traceback, unchanged local inputs and no remaining owners. An ADB exit zero by
itself is insufficient. Logs and detailed manifests remain under ignored
`dist/lvgl-app/checks/`; preserve reviewed scoped receipts under validation.
Timeouts fail the check and request SIGINT only for that exact owned diagnostic,
allowing its finally cleanup to run; the timeout cleanup branch is not yet
fault-injection qualified on hardware. The initial six runner cases do not
include wipe tests, whose intentional Controller interruption traceback needs
an explicitly reviewed acceptance rule rather than broadly ignoring tracebacks.


Encrypted-key and mnemonic-ID entry now return exact typed Save/Back dictionaries
through native LVGL. Public-fixture LCD checks cover text preservation and original
discard routes; `mise run lvgl:app:hardware encrypted-entry` reruns them. Review
screens and full encrypt/decrypt flows are still pending. A sampled-short-press
release fallback now prevents a low observation being lost across a slow poll;
physical GPIO latency still needs measurement. See the encrypted-entry receipts.


Encrypted review adapters now preserve full values in a scrolling native list,
including the original space-marker policy. The public-fixture hardware check
`mise run lvgl:app:hardware encrypted-review` exercises original review/export
and decrypt Views. The initial completed crypto checkpoint is recorded in
`validation/encrypted-review-crypto-arm.json`: AES-ECB only, wrong-key rejection,
exact mnemonic recovery, scripted input on the physical LCD. This is not optical
qualification, a recommendation to change encryption settings, or coverage of
camera-derived IV modes. See DIVERGENCES.md for presentation changes and test
boundary details. Rendered-QR export is checked separately before claiming an
end-to-end QR round trip.


The subsequent rendered-QR round trip passed on the Luckfox LCD. Original
transcription-mode selection and fullscreen export Views produced a native QR;
native ZXing decoded the transmitted RGB565 framebuffer into exact expected
bytes. Those decoded bytes then entered the original decrypt View: a wrong key
was rejected, and the correct key restored the exact public mnemonic. The QR
framebuffer was black on exit and the runner found no remaining owners. Receipt:
`validation/encrypted-qr-roundtrip-arm.json`. This covers AES-ECB only and uses
scripted keys plus injected View dependencies; optical scanning, physical input,
full Controller integration and other encryption modes remain unqualified.


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


The address explorer LCD check passed all four seed/descriptor receive/change
cases. See `validation/explorer-arm.json` and rerun with
`mise run lvgl:app:hardware explorer`. Original Views generated/cached 20 addresses,
paged to index 17, matched independently derived addresses, and exported byte-exact
QRs decoded by native ZXing. Original QR return selection/scroll arguments, cached
page contents, list Back, and SeedOptions Back cleanup passed. This does not prove
exact visual scroll restoration, optical input or every script/network. Longer
scripted press/release timing passed after the initial pulse timeout; real GPIO
latency and that timeout's cause remain unqualified. Current host suite: 78 pass.


Final-word LCD checks passed all six 12/24-word zero/coin-bit/selected-word public
cases. See `validation/final-word-arm.json` and rerun with
`mise run lvgl:app:hardware final-word`. Original checksum calculation produced
exact independently derived BIP39 mnemonics/entropy; original pending-seed
conversion and Load/Discard destinations passed. Result Back preserved the
pending mnemonic. This does not qualify coin-keyboard collection or execution of
the destination finalize/discard Views, which retain separate acceptance scopes.
Current host suite: 80 tests pass. The installed app/image remains unchanged.


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


### Temporary deployment storage

The hardware runner now puts its Python/test bundle at
`/userdata/shieldsigner-lvgl-app`, avoiding approximately 820 KiB of files on
RAM-backed `/tmp`. Bytecode remains in the separate checked-hash cache.
The native executable remains `/tmp/shieldsigner-lvgl-host`: `/userdata` is
mounted `noexec`, which the runner respects. Both the deployed bundle and binary
are hash verified, and receipts record the two paths. These files are diagnostic
artifacts; no installed app or boot configuration is replaced.

This change alone did not resolve the real Controller entropy failure; see
`validation/userdata-bundle-camera-failure-arm.json`. The separate grayscale
sample experiment also failed and stays test-only
(`validation/controller-entropy-luma-experiment-arm.json`).


### Entropy capture wipe interruption

Both explicit wipe interruption and the original inactivity-timer worker pass
while physical NV12 entropy capture is active. Tests verify original seed-buffer
wipe, cleared image references, camera owner exit 0, zero remaining DMA buffers,
old native UI reaping/restart, and return through the original Controller to Home.
See `validation/entropy-wipe-arm.json` and `validation/entropy-wipe-timer-arm.json`.
The timer test expires its activity timestamp instead of waiting five minutes.
The guarded lifecycle adapter routes its expected interruption without printing
an error traceback; unrelated exceptions retain the original error path.


### Settings QR review and apply

`mise run lvgl:app:hardware settingsqr --bytecode-cache` passes public SettingsQR
parse → review → Cancel, and parse → review → Apply → confirmation → Home.
Original parsing and application remain in the pinned View; the adapter only
provides presentation. No changes occur before Apply; Cancel preserves the
settings dictionary. This diagnostic disables persistence and verifies no file
was written. See `validation/settingsqr-arm.json`. It injects View initialization
and QR text, so optical scan, display-driver changes and the full Controller
route are not qualified by this receipt.


SettingsQR now also passes the original Controller/View initialization for both
Apply and Cancel, with real health/wipe workers and Home return. See
`validation/controller-settingsqr-apply-arm.json` and
`validation/controller-settingsqr-cancel-arm.json`. The subsequent scan-route
check passes a public synthetic NV12 QR through the native frame receiver, Rust
QR worker, original DecodeQR/ScanView, settings review, Apply, confirmation and
Home (`validation/controller-settingsqr-scan-arm.json`). That run substitutes
only the camera source, uses scripted buttons and disables persistence. It does
not qualify optical acquisition, persistent writes or display-driver switching.
Rerun with `mise run lvgl:app:hardware controller-settingsqr-scan --bytecode-cache`.


### Power message presentation

`mise run lvgl:app:hardware power-presentation --bytecode-cache` renders the
original restart and Loader-mode messages using upstream `reset_screen`, and
the unplug message using upstream `power_off_not_required_screen`. The original
PowerOffView's Back route passes with scripted input. Restart and Loader system
commands are not invoked; launcher/restart and boot behavior remain unqualified.
See `validation/power-presentation-arm.json`.


### Text QR entry and transcription

`mise run lvgl:app:hardware textqr --bytecode-cache` passes exact native entry
Save/Back and the original entry → review → generate → transcription → whole QR
→ zoom navigation → Done route to Text QR. Original View escape parsing remains
unchanged; public fixtures cover whitespace, Unicode and CRLF. See
`validation/textqr-arm.json`. View initialization and buttons are injected.
Full-screen mode, optical confirmation, larger TextQR matrices and the combined
Controller flow remain unqualified by this receipt.


TextQR full-screen and scan-confirmation are now separately qualified with
injected View initialization: `mise run lvgl:app:hardware textqr-output-confirm
--bytecode-cache`. Three full-screen outputs decode byte-for-byte from the RGB565
pixels sent to the LCD (spaces, Unicode/CRLF, and longer text), and clear to black
on exit. The original scan-confirmation View passes matching/mismatching/cancelled
synthetic NV12 input, with stopped sources and QR worker exit 0. See
`validation/textqr-output-confirm-arm.json`. This closes the earlier isolated
full-screen/confirmation gap, but does not prove optical camera reading, every
transcription size or full Controller navigation.


### Version and System Info

Original SystemInfoView passes through the real Controller using actual device
reads, native scrollable information and Back to Hardware Settings. VersionView
also passes through the real Controller and upstream `version_screen`, using the
original UTC timestamp formatting. See `validation/controller-system-info-arm.json`
and `validation/controller-version-arm.json`.

The installed image lacks `seedsigner/version.json`; its original VersionView
fails before rendering. The Version test redirects only the original metadata
reader's file path to a temporary public fixture. This does not qualify installed
image provenance. Generating a correct version.json is a mandatory packaging
requirement for the eventual LVGL image. No installed files were modified.


### Live Memory Info

MemoryInfoScreen calls the pinned original `_build_lines` sampler/formatter and
uses its original two-second refresh interval. The existing UI loop sends a
bounded update only when text changes; the upstream button-list label is updated
in place, preserving focus and scroll without a rendering worker.
`mise run lvgl:app:hardware controller-memory-info --bytecode-cache` passed six
real samples and Back to Hardware Settings through the original Controller.
`live-info-protocol` separately checks preserved selection/nonzero scroll and
malformed/inactive-message rejection/recovery. See
`validation/controller-memory-info-arm.json` and
`validation/live-info-protocol-arm.json`. These checks do not qualify long soaks
or whole-app performance.


### Battery Info

Battery Info uses the original BatteryHat read API and original display values/
precision at the original five-second cadence, refreshing the native live label
on the existing UI loop. `controller-battery-absent` passes the real no-monitor
warning/Back route. `controller-battery-fixture` separately passes live values
and Back through the real Controller with a public sensor-API fixture. See
`validation/controller-battery-absent-arm.json` and
`validation/controller-battery-fixture-arm.json`. The latter is display/navigation
qualification, not actual battery/I2C behavior or read latency. No charging or
calibration control changed.


### Hardening report pages

`mise run lvgl:app:hardware controller-hardening --bytecode-cache` passes the
original read-only hardening checks/report through the real Controller, traverses
all five pages with the same report object, and returns to Advanced Settings
after Done. The existing paged-text builder preserves report text/page numbering
and exposes More/Done; native read-first focus permits reading overflowing text
before its action. Evidence: `validation/controller-hardening-arm.json`. This is
UI/report-flow qualification, not a claim that the development image is hardened.


### Network Info

The original network report pager now uses an explicit fixed-width native text
option. Build assets embed the pinned application's Inconsolata-Regular.ttf,
rendered at 16 px through LVGL TinyTTF, with left alignment and explicit line
spacing; source SHA/size are recorded in generated `branding/font.json`.
The public LCD capture was visually checked after rejecting an earlier bitmap
font layout. Original command lookup, page splitting and report caching remain
in the View.

`controller-network-fixture` passes pages and the original return path through
the real Controller using public command-output data. `controller-network-absent`
passes the actual unavailable-command path; this image has no
`/usr/bin/network-info`. Receipts are `validation/controller-network-fixture-arm.json`
and `validation/controller-network-absent-arm.json`. The original last-page Done
returns BackStack (the prior page for a multi-page visit), so Back is needed to
leave earlier pages. This quirk is preserved and documented. Tests now reject
unexpected page order immediately instead of waiting for a navigation timeout.


### Battery calibration screens

Calibration intro, start and running screens now use LVGL. The running adapter
compiles the pinned original `_run`, replacing only its PIL drawing block. Log
format/cadence, charging timeout and deletion/return rules remain original; camera
calls use the private guarded Rust adapter with original request arguments.
Native status updates consume their acknowledgements to keep the event queue
bounded during long runs.

`calibration` passes both setup Back routes and active-camera cancellation with
temporary logs. `controller-calibration` passes setup → running → cancel → Home
through the real Controller. `controller-calibration-charging` passes the original
30-second abort using a positive-current fixture and real wall-clock timing:
437 received frames, 56 status updates, deleted temporary log, camera exit 0,
zero DMA buffers and Home return. See matching receipts under `validation/`.
Battery/card metadata are fixtures. Real battery discharge, electrical charging
detection and calibration-log processing on actual media remain unqualified.


### Donation attribution screen

DonateScreen reuses upstream `donate_screen` with the original donation text and
`seedsigner.com` attribution. The original DonateView passes through the real
Controller and returns to Settings via native Back. See
`validation/controller-donate-arm.json`. This screen has text/URL only in the
pinned fork; no QR payload, payment or browser action is added.

## I/O Test checkpoint

Original Controller camera capture, Clear, reopen and Exit pass on the LCD with
scripted input. Wipe during capture and an entropy-wipe regression also pass.
See DIVERGENCES.md for crop/layout differences, input override fix, scoped
receipts and the remaining hard-timeout cleanup limitation.

## Isolated entry point (development)

`python/app.py` assembles the LVGL adapters and invokes the pinned original
`main.py` CLI. Original installed main.py is now source guarded too. The entry
requires an absolute separate settings filename, refuses competing Python/camera
owners, and has a read-only `--check` mode. Arguments after `--` are passed to the
original CLI. Nothing installs a boot service or changes the installed launcher.

Actual-board preflight passes (`validation/app-entry-check-arm.json`), with no
Controller/hardware import, Settings instance or settings write. Interactive
entry, complete shutdown/signal handling and production service integration still
need dedicated qualification. Do not use this as a release-ready boot launcher.

## First paired Home resource measurement

Same original Controller, small-RAM policy, GPIO script and sample cadence;
physical LCD; eight seconds idle then Settings and back. One warm-device pair,
LVGL first and PIL second, with identical deployed test bundle verified.
Medians use Home seconds 1–7; CPU uses process-tick deltas across that window.

| Metric | LVGL Python | LVGL native | Original PIL Python |
|---|---:|---:|---:|
| RSS (KiB) | 24,768 | 1,520 | 24,900 |
| Anonymous RSS (KiB) | 14,864 | 212 | 14,436 |
| Swap (KiB) | 40 | 0 | 344 |
| Threads | 5 | 1 | 5 |
| CPU (% of one core) | 11.170 | 1.167 | 7.503 |

This does not establish a memory win. LVGL Python RSS is similar, and it adds a
native process. RSS omits swapped pages and shared pages cannot be blindly summed
as total physical RAM. Both paths already share the small-RAM import policy.
The observed idle process CPU is higher with LVGL; polling needs investigation.
These are benchmark-process measurements with script/sampling overhead, one run
order and warm caches, not production CPU averages or cold-start latency.
Camera/QR/signing, repeat pairs, responsiveness and soak remain open.
Evidence: validation/frontend-idle-comparison.json and resources-{lvgl,pil}-arm.json.

### Input idle fast path and second pair

Profiling identified idle input bookkeeping and empty-queue exception handling,
as well as significant scripted-GPIO overhead. The runtime now skips per-key
state work only when no key or pending release/debounce exists, and avoids a
get/exception for an empty event queue. Hardware/lifecycle polling cadence stays
unchanged. Host debounce, short-release and lifecycle tests pass (152 tests).

| Second warm pair | Python RSS KiB | Python swap KiB | Python CPU % | Native CPU % |
|---|---:|---:|---:|---:|
| LVGL | 23,920 | 816 | 8.179 | 0.835 |
| PIL | 25,592 | 624 | 7.673 | — |

LVGL native RSS remains 1,520 KiB. Combined measured process CPU is 9.014%,
versus 12.337% in the earlier run, while PIL remains lower in this pair. This is
not isolated proof of the optimization's size: warm cache/system pressure and
harness changes differ between pairs. It still does not establish a total-memory
win. Evidence: validation/profile-lvgl-idle-arm.json and
validation/frontend-idle-comparison-input-fastpath.json.

### First live-camera observation and comparison tooling

Read-only memory-map accounting of the ongoing interactive app is saved in
`validation/interactive-python-memory-maps.json`. At that instant Python had
19,308 KiB RSS and 4,528 KiB swap; anonymous mappings plus heap accounted for
13,288 KiB RSS and 3,884 KiB swap. The libpython mapping contributed 3,740 KiB RSS.
Most Pillow native-library pages were not resident. This is an uncontrolled
interactive observation, not a before/after comparison or object attribution.
It corrects any implication that old rendering libraries alone explain most
Python memory. Library-owned Python objects can still reside in anonymous heap.

`mise run lvgl:app:memory-maps --pid PID` reads this accounting without launching
another Python on the board or accessing object values. It validates the target
interactive entry and process identity, omits addresses and private filenames,
and optionally saves the sanitized report with `--output PATH`.

`validation/resources-lvgl-camera-arm.json` records a warm original-Controller
Home → live scan → Home run on the physical LCD. The camera workload suppresses
payload completion, holds Back after fifteen seconds and observes no remaining
camera/QR owners or DMA objects after exit. No QR values or frames are saved.
The initial brief Back tap was unreliable under preview load; that failed
diagnostic and the invalid stock-V4L2 baseline are retained as failure evidence.
The corrected original-frontend harness explicitly installs the pinned Rust
camera/QR integration and Rust LCD transport. Matching-bundle runs now pass for
both frontends; frontend-camera-comparison.json records the first pair. That
pair does not establish a total-memory win: LVGL Python has slightly lower RSS
and swap, but adds a native UI process and leaves less system MemAvailable.
The full public multisig flow also passes under the new dependency policy
(dependency-wallet-flow-arm.json), including verified signature and QR bytes.

During the successful LVGL preview window (seconds 5–14), median Python RSS was
16,050 KiB with 4,440 KiB swap; native UI RSS 1,660 KiB, camera owner 7,814 KiB,
QR worker 824 KiB. DMA reported one 3,981,312-byte object; median system
MemAvailable was 7,816 KiB. These values cannot be summed as total physical RAM.
Sampling includes significant harness overhead. No FPS/latency or production
memory improvement is established. See frontend-camera-lvgl-observation.json.

Preview input had a measured bottleneck: the native loop slept 5 ms after each
4 KiB read, including busy preview reads. It now backs off only on non-ready
reads, preserving timer service and idle cadence. Headless host preview median
falls from 195.3 ms to 6.5 ms; physical display round trips measure 136.9 ms.
The first instrumented camera run completes 45 cycles versus the earlier 28,
with 3.39 completed previews/second between first/last completion. Most remaining
time is preview acknowledgement/display output. This is not a 30x camera-FPS
claim or a memory improvement. Stage timing and matched resource evidence:
resources-lvgl-camera-fast-input-arm.json and
frontend-camera-fast-input-comparison.json. SPI coordinate batching is the next
independently checked change; the earlier numbers precede that change.

Coordinate batching subsequently passes unit wire checks, the native 320-column
fake-SPI pipeline and physical display output (131.5 ms median). The sampled
scan measures 3.78 completion fps. Separately, the tools-loaded camera case
without resource sampling passes two 30-second reopen/cancel scans at 4.85 fps,
owner exit 0 and zero remaining DMA buffers. See
`validation/camera-fast-preview-soak-arm.json`. This is bounded camera lifecycle
coverage with scripted input, not optical QR-vector or long-soak qualification.

Reproduce reports with `mise run lvgl:app:resources RECEIPT.json`; add a second
receipt for a comparison. The tool rejects failed/unclean runs, changed sources,
unverified deployment, mismatched bundles/binaries/workloads and unstable sampled
process owners. It reports CPU from counter deltas and keeps resident memory,
anonymous memory, swap, thread counts and DMA separate. The next camera runs
also require explicit successful QR-frame processing counters.

### Native artifact manifest at entry

The isolated entry now requires the native build manifest as well as its binary.
Default is `BINARY.manifest.json`; `--native-manifest PATH` selects another path
(such as the host build's `dist/lvgl-app/build/build-manifest.json`). The temporary
hardware runner deploys the sidecar and verifies its contents against the exact
local build manifest. Entry checks ARM musl target metadata and streaming SHA256
before hardware setup. Missing/mismatched metadata fails preflight.
Actual-board positive and deliberate wrong-binary preflight pass without opening
hardware (`validation/app-entry-native-manifest-arm.json`). Host suite: 155 tests.
Image/service packaging and full interactive requalification remain open.

The actual entry route also passes with manifest verification. Shutdown now calls
original Settings.flush_save after worker stop attempts. A board test confirms a
still-pending deferred change is persisted to isolated settings at exit while the
original settings file remains unchanged
(`validation/app-entry-settings-flush-arm.json`). The change was injected by the
diagnostic; full settings-UI persistence and failure/boot/service cases remain.

Actual original settings UI persistence also passes: enable Persistent settings,
select sats denomination, Back to Home, flush pending change at entry shutdown,
and reload both values with the original Settings reader. No setting-value
assignment is injected in that case. The original settings file remains unchanged;
only isolated temporary JSON is used
(`validation/app-entry-settings-ui-arm.json`). Reboot/SD durability and other
setting types/failure paths remain separate checks.

ST7735 selection through original Controller/settings UI also passes on ARM with
fake LCD drivers: logical 240×240 stays fixed, physical target changes
240→128→240, scaled frames reach the driver and old accumulator clears before
release (`validation/st7735-settings-ui-arm.json`). Physical 128×128 hardware and
optical/gesture/fault checks remain open.


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

# Firmware source and evidence inventory

Audit snapshot: 2026-10-31, after the canonical artifact migration. This is a
checkpoint review of `firmware/lvgl-app/` and `firmware/lvgl-demo/`, not a firmware
release audit. It does not change runtime code, source pins, tests or receipts.

## What belongs in the source checkpoint

| Path | Classification | Keep / maintenance boundary |
|---|---|---|
| `firmware/lvgl-app/python/` | 51 Python runtime/adaptation files | Deliberate source; source guards, import policies and checked caches preserve the upstream algorithm boundary. Never include its `__pycache__/`. |
| `firmware/lvgl-app/native/` | 1 C++ file and 7 headers | Native renderer/protocol source, configuration and embedded asset source. Text headers are intended build inputs, not compiled binary leakage. |
| `firmware/lvgl-app/patches/` | 17 patches + one SDK predecessor text | Preserve exact portability changes and the reviewed strip-function predecessor. |
| `firmware/lvgl-app/licenses/` | Notices and font metadata | Preserve original bytes and provenance. Unresolved grants remain explicit; see below. |
| `firmware/lvgl-app/tests/` | 152 Python files + one SDK text fixture | Public contracts, synthetic fixtures, ARM harnesses and earlier experiments; [runner/fixture index](../firmware/lvgl-app/tests/README.md). |
| `firmware/lvgl-app/validation/` | 295 curated JSON receipts | Deliberate evidence, including failures; [complete index](../firmware/lvgl-app/validation/README.md). Fresh raw logs belong in ignored checks. |
| LVGL app top-level tooling | Build, assets, licenses, packaging, staging, resource and diagnostic tools | Required to reproduce/develop the source. Host tools are distinct from files shipped under `python/`. |
| `source-guards.json`, `sources.lock.json`, `locale-builder.lock.json` | Source/recipe identity | Keep exact pinned identities; do not update as a side effect of organization work. |
| `firmware/lvgl-app/service/` | Launcher source | Source, not an installed service or proof of activation. |
| App README / focused docs / coverage / divergence history | Current guide and historical evidence | Preserve claims and chronology when splitting docs. English-only current work does not require deleting existing locale source or tests. |
| `firmware/lvgl-demo/` | 8 source/docs files at audit start | Historical standalone hardware demo, not the wallet frontend. Retain separately; generated executable/captures live under `dist/firmware/work/lvgl-demo/`. |
| `scripts/firmware_paths.py`, `scripts/firmware-artifacts.py`, related mise/image hooks and tests | Cross-tree integration | A recoverable checkpoint needs these alongside the app, rather than only committing the app directory. Review as a coherent tooling change. |

Counts exclude ignored Python caches and will change as documentation is split.
The audit found 583 Git-visible untracked app/demo files during that split; the
stable test/evidence counts above are more useful than the changing total.

## Pinned source dependencies

The authoritative list is [sources.lock.json](../firmware/lvgl-app/sources.lock.json).
These are fetched checkouts, not vendored directories to add to Git:

| Lock key | Upstream | Commit |
|---|---|---|
| `application` | `3rdIteration/seedsigner` | `efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f` |
| `screens` | `kdmukai/seedsigner-lvgl-screens` | `33ddc0763c31b5ae0b6380147ba624a7fc0c9273` |
| `lvgl` | `lvgl/lvgl` | `85aa60d18b3d5e5588d7b247abf90198f07c8a63` |
| `reference_bindings` | `kdmukai/seedsigner-raspi-lvgl` | `1cb456500e6adcb09801a88d386fa0dc1134c1ec` |
| `reference_app` | `kdmukAI-bot/seedsigner` | `fd9ba8fc766f715668bc37fbb5485499def9e52f` |
| `language-packs` | `kdmukAI-bot/seedsigner-language-packs` | `a9e39dabf60e093bb3d1494eb4728f83342c878b` |

`sources.py` enforces pinned revisions and clean checkouts. Build provenance also
hashes native/patch inputs, local build tooling and shared `scripts/firmware_paths.py`.
Keep those guards. The demo separately pins the same LVGL commit in `build.py`.

## Source/privacy and generated-data findings

The filename/content review covered the app/demo trees, excluding ignored cache
files. Every non-cache file was UTF-8 text; no binaries, symlinks, sensor pictures,
framebuffer captures, PDFs, STEP files, Telegram sessions/history or OS build
outputs appeared in those trees. Header-embedded graphics are intentional source.

A narrow scan found **zero matching files** for private-key blocks, common token
formats and credential assignments, operator home/SSH targets, or private/tailnet
IPv4 literals. Recursive receipt-field checks found no nonempty fields named
`mnemonic`, `passphrase`, `private_key`, `password`, `host` or `serial` (including
other common equivalent names). Values were not printed in the scan report.
These checks identify common leaks; they do not establish that every arbitrary
log string is safe or that keys disguised in other forms cannot exist.

Public wallet literals are deliberate fixtures, not unexpected wallet files:
[multisig_fixture.py](../firmware/lvgl-app/tests/multisig_fixture.py) explicitly
identifies upstream regtest data and its source SHA. Synthetic QR/frame helpers
build known public pixels in memory. Preserve these fixture labels and never
replace them with a user's seed, passphrase, PSBT or photographs.

At audit time 240 Python cache files were excluded by the existing `__pycache__/`
rule. `dist/` already excludes canonical sources, compiler work, staging, image
binaries, checks, jobs and archives. No narrowly proven ignore leak required a new
local `.gitignore`. Existing PDF/STEP Git LFS policy remains unchanged.

## Evidence and qualification boundaries

All 295 JSON receipts parse: 248 top-level passes, 29 failures, 18 without a
top-level `passed` flag. The [evidence index](../firmware/lvgl-app/validation/README.md)
lists every receipt once and separates build/memory baseline, failures,
host/notice checks, resource history and workflow history. Failure receipts are
useful regression evidence, not cleanup garbage.

The frozen image remains `lvgl-dev.cb6170a37a5a`. Its build-time receipts retain
original `flashed: false` / boot-unqualified claims. Later user-reported boot,
LVGL UI and camera success is separate acceptance metadata in the image store.
Real-wallet acceptance is pending. None of this audit reruns optical tests,
changes wallet logic, adds smartcard work or upgrades license qualification.

The [notice inventory](../firmware/lvgl-app/licenses/README.txt) and
[notice audit](../firmware/lvgl-app/validation/notice-audit-host.json) explicitly
record two unresolved upstream issues: the pinned screen repository lacks a
top-level grant, and `seedsigner-icons.otf` lacks embedded copyright/license
records. Existing app/OS dependency licenses are a separate image-level concern.
Keep `licenseClosureVerified=false`; obtain applicable terms before claiming
redistribution closure. Preserving the development source and notices is not
such a claim.

## Actionable next checkpoint steps

1. Include the app/demo source, patches, locks, notices, tests, curated receipts
   and integration tooling in explicit reviewed path sets. Avoid blanket staging;
   unrelated hardware/site changes require their own review.
2. Review the documentation split as one coherent navigation change. Preserve
   historical evidence links and distinguish old receipts from current commands.
3. Treat `record-checkpoint.py`, `record-passphrase.py` and `record-camera.py` as
   **historical snapshot writers**. They contain fixed dates/test counts and write
   directly to existing curated receipt filenames. Do not rerun them to claim
   current qualification. A future cleanup can archive or replace them with a
   named-output recorder; no source move is needed for this checkpoint.
4. The standalone demo guide now uses `dist/firmware/work/lvgl-demo` and clearly
   labels that experiment as superseded by the app frontend. Temporary aliases
   preserve earlier artifacts, but should not become new defaults.
5. Keep captures from `render_rgb565.py`, demo `capture.py` and physical entropy
   harnesses in ignored checks/work directories. A command accepting an explicit
   destination can bypass an otherwise safe default; never copy private captures
   into curated evidence or the public website.
6. Before a public checkpoint, repeat the filename/redacted-value review on the
   **actual proposed file set**. The scan above is a dated snapshot, not a blanket
   approval of future logs. No files have been staged or committed by this audit.

See [artifact lifecycle](FIRMWARE-ARTIFACTS.md) for image discovery and frozen
verification, and [cleanup goal](REPO-CLEANUP-PLAN.md) for the remaining phases.

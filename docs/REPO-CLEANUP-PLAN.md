# Repository cleanup goal

Make this repository easy to navigate, build and review while preserving the
working firmware and hardware designs. Begin with firmware artifact sprawl:
there must be one obvious place to find a verified flash image, one named staging
area per build, and a clear separation between sources, reusable work data,
checks and historical artifacts.

This cleanup changes repository organization and tooling. Device behavior,
production import paths, Rust crate names, source pins, upstream attribution and
licenses stay stable. Dependency upgrades, new firmware features, another flash,
translation work and smartcard development belong to separate tasks.

## Preserve the working baseline

The current flashed firmware is `lvgl-dev.cb6170a37a5a`. The user confirmed boot,
LVGL usability and a camera scan. Automated public-fixture signing/export checks
have passed. End-to-end acceptance with the user's own wallet remains pending;
wallet availability does not block this cleanup.

| Artifact | SHA-256 |
|---|---|
| Compressed image | `834b2ca4d24055dbc533997e43e92bb54932e75c49dff27698316a51a6859853` |
| Raw image | `e605e47ab21dc4785a24ee356966b8cf649fe1716248de126cfce9605601e862` |

Keep the image, checksums, packed verification report, runtime manifest and build
provenance together. Historical receipts retain their original identities and
claims. A cleanup commit must not relabel the flashed image as a newly built or
newly qualified release.

## Current execution status

The canonical path helper, producer defaults, image-management commands and mise
entry points are implemented. Migration moved 68 artifact paths and preserved a
source checkpoint. Baseline hashes, compressed/raw correspondence and frozen
runtime/overlay/camera provenance verify. All 245 LVGL host tests pass after the
move. All 55 compatibility aliases resolve correctly; 18 artifact-tool tests,
the canonical native host build and all nine native protocol groups pass.
The host rebuild left all 2,170 frozen image/staging file hashes unchanged.
Phase 1 is complete. The follow-up cleanup also completed the source checkpoint
review, current/history documentation split and test/evidence indexing in phases
2–4. The reviewed firmware/tooling source is committed; no generated image,
private capture or build cache is included. The LVGL README is now a short entry
point, with focused architecture/build/memory/acceptance guides and both full
notebooks preserved under `docs/history/`. All 295 JSON receipts are indexed
exactly once, including historical failures. See the
[source inventory](FIRMWARE-SOURCE-INVENTORY.md) for reviewed boundaries and the
[test map](../firmware/lvgl-app/tests/README.md) for runner scope.

Phase 5 remains selective maintenance, not a blanket deletion pass. Source pins,
licenses and useful compiler/SDK caches are retained. The known historical
recorder scripts remain explicitly labelled rather than being rerun or silently
rewritten. No new OS image or board flash was required.

## Phase 1: establish the artifact lifecycle

Use the [canonical firmware layout](FIRMWARE-ARTIFACTS.md) under
`dist/firmware/`. Migrate existing data without broad deletion and retain
compatibility aliases while older scripts or receipts still reference them.

- Put user-facing verified images only in `images/<version>/`.
- Put each build's runtime, overlay and combined camera bundle in one
  `staging/<build-id>/` directory.
- Keep source checkouts, reusable compiler/SDK work, check output and remote job
  metadata in their dedicated directories.
- Update producer defaults, collection/verification tools and mise entry points
  together. Explicit output overrides remain available where already supported.
- Provide `firmware:where`, `firmware:verify` and `firmware:stage` entry points.
  Finding the current image must not require knowing an old attempt directory.

**Acceptance:** the current-image command resolves one canonical image directory;
its raw and compressed hashes match the baseline; frozen manifests still verify;
new staging and build outputs use the new hierarchy; legacy aliases resolve to
preserved data rather than duplicate copies. No image is silently promoted merely
because it is the newest file.

## Phase 2: make the source checkpoint reviewable

At the start of this cleanup, `firmware/lvgl-app/` and `firmware/lvgl-demo/` were
untracked, alongside changes to mise and image integration scripts. Review that
work before staging it for future coherent commits.

- Inventory intended source, patches, pins, licenses, tests and accepted evidence.
- Review private-data boundaries before Git staging. Exclude credentials,
  Telegram sessions/history, private infrastructure settings, captured wallet or
  camera data, build caches and image binaries. Do not print secret values during
  scanning; review filenames and redacted findings.
- Preserve deliberate public fixtures and upstream notices. PDFs/STEP references
  continue to use the established Git LFS policy.
- Prepare separate reviewable changes for the baseline firmware, artifact tooling
  and documentation. Avoid a blanket `git add .` or unrelated hardware edits.

**Acceptance:** every proposed file has a source/evidence purpose; generated and
private data are excluded; attribution and pins are preserved; the working source
can be recovered independently of disposable build caches.

## Phase 3: separate current documentation from the lab notebook

The starting LVGL README was about 1,883 lines and DIVERGENCES about 3,322 lines.
Their chronological evidence is useful, but it obscures the current instructions.

- Keep a short firmware entry README with architecture, current status, build/test
  commands, image discovery and links to evidence.
- Extract current build/flash, memory, upstream-divergence and acceptance guides
  into focused documents. Move earlier chronology into clearly marked history.
- Reconcile coverage labels from actual adapters and receipts: implemented,
  automated fixture checked, user reported, or still pending. Rendering a screen
  is not equivalent to completing a wallet or physical hardware workflow.
- Use one authoritative current-image index. Other docs link to it rather than
  independently naming whichever image was current when they were written.
- Preserve root navigation for firmware, native KiCad variants, enclosure,
  sourcing and the static website. Keep historical hardware variants distinct.

**Acceptance:** a new reader can locate the current image and its qualification
status from the root README; historical material is reachable; links and current
commands resolve; pending wallet acceptance remains visible.

## Phase 4: classify tests and evidence before moving them

The starting LVGL tree contained roughly 153 test/fixture files and 295 validation
receipts. First index them by purpose: host unit tests, host native protocol tests,
board fixtures, immutable build/image checks and historical investigations.

- Separate current acceptance evidence from historical experiments through an
  index and explicit status labels.
- Retain failure receipts that explain a regression or support a negative test.
  Archive with provenance instead of deleting everything marked failed.
- Move test files only after updating runner discovery, helper imports, source
  guards and relative paths together. Keep public fixture payloads explicit.
- Leave production Python, native runtime and Rust crate layouts alone during
  the first cleanup. Renaming them adds behavior risk without fixing image sprawl.

**Acceptance:** tests are discoverable by purpose; no runner quietly loses cases;
retained receipts have a reason and scope; existing fixture behavior still passes.

## Phase 5: simplify maintenance and prune deliberately

Group related mise tasks and move long inline implementations into named scripts
where useful, while retaining familiar command names. Add ignore rules only for
known generated data. After reproducibility and references are checked, remove
specific obsolete duplicates or failed partial outputs.

Keep reusable SDK/compiler/download caches and at least one verified baseline
image. Do not run a blanket deletion of `dist/`, vendor snapshots, reference
research or manufacturing outputs. Keep image binaries out of ordinary Git
history; any future release publication is a separate explicit action.

**Acceptance:** the documented build/verification paths work, relevant host tests
pass, artifact hashes are unchanged where preservation is required, and a final
inventory distinguishes source, current artifacts, reusable work and archive.

## Execution order and stopping conditions

Finish and verify one phase before broadening file moves. Commit boundaries should
make organization changes distinguishable from prior functional firmware work.
If a path move exposes a behavior change, fix or isolate it before proceeding.
Do not require a real wallet, alter the flashed device, or repeat expensive OS
builds just to validate a documentation-only change. Use public fixtures for any
necessary automated signing regression.

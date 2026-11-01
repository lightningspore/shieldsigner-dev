# Firmware artifacts

The canonical user-facing home for verified flash images is: **`dist/firmware/images/`**.
Use `mise run firmware:where` to find the current image and
`mise run firmware:verify` to check its recorded identity. The `images/current`
convenience symlink selects the current version; a newly generated image is not
current until it has been verified and deliberately selected.

**Rollout status:** 68 artifact paths have been migrated. The baseline image,
its compressed/raw correspondence and frozen runtime/overlay/camera provenance
verify in their canonical locations. A pre-migration source checkpoint and move
journal are retained under `archive/` and `legacy-paths.json`. No device changes
or new OS image were needed.

All directories below are generated local data under the existing ignored
`dist/` tree. Source code and curated documentation remain outside this tree.

```text
dist/firmware/
├── sources/
│   ├── lvgl/<pinned-repository>/
│   └── seedsigner-os/
├── work/
│   ├── lvgl/                  # compiler output, reusable build data
│   └── os/<job>/              # OS build output, before image promotion
├── staging/<build-id>/
│   ├── runtime/
│   ├── overlay/
│   └── camera-bundle/
├── images/<version>/          # verified flash files and their provenance
├── checks/                    # generated host/board check output
├── jobs/                      # remote build job metadata
└── archive/                   # preserved superseded attempts and snapshots
```

## What belongs where

| Area | Purpose | Retention rule |
|---|---|---|
| `sources` | Exact pinned upstream checkouts | Reusable inputs; preserve pins and notices |
| `work` | Compiler objects, SDK output and intermediate files | Disposable only through targeted cleanup; retain useful caches |
| `staging` | Immutable inputs for one named build | Never overwrite an existing attempt |
| `images` | Verified `.img` / `.img.xz`, checksums and reports | Keep the working baseline and its identity together |
| `checks` | Generated logs and metadata-only test output | Promote useful evidence to curated validation with its scope |
| `jobs` | Build identity, location and status records | A PID/log record alone does not prove a live or successful build |
| `archive` | Older attempts still needed for provenance/reproduction | Review references before pruning |

An SDK may produce an intermediate image in `work/os/<job>/`. That file is not
the user-facing flash candidate. Verification and collection place accepted
artifacts in `images/<version>/`, alongside their checksum and packed verification
report. Avoid copies in miscellaneous staging or download directories.

## Current working baseline

Version: **`lvgl-dev.cb6170a37a5a`**.

The image is `shieldsigner-lvgl-dev-cb6170a37a5a.img.xz`; the decompressed `.img`
has the same stem. The compressed image is 64,329,836 bytes; raw image size is
363,778,048 bytes. An image-aware flasher can consume `.img.xz`; a raw-device write
must use the decompressed `.img`.

| Form | SHA-256 |
|---|---|
| `.img.xz` | `834b2ca4d24055dbc533997e43e92bb54932e75c49dff27698316a51a6859853` |
| `.img` | `e605e47ab21dc4785a24ee356966b8cf649fe1716248de126cfce9605601e862` |

Packed readback and ARM userspace smoke tests passed. The user subsequently
confirmed boot, a usable LVGL UI and camera scanning. These are separate from
end-to-end acceptance with a real wallet, which is pending. Automated public
wallet signing/export fixtures already passed; the cleanup does not require the
user to have a wallet handy.

## Commands and migration

- `mise run firmware:where` prints JSON containing the selected version, directory,
  compressed image, raw image and verification report. Selection lookup does not
  hash the image; use the verification command before relying on its identity.
- `mise run firmware:verify` checks the current image hashes, sizes and packed
  verification report. `mise run firmware:verify <version>` checks a named image.
- `mise run firmware:stage -- --name <unique-build-id>` builds the LVGL app and
  prepares its runtime, overlay and combined camera bundle in one staging area.
  It does not build an OS image or flash the board. By default it uses the current
  image record's camera base; `--camera <bundle-directory>` overrides that input.
  An existing staging name is rejected. Use `mise run firmware:stage -- --help` for
  the CLI options. Task arguments are forwarded to the underlying command.
- `mise run firmware:test` runs isolated artifact-management tests without
  building an OS image or accessing a device.

Builds keep their established source pins and existing task names. New producer
defaults use this layout. Explicit output overrides remain supported where they
were already part of a tool's interface.

The old `dist/lvgl-app` and `dist/os` locations are temporary compatibility
aliases. They keep earlier scripts and historical receipt paths usable during
migration;
they are not additional homes for new flash images. Do not create new candidate
directories there or rewrite the identity inside an old receipt to make it look
current. Remove aliases only after callers and references have been migrated.

See the [repository cleanup plan](REPO-CLEANUP-PLAN.md) for phased work and
acceptance checks, and the [LVGL guide](../firmware/lvgl-app/README.md) for runtime
architecture and the detailed validation record.

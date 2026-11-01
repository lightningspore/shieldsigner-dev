# ShieldSigner LVGL frontend

The development image boots with LVGL by default. The user confirmed usable UI
and camera scanning on the Luckfox Pico Mini. **Real-wallet end-to-end acceptance
and production qualification remain pending.** Current scope is English, with no
smartcard feature work. The tested hardware uses the standard 240×240 display/
button board and base-fork pinout; this does not qualify the 2.8-inch carrier.

The port reuses pinned SeedSigner LVGL screens in a native C/C++ renderer while
keeping the pinned ShieldSigner Python Controller, Views and wallet models.
The Rust camera/LCD runtime and native ZXing-C++ QR reader remain part of the image.
This is a frontend migration, not a complete rewrite of the wallet in Rust.

## Find the tested image

```sh
mise run firmware:where
mise run firmware:verify
```

Current identity: `lvgl-dev.cb6170a37a5a`.

```text
dist/firmware/images/lvgl-dev.cb6170a37a5a/
  shieldsigner-lvgl-dev-cb6170a37a5a.img.xz
  shieldsigner-lvgl-dev-cb6170a37a5a.img
  image.json
```

The compressed image is 64,329,836 bytes; the raw image is 363,778,048 bytes.
Etcher can select the `.img.xz` directly. Raw-device writers need the decompressed
`.img`. Flashing is the last step, after verification and deliberate selection.
These commands do not flash or operate the device.

`firmware:verify` checks both image files, streams XZ to reproduce the raw digest,
and checks the frozen runtime/overlay/camera provenance against the packed report.
It verifies the selected artifact without requiring today's source to reproduce
its historical build-input hashes.

## Read by topic

| Topic | Guide |
|---|---|
| Processes, rendering, camera and upstream boundaries | [Architecture](docs/ARCHITECTURE.md) |
| Build, stage, verify and artifact locations | [Build workflow](docs/BUILD.md) |
| Measured memory, improvements and retained dependencies | [Memory](docs/MEMORY.md) |
| What passed and what still needs acceptance | [Acceptance](docs/ACCEPTANCE.md) |
| Current departures from pinned upstream | [Divergences](DIVERGENCES.md) |
| Screen inventory and scoped evidence | [Coverage](COVERAGE.md) |
| Test runners, hardware fixtures and public payloads | [Test map](tests/README.md) |
| Current checks versus historical investigations | [Evidence index](validation/README.md) |
| Repository artifact layout | [Firmware artifacts](../../docs/FIRMWARE-ARTIFACTS.md) |

## Current evidence

The post-layout-cleanup host suite passes **245 tests**. Frozen runtime verification
passes for 253 files / 5,469,515 payload bytes; overlay verification passes for
256 files / 5,471,787 bytes. The artifact relocation did not rebuild the frozen
image or change its device behavior.

Packed verification covers the Mini DTB, 12 MiB CMA, overlay/source-cache bytes,
launchers and ARM userspace smoke tests. The user's boot/UI/scan observations are
physical evidence, separate from static readback and QEMU checks.

- [Image build receipt](validation/image-memory-cleanup-built.json)
- [Packed image verification](validation/image-memory-cleanup-packed.json)
- [Memory cleanup acceptance](validation/memory-cleanup-acceptance.json)
- [Packaged cache memory comparison](validation/packaged-source-cache-memory-summary.json)

Python private anonymous RAM plus swap was 10.75 MiB at Home, 13.26 MiB during
live scanning, and a maximum sampled 16.31 MiB in the measured transaction flow.
Those are scoped Python-process observations, not total-device RAM or universal
peak guarantees; see [Memory](docs/MEMORY.md).

## Development boundaries

Pinned inputs are in [sources.lock.json](sources.lock.json); source fingerprints
are in [source-guards.json](source-guards.json). Source checkouts stay clean.
Portability patches apply to a disposable build copy. Packaging preserves source,
ABI, file-hash and cache guards. Original wallet/encoding/entropy algorithms remain
authoritative; scoped public fixtures do not establish real-wallet acceptance.

Generated files live under `dist/firmware`: source checkouts, disposable work,
staging, verified images, checks, jobs and archives have separate locations.
Pass explicit `--output` when staging a new artifact. Never edit a frozen staging
bundle or reuse an existing staging name to represent different bytes.

## Historical evidence

The former chronological documents remain intact in
[README notebook](docs/history/README-notebook.md) and
[Divergence notebook](docs/history/DIVERGENCES-notebook.md). Their checkpoint
statements can describe superseded behavior or earlier acceptance limits.
Existing `validation/` receipts remain in place, including their recorded
historical paths. Compatibility aliases preserve those paths during cleanup.
The earlier standalone experiment remains under `firmware/lvgl-demo`.

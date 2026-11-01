# Current firmware: LVGL, Python and the Rust camera

The current bench image is **`lvgl-dev.cb6170a37a5a`** for Luckfox Pico Mini
microSD boot. Bench testing confirmed boot, usable LVGL screens and camera QR
scanning through direct user observation. Automated public-fixture tests cover transaction review, change verification,
signing and QR export. End-to-end acceptance with a real wallet remains pending.
This is a development checkpoint, not a production release.

The tested setup uses the standard **240×240 display/button board** and the
`base-fork` pin profile. The website's eight-pin 2.8-inch pill carrier is a
separate hardware build. Its LCD wiring, buttons and UR2 reader require matching
configuration and physical bring-up; the bench result does not qualify that PCB.
Smartcards and additional languages were outside this LVGL test scope.

## What runs where

| Layer | Responsibility |
|---|---|
| Linux / Buildroot | Boot, memory management, sensor/ISP drivers, SPI, GPIO and process isolation |
| Python application | Original SeedSigner/ShieldSigner navigation, wallet state, transaction review/signing logic and QR-format assembly |
| Native LVGL renderer | C/C++ screen layout, fonts, display rendering and live preview, driven by the Python application |
| Rust camera process | Controls the SC3336 sensor and ISP through existing Linux interfaces, including exposure and white balance |
| Native ZXing-C++ worker | Decodes grayscale camera pixels and returns original QR bytes, including binary payloads |

LVGL replaces the presentation path; it does not replace the Python wallet
application. The camera and decoder are separate processes. The normal direct
QR path avoids JPEG encoding/decoding, keeps binary payloads intact, and leaves
animated QR assembly to the application. This is ZXing-C++, not a Rust QR decoder.

The Rust camera path does not link or call the vendor RKAIQ userspace library.
It still uses Linux drivers and the Luckfox/Rockchip SDK build. This is not a
Linux-free image or a claim to reproduce every RKAIQ feature, sensor or ISP mode.
Pillow remains for still-image/entropy work and other retained consumers; moving
screen drawing to LVGL does not remove all Python image dependencies.

## Evidence and its limits

| Check | Result and scope |
|---|---|
| Packed image | Hashes, readback and ARM userspace smoke checks passed; emulation alone does not test a display or camera |
| Real device | User reported boot, LVGL usability and camera scanning on the bench setup |
| Signing logic | Public-fixture transaction review, change verification, signature and export checks passed |
| Settings and entropy | Packaged-runtime hardware checks passed, including settings save/reload and camera/RNG seed creation/wiping |
| Host renderer after repository cleanup | Nine native protocol groups passed using canonical source/work paths |
| Personal wallet acceptance | Pending; public fixtures do not replace this end-to-end check |
| Pill carrier, 2.8-inch LCD and smartcards | Not qualified by the bench firmware results above |

This separates a rendered screen, an automated fixture and a user-observed
hardware result. The remaining acceptance work includes a complete wallet
handoff and physical testing of each intended hardware profile.

## Memory: what was actually measured

The Mini has 64 MiB physical RAM. In the measured Linux configuration, about
45 MiB is reported as `MemTotal`, with 12 MiB reserved for camera DMA and roughly
7 MiB in other platform/kernel reservations that remain incompletely attributed.
Compressed RAM swap uses RAM too;
its logical swapped-byte count is not additional physical memory.

Recent isolated hardware observations used the packaged LVGL runtime on the
240×240 bench setup. The cache comparison simulated first-boot source compilation
with isolated cache prefixes; it was not a measured physical-reboot comparison.
These are workload measurements, not maximum allocations or an all-process total:

| Measurement | Observed value | Meaning |
|---|---:|---|
| Python at Home, shipped bytecode cache | 11,012 KiB | Private anonymous RAM plus logical swap |
| Python during camera preview, shipped cache | 13,576 KiB | Same metric; 57 preview frames processed and clean stop |
| Source-compilation control, Home / preview | 12,308 / 14,084 KiB | Same workload without the ordinary shipped cache: 1,296 / 508 KiB higher |
| Native LVGL private RAM, Home | 92 KiB | Real-camera comparison after preview-buffer lifecycle cleanup |
| Native LVGL private RAM, active preview | 356 KiB | Unchanged in that comparison; active preview still needs its buffer |

These rows come from separate scoped comparisons. Do not add them together or
call them total device RAM. RSS includes shared pages; PSS apportions shared
pages; private anonymous RAM plus swap also includes logically swapped data.
The [memory and threads guide](/guides/memory-threads/) explains those distinctions
and labels older Python-renderer snapshots separately.

The wins came from delaying optional imports, releasing disposable source/input
buffers, avoiding needless preview-buffer writes and shipping checked-hash
bytecode for unchanged sources. One earlier QR executable-hash fix lowered an
isolated startup peak by 7.82 MiB through chunked reads; that is a transient peak
saving, not a permanent reduction during scanning. Import-chain reductions
likewise are not interchangeable with running-app memory savings.

## Find and verify the local image

From the repository root:

```sh
mise run firmware:where
mise run firmware:verify
```

`where` reports the selected image paths; `verify` hashes its files and checks the
recorded packed evidence. The canonical home is `dist/firmware/images/`, selected
through `images/current`. The image is a **local build artifact**; this website
does not publish a firmware binary download.

| Artifact | SHA-256 |
|---|---|
| `shieldsigner-lvgl-dev-cb6170a37a5a.img.xz` | `834b2ca4d24055dbc533997e43e92bb54932e75c49dff27698316a51a6859853` |
| Decompressed `.img` | `e605e47ab21dc4785a24ee356966b8cf649fe1716248de126cfce9605601e862` |

Hashes identify these exact files, not another build. An image-aware flasher can
accept `.img.xz`; a raw block-device writer requires the decompressed `.img`.
Use the [flash checklist](/build/flash/) to verify the profile before writing.

## Iterate without another full OS build

The desktop renderer can be built and tested without touching a device:

```sh
mise run lvgl:app:build:host
mise run lvgl:app:test:host
mise run firmware:test
```

For a named ARM runtime/overlay staging area, use the current camera base or pass
an explicitly reviewed camera bundle. This step builds application inputs; it
does not build or flash an OS image:

```sh
mise run firmware:stage -- --name my-lvgl-iteration
```

Outputs go to `dist/firmware/staging/<name>/`; compiler work stays in
`dist/firmware/work/`. Frozen baseline inputs and images are preserved. Use a new
name for each attempt. Keep SDK/download/compiler caches and inspect actual
launcher/container state plus terminal exit status for remote image jobs.
See [compile](/build/compile/) for the next boundary, and the
[artifact lifecycle](https://github.com/lightningspore/shieldsigner-dev/blob/main/docs/FIRMWARE-ARTIFACTS.md)
for paths and preservation rules.

## Source and evidence

Implementation and detailed evidence live in the public repository:

- [LVGL architecture and validation record](https://github.com/lightningspore/shieldsigner-dev/tree/main/firmware/lvgl-app)
- [Rust camera source and supported scope](https://github.com/lightningspore/shieldsigner-dev/tree/main/firmware/rkaiq-rs)
- [Packaged-cache memory comparison](https://github.com/lightningspore/shieldsigner-dev/blob/main/firmware/lvgl-app/validation/packaged-source-cache-memory-summary.json)
- [Native preview memory comparison](https://github.com/lightningspore/shieldsigner-dev/blob/main/firmware/lvgl-app/validation/native-preview-memory-summary.json)
- [Memory-cleanup acceptance and limitations](https://github.com/lightningspore/shieldsigner-dev/blob/main/firmware/lvgl-app/validation/memory-cleanup-acceptance.json)

Historical receipts retain their original dates, paths and claims. They should
not be read as a new release qualification merely because documentation moved.

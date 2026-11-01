# Build and artifact workflow

[Overview](../README.md) · [Acceptance](ACCEPTANCE.md) ·
[Canonical artifact layout](../../../docs/FIRMWARE-ARTIFACTS.md)

Run commands from the repository root using mise. The shared path authority is
`scripts/firmware_paths.py`; `firmware/lvgl-app/artifact_paths.py` exposes it to
host tools. Device runtime code does not depend on host artifact paths.

| Location under `dist/firmware/` | Purpose |
|---|---|
| `sources/lvgl/` | Pinned clean upstream checkouts |
| `sources/seedsigner-os/` | OS source checkout |
| `work/lvgl/`, `work/os/` | Disposable build output and intermediate files |
| `work/lvgl-demo/` | Earlier isolated experiment |
| `staging/NAME/` | Named runtime, overlay and combined camera bundle |
| `images/NAME/` | Selected verified image, hashes and packed report |
| `checks/lvgl/host/`, `checks/lvgl/hardware/` | New scoped check output |
| `jobs/`, `archive/` | Remote-job records and retained historical artifacts |

## Local tests and build

```sh
mise run lvgl:app:test
mise run lvgl:app:build:host
mise run lvgl:app:test:host
mise run lvgl:app:build
```

The unit suite uses Python 3.12, Pillow 11.3.0 and qrcode 7.3.1 through the mise
task. It currently passes 245 tests. The host protocol suite requires a fresh
host binary and matching build manifest. ARM builds use the pinned Zig toolchain;
`build.py` fetches verified sources and patches a disposable copy.

## Stage without flashing

```sh
mise run firmware:stage --name UNIQUE_NAME
```

This builds the native application, stages an inactive runtime and image overlay,
and attaches it to a verified camera base. It does not build an OS image, install
on the device or flash. Existing staging names are immutable. For individual
steps, `lvgl:app:bundle`, `lvgl:app:image-draft` and `lvgl:app:image-attach` retain
their explicit `--output` interfaces; inspect `--help` for required arguments.

Verify the frozen tested payload independently:

```sh
mise run lvgl:app:bundle --verify dist/firmware/staging/lvgl-dev.cb6170a37a5a/runtime
mise run lvgl:app:image-draft --verify dist/firmware/staging/lvgl-dev.cb6170a37a5a/overlay
mise run firmware:verify
mise run firmware:where
```

A new bundle requires build inputs matching current source. Verification of an
existing frozen bundle checks that bundle's recorded bytes and provenance rather
than silently replacing them with a current build.

## OS image and physical acceptance

The selected tested image is dev / base-fork / automatic startup / zram16-lzo
for the standard 240×240 display/button board. Do not treat its verification as
qualification of the pill/2.8-inch carrier or reuse its I/O profile blindly.

Follow the repository [OS build guide](../../../docs/OS-BUILD.md) for local/remote
Buildroot commands and the [artifact guide](../../../docs/FIRMWARE-ARTIFACTS.md)
for collecting a new verified image. Staging is not image promotion. Keep build
output separate from the deliberately selected `images/current` artifact.
Perform packed checks, review [acceptance gaps](ACCEPTANCE.md), then flash last.

Hardware tests are separate and explicit:
`mise run lvgl:app:hardware --help`. They can stop/start their own test workers
and temporarily deploy public fixtures, so they are not part of host-only tests.
Do not run them against an active wallet session or claim they used real funds.

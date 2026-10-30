# Luckfox OS image builds

## Current carrier build command

The wrapper defaults to `SHIELDSIGNER_IMAGE_VARIANT=production`, `SHIELDSIGNER_READER_VARIANT=UR2` and `SHIELDSIGNER_CAMERA_BACKEND=rust`. It prepares reviewed camera/image hooks in the pinned Luckfox OS checkout, configures SEC1210 UR2, and installs the Rust SC3336 owner plus the native open-source QR reader. `mise run os:prepare` applies only reviewed source preparation without compiling or flashing. Unknown checkout edits are rejected.

The historical two successful builds and matching hashes below used unchanged upstream **URT/vendor camera**; they remain baseline evidence. They do not qualify the new Rust image. Use `SHIELDSIGNER_CAMERA_BACKEND=vendor SHIELDSIGNER_READER_VARIANT=URT mise run os:build` only for that explicit baseline or matching hardware.

Production local output defaults to `dist/os/<reader-variant>/<camera-backend>/`; development adds `/dev/`, with `build.log`, `reader-config.json`, `camera-hooks.json` and `camera-bundle.json`. Keep these input manifests with image/checksum files. New image checksums are expected to differ from the historical URT/vendor baseline.

## Native frontend image selection

For the tested base-fork Mini development configuration, explicitly stage all profiles:

```sh
mise run os:camera:bundle -- --output dist/os/image-bundles/NEW_NATIVE_BUNDLE \
  --variant dev --memory-profile zram16-lzo --lcd-backend rust \
  --frontend-backend rust --io-profile base-fork --app-startup automatic
SHIELDSIGNER_BUILD_HOST=YOUR_CONFIGURED_SSH_BUILDER \
  mise run os:remote:build -- --bundle dist/os/image-bundles/NEW_NATIVE_BUNDLE --variant dev
```

`frontendBackend` is independent of automatic/held startup and is recorded in the immutable manifest/install receipt. Its explicit launcher export selects frame reception, preview preparation and QR IPC. The current native frontend requires the Rust extension package selected by `--lcd-backend rust`; a mismatched bundle is rejected. Bundles omitting the frontend field retain the historical Python selection. The overlay verifier rejects a missing, changed or duplicated export.

Packed readback with `--qemu-python` additionally exercises native socket reception, all 256 QR byte values through the installed app/actual reader, four preview rotations against packed Pillow, native worker closure and guarded startup routes. The QEMU launcher digest is distinct from the actual reader. These checks do not replace a physical cold boot or GUI tests. Native frontend staging/smoke support is implemented; a newly built image must pass it before claiming image integration.

## Build the Rust-camera image

The complete SDK build requires x86_64 Linux and Docker. The documented Proxmox guest can run it independently of this desktop. From the project root:

```sh
SHIELDSIGNER_BUILD_HOST=YOUR_CONFIGURED_SSH_BUILDER mise run os:remote:build
SHIELDSIGNER_BUILD_HOST=YOUR_CONFIGURED_SSH_BUILDER mise run os:remote:status
```

The remote launcher builds the locked Rust ARM binaries and pinned ZXing C++ reader locally with mise/uv, creates a checksummed runtime bundle, verifies the bundle, transfers only public build scripts/runtime assets to guest 610, and starts a detached image job. It refuses to overwrite an existing attempt or run alongside another SDK build. A workspace/cache lock survives SSH disconnection. Inspect the actual launcher process, Docker container and exit-code file; a log or PID file alone is not liveness evidence. Job metadata is under ignored `dist/os/remote-jobs/`.

The guest prerequisites are the Docker/Git setup below plus pinned `uv 0.12.7` on its PATH. The new detached runner adds `/usr/local/bin` explicitly. It preserves the upstream compiler/toolchain/source caches and records the true exit status atomically. It does not flash hardware, enable secure boot, provision fuses or publish images.

For a local x86_64 Linux builder with Docker, use `mise run os:build`. Without an explicit bundle the wrapper first runs `camera:rust:arm` and `camera:qr:native-build`. To reuse one immutable, verified runtime snapshot:

```sh
mise run os:camera:bundle -- --output dist/os/my-reviewed-camera-bundle
SHIELDSIGNER_CAMERA_BUNDLE="$PWD/dist/os/my-reviewed-camera-bundle" mise run os:remote:build
```

The bundle command expects native outputs from the two build tasks to exist. Bundles are immutable directories; select a new directory after changing code. Each bundle records file hashes, source revision/dirty status, version and upstream pins. It contains runtime assets and license notices only, without original RKAIQ binaries, reverse-engineering fixtures, camera images or private IQ/reference traces. Runtime license notices are regenerated for every staged bundle. A dirty development snapshot is identified as such and is not a frozen release.

### CMA12 diagnostic correction (current reflash artifact)

Use `dist/os/remote/rust-0.0.38-dev-dev-e69de65/shieldsigner-0.0.38-dev-e69de65-adb-cma12.img.xz` for the next diagnostic boot. The earlier `adb.img.xz` booted and provided ADB with the app held, but inherited upstream's **1 MiB CMA** default; headless capture failed RKISP/BAY3D buffer allocation with `-12` despite general free RAM. Earlier successful camera/restart tests used 12 MiB CMA.

The bounded unsigned derivative changes only `rk_dma_heap_cma=1M` to `rk_dma_heap_cma=12M` in the first 32 KiB U-Boot environment and updates its CRC. Every byte after that environment—including kernel, DTB, rootfs, ADB and app hold—is unchanged. `scripts/patch-image-cma.py` accepts only the exact allowlisted development base hash and new regular-file outputs; it never writes a card. See the [derivative proof](../reverse-engineering/rkaiq/image-cma12-derivative-validation.json).

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `shieldsigner-0.0.38-dev-e69de65-adb-cma12.img` | 361,488,384 | `46b1cfc4e1011dca3d57937bbadae51011b00e1d156db0f1e7f6260d9200ed15` |
| `shieldsigner-0.0.38-dev-e69de65-adb-cma12.img.xz` | 62,051,116 | `e46f5c77b2b1009bbf30f0c6f0c7bda163a4214c13cd3ae3b108caf50803479e` |

XZ streaming decode reproduced the raw checksum. The CMA12 derivative still needs its own physical boot and camera test. After boot, inspect `adb shell 'cat /proc/cmdline; grep Cma /proc/meminfo'` and require an effective `rk_dma_heap_cma=12M` / `CmaTotal: 12288 kB` before capture. Keep the app/display/buttons held while the board GPIO profile is reviewed. The [first development boot receipt](../reverse-engineering/rkaiq/image-development-boot-validation.json) verifies working ADB, 67 installed file hashes/modes, open modules/device nodes, read-only squashfs and tmpfs on the earlier CMA1 boot; it explicitly records that capture remained blocked.

Future Rust-image builds export `MINI_CMA_SIZE=12M` and explicitly forward it into Docker. New bundles record `cameraCmaSize`; packed-image verification validates environment CRC and requires a unique matching CMA token. Existing historical bundles without that field retain their earlier validation scope.

### Current diagnostic development image

The clean `e69de6586b53a21bf473134f85e6c6ccdf358b08` development image completed with exit 0 on 2026-10-28 at 23:48:03 UTC (40m29s). Its immutable runtime bundle is `6b396c5dc38d6cd82af739a22f1d686b649c67fb7443c043348bd9883a6f3eab`. This is a bench image with **automatic app, display and button startup held**, not a GPIO-profile fix.

Use `dist/os/remote/rust-0.0.38-dev-dev-e69de65/shieldsigner-0.0.38-dev-e69de65-adb.img.xz` for diagnostic bring-up. The raw `.img`, `SHA256SUMS`, validation receipt, bundle manifest and build log are beside it. The earlier production `dd4bd96` artifacts remain in their separate directory.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `shieldsigner-0.0.38-dev-e69de65-adb.img` | 361,488,384 | `d4fdfa0be754764092cfeb67c0d78336ed83186644f562952dccb6ff6ad8e0c2` |
| `shieldsigner-0.0.38-dev-e69de65-adb.img.xz` | 62,051,124 | `090ad5f5a526da8bf2510830a42008ef48ea1b9524e8008472a38db0f8169753` |

Streaming XZ decompression completed successfully and reproduced the raw image's exact hash and byte count. Packed-image readback verified the actual selected Linux FIT has USB **peripheral** mode and the reviewed development Mini DTB; the real ARM ADB daemon is executable, and `S50usbdevice` contains active noncomment ADB enable/launch commands. The exact executable `S99seedsigner` prints the diagnostic hold explanation instead of starting the app. Kernel USB gadget/configfs/functionfs support is built in.

The [development image proof](../reverse-engineering/rkaiq/image-camera-development-build-validation.json) records those hashes and modes, the unchanged tested Rust/native QR binaries, all runtime/startup checks, and actual packed Python 3.12/Crypto 3.23 direct-data AES/CompactSeedQR/UR tests under userspace QEMU. **Physical boot and USB enumeration are not proven by these checks.** First boot is **ADB inspection only**: run `adb devices` and the read-only identity/inventory commands below. Leave the app/display/buttons held; do not manually launch the app or exercise buttons until the GPIO profile is reviewed. A blank display is expected while the app is held.

### What is installed

| Item | Image path / behavior |
|---|---|
| Rust camera owner | `/usr/lib/shieldsigner-camera/camera-probe`, static ARM executable |
| Native QR worker | `/usr/lib/shieldsigner-camera/shieldsigner-qr-reader`, pinned open-source ZXing build |
| Python process-local integration | `/usr/lib/shieldsigner-camera/python/`; installed app source stays unchanged |
| Native pipeline/owner config | `/usr/lib/shieldsigner-camera/pipeline.json` and `owner.json` |
| Startup | `/usr/bin/shieldsigner-launch` invokes the pinned app at `/opt/src` through the integration launcher |
| Open kernel modules | S21 loads the reviewed CIF/ISP/CSI/sensor modules without Rockit; capture starts when the app opens Camera |
| Runtime output | `/tmp/shieldsigner-camera` on tmpfs; diagnostic full logs remain opt-in |
| Calibration | Selected SDK SC3336 IQ JSON is retained; the Rust owner reads it directly |
| Reader/display configuration | UR2 and HOTHMI 10 MHz SPI limit. Fork GPIO mapping still needs carrier review; development holds automatic app/display/button startup. |

The camera source hash/profile must match the reviewed image application. The Mini build selects the Mini device tree; final compiled model/profile and hardware behavior must be verified, not inferred from its filename. A compatibility adapter explicitly reports the fixed native 640x480 RGB stream even if old V4L2 configuration requests another size/node.

The SDK still compiles its media stage because the image pipeline and open drivers depend on its build structure. The staged image removes closed camera userspace (`rkipc`, RKAIQ/ Rockit camera libraries and launchers) both during rootfs installation and again in the late OEM pre-pack hook. The stock camera bootstrap and delayed RKAIQ startup are disabled. A post-pack staging check fails if forbidden userspace, required IQ data, open ISP modules, startup hashes or runtime assets do not match. This is not a claim that every kernel component or every unused vendor package has been rewritten.

The SDK's late filesystem strip pass also rewrites binaries that already report as stripped. An interim build was correctly rejected after this changed the tested camera binary's hash. The reviewed image hook now excludes **only** `/usr/lib/shieldsigner-camera/camera-probe` and `/usr/lib/shieldsigner-camera/shieldsigner-qr-reader` from that pass. It checks the pinned SDK function shape, preserves normal stripping for every other file, and records the policy in the image dependency receipt. [The actual SDK strip-tool fixture](../reverse-engineering/rkaiq/image-camera-native-preservation-validation.json) verified both runtime hashes remain exact while ordinary and same-directory control executables are still stripped. The verifier continues to require byte-for-byte runtime hashes; it does not substitute a weaker executable-equivalence check.

The selected IQ calibration's **contents** are pinned too: `8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a`, identical on the tested camera board and assembled SDK tree. Full private IQ contents are not stored in the repository. Image verification rejects a same-named but different calibration file.

The pinned application's QR classifier imports `Cryptodome.Cipher.AES` even before classifying CompactSeedQR. The SDK baseline carried PyCryptodomex 3.21.0 while the app pins 3.23.0. The Rust-image hook now aligns that package to **3.23.0**, with reviewed recipe/hash-file guards, a SHA-256-pinned PyPI source and license hashes in `scripts/camera-image-dependencies.json`. Rootfs installation requires the 3.23.0 package-install stamp and records its build inputs in `python-dependency-build.json`. Older 3.21.0 dependencies used for isolated on-device diagnostics do not qualify the final image's dependency alignment.

An image build and staged-rootfs checks do not prove hardware boot, LCD/buttons, smartcards, physical power cycling or secure-boot configuration. Those remain separate acceptance tests. See the [Rust-camera completion audit](../reverse-engineering/rkaiq/completion-audit.json) for current evidence.

### Verified 0.0.38 image artifact

The clean `dd4bd96dad3642911964786a657babf30f82ffea` source build completed on
2026-10-28 with exit 0 in 27 minutes 9 seconds. The local artifact is
`dist/os/remote/rust-0.0.38-dev-dd4bd96/shieldsigner-0.0.38-dev-dd4bd96.img`:

- Size: **348,602,368 bytes**.
- SHA-256: `a4d712b3ea1f56177ebd7a974cfb44b7a1a5408d4e641af9b9b3c5aebab0b431`.
- Compressed root filesystem: **45,791,839 bytes** at offset 302,809,088.

The adjacent `.img.xz` is **48,720,128 bytes** (46.46 MiB), SHA-256
`5dc51b2a1b32e51d29982eb7ab0a7e62d6000cf758c1b953a82ecafd0675bef8`.
Streaming decompression reproduces the exact verified image hash above;
see [compression verification](../reverse-engineering/rkaiq/image-camera-compression-validation.json).
This reduces transfer size without changing partitions or device contents.

[Packed-image evidence](../reverse-engineering/rkaiq/image-camera-build-validation.json)
records matching builder/local hashes, all runtime assets and startup modes,
the selected Mini DTB, open modules, absent closed camera runtime, and packed
Python 3.12.10/PyCryptodomex 3.23.0 AES/CompactSeedQR/UR direct-data checks under
ARM userspace emulation. This image has **not** been flashed or booted.

Repeat the extraction check on Linux with `squashfs-tools` installed; add
`qemu-user` for the optional direct-data tests. Use the matching immutable
bundle and a new output directory:

```sh
mise exec -- uv run --python 3.13 python scripts/verify-os-image.py \
  --image /absolute/path/shieldsigner-0.0.38-dev-dd4bd96.img \
  --bundle "$PWD/dist/os/image-bundles/0.0.38-dev-dd4bd96" \
  --output /absolute/path/new-readback-directory --qemu-python
```

The helper reads and extracts the image; it does not flash hardware or register
system-wide emulation handlers. Emulated direct-data tests do not test camera
pixels, physical display or normal boot.

### Image variants and diagnostic access

`production` preserves upstream hardened non-dev behavior: USB host mode, a disabled ADB stub, and no network or serial login. The successful `dd4bd96` image uses this policy. A production board does **not** enumerate as an ADB USB device; USB absence alone cannot establish a boot failure.

`SHIELDSIGNER_IMAGE_VARIANT=dev` (or remote `--variant dev`) selects upstream development behavior with explicit USB gadget mode and read-only squashfs. UART2 console remains disabled because it shares the smartcard reader's UART. Development retains the real ARM ADB daemon. Its `S99seedsigner` deliberately holds automatic app/display/button startup while hardware GPIO mapping is reviewed; it prints an explanation and leaves inspection to ADB. Do not run `/usr/bin/shieldsigner-launch` until the board profile has been checked. This development image needs its own exact compiled kernel/DTB ABI receipt and immutable bundle; a production bundle cannot be silently reused.

A kernel-only `--kernel-probe` job stops after the existing upstream kernel boundary, before Buildroot/rootfs compilation, and captures the fixed ABI sources plus actual configuration/DTB. It is not an image build or boot proof. Probe-only bundles cannot build images.

### First boot of a diagnostic development Rust-camera image

For Sam's standard display/button board, use the existing
[`0.8.5-luckfox` fork mapping](https://github.com/lightningspore/seedsigner/tree/228ebc0fa94251132d50adcf3db473ac48c293c5),
stored as [an app-format configuration](../firmware/bench-profiles/base-fork-io-config.json).
This bench wiring uses LCD DC56/reset57 and button GPIOs
58/53/59/54/52/55/43/42 (up/down/left/right/press/1/2/3).
The normal ST7789 app driver handles color inversion; no replacement display
driver is needed. The bench configuration uses 10 MHz SPI.

With the app stopped, apply it for the current diagnostic boot using the app's
existing `io_config.json` mechanism. UART2 must be released because GPIO42/43
are buttons on this board, rather than the carrier's smartcard UART:

```sh
adb push firmware/bench-profiles/base-fork-io-config.json /tmp/base-fork-io-config.json
adb shell '/etc/init.d/S60pcscd stop; if test -e /sys/bus/platform/drivers/dw-apb-uart/ff4c0000.serial; then echo ff4c0000.serial > /sys/bus/platform/drivers/dw-apb-uart/unbind; fi; mount -o bind /tmp/base-fork-io-config.json /opt/src/seedsigner/hardware/io_config.json'
adb shell '/usr/bin/shieldsigner-launch -- --iotest'
```

This opens the app's built-in I/O test. The configuration bind and UART release
are temporary for this boot, and do not rewrite the read-only image or change
the carrier's default mapping. Stop the app before changing profiles. Reboot
restores the image's held-app startup and original configuration. Camera tests
still require the CMA-corrected image described above.

The ADB commands below apply only to a checksum-verified **development** image whose packed readback confirms USB peripheral mode, a real executable ARM `adbd`, and the diagnostic app hold. They do not apply to the production `dd4bd96` image.

After writing the checksum-verified image to the intended test microSD and
booting it, retain the board's own identity and read-only camera inventory:

```sh
adb shell 'cat /etc/seedsigner-os-release; uname -r; cat /proc/device-tree/model'
adb shell '/usr/lib/shieldsigner-camera/camera-probe list' > /tmp/shieldsigner-image-camera-inventory.json
```

The identity should record camera `0.0.38-dev` and the built bundle hash; the
Mini model should be `Luckfox Pico Mini` with kernel `5.10.160`. Compare the
actual sensor/CIF/ISP image, metadata and subdevice nodes against
`/usr/lib/shieldsigner-camera/pipeline.json` and `owner.json`. SDK header and
DTB checks establish compatibility but cannot establish boot-time device or
media-entity numbering. The inventory must show the SC3336 and the expected
full-ISP32 graph before capture is accepted.

The new image's S21 already loads only the open camera modules. Keep that
native startup in place; the kit's one-boot skip/restore tools target the older
test image's pinned vendor startup scripts. The new launcher starts capture
when a camera screen opens and uses the native QR worker.

Only after the board GPIO/display/button profile has been reviewed, with other camera screens closed, copy the kit's
`native_qr_hardware_check.py` to `/tmp` and exercise the image's installed
runtime and naturally detected profile:

```sh
adb shell 'PYTHONPATH=/usr/lib/shieldsigner-camera/python python3 /tmp/native_qr_hardware_check.py --app-root /opt/src --reader /usr/lib/shieldsigner-camera/shieldsigner-qr-reader --camera-config /usr/lib/shieldsigner-camera/owner.json --report /tmp/shieldsigner-image-native-qr.json'
```

Its `realCamera.runtimeProfile` should be `luckfox_22` without a test override.
The synthetic binary, CompactSeedQR and UR cases check application integration;
then scan the complete printed public target through the actual camera screen.
Keep the entire QR and its white border in view. Finally observe the physical
LCD, each button, live exposure/white-balance response under changed lighting,
and a physical power cycle. Record those observations separately from image
file checks and synthetic fixture results. No new image has been flashed by
the build or verification tools.


## Image size: software versus reserved space

The measured vendor-camera SD image is 347,537,408 bytes, but its compressed
Linux root filesystem uses only 44,725,597 bytes (42.65 MiB). Its Rockchip
layout reserves 32 MiB for boot and 256 MiB for writable userdata before the
root filesystem, which starts at byte 302,809,088. These reservations explain
most of the raw file size. Nonzero-block counts do not establish minimum safe
partition sizes. See the [measured size analysis](../reverse-engineering/rkaiq/image-size-analysis.json).

The successful Rust-camera image above is 348,602,368 bytes, 1,064,960 bytes
(0.31%) larger than the baseline. Its compressed root filesystem is
45,791,839 bytes (43.67 MiB). The earlier approximate 44 MiB figure described
only that filesystem, not a complete SD image. No large OS reduction has yet
been implemented.

For a smaller download, compress the verified full image and verify its hash
after decompression. For a smaller raw image, a future lean layout could reduce
boot/userdata reservations together with bootloader, packer and mount settings;
this needs boot, power-cycle and update/recovery testing. Do not truncate the
existing image, because its root filesystem is located after those regions.

For less installed software, first evaluate removing runtime Git and
setuptools, replacing Git-based version lookup with baked metadata, then audit
unused OEM tools and libraries. Preserve UI/fonts, wallet/smartcard crypto,
camera drivers and required notices. Unpacked file sizes are not compressed
savings: measure the repacked filesystem before setting a target. These are
follow-up options; the current verified-baseline build is unchanged.

The [temporary-copy QR size experiment](../reverse-engineering/rkaiq/qr-runtime-size-analysis.json)
reduces the native worker from 8,431,056 to 894,932 bytes by stripping symbols;
allocated sections remain byte-identical and ARM-emulated binary payload tests
pass. Estimated whole-file compressed savings are 1.59–2.15 MB, not measured
SquashFS savings. A future release must strip before computing bundle hashes
and rerun hardware qualification. The Rust camera executable is already
stripped. Its large copyright HTML compresses to about 98 KB with xz, so it is
not a meaningful first target for flash savings; preserve the notices.

## Notes: faster iteration and a possible Linux-free variant

These are development options, not changes made to the current build. A PyPI mirror is deferred.

### 1. Iterate on Buildroot faster

Start by retaining the existing Rust toolchain, ccache and repository volumes. Verify the Rust cache is successfully packaged after this first build and restored on the next one. Source caching avoids downloads; compiler/toolchain caching avoids compilation. The upstream SDK preparation cleans its checkout for production builds, so retaining the repository volume does not by itself preserve all incremental build output. Check whether the SDK's `dl/` directory survives that preparation before relying on it as a durable download cache; a separate download volume is a possible follow-up.

Use the shortest loop appropriate to the change:

| Change | Development loop | What still needs validation |
|---|---|---|
| Python menus, transaction logic or rendering | Run host-side tests/preview with hardware interfaces mocked; use a separate development device/image for real hardware | Production image packaging and actual display/camera/card behavior |
| Reader configuration, init scripts or rootfs overlay | Re-run rootfs/post-build processing and SDK image packaging in a retained development workspace | Files actually present in the final image; UART2 console conflict; boot behavior |
| One native package | Rebuild or reconfigure that package within the configured Buildroot tree, then regenerate images | Dependencies are not automatically rebuilt; SDK packaging must run afterward |
| Device tree or kernel driver | Rebuild the affected kernel/device-tree artifacts with the SDK pipeline | Boot compatibility and hardware I/O |
| Architecture, libc or toolchain | Full clean build with matching cache inputs | ABI consistency across all packages |

For a configured Buildroot development tree, the upstream package targets are `make <package>-rebuild` (compile/install again), `make <package>-reconfigure` (configure first), and `make <package>-dirclean` (discard that package's build directory). Follow with `make` to regenerate rootfs images, and the Luckfox SDK packaging steps to produce the flashable artifact. These are reference commands, not a tested incremental workflow for this carrier yet. Do not run them against the active build workspace while it is compiling.

Use a separate SDK workspace for rapid experiments: the pinned production runner restores pristine source and would erase ad hoc edits. Keep changes as explicit patches or commits. Package removal requires a full rebuild because Buildroot does not uninstall its files from the target tree. A changed dependency may also require rebuilding its consumers. Avoid the Luckfox SDK's blanket clean command: the pinned upstream scripts document that it can remove required vendor prebuilts.

After development succeeds, run the unchanged production pipeline with recorded inputs. Compare final hashes for reproducibility and perform hardware bring-up. A fast incremental build is useful evidence during development, but cannot establish a clean production result by itself.

Reference: [Buildroot 2024.11.4 rebuilding guidance](https://github.com/buildroot/buildroot/blob/2024.11.4/docs/manual/rebuilding-packages.adoc). No PyPI proxy or new download-cache service has been installed.

### 2. Potentially remove Linux

Python does not inherently require Linux. A future firmware could use MicroPython on bare metal or an RTOS, or a port of CPython to another sufficiently capable operating environment. Neither is a drop-in replacement for this application. A MicroPython route would retain compatible Python logic while replacing the CPython extensions and Linux services it currently uses.

| Existing function | Work needed without Linux |
|---|---|
| Python application and Bitcoin logic | Audit language/library compatibility, memory use, transaction formats and signing behavior; reuse only what tests establish is compatible |
| Pillow-based UI | Replace rendering with an embedded graphics library and a display driver |
| SPI/GPIO buttons and backlight | Supply peripheral initialization, drivers, pulls, timing and debounce |
| Camera and QR decoding | Supply sensor/CSI/ISP support, capture buffers and a compatible decoder; this is a major feasibility risk on Luckfox |
| PC/SC and CCID smartcard stack | Implement the SEC1210 UART transport and required card protocol/application handling, including errors and timeouts |
| Cryptographic extensions | Provide tested embedded implementations with equivalent behavior, adequate entropy and appropriate secret handling |
| Boot, storage and updates | Supply startup/memory initialization, filesystem handling, recovery and the intended verified update/boot mechanism |

The SEC1210 still handles its card electrical interface; removing PC/SC would require replacing the host-side communication stack, not driving all card contacts directly from GPIO. A Satochip can perform supported signing inside the card, but the host still needs transaction parsing, user confirmation, communication and other cryptographic operations. SeedKeeper storage does not move signing out of the host.

On the Luckfox, Linux currently supplies hardware support that firmware would need to replace. No supported Linux-free Python runtime with this board's complete camera/display/card stack has been established here. A different microcontroller with documented camera and embedded-runtime support may be a better fit, but would constitute a separate hardware variant and needs its own feasibility study.

Suggested feasibility sequence: first display and buttons, then a disposable-card ATR/APDU exchange through SEC1210, then camera capture and QR decoding, then transaction parsing/signing with known test vectors. Measure RAM, boot time and throughput at each stage. Reassess the hardware after camera feasibility is known. Keep the current Linux carrier as the working baseline while exploring this option; a smaller OS alone does not establish a more secure signer.

Reference: [MicroPython differences from CPython](https://docs.micropython.org/en/latest/genrst/index.html), [pinned application requirements](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/requirements.txt), and the card roles in [SMARTCARDS.md](SMARTCARDS.md).

Run from this project folder:

```sh
mise run os:build
```

The wrapper clones the upstream OS into the ignored `tools/os/seedsigner-os/` folder, checks its pinned revision and clean working tree, and invokes the Mini microSD build. Output and the latest attempt log are under `dist/os/`. It does not flash hardware or provision secure boot.

## Pinned inputs

- OS: `e7589465aff172f4f510ad46d18776ccc8d2c203`.
- Application: `efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f`.
- Target: Mini, microSD, default non-dev variant, four jobs.
- Container and SDK: definitions and SDK revision supplied by the pinned OS checkout. A complete reproducibility claim also requires recording the actual Docker image identity and verifying output hashes.

Luckfox uses the vendor SDK pipeline under `opt/luckfox/`, including its Buildroot root filesystem, rather than the Raspberry Pi pipeline under `opt/buildroot/`.

## Trial on 11 October 2026

Docker Desktop was started successfully on this Apple Silicon Mac. The upstream preflight exited with status 1:

```text
[ERROR] ARM64 Macs not supported due to Docker emulation issues
Use GitHub Actions or x86_64 machine for building
```

Compilation never started and no image was produced. The README mentions ARM emulation, but the executable build script explicitly rejects it; the script governs this attempt. Use an x86_64 Linux builder with Docker, or an appropriate GitHub Actions workflow, for the next attempt. The SDK checkout alone is documented as about 37 GB; reserve additional space for compilation and caches. Upstream defaults use Docker named volumes for repository and compiler caches, outside this project directory.

## Carrier-specific configuration still needed

This trial deliberately uses unchanged upstream source. Its reader configuration selects `SEC1210URT`, while our BOM selects `SEC1210/PV-UR2`. Before hardware testing, change the serial reader device to `/dev/ttyS2:SEC1210UR2` in a documented local patch and record its checksum. Keep the UART2 serial console disabled so it does not conflict with the reader. Successful compilation alone will not establish screen, GPIO, camera or smartcard operation on this carrier.

Sources: [pinned build script](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/build.sh), [pinned README](https://github.com/3rdIteration/seedsigner-os/blob/e7589465aff172f4f510ad46d18776ccc8d2c203/opt/luckfox/README.md), [electrical review](ELECTRICAL-REVIEW.md).

## Proxmox builder

On 11 October 2026, a dedicated unprivileged Ubuntu 22.04 LXC container was created on `pve-beelink2` (`BUILD_HOST`), ID **610**, hostname `shieldsigner-builder`. Resources: six CPU cores, 8 GB RAM, 2 GB swap allowance and a 140 GB thin-provisioned root disk. Nesting and keyctl are enabled for Docker. It does not start automatically with the host. Beelink1 was excluded because available memory was under 1 GB.

Docker is installed inside the guest. Both x86_64 architecture and the SDK's `setarch -R` prerequisite passed. The same pinned build wrapper runs under `/opt/shieldsigner-build/`, with `SHIELDSIGNER_BUILD_JOBS=6`. The launched attempt is independent of the local SSH connection.

```sh
mise run os:remote:status
```

Remote output is `/opt/shieldsigner-build/dist/os/`; `launcher.log` includes setup and the whole attempt, `build.log` includes the upstream build, and `exit-code` appears when the attempt finishes. Absence of `exit-code` alone is not proof of a healthy running process: inspect guest processes and Docker when diagnosing a stalled build. No hardware flashing is performed. The reader variant adjustment above remains pending; this first attempt uses unchanged upstream source.

### Provisioning commands used

These commands create a new guest. Do not repeat `pct create` against the existing ID 610. Check available RAM, storage and guest IDs before recreating this setup elsewhere.

Run on Beelink2 over SSH:

```sh
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
pct create 610 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname shieldsigner-builder --unprivileged 1 \
  --features nesting=1,keyctl=1 --cores 6 --memory 8192 --swap 2048 \
  --rootfs local-lvm:140 --net0 name=eth0,bridge=vmbr0,ip=dhcp --onboot 0
pct start 610
pct exec 610 -- bash -lc 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io git ca-certificates && systemctl enable --now docker'
pct exec 610 -- bash -lc 'docker info --format {{.Architecture}}; setarch x86_64 -R true'
```

Proxmox verified the template checksum. Initial provisioning allocated two cores/6 GB; these were increased with `pct set 610 --cores 6 --memory 8192` before launching compilation.

The project wrapper `scripts/build-os.sh` was copied into `/opt/shieldsigner-build/scripts/` using `scp` to the host and `pct push` into the guest. It automatically clones the pinned OS checkout. Inside the guest, the launch is equivalent to:

```sh
mkdir -p /opt/shieldsigner-build/dist/os
nohup bash -c 'SHIELDSIGNER_BUILD_JOBS=6 bash /opt/shieldsigner-build/scripts/build-os.sh; echo $? > /opt/shieldsigner-build/dist/os/exit-code' \
  > /opt/shieldsigner-build/dist/os/launcher.log 2>&1 < /dev/null &
```

Do not launch concurrent builds into this same workspace/cache. Preserve the previous logs and exit code before a new attempt. The first launched Docker container was `seedsigner-build-1791774223`; its image identity was `sha256:bbe1aa686b79ace7fc380820b88b74e4035015859442bd1938d17c4d83c28eb8`. Base Ubuntu image digest: `sha256:5ec03bb3441e8b0bf3b4f9cd4629a1ae763010dc3035bb8da3ae6cf026486401`. SDK pin: `0b5c1f30ca6333b7ec5af70d26511da9ef8d39af`.

### What Rust and LLVM build

The application is Python. The enabled `python-cryptography` package contains Rust extensions; the external `python-pgpy` and `python-specter-card` packages depend on it. The SDK target is `armv7-unknown-linux-uclibceabihf`. This upstream build supplies support for that Rust Tier 3 target and builds the Rust toolchain/target standard library from source because the prebuilt target standard library is unavailable. LLVM is the compiler infrastructure used by rustc and is compiled as part of this host toolchain work. This does not mean an LLVM compiler is required at runtime on the signer.

The initial run reports six general build jobs and three LLVM/Rust jobs. Upstream limits Rust parallelism because LLVM compilation can need about 2 GB per job. The `seedsigner-rustcache` Docker volume retains the built toolchain for later runs; `seedsigner-ccache` retains C/C++ compiler cache, and `seedsigner-repos` retains SDK/app source checkouts. All live inside this dedicated guest. Cache restore success must be checked in subsequent logs; a cache volume existing alone does not prove reuse.

Source evidence is in the pinned OS checkout: `opt/luckfox/configs/luckfox_pico_defconfig` enables `BR2_PACKAGE_PYTHON_CRYPTOGRAPHY`, `opt/luckfox/os-build.sh` patches Rust's uClibc target support and job count, `opt/luckfox/rust-toolchain-cache.sh` implements caching, and the two external package `.mk` files declare their dependencies.

### Collecting logs and completed artifacts

After `exit-code` reports zero, list the output files and verify their checksums. The archive commands below collect guest output via the Proxmox host; run from this local project directory. They also work for diagnostic logs from a failed attempt, but a growing live log is only a snapshot.

```sh
ssh root@BUILD_HOST 'pct exec 610 -- tar -C /opt/shieldsigner-build/dist/os -czf /tmp/shieldsigner-os-output.tar.gz . && pct pull 610 /tmp/shieldsigner-os-output.tar.gz /tmp/shieldsigner-os-output.tar.gz'
mkdir -p dist/os/remote
scp root@BUILD_HOST:/tmp/shieldsigner-os-output.tar.gz dist/os/remote/output.tar.gz
tar -xzf dist/os/remote/output.tar.gz -C dist/os/remote
```

Record image filenames, SHA-256 checksums, Docker image identity, source revisions, build flags and the actual exit status. The first attempt has reached U-Boot compilation; a successful finished image and hardware boot remain unverified. A single successful build would not establish reproducibility; compare against a second matching build or the corresponding upstream artifacts before making that claim.

## Automatic cached-build comparison

A guest-side watcher runs `scripts/benchmark-os.sh` under `/opt/shieldsigner-build/`. It waits for the existing first run's exit code and starts a second run only if the first succeeded. Six jobs and the same pinned source/target/flags are used. The cached wrapper is installed as `scripts/build-os-cached.sh`; outputs are separate so the first attempt's evidence is retained.

- First attempt: `dist/os/`.
- Second attempt: `dist/os-second/`.
- Watcher log/lock and timing result: `dist/os-benchmark/`.

The result JSON records exit codes, wall times, a successful Rust cache restore without a host-rust rebuild, whether the second run was faster, and whether the artifact checksum manifests match. The first duration includes source/container setup and is approximate from the launch-log creation time; the second is timed directly. This comparison includes warm Docker/source caches as well as the Rust cache. Cache restore must show the successful restore line and should not be followed by a source rebuild fallback. The watcher survives SSH disconnection and does not alter the active first build. It uses a lock to prevent duplicate watchers. A failed first run does not trigger the second build. No speed improvement is claimed until both results are measured.

## First completed build result

The first Mini microSD build completed successfully on 12 October 2026 UTC (11 October local time), exit code **0**, in approximately **8,906 seconds (2 h 28 min 26 s)** including container/source setup. This measured cold build took longer than the upstream README's indicative estimate.

Artifact: `seedsigner-luckfox-pico-mini-sd-efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f-osproduction-unsigned.img` — **347,537,408 bytes**.

SHA-256: `8ba8fa6bcad15514297a2e058bf06c94774ce4e3a891e5a0364527a458302761`.

The image, build logs, exit code and checksum manifest were retrieved into ignored `dist/os/remote/first/`; the local image checksum matches the remote manifest. This is an unsigned upstream baseline image. It has not been flashed or boot-tested, and the documented SEC1210 UR2 configuration adjustment remains required before bring-up of the selected carrier variant.

The second run completed successfully with a verified Rust toolchain restore. Its measured results are below and in `docs/os-build-benchmark.json`.

## Completed cache benchmark

Both attempts exited **0**. The second run explicitly restored the cached Rust 1.82.0 toolchain and did not rebuild `host-rust`. This comparison uses the same source revisions, Mini microSD target, non-dev/unsigned configuration, Docker image and six build jobs on the same Proxmox guest.

| Run | Wall time | Result |
|---|---:|---|
| Cold first run, including setup | 8,906 s — 2 h 28 min 26 s | Successful image |
| Cached second run | 1,625 s — 27 min 5 s | Successful image; Rust cache restored |

The cached build was **5.481× faster**, with **81.75% less elapsed time**. This is the measured benefit of the warm toolchain, Docker/source and compiler caches together; it does not isolate the contribution of each cache.

Both 347,537,408-byte images have SHA-256 `8ba8fa6bcad15514297a2e058bf06c94774ce4e3a891e5a0364527a458302761`. The remote files were compared byte-for-byte, and both local copies were independently hashed against their manifests. This demonstrates identical output across these two matching builds on this host, not reproducibility across every possible build environment.

Local files: `dist/os/remote/first/` and `dist/os/remote/second/`. Machine-readable evidence: [os-build-benchmark.json](os-build-benchmark.json). The watcher has finished and released its lock. The Proxmox guest and cache volumes remain available for future builds. No image was flashed or fuse provisioned. These upstream baseline images still require the documented UR2 reader configuration adjustment before bring-up of our selected carrier.

# Luckfox OS image builds

## Current carrier build command

The wrapper now defaults to `SHIELDSIGNER_READER_VARIANT=UR2` and `SHIELDSIGNER_CAMERA_BACKEND=rust`. It prepares reviewed camera/image hooks in the pinned Luckfox OS checkout, configures SEC1210 UR2, and installs the Rust SC3336 owner plus the native open-source QR reader. `mise run os:prepare` applies only reviewed source preparation without compiling or flashing. Unknown checkout edits are rejected.

The historical two successful builds and matching hashes below used unchanged upstream **URT/vendor camera**; they remain baseline evidence. They do not qualify the new Rust image. Use `SHIELDSIGNER_CAMERA_BACKEND=vendor SHIELDSIGNER_READER_VARIANT=URT mise run os:build` only for that explicit baseline or matching hardware.

Local output defaults to `dist/os/<reader-variant>/<camera-backend>/`, with `build.log`, `reader-config.json`, `camera-hooks.json` and `camera-bundle.json`. Keep these input manifests with image/checksum files. New image checksums are expected to differ from the historical URT/vendor baseline.

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
| Reader/display configuration | UR2; reviewed FOX_22 HOTHMI SPI limit of 10 MHz, validated against existing DC/reset/CS mapping |

The camera source hash/profile must match the reviewed image application. The Mini build selects the Mini device tree; final compiled model/profile and hardware behavior must be verified, not inferred from its filename. A compatibility adapter explicitly reports the fixed native 640x480 RGB stream even if old V4L2 configuration requests another size/node.

The SDK still compiles its media stage because the image pipeline and open drivers depend on its build structure. The staged image removes closed camera userspace (`rkipc`, RKAIQ/ Rockit camera libraries and launchers) both during rootfs installation and again in the late OEM pre-pack hook. The stock camera bootstrap and delayed RKAIQ startup are disabled. A post-pack staging check fails if forbidden userspace, required IQ data, open ISP modules, startup hashes or runtime assets do not match. This is not a claim that every kernel component or every unused vendor package has been rewritten.

The SDK's late filesystem strip pass also rewrites binaries that already report as stripped. An interim build was correctly rejected after this changed the tested camera binary's hash. The reviewed image hook now excludes **only** `/usr/lib/shieldsigner-camera/camera-probe` and `/usr/lib/shieldsigner-camera/shieldsigner-qr-reader` from that pass. It checks the pinned SDK function shape, preserves normal stripping for every other file, and records the policy in the image dependency receipt. [The actual SDK strip-tool fixture](../reverse-engineering/rkaiq/image-camera-native-preservation-validation.json) verified both runtime hashes remain exact while ordinary and same-directory control executables are still stripped. The verifier continues to require byte-for-byte runtime hashes; it does not substitute a weaker executable-equivalence check.

The selected IQ calibration's **contents** are pinned too: `8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a`, identical on the tested camera board and assembled SDK tree. Full private IQ contents are not stored in the repository. Image verification rejects a same-named but different calibration file.

The pinned application's QR classifier imports `Cryptodome.Cipher.AES` even before classifying CompactSeedQR. The SDK baseline carried PyCryptodomex 3.21.0 while the app pins 3.23.0. The Rust-image hook now aligns that package to **3.23.0**, with reviewed recipe/hash-file guards, a SHA-256-pinned PyPI source and license hashes in `scripts/camera-image-dependencies.json`. Rootfs installation requires the 3.23.0 package-install stamp and records its build inputs in `python-dependency-build.json`. Older 3.21.0 dependencies used for isolated on-device diagnostics do not qualify the final image's dependency alignment.

An image build and staged-rootfs checks do not prove hardware boot, LCD/buttons, smartcards, physical power cycling or secure-boot configuration. Those remain separate acceptance tests. See the [Rust-camera completion audit](../reverse-engineering/rkaiq/completion-audit.json) for current evidence.


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

# Real GUI camera benchmark

`gui-camera-bench.py` launches the installed application's **real ScanView** through `Controller.start(initial_destination=...)` and the existing camera/QR integration. It bypasses startup interstitials to enter Scan directly. The application's normal animated loading screen remains intact; no static-loader replacement or synthetic UI result is installed.

Run only on the reviewed board GPIO/display profile, after stopping other application/camera owners. This harness uses the physical camera, display and buttons. It does not install firmware, change boot services or edit installed app files. The adjacent `base-fork-io-config.json` is a separate bench profile; this launcher does not silently install it.

Copy the harness to the target, then launch it using the installed Python runtime:

```sh
adb push firmware/bench-profiles/gui-camera-bench.py /tmp/gui-camera-bench.py
adb shell 'python3 -u /tmp/gui-camera-bench.py --small-ram --duration 60 --state-file /tmp/gui-camera-bench-state.json'
```

For the reviewed Rust LCD extension/shim already staged on the target:

```sh
adb shell 'python3 -u /tmp/gui-camera-bench.py --small-ram --rust-lcd --lcd-python-root /tmp/lcd-python --duration 60'
```

Paths for the application, camera Python modules, owner config and QR reader have explicit CLI overrides; see `--help`. `--small-ram` explicitly sets `SHIELDSIGNER_SMALL_RAM=1`; without it the harness sets that variable to `0` rather than inheriting a previous shell's choice. It leaves other runtime diagnostic settings alone, so record the launch environment when comparing runs. Rust LCD support is opt-in and must be installed before Renderer construction.

Telemetry is published immediately, every two seconds, and after cleanup. Each update writes a private temporary file in the same directory and atomically replaces the state file, so a reader sees a complete previous or next JSON document. It records only frame/reconnect/error counts, renderer successful-call/error counts, bounded recent stream status, selected bench options and process-termination metadata. It never saves images or decoded QR payloads. Weak stream references avoid retaining stopped sessions' image buffers. Read it without starting another on-board Python process:

```sh
adb shell 'cat /tmp/gui-camera-bench-state.json'
```

Reader failures print their full chained traceback to **stderr**. Capture that stream on the desktop if needed; avoid accumulating large logs in the Mini's tmpfs. Renderer errors are counted and re-raised into the real application's existing behavior.

`--duration` and SIGINT/SIGTERM request **benchmark process termination**, not a UI button cancellation. The application catches `BaseException`, so an exception sentinel cannot reliably unwind it. An independent Python watchdog instead requests tracked camera/QR-owner cleanup, waits at most `--cleanup-seconds` (default 8), publishes termination metadata if possible, and calls `os._exit`. It does **not** claim Controller/application `finally` blocks ran or qualify Back/cancel behavior. New stream starts are refused once termination begins.

For `--duration`, the kernel's default SIGALRM is also armed at `duration + cleanup-seconds + 1` seconds. This hard fallback does not need the GIL and cannot be caught by the application's Python exception handler. It may bypass all Python cleanup and leave only the last complete telemetry snapshot; uninterruptible kernel I/O can still delay OS termination; the native managed-owner parent-death mechanism remains the fallback. After forced termination, independently check camera ownership/processes before another run. SIGINT/SIGTERM use the bounded watchdog once Python can dispatch the signal; use a duration for the independently armed hard deadline. No timer is a claim of actual UI navigation or orderly application shutdown.

To inspect a GIL-blocked run, add `--stack-dump-seconds 10`. `faulthandler.dump_traceback_later` uses a native watchdog and repeatedly writes all Python thread stacks to stderr even when ordinary Python telemetry cannot acquire the GIL. On the target's Python 3.12 this shows Python call sites; it does **not** promise a native C/C++ backtrace. Stack dumping and hard SIGALRM use separate timers. Capture stderr on the desktop rather than allowing repeated dumps to fill tmpfs.

## Runtime-only compressed RAM swap

The first recorded 180-second real GUI trial with zram, Small-RAM and Rust LCD delivered 2,544 full frames, 843 successful renderer calls, zero reader/renderer errors and one recovered startup reconnect. Duration cleanup reported no error. This is a bounded continuous-preview result, not a UI Back/cancel or optical decode qualification. See [the captured counters](../../reverse-engineering/rkaiq/memory/gui-zram-180s-result.json).

`enable-zram.sh` reproduces that **bench-only** RAM-swap configuration. It is not installed as a boot default. It accepts only kernel `5.10.160` with the reviewed development-image kernel-config receipt and exact module hashes from [the module build receipt](../../reverse-engineering/rkaiq/zram-module-build-receipt.json). The modules are already staged on the current board under `/userdata/shieldsigner-runtime/zram`; these commands are for a future deliberate setup, not instructions to reset its running configuration.

```sh
adb push firmware/bench-profiles/enable-zram.sh /tmp/enable-zram.sh
adb shell 'sh /tmp/enable-zram.sh'
```

An optional first argument selects a different directory containing those same pinned `zsmalloc.ko`/`zram.ko` files. The script loads `zsmalloc` before `zram`, selects **LZO before initializing disksize**, sets a 16 MiB logical block device and an 8 MiB compressed-allocation limit, then runs `mkswap` and `swapon` **only on `/dev/zram0`**. The default `lzo-rle` backend is not registered in this reviewed kernel. No SD swap file/backing device is created. The 8 MiB cap limits compressed allocator pages; it is not a promise that all module/metadata overhead fits inside that cap. A full incompressible working set may still fail allocations.

An already active `/dev/zram0` with exactly LZO/16 MiB/8 MiB and expected swap geometry is accepted without changing it. Other swap devices, additional zram devices, holders, different active settings, or a configured-but-inactive zram0 cause refusal. The script never resets, swaps off, unloads or reformats an initialized device. A failed partial setup is left for explicit inspection; it is not automatically reset. On-disk module hashes and the image receipt are checked; those checks do not retrospectively attest where an already loaded compatible module came from.

Read-only status:

```sh
adb shell 'cat /proc/swaps; cat /sys/block/zram0/comp_algorithm; cat /sys/block/zram0/disksize; cat /sys/block/zram0/mm_stat'
```

In this driver, `mem_limit` is write-only: `mm_stat` field 4 is the authoritative limit readback (`8388608`). `/proc/swaps` shows roughly 16,380 KiB usable after the swap header.

Teardown is **not automatic**. First stop the app, camera and QR owners and inspect their absence. Ensure available RAM can absorb all used swap, with additional working headroom; do not attempt swapoff under memory pressure. For this exact owned setup, a deliberate `swapoff /dev/zram0` disables only RAM swap; leave the configured device/modules in place. If swapoff fails, retain the existing state and investigate rather than resetting/unloading it. A reboot after stopping workloads is the simpler way to discard this runtime-only setup. Never run `swapoff -a`, reset or module-unload commands as part of this bench procedure.

## Persistent image integration: opt-in source wiring

The image builder now has separate `--memory-profile zram16-lzo`, `--lcd-backend rust` and `--io-profile base-fork` selections. They stage a standard-kernel zram policy, SDK-built uClibc LCD package and explicit guarded wiring/resource policy respectively. None is inferred from another. A separate `--app-startup automatic|held` choice defaults to held for dev and automatic for production; enabling a memory/LCD/IO profile does not select startup.

The actual zram/carrier kernel probe has passed. The base-fork UART2-disabled DTB probe also passed. The actual LCD package and `2663ac8` full image built successfully and passed packed readback/ARM QEMU checks. A read-only SquashFS runtime hardware check passed; a fresh persistent-image boot remains pending. Host checks are not a claim of new-image boot qualification. See [the integration checkpoint](IMAGE-INTEGRATION.md) for source, receipt, init, strip and packed-image requirements. The runtime-only setup above deliberately retains its old exact bench module pins.


## Diagnostic button control

`button_control.py` overlays named virtual active-low readings on the reviewed GPIO input objects. Physical low inputs remain active; it never writes GPIO lines. The adapter runs inside the app, adds no thread, and preserves normal debounce, repeat, hold and screensaver handling. The launcher `button-controlled-app.py` uses the real app startup and does not jump directly to Scan.

This is explicitly enabled diagnostic code, not part of the flashed default startup. Stop the existing `/start-seedsigner.sh` supervisor and app before launching it, and confirm camera owners are gone. Stage both files under `/tmp`, then use the same Small-RAM, Rust LCD, code-lock and 4096 KiB MEMLOCK environment as the normal launcher. Restarting normally/rebooting removes this process-local patch. The guarded source hash must match before it installs.

The app creates `/tmp/shieldsigner-buttons-PID` (0700) and publishes its active directory in `/tmp/shieldsigner-button-control-current.json` (0600). Requests accept only the eight named keys, a 30–1500 ms hold and a bounded ID; input files are limited to 512 bytes. Requests are consumed once, overlapping/duplicate requests are rejected, and release uses monotonic time. No TCP listener or arbitrary code command is exposed.

With the diagnostic app already running:

```sh
mise run camera:button KEY_PRESS
mise run camera:button KEY_LEFT --hold-ms 500
```

Use 120 ms menu presses and a 500 ms Scan cancellation: the frame-paced Scan loop may miss a brief press. The client waits up to 20 seconds for a release observation, allowing camera startup to block polling. A delivered/released acknowledgement is not proof of navigation; verify the app view and camera ownership/DMA separately. Do not replay a timed-out command without inspecting the current state.

Hardware proof: `reverse-engineering/rkaiq/memory/button-control-hardware-result.json` records three real-app Scan/Back cycles. Every cycle returned to MainMenuView with no camera/QR owners and zero allocated camera DMA. This tests software navigation, not electrical button wiring or optical QR decoding. The source fixture tests cover physical-input preservation, bounded press/release, duplicate handling and invalid requests.

## Python memory diagnostics

`python-object-census.py` exports only type counts, selected shallow sizes and process memory, without tracemalloc or object values. It adds a monitor thread, refuses the object walk below 8 MiB available RAM and has a 180-second process deadline. It is a diagnostic run, not a normal launcher. Touching objects decompresses cold pages, so report PSS and swap before/after together.

Full tracemalloc snapshots made the Mini unresponsive. `python-memory-profile.py` now refuses targets with less than 96 MiB MemTotal. Use `python-import-memory-profile.py` with the packed ARM Python under QEMU on a larger builder for full import snapshots. Its source-filename totals reflect allocation sites, not feature ownership, and are not target resident-memory measurements. The public guide and scoped summary are in `docs/MEMORY-THREADS.md` and `reverse-engineering/rkaiq/memory/python-deep-2026-10-29/summary.json`.

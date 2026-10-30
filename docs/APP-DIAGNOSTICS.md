# App diagnostics and real board exploration

These tools let a developer operate the real Luckfox app through ADB and collect rendered screens on request. They are explicitly enabled diagnostic helpers, separate from normal firmware startup. Button injection exercises application input handling; it does not validate physical switches or electrical pinouts.

## What the tools do

- `firmware/bench-profiles/button_control.py` wraps the reviewed GPIO objects' `read()` methods. A named virtual press returns active-low for a bounded interval; physical low inputs remain active. The code never writes GPIO pins and adds no thread.
- `firmware/bench-profiles/button-controlled-app.py` installs the input adapter and starts the normal camera/LCD integration. It does not skip startup notices or jump directly to a test view.
- The diagnostic launcher also remembers the latest rendered image by reference. A capture request saves that image as PNG. This can retain an extra preview frame and requested PNG encoding perturbs latency/memory; it is not enabled in the normal image or in the earlier reliability soaks.
- `scripts/camera-memory/button.py` sends one named press and waits for a release observation. `screen.py` requests and pulls one image. Neither exposes arbitrary Python commands or a network listener.

The source hash of `seedsigner/hardware/buttons.py` must match the reviewed implementation before installation. Changes to upstream button handling require review rather than bypassing the guard.

## Enable the diagnostic app

First identify and stop the running `/start-seedsigner.sh` supervisor and app, then confirm the camera and QR owners are gone. Do not run a second app against the same GPIO/SPI/camera resources. The upstream S99 service does not provide a conventional stop interface; do not assume passing it `stop` will stop the app.

Stage the two helpers:

```sh
adb push firmware/bench-profiles/button_control.py /tmp/button_control.py
adb push firmware/bench-profiles/button-controlled-app.py /tmp/button-controlled-app.py
```

After stopping the existing owners, launch from an ADB shell using the same explicit Small-RAM, Rust LCD and code-lock policy as the installed launcher:

```sh
ulimit -l 4096
export SHIELDSIGNER_SMALL_RAM=1
export SHIELDSIGNER_CAMERA_LOCK_CODE=1
export SHIELDSIGNER_LCD_BACKEND=rust
setsid nohup python3 -u /tmp/button-controlled-app.py \
  >/tmp/button-controlled-app.log 2>&1 </dev/null &
sleep 1
```

The short wait lets the detached process establish itself before the ADB shell closes. Rebooting removes `/tmp` helpers and returns to installed startup. Relaunching the original app without this helper also removes the process-local adapter; stop its existing supervisor/owners first.

The app creates `/tmp/shieldsigner-buttons-PID` with mode 0700 and a mode-0600 current-session pointer. Request files are capped at 512 bytes and accept only eight named keys, a bounded request ID and a 30–1500 ms hold. Requests are consumed once; duplicate and overlapping requests are rejected. Release uses monotonic time. Acknowledgements are input-layer observations, not assertions about the resulting screen.

## Drive and observe

From the repo root:

```sh
mise run camera:button KEY_PRESS
mise run camera:button KEY_DOWN
mise run camera:button KEY_LEFT --hold-ms 500
mise run camera:screen dist/app-demo/current.png
```

Use 120 ms presses for ordinary menus. A 500 ms left press is more reliable for Scan cancellation because Scan checks buttons at a slower frame-paced cadence. In list screens, Left generally selects the top navigation arrow and Press activates it. The home screen is a two-by-two grid. These distinctions are normal app behavior, not special commands in the adapter.

The client allows up to 20 seconds to observe release because camera startup may temporarily block input polling. If a command times out, inspect the log/current screen before sending another press; replaying can navigate twice. The app's executed-view log, process ownership and DMA readback establish actual navigation outcomes.

Capture is explicitly requested, not continuous screen recording. The renderer may briefly display a black transition/loading frame; wait for the expected view and capture again before diagnosing a display fault. Captures can contain camera scenes, mnemonic words, addresses or xpubs. Keep them under ignored `dist/`; never add the capture directory to the public site allowlist. Public test records contain only aggregate outcomes, source hashes and view names.

## Exploration on 29 October 2026

The normal app ran on the physical Mini with the Rust LCD, Rust camera and native ZXing worker. A disposable 12-word camera-generated seed was used with explicit user authorization. It was held in app memory, not deliberately written to a card/file, and was cleared by restarting the app after the demo.

| Flow | Observed outcome |
|---|---|
| Startup notice and Home | Operated with software button presses; actual screen captures collected |
| Tools and camera seed preview | Exposed the grayscale/RGB bug below; repeated successfully after the live fix |
| Entropy frame acquisition | Preview displayed varying frames and GOOD ENTROPY; ordinary pool and duplicate/flat-frame checks retained |
| Final image and seed length | Captured/accepted an image, selected 12 words, stopped the camera and released DMA |
| Seed backup/finalization | Viewed all three word pages, explicitly skipped the optional backup quiz, finalized the test seed |
| Address explorer | Chose Native Segwit, derived receive addresses, opened the first address QR |
| Xpub export | Chose single-sig Native Segwit and animated QR; reached derivation details and QR rendering |
| Export address-verification Scan | Opened and cancelled; returned to Home with owner/DMA cleanup |
| Settings | Browsed the menu without deliberately changing persistent settings |

Captured address-QR pixels decoded through the actual ARM ZXing worker under QEMU, returning a 42-byte `bc1` address. A captured xpub QR frame decoded to a 115-byte UR payload. This verifies rendered-pixel decoding, not optical capture, full animated-fragment assembly, transaction signing or an external coordinator round trip. No funded transaction was signed, and smartcard hardware was not exercised.

A local HTML demo gallery and images live under ignored `dist/app-demo/`. Mnemonic-word images are omitted from that gallery. Camera scenes and wallet captures are not published with this runbook.

## Bug found and fixed during exploration

The small-RAM video adapter returned a Pillow `L` frame for every video consumer. The camera-entropy screen uses `getextrema()` as RGB channel pairs; a grayscale frame instead returns two scalar integers. This produced `TypeError: cannot unpack non-iterable int object` and reached the app error screen while leaving the camera owner running.

The compatibility fix converts only full-resolution `display=True` image reads to RGB-shaped grayscale, preserving exact full-resolution Y pixels for ordinary QR reads. Preview-only resizing remains unchanged, and true still capture continues to use the RGB transport. The fix does not weaken the entropy-pool, variation or duplicate-frame checks.

A second guarded integration hook stops an active video stream before the controller shows its normal error destination. If cleanup itself fails, the original error is preserved. Regression tests cover image mode/pixels, compatibility with RGB extrema iteration, camera cleanup ordering/idempotence and preservation of the primary exception. The complete camera Python test suite passed 49 tests after these changes.

The two Python fixes were tested as temporary file bind mounts on this boot. They are committed source changes but **are not in the previously flashed 0.0.39-dev image**. Reboot removes those live file overlays; a new image must be built and boot-tested before calling the fixes persistent. Diagnostic input/capture tooling is likewise not a default firmware feature.

## Evidence and next tests

The earlier three software-controlled Scan/Back cycles are recorded in `reverse-engineering/rkaiq/memory/button-control-hardware-result.json`. The broader exploratory record is `reverse-engineering/rkaiq/memory/app-exploration-2026-10-29.json`. Neither contains mnemonics, QR payloads or camera images.

Remaining checks include repeating the exploration from a rebuilt image, optical QR decoding and coordinator signing/verification, physical button testing, backup quiz, seed recovery and smartcard operations. A successful menu exploration is not a substitute for those flows.

## Native frontend application protocol check

With the current compiled extension and runtime helpers on PYTHONPATH, set `SHIELDSIGNER_FRONTEND_BACKEND=rust` and run:

```sh
python3 native_qr_hardware_check.py --app-root /opt/src \
  --reader /usr/lib/shieldsigner-camera/shieldsigner-qr-reader \
  --report /tmp/new-native-qr-report.json --native-frames
```

Use a fresh report filename. This diagnostic feeds generated public byte-mode QR images through synthetic native socket reception into the actual installed `DecodeQR`. It checks binary/CompactSeedQR/animated-UR handling and worker stop/restart. It touches no camera or GPIO unless the separate `--camera-config` option is supplied. Native-frame synthetic checks should be run without that option; actual GUI/optical tests are a separate milestone. Do not interpret its timing, Python fixture allocations or QEMU execution as ordinary app performance.

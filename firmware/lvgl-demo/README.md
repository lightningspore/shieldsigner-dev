# Luckfox LVGL hardware demo (historical)

This earlier rendering experiment is superseded by the
[LVGL application port](../lvgl-app/README.md). Use that port for the current
image, architecture and acceptance status. This demo remains a separate small
experiment; its memory samples and hardware observations are historical, scoped
results, not current application qualification.

Standalone rendering proof, not a wallet UI migration. Uses upstream LVGL 9.5.0
(commit `85aa60d18b3d5e5588d7b247abf90198f07c8a63`, MIT license in the fetched
source tree). Inspired by the separation in kdmukai's SeedSigner LVGL projects;
this demo uses its own small screen, not their screen implementations.

Build from the repository root:

```
mise run lvgl:demo:build
adb push dist/firmware/work/lvgl-demo/lvgl-demo /tmp/lvgl-demo
adb push firmware/lvgl-demo/run.py /tmp/lvgl-demo-run.py
adb shell chmod 755 /tmp/lvgl-demo
```

Stop the regular app before starting: inspect current PIDs, suspend its
`/start-seedsigner.sh` supervisor with `kill -STOP SUPERVISOR_PID`, then terminate
only its app child with `kill -TERM APP_PID`. Verify camera/QR children are gone.
Do not reuse historical PID numbers. This prevents concurrent GPIO/SPI ownership
and the supervisor's failure/reboot loop.

```
adb shell "nohup sh -c 'exec python3 -u /tmp/lvgl-demo-run.py' </dev/null >/tmp/lvgl-demo.log 2>&1 & sleep 2"
adb shell cat /tmp/lvgl-demo.log
```

Up/Down navigates; Press or KEY1 selects a demo item. KEY3 exits. Items only
update status text; they perform no wallet, seed or camera operations. The
bottom bar animates. **Reboot to restore normal SeedSigner startup.** Installed
application/image files are unchanged; executable, logs, FIFO and capture live
in temporary RAM storage.

LVGL runs in a static ARMv7/musl C process. One 9,600-byte RGB565 partial draw
buffer sends bounded rectangles through a pipe to the Python adapter, which
reuses installed ST7789 initialization/inversion and physical-button handling.
The Python adapter sends rectangles directly to SPI, without Pillow rendering.
It also holds a 115,200-byte screenshot buffer for this demo. This pipe/adapter
is temporary integration glue, not the proposed final frontend architecture.

A mode-0600 local FIFO supports deterministic input tests:
`adb shell 'printf dp > /tmp/lvgl-demo-input'` moves down and selects. The adapter
saves the latest rendered RGB565 stream to `/tmp/lvgl-demo.rgb565`; this is a
software capture of transmitted pixels, not a photograph/readback of the LCD.

## Hardware result, 2026-10-30

Ran on the connected Mini using existing 240x240 ST7789 mapping, SPI mode 0,
10 MHz, normal-color inversion. Native process stayed running and transmitted
partial updates successfully. Injected down/select logged selection index 1
and click count 1; reconstructed capture visually checked. Physical button
mapping is the installed app's mapping; physical presses and panel appearance
still require user observation.

One instantaneous sample: LVGL process PSS 520 KiB; Python adapter PSS
14,839 KiB; neither had swap. This excludes wallet/camera workloads and is not
an application memory comparison. The Python adapter imports existing app
hardware modules, so its footprint is substantial even though C renders pixels.

## Expanded demo (v2)

The current screen replaces the original three status-only items:

- Live camera: installed Rust ISP/capture + native frame receiver and luma
  preview renderer, embedded as a changing LVGL image (240x160). This is a
  grayscale preview, not a new color-processing implementation or QR decoder.
- Public link QR: LVGL QR widget encoding `https://shieldsigner.dev`. No wallet
  or private data is used. A white quiet area surrounds the code.
- Display lab: RGB swatches and an adjustable LVGL bar. The bar is a UI test;
  it does not control electrical backlight brightness.

Left or KEY2 returns to the menu; KEY3 exits. Camera ownership starts only on
its screen and is stopped on Back/exit. The native C frontend and all experimental
adapter/build/diagnostic code stay in this folder. Installed camera/display
interfaces are reused without modifying their source. The camera's latest
preview is passed through a bounded, atomically replaced temporary RGB file;
this is intentionally demo glue, not the final transport design.

Host diagnostics (canonical outputs under ignored `dist/firmware/work/lvgl-demo/`):

```
mise exec -- uv run --with pillow python firmware/lvgl-demo/capture.py camera
mise exec -- uv run python firmware/lvgl-demo/memory.py camera-running
```

Expanded hardware checks: camera opened, live image rendered, Back stopped the
owner, camera reopened, and another Back returned DMA allocations to zero.
Screenshots of camera/QR/display test captured locally; captures are private
local artifacts and are not committed.

### Memory sample (v2, after imports warmed)

| PSS / state | Camera closed | Live camera | After Back |
| --- | ---: | ---: | ---: |
| Native LVGL | 644 KiB | 648 KiB | 648 KiB |
| Python adapter | 16,581 KiB | 18,271 KiB | 16,559 KiB |
| Rust camera process | absent | 8,216 KiB | absent |
| Linux MemAvailable | 21,824 KiB | 14,820 KiB | 21,808 KiB |
| DMA buffer objects | 0 | 1 (3,981,312 bytes) | 0 |
| Combined process threads | 2 | 11 | 2 |

PSS apportions shared resident pages; it is not Python object accounting or
whole-board RAM. DMA/kernel reservations and filesystem cache prevent treating
process sums as total system usage. All sampled demo processes had zero SwapPss.
System zram already held 3,334,144 bytes physically and stayed unchanged across
these samples; it is not an additional per-demo allocation. Camera imports
remain loaded after Back, while the owner and frame pool are released. The
native executable is staged on RAM-backed `/tmp`, so deployment itself also
uses memory outside these process totals. This miniature UI omits real wallet
workflows and cannot establish a fair full-app memory saving.

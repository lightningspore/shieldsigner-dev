# Connected Mini PCB: working LCD and physical buttons

The user identified the actual board in the sibling `seedsigner-luckfox-pico`
repository. Source paths/hashes and routed signals are recorded in
[boards/mini-pcb240.json](boards/mini-pcb240.json). The KiCad files were read only.
This is the Waveshare1.3-inch240x240 board, not the previously assumed separate
FOX_22 bench fixture or the new HOTHMI carrier.

| Signal | RV1103 global GPIO |
| --- | --- |
| LCD CS / clock / MOSI |48 /49 /50 |
| LCD reset / DC / backlight |51 /52 /43 |
| Up / Down / Left / Right / center |57 /59 /56 /54 /58 |
| Key1 / Key2 / Key3 |55 /4 /53 |

Key2 is GPIO0_A4, not GPIO1. GPIO56/57 are button inputs, not LCD outputs.
The old profile used the wrong reset/DC and treated the backlight as a key,
which explains its persistent mask64 and the dark display. `mini-pcb-ui` now
owns the routed pins; `app-ui` selects it. `display.init('mini-pcb240')` is explicit.
The old `bench240` request is rejected on this build. DUT1's loader rejects the
legacy `bench-ui` build, and the wired DUT0 loader rejects app-board profiles.

GPIO43 is driven high for the designed backlight jumper route. UART2 remains
muxed away and its IRQ/IER are disabled; its former RX pad now intentionally
serves as backlight GPIO. Thus `uart_gpio_output` reads0x800 after LCD init,
not zero. Entry still releases both UART pads before acquiring the LCD.
GPIO0_A4 is input-only. Full-duplex SPI/phase4 Pin fixture APIs are blocked on
USB-only app targets because they overlap LCD reset/DC/buttons.

Physical evidence on DUT1: white fill, genuine Home graphics and a captured
local-camera image are visible in the external camera. The user exercised all
eight switches; the raw seen mask is255 with renderer selection/power callbacks.
Final image also passed wrong-profile/fixture API rejection, native RAM settings,
and local camera→LCD→Home restore gates. Physical button evidence was collected
before the final guard/metadata-only build; the pin driver is byte-for-byte the
same source in both build manifests. Camera images stay in ignored local logs.
This establishes basic LCD/input operation, not calibrated colors, full app
startup, readable text from the oblique camera view or continuous preview FPS.

The full Controller/View graph is still incomplete. The next user-requested step
is a continuous preview; repeated five-second32-frame captures are insufficient.

## Continuous preview

`camera.start_preview()`, `next_preview()`, `stop_preview()` and
`preview_status()` retain the existing calibrated Rust AE/AWB sessions across
frames. The sensor stays streaming; CIF memory capture pauses at a completed
boundary while the ISP/display consume the buffer. Two settling frames are
discarded after live sensor control writes. NV12 views are read-only and expire
on the next fetch, stop or capture; consumers must finish before fetching again.
Do not retain them as snapshots. Capture/settings writes and camera reinit are
rejected during an active preview. Always stop in `finally`.

On an `app-ui` build loaded on DUT1, run
`mise run baremetal:camera:preview:demo`. The frozen cooperative adapter runs for
two minutes or until center/Key3, then stops the camera and restores native Home.
USB Ctrl-C is also supported. This is a preview adapter, not yet the Scan View,
QR decoder or entropy flow. `baremetal:camera:preview:lcd:gate` measures ninety
camera→LCD frames; `baremetal:camera:preview:gate` checks headless frame changes,
heap cleanup and a subsequent legacy capture on the wired DUT0.

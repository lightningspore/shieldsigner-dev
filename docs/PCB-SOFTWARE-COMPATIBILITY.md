# PCB and tested firmware compatibility

Reviewed 2026-10-31 against local KiCad pad nets, pinned application source,
reviewed I/O transforms and frozen compiled-profile metadata. This is a read-only
source/electrical compatibility audit; no board was powered, flashed or rebuilt.

**The carrier mapping matches the `carrier` application profile, but the currently
tested `lvgl-dev.cb6170a37a5a` image uses `base-fork` and must not be used unchanged
on either carrier PCB.** This is a firmware-profile mismatch, not evidence that
the carrier should be rewired to match the separate bench display/button board.

The order target is the main `variants/lcd-module-2.8` artwork revision
**0.0.9-dev**, retaining the main board's always-on topology and 35 fitted SMT
components / 17 purchasing SKUs. The separate `lcd-backlight-pwm` 0.0.8-dev
candidate is not the order target. Manufacturing exports must be regenerated and
matched to the selected main revision; this audit does not promote a cart.

## Findings and severity

| Severity / gate | Finding | Required action |
|---|---|---|
| **Critical — before carrier power-up** | Bench firmware drives GPIO56/57, carrier Left/Up switch nets, as LCD DC/reset outputs. Pressing those switches can short a driven high output to ground. | Use reviewed **carrier** pins, not the current bench image. Do not solve this by blindly swapping connector pins. |
| **High — functional bring-up** | All eight bench button assignments differ; UART2 is deliberately disabled and PCSC startup held in the bench profile. | Build/select a carrier-profile image; verify actual GPIO requests, internal pulls and UART resource policy. |
| **High — correct LCD configuration** | HOTHMI eight-pin wiring, 10 MHz limit and 320×240 geometry differ from the tested 240×240 module. | Keep carrier CS jumpers, explicit 10 MHz profile and `st7789_320x240` setting; qualify colors/orientation/clock physically. |
| **High — optional PWM only** | Dedicated PWM exists only on the separate candidate. Current profile has `bl: disabled`; no application brightness/PWM path is qualified. | Order main board for always-on behavior. If promoting PWM later, regenerate its own assets and implement/qualify the pinmux/control path. |
| **Medium — first article** | 1.8 V keys rely on correct-domain pulls; LCD regulator/load, assembly orientation and power behavior remain physical checks. | Verify continuity and rails before inserting modules, then test one article before quantity assembly. |
| **No new carrier conflict found** | SPI, voltage-domain topology, reader UART crossing and native camera connection agree with the intended carrier design. | Preserve these nets; schematic/DRC correctness does not prove assembled operation. |

## Exact Luckfox header map

Physical pin numbers below are **U202 module-header pad numbers**, not Linux
GPIO numbers. GPIO global number = bank × 32 + line. `/dev/gpiochipN` must still
be confirmed on the actual image; labels alone do not prove runtime numbering.
All GPIO pins listed are 3.3 V except pins 19/20, which are **1.8 V**.

| U202 pin | SoC / global GPIO | Main carrier net and intended function | `carrier` runtime |
|---:|---|---|---|
| 1 | VBUS | `+5V` | Power input |
| 2 | GND | `GND` | Return |
| 3 | 3V3 OUT | `+3.3V` | Host output; default backlight enable only |
| 4 | GPIO1_B2 / 42 | `UART_TX` → R602 → SEC1210 U601.11 RX | UART2 TX |
| 5 | GPIO1_B3 / 43 | `UART_RX` ← R603 ← SEC1210 U601.14 TX | UART2 RX |
| 6 | GPIO1_C0 / 48 | `Net-(JP203-B)` → JP203/JP205 → `RPI_SPI_CS` | SPI0 CS0, `/dev/spidev0.0` |
| 7 | GPIO1_C1 / 49 | `LCD_SCLK` | SPI0 clock |
| 8 | GPIO1_C2 / 50 | `LCD_MOSI` | SPI0 MOSI; display is write-only |
| 9 | GPIO1_C3 / 51 | `LCD_RST` | gpiochip1 line19 output |
| 10 | GPIO1_C4 / 52 | `LCD_DC` | gpiochip1 line20 output |
| 11 | GPIO1_C5 / 53 | `Key3`, SW508 → GND | gpiochip1 line21 input/pull-up |
| 12 | GPIO1_D0 / 56 | `JoystickLeft`, SW501 → GND | gpiochip1 line24 input/pull-up |
| 13 | GPIO1_D1 / 57 | `JoystickUp`, SW502 → GND | gpiochip1 line25 input/pull-up |
| 14 | GPIO1_D2 / 58 | `I2C-SDA`, no other main-board endpoint | Unused; candidate changes this to `LCD_PWM` |
| 15 | GPIO1_D3 / 59 | `I2C-SCL`, no other endpoint | Unused |
| 16 | GPIO1_C6 / 54 | `JoystickPress`, SW503 → GND | gpiochip1 line22 input/pull-up |
| 17 | GPIO1_C7 / 55 | `JoystickDown`, SW504 → GND | gpiochip1 line23 input/pull-up |
| 18 | GPIO0_A4 / 4 | `JoystickRight`, SW505 → GND | gpiochip0 line4 input/pull-up |
| 19 | GPIO4_C0 / 144, **1.8 V** | `Key1`, SW506 → GND | gpiochip4 line16 input/pull-up |
| 20 | GPIO4_C1 / 145, **1.8 V** | `Key2`, SW507 → GND | gpiochip4 line17 input/pull-up |
| 21 | GND | `GND` | Return |
| 22 | 1V8 OUT | Explicitly unconnected | Do not tie to 3.3 V |

There are no external 3.3 V pull-ups on Key1/Key2: the only carrier load is a
normally open switch to ground. That topology is appropriate for a 1.8 V input.
Confirm GPIO4 pinmux/pulls and actual released/pressed readings; the pinned button
opener can retry without `pull_up` after GPIO errors. Do not enable conflicting
PWM10/11 pinmux functions on these button pads.

## Why the working bench image is incompatible

The frozen camera bundle manifest records `ioProfile: base-fork`, and its
`payload/kernel-camera-abi.json` records `/serial@ff4c0000` UART2 as disabled.
The base-fork resource policy holds `S60pcscd` because GPIO42/43 belong to buttons
on that bench assembly. The current image is not an implicit carrier profile.

| Function | Tested base-fork global GPIO | Required carrier global GPIO |
|---|---:|---:|
| LCD DC | **56** (carrier Left switch) | 52 |
| LCD reset | **57** (carrier Up switch) | 51 |
| Up | 58 | 57 |
| Down | 53 | 55 |
| Left | 59 | 56 |
| Right | 54 | 4 |
| Press | 52 | 54 |
| Key1 | 55 | 144 |
| Key2 | 43 (carrier UART RX) | 145 |
| Key3 | 42 (carrier UART TX) | 53 |

The earlier `lcdpwm` fork mapping is also a distinct profile: its display pins
match the carrier but five button semantics differ. Neither a fork branch name
nor the fact that both screens use ST7789 establishes compatibility.

## HOTHMI LCD and default straps

Carrier J701 numbering reverses the HOTHMI vendor header numbering. Verify the
actual module's marked pin1 before mating; the eight-pin modules discussed in
research are not interchangeable by controller name alone.

| Carrier J701 pin | HOTHMI vendor pin | Net / function |
|---:|---:|---|
| 1 | 8 | `RPI_BACKLIGHT` / BL_E |
| 2 | 7 | `LCD_RST` |
| 3 | 6 | `LCD_DC` |
| 4 | 5 | `RPI_SPI_CS` |
| 5 | 4 | `LCD_SCLK` |
| 6 | 3 | `LCD_MOSI` |
| 7 | 2 | GND |
| 8 | 1 | `LCD_3V3` / VCC |

Factory default: **JP201/JP203/JP205 closed; JP202/JP204/JP206 open**.
JP201 holds BL_E high from host 3.3 V: always on, with no brightness software.
JP203+JP205 connect host CS to LCD CS. Leave JP206 open; grounding CS is a
different bus mode, not the intended default. On the main board, the legacy
JP202/JP204 branch shares host CS rather than exposing an independent PWM output.
Do not repurpose it as independent brightness control.

LCD VCC is the separate U701 regulator output `LCD_3V3`; it is not shorted to the
Luckfox 3.3 V output. U701 takes +5 V and has enable tied to +5 V. BL_E is a logic
enable, not GPIO-supplied backlight current. Regulator current/temperature and
startup logic levels still require measurement on the purchased module.

The retained HOTHMI drawing specifies a minimum write cycle of 66 ns; the
reviewed profile sets **10 MHz**, not the upstream 40 MHz default. Current
carrier transforms already implement that clock, but a physical scope check is
still needed. Color-inversion behavior was established on the bench module;
HOTHMI RGBW, inversion, rotation and full 320×240 extents need their own check.

LVGL's `renderer_bridge.py`, `runtime.py` and `luckfox.py` contain a 320×240 path,
selected by settings key **`display_config: st7789_320x240`**. Default is 240×240.
That source support is not a HOTHMI physical acceptance result. The separate
PIL/Rust frame wrapper `firmware/lcd-rs/python/shieldsigner_lcd_driver.py` currently
rejects geometry other than 240×240. Active LVGL does not install that wrapper,
but do not promise the retained PIL rollback frontend works at 320×240 unchanged.

## Required firmware integration

No firmware was changed for this audit. The explicit selection points are:

- `scripts/prepare-camera-image.py --io-profile carrier` selects the intended
  carrier map; use `--variant dev --app-startup automatic --memory-profile
  zram16-lzo --lcd-backend rust --frontend-backend rust` when preparing a comparable
  development bundle. Its compiled kernel proof must match the carrier profile;
  the frozen base-fork proof must not be relabeled. Follow the documented kernel
  probe/rebuild cycle if a matching proof is not available.
- `configure-image-io-profile.py ... --profile carrier` changes only FOX_22 SPI
  speed to 10 MHz in the pinned source. `configure-hothmi-display.py` independently
  checks carrier DC52/reset51, kernel-managed CS and the same 10 MHz setting.
  A plain runtime `--profile` flag on `app.py` does not select these pins.
- Pass an explicitly verified **carrier camera base** to
  `mise run firmware:stage --name UNIQUE_NAME --camera PATH_TO_CARRIER_BASE`.
  The command's default camera base is inherited from the currently selected
  image, which is base-fork. Do not accept that default for this PCB.
- For OS building, `SHIELDSIGNER_CAMERA_BUNDLE` selects the resulting combined
  bundle; `SHIELDSIGNER_CAMERA_BACKEND=rust`, `SHIELDSIGNER_IMAGE_VARIANT=dev` and
  `SHIELDSIGNER_READER_VARIANT=UR2` select the corresponding build paths. There is
  no current `SHIELDSIGNER_IO_PROFILE` switch: profile travels in the bundle.
- Verify packed `ioProfile`, actual installed `io_config.json`, DTB pinmux and
  UART2 state, startup resources, settings geometry and 10 MHz clock before
  normal use. UART2 reader availability requires carrier resource policy and
  hardware/service qualification; this audit does not expand smartcard scope.

## Separate PWM candidate

The 0.0.8-dev candidate changes only the dedicated backlight route: U202 pin14 /
GPIO1_D2 / gpiochip1 line26 / global58 becomes `LCD_PWM`, feeding JP202. R703
5.1 kΩ pulls it low. With JP201 closed and JP202 open it remains always on.
Optional PWM uses JP201 open and JP202 closed; never close both together.

PWM requires disabling conflicting I2C3 on that pad and enabling **PWM0_M1** in
the final DTB, then implementing a controller identified from the running device
tree rather than guessed `pwmchip` numbering. Current `bl: disabled` does none of
that. Low=off, high=on; PWM frequency/duty response, startup/shutdown and possible
camera flicker remain unqualified. This is not a reason to change the main order
or to claim existing software brightness support.

## Camera, power and first article

The SC3336 camera attaches to the Luckfox's native camera/FPC interface; neither
carrier routes those camera lanes through the LCD/button headers. No missing
carrier camera connector or SPI/pin conflict was found. Existing Linux camera/ISP
and Rust/ZXing behavior can be retained with the correctly profiled kernel; it
still needs testing with the larger display and assembled power load.

J301 USB-C and optional J302 both feed +5 V; J302 pin1 is +5 V, pin2 GND. They
have no source isolation or reverse-polarity protection. Use one regulated source
at a time; account for the Luckfox module USB input too. USB power does not prove
USB data/ADB connectivity through the carrier receptacle.

Before ordering, match Gerbers/BOM/CPL to the chosen main artwork revision and
retain the default straps. Before powering the first article, verify connector
orientation, no rail shorts, +5 V/LCD_3V3/host3V3 and correct LCD vendor pin order.
Then use the carrier image and check all buttons/pulls, RGBW/full extents, supply
current, regulator temperature and camera transitions. Native ERC/DRC and these
net checks do not prove soldering, connector fit, actual voltage, pinmux, optics
or physical timing. A first article remains necessary.

## Evidence

- [Carrier pinout audit](../variants/lcd-module-2.8/pinout-audit.json),
  [header map](../variants/lcd-module-2.8/header-map.json),
  [module audit](MODULE-PINOUT-AUDIT.md), [host pin data](luckfox-mini-pinout.json)
- [Main native checks](../variants/lcd-module-2.8/check-results.json) and
  [PWM candidate checks](../variants/lcd-backlight-pwm/check-results.json)
- [Earlier fork mapping audit](../reverse-engineering/rkaiq/fork-display-button-map-audit.json)
  and [base-fork physical observation](../reverse-engineering/rkaiq/base-fork-display-hardware-validation.json)
- [Profile transform](../scripts/configure-image-io-profile.py),
  [HOTHMI clock guard](../scripts/configure-hothmi-display.py),
  [bench I/O fixture](../firmware/bench-profiles/base-fork-io-config.json)
- [Current firmware acceptance](../firmware/lvgl-app/docs/ACCEPTANCE.md)

Pad maps were independently parsed from both native PCB files. Pre-artwork main
SHA-256: `b4eb7a7cef3f026bfc332a19980727a165de9ea826e4eb25dcc68e2c458004b7`;
PWM candidate: `c5644d7a6eb18ef013d008f880bb0813b05b33892b87eaa982da4638e973521a`.
The main artwork change must retain these electrical mappings; its new file hash
and regenerated checks belong to the final manufacturing/readiness record.

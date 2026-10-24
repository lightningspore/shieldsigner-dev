# Luckfox Mini and HOTHMI pinout audit

Reviewed 2026-10-24, pill PCB **0.0.6-dev**, SHA-256 `1b1c12a3a1a1300026a2a120e2115c351f9ba0c868ea393dbc02c223cc29a110`.

**PCB signal assignments and supply topology pass. One firmware correction is required: use 10 MHz SPI for the selected HOTHMI display.** No PCB change is indicated by this audit. This is a drawing/netlist review, not a powered hardware test. The checkout files remain the same revision.

## Sources and method

- Luckfox manufacturer [Mini A/B pinout diagram](https://wiki.luckfox.com/assets/images/LUCKFOX-PICO-MINI-GPIO-dd48b2490c683f3a1bafc86f54bf1e6e.webp), linked from its [GPIO documentation](https://wiki.luckfox.com/Luckfox-Pico-Plus-Mini/GPIO/), and the retained [Mini schematic](../reference/pdfs/Luckfox-Pico-Mini.pdf).
- HOTHMI [HTM-TFT028A16-SPI manufacturer specification](../reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf): pages 5–6 connector drawing/table, 7–8 voltage limits, 11 serial timing, 12 power sequence. The outline and timing table were visually inspected because text extraction omits the timing table.
- [AP2112 specification](../reference/pdfs/Diodes-AP2112.pdf), U701 pin order and regulator limits.
- Actual native PCB pad nets, including both pad instances per Luckfox pin, solder-jumper copper defaults, and fresh KiCad ERC/DRC/parity checks.
- Pinned application [FOX_22 mapping](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/src/seedsigner/hardware/io_config.json) and [display driver](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/src/seedsigner/hardware/displays/ST7789.py). A public-source mapping snapshot is retained under `reference/research/firmware/`.
- Pinned OS `e7589465aff172f4f510ad46d18776ccc8d2c203`, `opt/luckfox/os-build.sh`/`build-local.sh` SPI override and `files/configure-gpio.sh` Mini button setup. The SPI pinctrl includes CLK/MOSI/CS, deliberately omitting MISO so pin 9 can be reset. This checks source intent; the installed DTB is not measured here.

## All Luckfox Mini pins

These are **physical module pins**, viewed using the manufacturer's component-side diagram: USB at the top, pin 1 upper left and pin 22 upper right. The carrier mounts the module underneath using its reversed footprint. Do not mirror the manufacturer's numbers again when assembling. Match USB position, 5 V and both grounds with power off before inserting the module.

| Pin | Manufacturer function | Carrier assignment | Result |
|---|---|---|---|
| 1 | VBUS | +5V from USB-C or J302 | Correct input |
| 2 | GND | GND | Correct |
| 3 | 3V3 OUT | +3.3V; backlight-enable pull-high only | Correct output; not LCD power |
| 4 | GPIO1_B2 / UART2 TX | UART_TX → R602 → SEC1210 pin 11 RX | Correct direction |
| 5 | GPIO1_B3 / UART2 RX | UART_RX ← R603 ← SEC1210 pin 14 TX | Correct direction |
| 6 | GPIO1_C0 / SPI0 CS0 | JP203 → JP205 → LCD CS | Correct default path |
| 7 | GPIO1_C1 / SPI0 CLK | LCD_SCLK | Correct |
| 8 | GPIO1_C2 / SPI0 MOSI | LCD_MOSI | Correct |
| 9 | GPIO1_C3 / SPI0 MISO | LCD_RST, gpiochip1 line 19 | Correct GPIO reuse; omit MISO pinmux |
| 10 | GPIO1_C4 | LCD_DC, gpiochip1 line 20 | Correct |
| 11 | GPIO1_C5 | Key3, gpiochip1 line 21 | Correct |
| 12 | GPIO1_D0 | Left, gpiochip1 line 24 | Correct |
| 13 | GPIO1_D1 | Up, gpiochip1 line 25 | Correct |
| 14 | GPIO1_D2 / I2C3 SDA | I2C-SDA label only, no other endpoint | Unused, no conflict |
| 15 | GPIO1_D3 / I2C3 SCL | I2C-SCL label only, no other endpoint | Unused, no conflict |
| 16 | GPIO1_C6 | Press, gpiochip1 line 22 | Correct |
| 17 | GPIO1_C7 | Down, gpiochip1 line 23 | Correct |
| 18 | GPIO0_A4 | Right, gpiochip0 line 4 | Correct |
| 19 | GPIO4_C0, **1.8V** | Key1 switch to GND, gpiochip4 line 16 | Correct; internal pull-up only |
| 20 | GPIO4_C1, **1.8V** | Key2 switch to GND, gpiochip4 line 17 | Correct; internal pull-up only |
| 21 | GND | GND | Correct |
| 22 | 1V8 OUT | Explicitly unconnected | Correct; never tie to 3.3V |

The LCD signals are all on the Mini's 3.3 V GPIO bank. Pins 19/20 have no external pull-up or supply connection: their only carrier load is a normally-open switch to ground. The app requests pull-ups and the OS Mini setup configures the corresponding GPIO4 inputs. Do not add 3.3 V pull-ups, or use these as 3.3 V outputs. Other buttons likewise depend on firmware pull-ups. I2C3 is not used for this SPI display.

## LCD connection and orientation

Use **HOTHMI HTM-TFT028A16-SPI, no touch, J1 2.54 mm row**. Its separate 2 mm connector is not used. Module numbering is intentionally opposite the carrier's J701 numbering. Front/back views must not be confused; verify every signal label rather than matching equal numbers.

| HOTHMI J1 | Function | Carrier J701 | Source |
|---|---|---|---|
| 1 | VCC | 8 | LCD_3V3, U701 output |
| 2 | GND | 7 | Common ground |
| 3 | SDA | 6 | Mini pin 8, SPI MOSI |
| 4 | SCL | 5 | Mini pin 7, SPI clock |
| 5 | /CS | 4 | Mini pin 6 through JP203/JP205 |
| 6 | D/C | 3 | Mini pin 10, GPIO1_C4 |
| 7 | /RES | 2 | Mini pin 9, GPIO1_C3 |
| 8 | BL_E | 1 | Mini 3.3 V output through JP201 |

SDA/SCL here mean **SPI**, not I2C. The display is write-only; there is no missing MISO connection. BL_E is a logic enable, not the 120 mA backlight supply. Leave JP201/203/205 closed and JP202/204/206 open. BL is then always enabled, CS is kernel-managed, and the GPIO used for CS is not simultaneously used for dimming.

## Power rails

- USB-C VBUS and J302 pin 1 feed **the same regulated +5V rail**, supplying Mini pin 1, SEC1210 and U701. J302 pin 2 is ground. Use one input source at a time, including the Mini's own USB connector; there is no source isolation or reverse-polarity protection.
- U701 AP2112K pin 1 VIN and pin 3 EN are +5V; pin 2 is GND; pin 4 NC; pin 5 supplies **LCD_3V3**. Input/output capacitors C701/C702 are 10 µF nominal, each to ground. This is the correct regulator pinout.
- LCD_3V3 has exactly three component endpoints: U701 output, C702 and J701 VCC. It is **not joined to Mini pin 3**. Neither 5 V nor 1.8 V is connected to the LCD supply or its data pins.
- The LCD requires 3.1–3.6 V, nominal 3.3 V. HOTHMI specifies signal inputs no higher than IOVCC + 0.3 V and no higher than 3.6 V. Both host GPIO and LCD use nominal 3.3 V; measure startup/shutdown as well as steady-state levels because the supplies come from different regulators.
- AP2112's 600 mA headline rating is not a thermal guarantee here. At 150 mA, 5→3.3 V dissipates about 0.255 W. HOTHMI's 120 mA typical figure is the backlight, not guaranteed maximum total module current. Current, rail droop, regulator temperature and enclosure ambient remain first-article acceptance measurements.

## Required firmware correction: 10 MHz SPI

The pinned driver defaults to **40,000,000 Hz** when `spi_hz` is omitted, as in FOX_22. HOTHMI page 11 specifies write-clock cycle **at least 66 ns**, high/low pulses at least 15 ns and data setup/hold at least 10 ns. The cycle alone limits the specified write rate to approximately **15.15 MHz**. A 40 MHz request (25 ns period) exceeds that requirement. The driver's generic comment describing 40 MHz as rated does not qualify this particular module.

Use **10,000,000 Hz**, mode 0, SPI bus 0/device 0 and kernel-managed CS. A 100 ns cycle gives nominal 50 ns high/low pulses; actual edge quality, setup/hold and CS timing still require measurement. Start at a lower speed if needed during bring-up.

Apply the checked patch to an application checkout **before packaging the rootfs**, or to the mounted/staged rootfs configuration before repacking:

```sh
mise exec -- uv run python scripts/configure-hothmi-display.py /path/to/app/src/seedsigner/hardware/io_config.json
# For a staged image, the corresponding path is:
# /path/to/rootfs/opt/src/seedsigner/hardware/io_config.json
```

The tool validates the reviewed display pins, changes only FOX_22 `display.spi_hz`, and can be run repeatedly. It refuses unexpected profiles/settings. It has been verified against the pinned public config, **not applied to an installed or rebuilt image in this audit**. The existing `os:build` wrapper does not automatically apply this patch; verify the final packaged config explicitly. A successful old OS build does not close this correction.

## Reproduce and finish on hardware

```sh
mise run variant:lcd:pinouts
mise run variant:lcd:check
```

The first command checks all module/LCD pad nets, default jumper paths, separated rails, 1.8 V button endpoints, UART directions and pinned app mappings. It also verifies that the 10 MHz patch is idempotent and changes no other config. Results are retained in `variants/lcd-module-2.8/pinout-audit.json`. Native ERC/DRC/parity ran with zero violations, zero unconnected items and zero exclusions.

Before first power, check continuity from actual module VCC/GND and all eight LCD pins to the identified carrier endpoints. Confirm the purchased modules match these drawings. Then verify final-image FOX_22 selection, `/dev/spidev0.0`, reset as GPIO rather than MISO, actual SPI clock/CS/DC/reset waveforms, all eight buttons, LCD initialization/rotation/colors, and the power/thermal measurements above. These remaining checks are physical bring-up work, not evidence of a known PCB miswire.

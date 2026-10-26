# Luckfox Mini pinout & signal map

All **22 header pins** of the Luckfox Pico Mini A/B, with electrical capabilities, voltage domains and actual ShieldSigner connections. The diagram uses the manufacturer's component-side orientation: **USB at the top, pin 1 upper left, pin 22 upper right**. Choose the released 0.0.7 carrier or the 0.0.8 PWM candidate. Always-on backlight remains the default on both.

## How to read the diagram

The gold pad numbers are **physical header pin numbers**. `GPIO1_D2` identifies a processor pad; **GPIO #58** is the manufacturer's legacy global GPIO number. These are three different numbering systems. For example, physical **pin 14** is **GPIO1_D2**, bank **1**, line **26**, legacy global number **58**. Under the pinned app’s bank/line convention this corresponds to `/dev/gpiochip1`, line 26; the app does not yet configure pin 14 for brightness. Identify chip labels on the actual running image before using a chip path. A Linux `pwmchip` number is a separate runtime identifier.

GPIO offsets are `group × 8 + bit`, with A=0, B=1, C=2, D=3. The legacy global number is `bank × 32 + offset`. Suffixes `_M0`, `_M1` and `_M2` select alternative physical routes for a peripheral. They do not create additional independent peripheral controllers.

Colored labels show documented serial, PWM and ADC alternatives. **One pad cannot perform all of its alternate functions at once.** Device-tree configuration selects the peripheral or GPIO role. The label beneath the capabilities describes what ShieldSigner actually connects there. Additional SoC debug/parallel-bus muxes are outside this serial/PWM/ADC reference.

The diagram is an orientation illustration, not a dimensioned mechanical drawing. The carrier mounts the module on its underside; do not mirror the manufacturer's pin numbering again. Match USB orientation, pin 1 (+5 V) and both grounds before inserting it.

## Voltage levels and buttons

**Pins 19 and 20 are 1.8 V GPIO**, respectively GPIO4_C0 / Button 1 and GPIO4_C1 / Button 2. Our wiring matches the retained upstream board: each switch connects its input directly to ground. Upstream's FOX_22 app configuration requests an internal pull-up, so a released button reads high in its own 1.8 V domain and a pressed button reads low. There is no carrier 3.3 V pull-up on either input. Confirm that the final OS enables the inputs and pulls.

**Pin 22 is a 1.8 V power output**, not another GPIO, and is unconnected on both carriers. It is not the source used to power the buttons. The other exposed GPIO pins use a 3.3 V I/O domain. Treat these voltage domains as wiring limits; the presence of an ADC/PWM alternative does not make a pad 3.3 V or 5 V tolerant.

Pin 1 is the 5 V supply connection. USB-C VBUS and J302's +5 V pin share that carrier rail, without source isolation. Use one input source at a time, including the Mini's own USB connector. Pin 3 is the Mini's 3.3 V **output**: it supplies the default backlight-enable high level and TP802, while the LCD's operating power comes from the separate U701 regulator on **LCD_3V3**. The regulators' outputs are not tied together.

## Which interfaces are already used?

- **SPI0:** pins 6–8 provide LCD CS0, clock and MOSI. Pin 9's MISO-capable pad is deliberately used as the display-reset GPIO. The selected screen is write-only, so configure SPI without MISO. Set the HOTHMI SPI clock to 10 MHz; the pinned application otherwise defaults to 40 MHz. See the [timing audit](MODULE-PINOUT-AUDIT.md).
- **UART2:** pins 4/5 serve the SEC1210 smartcard reader through R602/R603, with TX crossing to RX. Keep the UART2 serial console disabled so it cannot occupy the reader's UART. The intended reader device is `/dev/ttyS2:SEC1210UR2`; confirm it in the final image.
- **GPIO buttons:** pins 11–13 and 16–20 are inputs with pull-ups. The Mini's commonly demonstrated PWM10_M1 and PWM11_M1 use pins 16/17, which are our joystick press/down inputs. Do not enable those default PWM examples for this carrier.
- **I2C:** the LCD labels SDA/SCL refer to **SPI MOSI/clock**, not I2C. Released pin 14 / I2C3 SDA and pin 15 / I2C3 SCL have no external carrier endpoint. The PWM candidate reserves pin 14 for LCD brightness control. I2C4's alternate pins 8/9 are already LCD data/reset; its presence in the capability list does not give us a free I2C bus.
- **Optional backlight PWM:** the 0.0.8 candidate routes physical pin 14 / GPIO1_D2 / PWM0_M1 through JP202 to BL_E. Disable I2C3 on that pad before enabling PWM0_M1. PWM0_M0 on the module's USER-button pad is another route of the same PWM0 controller, not another independent output. HOTHMI specifies high/on and low/off for BL_E; PWM frequency and brightness response still need a physical screen test.

## Always-on and optional PWM

| Mode | JP201 | JP202 | Result |
| --- | --- | --- | --- |
| **Always on — default on both revisions** | Closed | Open | Backlight enabled without brightness firmware |
| **Optional PWM — 0.0.8 candidate only** | Open | Closed | Dedicated pin 14 drives BL_E; R703 pulls it low/off when undriven |

Keep JP203/JP205 closed and JP204/JP206 open. Change straps with power disconnected; never close both JP201 and JP202. The released 0.0.7 board does not have the candidate's dedicated pin-14 route. Its legacy backlight option instead repurposes the CS path and is not the independent PWM feature shown for the candidate.

The [candidate's native design and checks](../variants/lcd-backlight-pwm/README.md) are separate from the existing released manufacturing bundle and saved JLC cart. This documentation does not change the cart or claim that the optional brightness firmware is installed.

## Other module connections

| Connection | Location / function | Carrier use |
| --- | --- | --- |
| USER | On-module button, GPIO1_A2, legacy GPIO 34; PWM0_M0 alternative | Not a numbered carrier-header pin |
| ACT | On-module ACT indicator, GPIO3_C6, legacy GPIO 118 | Not a numbered carrier-header pin |
| TXP / TXN / GND / RXP / RXN | Separate Ethernet pads below the main pin rows | Not wired by this carrier; require appropriate Ethernet interface hardware |
| Camera FPC | Dedicated module camera connector | Separate camera cable, outside the 22-pin header |
| Mini USB | Module's USB interface | Distinct from the carrier's power-only USB-C connector |

## Audit results and source discrepancy

The [machine-readable check report](luckfox-pinout-check.json) verifies **44 native pad instances per board** (two pads per physical header pin), **35 mux alternatives** against a pinned SDK source, all **17 GPIO numbering/domain entries**, eight app button mappings and both display GPIO mappings. It also checks physical row order, UART crossover, isolated LCD power, candidate PWM endpoints, and each documented button's actual switch reference. Both released and candidate header assignments match the reviewed data. The check runs whenever the static site is built, so a changed PCB mapping cannot silently leave this diagram stale.

One manufacturer drawing discrepancy is documented: the official GPIO image places **SPI0 CS1 on pin 15 / GPIO1_D3**. The retained Mini schematic and SDK `spi0m0_cs1` instead assign **GPIO1_D2 / physical pin 14**. This diagram follows those agreeing sources. ShieldSigner uses **CS0 on pin 6**, so the discrepancy does not affect our display wiring. The candidate's pin-14 **PWM0_M1** mapping is independently confirmed by the SDK.

The earlier supply prose also omitted test point TP803: LCD_3V3 has **four** component endpoints—U701 output, C702, J701 VCC and TP803. That prose is corrected; the PCB wiring was already correct.

This audit checks drawings, native nets and pinned source configuration. Final-image pinmuxes, live GPIO-chip identities, pull-ups, rail sequencing, physical continuity, SPI timing and the actual screen's PWM response remain bring-up measurements.

## Primary sources and reproduction

- [Luckfox Mini A/B GPIO diagram and numbering guide](https://wiki.luckfox.com/Luckfox-Pico-Plus-Mini/GPIO/).
- [Luckfox SDK pinctrl source, pinned commit 824b817](https://github.com/LuckfoxTECH/luckfox-pico/blob/824b817f889c2cbff1d48fcdb18ab494a68f69d1/sysdrv/source/kernel/arch/arm/boot/dts/rv1106-pinctrl.dtsi). This shared RV1103/RV1106-family pinctrl source verifies each serial/PWM/ADC pad listed here; the Mini's actual header/voltage mapping comes from the manufacturer diagram and schematic.
- Retained [Mini schematic](../reference/pdfs/Luckfox-Pico-Mini.pdf), [HOTHMI specification](../reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf) and [upstream reference provenance](../reference/provenance.json).
- [Official PWM and pinmux configuration](https://wiki.luckfox.com/Luckfox-Pico-Plus-Mini/PWM/).
- [Pinned FOX_22 application mapping](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/src/seedsigner/hardware/io_config.json).

Run `mise run variant:lcd:pinout-diagram` for the focused diagram audit, and `mise run variant:lcd:pinouts` for the existing rail/default-jumper/application audit. Review data lives in `docs/luckfox-mini-pinout.json`; source snapshots and their recorded SHA-256 hashes are retained under `reference/pinouts/` and `reference/pdfs/`.

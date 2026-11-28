# Display and full-size Pico pinout review

The current native board's checked pin assignments are recorded in
[pinout-review.json](pinout-review.json), bound to its PCB SHA-256. The review
covers all 40 Pico/Pico Plus positions, J701's eight signals, J702's 14 positions
and the default power/backlight/CS straps. It does not qualify physical fit or
powered firmware operation. The full-size host physical pin numbers differ from
the Mini numbers in the main project's older guides.

## Waveshare 2inch LCD Module — SKU 17344

Exact user-selected product:
[Waveshare product page](https://www.waveshare.com/2inch-lcd-module.htm),
[manufacturer wiki](https://www.waveshare.com/wiki/2inch_LCD_Module).
This is the 240×320 ST7789V/VW SPI module, not a Pico display board or a HAT.

Retained manufacturer documents:

- [Module schematic, two pages](reference/Waveshare-2inch-LCD-Module-Schematic.pdf)
  ([official PDF](https://files.waveshare.com/upload/e/ee/2inch_LCD_Module_SchDoc.pdf)).
  Page 1 gives J1/J2 numbering and the backlight circuit; page 2 shows PCB orientation.
  This is the module schematic, not a complete controller datasheet.
- [Dimension drawing](reference/Waveshare-2inch-LCD-Module-Dimensions.jpg)
  ([official image](https://www.waveshare.com/img/devkit/LCD/2inch-LCD-Module/2inch-LCD-Module-size_960.jpg)).
- [Rear photograph and connector labels](reference/Waveshare-2inch-LCD-Module-Rear.jpg).
- [Original URLs, retrieval timestamp and SHA-256 hashes](reference/Waveshare-2inch-LCD-Module-Sources.json).

The schematic's J1 numbering runs opposite carrier J701 numbering. Its PH2.0
connector J2 uses another numbering convention. Match signal labels, not equal
pin numbers or cable colors.

| Waveshare J1 | Signal | Carrier J701 | Full-size Pico/Plus physical pin |
|---:|---|---:|---|
| 1 | VCC | 8 | Dedicated LCD_3V3 regulator, not host 3V3 |
| 2 | GND | 7 | Common ground |
| 3 | DIN / MOSI | 6 | 15 |
| 4 | CLK | 5 | 14 |
| 5 | CS | 4 | 12 through default JP203/JP205 |
| 6 | DC | 3 | 7 |
| 7 | RST | 2 | 16; GPIO reuse of SPI MISO |
| 8 | BL | 1 | 36 / host 3V3 through JP201, always on |

Use **3.3V supply and 3.3V logic** for this carrier connection. Do not feed the
Waveshare module 5V while using the carrier's 3.3V logic: its wiki requires
matching supply and logic voltages. The retained schematic has an onboard
backlight transistor; BL is its control input, not a GPIO-powered LED supply.
Keep JP201/JP203/JP205 closed and JP202/JP204/JP206 open for the default build.

Electrical pin order matches J701. Mechanical interchangeability is separate:
the module is **58×35mm**, with **53×30mm mounting centers** derived from the
dimension drawing's 2.5mm corner offsets. These differ from the HOTHMI mounting
pattern. The PH2.0 cable connector does not mate directly with the carrier's
2.54mm J701 socket. A signal-matched cable or fitted 2.54mm header and separate
mounting arrangement need physical verification. No PCB or enclosure change was
made for this smaller display in this review.

Firmware must use the Waveshare 2-inch 240×320 panel initialization/rotation,
the carrier GPIO mapping and a write-only SPI configuration with MISO disabled.
Sharing an ST7789 controller with HOTHMI does not prove identical initialization.

## Other reviewed modules

- HOTHMI **HTM-TFT028A16-SPI, no touch**: J701 uses the same signal order and
  reversed vendor numbering shown above. See the retained
  [manufacturer specification](../../reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf),
  pages 5–6. Its reviewed clock limit is 10MHz; physical operation remains open.
- LCDWIKI **MSP2807/MSP2806 ILI9341**: the
  [manufacturer pin table](https://www.lcdwiki.com/2.8inch_SPI_Module_ILI9341_SKU:MSP2807)
  matches J702 pins 1–8: VCC, GND, CS, RESET, DC, MOSI, SCK, LED.
  Pins 9–14 are intentionally unconnected: no readback or touch. Check the exact
  purchased board's regulator and voltage requirements. JP701 selects 3.3V by
  default; open it before selecting 5V with JP702. Never close both.
- Full-size Luckfox [Pico pin diagram](reference/pinout.jpg) and
  [Pico Plus pin diagram](reference/plus-pinout.jpg), cross-checked with their
  retained [Pico schematic](reference/Luckfox-Pico.pdf) and
  [Plus schematic](reference/Luckfox-Pico-Plus.pdf). All connected functions agree
  across the two modules; their differing unused GPIOs remain unconnected.

Fit only one LCD and the corresponding socket arrangement. Before first power,
check continuity from the actual module's marked VCC/GND and all six signal pins
to the carrier. Powered display, full-size host firmware and mounting remain
first-article work.

# Prototype bring-up record — UNTESTED template

Copy per physical board. A blank field is not a pass. Keep secrets/PINs/private keys out of this record.

| Build identifier | Record |
|---|---|
| Board/source revision and variant (eight-pin pill / standard FPC) | |
| PCBA supplier/order/date | |
| Module type/storage | |
| LCD/camera exact model and physical LCD revision | |
| Firmware version/image hash | |
| U601 marking / MPN | |
| Reader device/configuration | |
| Test card/app version (no secrets) | |
| Instruments / date / tester | |
| Supply setpoint/current limit | |

| Test | Measurement / evidence | Pass, fail or pending |
|---|---|---|
| Inspection / DNP / jumpers / insulation | | Pending |
| Unpowered supply short check | | Pending |
| Carrier-only +5V / settled input current | | Pending |
| Bridge reset waveform / VDD33 | | Pending |
| Host boot +5V/+3.3V minima and current | | Pending |
| LCD interface orientation / SPI / pixel test (320×240 corners) | | Pending |
| Standard FPC only: R405, R406, R407 currents (N/A for pill) | | Pending |
| Pill only: J1/carrier numbering and 3.3 V continuity | | Pending |
| Pill only: actual C701/C702 MPN, capacitance-at-bias evidence, paste/stencil/process | | Pending |
| Pill only: LCD_3V3 startup/load min AND max versus LCD 3.1–3.6 V operating range | | Pending |
| Pill only: whole-module LCD current, U701 case temperature, local ambient, enclosure state and time to thermal stability | | Pending |
| Pill only: header heights/insertion, 12 mm supports, screws and clearance | | Pending |
| All eight key states / debounce / case fit | | Pending |
| Camera + harmless QR | | Pending |
| PC/SC reader / connected slot | | Pending |
| Presence / removal / activation / ATR | | Pending |
| Card Info / test applet operation | | Pending |
| Cold boot repetition (count/failures) | | Pending |
| Short interruption / brownout recovery | | Pending |
| Combined-load current / rail minima | | Pending |

## Pill display and button measurements

Use the [eight-pin electrical review](DISPLAY-BUTTON-REVIEW.md) for signal names
and acceptance order. Record actual measurements; a software transfer or input
allocation alone does not establish panel output or switch operation.

| Display / startup check | Evidence | Result |
|---|---|---|
| Installed HOTHMI profile and 320×240 setting; fresh or persisted settings identified | | Pending |
| Kernel bank labels, `/dev/gpiochip-bankN` targets and active GPIO consumers | | Pending |
| SPI mode 0, actual clock frequency, CS/DC/reset timing capture | | Pending |
| RGBW/byte order, inversion, orientation and all four visible corners | | Pending |
| Cold/warm starts: attempts, failures and supply conditions | | Pending |

Measure each input relative to GND. Key1/Key2 use the **1.8 V** domain; never
add 3.3 V pull-ups. Other keys use 3.3 V. Each released input must be stable high
and pressed low, with only the intended UI event. Record bounce/holds/repeats and
case actuation separately from the DC readings.

| Key / switch | GPIO bank / line | Released V | Pressed V | UI event / holds / case result |
|---|---|---|---|---|
| Left / SW501 | 1 / 24 | | | Pending |
| Up / SW502 | 1 / 25 | | | Pending |
| Press / SW503 | 1 / 22 | | | Pending |
| Down / SW504 | 1 / 23 | | | Pending |
| Right / SW505 | 0 / 4 | | | Pending |
| Key1 / SW506, 1.8 V | 4 / 16 | | | Pending |
| Key2 / SW507, 1.8 V | 4 / 17 | | | Pending |
| Key3 / SW508 | 1 / 21 | | | Pending |

Unresolved findings / disposition:

Production approval: **not granted by this template**.

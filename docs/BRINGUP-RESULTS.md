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
| Pill only: LCD_3V3 voltage/minimum at startup and fills | | Pending |
| Pill only: LCD current, U701 case temperature, ambient and run duration | | Pending |
| Pill only: header heights/insertion, 12 mm supports, screws and clearance | | Pending |
| All eight key states / debounce / case fit | | Pending |
| Camera + harmless QR | | Pending |
| PC/SC reader / connected slot | | Pending |
| Presence / removal / activation / ATR | | Pending |
| Card Info / test applet operation | | Pending |
| Cold boot repetition (count/failures) | | Pending |
| Short interruption / brownout recovery | | Pending |
| Combined-load current / rail minima | | Pending |

Unresolved findings / disposition:

Production approval: **not granted by this template**.

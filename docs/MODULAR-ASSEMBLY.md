# Build the modular carrier

The intended work split is **JLCPCB solders the 32 small parts; you solder ordinary headers, plug modules together and install screws**. Use the [modular design guide](LCD-MODULE-VARIANT.md) and its matched files, rather than the standard FPC carrier instructions.

## Customer shopping list

| Item | Qty | Required specification |
|---|---:|---|
| Waveshare Pico-ResTouch-LCD-2.8 | 1 | Assembled 2.8-inch ST7789 display with its two receptacle rows; no Pico CPU |
| Luckfox Pico Mini | 1 | Compatible RV1103/microSD boot variant; SC3336 camera support |
| Display male header strips | 2 | 1×20, 2.54 mm pitch, 0.64 mm square pins, nominal 2.54 mm insulator and 6 mm exposed posts |
| Carrier Luckfox socket strips | 2 | 1×11, 2.54 mm pitch, nominal 8.5 mm housing height, mates with 0.64 mm square pins |
| Luckfox male strips | 2 if needed | 1×11, 2.54 mm pitch; omit if the purchased module already has correctly oriented headers |
| Display support extensions | 4 | M2.5 male-female, 8 mm body; short male stud suitable for the display's 4 mm bosses |
| Carrier support screws | 4 | M2.5×4 mm, with suitable washers if needed; check engagement and case clearance |
| Camera, microSD, regulated 5 V supply and enclosure | 1 set | Match the Luckfox and this larger PCB; the old enclosure does not fit |

Buy headers to the specified heights, not only pitch. The module's packaged spacers are not specified as 8 mm; measure them before reusing them. Generic longer breakaway **male** strips can be trimmed to the exact pin counts. Precut sockets avoid cutting through a female contact. The [CSV](../variants/lcd-module-2.8/assembly-extras.csv) is a separate customer list, not a JLC SMT BOM.

## 1. Request the PCBA quote

Unzip the [modular order kit](https://www.shieldsigner.dev/files/shieldsigner-modular-order.zip). Upload its inner Gerber ZIP, then its matching BOM and CPL. Select two-sided SMT assembly, two copper layers and 1.6 mm thickness. The [kit instructions](../variants/lcd-module-2.8/manufacturing/README.md) explain the datum, population and quote checks.

Start with five assembled prototypes. Confirm the assembler's preview shows all eight switches on top and the card socket/USB/SEC1210 on the bottom. Confirm the socket entrance, USB port direction and SEC1210 pin 1 visually before approving assembly. No retail LCD, Luckfox, customer headers, supports or DNP parts should appear in the SMT BOM/CPL. Request review of the card socket's tray handling and double-sided process; its public SMT catalog listing is not a completed quote.

Do not solder the small parts yourself if using the assembled-carrier route. The supplied files identify them by manufacturer part number and LCSC code. Any substitution needs an electrical/footprint review, especially the SEC1210 firmware suffix and card socket.

## 2. Inspect and install the headers

Keep all power disconnected. Inspect the PCBA for solder bridges, polarity and the stated DNP population. Fit the two 1×20 **male** strips on the carrier's display side at J701. Use the unpowered LCD as an alignment jig while lightly tacking one pin on each strip; verify both rows are straight before finishing the joints. Do not force the module or solder with power connected.

Fit the two 1×11 **female** socket strips on the carrier's Luckfox mounting side. Match the KiCad 3D assembly: the Luckfox microSD/components face outward and the USB end follows the board marking. If the module lacks headers, install two male strips so the long posts enter the carrier sockets. Tack a corner, check perpendicular alignment and then finish the remaining joints.

The carrier has **62 customer header joints** (40 LCD + 22 Luckfox sockets). An unheadered Luckfox adds 22 joints, for **84 total**, all at 2.54 mm pitch. A module with suitable preinstalled headers saves those 22 joints. The customer does not solder the SEC1210 QFN, USB contacts, card socket or an LCD FPC connector.

## 3. Support the display mechanically

Use H701–H704's four 2.7 mm clearance holes. Their centers come from the manufacturer's STEP, not an estimated screenshot. The intended support is 8 mm extensions between the carrier and the module's 4 mm factory bosses, placing the LCD PCB back approximately 12 mm above the carrier. Verify thread engagement without bottoming out or pulling on the PCB.

At these nominal dimensions, the display receptacle openings sit about 3 mm above the carrier and the specified male posts enter them by about 5.54 mm. The male insulators are 2.54 mm tall, leaving a small gap rather than loading the connector housings. The supplied STEP depicts a 0.02 mm wider row spacing than the nominal Pico interface; confirm smooth mating on the purchased module before tightening supports.

Support the display with its screws, not only friction in the electrical headers. Keep metal housings and screw ends away from circuit pads. Check the camera cable path and access to both USB/microSD locations before designing an enclosure. The source card-socket model is an outer envelope, so use the real socket drawing/card for its insertion opening.

## 4. Check connections before power

With the modules removed, check resistance between +5 V and ground and between +3.3 V and ground. Investigate an apparent short before attaching the LCD. Verify J701 pin 39 goes to +5 V and its ground pins go to ground. Verify its SPI/reset/DC pins against the design guide's table; the 40-pin numbering is Pico-style, not Luckfox numbering.

Keep JP203/JP205 closed and JP204/JP206 open. The assembled display has its own backlight circuit; do not populate the old J401/C401/Q401/R401–R410 circuitry. Leave the module's SD slot empty—it is not the Luckfox boot slot.

## 5. Bring up in stages

1. Insert only the Luckfox and boot media. Use one current-limited regulated 5 V source. Verify +5 V and Luckfox +3.3 V at J701; power down before adding the display.
2. Connect and support the display. Measure whole-device current and both rails during boot. The manufacturer quotes 140 mA at 5 V for the display module; total signer consumption also includes the CPU, camera and smartcard.
3. Begin display tests at a conservative SPI clock, such as 1 MHz. Test red/green/blue/white/black fills and labeled corners. Confirm inversion, RGB/BGR order, rotation, offsets and full Plus-sized UI before increasing clock speed. The existing ST7789 family driver is a starting point, not a tested module firmware image.
4. Test all eight buttons and the SC3336 camera, including QR focus/rotation. The camera retains its own ribbon connection.
5. Use the SEC1210/PV-UR2 reader configuration, test the presence switch, read a compatible card's ATR and exercise the intended SeedKeeper/Satochip workflow. Use test material until physical bring-up is complete. A small SIM-size smartcard needs an appropriate full-size adapter for this socket.

Record rail minima, current, actual header/spacer dimensions, firmware revision, display tests and card results in the [bring-up record](BRINGUP-RESULTS.md). Native design checks and a successful OS compilation do not replace these measurements.

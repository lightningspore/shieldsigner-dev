# Assemble the eight-pin pill carrier

**JLCPCB solders the 35 SMT parts. You solder ordinary headers, plug in the modules and install screws.** Use the [0.0.6-dev pill design](LCD-MODULE-VARIANT.md) and its matched files. The old Pico-format LCD carrier and standard FPC kit are different boards.

For an optional DIY build, use the separate [self-assembly guide](SELF-ASSEMBLY.md) and DigiKey purchase CSV. The original JLC kit below remains the assembled-board ordering path.

## First article before repeat builds

The immediate target is **one working first article**, with perhaps three finished units later. Do not buy or assemble a 20-unit batch to validate this revision. DigiKey parts plus bare PCBs are an acceptable route; the standard JLC assembly-stock shortage does not prevent self-assembly.

1. Before ordering, close the drawing-level review of footprints, power, module/header orientation and paste/reflow access. Price one populated board, sensible component spares, the minimum bare-PCB order, stencil, shipping and any missing assembly/test tools. The existing $19.16 fitted-parts estimate is dated and excludes these costs.
2. Confirm a practical assembly method for the two-sided board and SEC1210 exposed-pad QFN. Choose a controlled reflow/rework process or a local assembler; inspect the hidden-pad process rather than assuming an iron can solder it. Identify any second-side retention or heat-sensitive socket constraints before applying paste.
3. Inspect a bare PCB and dry-fit the actual USB connector, socket, headers, Luckfox, LCD and supports. Confirm the signal-by-signal reversed LCD numbering without power. Stop for footprint, interference or orientation discrepancies.
4. Populate one carrier only. Inspect and test it without either module; follow the staged power checks below using a current-limited supply. Investigate shorts, unexpected current or heat before connecting costly modules. Log actual measurements rather than checking boxes from simulation.
5. Fit modules one at a time, with power removed between changes. Demonstrate display corner/color patterns, all buttons, camera QR scanning, reader/card insertion and a harmless test transaction. Capture supply minima, LCD regulator temperature at recorded ambient/load, repeated starts and interruption recovery in the [bring-up record](BRINGUP-RESULTS.md).
6. Release the second and third builds only after the first-article record has no unresolved electrical, mechanical, thermal or firmware failures. Fix the design and regenerate matching fabrication/BOM files if necessary. Buying a few spare components is reasonable; repeating a known failing assembly is not.

A passing first article supports the next small build; it does not establish mass-production yield. Acceptance limits must come from the exact module/component specifications and intended operating conditions. Record those limits alongside measurements before declaring a pass.

## Customer shopping list

| Item | Qty | Specification |
|---|---:|---|
| HOTHMI HTM-TFT028A16-SPI | 1 | No-touch 2.8-inch ST7789V module; confirm J1 1×8, 2.54 mm row and 88×53.3 mm drawing |
| Luckfox Pico Mini | 1 | Compatible RV1103/microSD boot variant and matching camera |
| LCD carrier socket | 1 | 1×8 female, 2.54 mm pitch, 8.5 mm housing, accepts 0.64 mm square posts |
| LCD male strip | 1 if needed | 1×8, 2.54 mm pitch, 0.64 mm square, 2.54 mm insulator, 6 mm exposed mating posts |
| Luckfox carrier sockets | 2 | 1×11 female, 2.54 mm pitch, 8.5 mm housing |
| Luckfox male strips | 2 if needed | 1×11; long posts face carrier sockets; omit if correctly preinstalled |
| Display spacers | 4 | M2.5 female-female, 12 mm body, nominal 5 mm outside diameter |
| Mounting screws | 8 | M2.5×4; check engagement through each PCB and any washers |
| Washers | As needed | M2.5, no more than 5 mm outside diameter in the reserved hardware area |
| Camera, microSD, 5 V supply, enclosure | 1 set | Match the selected Luckfox and 160×70 mm carrier; old enclosure does not fit |

The LCD's separate 2 mm J2 connector is not used. Fit the 2.54 mm J1 row if the seller supplies it bare. Confirm connector type, pitch and pin orientation on the purchased module; the photograph/drawing is not a guarantee that a header is fitted. Buy headers by **height and post length**, not pitch alone. Precut female strips avoid damaging contacts when trimming.

[Customer-parts CSV](../variants/lcd-module-2.8/assembly-extras.csv) is separate from the JLC SMT BOM. A compatible full-size smartcard is also needed for reader tests; [choose a card/app](SMARTCARDS.md) for your workflow.

For the [printed enclosure](ENCLOSURE.md), use its screw list in place of the eight short mounting screws above. It keeps all four LCD spacers, uses three case-to-spacer screws and leaves one base post absent for Luckfox connector access.

## 1. Get a matched PCBA quote

Unzip the [pill order kit](https://www.shieldsigner.dev/files/shieldsigner-modular-order.zip). Upload the inner **shieldsigner-modular-gerbers.zip**, then **bom-jlcpcb.csv** and **cpl-jlcpcb.csv**. Request two copper layers, 1.6 mm thickness and two-sided SMT assembly. Expect **35 placements / 17 catalog lines**: eight switches plus U701/C701/C702 on top, and 24 parts underneath.

For the current first-article plan, populate and qualify **one board first**; leave the remaining bare boards unassembled. A fabricator minimum quantity is not a requirement to assemble every board. If JLC assembly is used, confirm its minimum assembled quantity and pricing before choosing that route. Check JLC's preview for SEC1210 pin 1, card-socket entrance, USB orientation and the eight switches. Ask about socket handling and its double-sided process. The LCD, Luckfox, customer headers, supports and copper jumpers do not belong in the SMT BOM/CPL. There are no obsolete FPC/backlight parts to populate and no DNP courtyard exceptions to approve.

Confirm stock, rotation, DFM, loading/attrition fees and final quote before payment. No paid order or physical qualification is implied by the software checks. Do not substitute the SEC1210 firmware suffix or an arbitrary eight-pin LCD.

**JLC placement check:** the initial catalog preview needed J301 rotated 180° and moved inward, plus a sideways offset for J601. These adjustments are saved in the current cart. Fresh CPL uploads require the same pad/locating-hole alignment review; the generic CPL retains KiCad's origins. See the [saved corrected preview and repeat-upload instructions](../variants/lcd-module-2.8/manufacturing/placement-review/README.md). Keep **Confirm Parts Placement: Yes** for assembler review.

## 2. Inspect the assembled carrier

Keep all power disconnected. Inspect the QFN, USB and card contacts for bridges, capacitor damage and correct orientation. Check that U701 is the selected 3.3 V regulator. Verify resistance between +5V/GND, LCD_3V3/GND and Luckfox +3.3V/GND; investigate an apparent short.

The dedicated LCD_3V3 output must not be shorted to the Luckfox 3.3 V output. The LCD header never receives 5 V. Confirm header pad 8 is LCD_3V3 and pad 7 is GND against the [signal table](LCD-MODULE-VARIANT.md#exact-connector-wiring).

## 3. Solder the ordinary headers

Install the **1×8 female socket on the carrier front at J701**. Install two **1×11 female sockets on the Luckfox mounting side**. Tack one end, check perpendicular alignment and finish the joints.

If the LCD lacks its J1 header, fit a 1×8 male strip with the long mating posts pointing down toward the carrier. The carrier numbers run opposite the module's: **carrier 1/BL → module 8/BL_E; carrier 8/3V3 → module 1/VCC**. Match every signal before using the unpowered module as an alignment jig. Never connect by equal pin numbers.

If needed, fit the Luckfox's two male strips so the long posts enter its sockets. The microSD/components face outward and the module USB end follows the KiCad assembly. The carrier has **30 customer solder joints**: 8 LCD socket + 22 Luckfox sockets. Bare LCD/Luckfox modules add 8 + 22, for **60 maximum**, all at 2.54 mm pitch. No customer reflow or fine-pitch connector soldering is required.

## 4. Mount and fit-check

Use four **12 mm M2.5 female-female spacers** at H701–H704. Fasten from below the carrier and above the display using eight short screws. Check engagement, washer diameter and screw clearance before tightening. Do not use the earlier Pico module's factory bosses or 8 mm extension instructions.

The CAD stack gives about 5.04 mm electrical pin insertion and 6.8 mm clearance beneath the LCD's rear connector. Confirm smooth mating with no forced bending. Support the display mechanically; do not use the header as the only support. Check Luckfox removal, camera cable routing, both microSD/USB access paths and smartcard insertion.

The LCD front is approximately 17.7 mm above the carrier. Switch actuators are much lower, so the case needs button plungers or suitable wells. Enclosure and physical stack tolerances are not qualified by the STEP envelopes.

## 5. Apply power in stages

1. Leave both modules out. Use one current-limited regulated 5 V supply at the carrier's power input. Verify U701 VIN/EN and LCD_3V3 output. Increase the limit only after checking unexpected current or heating.
2. Power down, fit the Luckfox and boot media, then power up. Verify the independent Luckfox 3.3 V rail. Avoid simultaneously powering carrier and module USB ports.
3. Power down, connect and support the LCD, then measure supply rails and whole-device current during boot and solid-color fills. Record U701 temperature and rail minima. The module drawing's 120 mA backlight figure is not a whole-device power budget.
4. Keep JP201/JP203/JP205 closed, JP202/JP204/JP206 open. The default backlight is always on. Test SPI at a conservative clock, such as 1 MHz, then increase only after stable operation. Check reset, inversion, RGB/BGR order, rotation, offsets and all four labeled corners at landscape 320×240. An ST7789 family driver is a starting point, not a tested module firmware image.
5. Test all eight buttons and camera scanning. Then load the UR2 UART/PCSC reader configuration and exercise the [smartcard bring-up steps](BRINGUP.md). Start with disposable test data, not a real wallet seed.

Record module revision, header/spacer measurements, firmware version, measured current/temperature, display tests and card transactions in the [bring-up record](BRINGUP-RESULTS.md). A clean PCB check and a successful OS build do not establish these physical results.

Revision **0.0.6-dev** uses shared-supplier C&K switches and GCT USB4125-GF-A-0190 with revised native lands. Use matched revision files and the measured-height button setup in [self-assembly](SELF-ASSEMBLY.md). Physical first-article fit and powered bring-up remain pending.

## Alternative 5 V power header (0.0.6-dev)

J302 is an optional ordinary **1×2, 2.54 mm through-hole header** beside USB-C. Solder it yourself if desired; it is excluded from the factory SMT BOM and CPL. **Pin 1 (square pad) is +5 V; pin 2 is GND**, also printed on the top silkscreen. A standard male strip or two soldered wires fits the same lands. Fitting the header adds two customer solder joints.

Use a **regulated 5 V supply**. This is not a raw battery input. J302 and USB-C feed the same +5 V rail, including the existing TVS and input capacitors. There is no reverse-polarity or source-selection circuit: **disconnect USB power before powering J302**, and vice versa. Also disconnect the Luckfox module USB supply before applying external power. Confirm polarity before connecting. Enclosed use needs a deliberate wire exit; no case opening for J302 is provided by this PCB change.

J301 now uses **GCT USB4125-GF-A-0190**, JLC **C5246813** / DigiKey **2073-USB4125-GF-A-0190CT-ND**. The manufacturer drawing specifies the same lands and 1.90 mm shell stakes. Inspect actual protrusion/wetting on the 1.6 mm PCB during first article. The old no-suffix 1 mm-stake part was omitted by the 0.0.5-dev quote; that quote is superseded for ordering this revision.

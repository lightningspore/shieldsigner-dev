# ShieldSigner eight-pin pill — 0.0.12-dev

Open `kicad/SeedSigner-Plus-smartcard-pico.kicad_pro`. The inherited basename preserves hierarchical annotation paths; this is an independent native project. See [design and exact wiring](../../docs/LCD-MODULE-VARIANT.md), [customer assembly](../../docs/MODULAR-ASSEMBLY.md) and [quote instructions](manufacturing/README.md).

The **160×70 mm capsule** centers a 2.8-inch HOTHMI HTM-TFT028A16-SPI between the controls. A single eight-pin 2.54 mm socket follows the user's existing Luckfox carrier numbering. There is no Pico-format LCD connector or projecting rectangular bay. A dedicated AP2112K-3.3 supplies LCD_3V3 independently of the Luckfox's 3.3 V output.

There are **72 footprints** and **44 factory SMT placements across 18 catalog lines**. Nine Keystone 5015 / C2906768 service loops replace the optional J302 power header and add clip access to host/LCD 3.3 V, UART and local grounds. Four additional 2.7 mm M2.5 bracket holes supplement the four original LCD support holes. The six copper jumpers and 12 small probe pads are retained. Modules, their headers and screws remain customer assembly; the Keystone points are factory assembled.

The released two-layer revision adds the official The Space logo and `denver.space` on the rear
silkscreen. The [artwork audit](branding-audit.json) proves that all non-silk
PCB data is unchanged from 0.0.7. Always-on backlight remains the factory
default; the optional PWM candidate is separate. See the
[order-readiness review](../../docs/PCB-ORDER-READINESS.md) for current stock
and supplier gates. **Do not use the bench firmware unchanged:** its LCD
outputs conflict with carrier buttons. Use the
[carrier-profile guide](../../docs/PCB-SOFTWARE-COMPATIBILITY.md).

Run `mise run variant:lcd:fab` for native/model/footprint checks and matched Gerbers/BOM/CPL. `variant:lcd:review` renders both sides and exports assembly STEP/GLB; `variant:lcd:package` bundles the portable project and pins release hashes. Manufacturing uses the shared auxiliary origin (50,130) mm. Standard carrier files do not apply.

Twenty-two retained local STEP models have source/hash records. LCD, socket, switch, USB and threadless supports are dimensional envelopes. `mechanical.json` records the stack, mounting centers and drawing discrepancies; `header-map.json` records both numbering conventions. Run `git lfs pull` in a fresh checkout.

This is a prototype quote/review design, not a physically qualified signer. Assembler preview/DFM, purchased-module fit, rail/thermal measurements, firmware/display behavior, smartcard transactions and enclosure fit remain to be tested.

## Four-layer working board

The working native PCB now has four copper layers: F.Cu signal, In1.Cu GND,
In2.Cu GND, B.Cu signal. Both inner planes are filled and connected through
existing GND through-vias and plated pads. The first conversion preserved outer routing and placement; see the historical `four-layer-audit.json`. The later service revision is recorded in `serviceability-audit.json`. Total thickness stays
1.6 mm: four 0.035 mm copper layers, 0.2/1.04/0.2 mm FR4 dielectrics and two
0.01 mm masks. This is a nominal stackup requiring fabricator confirmation,
without an impedance-control claim. Outer support keepouts remain unchanged.

The 0.0.12-dev silkscreen identifies this service revision; released two-layer quote
ZIPs and old artwork-only audits do **not** describe this working four-layer
revision. Regenerate fabrication files with `mise run variant:lcd:fab`, select
four layers in the supplier quote and obtain a new supplier review. The separate
PWM candidate and source-authored tscircuit layout have not been converted.

## Readable native schematic

All six native sheets were reviewed and relaid out: system flow overview, host
module and factory strap table, USB-C input/protection, physical control map,
SEC1210/card interface and dedicated LCD regulator/eight-pin header. U201 and
TP201 are explicitly labelled schematic-only legacy references. Component
identities, values, footprints and complete pin-to-net partitions are unchanged;
`schematic-readability-audit.json` records the native netlist comparison.

Run `mise run variant:lcd:schematic:review` to verify the electrical fingerprint
and export the six-page PDF and individual SVGs under
`dist/lcd-module-2.8/schematic-review/`. Native schematic changes are editable in
KiCad; these are not images pasted over the design. The one-time conversion
and layout tasks record changes already applied and must not be replayed.

## Factory service points and independent bracket mounting

`serviceability.json` is the machine-readable point/mount map. H705-H708 form a
109 x 47.8 mm rectangle, with 2.7 mm NPTH holes and 6 mm copper keepouts on all
four layers. Use M2.5 hardware with a head/washer OD no larger than 5 mm. These
are optional anchors for custom printed brackets; the existing enclosure still
uses the original LCD spacer holes and needs no new posts. Do not assume the
new anchors make an arbitrary bracket fit: model the actual head, standoff,
module and insertion paths.

TP902 (GND), TP901 (+5V) and TP909 (GND) form the front bench-power row at 15 mm pitch. The six
rear loops provide LCD_3V3, host 3V3, UART_TX, UART_RX and two local grounds.
All are Keystone 5015 SMT parts in the factory BOM/CPL with paste apertures.
No test-point soldering is assigned to the customer. The 1.52 mm STEP model is
a nominal occupied envelope, not a detailed supplier model.

Use regulated, current-limited 5 V for bench injection. Disconnect USB supplies
first; the board has no source isolation or reverse-polarity protection. The
loops are test contacts, not a strain-relieved permanent power connector.

The 2026-11-09 catalog refresh shows zero standard-assembly stock for the
selected switches, SEC1210 and smartcard socket. The generated kit is suitable
for supplier review, but requires confirmed sourcing/attrition and new assembly
placement/DFM approval before checkout. Software checks do not qualify hardware.

For bracket CAD in the existing enclosure frame (X = PCB X - 128; Y = 89.579 -
PCB Y), the new hole centers are (-50, +23.9), (+59, +23.9), (-50, -23.9),
(+59, -23.9) mm. They are clearance holes: engage screws in a nut, standoff or
printed bracket insert, not threads cut into the FR4. Choose screw lengths from
the actual bracket stack and reserve the module/connector access paths.

## Power clips — 0.0.12-dev

The front service row is **TP902 GND — TP901 +5V — TP909 GND**,
with **15 mm centre spacing** (previously 7 mm between the original pair).
All three are factory-assembled Keystone 5015 loops. The additional ground
gives a second instrument/clip attachment, with no new purchased part type.
Land-edge separation is 11.6 mm; actual clip jaw/insulation fit and strain
still need checking on a first article. Use one regulated, current-limited
5 V source and disconnect other power sources before bench injection.

This changes only service-point placement, their connection spurs and one
additional GND point. The retained circuitry, header pins and GPIO mappings
are unchanged; see [the layout audit](power-clip-layout-audit.json).

### Rear component placement — 0.0.12

U701 and its 10 µF input/output capacitors C701/C702 are now on the back, keeping the regulator and reader electronics accessible from the same side. The switches, display header and front power clip row retain their positions and sides. The reader reset resistor is horizontal above the aligned reset/input capacitors; the reader filter passives and jumper rows have been regularized. Rear reference labels use consistent 0.8 mm lettering with 0.15 mm strokes, with a vertical R607 reference where space is constrained.

Factory assembly is **11 front / 33 back**, still 44 placements and 18 SKUs. The [exact edit record](../../docs/pcb-rear-placement-edits.json) and [rear audit](rear-layout-audit.json) cover the placement and local routing changes; original pad nets and board/project rules are preserved. Supplier placement/DFM review must use the regenerated CPL. Mechanical models and native electrical/clearance checks do not establish physical rework access or thermal performance.

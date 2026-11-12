# 0.0.13: 45-degree routing and optional battery-module input

The main four-layer carrier now uses only horizontal, vertical and 45-degree straight trace segments. The angle audit allows two nanometres of serialization rounding, not a routing-angle exception. Fifteen pre-existing zero-length segments were removed. Native ERC, refilled DRC and schematic parity remain required in addition to this geometry check.

All 72 pre-existing footprints and their pad nets are retained. Two unconnected GND stitching vias beside TP909 were removed, and one GND via was moved out of C601’s paste land. The SEC1210/PV-UR2 reader and Amphenol 7312P0225A13LF socket are unchanged. The revision has **73 footprints**, with the same **44 factory SMT placements / 18 SKUs** and nine Keystone loops. The historical 0.0.12 service/rear-layout audits describe that baseline; [the current audit](../hardware/angle-header-audit.json) and [explicit route record](pcb-angle-header-edits.json) verify the changes from it.

## J302 under the LCD

J302 is a customer-fitted, front-side **1×2, 2.54 mm right-angle male header** at board coordinates **177.3, 107.8 mm**. Pin 1 is **+5V**, pin 2 is **GND**. Its pins point **left, inward toward the display center**. A mating daughterboard sits to its left and slides right onto the pins. It coexists with the three front power clip points and is excluded from JLCPCB SMT BOM/CPL. Fitting it adds two through-hole solder joints.

The retained KiCad horizontal-header STEP extends approximately 10.04 mm left of pin 1 and 2.54 mm above the carrier's front surface. Its footprint/model fits within the LCD's 88×53.3 mm projected outline. The existing drawing-based stack reserves 6.8 mm below the LCD's deepest rear feature, leaving a nominal 4.26 mm above this header. Actual purchased header, mating daughterboard connector and LCD tolerances still need a physical fit check.

This provides a connection for the **regulated 5 V output of a future battery/charger/boost module**. It is not a bare-cell connector. The carrier has no battery charger, boost converter, source switching or reverse-polarity protection. Disconnect USB power before supplying J302. A battery/module has not been selected, so no cell dimensions, mounting arrangement or usable battery capacity are qualified. The planned battery location is under the LCD; the connector sits near its right edge, facing inward for a future slide-in daughterboard.

## Recheck and export

Run `mise run hardware:check` (including the angle/header audit), `mise run build`, `mise run check` and `mise run tscircuit:pill:reference:check`. `mise run hardware:angles` reruns the focused geometry and retained-circuit checks. Then regenerate the matched fabrication/review kit with `hardware:fab`, `hardware:review` and `hardware:package`.

Earlier JLCPCB quote uploads do not contain this revision. Upload the new matched kit and review placements/DFM before the final order. Existing software checks do not qualify a battery assembly or powered first article.

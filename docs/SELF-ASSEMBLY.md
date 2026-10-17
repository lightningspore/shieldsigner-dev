# Optional self-assembly with DigiKey parts

**JLCPCB remains the primary route:** order the existing assembled pill carrier, then fit the headers and modules using the [assembly guide](MODULAR-ASSEMBLY.md). The native board and matched JLC BOM/CPL are unchanged.

For self-assembly of the same 0.0.4-dev board, use the separate [DigiKey sourcing table](../variants/lcd-module-2.8/self-assembly/BOM-DIGIKEY.md) and [purchase CSV](../variants/lcd-module-2.8/self-assembly/bom-digikey.csv). The CSV gives exact cut-tape/tray order codes, reference designators, electrical specifications, original JLC identities, and installed quantities for one or five boards. It is a shopping list, not a JLC upload file.

## What is covered

| Population | Self-assembly status |
|---|---|
| 11 capacitors, 10 resistors, indicator LED and TVS | All 23 pieces / 12 lines have selected DigiKey parts using the existing footprints |
| SEC1210/PV-UR2, Amphenol card socket and AP2112K regulator | Exact original MPNs listed at DigiKey; three more pieces / three lines |
| Eight XKB switches and SHOUHAN USB-C connector | Original parts required from another source; no mechanical substitution approved |
| LCD, camera and Luckfox | Outside this supplier list |
| Customer headers, fasteners, card, microSD and supply | Follow the existing shopping/assembly and enclosure specifications |

**26 of 35 SMT pieces are listed at DigiKey.** The [remaining-parts CSV](../variants/lcd-module-2.8/self-assembly/remaining-parts.csv) explicitly lists the other nine. A DigiKey-only full-board order is not ready yet.

## Commodity substitutions

- Resistors retain 0805 dimensions, resistance, ±1% tolerance and 125 mW rating. Bourns supplies the 5.1 kΩ USB-C pull-downs because the comparable Yageo cut-tape part was out of stock.
- Capacitors retain 0805 dimensions, capacitance, voltage rating, tolerance and dielectric. The 33 pF and 100 nF parts retain their exact original MPNs; the 10 µF and 1 µF selections use stocked equivalents.
- The Kingbright green indicator uses the existing 0805 lands and 560 Ω resistor. Match its cathode to native K/pad 1. Brightness differs by device; the illustrative current is about 4.2 mA at 5 V and typical forward voltage.
- Littelfuse SMF5.0CA retains the bidirectional 5 V stand-off, 200 W pulse class and SOD-123F package. It is transient suppression, not an overvoltage disconnect.

Each selected part links to its DigiKey page in the sourcing table. Stock was checked on **2026-10-17** and is not reserved. Prototype effective capacitance, LED brightness and powered behavior remain bench measurements, as with the JLC population.

## Assembly process

Self-assembly of the whole carrier includes a **24-pin exposed-pad QFN**, SMT card socket and two-sided population. A controlled paste/reflow process and inspection are appropriate; this requires more equipment and technique than the header soldering needed after JLC assembly. Use native paste, silk and placement information with the original reference designators. Replacements keep their existing footprints and net assignments; confirm LED polarity and IC pin 1 before heating.

After assembly, follow the [staged rail and module checks](MODULAR-ASSEMBLY.md), then [reader bring-up](BRINGUP.md). Keep all eight original switch actuator geometries and the original USB receptacle until a separately reviewed revision says otherwise. C&K PTS636 and GCT USB4135 are investigation candidates, not alternatives authorized by this BOM.

Use the [enclosure hardware list](ENCLOSURE.md) when printing the case. M2.5 thread and spacer length alone do not establish clearance: a 5 mm-across-flats hex spacer has approximately 5.77 mm across corners and does not fit a 5 mm circular envelope.

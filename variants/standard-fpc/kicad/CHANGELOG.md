# Native KiCad variant changes

The baseline is upstream commit `efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f`; file hashes are recorded in provenance.json. The unchanged source PCB and schematics remain in ../reference/.

- Restored the full .kicad_pro and original hierarchical sheets instead of generic tscircuit symbols.
- Bundled missing custom symbols by extracting their exact embedded definitions into project-local symbol libraries. Standard symbols are also pinned locally, preventing missing global-library configuration from hiding schematic issues.
- Preserved original DNP flags, copper, closed jumper footprints, layer drawings and custom module/socket geometry.
- Kept baseline native ERC/DRC reports in ../dist/kicad/. They expose inherited issues; no errors are silently excluded or manufacturing rules relaxed.

See ../docs/HARDWARE.md and ../docs/COMPONENTS.md for rationale, original pad maps, assembly defaults and unresolved source discrepancies.

- Declared 38 intentionally unused LCD, module and reader pins with no-connect markers, based on baseline ERC pin coordinates.
- Corrected SEC1210 SC1_VCC, SC2_VCC and VDD33 symbol pin types to power outputs, following DS00001561D table 6-4.
- Annotated known external USB +5V/GND supply with PWR_FLAG symbols; these annotations add no hardware.
- Declared U201/TP201 as schematic-only (not on board or in BOM), preserving the alternative interface wiring without requesting absent PCB parts.
- Changed C603/C604 from 100 nF to 1 µF in both PCB and schematic; selected the same supplier ID as reference C602 (C28323), subject to effective-capacitance qualification. Their footprints and routing are unchanged.
- Snapshotted placed footprint definitions into project-local libraries. No copper geometry, board outline, component placements or manufacturing rules were relaxed.

Native verification: zero ERC errors (10 warnings); zero unconnected PCB items; zero schematic/PCB parity issues. DRC retains 13 errors and 29 warnings. See ../KICAD.md for the remaining review list. These are not automatically waived.

## Electrical / sourcing desk review — 2026-10-11

- Corrected J401 supplier code from C19273935 (bottom-contact Hong Cheng) to C2931360 (the specified top-contact Amphenol connector).
- Added exact manufacturer/MPN/datasheet/LCSC metadata for 45 catalog-backed footprints (43 fitted carrier parts and two DNP straps).
- Named U601 as the actual stocked SEC1210/PV-UR2; named Q401, D302, J301 and switches with their selected catalog identities. Copper/placement is unchanged; these metadata updates do not qualify the legacy footprints/stencils/models.
- Generated a matching 43-reference JLCPCB carrier BOM/CPL, excluding U202, DNP items and copper jumpers. Public availability is timestamped and unreserved.
- Resolved the earlier reset edge concern: DS00001561D's 100 ns figures are minima and it allows an external RC. No reset redesign applied.
- Added electrical review, BOM/assembly plan, staged bring-up/results and smartcard compatibility guides. Physical testing remains pending; layout DRC still has 13 errors.

## Board-edge clearance fix — 11 October 2026

- Trimmed the outer ends of U202 SMD pads 1/2 by 0.20 mm, preserving their inner edges and module placement; updated the local footprint library.
- Refilled and saved copper zones. Native board serialization also normalizes metadata and object ordering.
- Verified unchanged track/via geometry, board outline and all footprint positions. Exactly two pad position/size pairs changed.
- New native checks: zero ERC errors, zero unconnected items/parity issues; ten DRC errors (courtyard overlaps) and 29 warnings. Both edge violations and the adjacent starved thermal are resolved without relaxing rules. Physical module solderability remains unqualified.

## Layout and native tooling completion — 11 October 2026

- Moved C301 +0.15 mm in Y, R607 +0.03 mm in Y and optional J302 −0.50 mm in X; retained connectivity with local same-net joins.
- Preserved all eight button centers and copper lands; added dedicated XKB footprint identity and assembly envelope from the supplier drawing. Paste/reflow qualification remains pending.
- Retained the two overlapping alternate strap pairs as explicit DNP exceptions with a population guard, instead of changing their shared-land configuration.
- Moved colliding decorative graphics to fabrication layers and repositioned affected reference labels; opened mask/paste for LCD connector mounting plates.
- Removed stale instance `lib_name` overrides, synchronized power symbols and the schematic-only U201 footprint field, converted duplicate local I2C labels to global labels, and declared SEC1210 TEST as input per the datasheet.
- Final default-variant result: zero ERC errors/warnings, zero active DRC errors/warnings, two documented DNP exclusions, zero unconnected/parity issues.
- Added backed-up recipe editing, native DRC regression rejection, track-net checks and replay preconditions. Deliberate bad-placement rollback was verified byte-for-byte.

## 12 October 2026 — purchase metadata correction

C603/C604 already had the reviewed 1 µF circuit value, but their purchase properties/selection still described the old 100 nF component. Corrected both to C28323 / Samsung CL21B105KBFNNNE, matching C602. Geometry and electrical connections are unchanged. Regenerated BOM/CPL, native reports and Gerbers; added a guard against losing approved value/catalog corrections. Supersedes the earlier preview’s incorrect purchase metadata.

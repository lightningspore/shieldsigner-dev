# BOM and JLCPCB assembly plan

Target: **a fully populated carrier PCB from JLCPCB**, with the Luckfox module optional. The practical default is a carrier without U202. That does not mean leaving the fine-pitch reader or connectors for hand assembly: the carrier BOM includes all 43 required fitted pieces, including SEC1210, LCD connector, card socket, USB-C, switches, capacitors, resistors, MOSFET and indicator.

## LCD candidate qualification — 11 October 2026

**Reject HS280S010B / C2939938 as a drop-in replacement.** The supplier datasheet describes an assembled display board with a 14-pin, 2.54 mm interface, not the bare 40-pin FPC panel required by J401. Matching the 2.8-inch size and ST7789V controller does not establish compatibility.

| Requirement | Carrier/reference panel | HS280S010B datasheet | Result |
|---|---|---|---|
| External connection | 40-position 0.5 mm FPC, Amphenol top-contact connector | J2: 14-pin 2.54 mm connection | Incompatible |
| Envelope | Reference panel 47.8 × 66.95 × 2.13 mm | Assembled module 50 × 86 × 12.7 mm | Does not match current mechanical design |
| SPI pins | J401 CS9, clock10, DC11, MOSI13, reset15 | J2 CS3, clock7, DC5, SID6, reset4 | Requires an adapter and wiring redesign |
| Backlight | J401 anode33; cathodes34–36 via three 47 Ω branches and Q401 | J2 LED8; drawing labels this an I/O control, no exposed equivalent cathode branches | Existing backlight circuit is not qualified for this module |
| Supply | Carrier +3.3 V | Table gives 2.8 V typical/3.3 V maximum; drawing says operating 3.3 V | No margin established; clarify datasheet inconsistencies if reconsidering |
| Viewing behavior | Reference IPS/full viewing angle | Datasheet gives directional viewing; table says 6 o'clock while drawing says 12 o'clock | Not established equivalent; documentation discrepancy |

Datasheet evidence: page 4 physical/electrical data, page 5 mechanical drawing and connector pitch, page 7 DC characteristics, page 11 interface table. Some entries are inconsistent; do not use them to qualify supply or backlight limits without manufacturer clarification. The four-LED backlight characterization in this module does not establish requirements for the original bare panel.

An adapter could translate the SPI signals, but would still require a different mounting/enclosure arrangement and a separately qualified LED control/power interface. This is a separate design option, not an approved BOM substitution. C2939938 has not been added to the carrier BOM.

The original screen source remains the [upstream supplier link](https://www.alibaba.com/x/B1E3wJ), documented in the [display-hat README](https://github.com/3rdIteration/seedsigner-hardware/blob/main/display_hats/plus_hat/README.md). No exact JLC-stocked replacement has been qualified. Next obtain the exact bare-panel MPN/drawing, resolve the reference connector-numbering discrepancy, then match all 40 contacts, FPC pitch/contact face/cable geometry, SPI mode and backlight ratings. JLC installation of the cable and screen still needs an explicit assembly quote.

See the [saved PDF index](PDF-REFERENCES.md) and [HS280S010B datasheet](../reference/pdfs/C2939938.pdf). The supplier PDF and rendered drawing were inspected; this is a desk review, not a physical fit test.

## Current deliverables

- [Grouped JLCPCB sourcing table](BOM-TABLE.md): exact manufacturer/MPN, C-code, quantity and dated public availability for every selected carrier part.
- `manufacturing/jlcpcb/bom-carrier-jlcpcb.csv`: 21 JLCPCB component lines, 43 fitted pieces per carrier.
- `manufacturing/jlcpcb/cpl-carrier-jlcpcb.csv`: the same 43 references with native KiCad coordinates, side and rotation.
- `manufacturing/jlcpcb/population-audit.csv`: accounts for all 53 PCB footprints, including excluded parts.
- `docs/bom-selection.json` and `docs/jlc-catalog.json`: machine-readable selections and timestamped public catalog evidence.
- `manufacturing/jlcpcb/readiness.json`: explicitly marks this package **review_only**.

The source PCB, BOM and CPL agree on reference designators. The current catalog snapshots show a positive `canPresaleNumber` for all selected carrier parts. That field is preserved with its original name; it is not a reservation, guaranteed lead time or account-specific quotation. The separate `overseasStockCount` is not substituted for it.

## What is excluded, and why

| Item | Treatment |
|---|---|
| U202 Luckfox Pico Mini | Excluded from default carrier assembly; module optional |
| J302 | DNP alternate direct-power header |
| R404, R408 | DNP opposing LCD mode straps; must remain absent |
| JP201–JP206 | PCB solder-jumper footprints, not purchased components; preserve default copper bridge/open settings |
| U201, TP201 | Schematic-only alternative interface/testpoint; no PCB footprints |
| LCD panel, camera, microSD, cards and enclosure | System parts outside this carrier's PCBA BOM |

Leaving U202 off is within the requested scope. Attaching that module later is a separate assembly operation. A **no-solder system** instead needs JLCPCB to mount the module or a redesigned, populated socket arrangement. The default carrier file does not pretend to provide sockets that are absent from the PCB.

## Corrected identities

| Reference | Selected identity | Reason |
|---|---|---|
| J401 | Amphenol 62684-402100ALF / **C2931360** | Matches the named top-contact connector; rejects inherited C19273935, a bottom-contact Hong Cheng part |
| U601 | Microchip SEC1210/PV-UR2 / **C633309** | Actual stocked UART bridge identity; requires UR2 reader setting |
| Q401 | AOS AO3400A / **C20917** | Replaces a generic MOSFET value with its catalog identity |
| D302 | KENTO KT-0805G / **C2297** | Replaces a generic LED value with the green indicator identity |
| J301 | SHOU HAN TYPE-C 6P(073) / **C668623** | Actual six-contact power connector; legacy footprint name alone is misleading |
| SW501–SW508 | XKB TS-1101-C-W / **C318938** | Stocked 2.5 mm switch, not the TE FSMSM named by the footprint/model |
| C603, C604 | Samsung CL21B105KBFNNNE / **C28323** | Native 1 µF corrections already applied, following controller output-decoupling requirements |
| D301 | R+O SMF5.0CA / **C19077498** | Actual supplier manufacturer differs from the inherited Vishay datasheet link |

All fitted parts have manufacturer/MPN/LCSC metadata in the native PCB and schematic. Catalog identity verification does not certify a package substitution: the connector/switch mask, paste, polarity and body geometry still need the checks identified in [electrical review](ELECTRICAL-REVIEW.md).

## Availability and prototype quantities

At the 2026-10-11 snapshot, J601 C5417011 had **28** in the public available-to-order field and U601 C633309 had **52**. The correct LCD connector C2931360 had **21,786**. These are dated observations, not promises. The matching TE FSMSM C7278475 and URT C633310 had zero, so they are not silently substituted into this order plan.

Five prototypes is the provisional planning quantity until a batch size is chosen. JLCPCB attrition/spares and any minimum placement quantity must be checked in the quote; the per-board BOM is not an order-quantity calculation. A 25-board batch would already be close to the socket snapshot quantity before manufacturing loss/spares. Do not assume that stock still exists when the files are uploaded.

No current price is presented as a finished-board cost. A PCBA quote must include board fabrication, both-side assembly, setup/extended part charges, component loss, stencil/fixture requirements, shipping and taxes. Public unit prices alone cannot predict that total.

## JLCPCB process and the optional host

Request **both-side assembly** and let the quote determine the compatible service tier. The carrier has top-side controls and bottom-side electronics/connectors. USB-C also has through-hole shell attachments: confirm those are soldered as part of the accepted process. The custom outline/notch, fine-pitch parts, exposed-pad QFN and heavy card socket can affect fixture and DFM requirements. [JLCPCB fixture guidance](https://jlcpcb.com/help/article/uses-for-fixtures-and-pallets-during-smt-soldering).

For a host-inclusive version, JLCPCB must accept the exact Mini A/B module, its supplied packaging, attachment method and soldering limits. There is no verified JLCPCB module C-code in this plan. A consignment/global-sourcing path exists, but module acceptance, lead time and cost require confirmation. Do not put a made-up module code into the automated carrier BOM. [Component matching guidance](https://jlcpcb.com/help/article/component-matching-guidelines-for-pcba-orders), [consignment terms](https://jlcpcb.com/help/article/consignment-part-terms-conditions).

A fully assembled carrier does not include firmware provisioning or proof of functional behavior unless explicitly quoted. Include the prototype tests from the bring-up guide in a later production test specification.

## Before these become order files

1. Resolve or individually justify the native DRC findings. Do not lower clearance rules to make the report pass.
2. Qualify actual XKB switch terminal/paste geometry and actuator height; correct the legacy 3D model or use a verified model.
3. Review J401 mounting-plate solder-mask/paste openings and the exact LCD cable contact face.
4. Review USB-C shell soldering and the custom card socket/QFN stencil geometry.
5. In JLCPCB's placement preview, check each connector, IC, LED and transistor orientation. Native KiCad rotation is not automatically the supplier's zero-degree orientation; both-side rotations are currently unqualified.
6. Refresh inventory, match exact C-codes and obtain the DFM/assembly quote. Confirm all intended parts are selected; do not let automatic alternatives change contact type or package.
7. Only then produce a versioned Gerber/drill/assembly release with the same source revision and approved BOM/CPL.

This task prepares a reproducible sourcing/placement review package. It has not submitted a quote, placed an order, reserved parts, or sent material to JLCPCB. Those actions have not been performed implicitly.

## Regenerate with mise

```sh
mise run bom:refresh
mise run bom:generate
```

The refresh task performs read-only public catalog requests and retains failures as unverified. The generate task exports fresh native position data, checks selection/native metadata agreement, generates matching carrier BOM/CPL and accounts for every footprint. DNP and optional-host exclusions are intentional and checked. The experimental tscircuit BOM is not the JLCPCB ordering source.

## Completed native layout checks

The default carrier now has zero active ERC/DRC errors or warnings and no unconnected/parity issues. Two native courtyard exclusions are limited to the mutually exclusive R403/R404 and R409/R408 strap pairs; R404/R408 remain DNP. The check tool verifies the population assumption and rejects undocumented exclusions. Small passive/header placements, switch assembly envelopes and silkscreen collisions were corrected. LCD connector mounting lands now include solder-mask openings and paste apertures.

`mise run kicad:fab` produces nine Gerber layers, separate PTH/NPTH drill files, a ZIP and a board/file hash manifest after passing checks. The files support fabrication/DFM review; they do not reserve parts or establish switch reflow, enclosure actuator fit, panel compatibility or physical operation. The native BOM/CPL has been regenerated after placement changes. See [KICAD.md](../KICAD.md) for the editing and verification workflow.

# Ten-board prototype order

**Files are prepared for a JLCPCB prototype quotation. The new headers are
catalog-sourceable; ten smartcard sockets are already pre-ordered by the user. Do not approve
assembly payment until the exact-part sourcing, placement preview and DFM items
below are resolved.**

Upload `shieldsigner-full-pico-gerbers.zip`, `bom-jlcpcb.csv` and
`cpl-jlcpcb.csv` from the same outer prototype package. Do not use the website's
Mini-board downloads. `manifest.json` pins all manufacturing files to the board
SHA-256. `gerber-audit.json` independently checks the exported lands, perimeter,
334 drill/slot objects and coordinate datum.

## PCB and assembly selections

| Setting | Selection |
|---|---|
| Quantity | 10 assembled carriers |
| Finished PCB | 160 × 70 mm capsule; four copper layers |
| Material / thickness | FR-4, nominal 1.6 mm; confirm supplier stackup |
| Outer copper | 1 oz nominal |
| Solder mask / legend | Green / white |
| Finish | ENIG |
| Assembly | Both sides; Standard PCBA quotation |
| Population | 46 SMT pieces / 19 catalog lines; 11 top, 35 bottom |
| Via-in-pad process | Quote Epoxy Filled & Capped for exposed-pad vias; do not leave U601's exposed-pad via process unspecified |
| Panel preparation | Panel by JLCPCB; routed tabs with removable side rails, fiducials and tooling; see panel proposal |
| JLC order number | On removable rail, not on the front artwork or contact lands |

The Gerbers describe the finished carrier, not an assembly panel. The included
`panel-proposal.svg` is a supplier tooling proposal, not an upload Gerber.
Have JLCPCB approve its tabs, rails and depanelization, including USB/card access.
Request rails removed after assembly, with no residual tabs that obstruct the
finished carrier. If the factory translates the panel origin, it must translate
**every** CPL coordinate by the identical amount.

## Parts procurement

- **New carrier headers:** exact XKB X6511WVS-20H-C60D48R2 / **C2883777**.
  Two per carrier: 20 installed for ten boards. Proposed purchase/reservation is
  26 including six provisional spares; JLCPCB's actual attrition requirement
  controls. The dated standard-assembly snapshot is 73. Do not substitute R1,
  right-angle, through-hole or a different tail span.
- **Existing smartcard socket:** exact Amphenol **7312P0225A13LF / C5417011**.
  Ten installed; the user has already pre-ordered ten. **Do not duplicate this
  purchase.** The user confirmed these are pre-ordered into their JLCPCB parts library.
  Confirm usable arrival and check the final attrition requirement. Twelve was a provisional
  planning quantity including two spares, not an additional purchase request.
  The public snapshot contains only one in standard assembly stock; it does not
  show private pre-orders. Overseas stock is recorded separately. See
  `customer-procurement.json` and `procurement-for-ten.csv`.
- SEC1210 must remain **SEC1210/PV-UR2 / C633309**. Do not substitute a different
  reader firmware suffix. Remaining catalog identities and stock for ten are in
  `stock-for-ten.json`; all stock remains unreserved.

JLCPCB provides [pre-order and Global Sourcing](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction).
A catalog listing and this source audit are not a supplier reservation or an
accepted sourcing quote. The Amphenol manufacturer's
[exact-part page](https://www.amphenol-cs.com/product/7312p0225a13lf.html) identifies
active distributor channels for the socket.

## Placement review before approval

The corrected upload CPL already contains the retained J301/J601/U601 supplier
compensations. **Do not apply those offsets a second time.** The native-reference
CSV is diagnostic only. Verify the USB stakes/mouth, all smartcard socket pads
and locating holes, SEC1210 pin 1, LED polarity and regulator pin 1 in JLCPCB's
preview. Confirm the default J701 display build and DNP J702.

J203 and J204 are the two physical header strips expanded from logical U202;
the module itself is not a factory placement. The header body centers are:

| Assembly ref | Native X / Y (mm) | Upload CPL X / Y (mm) | Side / rotation |
|---|---|---|---|
| J203 | 85.3475 / 81.449 | 35.3475 / 48.551 | Bottom / 90° |
| J204 | 103.1275 / 81.449 | 53.1275 / 48.551 | Bottom / 90° |

The manufacturer-zero convention used here has the row along X. Check JLCPCB's
actual catalog model: each row must lie along the carrier's short axis, with
20 contacts at 2.54 mm pitch and row centers 17.78 mm apart. Verify **every
alternating R2 solder tail**, not just the body boxes. 90° and 270° are physically
equivalent for this unpolarized even-contact strip; a 0°/180° row is wrong.
`header-placement-map.json` records full-size-module pin correspondence and the
native contact-1 end. If JLCPCB lacks a usable catalog model, supply the XKB
manufacturer drawing and require the model/land alignment to be reviewed before
releasing assembly. The preview has not been approved by this local workflow.

## Customer-fitted parts and first article

Use an **unheadered full-size Luckfox Pico or Pico Plus**. Fit two exact Harwin
**M20-7822042** female socket strips to the module's underside, with the openings
facing the carrier. The Pico USB end must face the carrier’s **USB END** arrow.
Pico contact 1 is at native (103.1275, 57.319); contact 40/VBUS is at
(85.3475, 57.319). The XKB strips’ own pin numbering is recorded separately;
follow the Pico orientation mark when installing the module. These are module-side parts; they do not go into the JLCPCB
carrier BOM. Keep the module component side/microSD outward. With everything
unpowered, the assembled carrier can serve as an alignment fixture while fitting
the two socket strips to the module. Do not force a misaligned module.

J701 display header/socket, chosen LCD, J302 optional power header, Pico/Plus,
module sockets and M2.5 supports remain customer-fitted. Fit one display only.
Preserve the documented JP701/JP702 mutually exclusive voltage selection; never
bridge both. Enclosure/ethernet support and the full-size module's firmware/BSP
remain unqualified. Do not assume the existing Mini enclosure fits this stack.

Before inserting modules, inspect the solder joints and check for supply shorts.
Power from one source at a time with current limiting. Check the carrier display
regulator rail first; HOST3V3 is supplied by the module and is not expected from
an empty carrier. Bring up one unit through power, all controls, display,
microSD/camera and smartcard tests before operating the remaining prototypes.
The included bring-up and software-compatibility documents explain the inherited
bench-image pin conflict; no full-size Pico/Plus powered qualification is claimed.

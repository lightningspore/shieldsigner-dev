# Eight-pin pill carrier: 0.0.9 first-article review kit

**Status: stock_review_required.** This artwork revision adds `denver.space` branding
and preserves the existing electrical/mechanical layout. See the included
`branding-audit.json` and `PCB-ORDER-READINESS.md`. The previous 0.0.7 supplier
preview and unpaid quote are historical; no new upload, cart update, assembler
placement approval or physical qualification is claimed.

Unzip the outer order ZIP once. Upload **shieldsigner-modular-gerbers.zip**, then
its matching **bom-jlcpcb.csv** and **cpl-jlcpcb.csv**. Request two copper layers,
1.6 mm thickness and both-side SMT assembly for the 160×70 mm pill. Do not mix
standard FPC, former Pico-bay or separate PWM-candidate files into this order.

There are **35 SMT placements / 17 catalog lines**: 11 on top (eight switches
and U701/C701/C702), 24 underneath. Modules, customer headers/supports, six copper
jumpers and 12 copper-only test pads are outside the SMT population. J302 is the
optional customer-fitted +5 V/GND input header.

Gerbers, plated/nonplated drills and CPL use the same auxiliary origin (50,130)
mm. CPL Y is 130 minus native PCB Y; bottom X is not mirrored. Supplier
compensation for J301/J601/U601 is already included in the upload CPL; the native
reference CSV is diagnostic only. **Do not repeat the historical manual moves.**
Use [the placement checklist](placement-review/README.md) for the new preview.

The saved manufacturer land-pattern/model checks remain useful. Regenerated
native checks and the compatibility proof must match the new PCB hash. Stock
files are dated snapshots, not reservations. Select the exact USB connector if
JLC's BOM importer leaves it unchecked. Confirm all matched MPNs, stock/attrition,
DFM and a new quote before payment; do not substitute the SEC1210 firmware suffix.

## Five-board stock blocker

Fresh public fields show only **2** C5417011 / 7312P0225A13LF sockets under
`canPresaleNumber`, against **5** installed sockets required. `overseasStockCount`
is 9 and is kept separate; it is not automatically available to standard assembly.
Five assembled units are not checkout-ready until JLC confirms enough exact
sockets and attrition. Do not assume two visible sockets guarantee two units.
Switches show 46 against 40 installed; SEC1210 shows 46 against 5. All stock remains
unreserved and subject to assembler sourcing review. No part swap is proposed.

## Factory and first-article gates

**Do not power this carrier using the tested base-fork bench image unchanged.**
It drives two carrier button nets as LCD outputs. Use the carrier-profile image
and read the included `PCB-SOFTWARE-COMPATIBILITY.md` before inserting modules.
This is a real profile conflict; the artwork change does not fix it.

The capsule still needs an approved assembly rail/fiducial/tooling/depanelization
plan. The nominal board uses 0.15 mm minimum routed tracks, 0.30 mm via drills,
0.15 mm actual via annuli and four USB plated slots of 0.60 × 1.20 mm. The native
rules enforce 0.15 mm copper and 0.20 mm routed-edge clearance. These selected
features do not replace factory Gerber DFM or inspection.

Review the QFN exposed-pad stencil and central via for solder wicking/voiding,
then establish a physical inspection/rework process. U202 and R606 reference
text were already small in the old layout; inspect them and all new artwork in
the new fabrication preview. Copper mask/pad clearance and legibility need visual
review even when electrical DRC passes.

Exact header purchase MPNs, LCD/module physical fit, rail transients, LCD-regulator
thermal margin, smartcard operation and enclosure assembly remain unqualified.
Build and measure one first article before populating repeats. The supplied
readiness and bring-up guides specify those checks. Do not infer carrier
qualification from the separately tested 240×240 firmware bench setup.

## Historical evidence

`history/0.0.7-preview/` preserves the old correction record, release manifest,
readiness report, placement guide and unpaid quote. Their hashes/claims apply
only to the original 0.0.7 board. The root-level dated quote and older feasibility
reports also retain their original identities; they are not a new 0.0.9 quote.

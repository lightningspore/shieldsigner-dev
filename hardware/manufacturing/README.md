# Eight-pin pill carrier: fabrication and review kit

The working PCB is now four-layer. Historical 0.0.9 ZIPs remain two-layer; do not mix them with new exports. Confirm the nominal 1.6 mm stackup with the fabricator.

**0.0.13-dev: stock_review_required.** Four copper layers, nine factory Keystone SMT points and four new bracket mounts. The current `angle-header-audit.json` verifies retained footprints/pad nets, protected supplier component poses, 45-degree routing and the restored customer header; `branding-audit.json` is historical 0.0.9 evidence. The selected switches, reader IC and socket have zero standard-assembly stock as of 2026-11-09. Confirm sourcing, attrition and new placement/DFM review before checkout.

Unzip the outer order ZIP once. Upload **shieldsigner-modular-gerbers.zip**, then
its matching **bom-jlcpcb.csv** and **cpl-jlcpcb.csv**. For freshly regenerated working-board Gerbers, request four copper layers,
1.6 mm thickness and both-side SMT assembly for the 160×70 mm pill. Do not mix
standard FPC, former Pico-bay or separate PWM-candidate files into this order.

There are **44 SMT placements / 18 catalog lines**: 11 on top and 33 underneath, including all nine Keystone 5015 / C2906768 service points. Modules, customer headers/supports, six copper jumpers and 12 copper-only probe pads are outside the SMT population. J302 is a customer-fitted front-side right-angle 5 V/GND header under the LCD, excluded from factory assembly. TP901/TP902 provide factory-fitted +5 V/GND bench clips.

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

## Five-board stock blockers

The 2026-11-09 public snapshot shows zero standard-assembly stock for the
selected switches (C2689642), smartcard sockets (C5417011) and SEC1210 reader
(C633309). Five boards require 40 switches, five sockets and five reader ICs,
before attrition. Overseas stock is recorded separately in `readiness.json`;
it is not automatically available to standard assembly. All inventory remains
unreserved. Exact-part sourcing and attrition must be confirmed before checkout.

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
text now meet the 0.8 mm height / 0.15 mm stroke screen; inspect all new artwork
in the fabrication preview. Copper mask/pad clearance and legibility need visual
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

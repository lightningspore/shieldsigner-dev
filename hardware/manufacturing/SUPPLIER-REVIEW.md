# Supplier review request — ShieldSigner 0.0.12-dev

Prepared locally; not sent, uploaded, quoted or approved.

PCB SHA-256: `5a874247461a4dcaff97fbb4b9023068d565e46f8a7cc002c987ccaeaaf6ab08`. Match all replies and placement previews to this
revision and the checked Gerber/BOM/CPL file hashes in `readiness.json`.
Prototype basis: five bare PCBs; quote one populated first article and the
incremental cost for five populated boards separately. Do not release repeat
assemblies until the first article passes the supplied bring-up record.

## Board and population

160 × 70 mm capsule, four copper layers, nominal 1.6 mm finished thickness.
F.Cu and B.Cu carry signals/components; both inner layers are GND planes.
Confirm the production stackup and finished thickness tolerance. Double-sided
SMT: 44 placements / 18 SKUs, 11 top and 33 bottom. All nine Keystone
5015 / C2906768 points must be factory fitted: TP901, TP902 and TP909 top,
TP903–TP908 bottom. J302 is customer-fitted: do not factory assemble the front-side 1x2 right-angle 5 V/GND header. Customer module headers and hardware
are excluded; copper-only jumpers/probe pads are not purchased components.

## Sourcing answers required

The 2026-11-09 public snapshot has zero standard assembly stock for
C2689642 / PTS636SK25SMTRLFS (8 per board),
C5417011 / 7312P0225A13LF (1 per board), and
C633309 / SEC1210/PV-UR2 (1 per board).
Confirm exact-MPN availability, acquisition method, MOQ, attrition, cost and
lead time. Overseas quantities are separate inventory and not reservations.
Do not substitute the reader firmware suffix or package without design review.

## DFM and assembly answers required

- Propose a panel drawing with rails, fiducials, tooling and depanelization
  appropriate to the capsule. Preserve USB/card access, the original LCD
  supports and all four new 2.7 mm NPTH bracket holes. Show attachment locations,
  board-to-panel clearances and the removal method before approval.
- Confirm the 0.15 mm minimum tracks, 0.30 mm via drills, 0.15 mm actual via
  annuli and four 0.60 × 1.20 mm plated USB slots against the supplied Gerbers.
- Review QFN U601: four paste windows, approximately 63.1% exposed-pad paste
  coverage and an existing 0.30 mm through-via in the thermal pad. Specify
  stencil thickness, via treatment, solder-wicking control, hidden-pad
  inspection and rework criteria; no filled/capped process is assumed.
- Confirm two-sided reflow sequence, retention of the underside socket/loops,
  exact component thermal limits and USB shell-stake solder-fill process.
- Review the compensated CPL once. Inspect J301 mouth/stakes/tails, J601
  numbered contacts and U601 pin 1 against `placement-review/README.md`.
  Confirm all nine Keystone rows and sides. Do not apply historical manual
  corrections a second time. Return a current placement preview.
- Report any silk, paste, solder-mask, edge or tooling changes for review.
  Native ERC/DRC pass, but this is not supplier DFM or physical qualification.

## Release evidence

Record the accepted panel drawing, stackup, exact-part sourcing/attrition,
placement preview, process/inspection plan, quote and output hashes. A physical
first article must establish header/module fit, shorts and rail voltages before
modules, LCD operation, buttons, camera, card operation and temperature/current
limits. Follow `BRINGUP.md`; use the carrier firmware profile described in
`PCB-SOFTWARE-COMPATIBILITY.md`. No powered acceptance results exist yet.

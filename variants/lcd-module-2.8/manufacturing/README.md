# Eight-pin pill carrier: prototype quote kit

Unzip the outer order ZIP once. Upload **shieldsigner-modular-gerbers.zip**, then its matching **bom-jlcpcb.csv** and **cpl-jlcpcb.csv**. These are one set for the **0.0.6-dev, 160×70 mm pill carrier**. Do not mix the standard FPC or former Pico-bay files into this order.

Request **two copper layers, 1.6 mm thickness and two-sided SMT assembly**. There are **35 placements / 17 catalog lines**: eight switches and U701/C701/C702 on top; 24 parts underneath. Gerbers/drills/CPL share the auxiliary origin (50,130) mm. CPL coordinates use millimeters, Y = 130 minus PCB Y; bottom X is not mirrored. Inspect socket entrance, USB orientation, SEC1210 pin 1, regulator pin 1, sides and rotations in the assembler's preview.

Switch, USB, card, SEC1210 and AP2112 lead lands follow retained supplier/manufacturer drawings. The SEC1210 has four reduced exposed-pad paste windows. Customer Luckfox castellated lands have no stencil paste. Old bare-panel FPC/backlight lands and optional J302 are removed, not part of this PCB. There are **zero DRC exclusions**. Four both-side 6 mm hardware keepouts reserve space around M2.5 supports; the copper planes and input circuitry clear those areas.

J701, U202, H701–H704 and six copper jumpers are outside SMT BOM/CPL. `population.csv` accounts for all **47 footprints**. `customer-parts.csv` lists the retail LCD, ordinary headers and supports. JLCPCB does not source/install the retail LCD or Luckfox. Customer soldering is limited to 2.54 mm headers: 30 carrier joints, up to 30 additional module joints if bare.

The immediate plan is **one populated first article** before repeat builds. Ask the supplier to state its bare-board and assembled-board minima separately; surplus bare boards may remain unpopulated. The historical stock report below was calculated for five boards and does not prescribe five assembled units. `stock-for-five.json` contains dated public assembly-stock fields and required quantities, not a reservation. Final stock, minimum-purchase/attrition fees, card-socket handling, loading and the actual quote need JLCPCB confirmation. Do not substitute the SEC1210 firmware suffix or an arbitrary display.

The matching kit passes native ERC/DRC, connectivity, schematic parity and the documented model/land-pattern/geometry assertions. It is prepared for **prototype quotation and assembler DFM**, not physical qualification. Header fit, LCD rail/thermal behavior, display initialization, reader/card transactions and enclosure fit remain first-article work. The LCD, socket and supports use explicitly simplified dimensional models. No paid order has been placed.

USB4125-GF-A uses its 1.90 mm shell stakes on the 1.60 mm PCB. Stakes do not protrude through the opposite face. Have JLC review insertion/solder fill and all rotations in the assembly preview; do not substitute -0190 without a deliberate BOM review. Switches are C&K PTS636SK25SMTRLFS, C2689642.

## Nominal fabrication screen and assembly preparation

`mise run variant:lcd:fab-audit` records the [fabrication capability audit](fabrication-capability-audit.json). Current native features include 0.20 mm minimum routed tracks, 220 vias with 0.30 mm drills / 0.15 mm actual annular rings, and four plated USB slots of 0.60 × 1.20 mm. Native DRC enforces 0.15 mm copper clearance and 0.20 mm routed-edge clearance. These selected nominal features screen within [JLC's published rigid-PCB capability profile](https://jlcpcb.com/capabilities/pcb-capabilities/); this is not an independent Gerber DFM review or inspection of finished boards.

The single capsule is not an approved assembly panel. JLC's [standard-assembly rail/fiducial guidance](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order) and [irregular-outline review requirement](https://jlcpcb.com/help/article/pcb-dimensions) still need a supplier-approved implementation for this board. Obtain the rail/tooling/fiducial/depaneling drawing and its cost. Do not put tabs where they obstruct USB/card access, display supports or the final enclosure. No board-area or case geometry change has been approved by the software screen.

Visible footprint reference labels U202 (0.10 mm stroke) and R606 (0.70 mm height) are flagged for fabrication-preview legibility review. This limited text scan does not cover board artwork or establish an electrical fault. A future layout revision can improve them alongside any first-article corrections; do not mix modified art with an older pinned release kit.

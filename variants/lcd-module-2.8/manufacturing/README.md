# Modular 2.8-inch prototype quote kit

Unzip the outer order ZIP once. Upload **shieldsigner-modular-gerbers.zip** for the PCB, then **bom-jlcpcb.csv** and **cpl-jlcpcb.csv** for assembly. These three files are one set. Do not mix standard-carrier or upstream order files into this variant.

Request **two-layer, 1.6 mm PCB and two-sided SMT assembly**. There are 32 fitted SMT placements across 16 catalog lines. Eight switches are on top; the reader, USB power and remaining circuitry are on the bottom. The drill set includes separate plated and nonplated files, USB shield slots, Luckfox/LCD header holes and four M2.5 clearance holes. All fabrication/placement files use the native auxiliary origin (50,130) mm. CPL coordinates are millimeters; X is not mirrored for bottom parts. Inspect the assembler's preview for side, rotation, socket card entrance, USB orientation and SEC1210 pin 1 before approving a quote.

The revised switch, USB, card and SEC1210 lead solder lands follow their supplier drawings; the SEC1210 EP has four reduced paste windows. Unpopulated bare-LCD parts and the customer's Luckfox mounting lands receive no stencil paste. USB ground A12 deliberately uses a solid plane connection and an explicit ground trace; global clearance/thermal rules are unchanged.

J701, U202, H701–H704 and copper jumpers do not belong in the SMT BOM/CPL. `population.csv` accounts for every footprint. `customer-parts.csv` lists the purchased display module, ordinary through-hole headers and supports. Customer soldering is on the 2.54 mm headers, not the SEC1210 QFN, card socket or USB-C contacts. JLCPCB is not being asked to source/install the retail LCD or Luckfox module.

Use five assembled boards for the initial quote. The dated public catalog snapshot had enough parts for five, with **28 smartcard sockets** and **55 SEC1210/PV-UR2** available in the assembly stock field. The socket minimum-purchase field was three. This is not a reservation; the quote determines current stock, loading/attrition fees, tray handling and actual order quantities. Do not substitute SEC1210 firmware suffixes or a generic 2.8-inch display without review.

This kit passes native ERC/DRC, connectivity, parity and mechanical/footprint assertions. It is ready for **prototype quotation and assembler DFM review**, not a claim of completed physical qualification. No paid order has been placed. Header fit, first power-up, firmware display initialization, reader/card transactions and enclosure fit still need first-article tests.

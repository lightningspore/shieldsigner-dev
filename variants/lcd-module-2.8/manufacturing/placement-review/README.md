# JLCPCB assembly placement guide — PCB 0.0.6-dev

Assembly package **r2**, 2026-10-24. The copper, drills and BOM are unchanged. This guide accompanies the Gerbers, BOM and CPL in the same ZIP.

## Upload and confirm

1. Upload `shieldsigner-modular-gerbers.zip`, `bom-jlcpcb.csv` and `cpl-jlcpcb.csv`. Select 1.6 mm, LeadFree HASL and Both Sides assembly. The BOM contains 35 SMT placements across 17 catalog lines. Modules and through-hole headers are customer fitted.
2. **The CPL contains native KiCad origins and rotations. It is not a precompensated export of the manually adjusted JLC cart.** A new upload needs the following catalog alignment checks. Do not assume saved cart adjustments transfer to a fresh upload.
3. **J301 USB-C:** the initial catalog interpretation needed a 180-degree rotation and an inward translation. The cable mouth must face outward; all six signal/power tails must overlap the inward-facing solder lands, and all four shell stakes must align with their slotted lands.
4. **J601 smartcard:** use the user's verified orientation described below: tapered edge at top, notch at bottom in the carrier-bottom/component-side view. Check the numbered contacts and both locating holes; do not rotate it back to the old intermediate preview.
5. Keep **Confirm Parts Placement: Yes**. Review the assembler's final DFM/placement confirmation before approving assembly. The browser preview check is not a physical qualification or production release.

The current five-board quote is USD 195.54 before freight/tax/coupons. No payment or order was submitted during this review. Exact corrected numeric supplier placements have not been exported; obtain the assembler-confirmed export before implementing automatic CPL compensation.

## Numbered-contact verification completed

**The user's revised J601 rotation passes the contact-position check.** Its component-side view has the tapered edge at the top and the notch at the bottom. The prior offset-only preview below is historical and must not be reused.

The [numeric audit](smartcard-contact-audit.json) compares every C1–C8/COM/NO pad center and land size, plus both locating holes, with the **JLCEDA/EasyEDA official library (嘉立创EDA/EasyEDA官方库)** [C5417011 footprint](https://easyeda.com/api/components/fac09934403f4310b3853998f3c08281), obtained through its [part lookup](https://easyeda.com/api/products/C5417011/components?version=6.4.19.5). The catalog footprint differs from our component-local origin by **+0.8 mm X, 0 mm Y**; after this translation all compared dimensions agree within **0.001 mm**. That is a library-coordinate comparison, not a measured assembly tolerance. The manufacturer drawing's page 2 establishes the numbered pattern.

In the **carrier-bottom/component-side view shown by JLC**, the upper row runs **C1, C2, C3, C4 left to right**; the lower row runs **C5, C6, C7, C8 left to right**. The detection contacts are **NO then COM left to right**, between the rows and to their right. The locating holes are lower left and upper right. This asymmetric contact pattern, together with the outline, resolves the 180-degree ambiguity that the two locating holes alone do not reliably resolve.

| Contact | Native net / purpose | Check |
|---|---|---|
| C1 | SEC1210_SC_VCC, switched card supply | Upper left |
| C2 | SEC1210_SC_RST | Upper row, second |
| C3 | SEC1210_SC_CLK_PostR | Upper row, third |
| C4 | RFU, unconnected | Upper right |
| C5 | GND | Lower left |
| C6 | SEC1210_SC_VCC, tied to card VCC by this design | Lower row, second |
| C7 | SEC1210_SC_IO | Lower row, third |
| C8 | RFU, unconnected | Lower right |
| NO | SEC1210_SC_PRSNT | Left detection pad |
| COM | GND | Right detection pad |

The current preview was checked by registering the catalog outline/holes, calculating its numbered contact locations and temporarily moving the model aside to expose the actual copper. Upper row, lower row and both switch pads matched. **Undo restored the user's placement exactly**; no rotation or offset change was retained by this check. No order/payment was submitted. Final assembler DFM/placement approval and physical bring-up remain separate.

## Superseded preview

`jlc-bottom-corrected.png` is retained only as historical evidence of an **incorrect offset-only smartcard assessment**. It is not the final assembly reference. The user subsequently rotated J601; the numbered-contact check above supports that revised orientation.

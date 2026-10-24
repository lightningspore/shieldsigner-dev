# JLCPCB assembly placement guide — PCB 0.0.6-dev

Assembly package **r3**, 2026-10-24. The upload CPL now includes the supplier rotation/origin corrections. It was re-uploaded into JLCPCB and visually checked **without manual component moves**. Copper, drills and the BOM design are unchanged.

## Upload and confirm

1. Upload `shieldsigner-modular-gerbers.zip`, `bom-jlcpcb.csv` and **`cpl-jlcpcb.csv` from this package**. Select 1.6 mm, LeadFree HASL and Both Sides assembly. Expect 35 SMT placements across 17 catalog lines. Modules and through-hole headers are customer fitted.
2. **Do not repeat the old manual rotations/offsets. They are already applied in this CSV.** `placement-review/cpl-native-reference.csv` is a diagnostic native export, not the JLC upload file.
3. Explicitly select J301 USB4125-GF-A-0190 / C5246813 in JLC's matched BOM if it is unchecked: the uploader otherwise omits this connector. Verify quantity 5 for a five-board assembly.
4. Inspect the imported placements: USB mouth outward, solder tails on inward lands, all shell stakes in slots; smartcard tapered edge up and notch down in bottom/component-side view, with numbered contacts as below; U601 pin-1 marker at the native upper-left triangle.
5. Keep **Confirm Parts Placement: Yes** and review final assembler DFM before approving assembly. The preview check is not physical qualification.

| Ref | Corrected CPL Mid X (mm) | Mid Y (mm) | Rotation | Correction from native export |
|---|---:|---:|---:|---|
| J301 | 46.510000 | 9.830000 | 0° | +0.84 mm Y; +180° |
| J601 | 88.620000 | 20.050000 | 0° | -0.8 mm X; +180° |
| U601 | 85.000000 | 43.700000 | 0° | +180° |

All other 32 placement rows are unchanged. Corrections are pinned to the PCB SHA and catalog identities in `jlc-placement-corrections.json` in the native source package. The exporter rejects a changed board, changed identity/side/datum, or attempts to apply compensation twice. Each new catalog model or PCB revision still needs preview review.

J301's translation uses the four physical shell-stake centers as the mechanical datum; the supplier's copper-pad centers are not a substitute for the manufacturer lead geometry. Its imported preview shows the six solder-tail ends overlapping their lands and the stakes aligned with the slots. U601's corrected pin-1 dot agrees with the native triangle. D302 LED's library has a different pad-1 baseline and needs **no** additional rotation: a blanket rotation change for all bottom-side parts would be incorrect. U701 remains unchanged on top.

The checked five-board quote is USD 195.54 before freight/tax/coupons. No payment/order was submitted during this review.

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

The current preview was checked by registering the catalog outline/holes, calculating its numbered contact locations and temporarily moving the model aside to expose the actual copper. Upper row, lower row and both switch pads matched. **Undo restored the user's placement exactly** during that earlier check. Package r3 subsequently reproduced this same numbered-contact orientation from the corrected CSV with no manual moves. No order/payment was submitted. Final assembler DFM/placement approval and physical bring-up remain separate.

## Superseded previews

The old `jlc-bottom-corrected.png` and assembly packages r1/r2 predate the corrected CPL. Do not use their smartcard orientation or their uncompensated CSV for a new order. Use r3 and the table above.

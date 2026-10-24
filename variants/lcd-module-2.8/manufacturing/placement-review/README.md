# JLCPCB placement correction, 2026-10-24

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

## Earlier review history

> **Superseded smartcard assessment:** the user subsequently rotated J601 by 180°, producing a substantially better match to the manufacturer's tapered body/notch and the PCB silkscreen. The earlier claim below that retaining its rotation was sufficient is withdrawn. `jlc-bottom-corrected.png` is an **intermediate historical preview**, not an approved assembly reference. Preview markers alone did not establish contact orientation. Leave the user's revised placement intact and require final C1–C8/COM/NO and locating-hole alignment against the manufacturer drawing before assembly approval. The USB-C correction remains a separate finding.

PCB 0.0.6-dev is unchanged. The current five-board JLCPCB cart was updated using its component-placement editor, saved back to the cart, and checked through the cart's saved Part Placement preview. The saved corrected bottom image is `jlc-bottom-corrected.png`.

- **J301 USB4125-GF-A-0190 / C5246813:** rotated 180 degrees relative to the initial JLC interpretation and translated inward until the six solder tails overlap the six PCB lands. The cable mouth faces the outside board edge. The shell stakes align with the slotted lands.
- **J601 7312P0225A13LF / C5417011:** retained its rotation and translated sideways. The two asymmetrically placed locating pegs were aligned with the two PCB locating holes, rather than relying on the body silkscreen. The footprint holes and contact pattern were compared with manufacturer drawing page 2. The catalog body's outline is not a substitute for the manufacturer's drawing or final assembly DFM.
- The price remains **USD 195.54**, five boards, before shipping/tax/coupons. Saved PCBA settings were checked: Standard, Both Sides, quantity 5, **Confirm Parts Placement: Yes**.
- No order or payment was submitted. The visual preview is not assembler qualification or a physical fit test. Review JLC's final DFM/placement confirmation before releasing production.

## Fresh uploads

These are **supplier-side adjustments saved in this cart**, not changes to the native PCB. The downloadable `cpl-jlcpcb.csv` still contains the native KiCad footprint origins/rotations. Re-uploading that file starts with the original catalog interpretation: repeat the two alignment checks above. Do not assume these adjustments transfer to another quote or a different catalog model. Exact corrected numeric supplier placements were not exported by this preview UI, so no guessed offsets have been baked into the generic CPL.

Do not use the saved intermediate image as the final smartcard orientation reference. Obtain/export the assembler-confirmed numeric placements before turning these into automatic CPL compensation. No native copper, drill, BOM or Gerber changes have been made for these supplier placement adjustments.

# JLCPCB placement correction, 2026-10-24

PCB 0.0.6-dev is unchanged. The current five-board JLCPCB cart was updated using its component-placement editor, saved back to the cart, and checked through the cart's saved Part Placement preview. The saved corrected bottom image is `jlc-bottom-corrected.png`.

- **J301 USB4125-GF-A-0190 / C5246813:** rotated 180 degrees relative to the initial JLC interpretation and translated inward until the six solder tails overlap the six PCB lands. The cable mouth faces the outside board edge. The shell stakes align with the slotted lands.
- **J601 7312P0225A13LF / C5417011:** retained its rotation and translated sideways. The two asymmetrically placed locating pegs were aligned with the two PCB locating holes, rather than relying on the body silkscreen. The footprint holes and contact pattern were compared with manufacturer drawing page 2. The catalog body's outline is not a substitute for the manufacturer's drawing or final assembly DFM.
- The price remains **USD 195.54**, five boards, before shipping/tax/coupons. Saved PCBA settings were checked: Standard, Both Sides, quantity 5, **Confirm Parts Placement: Yes**.
- No order or payment was submitted. The visual preview is not assembler qualification or a physical fit test. Review JLC's final DFM/placement confirmation before releasing production.

## Fresh uploads

These are **supplier-side adjustments saved in this cart**, not changes to the native PCB. The downloadable `cpl-jlcpcb.csv` still contains the native KiCad footprint origins/rotations. Re-uploading that file starts with the original catalog interpretation: repeat the two alignment checks above. Do not assume these adjustments transfer to another quote or a different catalog model. Exact corrected numeric supplier placements were not exported by this preview UI, so no guessed offsets have been baked into the generic CPL.

Use the saved image as the visual reference. Obtain/export the assembler-confirmed numeric placements before turning these into automatic CPL compensation. The native copper, drill, BOM and Gerber files do not require replacement for these supplier placement adjustments.

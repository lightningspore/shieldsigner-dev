# Switch and USB-C mechanical substitution review

Reviewed 2026-10-17 for the LCD-module pill carrier, native PCB 0.0.4-dev. This is a drawing comparison, not a sample-fit approval. The original-board findings below explain why revision 0.0.5-dev changes the native lands; they are not a prohibition on a new revision.

## Original-board comparison (0.0.4-dev)

| Original | Candidate | Disposition |
|---|---|---|
| XKB TS-1101-C-W, eight switches | C&K PTS636SK25SMTR LFS, G leads | Electrically plausible; different recommended lands and button tolerance. Not approved on the existing board/case. |
| SHOUHAN TYPE-C 6P(073), J301 | GCT USB4135-GF-A | Reject as a drop-in: surface-mount shell tabs replace through-hole stakes. |
| Same SHOUHAN connector | GCT USB4125-GF-A | Closer candidate, but slot size and contact-row position differ. Requires sample and footprint review. |

At revision 0.0.4-dev, these nine fitted pieces were two unresolved purchase lines. Revision 0.0.5-dev resolves their sourcing with the redesigned lands described below.

## Switch: nominal height alone is insufficient

Compare the [original XKB drawing](../reference/pdfs/C318938.pdf) with the [C&K drawing](../reference/pdfs/CK-PTS636.pdf), pages 3–4. The retained C&K document is the 7 October 2020 edition. Select the **2.5 mm G-lead version without the optional ground pin**; J and F lead variants have different land patterns.

All dimensions below are mm. The native footprint is `XKB_TS1101_C_W_reflow` in the variant's local ShieldSigner library.

| Feature | Existing footprint / XKB | C&K G-lead 2.5 mm drawing |
|---|---|---|
| Pad centers, X | ±3.700 | ±3.875 recommended |
| Each recommended copper land | 1.20 × 1.00 | 1.25 × 2.10 |
| Inner gap / outer span | 6.20 / 8.60 | 6.50 / 9.00 |
| Body | 6.0 × 3.6 | 6.1 ±0.1 × 3.7 ±0.2 |
| Height | 2.5 ±0.1 | 2.5 ±0.2 |
| Actuator | 2.6 × 1.3 | 2.7 × 1.3 |
| Operating force | 260 gf | 250 ±50 gf |

The C&K recommended pads move 0.175 mm outward on each side and extend substantially farther across the lead. Nominal lead overlap with the existing pads is possible, but this is not the manufacturer's recommended land pattern. Land-area overlap is not a measurement of actual solder-joint coverage.

The more consequential finding is in `enclosure/case.scad`: the button tip rests at z=2.6 above the carrier, with 0.35 mm allowed downward movement. With a nominal 2.5 mm switch this leaves a 0.1 mm gap. The C&K height tolerance alone changes that gap to **−0.1 through +0.3 mm**, before PCB, solder and printed-part tolerances. A tall sample can preload the button; a short one can consume too much available stroke. Its specified travel also has tolerance. The original switch itself still requires physical enclosure qualification.

Before selecting this switch: obtain samples, measure soldered height and travel, check all button locations, and establish a plunger/stop tolerance budget. A revised footprint needs normal clearance, paste and courtyard review; changing the purchase number alone is insufficient.

## USB-C: compare shell retention as well as the six contacts

The native `SHOUHAN_TYPE_C_6P_073` footprint has six signal/power pads at y=−3.18. Across X, the ground, VBUS and CC pairs are ±2.75, ±1.52 and ±0.50. Shell stakes are at x=±4.32, y=−2.70 and +1.10. Dimensions are in mm.

| Feature | Existing footprint | GCT USB4125, rev A6 | GCT USB4135, rev A2 |
|---|---|---|---|
| Shell retention | Four plated slots | Four plated slots | Four SMT lands |
| Shell X pitch | 8.64 | 8.64 | 10.25 |
| Shell row pitch | 3.80 | 3.80 | 3.58 |
| Slot opening | 0.50 × 1.20 | 0.60 × 1.20 recommended | No slots |
| Shell copper around slots | 1.00 × 1.70 | 1.10 × 1.70 recommended | Different SMT geometry |
| Contact row to rear shell row | 0.48 | 0.68 | Different shell layout |
| Ground contact land width | 0.90 | 0.76 | 0.76 |
| Body width / depth | 8.94 / 6.80 in original drawing | 8.94 / 6.80 | 8.94 / 6.90 |

Both GCT drawings retain the same contact order and nominal X positions. That is helpful electrically but does not establish mechanical interchangeability.

**USB4125:** aligning the shell slots leaves the contact row displaced by 0.20 mm. Its recommended slot is 0.10 mm wider than ours. The drawing does not justify assuming its stakes will enter our narrower finished holes. It also offers two shell-stake lengths: blank suffix is 1.00 mm; `-0190` is 1.90 mm. Select and verify the actual ordered suffix against PCB thickness, insertion and solder access. Do not silently substitute one length for the other. The face is 2.60 mm beyond the front shell row, matching the original drawing's nominal relationship; physical plug/case access still needs verification.

**USB4135:** the SMT shell lands move outward and have different row spacing. Existing plated-slot pads cannot be treated as its intended retention lands. It needs a PCB revision and a fresh enclosure/plug-access check.

The inherited KiCad fabrication outline is not a reliable substitute for a manufacturer's mating-face datum. Use the dimensioned drawing and actual connector sample when assessing case recess and cable clearance.

## Next qualification step

Prioritize **USB4125 samples** over USB4135. Measure stake width/thickness, insertion into a plated-slot coupon, contact registration and cable access. For the switch, test a soldered C&K sample with an adjustable plunger coupon before deciding on a board/case variant. Then choose whether to preserve original parts on this revision or produce a distinct DigiKey-oriented revision. No physical tests have been performed by this review.

## Retained sources

- [XKB original drawing](../reference/pdfs/C318938.pdf).
- [SHOUHAN original drawing](../reference/pdfs/C668623.pdf).
- [C&K PTS636 archived manufacturer datasheet](../reference/pdfs/CK-PTS636.pdf), 7 October 2020; [download source](https://datasheet.lcsc.com/datasheet/pdf/229e2204c94be8eac226511395a363de.pdf?productCode=C2689642).
- [GCT USB4125 drawing](../reference/pdfs/GCT-USB4125.pdf), A6, 20 November 2025; [manufacturer source](https://www.gct.co/files/drawings/usb4125.pdf).
- [GCT USB4135 drawing](../reference/pdfs/GCT-USB4135.pdf), A2, 13 September 2024; [manufacturer source](https://www.gct.co/files/drawings/usb4135.pdf).

PDF byte counts and SHA-256 are recorded in [the reference index](PDF-REFERENCES.md) and `pdf-references.json`. Stock and exact distributor order suffixes must be checked when ordering; this report does not establish current availability.

## Shared-supplier design direction — 2026-10-17

The priority is now one exact manufacturer part number at JLCPCB and DigiKey; preserving the old footprint is secondary. Revise the PCB around the chosen part rather than accepting an undocumented footprint compromise.

| Function | Target MPN | JLCPCB assembly catalog | DigiKey cut-tape order code |
|---|---|---|---|
| Eight switches | C&K PTS636SK25SMTR LFS | [C2689642](https://jlcpcb.com/partdetail/CK-PTS636SK25SMTRLFS/C2689642) | [CKN12322-1-ND](https://www.digikey.com/en/products/detail/c-k/PTS636SK25SMTR-LFS/10071735) |
| USB-C | GCT USB4125-GF-A | [C3151650](https://jlcpcb.com/partdetail/GCT-USB4125_GFA/C3151650) | [2073-USB4125-GF-ACT-ND](https://www.digikey.com/en/products/detail/gct/USB4125-GF-A/13547388) |

Both suppliers list each exact target MPN. DigiKey explicitly lists the spaceless C&K spelling as an alias. USB4125-GF-A is the default 1.00 mm stake version; do not replace it with the separately cataloged -0190 version without updating the selection. Catalog presence is confirmed; quantities vary and order-time JLC assembly availability still needs checking.

These candidates required a new board revision rather than fitting them to the 0.0.4-dev lands. Revision 0.0.5-dev implements the changes below. Assembler solderability review and physical switch/button qualification remain pending.

## Implemented revision 0.0.5-dev

The native board now uses C&K recommended G-lead lands (1.25 × 2.10 mm at X=±3.875) and GCT USB4125 recommended copper/slots (1.10 × 1.70 mm copper; 0.60 × 1.20 mm slots). The USB contact row moves 0.20 mm while shell and mating-face positions stay fixed. A local joystick detour and USB 5 V route adjustment restore clearance without relaxing rules. The hierarchical schematics, local libraries, JLC overrides and DigiKey list use the new exact MPNs. Nominal envelope STEP models are explicitly drawing-derived, not manufacturer CAD.

The case now provides a measured switch-height parameter; see [self-assembly setup](SELF-ASSEMBLY.md#cost-and-button-setup). Physical switch travel and printed tolerances remain first-article measurements. The default USB stake length is 1.00 mm on a 1.60 mm PCB: it does not protrude through the opposite face. Have the assembler review insertion and solder fill in the placement/DFM preview; self-assembly needs inspection of the plated-slot joints.

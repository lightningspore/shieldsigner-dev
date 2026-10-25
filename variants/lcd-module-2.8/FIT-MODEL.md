# Full PCB assembly and case fit kit · 0.0.1-dev

The assembly contains the carrier and fitted SMT bodies, HOTHMI HTM-TFT028A16 SPI display, Luckfox Mini, both module mating headers, and four display spacers. It targets carrier 0.0.7-dev. Camera and ribbon are excluded from this PCB fit kit because their exact purchased dimensions are not established; the existing enclosure preview shows their assumed envelopes.

## Import into CAD

Download **shieldsigner-fit-kit.zip** from the website's 3D model section. Import `shieldsigner-pcb-fit.step` as **millimetres**. Import the `case/*.stl` files as millimetres at their existing origin: they are already positioned for assembly, not for printing. Disable automatic centering or dropping parts onto the ground. Move the whole PCB assembly as one body/group if trying a different case.

Origin: carrier XY centre, front component mounting plane Z=0; front is +Z, rear is −Z. Native KiCad STEP is translated by (−128, +89.579, −1.595) mm. The GLB files use standard glTF **metres**, with the same origin and orientation. They preserve separately selectable display, Luckfox, sockets, headers, spacers and carrier groups. `shieldsigner-case-fit.glb` adds the assembled printed case. Its shell is made transparent by the website viewer. STEP preserves full geometry but is a compound rather than an editable parametric PCB design.

## Nominal stack verified against exported geometry

| Interface | Geometry | Modeled fit |
| --- | --- | --- |
| LCD | 1×8, 2.54 mm pitch; 17.78 mm first-to-last pin span | 8.5 mm female socket, 6 mm male mating post; 5.04 mm insertion, 0.96 mm housing gap |
| Luckfox | Two 1×11 rows, 2.54 mm pitch; 25.40 mm pin span; 17.78 mm row spacing | 8.5 mm female sockets, 6 mm male mating posts; 6 mm insertion, housing faces touch |
| LCD support | Four 12 mm spacers; centres 82.5 × 47.8 mm | Carrier holes 2.7 mm; display holes 3.0 mm; modeled spacer body Ø5 mm |
| LCD module | 88 × 53.3 mm; drawing-derived envelope | Rear PCB plane Z=12 mm; front Z=17.70 mm; unused rear connector bottom Z=6.80 mm |
| Full PCB assembly | Carrier nominally 160 × 70 × 1.6 mm | Rearmost Luckfox feature Z=−17.82 mm; total height 35.52 mm |

The pin-centre audit checks every modeled header pin against its native PCB pad, with less than 0.001 mm modeled XY error. See `assembly-fit-check.json` for measured coordinates and source hashes. Run `mise run variant:lcd:stack` to repeat; `mise run variant:lcd:fit-model` regenerates the kit.

The Luckfox has 3.18 mm clearance to the **flat base inner floor**; the display front is 0.90 mm below the **flat front inner plane**. These plane comparisons do not describe every rib, boss or aperture. `mise run enclosure:fit` separately checks case/hardware collision geometry, reserving the upstream Luckfox's bounding envelope where its STEP surfaces are not closed solids.

## What still needs a physical check

Headers are generic KiCad models, **not verified purchase MPNs**. Choose straight 2.54 mm strips with 8.5 mm female body height, 2.54 mm male insulator, nominal 0.64 mm square posts and 6 mm exposed mating length. Verify the manufacturer's maximum insertion depth and contact engagement: modeled overlap does not prove an electrical contact or tolerance fit. The Luckfox stack assumes fully seated housing faces; a socket that cannot accept 6 mm will make it sit farther out.

The retained HOTHMI drawing (Rev 0-0, 2022-10-27, ±0.3 mm general tolerance) gives PCB 1.6 mm, front 4.1 mm, rear connector 5.2 mm: a conservative 10.9 mm total envelope. Product prose has also stated 7.7 mm. Measure the purchased display revision before relying on the shell clearance. The model is an envelope, not manufacturer production CAD.

Dry-fit the display on its four spacers and headers without forcing it down. Check Luckfox socket seating, solder tails/fillets, screw head clearance, rear connector, camera cable bends, USB/card access and print shrinkage. The first article remains the fit qualification; this model is intended to make that check possible before ordering multiples.

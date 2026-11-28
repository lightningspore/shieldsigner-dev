# Branding sources

`denver-space-source.webp` is the official monochrome **The Space** logo from
[denver.space](https://denver.space/assets/branding/Logos/TheSpace_Logos_Full_3.webp),
retrieved 2026-10-31. The Space retains ownership of its logo; this asset is not
relicensed as original ShieldSigner artwork.

`denver-space-silkscreen.svg` is the PCB-print adaptation. `mise run pcb:denver`
reproduces it from the hash-pinned source and adds native filled polygons plus
`denver.space` text to the main carrier's rear silkscreen. Sub-printable orbit
hairlines are removed at the 30 mm print width; the monochrome lettering and
main orbit remain. The PCB geometry is mirrored for normal reading from below.

[Branding metadata](../../hardware/branding.json) records the
source hash, conversion and placement. The
[independent artwork audit](../../hardware/branding-audit.json)
proves the non-silkscreen PCB data remains unchanged.

The existing ShieldSigner mark is repository-authored vector artwork. Its
concept and preview PNGs are design references; the SVG is the reusable mark.

## Front orbital field guide

`front-orbital-field-guide.svg` is the art-only vector plate for the large front
composition. Its typography is a portable SVG approximation; the native KiCad
stroke-font render in [`hardware/board-top.png`](../../hardware/board-top.png)
is the exact board preview. The existing ShieldSigner mark is reused directly.
Orbital linework draws on the project's space/navigation theme; it does not
replace or relicense The Space's attributed rear logo.

The native artwork is one selectable group, **Front / Orbital field guide**,
on `F.SilkS`. It combines the QR signing workflow, control markings and display
supply/assembly reminders. The QR finder drawings are symbols, not scannable
codes. The central art is visible during assembly and is covered by the display
in the finished device; the control markings and perimeter remain around it.

Rebuild a candidate with `mise run pcb:front-artwork`. The `-- --apply` option
requires the exact recorded predecessor (or identical installed artwork), then
runs protected-tree, aperture-clearance and native DRC gates before installation.
The generator uses the pinned predecessor's KiCad-extracted geometry so later
reference regeneration cannot accumulate or clip the artwork against itself.

[`docs/pcb-front-artwork.json`](../../docs/pcb-front-artwork.json) records the
delta; [`hardware/front-artwork-audit.json`](../../hardware/front-artwork-audit.json)
links it to the previous routing/socket audits. All original objects, rear art,
footprints, copper, mask/paste, outline, rules and fills are preserved. Added
strokes are at least 0.15 mm; artwork is kept 0.35 mm from front mask apertures
and reserves front component bodies, mounting hardware and existing text.
These checks do not qualify the supplier's printing process or physical hardware.

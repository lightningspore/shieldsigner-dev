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

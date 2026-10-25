# Printable PCB assembly fit mockup

Run `mise run variant:lcd:printable-fit` from the repository root.

Open **`dist/fit/shieldsigner-printable-fit-mm.stl`** in the slicer as millimetres. It represents the carrier, display, Luckfox, header stacks and display spacers at their current positions. It is a single connected outer body with watertight, consistently wound mesh geometry. The STL is approximately 1 MB, rather than the detailed 128 MB multi-body STEP assembly.

The fit mockup retains overall bounds approximately **159.86 × 70.13 × 35.52 mm**. It uses the same case coordinate frame as the STEP: carrier XY centre, front mounting plane Z=0, front +Z. STL has no unit metadata, so select mm. A slicer may automatically drop it onto the build plate; retain its original coordinates when comparing against the assembled case in CAD.

For just the carrier outline and holes, use **`dist/fit/shieldsigner-bare-pcb-mm.stl`**. It comes from the largest native carrier solid rather than a redrawn capsule.

This is a print-only approximation. The upstream Luckfox's open/doubled surfaces are replaced by a solid bounding envelope. Enclosed socket cavities are filled, and 2 mm vertical ties join floating modeled details to the carrier. Those artificial filled areas must not be treated as real electronics or available clearance for case features. Mounting holes crossed by ties may be blocked. Use the detailed assembly for local connector and fastener clearance work.

The full assembly has overhangs and needs a support strategy; mesh validity does not guarantee an easy FDM print. For checking only PCB position and mounts, the bare PCB STL is the simpler print. The tall header stack has not been reduced. The PCB electrical design and case geometry are unchanged.

`dist/fit/printable-fit-check.json` records source hashes, dimensions, mesh checks and output checksum. The task checksum-verifies the native GLB, refreshes group meshes, performs solid unions and re-imports the exported STL to check watertightness and connected outer-body count. Generated files live in ignored `dist/`; the script is the reproducible source. These new STLs are local outputs and are not in the earlier release-pinned fit-kit ZIP.

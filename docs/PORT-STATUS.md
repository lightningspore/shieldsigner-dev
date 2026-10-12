# Board status and why the tscircuit view looked incomplete

The native KiCad project is the preferred design. The tscircuit version is an experimental port of the current native board, with a recorded source SHA-256 and stale-source checks. Native checks have now run: zero ERC errors/warnings, zero active DRC errors/warnings and zero PCB unconnected items/parity issues, with two explicit DNP strap courtyard exceptions. See [native check details](../KICAD.md). Neither design is fabrication-approved.

| Observation | Cause / evidence | Handling |
|---|---|---|
| No routed copper in the dev server | The editable source preview renders TSX with routing disabled; copper is appended by `scripts/build.tsx`. | `mise run dev` now loads routed circuit JSON on port 3020. `dev:source` retains the unrouted TSX preview on port 3022. |
| Resistors, capacitors and switches look like ICs | The initial port rendered all 53 parts as generic `<chip>` symbols. | The component guide explains their real functions. Use the hierarchical native schematic for conventional symbols. |
| SW503 / U202 outside-board errors | Native renderer reports footprint bounding boxes outside the notched outline. A separate polygon containment check found all extracted pad polygons within the source outline using a 0.02 mm tolerance. | Expected errors were removed from compiled circuit JSON, not fixed geometrically. Build now preserves them in `dist/validation-report.json`; native mechanical/DRC review is still required. |
| Closed jumpers still appear electrically separate | Generic-chip ports and named nets do not encode the closed bridge or actual solder bridge copper. | Native KiCad retains the source footprint. Read default/alternative signal paths in HARDWARE.md. |
| Every LCD strap appears to be fitted | DNP metadata was initially omitted. | Metadata and generated BOM now retain J302, R404, R408 as DNP. Do not fit both members of either LCD strap pair. |
| “Unconnected” nets appear in the total | Duplicate physical lands need the same named group, including unused U202 pin 22. | 86 names include deliberately unused pins, not 86 useful application signals. |
| Too many apparent module pins | One physical pin can have a castellated land and through-hole, each given a unique port. | Use original KiCad pad number from the guide rather than assuming tscircuit pinN is a package pin number. |
| Missing bodies, labels and production details | Original silk, courtyards, models, stencil subdivisions and manufacturing settings were not fully ported. | Native KiCad is the appropriate source for those features. |
| U201 / TP201 in the schematic but absent from the PCB | Pinned rpi_interface sheet also contains a Waveshare interface symbol and test point absent from the 53-footprint PCB. | Do not silently invent their placement. Native ERC/DRC/netlist comparison must establish whether they are intentional schematic-only interfaces or source drift. |
| README and schematic disagree on LCD pinout orientation | Upstream README says not reversed; screen sheet note says reversed. | Resolve against the actual LCD drawing/cable before assembly. |

## What the automated port checks actually cover

- Component/net/track/via/fill counts, original pad positions and polygon vertices.
- Circuit JSON schema validity and existence of electrical source associations for imported copper.
- The native preview contains the expected component and SMT-pad counts.
- Default DNP references and opposite LCD strap endpoints.
- Complete explanatory coverage of all PCB component references.

These checks do not prove that appended copper reaches every required pad, has correct clearance, includes solder jumper bridge connections, uses a qualified stackup, meets a power budget or can be manufactured. Reference copper is appended after native renderer checks; manufacturing DRC is not run on that output by the tscircuit checks.

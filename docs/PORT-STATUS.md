# Native reference and experimental tscircuit status

The default repository preview follows the main **0.0.13-dev, four-layer KiCad board** in `kicad/` through `src/PillCarrierReference.tsx`. Current assembly data and audits live in `hardware/`; the main board has 73 footprints, 44 factory placements and nine Keystone service loops. Its native ERC/DRC/connectivity/parity checks permit zero exclusions. The independent source-authored tscircuit experiment below remains a separate layout; its explicit `tscircuit:pill:*` commands do not replace the fabrication reference. The historical FPC snapshot now reads `variants/standard-fpc/kicad/`.

The native KiCad project is the preferred design. The original tscircuit version is an experimental port of the standard FPC native board, with a recorded source SHA-256 and stale-source checks. The historical FPC board has recorded zero ERC errors/warnings, zero active DRC errors/warnings and zero unconnected/parity issues, with its two explicit DNP strap courtyard exceptions. See [native check details](../KICAD.md). Neither design is fabrication-approved.

## Independent source-authored experiment

`src/PillCarrier.tsx` is the explicit experimental pill entry. It is separate from the default native reference preview. It imports ordinary TSX circuit
blocks from `src/pill/sections/`, shared net names, reusable manufacturer
footprints, symbols, artwork and local GLB models. It has no runtime dependency
on KiCad files, extracted pad/net snapshots, imported tracks or patched Circuit
JSON. The normal `Circuit.renderUntilSettled()` result is written unchanged.

```sh
mise run tscircuit:pill:check
mise run tscircuit:pill:dev
```

The seven sheets cover USB power, Luckfox interface, controls, SEC1210,
smartcard socket, display and test points. Native resistor/capacitor/pushbutton/
connector/diode/LED/testpoint/solderjumper primitives carry electrical intent;
three chip elements represent the host module and two ICs. Copper-only test
pads/jumpers use `doNotPlace` to exclude them from component selection; their
lands and connectivity remain. Customer-fitted headers have no invented
manufacturer identity; the resulting part-selection warnings are retained. The core serializes
solder jumpers as `simple_chip`, despite their semantic source primitive.
The host module's PTH and castellated contacts are distinct physical ports
with explicit internal connections. Closed JP201/JP203/JP205 copper is part of
the reusable jumper footprint; their factory-connected net names are canonical
aliases. Changing strap modes requires changing those aliases and bridged flags
together. The separate standard FPC board's DNP exceptions are unchanged.

The 160×70 mm capsule, eight nonplated holes, native lands, component origins,
rotations and sides are retained. Both silkscreen layers use editable text and
native drawing primitives; only logos are small SVG assets. Typography uses the
tscircuit font. Footprints define solder mask, paste, fabrication and courtyards;
the SEC1210 stencil has four separate paste windows. Forty-two CAD placements
use thirteen reusable local GLB assets. Source provenance and retained licenses
are in `src/pill/provenance.json` and `src/pill/notices/`.

The built-in local pipeline routes new copper and recomputes ground pours;
this is a new layout, not a copy of the native tracks. Minimum trace width is
0.20 mm. A source-authored thermal ground via serves the QFN exposed pad.
Outputs in `dist/pill-native/` include unmodified Circuit JSON, two PCB views,
seven schematic views, build/schema reports, an independent native comparison,
and `ShieldSigner-pill-tscircuit-source.zip`. The ZIP builds without the native
project or generated reference data.

`tscircuit:pill:check` exercises source architecture, source freshness, netlist,
schematic placement, PCB placement, Gerber-derived shorts and PCB routing style.
An independent test compares all 190 lands to KiCad polygonization within
0.005 mm and compares complete electrical partitions in both directions to
catch missing connections and unintended shorts. KiCad is used only as a test
oracle. The regular repository `mise run check` also remains required.

The pinned core emits several fields incompatible with its `circuit-json` peer
schema (including numeric display offsets, string pin arrangements and null
optional group/board-artwork IDs). `schema-compatibility.json` records all such
findings. The check accepts only explicitly enumerated upstream field families;
it does not modify the emitted JSON or waive native circuit errors. U202 lacks
a native courtyard, so that renderer warning is retained. These are upstream
limitations, not a claim of strict whole-document schema validity.

Native KiCad remains the fabrication reference. Software checks do not qualify
physical fit, thermal behavior, supplier assembly, powered operation or this new
routing for manufacture.

## Earlier standard FPC reference port

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

## Native reference preview

The current 160×70 mm pill carrier has a separate entry point,
`src/PillCarrierReference.tsx`. The standard FPC entry point and generated reference remain
separate. Native KiCad and its local libraries remain the design authority.

```sh
mise run tscircuit:pill:reference:build
mise run tscircuit:pill:reference:check
mise run tscircuit:pill:reference:dev
```

Build regenerates `src/generated/pill-board.json` from
`kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb`, records
its SHA-256 and rejects stale data. Outputs are in `dist/pill-tscircuit/`:
Circuit JSON, top/bottom PCB SVGs, a generic-symbol connectivity schematic,
assembly BOM and validation report. Dev serves the routed JSON on port 3020.
The source-only entry point shows component placement without imported copper.

The original 0.0.9 port retained all 60 footprints, 56 named nets, 538 tracks, 234 vias,
14 zone polygons, one board copper graphic and three closed jumper copper
bridges (JP201/JP203/JP205). Closed jumpers also connect their two ports in the
electrical source model. The other three jumpers remain open. There are no DNP
footprints in this variant; optional J302 remains excluded from the factory BOM.
LCD header pinout and jumper defaults are checked independently of the renderer.
All eight nonplated board holes are present, including the two circles defined
inside the smartcard footprint. Capsule arcs use a 0.002 mm chord-error target.

The compiled Circuit JSON now includes:

- Front/rear silkscreen as 1,550 native BRep shapes, including the ShieldSigner
  marks, Space artwork, denver.space lettering, board text and visible component
  references. KiCad's font engine resolves glyphs, rotations and mirrored text;
  counter shapes in letters remain holes. Text and original editable geometry
  also remain in the native snapshot.
- All 420 native solder-mask openings and 111 paste apertures, including
  paste-only stencil subdivisions. Inferred tscircuit paste is replaced rather
  than mixed with the native apertures.
- Native per-component courtyard contours and both fabrication drawing layers.
  Plain PCB SVGs hide fabrication/courtyard overlays; the Circuit JSON and
  individual layer SVGs retain them for review. Native copper-only test pads
  and the Pico module still have no conventional closed courtyard; their
  remaining renderer warnings are preserved.
- All 48 visible native model instances, grouped into 42 component assemblies.
  GLB assets are embedded in Circuit JSON and also emitted under `models/`.
  Conversion preserves authored transforms, materials and the 1.6 mm board's
  top/bottom reference surfaces. The source STEP files, model provenance and
  licenses remain bundled. Some source models are documented nominal envelopes.

`layers/` contains individual SVGs for every extracted non-copper layer,
including comments and empty declared layers. `native-details.json` retains
text metadata, model instances, layer geometry and the source-item inventory.
`native-design.json` preserves the entire board syntax tree and project rules,
including the complete stackup, pad/zone settings and attributes that have no
Circuit JSON equivalent. `native/` is a hash-manifested snapshot of the complete
KiCad project and its local libraries. No source design information is discarded
because tscircuit lacks a corresponding setting.

The package also includes original-layer Gerbers, separate plated/nonplated
drills, native CPL coordinates, the existing supplier BOM/CPL and population
reference, all six native schematic sheet SVGs, and a native GLB assembly with
copper, mask and silkscreen. `shieldsigner-pill-tscircuit.zip` bundles those outputs
and the reproducible tscircuit source. The supplier reference retains its own
assembly/readiness caveats; a native diagnostic position CSV is not a replacement
for its compensated supplier CPL.

`tscircuit:pill:reference:check` compares every physical land to independent KiCad
polygonization (0.005 mm tolerance), checks artwork/aperture/model coverage and
schema validity, and raster-compares both silkscreen layers to KiCad's independent
SVG plotter at 3200-pixel width with a one-pixel boundary allowance. The check
rejects lost artwork rather than only checking element counts.

Placement checks use the compiled Circuit JSON: the build restores native
component layers after rendering already-projected pad geometry, avoiding a
second mirror. Source-only placement heuristics otherwise treat bottom-side
components as top-side. Native pill ERC/DRC, connectivity and schematic parity
pass with zero exclusions. The separate standard board retains its two documented
DNP exceptions.

Additional tscircuit checks cover netlist, schematic placement, compiled PCB
placement and default Gerber-derived shorts analysis on both copper layers. Use
the locally bundled analyzer to avoid an unnecessary CDN download:

```sh
TSCI_TEST_MODE=true mise exec -- bunx tsci check shorts dist/pill-tscircuit/shieldsigner-plus.circuit.json
```

The tscircuit PCB style audit flags ten inherited long tracks at non-45-degree
angles. Their exact endpoints are preserved and tested against native geometry.
Native DRC reports no clearance/connectivity violations for these tracks.

The tscircuit schematic remains a generic-symbol connectivity view; the native
hierarchical sheets are preserved separately, with their original symbols and
layout. The source-only TSX preview renders electrical components and placement;
use the compiled preview for imported copper, native artwork and models. Native
KiCad remains authoritative for fabrication and project rules. These software
checks do not establish physical fit, assembly quality or powered qualification.

The official `tscircuit/skill` was obtained before beginning this port:
https://github.com/tscircuit/skill. Existing upstream attribution and library
snapshots are retained.

## Four-layer native working revision

The pill reference extractor preserves In1.Cu/In2.Cu as inner1/inner2, four-layer through-vias and both ground planes. The separately routed source-authored `PillCarrier.tsx` remains its previous two-layer design. Released two-layer quote packages are historical; the working native project is authoritative.

## 0.0.11-dev service reference update

The native reference now contains 71 footprints, 56 named nets, 562 tracks and
240 vias. Eight Keystone 5015 factory SMT parts replace J302 and add service
access. Four independent M2.5 bracket holes supplement the original supports.
The converted reference retains both inner GND planes, 12 bare probe pads and
the original functional routing, with two standalone GND stitches removed.
The separately source-authored experimental layout remains the older two-layer
0.0.9 design; it must not be used for the current order kit.

## 0.0.13 native routing/header update

The main native carrier now has 73 footprints and a customer-fitted right-angle J302 under the LCD. All straight tracks use 45-degree increments; the SEC1210/socket and all existing pad nets remain unchanged. See [revision details and battery-module limits](PCB-ANGLE-HEADER-REVISION.md). The independent source-authored experiment remains historical.

# Native KiCad board

For the **current eight-pin pill**, start with [its project](variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pro) and `mise run variant:lcd:open`. Its complete workflow is at the end of this guide. The standard `kicad:*` tasks and reference discussion below target the separate original FPC carrier.

Open [the complete KiCad project](kicad/SeedSigner-Plus-smartcard-pico.kicad_pro). It includes the hierarchical schematic, routed PCB, project settings, and project-local symbol/footprint libraries. Native KiCad is now the preferred editor. The original tscircuit work remains for comparison.

## Use mise

```sh
mise install bun@1.2.21 uv@0.12.7
mise run kicad:setup
mise run kicad:open
mise run kicad:export
mise run kicad:check
mise run docs
mise run kicad:preview
```

The source requires KiCad 10. The existing installed KiCad 9 cannot open it. Setup caches the official KiCad **10.0.7** macOS image (~1.34 GB) in ignored `.tools/` and mounts it read-only. The wrapper mounts the cached image again when needed after restart. Your installed application is preserved. Alternatively set `KICAD_CLI` to the absolute path of your own KiCad 10 CLI. The open task launches the corresponding app. This cached setup is macOS-specific.

The project tasks deliberately disable auto-installing the parent monorepo's unrelated infrastructure tools. Bun and uv are pinned in `mise.toml`; `op` for Telegram remains supplied by the existing monorepo configuration. KiCad itself is managed by the project wrapper because the GUI/CLI bundle is distributed as a macOS disk image.

## What changed

See [native variant changelog](kicad/CHANGELOG.md). The working project starts from the pinned upstream PCB, preserving its geometry, routing, hierarchy, DNP settings and original drawings. Its complete local libraries now remove missing-library setup dependencies. This is a refinement of the upstream design, not a fresh autorouted layout.

Native fixes add explicit no-connect declarations, correct SEC1210 power-output pin types, annotate USB power entry, and declare the unused alternative header/testpoint as schematic-only. C603/C604 change from 100 nF to 1 µF to align nominal output decoupling with the [SEC1210 datasheet](https://www.microchip.com/content/dam/mchp/documents/UNG/ProductDocuments/DataSheets/00001561D.pdf), table 6-4 notes 6-2 and 6-3. The full [component guide](docs/COMPONENTS.md) reflects those changes and explains each part, selection rationale and pad/net usage.

## Native checks and remaining work

Current results from KiCad 10.0.7:

| Check | Result |
|---|---|
| Schematic ERC | 0 errors; 0 warnings |
| PCB connectivity | 0 unconnected items |
| Schematic/PCB parity | 0 issues |
| Layout DRC | 0 active errors; 0 warnings; 2 documented exclusions |

Native reports retain the two excluded courtyard findings with their comments. R403/R404 and R409/R408 are mutually exclusive mode straps sharing lands. R404 and R408 must remain DNP in the current variant. `docs/drc-assembly-exceptions.json` records the rationale, and `mise run kicad:check` fails if that population changes. No clearance or thermal-spoke limits were reduced. These exclusions are an explicit assembly decision, not physical separation of the alternate footprints.

Small placement changes separate C301/C302 and R607/C603 and shift the optional J302 header left. The selected XKB switch has its own native footprint identity and a 9.1 × 6.5 mm assembly envelope; all button centers remain fixed. Extended copper lands remain as inherited and need paste/reflow qualification. Decorative outlines that collided with labels/pads moved to fabrication layers; signal labels remain on silkscreen. The LCD connector mounting lands now have mask openings and paste apertures.

`mise run kicad:check` returns success for this documented default variant. DRC is a geometry/connectivity check; it does not establish module fit, effective capacitance, backlight current, assembly rotations or physical bring-up results. `mise run kicad:fab` reruns the gate and exports Gerbers/separate PTH/NPTH drill files under `dist/kicad/fabrication/`, plus a ZIP and hash manifest. Assembly is still subject to the qualifications listed in BOM.md.

## Review files

`mise run kicad:export` generates the hierarchical schematic PDF, native top/bottom PCB SVGs and XML netlist under `dist/kicad/`. The export command succeeds independently of DRC; a successful export is not a passed layout check. No production Gerbers are presented as approved manufacturing files.

The board bundle contains the native project, local libraries, rationale docs and review reports. It excludes Telegram account credentials and message history. All work remains in this project folder.

`mise run kicad:preview` serves the native review page at http://localhost:3021/board.html. This is a browser preview of native exports; editing takes place in the KiCad desktop application.

## Board-edge correction — 11 October 2026

U202 SMD pads 1/2 were shortened from 2.25 to 2.05 mm along their long axis; their local centers moved from −1.65 to −1.55 mm. This removes 0.20 mm from the outer end while keeping the inner edge unchanged. Pad height, module placement, PTH lands/drills, routing and board outline are unchanged. The project-local module footprint matches the edited board. KiCad zone fills were regenerated and saved.

The two edge-clearance violations and the adjacent starved thermal violation are absent from the updated DRC report. No manufacturing rules or minimum spoke counts were relaxed. At that stage, ten courtyard overlaps remained; the later completion work above resolves them or documents the two DNP exceptions. These shortened solder lands still require physical module/solder-joint qualification before manufacturing approval.

## Repeatable native editing

Use `mise run kicad:edit path/to/recipe.json`. The tool launches the pinned KiCad Python interpreter, snapshots the board/project, and applies named operations by reference or UUID. Move operations require an explicit `from` position so replay cannot shift a component twice. Recipes can also declare an expected board SHA-256.

Before installing a candidate, the tool reloads it, verifies the footprint count, runs native DRC against the same project rules/libraries, rejects newly introduced violations or broken connectivity, and checks original track net assignments. Any exception restores the original board bytes. Backups, recipes, candidate reports and hash audits are in ignored `.tools/pcb-edits/`. A deliberate overlapping-placement test was rejected with the working board SHA-256 unchanged; an idempotent reference-text edit passed.

Use the committed `docs/pcb-*-edits.json` files as the record of changes already applied, not a command to replay all edits. Save/reload checks may normalize native file ordering/metadata. The original source snapshots remain unchanged in `reference/`. `scripts/cleanup-schematic.py` preserves wire/junction/no-connect geometry while normalizing cached symbol overrides and ERC metadata. Avoid direct `LIB_ID` UTF8 methods and SWIG graphics Add/Remove loops; the tool uses the tested string setter and modifies existing graphics in place.

`mise run kicad:tools:check` repeats the accepted no-op, stale move and deliberately bad-placement integration checks, and confirms board/project bytes are preserved.

After an accepted edit, run `mise run kicad:check`, `mise run bom:generate`, and `mise run review:build`. The final parity check and manufacturing exports use the working project, not the candidate-only layout check.

Library paths use the exact tracked `Footprints/` capitalization. This prevents a case-insensitive Mac checkout from masking missing libraries in Linux checkouts.

## Eight-pin pill carrier

The [0.0.6-dev pill carrier](docs/LCD-MODULE-VARIANT.md) is an independent project under `variants/lcd-module-2.8/kicad/`. Use `mise run variant:lcd:open`. It follows the existing Luckfox eight-pin interface, keeps a 160×70 mm capsule and places a 2.8-inch module between the controls. A dedicated AP2112 supplies LCD_3V3. The obsolete bare-panel sheet/lands and Pico-format bay are removed.

`variant:lcd:check` runs native ERC/DRC/connectivity/parity with zero permitted exclusions. `variant:lcd:models` checks 22 model hashes, reviewed solder lands, exact connector mapping, capsule edges, supports and both-side hardware clearance. `variant:lcd:fab` builds 35-part/17-line matched Gerbers/drills/BOM/CPL. `variant:lcd:review` produces both assembled views, a complete schematic PDF and STEP/GLB exports. `variant:lcd:package` pins public release outputs. LCD/socket/support models are explicit dimensional envelopes.

Standard `kicad:*` tasks and the experimental tscircuit port still target the separate standard FPC carrier. Its two DNP courtyard exclusions do not apply to the pill PCB. Keep the two manufacturing sets separate.

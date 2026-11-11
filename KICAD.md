# Working with KiCad

The main design is [`kicad/SeedSigner-Plus-smartcard-pico.kicad_pro`](kicad/SeedSigner-Plus-smartcard-pico.kicad_pro): the **0.0.12-dev, four-layer, eight-pin display carrier**. Its inherited filename preserves schematic annotation paths. Supporting files live in [`hardware/`](hardware/README.md), including the [matched assembly data](hardware/manufacturing/README.md).

## Setup and open

```sh
mise install bun@1.2.21 uv@0.12.7
mise run kicad:setup
mise run kicad:open
```

The source requires KiCad 10. The wrapper caches the official **10.0.7** macOS image in ignored `.tools/` and mounts it read-only, preserving the installed application. The initial download is approximately 1.34 GB. On other setups, set `KICAD_CLI` to your KiCad 10 CLI. The cached disk-image workflow is macOS-specific.

All local symbols, footprints and models are kept with the project. Preserve the exact `Footprints/` capitalization for Linux compatibility. PDFs and STEP models use Git LFS; hydrate them with `git lfs pull` when needed.

## Validate and export

```sh
mise run hardware:check
mise run hardware:fab
mise run hardware:review
mise run hardware:package
```

`hardware:check` checks native ERC/DRC/connectivity/parity, local models and mechanical geometry, the recorded service/rear-placement edits, and module pinouts. The current board permits **zero DRC exclusions**.

`hardware:fab` creates a matched four-layer Gerber/drill/BOM/CPL set. `hardware:review` exports the complete schematic PDF, its front-page PNG, assembly renders and STEP/GLB files. The front-page render uses Poppler (`pdftoppm`; `brew install poppler` on macOS). `hardware:package` packages existing, matching exports. These generated outputs are under `dist/lcd-module-2.8/`; tracked assembly data is under `hardware/manufacturing/`.

`kicad:check`, `kicad:export` and `kicad:fab` also target the main native project. `kicad:fab` exports bare-board fabrication data; use `hardware:fab` for the matched assembly kit. Existing `variant:lcd:*` tasks remain compatible aliases for current-board tooling.

Passing software checks does not qualify physical fit, reflow, thermal operation or powered behavior. Supplier review and first-article measurements remain necessary; see [order readiness](docs/PCB-ORDER-READINESS.md).

## Editing workflow

Edit the native project first, then regenerate the experimental reference data:

```sh
mise run kicad:check
mise run generate
mise run build
mise run check
mise run tscircuit:pill:reference:check
```

For scripted edits, `mise run kicad:edit path/to/recipe.json` creates a backup and applies explicit reference/UUID edits through the pinned KiCad Python API. Move recipes require their original positions; a stale recipe must fail. Candidate checks reject newly introduced DRC/connectivity issues and preserve original pad/track nets. Backups and audit logs remain in ignored `.tools/pcb-edits/`.

The `docs/pcb-*-edits.json` files record edits already applied. Do not replay them blindly. Preserve project rules, local library snapshots, attribution and the upstream reference. After edits, regenerate the matched assembly files and review views, and check the resulting placement sides and rotations.

## Historical designs

The old **40-pin FPC carrier** is preserved in [`variants/standard-fpc/kicad/`](variants/standard-fpc/README.md). Run `mise run kicad:standard:check` for it. Its two documented DNP courtyard exceptions apply only to that design; R404 and R408 remain DNP. Its assembly data is separate from the main board's kit.

The [backlight PWM candidate](variants/lcd-backlight-pwm/README.md) is an optional experiment. Always-on backlight remains the main-board default.

`hardware/kicad` and the former `variants/lcd-module-2.8` directory are compatibility links. The single editable main project lives in `kicad/`.

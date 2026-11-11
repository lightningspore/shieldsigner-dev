# Contributing

Read [AGENTS.md](AGENTS.md), [KiCad workflow](KICAD.md) and [port status](docs/PORT-STATUS.md) before changing hardware.

Use mise tasks and uv-managed Python environments. Install JavaScript dependencies with `mise run setup`. Keep native KiCad as the reference design and preserve upstream attribution and project-local libraries.

For hardware edits, run `mise run hardware:check`, regenerate the native reference with `mise run build`, then run `mise run check` and `mise run tscircuit:pill:reference:check`. Regenerate the matched assembly exports and review views when placement, routing or population changes. Preserve the historical FPC board's documented DNP exceptions.

Document what was checked and distinguish software verification from supplier approval and physical first-article results. Current-board files belong in `kicad/` and `hardware/`; alternate designs belong in `variants/`.

Website content is generated from the source allowlist. Follow [website/README.md](website/README.md), edit original docs/templates, and run website checks plus desktop/mobile UI tests for UI changes.

Never commit credentials, Telegram sessions/history, Terraform state, private infrastructure configuration or OS build caches. Keep local outputs in ignored build/cache directories. PDFs and STEP models use Git LFS.

## Useful tasks

Run these from the repository root. `mise tasks` lists descriptions; `mise run tasks:check` checks task wiring without executing the workflows.

| Work | Commands |
|---|---|
| Main PCB | `kicad:open`, `hardware:check` |
| Assembly kit | `hardware:fab`, then `hardware:review`, then `hardware:package` |
| Native reference preview | `build`, then `check`, `tscircuit:pill:reference:check`; `dev` serves port 3020 |
| Datasheets | `datasheets:check`; `datasheets:fetch` downloads missing PDFs |
| Historical FPC board | `kicad:standard:check`, `bom:standard:generate`, `docs:standard` |
| Website | From `website/`: `setup`, `build`, `check`, `dev`; run `ui:test` against that running preview |

`variant:lcd:*` names remain hidden compatibility commands. Use `hardware:*` for repeatable main-board work. One-time board conversions and historical edit recipes are available explicitly but should not be replayed as routine cleanup. `camera:*`, `lvgl:*` and `firmware:*` cover the separate firmware work; device, remote build and deploy tasks require their documented environment. `check` is the tscircuit/source check, not a substitute for `hardware:check` or the website checks.

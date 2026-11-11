# Contributing

Read [AGENTS.md](AGENTS.md), [KiCad workflow](KICAD.md) and [port status](docs/PORT-STATUS.md) before changing hardware.

Use mise tasks and uv-managed Python environments. Install JavaScript dependencies with `mise run setup`. Keep native KiCad as the reference design and preserve upstream attribution and project-local libraries.

For hardware edits, run `mise run hardware:check`, regenerate the native reference with `mise run build`, then run `mise run check` and `mise run tscircuit:pill:reference:check`. Regenerate the matched assembly exports and review views when placement, routing or population changes. Preserve the historical FPC board's documented DNP exceptions.

Document what was checked and distinguish software verification from supplier approval and physical first-article results. Current-board files belong in `kicad/` and `hardware/`; alternate designs belong in `variants/`.

Website content is generated from the source allowlist. Follow [website/README.md](website/README.md), edit original docs/templates, and run website checks plus desktop/mobile UI tests for UI changes.

Never commit credentials, Telegram sessions/history, Terraform state, private infrastructure configuration or OS build caches. Keep local outputs in ignored build/cache directories. PDFs and STEP models use Git LFS.

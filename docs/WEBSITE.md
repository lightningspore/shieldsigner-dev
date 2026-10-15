# ShieldSigner website

The site at [shieldsigner.dev](https://shieldsigner.dev/) is a Django documentation and build guide for the public [design repository](https://github.com/lightningspore/shieldsigner-dev). It uses the LightningSpore project's Django/HTMX patterns. It has no accounts, wallet operations, seed inputs or database. Signing and card operations take place on the user's device.

## Where content lives

| Content | Authoritative source |
|---|---|
| Reference guides, including the header-LCD variant | Repository Markdown; explicit list in `website/knowledge/catalog.py` |
| PCB/parts/compile/flash/use/cards task pages | `docs/workflows.json` |
| Whole-device shopping list | `docs/system-parts.json` |
| Smartcard workflows | `docs/card-workflows.json` |
| Standard carrier table and readable passive values | Native BOM, `docs/jlc-catalog.json`, `scripts/part-values.py` |
| Module-variant drawings, native files and filtered carrier BOM | `variants/lcd-module-2.8/`; independent native files, model provenance, SMT population and quote kit |
| Supplier PDF references | `reference/pdfs/`, Git LFS, and `docs/pdf-references.json` |
| Site version | `website/version.json`; build adds Git revision and dirty status |

Edit the source files, then run content synchronization. Do not edit generated `website/content/` or `website/public/` copies. The packager uses allowlists rather than copying the entire repository. Private Telegram material, credentials, infrastructure state and OS caches must stay out of public content.

## Preview and check

From `website/`:

```sh
mise run setup
mise run content
mise run check
SHIELDSIGNER_PORT=8031 mise run dev
```

Open the local server printed by Django. Reference guides are at `/guides/`; the 2.8-inch variant is `/guides/lcd-module/`. Six task pages live under `/build/`. `/downloads/` offers separate modular and standard FPC carrier bundles, plus modular STEP/GLB assemblies. Each variant guide identifies its own files so a user does not combine unrelated BOMs and placement files.

With the preview running, use `UI_BASE_URL=http://127.0.0.1:8031 mise run ui:test` for desktop/mobile/no-JavaScript navigation and task checks. Response tests also load every allowlisted guide. Hardware edits need their own KiCad checks; a passing website test says nothing about electrical or manufacturing readiness.

## Version and publish

Use pre-1.0 development versions while the hardware remains unqualified. The visible version and Git revision identify the content build; a dirty marker indicates uncommitted inputs. `assets/modular-downloads.json` pins modular release asset hashes and the exact PCB hash. Content packaging rejects a changed board with stale modular order files; missing local artifacts are fetched from the pinned public release and verified.

Static CSS/JavaScript URLs include the revision to avoid retaining a previous site's assets through browser/Cloudflare caches.

The production route is Cloudflare HTTPS → dedicated outbound Tunnel → Caddy → Django/Gunicorn. The site uses a separate Compose project on the existing web host. Both apex and `www` serve the same site, with apex canonical metadata. All Cloudflare DNS remains in the existing shared DNS Terraform state in the private infrastructure repository. Public site sources contain no credentials or state.

After checks, `SHIELDSIGNER_DEPLOY_HOST=<authorized-ssh-host> mise run deploy` packages an allowlisted content-addressed release, builds the pinned image and updates the web/Caddy services after the origin health check. The tunnel connector is managed separately. `/healthz` reports version, revision and packaged content counts. Check public guide links and downloads after deployment. Retained immutable releases support rollback without a database migration.

For detailed local/operator procedures, see [website implementation notes](../website/README.md). This page describes the public architecture without providing account access.

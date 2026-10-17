# ShieldSigner website

The site at [shieldsigner.dev](https://shieldsigner.dev/) is a Django documentation and build guide for the public [design repository](https://github.com/lightningspore/shieldsigner-dev). It uses the LightningSpore project's Django/HTMX patterns. It has no accounts, wallet operations, seed inputs or database. Signing and card operations take place on the user's device.

## Where content lives

| Content | Authoritative source |
|---|---|
| Reference guides, including the header-LCD variant | Repository Markdown; explicit list in `website/knowledge/catalog.py` |
| PCB/parts/compile/flash/use/cards task pages | `docs/workflows.json` |
| Whole-device shopping list | `docs/system-parts.json` |
| Smartcard workflows | `docs/card-workflows.json` |
| Standard carrier table and readable passive values | Standard native BOM/catalog plus pill `manufacturing/bom-jlcpcb.csv` and `jlc-catalog.json`; `scripts/part-values.py` |
| Pill drawings, native files and matched carrier BOM | `variants/lcd-module-2.8/`; independent native files, model provenance, SMT population and quote kit |
| Supplier PDF references | `reference/pdfs/`, Git LFS, and `docs/pdf-references.json` |
| Site version | `website/version.json`; build adds Git revision and dirty status |

The PCB order and searchable shopping pages default to the eight-pin pill (35 pieces/17 lines). The shopping selector also exposes the separate standard FPC reference (43/21); it preserves the selected variant through searches and quantities. Pill system parts come from `variants/lcd-module-2.8/system-parts.json`.

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

CSS/JavaScript and the hero image use revisioned URLs; guide images and individual downloads carry content hashes. File responses require cache revalidation. This prevents an older board render surviving a design deployment in browser/Cloudflare caches.

The production route is Cloudflare HTTPS → dedicated outbound Tunnel → Caddy → Django/Gunicorn. The site uses a separate Compose project on the existing web host. Both apex and `www` serve the same site, with apex canonical metadata. All Cloudflare DNS remains in the existing shared DNS Terraform state in the private infrastructure repository. Public site sources contain no credentials or state.

After checks, `SHIELDSIGNER_DEPLOY_HOST=<authorized-ssh-host> mise run deploy` packages an allowlisted content-addressed release, builds the pinned image and updates the web/Caddy services after the origin health check. The tunnel connector is managed separately. `/healthz` reports version, revision and packaged content counts. Check public guide links and downloads after deployment. Retained immutable releases support rollback without a database migration.

For detailed local/operator procedures, see [website implementation notes](../website/README.md). This page describes the public architecture without providing account access.

## Printed enclosure and 3D viewer

The enclosure guide comes from `docs/ENCLOSURE.md`; printable geometry and checks live in `enclosure/`. Run `mise run enclosure:verify` to regenerate the portable print kit and its checks. Hardware mesh caches are generated from the native KiCad assembly with `enclosure/export_hardware.py` and `enclosure/color_hardware.py`; run them together with `mise run enclosure:hardware` after `mise run variant:lcd:review`. The native colored GLB is grouped into carrier, LCD, Luckfox, headers and supports for the exploded view.

`assets/enclosure-downloads.json` pins four assets to the separate `enclosure-preview-0.0.1-dev` release. The content builder verifies their checksums and the target PCB/SCAD hashes, and can fetch the pinned files in a fresh checkout. Enclosure downloads do not replace the 0.0.4-dev PCB order kit. Publish the matching assets before relying on a fresh checkout to build the site.

The viewer uses locally bundled Three.js 0.179.1 with its MIT license saved alongside the bundle. Edit `website/viewer/enclosure.js`, then run `mise run enclosure:viewer`. A small loader imports it on pages containing a viewer: the homepage and the enclosure guide. The homepage View 3D model button jumps directly to the interactive canvas. The viewer releases its WebGL resources during HTMX navigation; the tests exercise leaving and returning to the guide. Saved previews provide a static/no-JavaScript fallback. The ordinary response tests validate asset hashes and kit contents; `mise -C website run ui:enclosure` exercises both models, controls, responsive layout, HTMX lifecycle and no-JavaScript downloads.

## Upstream knowledge guides

The public knowledge base starts with `docs/START-HERE.md`, then `SOFTWARE-FEATURES.md`, `WALLET-BACKUPS.md` and `TROUBLESHOOTING.md`. These explain project boundaries, feature defaults, backup roles and diagnosis, while existing assembly guides remain the procedural source for this carrier.

Upstream citations pin full application commits. When updating firmware, review those guides against the new source, especially `settings_definition.py`, card applet support and platform-specific dependencies. README feature lists alone do not establish defaults or support on our image. Record the review date and keep documented software capability separate from the physical evidence in `BRINGUP-RESULTS.md`. Do not publish research caches or Telegram material through the content allowlist.

The practical public guides are `BUILD-TIPS.md`, `MULTISIG-PRACTICE.md` and `USEFUL-SOURCES.md`. Their public citations and prototype evidence are the publication basis; private review notes and source indexes are never copied by the content builder. Multisig acceptance tables describe proposed tests and remain explicitly unrun until results are recorded.

Deployment uploads use the remote account's disk-backed `.cache/shieldsigner-deploy/` directory, validate release identifiers before transfer, and remove the upload after a healthy deployment. Expanded release directories remain available for rollback. Avoid using `/tmp` for release archives: the website host may mount it as a small memory-backed filesystem.

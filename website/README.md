# ShieldSigner static website

ShieldSigner follows the **SeedPills static-site deployment pattern**: generated HTML,
CSS, JavaScript and downloads served directly by Caddy. Production contains no Python,
Django, Gunicorn, database or application server. The existing shared k3s website chart,
ECR repository and Cloudflare/Traefik route stay in place; routine releases do not change DNS.

## Build and preview

```sh
mise run setup
mise run build
mise run dev        # http://127.0.0.1:8030; rebuild after editing sources
mise run check
UI_BASE_URL=http://127.0.0.1:8030 mise run ui:test
UI_BASE_URL=http://127.0.0.1:8030 mise run ui:enclosure
```

Python, Jinja2 and Markdown are **build tools only**. `build` first synchronizes the
explicit public content allowlist, then renders `dist/`. The preview uses Python's
ordinary static-file server; Caddy serves the same document root in production.
Templates live in `templates/`, browser assets in `static/`, and guide/workflow sources
remain in the parent repository's `docs/`. Do not edit generated `content/`, `public/`
or `dist/` copies. All three directories and preview artifacts are ignored by Git.

`version.json` owns the visible development version. The build records the Git revision
and dirty-tree status. Release from a clean committed tree so the footer identifies the
deployed source. `package` checks the generated site, then creates a content-addressed
archive of the static document root and Caddy/container deployment files.

## Pages and interaction

- `/` links the six build/use tasks and the 3D model.
- `/build/<task>/` contains the PCB, parts, compile, flash, use and smartcard workflows.
- `/guides/` lists all guides. Browser-side search reads the generated, public-only
  `/static/guide-search.json`; it does not call a search backend.
- `/build/parts/` filters the two carrier variants and calculates quantities locally.
  Its pre-rendered templates preserve exact values, ratings and variant-specific BOMs.
  Query-string bookmarks remain supported with JavaScript.
- `/build/cards/seedkeeper/`, `/build/cards/satochip/` and `/build/cards/diy/` are actual
  static HTML pages. Old `?card=...` bookmarks redirect in the browser.
- `/costs/` shows a static pie chart of priced first-article items, explicit unquoted costs and quantity examples. It reads the reviewed BOM budget at build time; unknown costs have no chart slice.
- `/downloads/` and `/files/` provide reviewed, checksum-verified hardware sources,
  PDFs, matching fabrication kits and enclosure models.
- `/healthz` is a generated JSON file with hosting mode, version and source revision.

Without JavaScript, every guide and task remains readable, card tabs navigate to their
static pages, downloads work, and the complete pill parts list shows quantities for one
board. Filtering, computed multi-board quantities, guide search and WebGL need JavaScript;
the pages explain the fallback. Static model previews remain visible. Alpine retains the
mobile menu and browser-local checklists. Command copy and Three.js are browser-only.
Navigation uses normal document links; HTMX and server-side fragments have been removed.

## Public-file boundary

`scripts/sync-content.py` owns the guide and file allowlist. It verifies board, fabrication,
release and enclosure hashes before publishing. Fresh checkouts fetch missing release assets
from the pinned manifest URLs and verify their checksums. PDFs and STEP models use Git LFS.

Private Telegram/session data, credentials, infrastructure configuration, OS caches and local
cost-analysis outputs are excluded. The container build context accepts only `Dockerfile`,
`Caddyfile` and `dist/`. No repository crawler publishes arbitrary local files.

## Deploy and rollback

```sh
mise run deploy
```

This delegates to the neighboring `lightningspore-monorepo` helper at
`code/homelab/kubernetes/websites/deploy-shieldsigner.py`. It packages **this repository**,
builds/pushes an immutable linux/amd64 Caddy image, and waits for the existing Helm release.
Cluster credentials and hostnames remain in the private infrastructure repository. The
older electronics website source must not be used to rebuild the current site.

The production pod uses the same small static-service resource profile as SeedPills:
port 8080, non-root UID/GID 1000, read-only root filesystem, writable temporary data/config
volumes, no added capabilities, 16 MiB requested RAM and a 64 MiB limit. Caddy handles
compression, download headers, ordinary 404s and direct file serving.
The image removes Caddy's upstream low-port file capability because this service binds
unprivileged port 8080 and retains the existing drop-all-capabilities policy.

The infrastructure repository records the prior Helm revision/image for rollback. Rolling
back this migration requires restoring the complete previous Helm revision, including its
port/user/environment settings; the former Django image alone cannot use static-service
settings. The intentionally retained VM stack and tunnel have not been changed or stopped.
`deploy:vm` remains an optional explicit-host deployment path for newly packaged static
releases, using `Caddyfile.vm` for its edge proxy. Existing VM release directories retain
their original configuration.

## Verification

`check` tests every generated route, internal link and workflow anchor, canonical metadata,
public-file hashes/private boundaries, both order-kit populations and enclosure artifacts.
Desktop/mobile browser checks exercise BOM filtering/quantities, guide search, card pages,
checklist persistence, command copy, downloads, navigation and no-JavaScript access. The
enclosure suite loads both actual GLBs and exercises controls and static fallbacks.

Website checks do not qualify the physical hardware; the existing first-article limitations
remain part of the documentation.

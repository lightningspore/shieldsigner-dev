# ShieldSigner website

[shieldsigner.dev](https://shieldsigner.dev/) is a **static documentation site** for the
[public design repository](https://github.com/lightningspore/shieldsigner-dev). It follows
SeedPills' pattern: HTML and assets served directly by Caddy. No Python application,
Django, database, accounts or seed inputs run in production. Signing and card operations
take place on the user's device.

## Find the information

The homepage links six tasks: order the PCB, source parts, compile firmware, flash, use
SeedSigner and use smartcards. The [reference library](/guides/) includes component
rationale, smartcard compatibility, assembly, firmware builds and saved manufacturer PDFs.
The [downloads page](/downloads/) separates the pill and standard FPC carrier files.

The parts table defaults to separate system parts with JavaScript enabled. Select
Carrier/PCBA to inspect all passive values, ratings, exact references and quantities.
Switching carrier variants changes the underlying BOM rather than mixing their parts.
Quantity calculations support 1–100 boards; assembly CSVs remain per-board lists.

Search and filtering run in the browser. Without JavaScript the complete pill parts list
and all guides remain readable, quantities show one board, and CSVs can be downloaded.
Each smartcard workflow has its own static page, so card navigation works without scripts.
Old query-string card bookmarks redirect to those pages when JavaScript is enabled.

Checklists are stored locally in the browser. They are personal tracking, not hardware
qualification. The site does not receive checklist, wallet or smartcard data.

## Edit and preview

Edit authoritative documentation in `docs/`, workflow data in `docs/workflows.json`,
`docs/system-parts.json` and `docs/card-workflows.json`, templates in `website/templates/`,
and browser assets in `website/static/`. The guide catalog is an explicit allowlist.

```sh
mise -C website run setup
mise -C website run build
mise -C website run dev
mise -C website run check
UI_BASE_URL=http://127.0.0.1:8030 mise -C website run ui:test
UI_BASE_URL=http://127.0.0.1:8030 mise -C website run ui:enclosure
```

The build uses Python/Jinja2/Markdown and writes ordinary files under `website/dist/`.
These are build dependencies only. Production's image copies that directory into Caddy's
document root, like SeedPills. Rebuild after editing; generated copies are not source files.

## Downloads and models

The content builder checks the native board/readiness and published release hashes.
Missing exports can be fetched from pinned GitHub release assets in a fresh public
checkout. The pill has its own matched Gerbers/BOM/CPL, native KiCad kit, schematic PDF
and STEP/GLB; these do not replace the standard FPC files. Enclosure assets are separately
versioned and must target the matching carrier hash.

The 3D viewer uses locally bundled Three.js with its retained MIT license. Edit
`website/viewer/enclosure.js`, then run `mise run enclosure:viewer` from the repository root.
The homepage and enclosure guide load assembled/exploded GLB files directly. Normal page
navigation resets the viewer. Static previews and downloadable models provide the fallback.
Physical module/header/camera fit and powered bring-up remain unqualified by these renders.

## Hosting

Public HTTPS reaches the existing shared tunnel and website routing, then the static Caddy
service. The private infrastructure repository owns the shared DNS Terraform state, cluster
configuration and deployment credentials. This conversion does not create a second DNS
state or change the public routes.

The visible version and Git revision identify the website release independently of PCB,
enclosure and firmware versions. `/healthz` reports that metadata from a generated JSON
file. Deployment and rollback instructions are in `website/README.md` in the design repo.

Only reviewed, explicitly allowlisted sources are published. Private Telegram history,
sessions, credentials, infrastructure details, OS build caches and business-cost analysis
are excluded from the static document root and production image.

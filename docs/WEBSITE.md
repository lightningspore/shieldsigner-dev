# shieldsigner.dev website

The public knowledge site lives in [../website/](../website/README.md). It follows the Lightningspore
Django/HTMX approach and packages the original hardware documentation through an explicit allowlist.
Edit guides here, then run `mise run content` in `website/`; no second hand-maintained copy is needed.

Public site: https://shieldsigner.dev/ (apex canonical; both hostnames serve the site).
Local site: http://127.0.0.1:8030/.

DNS, zone import and the dedicated tunnel are in the existing shared `code/terraform/dns` state,
not a separate ShieldSigner state. The deployment runs as an isolated Compose project on the existing
Lightningspore website VM. See the website README for reproducible update, credential and rollback
commands. Terraform and site packages exclude private ingestion files and credentials.

The site publishes 14 guide pages plus an index, search, native board files, carrier Gerber review
outputs, BOM/CPL and nine saved supplier/manufacturer PDFs. It makes the remaining hardware testing
and UR2 image configuration caveats explicit. It does not publish Telegram messages or OS images.

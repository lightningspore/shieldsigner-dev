# ShieldSigner documentation website

Separate Django app following LightningSpore’s Django storefront: server-rendered templates, checked-in Markdown,
vendored HTMX/Alpine, normal links/forms with progressive enhancement, uv and mise. No database,
commerce, user accounts or secrets are needed for this read-only knowledge site. It shares the
Lightningspore website VM but uses a separate Compose project and dedicated Cloudflare tunnel.

## Work locally

```sh
mise run setup
mise run dev        # http://127.0.0.1:8030
mise run check
mise run ui:test
```

`content` syncs the explicit guide catalog and public file allowlist. Original hardware docs remain
in the parent project; edit them there, then run `mise run content`. Do not maintain duplicate guide
text by hand. The catalog includes the board/component rationale, electrical review, smartcards,
JLCPCB BOM, bring-up, cached Buildroot builds, tscircuit status and PDF index. Local private host
addresses are replaced in public guide copies. Telegram history, credentials, OS images/SDKs and
research caches are never crawled/copied. Production artifacts and public copies are ignored.

Design uses the LightningSpore dark/lime visual language and accessible server HTML. Small custom
CSS replaces the storefront's commerce-specific Tailwind classes here; there is no frontend build
chain. HTMX powers guide-search fragments and boosted navigation; Alpine controls the mobile menu.
Guides/search/download links also work without JavaScript. PDFs retain supplier ownership and the
original drawing; upstream attribution is visible on the homepage/footer and source links.

## Hosting and DNS ownership

All DNS lives in **the existing `code/terraform/dns` root and `state/dns` S3 backend**, as requested.
`cloudflare_shieldsigner_dev.tf` imports the already registered zone and owns the dedicated remotely
managed tunnel, its two ingress hostnames, apex/www proxied CNAME records and sensitive random bytes.
The provider/lockfile follow the existing Cloudflare v4 configuration. Registration and auto-renew
remain registrar settings, not Terraform resources.

From `code/terraform`, run:

```sh
mise run shieldsigner:plan
mise run shieldsigner:apply
mise run shieldsigner:install-token -- <ssh-host>
```

The wrapper retrieves the existing `Cloudflare Terraform` item from `spore-cloud` into process
memory. It never prints API or connector tokens. The saved plan and connector token are owner-only.
The shared state contains the tunnel credential and is stored in the existing encrypted S3 backend.

The initial full DNS plan found an unrelated update to `cname_webhook_timechain_win`. The
ShieldSigner-only bootstrap plan excludes that change and rejects destructive/out-of-scope actions.
Targeting is a bootstrap/isolated deployment measure: inspect the normal full `dns:plan` for future
shared-state maintenance. Do not apply unrelated drift just to launch this site.

## Deploy and update

Run checks/UI review, then `mise run deploy` from this directory. It builds a content-addressed
allowlisted archive, transfers it to `/opt/shieldsigner/releases/<hash>`, builds a locked production
image, starts only the ShieldSigner web/Caddy services and changes `/opt/shieldsigner/current` after
the origin health check. It does not restart the LightningSpore stack.

Production path: Cloudflare DNS/TLS → dedicated outbound Tunnel → `shieldsigner-caddy:80` →
Django/Gunicorn. Both hostnames serve the site; page metadata declares the apex canonical. Caddy applies security headers and health checks, and
uses loopback-only host port 8082 for smoke tests. There are no router forwards or public admin URLs.
Web is non-root/read-only with dropped capabilities and limits; the connector has a root-owned
owner-only token file mounted read-only and no added capabilities. One Gunicorn worker/two threads
keeps memory suitable for the existing small VM. Source/content ship in the immutable image.

Install the tunnel token using the Terraform wrapper, then start its connector from the current
release with the same `SHIELDSIGNER_RELEASE` and `--profile tunnel`. Inspect its logs for healthy
connections without printing the token file. Confirm public HTTPS, all guide links, search, PDF
and board downloads. This is a single home origin, not high availability.

Rollback uses a retained previous `/opt/shieldsigner/releases/<hash>` and its image: run Compose with
that hash, verify origin/public health, then repoint `current`. No database rollback is involved.
Preserve the dedicated tunnel and DNS records during content rollback.

## Validation

Django tests cover every guide, canonical metadata, full/fragment HTMX behavior, search and traversal/
private-file rejection. `ui:test` covers desktop/mobile navigation, search updates, no-JS fallback,
board image loading and overflow, with screenshots under ignored `artifacts/`.

This website presents a reviewed design and successful software builds. It deliberately does not
claim a manufactured/bench-tested signer: LCD qualification, reflow/paste, UR2 image configuration
and electrical/card bring-up remain pending.

For deployment from this public checkout, set `SHIELDSIGNER_DEPLOY_HOST` to your authorized SSH host. Cloudflare DNS Terraform and credentials remain in the private infrastructure repository; the public project contains no account access.

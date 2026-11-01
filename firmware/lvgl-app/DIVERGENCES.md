# Current divergences from upstream

[Overview](README.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Acceptance](docs/ACCEPTANCE.md)

The port keeps upstream wallet behavior while adapting startup, rendering and
resource ownership for the Luckfox. This is the current map; exact chronological
implementation notes and earlier acceptance limits are preserved in the
[divergence notebook](docs/history/DIVERGENCES-notebook.md).

## Pinned inputs

[sources.lock.json](sources.lock.json) is authoritative for full commit IDs.

| Input | Pinned commit prefix | Role |
|---|---|---|
| `3rdIteration/seedsigner` | `efdd1cfd14e8` | Original ShieldSigner application behavior |
| `kdmukai/seedsigner-lvgl-screens` | `33ddc0763c31` | Portable screen builders |
| `lvgl/lvgl` | `85aa60d18b3d` | Native widget/rendering library |
| `kdmukai/seedsigner-raspi-lvgl` | `1cb456500e6a` | Reference bindings |
| `kdmukAI-bot/seedsigner` | `fd9ba8fc766f` | Reference application |
| `kdmukAI-bot/seedsigner-language-packs` | `a9e39dabf60e` | Retained optional asset source |

Checkouts stay clean. Local portability patches apply to disposable build copies.
Reference inputs do not imply their entire runtime or hardware stack was adopted.

## Maintained changes

| Area | Intentional difference | Boundary / evidence |
|---|---|---|
| Frontend | Native C/C++ LVGL process, framed pipes and typed results replace PIL widget construction for supported screens | Python Controller/Views/models remain authoritative; [coverage](COVERAGE.md) records scoped paths |
| Display | 9,600-byte partial draw buffer and installed Rust LCD/frontend boundary | Physical UI confirmed; every screen/performance case is not globally qualified |
| Screen contracts | Bridges preserve class identity, argument initialization, scroll state, direct calls and result shapes | Source guards and host/hardware fixtures reject unsupported/mismatched paths |
| Keyboard/passphrase | Patches preserve KEY3 Save/top-nav behavior and exact passphrase bytes, including embedded NUL handling | Original Seed model owns normalization/derivation; passphrase is not generic trimmed text |
| Scaffold | Explicit list capacity raised from 32 to 128 | Fork Advanced menu needs 43 settings plus actions; order/index preserved |
| Camera/QR | Rust camera owner, preview transport and native ZXing-C++ QR reader feed the original decoder | Current image scanned on hardware; wallet payload acceptance remains scoped |
| Lifecycle | Explicit worker ownership, input delivery, camera transitions and cleanup | Public fixtures plus repeated-use receipts; no competing-owner force kill |
| Startup/dependencies | Lazy optional imports and release of disposable source/preview buffers | [Memory](docs/MEMORY.md); original algorithm/class structure is guarded |
| Bytecode | Checked-hash CPython 3.12 caches with fixed target filenames and a read-only launcher prefix | Stale-source fallback and packaging/cache tests; source remains present |
| Image integration | LVGL default supervised launcher with retained PIL rollback path and separate interactive settings | Frozen package/overlay/packed checks; user boot/UI/scan confirmation |
| Host layout | Shared paths under `dist/firmware` separate source/work/staging/images/checks | Layout cleanup preserves frozen bytes and source pins; legacy aliases retain old evidence paths |

Exact changes live in [patches/](patches/), [python/](python/), native host code,
[source guards](source-guards.json) and build/package helpers. Review patches and
guards together when changing upstream pins. Do not update guards merely to hide
an unexplained upstream or adaptation difference.

## Scope and unresolved questions

The active milestone is English and excludes smartcard feature work. Original
optional code may remain structurally preserved without that feature being
qualified in this port. No claim is made that all upstream workflows have passed
real-wallet acceptance; see [Acceptance](docs/ACCEPTANCE.md).

The notice audit preserves attribution and reports unresolved license closure:
the pinned screen core lacks a top-level license grant, the custom SeedSigner
icon font lacks embedded copyright/license records, and original OS/application
dependency notices need their own integration review. Retaining sources/notices
is not evidence those questions are resolved. See
[notice audit](validation/notice-audit-host.json) and the historical notebook.

For full decision history and exact receipts, read
[README notebook](docs/history/README-notebook.md) and
[divergence notebook](docs/history/DIVERGENCES-notebook.md). Historical entries
can describe intermediate gaps already addressed by later checkpoints.

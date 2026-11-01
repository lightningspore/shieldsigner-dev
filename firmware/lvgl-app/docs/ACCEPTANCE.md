# Acceptance and remaining work

[Overview](../README.md) · [Build](BUILD.md) · [Coverage](../COVERAGE.md)

Current image: **`lvgl-dev.cb6170a37a5a`**. The user flashed it and confirmed boot,
usable LVGL UI and camera decoding. Real-wallet end-to-end acceptance remains
pending because no wallet was available for that session. Production readiness
is not asserted.

The tested image is a **dev** image with **base-fork** I/O, automatic app startup
and **zram16-lzo** memory profile. Hardware observations used the standard
**240×240 display/button board**. They do not qualify the pill/2.8-inch carrier,
its display wiring, mechanical fit, or smartcard hardware.

| Evidence layer | Current result | What it establishes |
|---|---|---|
| Host unit tests | 245 pass after artifact relocation | Scoped contracts, guards and lifecycle regressions |
| Frozen runtime verification | 253 files, 5,469,515 payload bytes | Packaged bytes/native provenance/cache integrity |
| Frozen overlay verification | 256 files, 5,471,787 bytes | Inactive image-layer integrity and launcher/version checks |
| Packed image readback | Passed | Mini DTB, 12 MiB CMA, overlay/cache/launcher bytes and userspace smoke checks |
| Physical user session | Boot/UI/camera scan confirmed | These actions work on the tested board/image |
| Real-wallet acceptance | Pending | Full user wallet workflow still needs testing |

Packed ARM userspace checks include direct Python data/crypto, Rust LCD/frontend,
and LVGL menu/NUL-passphrase smoke tests. QEMU/readback cannot prove physical
buttons, optics, every wallet path, or indefinite stability. Hardware public
fixtures cover additional seed/transaction behavior without claiming real-wallet
or funds acceptance.

The [coverage inventory](../COVERAGE.md) records screen classes and scoped
receipts. It is not a percentage of production readiness. Earlier notebooks may
say a now-tested path was pending; later passing evidence supersedes that local
checkpoint without erasing its limits.

## Next useful acceptance session

1. Start from `firmware:where` and `firmware:verify`; record the exact image identity.
2. Exercise a disposable wallet: creation/import, passphrase entry and recovery,
   expected addresses/xpub and relevant QR formats.
3. Review a known public transaction fixture, verify change and export the signed
   result; independently compare expected outputs. A real-wallet session remains
   a separate user acceptance step.
4. Repeat camera/menu/QR transitions and check return-to-menu cleanup, settings
   persistence, shutdown and a fresh reboot.
5. Save a scoped receipt listing what was actually tested and any failures.

English is the active language scope. Smartcard development/testing is excluded
from this cleanup. Do not expand either scope merely to increase a feature count.
Notice/license closure also retains unresolved upstream provenance questions;
see [Divergences](../DIVERGENCES.md) and the retained notice audit.

## Primary receipts

- [Build](../validation/image-memory-cleanup-built.json)
- [Packed verification](../validation/image-memory-cleanup-packed.json)
- [Memory goal acceptance](../validation/memory-cleanup-acceptance.json)
- [Packaged wallet fixture](../validation/packaged-source-cache-wallet-arm.json)
- [Packaged entropy fixture](../validation/packaged-source-cache-entropy-arm.json)
- [Packaged settings fixture](../validation/packaged-source-cache-settings-arm.json)

Frozen payload manifests and `image.json` live in ignored artifact directories;
checked-in validation receipts preserve the historical evidence. The current
image directory's `acceptance.json` also records the user's observations and
pending real-wallet acceptance.

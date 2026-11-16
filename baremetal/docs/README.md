# Documentation

New readers should start with [status.md](status.md) and
[development.md](development.md).

## Overview

- [status.md](status.md): what works, what is excluded by design, known issues, next steps
- [development.md](development.md): toolchain, build/load/test loop, microSD images, porting rules, optical rig, safety rules
- [project-brief.md](project-brief.md): original mission, ground rules and phase plan with outcomes

## Hardware and runtime

- [hardware/cpu-base.md](hardware/cpu-base.md): MMU, caches, generic timer, GIC
- [hardware/camera-registers.md](hardware/camera-registers.md): SC3336, D-PHY, CSI and VICAP driver structure
- [hardware/camera-snapshots.md](hardware/camera-snapshots.md): reliable native camera snapshots
- [hardware/reference-isp.md](hardware/reference-isp.md): Linux ISP reference capture
- [hardware/usb-console.md](hardware/usb-console.md): DWC3 USB CDC console
- [hardware/mini-pcb-io.md](hardware/mini-pcb-io.md): Mini PCB LCD and buttons
- [hardware/reset-diagnostics.md](hardware/reset-diagnostics.md): reset records and watchdog

## Bring-up phases

- [bringup/milestones.md](bringup/milestones.md): scope after phase 9
- [bringup/phase-07-camera.md](bringup/phase-07-camera.md), [phase-08-isp.md](bringup/phase-08-isp.md), [phase-09-runtime.md](bringup/phase-09-runtime.md), [phase-10-boot.md](bringup/phase-10-boot.md), [phase-12-app-io.md](bringup/phase-12-app-io.md)
- [bringup/app-boot.md](bringup/app-boot.md): app autostart profile

## SeedSigner app port

Each page covers one ported subsystem: its upstream source, the reviewed
native boundaries and the gates that check it.

| Area | Pages |
| --- | --- |
| Inventory and core | [reference-inventory](app/reference-inventory.md), [app-core](app/app-core.md), [views](app/views.md), [settings-ui](app/settings-ui.md) |
| Crypto and text | [hash](app/hash.md), [secp256k1](app/secp256k1.md), [bip39](app/bip39.md), [unicode](app/unicode.md), [regex-unicode](app/regex-unicode.md) |
| Seeds | [seed](app/seed.md), [mnemonic](app/mnemonic.md), [mnemonic-entry](app/mnemonic-entry.md), [camera-seed-generation](app/camera-seed-generation.md), [backup-words](app/backup-words.md), [passphrase](app/passphrase.md), [passphrase-ui](app/passphrase-ui.md), [review-pages](app/review-pages.md) |
| QR | [scan](app/scan.md), [scan-overlay](app/scan-overlay.md), [qr-export](app/qr-export.md), [qr-confirmation](app/qr-confirmation.md), [animated-qr](app/animated-qr.md) |
| Bitcoin | [xpub-export](app/xpub-export.md), [psbt-framing](app/psbt-framing.md), [psbt-review](app/psbt-review.md) |

Component notes live next to their code: [app/README.md](../app/README.md),
[ui/README.md](../ui/README.md), [qr/README.md](../qr/README.md),
[patches/README.md](../patches/README.md) and
[tools/kernel-trace/README.md](../tools/kernel-trace/README.md).

## Engineering journal

[journal/](journal/) holds the chronological record: [history.md](journal/history.md)
(gate-by-gate log), [notes.md](journal/notes.md) (working notes and register
findings) and dated session handoffs. Each entry describes the state when it
was written; later entries supersede earlier ones.

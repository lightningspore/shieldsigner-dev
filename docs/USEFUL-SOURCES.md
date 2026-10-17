# Useful sources: where to verify an answer

Use primary documentation for the part, platform and software revision you actually have. This is a reviewed starting list, not an endorsement of every fork, release or linked product. Checked 2026-10-17.

| Source | Useful for | Scope |
|---|---|---|
| [Official SeedSigner](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/README.md) | Baseline signing model and original project | Official Raspberry Pi hardware instructions are not our Luckfox assembly guide |
| [ShieldSigner application](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/README.md) | Smartcards and added application features | Pinned to our application revision |
| [Hardware platform profiles](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/hardware_platform_support.md) | Display types, GPIO profiles and supported platforms | Match model and profile, not only screen size |
| [QR formats](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/qr_formats.md) | Recognizing wallet exports, transaction and seed payloads | Avoid exposing secret QR contents to online decoders |
| [Descriptor handling](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/multisig_descriptors.md) | Loading, using and clearing multisig policy | Application behavior at the pinned revision |
| [SeedSigner recovery](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/docs/recovery.md) | Script types, derivation paths and key encoding | Match network, account and any custom path |
| [BIP383](https://github.com/bitcoin/bips/blob/master/bip-0383.mediawiki) | Multisig descriptor threshold/key semantics | Specification, not a complete recovery procedure |
| [SeedKeeper applet guide](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/seedkeeper.md) | Persistent secret storage workflows | Card version, PIN and export policy matter |
| [Satochip guide](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/satochip.md) | On-card signing workflows | Distinct from SeedKeeper storage |
| [Bundled JavaCard applets](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/javacard_applets.md) | Applet identities and versions | Does not prove an arbitrary JavaCard is compatible |

For physical design, use the saved [manufacturer PDFs](PDF-REFERENCES.md), [current carrier BOM](../variants/lcd-module-2.8/manufacturing/BOM.md), and [electrical review](ELECTRICAL-REVIEW.md). For firmware provenance and reproducibility, use our [OS build record](OS-BUILD.md); the original project and fork use different platform build paths.

## Reading historical advice

Check date, hardware variant, release and whether a post describes a proposal, a patch, or a successful test. A pull request can be useful without being merged or present in your image. Stock, discounts and shipping estimates need a current supplier quotation. An old missing-feature report can become obsolete after a release.

Public guide additions cite public primary sources and project evidence. Community discussions help identify questions worth investigating; they are not substituted for measurements or a verified recovery test.

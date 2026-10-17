# Start here: what ShieldSigner is

ShieldSigner is an offline Bitcoin signing device. A separate wallet prepares a transaction; the signer reviews and signs its PSBT, then returns the signed data by QR. Your wallet broadcasts the transaction. The signer does not need a blockchain node or an Internet connection to sign.

This site documents a **prototype Luckfox Mini build** with a 2.8-inch eight-pin LCD, contact smartcard reader and printed enclosure. Digital design checks pass; physical assembly and electrical qualification remain pending. Start with the [test record](BRINGUP-RESULTS.md) before ordering.

## Which project does what?

| Project | Responsibility | What to use here |
|---|---|---|
| SeedSigner | Original Python Bitcoin signer and QR workflows | Learn the signing model; its Raspberry Pi hardware instructions are a different build |
| ShieldSigner application fork, `3rdIteration/seedsigner` | Adds smartcards and other tools to SeedSigner | Application pinned by our build wrapper |
| `3rdIteration/seedsigner-os` | Operating system and platform integration | Our pinned Luckfox Mini microSD build, using the vendor SDK/Buildroot path |
| `lightningspore/shieldsigner-dev`, this repository | Carrier PCB, enclosure, reproducible build wrappers and this website | Current eight-pin pill carrier files and guides |
| Older `seedsigner-luckfox-pico` work | Earlier hardware and porting history | Background; do not mix its board, display or image instructions into this carrier |

A Raspberry Pi image is not a Luckfox image. Luckfox models and flash targets also differ. Follow [Buildroot & firmware](OS-BUILD.md) and the [flash workflow](/build/flash/) for the selected Mini/microSD target and UR2 reader.

## Choose a path

- **Understand it first:** [Software features](SOFTWARE-FEATURES.md), then [wallet and backup concepts](WALLET-BACKUPS.md).
- **Build this hardware:** [Modular assembly](MODULAR-ASSEMBLY.md), [LCD interface](LCD-MODULE-VARIANT.md), then [enclosure and 3D viewer](ENCLOSURE.md).
- **Use existing hardware:** [Compile](/build/compile/), [flash](/build/flash/), then [first signing exercise](/build/use/).
- **Add a card:** [Card compatibility](SMARTCARDS.md) explains why SeedKeeper and Satochip serve different purposes. A card is optional for the ordinary in-memory signing workflow.
- **Something fails:** use [troubleshooting](TROUBLESHOOTING.md) to identify the failing layer before changing hardware or secrets.

## Versions describe different things

The website version is not the firmware version. The current modular PCB release is **0.0.5-dev** and enclosure preview is **0.0.2-dev**. Firmware identity comes from the exact OS and application commits, not those labels.

Our build wrapper pins OS `e7589465aff172f4f510ad46d18776ccc8d2c203` and application `efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f`. On a development device, `cat /etc/seedsigner-os-release` records the installed OS/application provenance. Compare it with the intended build before assuming a menu or feature is present.

## Sources and scope

Reviewed 2026-10-16: [official SeedSigner README](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/README.md), [ShieldSigner fork README](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/README.md), [fork repository map](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/repositories.md), and [platform support](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/hardware_platform_support.md). Links pin the reviewed revisions. The fork revision matches our application build pin; upstream documentation describes software support, not successful tests on our carrier. Our local build pins and hardware test record take precedence for this build.

For practical next steps, read [build tips](BUILD-TIPS.md), [multisig practice](MULTISIG-PRACTICE.md), and the [reviewed source list](USEFUL-SOURCES.md).

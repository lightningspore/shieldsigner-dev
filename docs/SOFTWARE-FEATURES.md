# Software features: what runs where

This build uses the ShieldSigner application fork of SeedSigner. The tables below describe the **pinned application's documented behavior**, not completed physical qualification of our carrier. Settings, installed dependencies and the selected hardware profile determine what appears and works.

## The normal Bitcoin signing workflow

1. Load or generate a seed on the signer. Ordinary SeedSigner operation holds the loaded seed in memory.
2. Export the wallet's public information to a coordinator wallet. This lets the coordinator construct transactions without receiving the seed.
3. Scan a PSBT, review its destination, amount, fee and change information, and sign only when they match your intent.
4. Return the signed transaction by QR to the coordinator for broadcast.

Single-signature and multisignature wallets need matching network, script and account information. A multisig wallet also needs its policy and cosigner information. Follow the [first-use workflow](/build/use/) with an unfunded test wallet before relying on a build.

SeedQR and CompactSeedQR accelerate seed entry; address verification helps check that a receive address belongs to the selected wallet. A SeedQR is a secret backup, not a public wallet export. [Backup concepts](WALLET-BACKUPS.md) explains the difference.

Source: [official application overview](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/README.md), [SeedQR formats](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/docs/seed_qr/README.md), [fork QR formats](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/qr_formats.md).

## Smartcards change where secrets live

| Card/backend | Role | Consequence |
|---|---|---|
| SeedKeeper | PIN-protected persistent storage of seeds and other secrets | Loading a seed brings it into signer memory; the host performs Bitcoin signing |
| Satochip | Key storage and signing inside the card | The application requests card signatures; importing a host-loaded seed still exposes it to the host during setup |
| Keycard | Separate card backend and compatibility layer | Disabled by default; requires its software support and compatible applet |
| Satodime | Bearer key-slot card operations | Not an ordinary PIN-protected SeedKeeper replacement; key unsealing has different consequences |
| Specter-DIY card | Separate mnemonic-storage backend | Disabled by default; requires its matching applet |

Our PCB has **contact transport only**. NFC or NDEF features in upstream software do not add an NFC radio to this board. A readable card or ATR does not establish that a compatible wallet applet is installed. See [exact reader and card requirements](SMARTCARDS.md).

Sources: [SeedKeeper](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/seedkeeper.md), [Satochip](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/satochip.md), [Keycard](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/keycard.md), [Satodime](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/satodime.md), [bundled applets](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/javacard_applets.md).

## Advanced features and fresh-settings defaults

These are defaults in the pinned source; an existing settings file can override them.

| Setting | Default | Purpose |
|---|---|---|
| BIP-85 child seeds | Enabled | Derive child seed backups from a parent and recorded derivation parameters |
| Smartcard support | Enabled | Expose supported card workflows; still requires a working reader stack |
| Satochip support | Enabled | Enable Satochip operations |
| SLIP-39 seeds | Disabled | Enable threshold-share seed workflows |
| Message signing | Disabled | Enable supported Bitcoin message-signing workflows |
| KeyCard support | Disabled | Enable the separate Keycard backend |
| Specter-DIY support | Disabled | Enable that card backend |
| Luckfox build tools | Disabled | Development functions; also require the corresponding OS tools |

Source of defaults: [settings definitions](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/src/seedsigner/models/settings_definition.py). BIP85 is under **Settings → Advanced**, then **Seed Options → BIP-85 child seed** after loading the parent. See [BIP85 upstream guide](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/bip85.md).

The fork also documents password generation, text QR tools, GPG tools, microSD operations and JavaCard applet installation. Treat these as separate advanced workflows with their own dependencies, backup requirements and destructive operations. A menu entry is not evidence that every tool is packaged or qualified on this Luckfox image. Start with the core signing/card path before adding them. Sources: [tool index](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/README.md), [GPG tools](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/gpg_tools.md), [microSD tools](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/microsd_tools.md).

## Offline operation versus development

Linux is the platform layer for camera/display drivers, Python libraries and PC/SC card services. The signing workflow uses QR transport; local PC/SC communication does not require Internet access. Development images, debug connections and networking need a separate threat assessment. Do not assume Raspberry Pi SD-removal behavior applies to this Luckfox image. See [OS build details](OS-BUILD.md) for the actual target and configuration.

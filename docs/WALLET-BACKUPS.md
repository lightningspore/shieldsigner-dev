# Wallets, secrets and backups

A signer, a backup and a coordinator wallet solve different problems. Before funding a wallet, practice restoring its backup and checking its fingerprint and receive addresses with the intended settings.

## Know what each item contains

| Item | What it is for | Is it a recovery backup? |
|---|---|---|
| Seed words | Secret input to wallet key derivation | Yes, with any required passphrase and wallet metadata |
| SeedQR / CompactSeedQR | Machine-readable representation of the seed | Yes; treat it like the words, with no automatic encryption |
| BIP39 passphrase | Additional input that selects a wallet | Needed when used; it is not the card PIN |
| SeedKeeper card | Persistent storage of secrets | Depends on what was saved and whether it can be read with its PIN |
| Satochip card | Persistent keys and on-card signing | Not a substitute for an independently tested recovery plan |
| xpub / descriptor | Public wallet derivation and policy information | Cannot reconstruct the secret seed; privacy-sensitive |
| Master fingerprint | Short wallet identifier | No; useful for comparison, not recovery |
| PSBT | Transaction data to review and sign | No |

Keep seed backups private. Public wallet exports can reveal addresses and transaction relationships even though they do not authorize spending. Never paste a real seed or seed QR into this website, an issue, or an online QR decoder.

Sources: [SeedQR encoding](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/docs/seed_qr/README.md), [recovery guidance](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/docs/recovery.md), [fork QR formats](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/qr_formats.md).

## Record the wallet configuration too

Keep the network, script type, account/derivation information, and whether a passphrase is required. Multisig recovery also needs the signing policy and cosigner public keys, normally captured in a descriptor or wallet configuration. A seed alone does not tell a coordinator every policy you previously used.

A passphrase mismatch can select a different wallet. When an address does not match, check passphrase, network, script, account and multisig descriptor before changing a backup. A loaded descriptor is application state: the fork provides **Tools → Clear Multisig Descriptor** when changing wallets.

Sources: [official recovery guide](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/docs/recovery.md), [fork multisig descriptor handling](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/multisig_descriptors.md).

## SeedKeeper is storage, not a second signer

Use **Seed Options → Backup seed → To SeedKeeper** to save a loaded seed, and **Seeds → Load a seed → From SeedKeeper** to load it. The pinned fork documents saving the BIP39 wordlist, master seed and passphrase together. Check what you actually saved: storing the passphrase beside the seed changes the separation your backup plan provides.

The card retains data after the signer powers down. The signer still receives a loaded seed and performs signing. PIN caching is off by default; enabling it retains the PIN for the session, with clearing on card change or restart. Keep an independent recovery plan; do not use factory reset or PIN guessing as troubleshooting.

SeedKeeper v0.2 stores a multisig descriptor as one entry; older v0.1 handling splits the template and xpubs. Card/app versions matter when transferring backups. Source: [SeedKeeper guide](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/seedkeeper.md), [descriptor storage](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/multisig_descriptors.md).

## BIP85 and SLIP39 need their own records

**BIP85** deterministically derives child seeds. Record the parent recovery information and exact derivation parameters, including application, word count and index. The same parent and parameters reproduce a child; an index by itself does not. Anyone with the parent can derive its children. A child backup does not recover its parent. Source: [BIP85 workflow](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/bip85.md).

**SLIP39** uses threshold shares and is disabled by default in this fork. Record the scheme and threshold/group arrangement and test the intended recovery workflow. Do not treat shares as ordinary BIP39 phrases or assume converting representations preserves an existing wallet. Source: [SLIP39 workflow](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/slip39.md).

Use the [first signing exercise](/build/use/) for a practical test, then consult [card workflows](/build/cards/) if persistent card storage is part of your plan.

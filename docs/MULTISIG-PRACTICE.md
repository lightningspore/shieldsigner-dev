# Practice multisig and missing-key recovery

A multisig wallet requires a threshold of distinct keys to authorize spending. A **2-of-3** wallet needs two of its three keys. This guide proposes a laboratory exercise with throwaway keys and a mutually supported test network. It does not select a funded custody arrangement or report completed tests on this prototype.

## Keys, devices and backups are different

| Item | Role |
|---|---|
| Three independent keys, A/B/C | The three cosigners in this exercise |
| Signing devices | Load keys or request card signatures; one device can handle multiple keys but shares its compromise risk across them |
| Coordinator wallet | Holds public wallet information, prepares transactions and broadcasts signed transactions |
| Wallet descriptor/configuration | Preserves policy and cosigner public information needed to reconstruct the wallet |
| Individual secret backups | Recover each cosigner, including its required passphrase |

Three cards are not automatically three independent signer implementations. SeedKeeper stores secrets that the host loads; Satochip signs on the card. See [card roles](SOFTWARE-FEATURES.md) before assigning them to a plan.

A descriptor specifies threshold and key expressions; `multi()` and `sortedmulti()` differ in how public-key ordering is handled. Preserve the actual exported policy instead of guessing it later. Source: [BIP383](https://github.com/bitcoin/bips/blob/master/bip-0383.mediawiki).

## 1. Record the test configuration

Choose a network, coordinator and script type that every selected signer supports. Use independently generated throwaway keys. Record these non-secret test fields:

- Coordinator version and signer OS/application commits.
- Network, script type, account/derivation paths and cosigner fingerprints.
- Whether passphrases are used, with recovery instructions kept separately from this record.
- Descriptor/configuration export format and any checksum.

Public wallet exports are privacy-sensitive. Keep the test record locally; this website has no wallet or seed upload flow. SeedSigner's [recovery reference](https://github.com/SeedSigner/seedsigner/blob/b2199c68b475eab0035b863b156f149757a1b4a6/docs/recovery.md) explains its path and public-key encoding conventions, including custom paths. A fingerprint is an identifier, not a backup.

## 2. Create and verify the practice wallet

Import the three public wallet keys into the coordinator and create the 2-of-3 practice wallet. Export its complete wallet configuration. Check several receive addresses using the signer's multisig address-verification workflow. Keep the descriptor/configuration alongside the test record.

The fork supports loading a multisig descriptor for address and change checks. It retains the loaded descriptor until cleared; use **Tools → Clear Multisig Descriptor** when switching wallets. Source: [pinned descriptor guide](https://github.com/3rdIteration/seedsigner/blob/efdd1cfd14e80a076a7e1ae91e9f2270ecbcd44f/docs/multisig_descriptors.md).

## 3. Exercise every signing pair

For separate test transactions, exercise **A+B**, **A+C** and **B+C**. Review the destination, amount, fee and change on the signer. Record the actual seed/card loading and QR formats used. A successful test of A+B alone does not exercise C or both remaining pair combinations.

Use the [first signing workflow](/build/use/) for the QR loop. Do not reuse the practice keys for savings.

## 4. Recover with a key unavailable

Recreate the coordinator from the saved wallet configuration in a separate test wallet. Compare multiple receive and change addresses with the original.

Then make A unavailable to the exercise and recover/sign with B+C. Repeat with B unavailable, then C unavailable. Preserve all original backups; simulate loss without deleting them. This tests the intended failure condition rather than rebuilding with all three secret keys available.

Do not plan to reconstruct missing cosigner public information from the remaining secrets. Keep the original policy/configuration and verify recovery in advance. [Wallet and backup concepts](WALLET-BACKUPS.md) explains what each backup preserves.

## Record results before choosing a real plan

| Check | Current project result |
|---|---|
| Export and fresh-coordinator import | Not run |
| Receive/change address agreement | Not run |
| A+B, A+C and B+C signing | Not run |
| Recovery with each key unavailable | Not run |
| Recovery instructions usable by the intended operator | Not run |
| Physical carrier qualification | See [hardware test record](BRINGUP-RESULTS.md) |

For a real arrangement, decide what failures must be tolerated, who can recover, where key backups and descriptor copies belong, and whether passphrases or hardware diversity add useful protection. Keep precise locations and secret material out of public documentation. More components also add recovery dependencies; test the procedure the actual recovery operator would follow.

Reviewed against the linked primary sources on 2026-10-17. The procedure and acceptance table are a proposed engineering test plan, not completed wallet operations.

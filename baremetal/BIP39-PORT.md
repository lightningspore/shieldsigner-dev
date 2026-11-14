# Native BIP39 leaf

The frozen `embit.bip39` and English 2048-word list are actual embit 0.8.0
source, matching the reference inventory. `baremetal:bip39:prepare` downloads the
hash-pinned source distribution and public vectors, preserves the MIT license,
and records each source/output hash. BIP39's const import goes directly to real
micropython.const, avoiding misc's unrelated eager curve-backend import. Type
annotations are removed. Package initialization exposes this real leaf only.

The original mnemonic-to-entropy, entropy-to-mnemonic, checksum, candidate-search
and full SHA512/2048 PBKDF2 algorithms remain intact. Callers own Unicode NFKD:
embit's original mnemonic_to_seed does not normalize strings internally. Native
Unicode normalization is supplied separately; this API does not apply the
SeedSigner Seed model's passphrase escape interpretation.

DUT1 RAM image9aac35e959dd54fff07c9970f029606db86f53544c40f91a4302eff714092f7a
passed all24published English vectors (entropy↔mnemonic, validity and64-byte seed),
five additional CPython/NFKD Unicode passphrase cases, invalid checksum/unknown
words and candidate lookup. Evidence: logs/phase-11/usb-20261114T231855.568015Z.
Native heap returned to baseline. Tests use public fixtures only. SHA256/512,
Unicode and UI regressions passed231905/231906/231908; original QR/scan loop
regression passed231935.44host tests passed.

The image's USB enumeration appeared after the loader gate's former20-second
observation window. Subsequent hardware API tests succeeded without reloading;
the observer now allows40seconds. This is transport/load observation, not a
cold-power benchmark. No SD, CAD or REF storage writes occurred.

This checkpoint does not port Seed, alternate seed types, secp256k1, derivation
paths, descriptors, signing, UR, or the full View/Controller routing. The generic
original QR classifier still needs the real Seed/SLIP39 dependencies. Optical QR
success also remains unproven. Do not use these primitive vectors as a wallet
qualification claim.

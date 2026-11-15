# Public curve fixtures and attribution

BIP32: Pieter Wuille, BSD-2-Clause as declared by the original document.
https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
The gate uses all published valid paths and invalid extended keys, preserving the
original keys exactly. Source SHA256 is pinned in app/secp-vectors-provenance.json.

BIP340: Pieter Wuille, Jonas Nick and Tim Ruffing; the specification declares
BSD-2-Clause licensing. The public CSV contains all19published rows:
https://github.com/bitcoin/bips/blob/master/bip-0340/test-vectors.csv
https://github.com/bitcoin/bips/blob/master/bip-0340.mediawiki
Its SHA256 is also pinned. These are public test keys/messages, not wallet data.

Original embit0.8.0 (Stepan Snigirev, MIT; app/LICENSE.embit) supplies the actual
host reference for additional public deterministic ECDSA/ECDH and Seed fingerprint
cases. Source/version and ctypes backend identity are checked during preparation.
BIP39 public vectors originate from Trezor's python-mnemonic corpus already pinned
by the BIP39/hash checkpoints. The gate does not derive expectations from the DUT.

libsecp256k1 is Bitcoin Core's actual implementation. Original MIT notice remains
unchanged in COPYING, and the exact upstream revision is pinned in source.json.

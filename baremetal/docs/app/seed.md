# Original Seed model on the native runtime

All original classes and methods from locked SeedSigner models/seed.py are
retained by tools/prepare_seed.py; app/seed-provenance.json records their hashes.
Copyright2021 SeedSigner, MIT notice app/LICENSE.SeedSigner. Type annotations
are removed, feature imports are deferred to actual modules, unavailable features
propagate explicitly before broad parse handlers, and logger calls are omitted.
Seed/Electrum passphrase methods use the REF-tested codec boundary while retaining
Electrum's own normalization. Other algorithms and class bodies are retained.

The native BIP39 Seed path now constructs the original model, checks wordlists,
normalizes mnemonic/passphrase, derives the full64-byte seed, exposes original
properties, compares seeds, regenerates after passphrase changes and disposes
fields. Native gate logs/phase-11/usb-20261114T232943.967070Z passed 24published
English vectors and 32REF passphrase→Seed derivations, uppercase normalization,
equality, optional regeneration, invalid checksum/unknown words, explicit missing
curve dependency and post-wipe wordlist usability.48host tests pass, including
all original class/method coverage. Class presence alone does not qualify Aezeed,
Electrum, SLIP39 or Xprv flows. Original bip85_supported metadata remains upstream
behavior; actual native curves/root fingerprints are now supplied by [secp256k1.md](secp256k1.md).
The BIP85 leaf and complete View workflows remain separate unfinished work.

The CPython ctypes/refcount secure_delete implementation cannot run unchanged.
The native boundary performs real volatile clearing only after both object and
data have sufficient GC HEAD allocations. It rejects views/unsupported types,
skips frozen/qstr/external storage, and preserves data lengths while invalidating
the current str/bytes object's cached hash. bytearray, heap bytes and UTF8 string
payloads are actually overwritten; Seed then drops its references as upstream.
Shared BIP39 wordlist contents and the shared list itself are protected. Public
frozen test constants are frozen with the image to exercise the real boundary;
REPL bytes literals are heap allocations and are not valid frozen-storage probes.
The first memory gate exposed that fixture mistake; the corrected gate passed.

MicroPython has no CPython refcounts. This internal API requires caller-owned
objects that will be discarded, including aliases. Never wipe dictionary keys;
mutating immutable buffers is destructive and aliases may have cached hashes.
Copies, hash/KDF temporaries, interned strings and previous buffers are not
promised erased. No complete secret-erasure or wallet security qualification is
claimed. Native gate logs/phase-11/usb-20261114T232932.219336Z proves bytes/bytearray/
UTF8 clearing, alias observation, all2048frozen words protected, frozen text/bytes
unchanged, rejection of memoryviews, and100neighbor-integrity/GC cycles.

DUT1 imageab515da0e3bb0dd59e8c2b45505a4fc8370103bcdb6dba5ae83aec0c0cde730f,
RAM load logs/phase-11/dut1-20261114T232910Z. Original QR/scan regression 233015 and passphrase regression 233016
passed; Home restored afterward. No storage/CAD changes. DUT0 is still idle on
the older Unicode image and needs a clean RAM reload before further tests because
the abandoned chr()-based fixture interned many characters.

Next integration gaps include original generic QR classification dependencies
(PSBT framing, SLIP39 wordlist, Aezeed checksum), full Seed/Controller/View routing,
curves and wallet operations, SD assets and actual optical QR qualification.

Current follow-up: [secp256k1.md](secp256k1.md) records actual native root/fingerprint gates; the
initial curve-unavailable gate described above was superseded by real key checks.

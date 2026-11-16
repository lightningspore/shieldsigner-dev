# Original mnemonic recognition and SLIP39 recovery

REF reports shamir-mnemonic 0.3.1, but its actual OS source is the SeedSigner fork
3rdIteration/python-shamir-mnemonic branch0.3-setuptools. The source archive is
pinned by the original OS package hash:
6fdcfb8d4380a8427ba28805eea63511a793fdfc6732d5c44d0f91a6b273445b.
The downloaded archive matches that pin. Its wordlist SHA256 matches a read-only
REF sha256sum exactly:
bcc4555340332d169718aed8bf31dd9d5248cb7da6e5d355140ef4f1e601eec3.
This is not a substitution of the differently published PyPI0.3.0 package.
MIT notices, including SatoshiLabs and Andrew R. Kozlik, remain with the source.

All original core, share, cipher, checksum, wordlist and recovery algorithms are
frozen. Type annotations are removed. File-backed wordlist loading now starts
from the actual frozen tuple; its original validation and index-map code remain.
Typed NamedTuple records use actual collections.namedtuple. Frozen dataclasses
use immutable namedtuple-backed subclasses with exact-class equality, tuple hash,
and mutation/deletion rejection. The native setattr hook and _asdict features
are enabled explicitly. Their representation is tuple-backed, so dataclass
introspection and exact repr/iteration API equivalence are not claimed. Public
record fields, constructors, equality/hash and immutability used by the algorithms
are tested. No Shamir interpolation, Feistel/KDF, threshold or checksum is replaced.

RecoveryState's defaultdict starts with pinned micropython-lib source. Mapping
operations, iteration, length and truth delegate to its real underlying dict;
this supplies the items() and empty-map behavior missing from that small upstream
implementation. Its general CPython defaultdict API is not claimed. replace()
uses the record's actual _asdict and original constructor with changed fields.
A minimal importlib.import_module resolves absolute/relative names through the
real builtin/frozen importer; it supplies no mock modules or host filesystem.

RANDOM_BYTES is deferred to an actual secrets.token_bytes provider. With no
qualified entropy provider present, generation requests raise FeatureUnavailable.
No predictable bytes replace entropy. Core combination/decryption uses the real
native SHA256 PBKDF2 routines. Native hash bounds still apply to extreme iteration
exponents; supported published vectors are checked separately. This does not
qualify an entropy source, share generation or the original Slip39Seed UI flow.

The whole locked original Aezeed source is also retained. Its CRC32C, word packing,
version and checksum checks run unchanged. The frozen record representation is
adapted as above. Blake2B and scrypt resolve actual providers or explicitly raise
FeatureUnavailable, including inside the original Seed exception paths; no fake
Aezeed decryptor is supplied. Full Aezeed decryption remains unfinished.

The native gate covers45 published SLIP39 recovery vectors, original RecoveryState
recovery/group prefixes, share round trips, stable record/set semantics and
mutation rejection. It also compares35 CRC32C cases against the whole original
CPython module; checks all five BIP39 word counts in mnemonic/four-letter/numeric
encodings; and preserves checksum-valid Aezeed versus ambiguous BIP39+Aezeed
classification. Fixtures are public and deterministic; the Aezeed checksum-only
samples are not claimed decryption vectors. This is injected-data testing, not
optical scanning or the full View/Controller workflow.

Use baremetal:mnemonic:prepare and baremetal:mnemonic:dut1:gate. Initial hardware
gates exposed missing defaultdict.items and disabled namedtuple._asdict; both
platform dependencies were corrected rather than bypassing recovery checks.
Console capture now stops early only after a traceback and observed REPL prompt,
retaining evidence. A plain observation timeout still does not stop computation.

The final record boundary also protects parameter records: a native probe showed
that subclassing a namedtuple could otherwise permit field mutation. Explicit
mutation/deletion guards and original _fields metadata now accompany those
classes; the full gate checks tuple equality/hash and attempted mutation. Both
BIP39 and SLIP39 shared wordlists are protected by disposal helpers.

Final image: 89da26d1f50b7e694deba68dbfe2d9ec2d0d0d64f355b6732679ec5d119e70cc,
DUT1 RAM load logs/phase-11/dut1-20261114T235301Z. Full recognition/recovery gate:
logs/phase-11/usb-20261114T235538.482395Z. All 45 published SLIP39 vectors pass,
including original RecoveryState and original generic QR classifier/share decoder.
The 26 BIP39 fixtures pass all three encodings; CRC/ambiguity and unavailable
entropy/decryption guards pass. Seed, both-wordlist clearing, PSBT and original
QR/scan-loop regressions pass; 52 host tests pass. Home restored at
logs/phase-11/usb-20261114T235607.170531Z; preview stopped, no console reader active.
Receipt: evidence/phase-12-mnemonic.json. No SD, CAD or REF storage changes.

The older QR regression's three-word "unknown public text" fixture consists of
actual BIP39 words. With the real dependency present, the original model now
recognizes its type and rejects its word count. The test expects that original
INVALID result; known missing UR/encryption dependencies still fail explicitly.
No catch was relaxed to hide an unavailable feature.

The build wrapper addresses makemanifest's inner timestamp shortcut, which only
checks .mpy freshness and can retain obsolete frozen QSTR enums after a correct
make dependency invocation. Only stale generated frozen C is invalidated when
QSTR headers or the manifest change. Pinned MicroPython source is preserved.
The observed duplicate _asdict enum error is resolved in the successful image.

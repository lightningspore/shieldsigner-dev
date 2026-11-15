# Original PSBT framing and parsing dependencies

The complete locked SeedSigner psbt_framing module now runs with actual pinned
embit0.8.0 source for base, compact integers, hashes, networks, Base58/Bech32,
script, transaction, EC/BIP32 models and PSBT parsing. Source/output hashes and
original MIT notices are retained. No reduced magic-prefix parser replaces it.
The original RejectCode and InvalidPSBTError classes are frozen as an error leaf;
the full PSBTParser review/signing policy is still unported.

Changes are platform boundaries: type annotations removed; MicroPython's actual
OrderedDict enabled; unsupported BytesIO.getbuffer length query replaced by
seek/tell/restore; unavailable dependencies propagate before broad parse handlers.
Regular parsing algorithms, strict rejection checks and returned models remain
upstream source. Existing QR log omission also covers the original compact-seed
branch's module-level logging call, which previously referenced an absent logger.

Only the secp256k1 import is deferred. An attribute request resolves the actual
backend described in SECP-PORT.md, or fails explicitly if a provider is absent;
it never returns a fabricated key/signature.
The original NUMS_PUBKEY initializer also needs a real curve parse, so module
__getattr__ computes and caches that exact original expression on first access.
This keeps parser imports lazy while actual curve operations use libsecp256k1.
Entropy follows the original source; with no os.urandom/filesystem provider,
requests fail rather than using a substitute RNG. None of these modules qualify
signing, entropy, EC/BIP32 operations or wallet review workflows.

The native gate compares the whole original checker + CPython embit0.8.0 reference
for15public synthetic cases: valid v0/v2 model round trips; duplicate map keys;
non-minimal key-length/type/value encodings; v2-only fields in each v0 map;
v0 transaction fields in v2; impossible map counts; count trailing bytes; extra
scope bytes; truncation and bad magic. A wrong-version or malformed result is the
original RejectCode, not a softened acceptance. The initial gate required explicit failure before a curve provider existed.
The current regression verifies actual generator/NUMS public keys (SECP-PORT.md). A12-word numeric SeedQR also passes the
actual original generic classifier/SeedQrDecoder, returns the published public
mnemonic and uses the real original Seed model for checksum classification.

Source prep: baremetal:embit:models:prepare and baremetal:psbt:framing:prepare.
Hardware gate: baremetal:psbt:framing:dut1:gate. The reference is complete original
code, not an independently rewritten equivalent. First parser-image regression
exposed the eager NUMS initialization; the corrected lazy expression is explicit
in provenance. This was an import dependency failure, not a failed curve result.

Generic text mnemonic classification still needs the actual SLIP39 wordlist;
24-word mnemonic ambiguity still needs the actual Aezeed checksum. Compact QR
ambiguity/encryption, UR, Controller/View routing, curves and actual printed-code
optical success remain separate work. Numeric injected-data success does not
establish optical scanning. No SD/CAD changes are involved.

Final DUT1 RAM image553bfe124eecf4292a11ea5c7e0f5aaccc432ced2069a499d900abec234bb9f9,
load logs/phase-11/dut1-20261114T233756Z; gate
logs/phase-11/usb-20261114T233824.657712Z. Seed233819, memory233825 and original
QR/scan233826 regressions pass. Home restored233827, camera off.50host tests pass.
Receipt: evidence/phase-12-psbt-framing.json. Shared build artifacts target DUT1;
DUT0 remains idle on the older Unicode image and needs a clean RAM reload before
its next test because of the earlier chr()-interning fixture. No console readers
remain active.

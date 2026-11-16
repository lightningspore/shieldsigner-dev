# Native original passphrase semantics

`seedsigner_port.passphrase.normalize_passphrase` is an explicit platform boundary
for the original SeedSigner Seed.set_passphrase codec expression. Source:
models/seed.py in the locked application; copyright2021 SeedSigner, MIT notice
in app/LICENSE.SeedSigner. The source guard and saved REF oracle identify it.

The original code doubles backslashes except those followed by lowercase u,
encodes raw_unicode_escape, decodes unicode_escape, restores the entire original
input on UnicodeDecodeError, then applies NFKD. The adapter implements that exact
result for UTF8 scalar strings without introducing a partial general-purpose
codecs or re.sub API. Literal uppercase U escapes, other escapes and trailing
backslashes stay literal; lowercase u requires exactly four hex digits. Unescaping
is one pass, including adjacent backslashes and escaped backslashes. Malformed
escapes restore the entire input before normalization, rather than a partially
decoded prefix. Existing Unicode characters retain their values before NFKD.

Valid lowercase-u surrogate escapes can produce strings on CPython that cannot
encode to the UTF8 needed by PBKDF2. The native boundary explicitly rejects these
with UnicodeError. It does not silently replace, combine or normalize surrogates
into a different seed. Malformed input still falls back as upstream does, even
if an earlier valid escape would have produced a surrogate. Normalization bounds
and missing general Unicode APIs are documented in [unicode.md](unicode.md).

Host tests compare10000generated edge cases plus fixed examples against the
original CPython codec expression, and515saved public REF cases. All 47 host tests
pass. REF oracle capture uses only stdlib with bytecode writes disabled; no app,
camera imports or storage modifications. Batches fit the reference ADB shell's
command limit; no stdin EOF or unsupported no-PTY transport is required.

Native DUT1 passed all 515REF cases,32 end-to-end passphrase→actual embit BIP39 seed
comparisons, native heap baseline and the24published BIP39 vector regression.
Gate: logs/phase-11/usb-20261114T232451.644096Z.
BIP39 regression: logs/phase-11/usb-20261114T232455.964820Z.
Home restored at logs/phase-11/usb-20261114T232458.620080Z, camera off.
RAM image60f75644f9cc78acb8cc716e6322d76bb3d051b9c3557fd7349dca0c37b92a89,
load logs/phase-11/dut1-20261114T232400Z passed the expanded observation window.

This is a tested dependency boundary, not the full original Seed model. Its
memory-clearing helpers depend on CPython ctypes/refcounts and still require a
real native policy/implementation; no erasure guarantee or fake wipe is supplied
here. Curve, root derivation, alternate seed types, full Controller/View routing
and optical QR qualification remain unfinished. No SD or CAD changes occurred.

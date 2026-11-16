# Original xpub derivation and static export

The original wallet helper bodies are frozen behind the same lazy native import
boundary as the other app models. The source commit and complete file/output
hashes are in `app/embit-utils-provenance.json`. Original derivation paths,
network/version selection, account xpub strings and receive/change address
calculations run on the existing native hashes and secp256k1 backend.
Function presence does not qualify descriptor handling or message signing.

MicroPython resolves a multiple-inheritance diamond depth-first. The original
StaticXpubQrEncoder therefore reached BaseQrEncoder's abstract methods instead
of BaseStaticQrEncoder's concrete methods. The generator materializes exactly
`cur_part`, `seq_len` and `is_complete` from BaseStatic on StaticXpub, preserving
the original CPython resolution and method bodies. Host source checks and native
public vector tests cover this compatibility change.

Original SeedOptions/export Views now have native xpub detail and static QR
screen facades. Details retain the source fingerprint/path/xpub, labels and Export
button. Static QR display uses the actual existing native qrcodegen/LVGL screen,
not the smaller transcription matrix helper. The byte payload travels as hex,
with a two-module quiet zone and a reviewed 512-byte limit. Original brightness
keys and in-memory setting updates use real native events. Any non-brightness
key exits, matching the source default behavior. `cancel_on_back=True` remains
explicitly unavailable because native exit events do not expose the exact key.

The original loading-screen calls draw the native loading spinner. They are a
foreground facade, not a Python thread: animation advances only when native UI
service runs. Screen replacement/blank releases its timer and widgets.

`mise run baremetal:app:xpub:prepare` generates independent CPython embit0.8.0
oracles. `baremetal:app:xpub:core:dut1:gate` checks 42 public combinations across
three networks, accounts0/7 and seven supported script/signature combinations.
It verifies static xpub payloads, original Specter fragment assembly/restart at
all three densities and single-signature receive/change addresses, including
Taproot. These are software/crypto math checks, not wallet security qualification.

`baremetal:app:xpub:dut1:gate` uses original Views, native key events and actual
framebuffer QR decoding. The static export routes to the original receive-address
verification prompt for singlesig and Home for multisig. The native gate stops at
the singlesig prompt; scanning/searching a coordinator's address is a later gate.
Detail Back, privacy warning and brightness persistence are also exercised.
Physical buttons, optical scanning and an external coordinator are not qualified.

Specter encoding is tested, but animated frame transport and UR dependencies
remain unported. The original format menus remain original; selecting an
unavailable provider raises an explicit development error. This stage does not
qualify animated export, custom/account-entry keyboards, wallet signing, entropy,
production security or persistent SD app boot. See the evidence receipt for
actual image, test and lifecycle results. The earlier unexplained reset stays open.

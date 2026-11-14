# Bare-metal QR decoder

The native app build links the same ZXing-C++3.1.1 decoder used by the Linux
camera path, pinned to commit287c85df6f961c8efbfb5ffd736cd9457b8b890e.
Upstream: <https://github.com/zxing-cpp/zxing-cpp>. Its Apache-2.0 license and
copyright notices stay with the cached sources in `.tools/zxing-cpp-3.1.1`.
`tools/build_qr.py` makes a disposable copy under `baremetal/build/qr`, disables
non-QR readers/writers and the unused thread link dependency, and uses automatic
scratch vectors in place of TLS. There is one foreground caller, no IRQ decoding.
Upstream binarization/detection/error correction/payload decoding are unchanged.
ZXing lazily retains immutable version/Reed-Solomon tables: the current gate
observed36616bytes on the first decode, then constant native heap across all
subsequent text/binary/rotation/inversion cases and ten repeat calls.
The compiler/toolchain and resulting archive hashes are recorded in its manifest.

`qr.decode(packed_luma,width,height)` returns raw payload bytes, or `None` for no
valid code. Dimensions are bounded to640x480 and length must match exactly.
Pass `frame[:640*480]` for a camera NV12 buffer. The C++ shim contains exceptions;
Python allocates the returned bytes only after the C++ stack has unwound. Payloads
are never printed by the decoder. Format interpretation/animated assembly belongs
to the original app DecodeQR model, which is not yet connected to this API.

`mise run baremetal:qr:prepare` regenerates public text/binary QR fixtures using
pinned qrcode8.2. `mise run baremetal:qr:gate` exercises exact bytes, rotation,
inversion, no-code and bounds on the real wired DUT0. This does not establish
optical scanning, original View routing or crypto/wallet correctness.

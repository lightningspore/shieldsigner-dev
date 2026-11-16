# Original standard and compact SeedQR export

The original `SeedQrEncoder` and `CompactSeedQrEncoder` now run on MicroPython.
All15original encoder classes are generated behind lazy imports; only the two
SeedQR encoders are qualified by this stage. Optional UR/xpub/PSBT providers still
fail explicitly when unavailable. Dataclass constructors are explicit, and compact
binary strings use a CPython-equivalent zero-padding helper.

QR matrices come from the pinned original **python-qrcode7.3.1** segmentation,
Reed–Solomon, placement and mask algorithms. Generated source hashes and original
BSD3-clause license are retained under `app/`. The port uses native PCRE2 through a
small binary-pattern facade, a lower-bound search adapter, standard native math,
and MicroPython's real two-argument `next` and class arithmetic dispatch. Indexed
integer arguments to `bytes.find` become equivalent single-byte values. Matrix
methods work; image/terminal backends raise explicit FeatureUnavailable. No PIL
image stub or different QR encoder replaces the original matrix algorithm.

The original format, privacy warning, overview, zoom and confirmation-prompt Views
use the existing native transcription builders. Both overview and zoom receive the
same original packed matrix, preventing differences in segmentation or mask when
hand-copying. Settings, Back/Done navigation and storage decisions remain original.
The helper bounds payloads to256 bytes and transcription templates to33 modules.
Other QR features or larger templates remain unqualified.

`mise run baremetal:app:seedqr:prepare` regenerates source/defaults and independent
public fixtures. Rebuild/load normal DUT1 app-ui, then run:

- `baremetal:app:seedqr:core:dut1:gate`:25 public cases compare exact payload bytes
  and every packed matrix module with **unmodified CPython qrcode7.3.1** plus
  embit0.8.0. Cases cover all five BIP39 lengths, standard/compact formats, NUL,
  final LF, high bytes, long numeric runs and odd alphanumeric segments. Actual
  native ZXing reads rendered modules, and the original seed decoder recovers
  each expected phrase. The measured 5.53 seconds is the whole core test workload,
  not startup time or a camera frame rate.
- `baremetal:app:seedqr:dut1:gate`: original Backup→format→warning→overview→zoom→
  confirmation prompt→Done→options→Home, with actual native key events. Public
  overview pixels are decoded from the real RGB565 renderer output; pan changes
  the zoom framebuffer. Back revisits format. Inactivity during a displayed QR
  exercises original cleanup and returns Home, whose pixels contain no QR.

These are known public test seeds and must never hold funds. QR payloads/matrices
are not logged by production helpers; public fixture data in test scripts is
explicitly public. Test seeds are removed, settings restored, and Home redrawn.
Memory wiping remains best effort; cleared seed-byte aliases and display pixels
are not evidence that every Python/C++ copy was erased.

This does **not** qualify optical camera focus/scanning, camera confirmation of a
handwritten QR, encrypted exports, other seed families, entropy generation,
transaction signing, SD app startup or a full wallet release. Development USB
access remains open. The earlier unexplained reset remains unresolved.

Follow-on: [QR-CONFIRMATION.md](qr-confirmation.md) records original confirmation
navigation with public pixel fixtures and the format-probe/input changes it needed.

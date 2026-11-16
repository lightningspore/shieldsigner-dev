# Original passphrase Views on native MicroPython

The original SeedAddPassphraseView, SeedReviewPassphraseView and
SeedAddPassphraseExitDialogView now use the actual native keyboard/review screens.
No wallet decisions are reimplemented in a fixture menu. Source View methods,
normalization, seed derivation, fingerprint comparison, finalization and history
remain the previously pinned original app code.

Reviewed screen defaults and keyboard label constants come from the original
seed_screens.py. `mise run baremetal:app:passphrase:prepare` regenerates them and
the public hardware gate's independent CPython embit fingerprint expectations.
The added screen mappings are compared with the existing Linux native adapter.
The display-only NUL/backslash mapping also matches that adapter: the underlying
value stays unchanged, while review displays distinguish NUL from a backslash.

The native event adapter snapshots the actual active textarea for both confirm
and Back. It uses the same existing nul_text shadow helper as the Linux native
host. Event bytes have an explicit length instead of strlen, preserving embedded
NUL and UTF-8. Confirm remains event kind2; Back uses kind6 with a true back flag.
The reviewed app adapter returns the original dictionaries: `passphrase`, with
`is_back_button=True` only for Back. A bare back index cannot silently discard
current input. New screen renders and event consumption clear the event buffer;
ordinary button/brightness results expose no stale text.

The existing255-byte native event bound remains. ASCII/UTF-8/NUL cases at the
bound return exact text. Oversized results raise explicitly; no prefix becomes
a passphrase. This is an implementation limit, not a BIP39 protocol limit. No
whole-memory erasure or entropy qualification is implied.

`mise run baremetal:app:passphrase:dut1:gate` proves these actual on-device paths
using only public abandon/about mnemonics and native key pulses:

- Enter `k`, confirm, compare actual before/after fingerprints, accept the review,
  finalize storage, open original seed options and return Home.
- Enter `k`, choose original Edit, preserve the entry, append `l`, review the new
  actual fingerprint, accept, finalize and return Home. Controller history unwinds
  without duplicating the finalized options destination.
- Enter `kl`, press actual Back, verify the original discard dialog sees the
  entire current entry, discard it, then finalize with the original empty
  passphrase fingerprint and return Home.
- Confirm an empty entry, choose the original skip action and finalize normally.

The gate also verifies exact confirm/back text for spaces, UTF-8 and embedded
NUL, and actual KEY1 case/KEY2 digit controls (`K6`). The keyboard intentionally
starts at the upstream central key `k`; the gate navigates its real layout rather
than injecting selected return values. Public test seeds are wiped/discarded.

Scope limits remain explicit: keyboard character inventory is the upstream
printable ASCII inventory. UTF-8 event transport and model normalization are
verified, but complete non-ASCII glyph rendering is not qualified. The existing
native review uses a fixed font/three-line layout; long passphrases can overflow
its visible region. Improving Unicode glyph coverage and long-text review is
still required before claiming a complete human-readable passphrase UI. These
tests also do not qualify optical QR acquisition, other wallet screens, full app
SD startup, randomness, side-channel behavior or whole-wallet security.

Follow-on: [REVIEW-PAGES.md](review-pages.md) records the later presentation pager
that exposes all long/hidden/non-ASCII character identities without requiring
universal glyph coverage. The former three-line overflow is avoided in the
original View's facade; raw low-level builders remain unchanged. An unexplained
runtime reset during expanded testing remains an open stability issue.

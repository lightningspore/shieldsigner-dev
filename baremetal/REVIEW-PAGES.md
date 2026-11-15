# Complete character review on the native display

The original SeedReviewPassphraseView still computes fingerprints and decides
Done/Edit/Scan/Back. Its native screen facade now supplies a presentation-only
pager when the old fixed-font review cannot reliably show the value. The model,
normalization, seed bytes and original action indices are unchanged.

Up to16 simple printable ASCII characters keep the existing native review.
Longer entries, spaces, backslashes, controls and non-ASCII characters use:

1. A legend explaining the representation.
2. Numbered character pages with explicit ranges and a Next button.
3. The original fingerprint/action screen, with a clear character-count summary
   instead of an overflowing or glyph-substituted passphrase label.

Pages use the existing real native button-list builder and embedded fixed-width
font, not a second software renderer. Up/Down scroll when necessary. Back on a
page moves to its predecessor; Back on the summary revisits the last page. Back
out of the legend returns the original Back result to the View. Done/Edit/Scan
return the original indices only after traversing the pages. Inactivity service
continues through the normal foreground poll.

Every ordinary visible ASCII character is kept, except backslash becomes `\\`.
Spaces are `\u0020`; NUL is `\u0000`. Other hidden/non-ASCII characters use
`\uXXXX` or `\UXXXXXXXX`. These are character identifiers, not UTF-8 byte dumps
or replacements for the model value. Literal backslashes are escaped so a
literal `\u0020` cannot be mistaken for a space. The first line of each page
identifies positions; line wrapping is presentation only. An escape never splits
across the intended lines/pages. At most24 display columns/four data lines per
page keep the fixed-width text within240px. Native pixel captures checked both a
full ASCII page and an emoji-identifier page without clipping.

Positions count Unicode scalar values in the original View's NFC display value,
not bytes or grapheme clusters. Seed derivation continues the original NFKD
behavior; no new normalization is introduced here. This supplies unambiguous
inspection for unsupported glyphs; it does not claim a universal font library.
The previous255-byte keyboard-event bound remains and errors explicitly.
Low-level direct C++ builder/ScreenSession calls are primitive rendering APIs;
the full paged behavior belongs to the original View's screen facade.

`mise run baremetal:app:review:prepare` prepares public fixtures using independent
CPython BIP39/PBKDF2/BIP32 fingerprints. `mise run baremetal:app:review:dut1:gate`
runs actual original Views, native page/key events and seed storage. It covers
180ASCII characters, mixed Unicode/NUL/space/backslash/newline, and63emoji;
backward/forward revisiting; original Back exit; actual inactivity wiping; and
20warm native rebuild cycles. The host independently decodes every displayed
page using Python's Unicode escape decoder and checks both the value and ranges.
Host unit tests also round-trip all1,112,064 valid Unicode scalar identities and
reject wrong/invisible/missing display receipts.

An unresolved runtime reset occurred before the added stress loop in one repeat
on the earlier accumulated runtime. DUT1 returned to maskrom with no fault text
in its USB transcript. A reload of the identical image and three subsequent
fresh/hot sequences passed, each including20stable-heap cycles; that does not
explain or close the reset. The evidence receipt records the failed run as well
as passing runs. More reset/fault diagnostics are needed before stability or
whole-wallet qualification. Optical QR and the remaining app/SD/entropy work
also remain open.

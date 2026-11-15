# Original manual BIP39 entry on the native runtime

The reviewed `SeedMnemonicEntryScreen` facade now uses the pinned native
`seed_mnemonic_entry_screen` builder. The original `SeedsMenuView`, `LoadSeedView`,
`SeedMnemonicEntryView`, checksum-error View and finalization Views keep their
navigation and storage decisions. The screen receives the actual selected
wordlist and saved initial letters; its text result is the chosen word. Back
remains the original navigation code. Other screen event kinds fail explicitly.

In hardware mode, the joystick chooses/commits letters. KEY1 and KEY3 scroll the
visible candidates; KEY2 accepts the highlighted word. Up from the first keyboard
row focuses Back. Candidate acceptance requires at least two visible prefix
letters. Existing words reopen with their letters preserved; DEL edits them.
These are behaviors of the existing pinned native screen, not new Python typing
or candidate-selection logic. Known native-library differences from the original
PIL keyboard remain documented in that library; this integration does not claim
pixel or interaction identity with the PIL screen.

Run `mise run baremetal:app:mnemonic:prepare`, rebuild/load the normal DUT1 app-ui
image, then `mise run baremetal:app:mnemonic:dut1:gate`. The generator uses pinned
CPython embit0.8.0 to derive independent public zero-entropy phrases/fingerprints.
The device gate sends native key pulses, never chosen text or View return values.
It exercises fresh entry, candidate scrolling, deletion, saved-word reopening,
checksum rejection, correction, cancellation, real key derivation and cleanup.
Only public test seeds are used and discarded. These fixtures must never hold
funds. Numeric reset snapshots are checked during each original app flow.

This is the English BIP39 entry boundary. It does not qualify entropy generation,
Electrum/Aezeed/SLIP39 entry, optical QR scanning, seed-word backup display/tests,
transaction signing or a full wallet release. Availability of those frozen Views
is not evidence that their screens/providers work. USB development access remains
open and the app is still RAM-loaded rather than automatically launched from SD.

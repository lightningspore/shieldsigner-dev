# Seed-word backup review and verification

The native screen adapter supports the original `SeedWordsScreen` and
`SeedWordsBackupTestPromptScreen`. It passes exact word slices to the existing
numbered-word builder, with an explicit four-word page offset. The original
privacy warning, backup menu, word Views, review/skip prompt, quiz, retry and
success Views continue to make navigation/storage decisions. The prompt preserves
its original explanation and disables top-nav Back, as its original post-init did.
No generic confirmation screen stands in for word review.

One original View bug is corrected in the generation step: `SeedWordsView` now
rounds the page count up. Rounding down omitted the trailing words of15/18/21-word
phrases. The guarded AST change is recorded in `app/views-provenance.json`; the
pinned upstream source remains intact. Final partial pages keep their actual word
count and explicit numbering offset rather than multiplying by that smaller count.
The existing native screen's compressed row spacing/warning border remain in use.

The seed Views' `random` import binds to `quiz_random`, which uses the pinned
MicroPython Yasmarang pseudorandom generator for question/distractor ordering and
Fisher-Yates shuffle with rejection sampling. It starts with a **predictable clock
seed**; this is not wallet entropy. Integer seeds repeat on this runtime but do
not reproduce CPython's Mersenne Twister sequence. Hardware entropy health and
`secrets` APIs remain unqualified/unavailable. Keys/nonces/seeds must not use this
quiz helper. No wallet entropy qualification follows from permutation tests.

Use `mise run baremetal:app:backup:prepare`, rebuild/load normal DUT1 app-ui, then
`mise run baremetal:app:backup:dut1:gate`. Public fixtures derive from incrementing
entropy bytes under independent CPython embit0.8.0. The device test sends actual
native key pulses through the original Controller/Views. It checks every page,
word slice, number offset, Back/review routes, wrong-answer retry, complete quiz,
and both stored-seed and pending-seed finalization behavior. Public test seeds are
removed afterward. These fixtures are unsuitable for funds.

This stage does not qualify other seed families, BIP85 backup, SeedQR export,
entropy generation, optical QR scanning, transaction signing or a full wallet
release. Inactivity cleanup and development USB access retain their existing
policies. Memory wiping remains best effort; screen rebuilds are not proof that
every copy of private data has been erased.

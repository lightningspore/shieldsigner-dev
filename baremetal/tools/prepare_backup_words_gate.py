# SPDX-License-Identifier: MIT
"""Independent CPython oracle of public backup phrases and root fingerprints."""

import pyformat  # noqa: F401  (formats generated Python on write)
from pathlib import Path
import re
from embit import bip39, bip32

path = Path(__file__).resolve().parents[1] / 'micropython/backup_words_gate.py'
fixtures = []
for count in (12, 15, 18, 21, 24):
    words = bip39.mnemonic_from_bytes(bytes(range(count * 4 // 3))).split()
    assert len(words) == count
    root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(words)))
    fixtures.append((words, root.my_fingerprint.hex()))
code, n = pyformat.subn_assignment(
    'fixtures',
    'fixtures = ' + repr(fixtures) + ' # PUBLIC CPython embit0.8.0 oracle.',
    path.read_text(),
    flags=re.M,
)
assert n == 1
path.write_text(code)
print('Prepared public backup lengths:', [len(f[0]) for f in fixtures])

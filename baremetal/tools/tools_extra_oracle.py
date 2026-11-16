# SPDX-License-Identifier: MIT
"""Host oracle for micropython/tools_extra_gate.py, from upstream SeedSigner code.

Uses the pinned upstream helpers/password_generation.py, EFF wordlists and
embit bip85/bip39 with the PUBLIC seed abandon x11 about (BIP85 index 0), and
the gate's scripted dice faces. Prints the ORACLE dict the gate embeds.

  uv run --python 3.13 --with embit --with pycryptodomex python baremetal/tools/tools_extra_oracle.py
"""

import hashlib, importlib.util, math
from pathlib import Path
from embit import bip32, bip39, bip85
from embit.wordlists.bip39 import WORDLIST

repo = Path(__file__).resolve().parents[2]
src = repo / 'dist/firmware/sources/lvgl/application/src/seedsigner'
spec = importlib.util.spec_from_file_location('pg', src / 'helpers/password_generation.py')
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)


def eff(name):
    return dict(
        l.split('\t', 1)
        for l in (src / 'resources/diceware' / name).read_text().splitlines()
        if l.strip()
    )


root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(['abandon'] * 11 + ['about'])))
length = lambda bits, alpha: max(1, math.ceil(bits / math.log2(alpha)))


def bip39_words(seed, count):
    data = pg.shake_stream(seed).read(math.ceil(count * 11 / 8))
    bits = ''.join(f'{b:08b}' for b in data)
    return [WORDLIST[int(bits[i * 11 : (i + 1) * 11], 2)] for i in range(count)]


faces = ''.join(str((i * 7 + i // 3) % 6 + 1) for i in range(50))  # gate dice() pattern
o = {}
o['pw-dice-hex'] = pg.hex_password_from_seed(
    hashlib.sha256(faces.encode()).digest(), length(128, 16)
)
o['pw-bip85-hex'] = pg.bip85_hex_password(
    bip85.derive_entropy(root, 128169, [length(128, 256), 0]), length(128, 256)
)
words = math.ceil(64 / math.log2(7776))
rolls = pg.dice_rolls_from_seed(bip85.derive_entropy(root, 89101, [6, words * 5, 0]), 6, words * 5)
m = eff('eff_large_wordlist.txt')
o['pw-bip85-eff-long'] = ' '.join(m[rolls[i : i + 5]] for i in range(0, len(rolls), 5))
o['pw-bip85-base85'] = pg.bip85_base85_password(
    bip85.derive_entropy(root, 707785, [length(128, 85), 0]), length(128, 85)
)
count = math.ceil(128 / 11)
o['pw-bip85-bip39'] = '.'.join(
    bip39_words(bip85.derive_entropy(root, 89101, [2048, count, 0]), count)
)
o['pw-bip85-dicerolls'] = ','.join(
    str(v)
    for v in pg.dice_roll_values_from_seed(bip85.derive_entropy(root, 89101, [20, 8, 0]), 20, 8, 0)
)
print('ORACLE=%r' % o)

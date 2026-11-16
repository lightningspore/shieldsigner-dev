# SPDX-License-Identifier: MIT
"""Generate native tests from a saved read-only REF oracle of original Seed codecs."""

import pyformat  # noqa: F401  (formats generated Python on write)
import hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = root / 'unicode/passphrase-ref-oracle.json'
d = json.loads(p.read_text())
assert d['refPython'] == '3.12.10' and d['unicodeVersion'] == '15.0.0'
assert (
    d['sourceSeedSha256']
    == json.loads((root.parent / 'firmware/lvgl-app/source-guards.json').read_text())[
        'models/seed.py'
    ]
)
code = '''# Public fixtures, saved REF oracle; not private passphrases.
from seedsigner_port.passphrase import normalize_passphrase
import camera
import gc
baseline=camera.settings()['rust_heap_bytes']
'''
for row in d['cases']:
    if row['utf8']:
        code += f"assert normalize_passphrase({row['input']!r})=={row['expected']!r}\n"
    else:
        code += f"try:\n    normalize_passphrase({row['input']!r})\n    assert False\nexcept UnicodeError:pass\n"
code += "from embit import bip39\n"
for row in [r for r in d['cases'] if r['utf8']][:32]:
    mnemonic = 'abandon ' * 11 + 'about'
    seed = hashlib.pbkdf2_hmac(
        'sha512', mnemonic.encode(), ('mnemonic' + row['expected']).encode(), 2048
    ).hex()
    code += f"assert bip39.mnemonic_to_seed({mnemonic!r},password=normalize_passphrase({row['input']!r})).hex()=={seed!r}\n"
code += (
    "for i in range(3):gc.collect()\nassert camera.settings()['rust_heap_bytes']==baseline\nprint('@@PASSPHRASE_REF_PASS',"
    + str(len(d['cases']))
    + ")\n"
)
(root / 'micropython/passphrase_gate.py').write_text(code)
print('Prepared', len(d['cases']), 'public REF passphrase cases')

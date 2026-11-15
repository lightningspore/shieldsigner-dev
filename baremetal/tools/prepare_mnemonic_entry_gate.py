# SPDX-License-Identifier: MIT
"""Pin public zero-entropy BIP39 fixtures using independent CPython embit."""
import re
from pathlib import Path
from embit import bip39,bip32
path=Path(__file__).resolve().parents[1]/'micropython/mnemonic_entry_gate.py'
fixtures=[]
for count in (12,15,18,21,24):
    mnemonic=bip39.mnemonic_from_bytes(bytes(count*4//3))
    words=mnemonic.split()
    assert len(words)==count and words[:-1]==['abandon']*(count-1)
    root=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(mnemonic))
    fixtures.append((count,words[-1],root.my_fingerprint.hex()))
code,count=re.subn(r'^fixtures = .+$','fixtures = '+repr(fixtures)+' # Independent public CPython embit0.8.0 oracle.',path.read_text(),flags=re.M)
assert count==1
path.write_text(code)
print('Prepared public zero-entropy lengths:',[f[0] for f in fixtures])

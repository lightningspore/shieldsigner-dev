# SPDX-License-Identifier: MIT
"""Public vectors for actual original Seed model construction and disposal."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'.tools/bip39-vectors.json').read_text())['english']
assert hashlib.sha256((root/'.tools/bip39-vectors.json').read_bytes()).hexdigest()=='fa3b937b7cff9c9b8ecd3aa011faeb8d6dd67993174b72326e83f4de8fdb30f8'
code='''# Generated public fixtures only; actual original Seed class on native runtime.
from seedsigner_port.seed import Seed,InvalidSeedException
from seedsigner_port.decode_platform import FeatureUnavailable
from embit import bip39
import camera
import gc
baseline=camera.settings()['rust_heap_bytes']
'''
for entropy,mnemonic,seed,_ in data:
 code+=f"words={mnemonic!r}.split()\ns=Seed(words,passphrase='TREZOR')\nassert s.seed_bytes.hex()=={seed!r}\nassert s.mnemonic_str=={mnemonic!r}\nassert s.mnemonic_display_list==words\nassert s.has_passphrase and s.passphrase=='TREZOR'\nassert s.seedqr_supported and s.bip85_supported\nalias=s.seed_bytes\ns.wipe()\nassert alias==bytes(64)\nassert s.seed_bytes is None and s.master_secret is None and s.mnemonic_list==[] and s.passphrase==''\nassert ' '.join(words)=={mnemonic!r}\nassert bip39.mnemonic_is_valid({mnemonic!r})\ndel alias,s,words\ngc.collect()\n"
mnemonic=data[0][1]
rows=[r for r in json.loads((root/'unicode/passphrase-ref-oracle.json').read_text())['cases'] if r['utf8']][:32]
for row in rows:
 expected=hashlib.pbkdf2_hmac('sha512',mnemonic.encode(),('mnemonic'+row['expected']).encode(),2048).hex()
 code+=f"s=Seed({mnemonic!r}.split(),passphrase={row['input']!r})\nassert s.passphrase=={row['expected']!r}\nassert s.seed_bytes.hex()=={expected!r}\ns.wipe()\ndel s\ngc.collect()\n"
code+=f"words={mnemonic!r}.split()\na=Seed(words)\nb=Seed([word.upper() for word in words])\nassert a==b\n"
code+='''a.set_passphrase('\\u0061')
assert a.passphrase=='a' and not a==b
a.set_passphrase('',regenerate_seed=False)
assert a.passphrase=='' and not a==b
a.set_passphrase('')
assert a==b
assert a.get_root().is_private
assert a.get_fingerprint()=='73c5da0a' # Public abandon/about, empty passphrase; CPython embit reference
assert a==b
for invalid in (['abandon']*12,['notaword']*12):
    try:Seed(invalid);assert False
    except InvalidSeedException:pass
try:Seed([]);assert False
except Exception:pass
a.wipe()
b.wipe()
assert len(bip39.WORDLIST)==2048 and bip39.mnemonic_is_valid('abandon '*11+'about')
for i in range(3):gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS original-seed-public-vectors-passphrase-wipe',24,32)
'''
(root/'micropython/seed_gate.py').write_text(code)

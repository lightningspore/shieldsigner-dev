# SPDX-License-Identifier: MIT
"""Prepare public BIP39 vectors for actual native embit API checks."""
import hashlib,json,urllib.request,unicodedata
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'.tools/bip39-vectors.json'
url='https://raw.githubusercontent.com/trezor/python-mnemonic/master/vectors.json'
sha='fa3b937b7cff9c9b8ecd3aa011faeb8d6dd67993174b72326e83f4de8fdb30f8'
if not p.exists():
 b=urllib.request.urlopen(url,timeout=60).read();assert hashlib.sha256(b).hexdigest()==sha;p.write_bytes(b)
b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==sha
code='''# Generated public vectors; no wallet secrets.
from embit import bip39
import binascii
import unicodedata as u
import camera
import gc
baseline=camera.settings()['rust_heap_bytes']
assert len(bip39.WORDLIST)==2048
'''
for entropy,mnemonic,seed,_ in json.loads(b)['english']:
 code+=f"entropy=binascii.unhexlify('{entropy}')\nmnemonic={mnemonic!r}\nassert bip39.mnemonic_from_bytes(entropy)==mnemonic\nassert bip39.mnemonic_to_bytes(mnemonic)==entropy\nassert bip39.mnemonic_is_valid(mnemonic)\nassert bip39.mnemonic_to_seed(mnemonic,password='TREZOR').hex()=={seed!r}\n"
for password in ['é','e\u0301','㍍ガバヴァぱばぐゞちぢ十人十色','\ufdfa','\x00']:
 m='abandon '*11+'about';password=unicodedata.normalize('NFKD',password)
 seed=hashlib.pbkdf2_hmac('sha512',m.encode(),('mnemonic'+password).encode(),2048).hex()
 code+=f"assert bip39.mnemonic_to_seed({m!r},password=u.normalize('NFKD',{password!r})).hex()=={seed!r}\n"
code+='''assert not bip39.mnemonic_is_valid('abandon '*12)
assert not bip39.mnemonic_is_valid('notaword '*12)
assert bip39.find_candidates('aban')==['abandon']
for i in range(3):gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@BIP39_PUBLIC_PASS',24,5)
'''
(root/'micropython/bip39_gate.py').write_text(code)
(root/'app/bip39-vectors-provenance.json').write_text(json.dumps({'url':url,'sha256':sha,'englishPublishedVectors':24,'additionalReference':'CPython hashlib + NFKD public Unicode strings','generatedSha256':hashlib.sha256(code.encode()).hexdigest()},indent=2)+'\n')

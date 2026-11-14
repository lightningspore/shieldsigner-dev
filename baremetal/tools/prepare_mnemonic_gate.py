# SPDX-License-Identifier: MIT
"""Public source-reference SLIP39/Aezeed/BIP39 classifier fixtures, no private data."""
import ast,hashlib,json,random,sys,types
from pathlib import Path
from embit import bip39
root=Path(__file__).resolve().parents[1]
source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models/aezeed.py'
module=types.ModuleType('_reference_aezeed');sys.modules[module.__name__]=module;exec(compile(source.read_text(),str(source),'exec'),module.__dict__)
wordmap={w:i for i,w in enumerate(bip39.WORDLIST)}
rng=random.Random(20261114)
checksum_words=[];ambiguous=None
for attempt in range(10000):
 prefix=bytes([0])+bytes(rng.randrange(256) for _ in range(28))
 encoded=prefix+module._crc32c(prefix).to_bytes(4,'big')
 value=int.from_bytes(encoded,'big')
 words=[bip39.WORDLIST[(value>>(11*(23-i)))&2047] for i in range(24)]
 if not checksum_words:checksum_words=words
 if bip39.mnemonic_is_valid(' '.join(words)):ambiguous=words;break
assert ambiguous and module.has_valid_checksum(ambiguous,wordmap)
code='''# Public fixtures only. Actual source algorithms, frozen storage and native KDF.
import shamir_mnemonic as sm
from shamir_mnemonic import wordlist,recovery,shamir
from seedsigner_port import aezeed
from seedsigner_port.seed import Seed,AezeedSeed
from seedsigner_port.decode_qr import DecodeQR,DecodeQRStatus
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.qr_type import QRType
from seedsigner_port.settings_schema import SettingsConstants
import importlib
import hashlib
import camera
import gc
assert importlib.import_module('shamir_mnemonic.wordlist') is wordlist
assert importlib.import_module('.wordlist','shamir_mnemonic') is wordlist
assert importlib.import_module('..wordlist','shamir_mnemonic.share') is wordlist
assert len(wordlist.WORDLIST)==1024
assert hashlib.sha256(('\\n'.join(wordlist.WORDLIST)+'\\n').encode()).hexdigest()=='bcc4555340332d169718aed8bf31dd9d5248cb7da6e5d355140ef4f1e601eec3'
baseline=camera.settings()['rust_heap_bytes']
'''
slip=json.loads((root/'app/shamir-vectors.json').read_text())
for title,phrases,expected,*rest in slip:
 code+=f"phrases={phrases!r}\nexpected={expected!r}\n"
 code+='''if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
'''
code+='''try:shamir.RANDOM_BYTES(16);assert False
except FeatureUnavailable:pass
'''
# Whole reference CRC, including empty input and embedded zero bytes.
for data in [b'',b'123456789',bytes(range(256)),bytes(33)]+[bytes(rng.randrange(256) for _ in range(n)) for n in range(1,32)]:
 code+=f"assert aezeed._crc32c({data!r})=={module._crc32c(data)}\n"
code+=f"aezeed_words={checksum_words!r}\nambiguous_words={ambiguous!r}\n"
code+='''mapping={word:i for i,word in enumerate(Seed.get_wordlist())}
assert aezeed.has_valid_checksum(aezeed_words,mapping)
assert aezeed.has_valid_checksum(ambiguous_words,mapping)
invalid=list(aezeed_words)
invalid[-1]=Seed.get_wordlist()[(mapping[invalid[-1]]+1)%2048]
assert not aezeed.has_valid_checksum(invalid,mapping)
assert not aezeed.has_valid_checksum(['abandon']*12,mapping)
try:AezeedSeed(aezeed_words);assert False
except FeatureUnavailable:pass
try:aezeed._extract_key(bytes(32));assert False
except FeatureUnavailable:pass
for words,kind in ((aezeed_words,'aezeed'),(ambiguous_words,'ambiguous')):
    d=DecodeQR()
    assert d.add_data(' '.join(words))==DecodeQRStatus.COMPLETE
    assert d.decoder.seed_type==kind
'''
bip=json.loads((root/'.tools/bip39-vectors.json').read_text())['english']
rows=[row[1] for row in bip]+[bip39.mnemonic_from_bytes(bytes(range(n))) for n in (20,28)]
for mnemonic in rows:
 prefixes=' '.join(w[:4] for w in mnemonic.split());numeric=''.join('%04d'%bip39.WORDLIST.index(w) for w in mnemonic.split())
 for payload in (mnemonic,prefixes,numeric):
  code+=f"d=DecodeQR()\nassert d.add_data({payload!r})==DecodeQRStatus.COMPLETE\nassert d.get_seed_phrase()=={mnemonic.split()!r}\nassert d.decoder.seed_type=='bip39'\ndel d\ngc.collect()\n"
code+='''assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS original-mnemonic-recognition-shamir-recovery',45,26,35)
'''
(root/'micropython/mnemonic_gate.py').write_text(code)
(root/'app/mnemonic-vectors-provenance.json').write_text(json.dumps({'shamirPublishedVectors':len(slip),'source':'REF-pinned archive vectors.json','bip39MnemonicCases':len(rows),'classifierFormats':['mnemonic','four-letter','numeric'],'aezeedCrcReferenceCases':35,'aezeedFixtures':'Public deterministic checksum-only and ambiguous BIP39+Aezeed; not decryption vectors','generatedSha256':hashlib.sha256(code.encode()).hexdigest()},indent=2)+'\n')
print('Prepared',len(slip),'SLIP39 vectors and',len(rows),'BIP39 mnemonic fixtures')

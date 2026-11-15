# SPDX-License-Identifier: MIT
"""Independent original CPython format-probe oracle; no AES operation is used."""
import ast,copy,json,hashlib,sys,types
from pathlib import Path
from embit import base58
root=Path(__file__).resolve().parents[1];source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner'
# Execute unmodified original KEF/base43 algorithms against actual CPython AES
# constants. The original public_data method does not invoke a cipher.
kef=types.ModuleType('reference_kef');exec(compile((source/'helpers/kef.py').read_text(),'<original kef>','exec'),kef.__dict__)
b43={};exec(compile((source/'helpers/base43.py').read_text(),'<original base43>','exec'),b43)
sys.path.append(str(root/'app'))
from seedsigner_port.settings_store import Settings,SettingsConstants
scope={'kef':kef,'Settings':Settings,'SettingsConstants':SettingsConstants,'QR_CODE_ITER_MULTIPLE':10000,'base43_decode':b43['base43_decode']}
node=next(n for n in ast.parse((source/'models/encryption.py').read_text()).body if isinstance(n,ast.ClassDef))
exec(compile(ast.Module(body=[node],type_ignores=[]),'<original public-data class>','exec'),scope)
tree=ast.parse((source/'models/decode_qr.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DecodeQR')
method=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='parse_encrypted_qr'))
method.decorator_list=[];method.body=[n for n in method.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<original format probe>','exec'),scope)
samples=[b'',b'\0',bytes(16),bytes(range(16)),bytes(range(20)),bytes(range(24)),bytes(range(28)),bytes(range(32)),b'A'*31+b'\n',b'A'*31+b'\0']
for version,meta in kef.VERSIONS.items():
    extra=kef.MODE_IVS.get(meta['mode'],0)+max(meta.get('auth',0),0)
    length=extra+(16 if meta.get('pkcs_pad',False) in (True,False) else 7)
    for identifier in (b'',b'public',b'\xff'):
        envelope=kef.wrap(identifier,version,100000,b'B'*length)
        samples.extend((envelope,b43['base43_encode'](envelope).encode(),envelope[:-1]))
cases=[]
for raw in samples:
    obj,public=scope['parse_encrypted_qr'](raw)
    state=(obj.mnemonic_id,obj.version,obj.iterations,obj.encrypted_data) if obj else None
    cases.append((raw,public,state))
# Public BIP38-shaped envelopes validate the actual base58/checksum/container
# parser only. Payload bytes are opaque test data; no decryption is claimed.
bip38=[]
for compressed in (False,True):
    raw=b'\x01\x42'+bytes([0x20 if compressed else 0])+bytes(range(36))
    bip38.append((base58.encode_check(raw),compressed,raw[3:7],raw[7:23],raw[23:39]))
code='''# SPDX-License-Identifier: MIT
# Generated PUBLIC format envelopes. No private QR text/payload is printed.
from seedsigner_port import kef,base43
from seedsigner_port.encryption import EncryptedQRCode
from seedsigner_port.bip38 import BIP38Key
from seedsigner_port.decode_qr import DecodeQR
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.controller import Controller
from seedsigner_port.seed import InvalidSeedException
from seedsigner_port.qr_type import QRType
import gc,machine
c=Controller.get_instance()
for seed in list(c.storage.seeds):c.discard_seed(seed)
c.storage.clear_pending_seed()
cases='''+repr(cases)+'''
for number,(raw,expected,state) in enumerate(cases):
    obj,public=DecodeQR.parse_encrypted_qr(raw)
    assert public==expected
    if state is None:assert obj is None
    else:assert (obj.mnemonic_id,obj.version,obj.iterations,obj.encrypted_data)==state
    analysis=DecodeQR.analyze_bytedata_payload(raw)
    assert (QRType.SEED__COMPACTSEEDQR in analysis.candidate_types)==(len(raw) in (16,20,24,28,32))
    assert (QRType.SEED__ENCRYPTEDQR in analysis.candidate_types)==bool(expected)
    if number%16==0:gc.collect()
print('@@PASS original-QR-format-probes-cpython',len(cases))
for text in ('','0','00','0123','000123','ABCDEF'):
    raw=base43.base43_decode(text)
    assert base43.base43_decode(base43.base43_encode(raw))==raw
print('@@PASS original-base43-leading-zeroes')
bip38='''+repr(bip38)+'''
for text,compressed,address,a,b in bip38:
    obj=BIP38Key(text)
    assert (obj.compressed,obj.address_hash,obj.encrypted_half1,obj.encrypted_half2)==(compressed,address,a,b)
    try:obj.decrypt('PUBLIC TEST');assert False
    except FeatureUnavailable:pass
for text in ('not-bip38','6Pinvalid',''):
    try:BIP38Key(text);assert False
    except InvalidSeedException:pass
for action in (lambda:kef.Cipher('PUBLIC','public',1).encrypt(b'PUBLIC',20),lambda:EncryptedQRCode().create('PUBLIC','public','PUBLIC'),lambda:EncryptedQRCode().decrypt('PUBLIC')):
    try:action();assert False
    except FeatureUnavailable:pass
print('@@PASS original-bip38-format-crypto-explicitly-unavailable')
assert c.storage.num_seeds()==0 and c.storage.get_pending_seed() is None
'''
(root/'micropython/qr_detection_gate.py').write_text(code)
(root/'app/qr-detection-public-oracle.json').write_text(json.dumps({'provider':'Original CPython KEF/base43/EncryptedQRCode/DecodeQR format-probe bodies; native Settings supplies only constructor defaults, overwritten by parsed metadata. Actual pycryptodomex3.23.0 constants; no encryption/decryption operation.','cases':len(cases),'gateSha256':hashlib.sha256(code.encode()).hexdigest()},indent=2)+'\n')
print('Prepared',len(cases),'independent public format probes')

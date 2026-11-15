# SPDX-License-Identifier: MIT
"""Generate native framing checks against the complete locked original checker."""
import ast,hashlib,json,types
from pathlib import Path
from io import BytesIO
from embit.psbt import PSBT
from embit.transaction import Transaction,TransactionInput,TransactionOutput
from embit.script import Script
root=Path(__file__).resolve().parents[1];src=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models'
parser=ast.parse((src/'psbt_parser.py').read_text());g={'BytesIO':BytesIO,'PSBT':PSBT,'Transaction':Transaction}
nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+[n for n in parser.body if isinstance(n,ast.ClassDef) and n.name in ('RejectCode','InvalidPSBTError')]
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<original error classes>','exec'),g)
tree=ast.parse((src/'psbt_framing.py').read_text())
nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<whole original framing>','exec'),g)
def field(key,value):return bytes((len(key),))+key+bytes((len(value),))+value
unsigned=Transaction(vin=[TransactionInput(b'\x11'*32,0)],vout=[TransactionOutput(1000,Script(b'\x51'))]).serialize()
header=b'psbt\xff';tx=field(b'\0',unsigned)
version=field(b'\xfb',(2).to_bytes(4,'little'));counts=field(b'\x04',b'\x01')+field(b'\x05',b'\x01')
v2globals=version+field(b'\x02',(2).to_bytes(4,'little'))+counts
ins=field(b'\x0e',b'\x11'*32)+field(b'\x0f',bytes(4))+b'\0'
outs=field(b'\x03',(1000).to_bytes(8,'little'))+field(b'\x04',b'\x51')+b'\0'
valid0=header+tx+b'\0\0\0';valid2=header+v2globals+b'\0'+ins+outs
cases=[('valid-v0',valid0),('valid-v2',valid2),('duplicate',header+version+version+b'\0'),('nonminimal-key-length',header+b'\xfd\x01\0\xfb\x04'+bytes(4)+b'\0'),('nonminimal-type',header+field(b'\xfd\x01\0',b'')+b'\0'),('nonminimal-value',header+b'\x01\xfb\xfd\x04\0'+bytes(4)+b'\0'),('v0-global-v2-field',header+tx+field(b'\x02',bytes(4))+b'\0\0\0'),('v0-input-v2-field',header+tx+b'\0'+field(b'\x0e',b'\x11'*32)+b'\0\0'),('v0-output-v2-field',header+tx+b'\0\0'+field(b'\x03',bytes(8))+b'\0'),('v2-global-tx',header+v2globals+tx+b'\0'+ins+outs),('v2-impossible-count',header+version+field(b'\x04',b'\xfe'+b'\xff'*4)+field(b'\x05',b'\x01')+b'\0'),('count-extra',header+version+field(b'\x04',b'\x01\0')+field(b'\x05',b'\x01')+b'\0'),('trailing',valid0+b'\0'),('truncated',valid0[:-3]),('wrong-magic',b'public-not-psbt')]
code='''# Public synthetic data; actual original checker + native embit, not signing.
import binascii
from seedsigner_port.psbt_framing import parse_psbt
from seedsigner_port.psbt_errors import InvalidPSBTError
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.decode_qr import DecodeQR,DecodeQRStatus
from embit import ec
import camera
import gc
baseline=camera.settings()['rust_heap_bytes']
'''
receipt=[]
for name,raw in cases:
 try:p=g['parse_psbt'](raw);expected='ok';serialized=p.serialize().hex()
 except g['InvalidPSBTError'] as e:expected='reject:'+e.code
 except Exception as e:expected='error:'+type(e).__name__
 receipt.append({'name':name,'rawHex':raw.hex(),'expected':expected})
 code+=f"raw=binascii.unhexlify('{raw.hex()}')\nresult='unexpected'\ntry:\n    parsed=parse_psbt(raw)\n    result='ok'\n"
 if expected=='ok':code+=f"    assert parsed.serialize().hex()=={serialized!r}\n"
 code+="except FeatureUnavailable:raise\nexcept InvalidPSBTError as e:result='reject:'+e.code\nexcept Exception as e:result='error:'+type(e).__name__\n"
 code+=f"assert result=={expected!r},({name!r},result)\ngc.collect()\n"
code+='''point=ec.PublicKey.parse(binascii.unhexlify('0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'))
assert point.sec().hex()=='0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
assert ec.NUMS_PUBKEY.sec().hex()=='0250929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0'
d=DecodeQR()
status=d.add_data('0000'*11+'0003')
assert status==DecodeQRStatus.COMPLETE and d.is_complete
assert d.get_seed_phrase()==['abandon']*11+['about']
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS original-psbt-framing-and-numeric-seedqr',15)
'''
(root/'micropython/psbt_framing_gate.py').write_text(code)
(root/'app/psbt-framing-vectors.json').write_text(json.dumps({'reference':'Whole locked original checker + embit0.8.0 on CPython','cases':receipt,'generatedSha256':hashlib.sha256(code.encode()).hexdigest()},indent=2)+'\n')

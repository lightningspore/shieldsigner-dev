# SPDX-License-Identifier: MIT
"""CPython-original public UR frames for later native protocol gates."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
# Import unmodified original app source, not the frozen output being tested.
source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/helpers'
sys.path.insert(0,str(source))
from ur2.ur import UR
from ur2.ur_encoder import UREncoder
from urtypes.bytes import Bytes
cases=[]
for data in (b'PUBLIC-UR-fixture',bytes(range(256)),b'\0PUBLIC\xff'*24):
 for density in (10,30,120):
    cbor=Bytes(data).to_cbor();encoder=UREncoder(UR('bytes',cbor),density);count=encoder.fountain_encoder.seq_len()
    parts=[encoder.next_part().upper() for _ in range(count+8)]
    cases.append((data,density,bytes(cbor),count,parts))
code='''# SPDX-License-Identifier: MIT
# PUBLIC original CPython UR oracle; protocol PRNG is fountain mixing, not entropy.
from seedsigner_port.ur2.ur import UR
from seedsigner_port.ur2.ur_encoder import UREncoder
from seedsigner_port.ur2.ur_decoder import URDecoder
from urtypes.bytes import Bytes
from urtypes.crypto import PSBT
import gc,machine
record=machine.last_reset();print('@@UR_RESET_BEFORE',record)
assert record is None or record['reason']==2
machine.clear_reset_record();machine.set_reset_marker(0x5552434f)
cases='''+repr(cases)+'''
for number,(data,density,expected_cbor,count,parts) in enumerate(cases):
    cbor=Bytes(data).to_cbor();assert cbor==expected_cbor
    encoder=UREncoder(UR('bytes',cbor),density)
    assert encoder.fountain_encoder.seq_len()==count
    actual=[encoder.next_part().upper() for _ in range(count+8)]
    assert actual==parts
    decoder=URDecoder()
    for part in [parts[count-1]]+list(reversed(parts[:count])):decoder.receive_part(part)
    assert decoder.is_success() and Bytes.from_cbor(decoder.result_message().cbor).data==data
    mixed=URDecoder()
    for _ in range(count*20+20):
        mixed.receive_part(encoder.next_part())
        if mixed.is_success():break
    assert mixed.is_success() and bytes(mixed.result_message().cbor)==expected_cbor
    encoder.restart();assert encoder.next_part().upper()==parts[0]
    gc.collect();print('@@PASS public-original-ur-fountain-cbor',number,density,count)
assert PSBT.from_cbor(PSBT(b'psbt'+bytes([255])+b'PUBLIC').to_cbor()).data==b'psbt'+bytes([255])+b'PUBLIC'
assert machine.last_reset() is None
print('@@PASS public-ur-psbt-registry')
'''
p=root/'micropython/ur_core_gate.py';p.write_text(code)
(root/'app/ur-public-oracle.json').write_text(json.dumps({'source':'Unmodified pinned original app helpers/ur2 and requirements-pinned urtypes','cases':len(cases),'gateSha256':hashlib.sha256(code.encode()).hexdigest(),'scope':'Public protocol bytes/CBOR/fountain mixing only, no signing/entropy qualification.'},indent=2)+'\n')
print('Prepared',len(cases),'public UR protocol cases')

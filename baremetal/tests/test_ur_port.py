# SPDX-License-Identifier: MIT
"""Original UR source provenance and public fountain/CBOR transport semantics."""
import hashlib,json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.append(str(root/'app'))
from seedsigner_port.ur2.ur import UR
from seedsigner_port.ur2.ur_encoder import UREncoder
from seedsigner_port.ur2.ur_decoder import URDecoder
from urtypes.bytes import Bytes
from urtypes.crypto import PSBT,HDKey,Keypath,PathComponent,CoinInfo,Account,Output,SCRIPT_EXPRESSION_TAG_MAP
class UrPortTests(unittest.TestCase):
 def test_source_files_are_unmodified_and_all_inputs_have_provenance(self):
    r=json.loads((root/'app/ur-provenance.json').read_text());self.assertEqual(len(r['files']),31)
    source=root.parent/'dist/firmware/sources/lvgl/application'
    for name,item in r['files'].items():
        output=(root/'app'/name).read_bytes();self.assertEqual(hashlib.sha256(output).hexdigest(),item['outputSha256'])
        self.assertEqual(item['sourceSha256'],item['outputSha256'])
        if item['source'].startswith('src/'):
            self.assertEqual(hashlib.sha256((source/item['source']).read_bytes()).hexdigest(),item['sourceSha256'])
 def test_single_part_and_mixed_fountain_bytes_roundtrip(self):
    for data in (b'PUBLIC-UR-fixture',bytes(range(256)),b'\0'*128+b'PUBLIC\xff'*40):
     for density in (10,30,120):
        cbor=Bytes(data).to_cbor();encoder=UREncoder(UR('bytes',cbor),density);count=encoder.fountain_encoder.seq_len()
        first=[encoder.next_part() for _ in range(count)]
        # Repeated/case-insensitive/out-of-order pure frames preserve exact CBOR.
        decoder=URDecoder()
        for part in [first[-1]]+list(reversed(first)):
            decoder.receive_part(part.upper())
        self.assertTrue(decoder.is_success());self.assertEqual(Bytes.from_cbor(decoder.result_message().cbor).data,data)
        # Drop every pure frame; deterministic fountain parts must recover data.
        mixed=URDecoder()
        for _ in range(count*20+20):
            mixed.receive_part(encoder.next_part())
            if mixed.is_success():break
        self.assertTrue(mixed.is_success());self.assertEqual(bytes(mixed.result_message().cbor),bytes(cbor))
        encoder.restart();self.assertEqual(encoder.next_part(),first[0])
 def test_actual_urtypes_crypto_registry_cbor_roundtrip(self):
    data=b'psbt\xffPUBLIC';self.assertEqual(PSBT.from_cbor(PSBT(data).to_cbor()).data,data)
    # Public deterministic key material only; these registry objects do no signing.
    key=HDKey({'key':b'\x02'+bytes(range(32)),'chain_code':bytes(range(32)),
               'origin':Keypath([PathComponent(84,True),PathComponent(1,True),PathComponent(7,True)],b'PUB!',3),
               'parent_fingerprint':b'PAR!','use_info':CoinInfo(type=None,network=1)})
    account=Account(b'PUB!',[Output([SCRIPT_EXPRESSION_TAG_MAP[404]],key)])
    restored=Account.from_cbor(account.to_cbor())
    self.assertEqual(restored.to_cbor(),account.to_cbor())

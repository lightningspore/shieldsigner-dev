"""Original payload parsers after lazy imports; public deterministic data only."""
import base64,json,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
try:
 from seedsigner.models.decode_qr import DecodeQR,DecodeQRStatus
 initial=DecodeQR()
 assert initial.decoder is None
 for name in ('urtypes','seedsigner.models.psbt_parser','seedsigner.helpers.ur2.ur_decoder','seedsigner.models.aezeed','datetime'):
  assert name not in sys.modules,('Eager parser remains',name)
 from seedsigner.models.decode_qr import TimeQrDecoder
 clock=TimeQrDecoder()
 assert clock.get_time() is None
 assert clock.add('oT261030153045.123')==DecodeQRStatus.COMPLETE
 assert clock.get_time().isoformat()=='2026-10-30T15:30:45'
 assert clock.add('oT261332153045')==DecodeQRStatus.COMPLETE
 assert clock.get_time() is None
 from embit import bip39
 cases=[dict(kind='time',fractionalSecondsTruncated=True,invalidDateReturnsNone=True)]
 for size in (16,32):
  entropy=bytes(range(size));words=bip39.mnemonic_from_bytes(entropy).split()
  numeric=''.join(str(bip39.WORDLIST.index(word)).zfill(4) for word in words)
  for label,payload in [('compact',entropy),('numeric',numeric)]:
   decoder=DecodeQR();assert decoder.add_data(payload)==DecodeQRStatus.COMPLETE
   assert decoder.get_seed_phrase()==words
   cases.append(dict(kind=label,wordCount=len(words)))
 from embit import psbt,transaction,script
 tx=transaction.Transaction(vin=[transaction.TransactionInput(bytes(32),0)],vout=[transaction.TransactionOutput(0,script.Script(b'\x6a\x4c\xc8'+bytes(range(200))))])
 payload=psbt.PSBT(tx).serialize()
 from seedsigner.helpers.base43 import base43_encode
 for label,data in [('base64',base64.b64encode(payload).decode()),('base43',base43_encode(payload))]:
  decoder=DecodeQR();assert decoder.add_data(data)==DecodeQRStatus.COMPLETE,label
  assert decoder.get_data_psbt()==payload and decoder.get_psbt().serialize()==payload
  cases.append(dict(kind=label,psbtBytesExact=True))
 from seedsigner.helpers.ur2.ur import UR
 from seedsigner.helpers.ur2.ur_encoder import UREncoder
 from urtypes.crypto import PSBT as UR_PSBT
 encoder=UREncoder(UR('crypto-psbt',UR_PSBT(payload).to_cbor()),max_fragment_len=60);fragments=[]
 for _ in range(30):
  fragments.append(encoder.next_part())
  if encoder.is_complete():break
 assert len(fragments)>1
 decoder=DecodeQR()
 for fragment in [fragments[-1],*reversed(fragments)]:decoder.add_data(fragment)
 assert decoder.complete and decoder.get_data_psbt()==payload and decoder.get_psbt().serialize()==payload
 cases.append(dict(kind='animated-ur',fragments=len(fragments),reversed=True,duplicate=True,psbtBytesExact=True))
 from seedsigner.models.psbt_parser import InvalidPSBTError
 decoder=DecodeQR();decoder.add_data(base64.b64encode(b'psbt\xffinvalid public framing').decode())
 assert decoder.get_psbt() is None
 from embit import compact
 unsigned=tx.serialize();entry=b'\x01\x00'+compact.to_bytes(len(unsigned))+unsigned
 refused=b'psbt\xff'+entry+entry+b'\x00\x00\x00'
 decoder=DecodeQR();decoder.add_data(base64.b64encode(refused).decode())
 try:decoder.get_psbt()
 except InvalidPSBTError:pass
 else:raise AssertionError('Original malformed PSBT refusal was lost')
 print(json.dumps(dict(passed=True,cases=cases,constructorLeavesOptionalParsersUnloaded=True,originalMalformedPSBTRefusal=True,originalUnreadableReturnsNone=True,publicFixtures=True,hardwareOpened=False,walletCreated=False)),flush=True)
finally:restore()

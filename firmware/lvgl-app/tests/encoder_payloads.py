"""Compare deferred encoders with pinned original code, using public fixtures."""
import json,sys,types
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
seed=None
try:
 from seedsigner.models import encode_qr as adapted
 assert not any(n=='urtypes' or n.startswith('urtypes.') for n in sys.modules)
 assert 'seedsigner.helpers.ur2.ur_encoder' not in sys.modules
 assert 'embit.psbt' not in sys.modules
 # Static encoders must also work without loading the UR backend.
 assert adapted.GenericStaticQrEncoder(data='public').next_part()=='public'
 assert adapted.GenericStringEncoder('public').next_part()=='public'
 assert 'seedsigner.helpers.ur2.ur_encoder' not in sys.modules
 original=types.ModuleType('public_original_encoders')
 sys.modules[original.__name__]=original
 source=Path('/opt/src/seedsigner/models/encode_qr.py').read_bytes()
 exec(compile(source,'/opt/src/seedsigner/models/encode_qr.py','exec'),original.__dict__)
 from seedsigner.models.seed import Seed
 from seedsigner.models.settings import SettingsConstants as C
 from embit import bip39,psbt,transaction,script
 from seedsigner.helpers.ur2.ur_decoder import URDecoder
 from urtypes.bytes import Bytes
 from urtypes.crypto import PSBT as UR_PSBT
 cases=[]
 def compare(name,kwargs):
  left=getattr(original,name)(**kwargs);right=getattr(adapted,name)(**kwargs)
  count=min(100,left.seq_len()+5)
  assert right.seq_len()==left.seq_len(),name
  for _ in range(count):
   assert left.next_part()==right.next_part(),name
   assert left.is_complete==right.is_complete,name
  assert left.cur_part()==right.cur_part(),name
  left.restart();right.restart()
  assert left.next_part()==right.next_part(),name
  cases.append(dict(encoder=name,partsCompared=count))
  return right
 for length in (16,32):
  words=bip39.mnemonic_from_bytes(bytes(range(length))).split()
  compare('SeedQrEncoder',dict(mnemonic=words))
  compare('CompactSeedQrEncoder',dict(mnemonic=words))
 compare('GenericStaticQrEncoder',dict(data='public café'))
 compare('GenericStringEncoder',dict(generic_string='public'))
 seed=Seed(bip39.mnemonic_from_bytes(bytes(range(16))).split())
 for network,coin in ((C.MAINNET,0),(C.TESTNET,1)):
  for name in ('StaticXpubQrEncoder','SpecterLegacyXPubQrEncoder','UrXpubQrEncoder'):
   compare(name,dict(seed=seed,derivation=f"m/84'/{coin}'/0'",network=network,sig_type=C.SINGLE_SIG))
  compare('UrXpubQrEncoder',dict(seed=seed,derivation=f"m/48'/{coin}'/0'/2'",network=network,sig_type=C.MULTISIG))
 tx=transaction.Transaction(vin=[transaction.TransactionInput(bytes(32),0)],vout=[transaction.TransactionOutput(0,script.Script(b'\x6a\x4c\xc8'+bytes(range(200))))])
 public_psbt=psbt.PSBT(tx)
 binary=bytes(range(256))*2
 for density in (C.DENSITY__LOW,C.DENSITY__MEDIUM,C.DENSITY__HIGH):
  for name,kwargs,expected in (
   ('UrPsbtQrEncoder',dict(psbt=public_psbt),public_psbt.serialize()),
   ('UrBytesQrEncoder',dict(data=binary),binary),
   ('UrTextQrEncoder',dict(text='public café text'*20),None)):
   encoder=compare(name,dict(kwargs,qr_density=density))
   decoder=URDecoder()
   for _ in range(200):
    decoder.receive_part(encoder.next_part())
    if decoder.is_complete():break
   assert decoder.is_success(),name
   result=decoder.result_message()
   if expected is not None:
    cls=UR_PSBT if name=='UrPsbtQrEncoder' else Bytes
    value=cls.from_cbor(result.cbor)
    assert value.data==expected,name
   else:assert result.type=='text'
 print(json.dumps(dict(passed=True,cases=cases,staticLeavesUrBackendUnloaded=True,originalOutputExact=True,urRoundTrips=True,publicFixtures=True,hardwareOpened=False)),flush=True)
finally:
 if seed is not None:seed.wipe()
 sys.modules.pop('public_original_encoders',None)
 restore()

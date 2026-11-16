# SPDX-License-Identifier: MIT
"""Independent original-helper/CPython embit public xpub and address oracle."""
import ast,hashlib,json,sys
from pathlib import Path
from embit import bip39,bip32,networks
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
from seedsigner_port.settings_schema import SettingsConstants as C
path=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/helpers/embit_utils.py'
names={'get_standard_derivation_path','get_single_sig_address'}
tree=ast.parse(path.read_text());nodes=ast.parse('from __future__ import annotations').body+[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns={'SettingsConstants':C,'embit':__import__('embit'),'bip32':bip32,'NETWORKS':networks.NETWORKS}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
words=bip39.mnemonic_from_bytes(bytes(range(16))).split();cases=[]
for network in (C.MAINNET,C.TESTNET,C.REGTEST):
 net=C.map_network_to_embit(network)
 for sig in (C.SINGLE_SIG,C.MULTISIG):
  for kind in (C.LEGACY_P2PKH,C.NESTED_SEGWIT,C.NATIVE_SEGWIT,C.TAPROOT):
   if sig==C.MULTISIG and kind==C.TAPROOT:continue
   for account in (0,7):
    derivation=ns['get_standard_derivation_path'](network,sig,kind,account)
    rootkey=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(words),password='PUBLIC'))
    xpub=rootkey.derive(derivation).to_public();version=bip32.detect_version(derivation,default='xpub',network=networks.NETWORKS[net]);key=xpub.to_string(version)
    payload='['+rootkey.child(0).fingerprint.hex()+derivation[1:]+']'+key
    addresses=[]
    if sig==C.SINGLE_SIG:
     for change,index in ((False,0),(True,7)):
      addresses.append((index,change,ns['get_single_sig_address'](xpub,kind,index,change,net)))
    cases.append((network,sig,kind,account,derivation,key,payload,addresses))
code='''# SPDX-License-Identifier: MIT
# PUBLIC known mnemonic/passphrase and independent CPython results only.
from seedsigner_port.seed import Seed
from seedsigner_port import embit_utils
from seedsigner_port.encode_qr import StaticXpubQrEncoder,SpecterLegacyXPubQrEncoder
from seedsigner_port.settings_schema import SettingsConstants as C
from embit import bip32
import gc,machine,time
record=machine.last_reset()
print('@@XPUB_RESET_BEFORE',record)
assert record is None or record['reason']==2
machine.clear_reset_record();machine.set_reset_marker(0x58505542)
words='''+repr(words)+'''
cases='''+repr(cases)+'''
seed=Seed(words,passphrase='PUBLIC');started=time.ticks_ms()
for number,(network,sig,kind,account,path,expected,payload,addresses) in enumerate(cases):
    assert embit_utils.get_standard_derivation_path(network,sig,kind,account)==path
    encoder=StaticXpubQrEncoder(seed=seed,derivation=path,network=network,sig_type=sig)
    assert encoder.xpub_base58==expected and encoder.next_part()==payload
    assert encoder.cur_part()==payload and encoder.seq_len()==1 and encoder.is_complete
    for index,change,address in addresses:
        assert embit_utils.get_single_sig_address(encoder.xpub,kind,index,change,C.map_network_to_embit(network))==address
    for density in (C.DENSITY__LOW,C.DENSITY__MEDIUM,C.DENSITY__HIGH):
        animated=SpecterLegacyXPubQrEncoder(seed=seed,derivation=path,network=network,sig_type=sig,qr_density=density)
        parts=[animated.next_part() for _ in range(animated.seq_len())]
        assert ''.join(part.split(' ',1)[1] if part.startswith('p') and ' ' in part else part for part in parts)==payload
        assert animated.is_complete and animated.next_part()==parts[0]
        animated.restart();assert animated.next_part()==parts[0]
    gc.collect()
    print('@@PASS public-original-xpub-address-encoders',number,network,sig,kind,account)
seed.wipe()
assert machine.last_reset() is None
print('@@XPUB_CORE_MS',time.ticks_ms()-started)
'''
(root/'micropython/xpub_core_gate.py').write_text(code)
(root/'app/xpub-public-oracle.json').write_text(json.dumps({'provider':'CPython embit0.8.0 plus original derivation/address helper bodies','cases':len(cases),'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'gateSha256':hashlib.sha256(code.encode()).hexdigest(),'scope':'Public mnemonic, PUBLIC passphrase, accounts0/7,3networks,7supported script/signature combinations; no signing/security qualification.'},indent=2)+'\n')
print('Prepared',len(cases),'public xpub cases')
import re
p=root/'micropython/xpub_flow_gate.py';text=p.read_text()
selected=[case for case in cases if case[0] in (C.MAINNET,C.TESTNET) and case[2]==C.NATIVE_SEGWIT and case[3]==0]
text=re.sub(r'^fixtures = .+$',lambda _: 'fixtures = '+repr(selected)+' # PUBLIC CPython oracle.',text,flags=re.M)
text=re.sub(r'^words = .+$',lambda _: 'words = '+repr(words)+' # PUBLIC prepared mnemonic.',text,flags=re.M)
p.write_text(text)

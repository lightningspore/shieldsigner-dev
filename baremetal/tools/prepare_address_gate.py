# SPDX-License-Identifier: MIT
"""Independent PUBLIC coordinator address pixels and exact search expectations."""
import json,hashlib,re,sys
from pathlib import Path
from embit import bip32,bip39,script,networks
import qrcode
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
from seedsigner_port.settings_schema import SettingsConstants as C
words=bip39.mnemonic_from_bytes(bytes(range(16))).split();master=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(words),password='PUBLIC'))
def path(network,kind,account=0):return "m/%d'/%d'/%d'"%({C.LEGACY_P2PKH:44,C.NESTED_SEGWIT:49,C.NATIVE_SEGWIT:84,C.TAPROOT:86}[kind],0 if network==C.MAINNET else 1,account)
def address(network,kind,index,change=False,account=0):
 key=master.derive(path(network,kind,account)).to_public().derive([int(change),index]).key
 spk={C.LEGACY_P2PKH:lambda:script.p2pkh(key),C.NESTED_SEGWIT:lambda:script.p2sh(script.p2wpkh(key)),C.NATIVE_SEGWIT:lambda:script.p2wpkh(key),C.TAPROOT:lambda:script.p2tr(key)}[kind]()
 return spk.address(networks.NETWORKS[C.map_network_to_embit(network)])
def case(name,network,kind,index,change=False,mode='success',scanned_kind=None,account=0):
 target=address(network,scanned_kind or kind,index,change,account)
 q=qrcode.QRCode(border=4,error_correction=qrcode.constants.ERROR_CORRECT_L);q.add_data(target);q.make(fit=True)
 rows=tuple(''.join('1' if b else '0' for b in row) for row in q.get_matrix())
 if mode=='no-match':
  master.derive(path(network,kind)).to_public()  # path must derive
  for i in range(1000):
   for change_ in (False,True):assert address(network,kind,i,change_)!=target
 return (name,network,kind,path(network,kind),target,index,change,mode,rows)
cases=[case('receive0',C.MAINNET,C.NATIVE_SEGWIT,0),case('change7',C.MAINNET,C.NESTED_SEGWIT,7,True),case('taproot7',C.TESTNET,C.TAPROOT,7),case('legacy7',C.MAINNET,C.LEGACY_P2PKH,7),case('skip10',C.MAINNET,C.NATIVE_SEGWIT,10,mode='skip'),case('cancel',C.MAINNET,C.NATIVE_SEGWIT,50,mode='cancel'),case('script-mismatch',C.MAINNET,C.NATIVE_SEGWIT,0,mode='script-mismatch',scanned_kind=C.LEGACY_P2PKH),case('other-account',C.MAINNET,C.NATIVE_SEGWIT,0,mode='no-match',account=1),case('last999',C.MAINNET,C.NATIVE_SEGWIT,999,True),case('boundary1000',C.MAINNET,C.NATIVE_SEGWIT,1000,mode='no-match'),case('idle',C.MAINNET,C.NATIVE_SEGWIT,1000,mode='idle')]
p=root/'micropython/address_flow_gate.py';text=p.read_text()
text=re.sub(r'^fixtures = .+$',lambda _: 'fixtures = '+repr(cases)+' # PUBLIC independent CPython oracle.',text,flags=re.M)
text=re.sub(r'^words = .+$',lambda _: 'words = '+repr(words)+' # PUBLIC prepared mnemonic.',text,flags=re.M);p.write_text(text)
(root/'app/address-public-oracle.json').write_text(json.dumps({'provider':'CPython embit0.8.0/qrcode7.3.1','cases':len(cases),'gateSha256':hashlib.sha256(text.encode()).hexdigest(),'scope':'Known public mnemonic/PUBLIC passphrase; 0/7/10/999 matching, exact1000 bound, another account, wrong script, cancel and idle; not optical/security qualification.'},indent=2)+'\n')
print('Prepared',len(cases),'public address scan/search cases')
search=[]
for name,index,change,mode,targetpath in [('simple0',0,False,'simple',"m/84'/0'/0'"),('next100',150,True,'simple-batch',"m/84'/0'/0'"),('nonstandard',1,True,'expanded-nonstandard',"m/44'/0'/1'"),('next10',10,False,'expanded-batch',"m/84'/0'/0'")]:
 pub=master.derive(targetpath).to_public().derive([int(change),index]).key
 target=script.p2wpkh(pub).address(networks.NETWORKS['main'])
 search.append((name,target,targetpath,C.NATIVE_SEGWIT,index,change,mode))
p=root/'micropython/address_search_gate.py';text=p.read_text()
text=re.sub(r'^fixtures = .+$',lambda _: 'fixtures = '+repr(search)+' # PUBLIC CPython oracle.',text,flags=re.M)
text=re.sub(r'^words = .+$',lambda _: 'words = '+repr(words)+' # PUBLIC prepared mnemonic.',text,flags=re.M);p.write_text(text)
# Exact public fixture for the real USB-interrupt tool, never scene data.
(root/'app/address-interrupt-public.json').write_text(json.dumps({'words':words,'address':cases[7][4],'derivation':path(C.MAINNET,C.NATIVE_SEGWIT)},indent=2)+'\n')

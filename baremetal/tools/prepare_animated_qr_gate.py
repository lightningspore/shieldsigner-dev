# SPDX-License-Identifier: MIT
"""Use existing independent PUBLIC xpub fixture for original Specter frames."""
import ast,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
tree=ast.parse((root/'micropython/xpub_core_gate.py').read_text())
values={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('words','cases')}
fixture=values['cases'][4] # Mainnet native singlesig/account0, independent embit oracle.
network,sig,kind,account,path,key,payload,addresses=fixture
# Match source SpecterLegacyXPubQrEncoder low-density40-character fragments.
count=(len(payload)-1)//40+1
parts=[('p%dof%d '%(i+1,count))+payload[i*40:(i+1)*40] for i in range(count)]
p=root/'micropython/animated_qr_gate.py';text=p.read_text()
for name,value in {'words':values['words'],'payload':payload,'derivation':path,'parts':parts}.items():
 text=re.sub(r'^'+name+r' = .+$',lambda _:name+' = '+repr(value)+' # PUBLIC independent oracle.',text,flags=re.M)
p.write_text(text)
print('Prepared',count,'public Specter QR frames')

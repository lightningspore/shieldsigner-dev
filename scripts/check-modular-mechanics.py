#!/usr/bin/env python3
"""Gate exact modular land patterns, purchased-module interfaces and portable models."""
import hashlib,json,math,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/lcd-module-2.8';K=V/'kicad'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one=sx['one'];children=sx['children'];parse=sx['parse']
tree=parse((K/'SeedSigner-Plus-smartcard-pico.kicad_pcb').read_text());fps={next(x[2] for x in children(f,'property') if x[1]=='Reference'):f for f in children(tree,'footprint')}
provenance=json.loads((K/'3dmodels/provenance.json').read_text())['models'];mechanical=json.loads((V/'mechanical.json').read_text())
def near(actual,expected,tolerance=.00001):assert len(actual)==len(expected) and all(abs(float(a)-e)<=tolerance for a,e in zip(actual,expected)),(actual,expected)
for relative,record in provenance.items():
 path=K/'3dmodels'/relative
 assert path.is_file(),f'Missing {path}; run git lfs pull'
 assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],f'Model changed or LFS pointer not hydrated: {path}'
modeled=[];copper_jumpers=[]
for ref,f in fps.items():
 dnp='dnp' in one(f,'attr');models=children(f,'model')
 if dnp:assert not models,f'{ref} DNP model must not appear in assembled views'
 if dnp or ref=='U202':
  for pad in children(f,'pad'):assert not {'F.Paste','B.Paste'} & set(one(pad,'layers')[1:]),f'Customer/DNP part {ref} must not receive reflow paste'
 if ref.startswith('JP'):copper_jumpers.append(ref);continue
 if not dnp:assert models,f'Missing assembled 3D representation: {ref}'
 for model in models:
  assert model[1].startswith('${KIPRJMOD}/3dmodels/'),f'Nonportable model: {model[1]}'
  relative=model[1].split('/3dmodels/')[1];assert relative in provenance,relative
 if models:modeled.append(ref)

def pads(ref):return {p[1]:p for p in children(fps[ref],'pad') if p[1]}
def land(ref,number,xy,size):
 p=pads(ref)[number];bottom=one(fps[ref],'layer')[1]=='B.Cu';near(one(p,'at')[1:3],[xy[0],-xy[1] if bottom else xy[1]]);near(one(p,'size')[1:3],size)
for ref in [f'SW{i}' for i in range(501,509)]:
 assert fps[ref][1]=='ShieldSigner:XKB_TS1101_C_W_reflow'
 land(ref,'1',[-3.7,0],[1.2,1]);land(ref,'2',[3.7,0],[1.2,1])
for i,x in enumerate([-6.82,-4.28,-1.74,.8]):
 land('J601',f'C{i+1}',[x,-12.05],[1.2,1.9]);land('J601',f'C{i+5}',[x,12.05],[1.2,1.9])
land('J601','COM',[8.42,-5.75],[1.4,1.9]);land('J601','NO',[5.88,-5.75],[1.4,1.9])
for n,x,w in [('A5',-.5,.7),('B5',.5,.7),('A9',1.52,.8),('B9',-1.52,.8),('A12',2.75,.9),('B12',-2.75,.9)]:land('J301',n,[x,-3.18],[w,1.2])
for p in children(fps['J301'],'pad'):
 if p[1]=='S1':
  x,y=map(float,one(p,'at')[1:3]);assert abs(abs(x)-4.32)<.00001 and min(abs(y-2.7),abs(y+1.1))<.00001
  near(one(p,'size')[1:3],[1,1.7]);near(one(p,'drill')[2:],[.5,1.2])
assert fps['U601'][1]=='ShieldSigner:Microchip_SEC1210_QFN24_reflow'
for n in range(1,25):
 if n<=6:xy=[-2.325,-1.625+(n-1)*.65];size=[.65,.35]
 elif n<=12:xy=[-1.625+(n-7)*.65,2.325];size=[.35,.65]
 elif n<=18:xy=[2.325,1.625-(n-13)*.65];size=[.65,.35]
 else:xy=[1.625-(n-19)*.65,-2.325];size=[.35,.65]
 land('U601',str(n),xy,size)
near(one(pads('U601')['25'],'size')[1:3],[3.4,3.4])
windows=[p for p in children(fps['U601'],'pad') if p[1]==''];assert len(windows)==4
for p in windows:near(one(p,'size')[1:3],[1.37,1.37]);assert one(p,'layers')==['layers','B.Paste']
assert one(pads('J301')['A12'],'zone_connect')[-1]=='2','Reviewed USB ground plane connection lost'
for n,p in pads('J701').items():
 n=int(n);near(one(p,'at')[1:3],[17.78 if n<=20 else 0,(n-1 if n<=20 else 40-n)*2.54]);near(one(p,'drill')[1:],[1])
for ref,xy in zip(['H701','H702','H703','H704'],mechanical['display']['mountingCenters']):
 f=fps[ref];near(one(f,'at')[1:3],xy);assert 'board_only' in one(f,'attr');p=children(f,'pad')[0];near(one(p,'drill')[1:],[2.7])
# PCB edits and reusable library footprints must agree, so updating from libraries
# cannot silently restore the inherited hand-solder lands.
for ref in [*[f'SW{i}' for i in range(501,509)],'J301','J601','U601']:
 f=fps[ref];library=parse((K/'Footprints/ShieldSigner.pretty'/(f[1].split(':')[-1]+'.kicad_mod')).read_text());bottom=one(f,'layer')[1]=='B.Cu'
 for pad in children(f,'pad'):
  xy=list(map(float,one(pad,'at')[1:3]));target=[xy[0],-xy[1] if bottom else xy[1]]
  candidates=[p for p in children(library,'pad') if p[1]==pad[1] and all(abs(float(a)-b)<.00001 for a,b in zip(one(p,'at')[1:3],target))]
  assert len(candidates)==1,(ref,pad[1],target)
  near(one(candidates[0],'size')[1:3],list(map(float,one(pad,'size')[1:3])))
module=next(m for m in children(fps['J701'],'model') if 'Waveshare' in m[1]);near(one(one(module,'offset'),'xyz')[1:],mechanical['display']['modelOffset']);near(one(one(module,'rotate'),'xyz')[1:],mechanical['display']['modelRotation'])
host=next(m for m in children(fps['U202'],'model') if 'Luckfox-Pico-Mini' in m[1]);near(one(one(host,'offset'),'xyz')[1:],mechanical['luckfox']['moduleModelOffset'])
report={'modelsVerified':len(provenance),'assembledReferencesWithModels':modeled,'copperOnlyJumpers':copper_jumpers,'landPatterns':'XKB, SHOUHAN, Amphenol and Microchip recommended land dimensions asserted','displayMounts':'Four M2.5 clearance holes match manufacturer STEP','modelLimitations':['Card socket is a dimensional envelope, not detailed manufacturer CAD','Standoff model omits threads','Physical first-article header fit remains to be confirmed']}
(V/'mechanical-check-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

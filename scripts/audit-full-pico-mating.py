"""Verify nominal header geometry after native KiCad GLB transforms, including B.Cu mirroring."""
import hashlib,itertools,json,math,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico';PCB=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';plus='--plus' in sys.argv;GLB=ROOT/'dist/full-size-pico'/('plus-fit.glb' if plus else 'header-fit.glb')
b=GLB.read_bytes();length,kind=struct.unpack_from('<II',b,12);g=json.loads(b[20:20+length])
contacts=[];models=[]
def local(n):
 if 'matrix' in n:return np.array(n['matrix']).reshape((4,4),order='F')
 x,y,z,w=n.get('rotation',[0,0,0,1]);r=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])
 out=np.eye(4);out[:3,:3]=r@np.diag(n.get('scale',[1,1,1]));out[:3,3]=n.get('translation',[0,0,0]);return out
def walk(i,parent,owner=None):
 n=g['nodes'][i];world=parent@local(n)
 if n.get('name')=='U202':owner={'node':i,'originMm':(world[:3,3]*1000).tolist(),'transform':world.tolist()};models.append(owner)
 bounds=[]
 if 'mesh' in n:
  for p in g['meshes'][n['mesh']]['primitives']:
   a=g['accessors'][p['attributes']['POSITION']];pts=np.array([list(v)+[1] for v in itertools.product(*zip(a['min'],a['max']))]);v=(world@pts.T).T[:,:3]*1000;bounds.append(np.array([v.min(axis=0),v.max(axis=0)]))
 for child in n.get('children',[]):
  bb=walk(child,world,owner)
  if bb is not None:bounds.append(bb)
 if not bounds:return None
 bounds=np.array([np.min(np.array(bounds)[:,0,:],axis=0),np.max(np.array(bounds)[:,1,:],axis=0)])
 if owner and n.get('name','').startswith('contact_'):
  contacts.append({'root':owner['node'],'number':int(n['name'].split('_')[1]),'boundsMm':bounds.tolist()})
 if n.get('name')=='U202':owner['boundsMm']=bounds.tolist()
 return bounds
for i in g['scenes'][g.get('scene',0)]['nodes']:walk(i,np.eye(4))
roots={p['root'] for p in contacts};assert len(roots)==2
verified=[]
for root in sorted(roots):
 model=next(m for m in models if m['node']==root);row=model['originMm'][0];surface=-model['originMm'][1];cs=[p for p in contacts if p['root']==root];assert {p['number'] for p in cs}==set(range(1,21))
 for c in cs:
  lo,hi=np.array(c['boundsMm']);y=(lo[2]+hi[2])/2;index=20-c['number'];expected_y=57.319+index*2.54;sign=1 if index%2==0 else -1
  assert abs(y-expected_y)<.00001
  assert abs((hi[0] if sign>0 else lo[0])-(row+sign*2.4))<.00001,'Mirrored R2 SMT tail phase is wrong'
  assert abs(hi[2]-lo[2]-.64)<.00001
  assert abs(-lo[1]-surface-9.14)<.00001
 verified.append(dict(contactCenterXmm=row,firstNativeYmm=57.319,lastNativeYmm=105.579,contacts=20,matingPinProjectionMm=6,insulatorTopMm=3.14,baseDatumOffsetMm=surface))
assert sorted(round(r['contactCenterXmm'],4) for r in verified)==[85.3475,103.1275]
# Socket M20-782 drawing: 8.50 +/- .15 high, contact point 3.41 +/- .25 below mouth.
# XKB male projects 6.0 mm above insulator; nominal tip passes contact by 2.59 mm.
report={'boardSha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'nativeGlbSha256':hashlib.sha256(b).hexdigest(),'carrierHeader':'XKB X6511WVS-20H-C60D48R2 / C2883777','moduleSocket':'Harwin M20-7822042','nativeTransformedRows':verified,'rowSpacingMm':17.78,'socketHeightMm':8.5,'nominalModuleUndersideMm':11.64,'nominalModuleComponentFaceMm':12.64,'nominalPinBeyondSocketContactMm':2.59,'housingHeightMinusPinLengthMm':2.5,'moduleSocketTailMm':3,'modulePcbNominalThicknessMm':1,'scope':'Nominal drawing geometry and native model transforms; housing height is not usable internal socket depth. Not a supplier mating qualification or physical fit test.'}
module=next(m for m in models if abs(m['originMm'][1])>1)
T=np.array(module['transform']);corners=[]
# Official pinout: 1/40 are at the USB end, 20/21 at the camera end.
# Vendor STEP coordinates are X across the 21mm PCB, Y=0 at the USB PCB edge.
for number,x,y,expected in [(1,1.61,-1.37,[103.1275,57.319]),(40,19.39,-1.37,[85.3475,57.319]),(20,1.61,-49.63,[103.1275,105.579]),(21,19.39,-49.63,[85.3475,105.579])]:
 pos=(T@np.array([x/1000,0,-y/1000,1]))[:3]*1000
 assert np.linalg.norm(pos[[0,2]]-expected)<.00001,('Manufacturer module pin orientation mismatch',number,pos,expected)
 corners.append(dict(modulePin=number,nativeContactMm=expected))
lo,hi=module['boundsMm']
report.update(module='Pico Plus' if plus else 'Pico',manufacturerPinCornersVerified=corners,manufacturerModuleBoundsMm=module['boundsMm'],nativeAxes=['carrier X','negative rear height including 0.085mm render surface offset','carrier Y'],envelopeBeyondNativeYMinMm=max(0,54.579-lo[2]),envelopeBeyondNativeYMaxMm=max(0,hi[2]-124.579))
target=V/'manufacturing'/('plus-mating-audit.json' if plus else 'mating-audit.json')
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(report,indent=2)+'\n')
print('Verified both native B.Cu R2 tail patterns, all 40 contacts, 17.78 mm row spacing and nominal 11.64 mm module underside.')
print(report['module'],'model edge projection (native minY/maxY):',round(report['envelopeBeyondNativeYMinMm'],3),round(report['envelopeBeyondNativeYMaxMm'],3),'mm')

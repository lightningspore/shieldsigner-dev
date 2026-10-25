#!/usr/bin/env python3
"""Audit mating geometry from the exported assembly, not just declared offsets."""
import hashlib,json,runpy
from pathlib import Path
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/lcd-module-2.8'
source=ROOT/'dist/lcd-module-2.8/shieldsigner-modular-assembly.glb'
manifest=json.loads((ROOT/'assets/modular-downloads.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==next(a['sha256'] for a in manifest['assets'] if a['name']==source.name)
board=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
assert hashlib.sha256(board.read_bytes()).hexdigest()==manifest['boardSha256']
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one,children=sx['one'],sx['children'];tree=sx['parse'](board.read_text());fps={next(p[2] for p in children(f,'property') if p[1]=='Reference'):f for f in children(tree,'footprint')}
frame=np.array([[1000,0,0,-128],[0,0,-1000,89.579],[0,1000,0,-1.595],[0,0,0,1]])
scene=trimesh.load(source);groups={};gold={};housing={}
keys=['J701','J701_1','J701_2','U202','U202_1','U202_2','U202_3','U202_4','H701','H702','H703','H704']
for node in scene.graph.nodes_geometry:
 n=node;group='carrier_and_smt'
 while n is not None:
  if str(n) in keys:group=str(n);break
  n=scene.graph.transforms.parents.get(n)
 t,g=scene.graph[node];m=scene.geometry[g].copy();m.apply_transform(frame@t);groups.setdefault(group,[]).append(m)
 color=np.array(getattr(getattr(m.visual,'material',None),'baseColorFactor',[255]*4))[:3]
 if group in keys and color[0]>80 and color[0]>color[1]>color[2] and color[2]<100:gold.setdefault(group,[]).append(m.vertices)
 if group in keys and max(color)<30:housing.setdefault(group,[]).append(m.vertices)

def bounds(parts):
 v=np.vstack(parts);return np.array([v.min(axis=0),v.max(axis=0)])
def native_pins(ref,x):
 f=fps[ref];at=list(map(float,one(f,'at')[1:]));a=np.radians(at[2] if len(at)>2 else 0);out=[]
 for pad in children(f,'pad'):
  if not pad[1]:continue
  px,py=map(float,one(pad,'at')[1:3]);wx=at[0]+np.cos(a)*px+np.sin(a)*py;wy=at[1]-np.sin(a)*px+np.cos(a)*py
  if abs(wx-128-x)<.01:out.append([wx-128,89.579-wy])
 return np.array(sorted(out,key=lambda p:p[1]))
interfaces=[]
for name,female,male,ref,count in [('LCD','J701_1','J701_2','J701',8),('Luckfox row A','U202_1','U202_3','U202',11),('Luckfox row B','U202_2','U202_4','U202',11)]:
 fg=np.vstack(gold[female]);mg=np.vstack(gold[male]);fh=bounds(housing[female]);mh=bounds(housing[male]);expected=native_pins(ref,fg[:,0].mean());assert len(expected)==count
 errors=[]
 for pt in expected:
  centers=[]
  for vertices in [fg,mg]:
   v=vertices[np.abs(vertices[:,1]-pt[1])<1.0];assert len(v);centers.append((v[:,:2].min(axis=0)+v[:,:2].max(axis=0))/2)
  errors.append(max(float(np.linalg.norm(c-pt)) for c in centers))
 assert max(errors)<.001,(name,max(errors))
 pitch=np.diff(expected[:,1]);assert np.max(np.abs(pitch-2.54))<.001
 male_span=bounds([mg]);female_span=bounds([fg])
 if name=='LCD':gap=mh[0,2]-fh[1,2];insertion=fh[1,2]-male_span[0,2]
 else:gap=fh[0,2]-mh[1,2];insertion=male_span[1,2]-fh[0,2]
 assert gap>=-.001 and insertion>4,(name,gap,insertion)
 interfaces.append({'name':name,'pins':count,'pitchMm':2.54,'pinSpanMm':round(float(np.ptp(expected[:,1])),4),'maxModelToPadXYErrorMm':round(max(errors),7),'femaleHousingHeightMm':round(float(np.ptp(fh[:,2])),4),'maleInsulatorHeightMm':round(float(np.ptp(mh[:,2])),4),'housingGapMm':round(float(gap),4),'nominalInsertionMm':round(float(insertion),4),'femaleHousingZMm':fh[:,2].round(4).tolist(),'maleHousingZMm':mh[:,2].round(4).tolist(),'maleMetalZMm':male_span[:,2].round(4).tolist()})
all_vertices=np.vstack([m.vertices for ms in groups.values() for m in ms]);bb=bounds([all_vertices]);lcd=bounds([m.vertices for m in groups['J701']]);host=bounds([m.vertices for m in groups['U202']])
mounts=[]
for ref in ['H701','H702','H703','H704']:
 bbp=bounds([m.vertices for m in groups[ref]]);center=(bbp[0,:2]+bbp[1,:2])/2;assert abs(bbp[0,2])<.001 and abs(bbp[1,2]-12)<.001
 mounts.append({'reference':ref,'centerMm':center.round(4).tolist(),'supportHeightMm':12,'carrierHoleMm':2.7,'displayHoleMm':3.0})
assert abs(lcd[1,2]-17.7)<.001 and abs(host[0,2]+17.82)<.01
report={'boardSha256':manifest['boardSha256'],'sourceGlbSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'coordinateFrame':{'units':'mm','origin':'Carrier XY centre; carrier front component mounting plane Z=0','nativeStepTranslationMm':[-128,89.579,-1.595],'front':'+Z','rear':'-Z'},'interfaces':interfaces,'mounts':mounts,'nominalPcbMm':[160,70,1.6],'assemblyBoundsMm':bb.round(4).tolist(),'overallHeightMm':round(float(np.ptp(bb[:,2])),4),'lcdFrontZMm':17.7,'lcdPcbRearZMm':12,'lcdRearConnectorBottomZMm':6.8,'luckfoxRearZMm':round(float(host[0,2]),4),'baseInnerFloorZMm':-21,'luckfoxToFlatBaseFloorMm':round(float(host[0,2]+21),4),'displayToFlatFrontInnerPlaneMm':.9,'findings':[],'qualification':'Nominal CAD alignment only. Generic header models have no selected purchase MPN or verified contact-depth tolerance. LCD is a drawing-derived envelope; camera/cable dimensions remain assumptions. First physical fit required.','remaining':['Choose exact female/male header MPNs and verify insertion depth, post lengths and tolerances against manufacturer drawings.','Measure the purchased display: retained drawing total stack is 10.9 mm while product prose has also stated 7.7 mm.','Dry-fit 12 mm spacers, 8.5 mm sockets and both module headers before tightening the case.','Check solder fillets, cable bends, plug access, print shrinkage and real module revision.']}
(V/'assembly-fit-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'interfaces':interfaces,'overallHeightMm':report['overallHeightMm'],'luckfoxToFloorMm':report['luckfoxToFlatBaseFloorMm'],'findings':report['findings']},indent=2))

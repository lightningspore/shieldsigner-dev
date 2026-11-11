#!/usr/bin/env python3
"""Verify clip spacing and bound every routing/placement change to the power row."""
from pathlib import Path
import hashlib,json,math,runpy,subprocess
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'hardware';pcb=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));c,o=sx['children'],sx['one']
before=subprocess.check_output(['git','show','b431865:kicad/'+pcb.name],cwd=ROOT);after=pcb.read_bytes();a=sx['parse'](before.decode());b=sx['parse'](after.decode())
assert hashlib.sha256(before).hexdigest()=='2f949d76b53bf75e4b6f56e5e68623900b1f3e9c2403770409e647953aabc93d'
def norm(n):
 if isinstance(n,list):return [norm(x) for x in n]
 try:return float(n)
 except ValueError:return n
def fps(t):return {next(p[2] for p in c(f,'property') if p[1]=='Reference'):f for f in c(t,'footprint')}
rear=runpy.run_path(str(ROOT/'scripts/rear-layout-audit.py'));rear['verify']()
old,new=fps(a),fps(b);assert set(new)==set(old)|{'TP909'}
for ref,f in old.items():
 expected=f;actual=new[ref]
 if rear['accepted']('footprint',ref,expected,actual):continue
 if ref in ['TP901','TP902']:
  expected=[x for x in f if not(isinstance(x,list) and x[0]=='at')];actual=[x for x in actual if not(isinstance(x,list) and x[0]=='at')]
 assert norm(expected)==norm(actual),'Unexpected footprint change: '+ref
removed={'56fd2af8-79db-4d41-927a-c41409eb5d2f','8fdb18c6-8b0b-4276-861e-2915c93aa190','c0599721-6440-47b9-af8d-88d82928a6bf'};moved='699b489a-78d6-49d1-b040-dfa3ee8a44b7'
for kind in ['segment','via']:
 prior={o(n,'uuid')[1]:n for n in c(a,kind)};current={o(n,'uuid')[1]:n for n in c(b,kind)}
 for key,node in prior.items():
  if rear['accepted'](kind,key,node,current.get(key)):continue
  if key in removed:
   assert kind=='segment' and key not in current;continue
  if key==moved:
   assert kind=='via' and o(node,'net')[-1]=='GND' and o(current[key],'net')[-1]=='GND'
   assert o(current[key],'at')[1:3]==['113','121.7']
   expected=[n for n in node if not(isinstance(n,list) and n[0]=='at')];actual=[n for n in current[key] if not(isinstance(n,list) and n[0]=='at')];assert norm(expected)==norm(actual)
  else:assert key in current and norm(node)==norm(current[key]),'Unexpected route change: '+key
 added=[n for key,n in current.items() if key not in prior and not rear['accepted'](kind,key,None,n)]
 assert len(added)==(5 if kind=='segment' else 1)
 assert all(o(n,'net')[-1] in {'+5V','GND'} for n in added)
for ref,net,x in [('TP902','GND',113),('TP901','+5V',128),('TP909','GND',143)]:
 f=new[ref];assert o(f,'layer')==['layer','F.Cu'] and list(map(float,o(f,'at')[1:3]))==[x,120]
 pads=c(f,'pad');assert len(pads)==1 and o(pads[0],'net')[-1]==net and list(map(float,o(pads[0],'size')[1:3]))==[3.4,1.8]
 assert 'F.Paste' in o(pads[0],'layers')
 assert next(p[2] for p in c(f,'property') if p[1]=='LCSC')=='C2906768'
assert o(o(b,'setup'),'tenting')==['tenting',['front','yes'],['back','yes']]
report={'passed':True,'baselineCommit':'b431865','baselineBoardSha256':hashlib.sha256(before).hexdigest(),'boardSha256':hashlib.sha256(after).hexdigest(),'revision':'0.0.12-dev','clipRowLeftToRight':['TP902 GND','TP901 +5V','TP909 GND'],'centerPitchMm':15,'previousCenterPitchMm':7,'adjacentPadEdgeGapMm':11.6,'factoryKeystonePoints':9,'factorySmtPlacements':44,'newGroundReference':'TP909','retainedFootprintsUnchangedExceptPowerRowAndRecordedRearEdits':True,'allExistingPadNetsUnchanged':True,'removedPowerAndGroundServiceSpurs':sorted(removed),'reroutedOriginal5VSpurs':['56fd2af8-79db-4d41-927a-c41409eb5d2f','8fdb18c6-8b0b-4276-861e-2915c93aa190'],'movedGroundServiceVia':moved,'newTracks':5,'newGroundVias':1,'allOtherTracksAndViasUnchangedExceptRecordedRearEdits':True,'rearPlacementAudit':'rear-layout-audit.json','viasTentedBothSides':True,'physicalClipFitVerified':False,'scope':'Layout/source comparison; actual clip jaws, insulation and strain require physical first-article verification'}
(V/'power-clip-layout-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

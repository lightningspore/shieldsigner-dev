#!/usr/bin/env python3
"""Verify 0.0.13 routing geometry, preserved circuitry and the under-LCD 5 V header."""
from pathlib import Path
import hashlib,json,math,runpy,subprocess,sys,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];K=ROOT/'kicad';V=ROOT/'hardware';PCB=K/'SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));c,o,parse=sx['children'],sx['one'],sx['parse']
record=json.loads((ROOT/'docs/pcb-angle-header-edits.json').read_text())
before=subprocess.check_output(['git','show',record['baselineCommit']+':kicad/'+PCB.name],cwd=ROOT)
assert hashlib.sha256(before).hexdigest()==record['baselineBoardSha256']
a,b=parse(before.decode()),parse(PCB.read_text())
def norm(n):
 if isinstance(n,list):return [norm(x) for x in n]
 try:return float(n)
 except ValueError:return n
def fingerprint(n):return hashlib.sha256(json.dumps(norm(n),separators=(',',':')).encode()).hexdigest()
def nodes(tree,kind):return {o(n,'uuid')[1]:n for n in c(tree,kind)}
def fps(tree):return {next(p[2] for p in c(n,'property') if p[1]=='Reference'):n for n in c(tree,'footprint')}
old,new=fps(a),fps(b);assert set(new)==set(old)|{'J302'}
for ref in old:assert norm(old[ref])==norm(new[ref]),'Existing footprint changed: '+ref
assert norm(o(a,'setup'))==norm(o(b,'setup')),'Board rules changed'
assert subprocess.check_output(['git','show',record['baselineCommit']+':kicad/'+PCB.with_suffix('.kicad_pro').name],cwd=ROOT)==PCB.with_suffix('.kicad_pro').read_bytes(),'Project rules changed'
assert not c(b,'arc'),'Curved tracks need a separate style review'
prior,current=nodes(a,'segment'),nodes(b,'segment');owned=set()
for key,item in record['changedSegments'].items():
 original=prior[key];assert fingerprint(original)==item['beforeSha256']
 replacements=[current[i] for i in item['replacementIds']]
 assert [fingerprint(n) for n in replacements]==item['replacementSha256']
 assert math.dist(list(map(float,o(replacements[0],'start')[1:])),list(map(float,o(original,'start')[1:])))<=0.00000201
 expected_end=item.get('expectedEndAfterGroundViaMove',list(map(float,o(original,'end')[1:])))
 if 'expectedEndAfterGroundViaMove' in item:
  assert o(original,'net')[-1]=='GND' and key=='b0da8967-7ed5-4fd4-a009-cf5ccfc9081e'
  assert math.dist(list(map(float,o(original,'end')[1:])),record['movedGroundVia']['from'])<.002
  assert expected_end==record['movedGroundVia']['to']
 assert math.dist(list(map(float,o(replacements[-1],'end')[1:])),expected_end)<=0.00000201
 for left,right in zip(replacements,replacements[1:]):assert norm(o(left,'end')[1:])==norm(o(right,'start')[1:])
 for n in replacements:
  for field in ['width','net','layer']:assert norm(o(n,field))==norm(o(original,field)),f'{key}: {field} changed'
 owned.update(item['replacementIds'])
 assert key not in current
for key,node in prior.items():
 if key in record.get('removedZeroLengthSegmentIds',[]):
  assert norm(o(node,'start')[1:])==norm(o(node,'end')[1:]) and key not in current
 elif key in record.get('retiredGroundViaStubSegmentIds',[]):
  assert o(node,'net')[-1]=='GND' and math.dist(list(map(float,o(node,'start')[1:])),list(map(float,o(node,'end')[1:])))<.002 and key not in current
 elif key not in record['changedSegments']:assert norm(node)==norm(current[key]),'Unrecorded route change: '+key
for key,sha in record['headerTracks'].items():
 assert fingerprint(current[key])==sha and o(current[key],'net')[-1] in {'+5V','GND'}
assert set(current)==(set(prior)-set(record['changedSegments'])-set(record.get('removedZeroLengthSegmentIds',[]))-set(record.get('retiredGroundViaStubSegmentIds',[])))|owned|set(record['headerTracks'])
oldvias,newvias=nodes(a,'via'),nodes(b,'via')
assert set(newvias)==(set(oldvias)-set(record.get('removedStandaloneGroundViaIds',[])))|set(record['headerVias'])
for key,node in oldvias.items():
 if key in record.get('removedStandaloneGroundViaIds',[]):
  assert o(node,'net')[-1]=='GND'
  assert not any(math.dist(list(map(float,o(tr,end)[1:])),list(map(float,o(node,'at')[1:3])))<.000002 for tr in prior.values() for end in ['start','end'])
 elif key==record.get('movedGroundVia',{}).get('uuid'):
  import copy
  expected=copy.deepcopy(node);assert o(node,'net')[-1]=='GND' and list(map(float,o(node,'at')[1:3]))==record['movedGroundVia']['from']
  o(expected,'at')[1:3]=[str(v) for v in record['movedGroundVia']['to']]
  assert norm(expected)==norm(newvias[key])
 else:assert norm(node)==norm(newvias[key]),'Unrecorded via change: '+key
for key,sha in record['headerVias'].items():assert fingerprint(newvias[key])==sha and o(newvias[key],'net')[-1] in {'GND','+5V'}
# KiCad uses integer nanometres; permit only two nanometres of serialization rounding.
for key,node in current.items():
 start=list(map(float,o(node,'start')[1:]));end=list(map(float,o(node,'end')[1:]));dx=abs(start[0]-end[0]);dy=abs(start[1]-end[1])
 assert math.hypot(dx,dy)>0.000002,'Zero-length track: '+key
 assert min(dx,dy,abs(dx-dy))<=0.00000201,'Non-45-degree track: '+key
header=new['J302'];assert header[1]==record['header']['footprint'] and o(header,'layer')[1]=='F.Cu'
assert list(map(float,o(header,'at')[1:3]))==record['header']['positionMm']
assert float(o(header,'at')[3])==record['header']['rotationDeg']==180
assert {'exclude_from_bom','exclude_from_pos_files'}<=set(o(header,'attr')[1:])
assert {n[1]:o(n,'net')[-1] for n in c(header,'pad')}==record['header']['pinNets']
assert all(o(n,'drill')[1:] == ['1'] and o(n,'size')[1:]==['1.7','1.7'] for n in c(header,'pad'))
# Compare actual schematic pin partitions after projecting out the single added connector.
out=ROOT/'dist/lcd-module-2.8/angle-header-review';base=out/'baseline';base.mkdir(parents=True,exist_ok=True)
for path in K.glob('*.kicad_sch'):(base/path.name).write_bytes(subprocess.check_output(['git','show',record['baselineCommit']+':kicad/'+path.name],cwd=ROOT))
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
for label,folder in [('before',base),('after',K)]:subprocess.run([str(cli),'sch','export','netlist','--format','kicadxml','--output',str(out/(label+'.xml')),str(folder/PCB.with_suffix('.kicad_sch').name)],check=True,stdout=subprocess.DEVNULL)
def electrical(path):
 t=E.parse(path);parts={n.attrib['ref']:(n.findtext('value'),n.findtext('footprint')) for n in t.findall('./components/comp') if n.attrib['ref']!='J302'}
 nets=sorted(sorted((n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if n.attrib['ref']!='J302') for net in t.findall('./nets/net'))
 return parts,[n for n in nets if n]
assert electrical(out/'before.xml')==electrical(out/'after.xml'),'Existing schematic circuitry changed'
report={'passed':True,'revision':record['revision'],'boardSha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'baselineCommit':record['baselineCommit'],'replacedSegments':len(record['changedSegments']),'removedZeroLengthSegments':len(record['removedZeroLengthSegmentIds']),'tracksChecked':len(current),'allowedAnglesDegrees':[0,45,90,135,180,225,270,315],'coordinateToleranceNm':2,'existingFootprintsAndPadNetsUnchanged':True,'smartcardIcAndSocketUnchanged':True,'correctedComponentsUnchanged':['J301','J601','U601'],'signalTrackEndpointsNetsWidthsLayersPreserved':True,'groundViaClearanceChanges':{'removedStandalone':record['removedStandaloneGroundViaIds'],'moved':record['movedGroundVia']},'existingSignalViasUnchanged':True,'projectAndBoardRulesUnchanged':True,'schematicProjectedPinPartitionsUnchanged':True,'header':record['header'],'factoryPlacements':44,'catalogLines':18,'supplierPlacementReviewRequired':True,'qualification':'Source geometry and netlist checks; run native ERC/DRC separately. Battery module, cable fit, source isolation and powered operation are not qualified.'}
(V/'angle-header-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

config=V/'jlc-placement-corrections.json';d=json.loads(config.read_text());d['previousBoardSha256']=record['baselineBoardSha256'];d['boardSha256']=report['boardSha256'];d['serviceCompatibility']={'audit':'angle-header-audit.json','auditSha256':hashlib.sha256((V/'angle-header-audit.json').read_bytes()).hexdigest()};d['reviewed']='2026-11-11';d['qualification']='0.0.13 routing/header revision; all original footprints and pad nets unchanged, including corrected USB, socket and reader. Fresh supplier placement/DFM review required.';d['uploadedCsvPreviewChecked']=False;d['reviewStatus']='review_required';config.write_text(json.dumps(d,indent=2)+'\n')

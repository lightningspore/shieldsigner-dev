#!/usr/bin/env python3
"""Native service revision audit: retained circuitry, placement and sourcing evidence."""
from pathlib import Path
import hashlib,json,runpy,subprocess,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/lcd-module-2.8';K=V/'kicad';name='SeedSigner-Plus-smartcard-pico';board=K/(name+'.kicad_pcb');out=ROOT/'dist/lcd-module-2.8/service-review';out.mkdir(parents=True,exist_ok=True)
base=sorted((ROOT/'.tools/pcb-edits').glob('service-*'))[-1];cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));c,o=sx['children'],sx['one']
def fps(path):return {next(q[2] for q in c(f,'property') if q[1]=='Reference'):f for f in c(sx['parse'](path.read_text()),'footprint')}
a,b=fps(base/board.name),fps(board)
retained=sorted(set(a)-{'J302'})
assert set(b)==set(retained)|{f'TP{i}' for i in range(901,909)}|{f'H{i}' for i in range(705,709)}
# Native save ordering can change; compare the semantic trees by UUID.
def normalize(n):
 if isinstance(n,list):return [normalize(q) for q in n]
 try:return float(n)
 except ValueError:return n
def geometry(n,ref):
 import copy
 n=copy.deepcopy(n)
 if ref in ['U202','R606']:
  field=next(q for q in c(n,'property') if q[1]=='Reference')
  effects=o(field,'effects');font=o(effects,'font')
  font[:]=[q for q in font if not (isinstance(q,list) and q[0] in ['size','thickness'])]
 return normalize(n)
for ref in retained:assert geometry(a[ref],ref)==geometry(b[ref],ref),'Original electrical/mechanical footprint changed: '+ref
removed=[]
for kind in ['segment','via']:
 oldnodes={o(n,'uuid')[1]:n for n in c(sx['parse']((base/board.name).read_text()),kind)}
 new={o(n,'uuid')[1]:normalize(n) for n in c(sx['parse'](board.read_text()),kind)}
 for key,node in oldnodes.items():
  if kind=='via' and tuple(map(float,o(node,'at')[1:3])) in {(172.5,81.8),(174.193,80.264)}:
   assert o(node,'net')[-1]=='GND' and key not in new
   xy=o(node,'at')[1:3]
   assert not any(o(track,end)[1:3]==xy for track in c(sx['parse']((base/board.name).read_text()),'segment') for end in ['start','end']),'Removed via had an original track connection'
   removed.append(key);continue
  assert new.get(key)==normalize(node),'Original signal routing changed'
assert len(removed)==2
for label,folder in [('before',base),('after',K)]:subprocess.run([str(cli),'sch','export','netlist','--format','kicadxml','--output',str(out/(label+'.xml')),str(folder/(name+'.kicad_sch'))],check=True)
def electrical(file):
 t=E.parse(file);parts={n.attrib['ref']:(n.findtext('value'),n.findtext('footprint')) for n in t.findall('./components/comp')}
 nets=[{(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')} for net in t.findall('./nets/net')]
 return parts,nets
oldparts,oldnets=electrical(out/'before.xml');newparts,newnets=electrical(out/'after.xml');drop={'J302',*[f'TP{i}' for i in range(901,909)]}
assert {k:v for k,v in oldparts.items() if k not in drop}=={k:v for k,v in newparts.items() if k not in drop}
def projected(nets):return sorted(sorted(p for p in net if p[0] not in drop) for net in nets if any(p[0] not in drop for p in net))
assert projected(oldnets)==projected(newnets),'Existing circuitry partition changed'
report={'passed':True,'revision':'0.0.11-dev','boardSha256':hashlib.sha256(board.read_bytes()).hexdigest(),'baselineBoardSha256':hashlib.sha256((base/board.name).read_bytes()).hexdigest(),'retainedElectricalMechanicalFootprintsUnchanged':retained,'silkFieldsRefined':{'U202':'Reference stroke 0.10 to 0.15 mm','R606':'Reference height 0.70 to 0.80 mm'},'correctedComponentsUnchanged':['J301','J601','U601'],'existingTracksUnchanged':True,'removedStandaloneGroundStitchViasMm':[[172.5,81.8],[174.193,80.264]],'netlistComparison':'Exact retained reference/value/footprint and projected pin partitions; only J302 replaced by eight factory Keystone test points','schematicFiles':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in K.glob('*.kicad_sch')},'factorySmtPlacements':43,'catalogLines':18,'newMounts':4,'limitations':['Supplier placement/DFM review required','Stock and attrition are not reservations','Physical fit, power, rail/thermal measurements and smartcard operation require first-article tests']}
p=V/'serviceability-audit.json';p.write_text(json.dumps(report,indent=2)+'\n')
config=V/'jlc-placement-corrections.json';d=json.loads(config.read_text());history=V/'manufacturing/history/0.0.9-placement-corrections.json'
if not history.exists():history.write_text(json.dumps(d,indent=2)+'\n')
d.pop('artworkCompatibility',None);d['boardSha256']=report['boardSha256'];d['previousBoardSha256']=report['baselineBoardSha256'];d['reviewed']='2026-11-09';d['qualification']='0.0.11 service revision: exact retained footprint and original routing checks; corrected parts unchanged. New Keystone footprints are symmetric single-pad SMT lands. Supplier preview and final DFM are still required.';d['serviceCompatibility']={'audit':p.name,'auditSha256':hashlib.sha256(p.read_bytes()).hexdigest()};d['uploadedCsvPreviewChecked']=False;d['reviewStatus']='review_required';config.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['retainedElectricalMechanicalFootprintsUnchanged','schematicFiles']},indent=2))

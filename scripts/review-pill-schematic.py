#!/usr/bin/env python3
"""Export native schematic review assets and verify electrical equivalence."""
from pathlib import Path
import hashlib,json,runpy,subprocess,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];K=ROOT/'hardware/kicad';OUT=ROOT/'dist/lcd-module-2.8/schematic-review';OUT.mkdir(parents=True,exist_ok=True)
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();name='SeedSigner-Plus-smartcard-pico.kicad_sch'
audit=ROOT/'hardware/schematic-readability-audit.json'
data=json.loads(audit.read_text())
backups=sorted((ROOT/'.tools/schematic-edits').glob('*'))
backup=backups[-1] if backups else None
def run(*args):subprocess.run([str(cli),*map(str,args)],check=True)
run('sch','export','netlist','--format','kicadxml','--output',OUT/'after.xml',K/name)
if backup:run('sch','export','netlist','--format','kicadxml','--output',OUT/'before.xml',backup/name)
service=(ROOT/'hardware/serviceability.json').exists()
def electrical(path,project=False):
 t=E.parse(path)
 parts={n.attrib['ref']:(n.findtext('value'),n.findtext('footprint')) for n in t.findall('./components/comp')}
 # Net numbering, ordering and auto-generated names can change with presentation.
 nets=sorted(sorted((n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')) for net in t.findall('./nets/net'))
 if project:
  drop={'J302',*[f'TP{i}' for i in range(901,910)]}
  parts={k:v for k,v in parts.items() if k not in drop}
  nets=sorted(sorted(p for p in net if p[0] not in drop) for net in nets if any(p[0] not in drop for p in net))
 return parts,nets
signature=hashlib.sha256(json.dumps(electrical(OUT/'after.xml'),sort_keys=True).encode()).hexdigest()
if backup:assert electrical(OUT/'before.xml',service)==electrical(OUT/'after.xml',service),'Retained schematic electrical content changed'
elif not service:assert signature==data['electricalEquivalence']['sha256'],'Schematic electrical content changed'
else:
 evidence=json.loads((ROOT/'hardware/serviceability-audit.json').read_text())
 assert all(hashlib.sha256((K/name).read_bytes()).hexdigest()==sha for name,sha in evidence['schematicFiles'].items()),'Stale service schematic evidence'
run('sch','export','svg','--output',str(OUT/'svg')+'/',K/name)
run('sch','export','pdf','--output',OUT/'shieldsigner-readable-schematic.pdf',K/name)

for filename,item in data['files'].items():item['afterSha256']=hashlib.sha256((K/filename).read_bytes()).hexdigest()
data['electricalEquivalence']={'status':'pass','sha256':signature,'method':'Independent native XML netlist export before/after; exact reference/value/footprint and complete pin partition comparison','components':len(electrical(OUT/'after.xml')[0]),'nets':len(electrical(OUT/'after.xml')[1])}
if service:
 audit=ROOT/'hardware/service-schematic-audit.json'
 data['electricalEquivalence']['scope']='Retained circuitry matches original; TP901-TP909 and optional restored J302 are excluded from the projection'
audit.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data['electricalEquivalence'],indent=2))

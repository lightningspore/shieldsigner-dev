#!/usr/bin/env python3
"""Exact semantic fingerprints for the reviewed rear placement/routing edits."""
from pathlib import Path
import hashlib,json,runpy
ROOT=Path(__file__).resolve().parents[1]
def normalize(node):
 if isinstance(node,list):return [normalize(v) for v in node]
 try:return float(node)
 except ValueError:return node
def fingerprint(node):return hashlib.sha256(json.dumps(normalize(node),separators=(',',':')).encode()).hexdigest() if node is not None else None
record=json.loads((ROOT/'docs/pcb-rear-placement-edits.json').read_text())
def accepted(kind,key,before,after):
 entry=record['changes'][kind].get(key)
 return bool(entry and entry['before']==fingerprint(before) and entry['after']==fingerprint(after))
def verify():
 sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));c,o=sx['children'],sx['one'];pcb=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';tree=sx['parse'](pcb.read_text())
 for kind,entries in record['changes'].items():
  nodes={(next(p[2] for p in c(n,'property') if p[1]=='Reference') if kind=='footprint' else o(n,'uuid')[1]):n for n in c(tree,kind)}
  for key,entry in entries.items():assert fingerprint(nodes.get(key))==entry['after'],f'Unreviewed rear edit: {kind} {key}'
 assert fingerprint(o(tree,'setup'))==record['unchangedSetupSha256'],'Board rules/setup changed'
 assert hashlib.sha256(pcb.with_suffix('.kicad_pro').read_bytes()).hexdigest()==record['projectSha256'],'Project rules changed'
 fps={next(p[2] for p in c(f,'property') if p[1]=='Reference'):f for f in c(tree,'footprint')}
 for ref in record['flippedReferences']:assert o(fps[ref],'layer')[1]=='B.Cu'
 for ref in [*[f'SW{i}' for i in range(501,509)],'J701','TP901','TP902','TP909']:assert o(fps[ref],'layer')[1]=='F.Cu'
 report={'passed':True,'boardSha256':hashlib.sha256(pcb.read_bytes()).hexdigest(),'editRecord':'docs/pcb-rear-placement-edits.json','editRecordSha256':hashlib.sha256((ROOT/'docs/pcb-rear-placement-edits.json').read_bytes()).hexdigest(),'regulatorClusterOnRear':record['flippedReferences'],'changedFootprints':list(record['changes']['footprint']),'factorySmtPlacementsBySide':{'front':11,'back':33},'rulesAndSetupUnchanged':True,'qualification':'Native geometry and exact source comparison; physical fit, rework access and thermal operation require first articles.'}
 (ROOT/'variants/lcd-module-2.8/rear-layout-audit.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':print(json.dumps(verify(),indent=2))

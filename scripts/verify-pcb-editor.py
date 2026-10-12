#!/usr/bin/env python3
"""Integration checks: accepted no-op and rejected copper overlap preserve the project."""
import hashlib,importlib.util,json,math,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('sexpr',ROOT/'scripts/kicad-sexpr.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
pcb=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';pro=pcb.with_suffix('.kicad_pro')
original={pcb:pcb.read_bytes(),pro:pro.read_bytes()}
tree=s.parse(pcb.read_text())
fps={next(x[2] for x in s.children(f,'property') if x[1]=='Reference'):f for f in s.children(tree,'footprint')}
temp=ROOT/'.tools/editor-tests';temp.mkdir(parents=True,exist_ok=True)
def run(recipe):
 path=temp/'recipe.json';path.write_text(json.dumps(recipe))
 return subprocess.run([sys.executable,str(ROOT/'scripts/pcb-edit.py'),str(path)],capture_output=True,text=True)
try:
 # Valid idempotent text edit exercises save/load, project-library resolution and DRC gating.
 reference=next(x for x in s.children(fps['D301'],'property') if x[1]=='Reference')
 uid=s.one(reference,'uuid')[1];local=[float(x) for x in s.one(reference,'at')[1:3]]
 placement=[float(x) for x in s.one(fps['D301'],'at')[1:]];angle=math.radians(placement[2] if len(placement)>2 else 0)
 at=[placement[0]+local[0]*math.cos(angle)+local[1]*math.sin(angle),placement[1]-local[0]*math.sin(angle)+local[1]*math.cos(angle)]
 accepted=run({'edits':[{'action':'text-position','uuid':uid,'position':at}]})
 assert accepted.returncode==0,accepted.stderr
 assert pcb.read_bytes()==original[pcb] and pro.read_bytes()==original[pro],'No-op changed project bytes'
 old=[float(x) for x in s.one(fps['C301'],'at')[1:3]];target=[float(x) for x in s.one(fps['C302'],'at')[1:3]]
 rejected=run({'edits':[{'action':'move','ref':'C301','from':old,'delta':[b-a for a,b in zip(old,target)]}]})
 assert rejected.returncode!=0 and 'Candidate introduces DRC issues' in rejected.stderr,rejected.stderr
 assert pcb.read_bytes()==original[pcb] and pro.read_bytes()==original[pro],'Rejected edit changed project bytes'
 stale=run({'edits':[{'action':'move','ref':'C301','from':[0,0],'delta':[1,1]}]})
 assert stale.returncode!=0 and 'recipe not replayed' in stale.stderr
 assert pcb.read_bytes()==original[pcb] and pro.read_bytes()==original[pro]
 # A DRC exception must not hide an invalid assembly population.
 text=original[pcb].decode()
 a,b,block=next((a,b,v) for a,b,v in s.expressions(text) if v.startswith('(footprint ') and '(property "Reference" "R404"' in v)
 assert '(attr smd exclude_from_bom dnp)' in block
 pcb.write_text(text[:a]+block.replace('(attr smd exclude_from_bom dnp)','(attr smd exclude_from_bom)',1)+text[b:])
 population=subprocess.run([sys.executable,str(ROOT/'scripts/kicad.py'),'check'],capture_output=True,text=True)
 assert population.returncode!=0 and 'Invalid DNP exception: R404' in population.stderr,population.stderr
 pcb.write_bytes(original[pcb])
 result={'validNoOpAccepted':True,'newCopperOverlapRejected':True,'staleMoveRejected':True,'invalidDnpPopulationRejected':True,'boardAndProjectBytesPreserved':True,'pcbSha256':hashlib.sha256(original[pcb]).hexdigest()}
 (ROOT/'dist/kicad/editor-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
finally:
 for path,data in original.items():
  if path.read_bytes()!=data:path.write_bytes(data)

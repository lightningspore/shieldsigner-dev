"""Rip up only copper conflicting with the new module lands, retaining evidence."""
import hashlib,json,runpy,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'))
OUT=ROOT/'dist/full-size-pico';PCB=ROOT/'variants/full-size-pico/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
removed={}
for iteration in range(6):
    report=OUT/f'drc-prune-{iteration}.json'
    subprocess.run([str(cli),'pcb','drc','--refill-zones','--schematic-parity','--severity-all','--format','json','--output',str(report),str(PCB)],check=True,stdout=subprocess.DEVNULL)
    d=json.loads(report.read_text());text=PCB.read_text();tree=sx['parse'](text)
    host=next(f for f in sx['children'](tree,'footprint') if any(p[1:3]==['Reference','U202'] for p in sx['children'](f,'property')))
    changed=[f for f in sx['children'](tree,'footprint') if any(p[1]=='Reference' and p[2] in {'U202','C701','JP701','JP702'} for p in sx['children'](f,'property'))]
    newpads={sx['one'](p,'uuid')[1] for f in changed for p in sx['children'](f,'pad')}
    copper={sx['one'](n,'uuid')[1]:n for n in tree if isinstance(n,list) and n[0] in {'segment','via'}}
    drop={key for key,n in copper.items() if sx['one'](n,'net')[-1]=='unconnected-(U202-1V8(OUT)-Pad22)'}
    for issue in d['violations']:
        if any(i['uuid'] in newpads for i in issue['items']):
            drop.update(i['uuid'] for i in issue['items'] if i['uuid'] in copper)
    if not drop:
        (OUT/'drc-pruned.json').write_text(report.read_text());break
    spans=[]
    for a,z,raw in sx['expressions'](text):
        if not raw.startswith(('(segment','(via')):continue
        node=sx['parse'](raw)
        if node[0] not in {'segment','via'}:continue
        key=sx['one'](node,'uuid')[1]
        if key in drop:
            spans.append((a,z));removed[key]=dict(kind=node[0],net=sx['one'](node,'net')[-1],sha256=hashlib.sha256(raw.encode()).hexdigest())
    for a,z in sorted(spans,reverse=True):text=text[:a]+text[z:]
    PCB.write_text(text)
    print('Local rip-up pass',iteration+1,':',len(drop),'copper items',flush=True)
(OUT/'local-ripup.json').write_text(json.dumps(removed,indent=2)+'\n')
print('Remaining native findings:',{k:sum(v['type']==k for v in d['violations']) for k in {v['type'] for v in d['violations']}},'unconnected',len(d.get('unconnected_items',[])))

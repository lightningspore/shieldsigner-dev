"""Remove native-DRC-identified open-ended copper left by the Mini replacement."""
import json,runpy,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/full-size-pico'
PCB=ROOT/'variants/full-size-pico/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'))
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
removed=[]
for iteration in range(20):
 report=OUT/'drc-pruned.json'
 subprocess.run([str(cli),'pcb','drc','--refill-zones','--schematic-parity','--severity-all','--format','json','--output',str(report),str(PCB)],check=True,stdout=subprocess.DEVNULL)
 d=json.loads(report.read_text())
 drop={item['uuid'] for issue in d['violations'] if issue['type'] in {'track_dangling','via_dangling'} for item in issue['items']}
 if not drop:break
 text=PCB.read_text();spans=[]
 for a,z,raw in sx['expressions'](text):
  if not raw.startswith(('(segment','(via')):continue
  node=sx['parse'](raw)
  if node[0] not in {'segment','via'}:continue
  key=sx['one'](node,'uuid')[1]
  if key in drop:spans.append((a,z));removed.append(key)
 for a,z in sorted(spans,reverse=True):text=text[:a]+text[z:]
 assert spans,'Dangling report did not identify removable copper'
 PCB.write_text(text)
 print('Removed',len(spans),'dangling copper items',flush=True)
(OUT/'dangling-cleanup.json').write_text(json.dumps({'removed':removed},indent=2)+'\n')
print('Remaining findings',len(d['violations']),'unconnected',len(d['unconnected_items']))

"""Rebuild the ten-board prototype review kit; no purchase or external publication."""
import csv,datetime,hashlib,json,runpy,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico';K=V/'kicad';PCB=K/'SeedSigner-Plus-smartcard-pico.kicad_pcb';M=V/'manufacturing';OUT=ROOT/'dist/full-size-pico';P=OUT/'prototype';sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):subprocess.run(list(map(str,args)),cwd=ROOT,check=True)
run(['uv','run','python','scripts/refresh-jlc.py','--pico-full'])
run(['uv','run','python','scripts/manufacture-full-pico.py'])
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();native=cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'
assert native.exists(),'Native pcbnew Python is required for drill export review'
run([native,'scripts/dump-full-pico-drills.py'])
run(['uv','run','--with','gerbonara==1.6.3','python','scripts/check-full-pico-gerbers.py'])
run(['uv','run','python','scripts/draw-full-pico-assembly.py'])
run(['bun','scripts/render-full-pico-gerbers.mjs'])
run([cli,'pcb','export','glb','--force','--component-filter','U202','--no-board-body','--output',OUT/'header-fit.glb',PCB])
run(['uv','run','--python','3.11','--with','numpy','python','scripts/audit-full-pico-mating.py'])
base=PCB.read_text().replace('${KIPRJMOD}',str(K));plus=base
for a,z,raw in list(sx['expressions'](plus))[::-1]:
 if raw.startswith('(model ') and 'Luckfox-Pico' in raw:
  replacement=raw.replace('(hide yes)','') if 'Luckfox-Pico-Plus.step' in raw else raw.replace('(offset','(hide yes) (offset',1)
  plus=plus[:a]+replacement+plus[z:]
plus_path=OUT/'plus-preview.kicad_pcb';plus_path.write_text(plus)
run([cli,'pcb','export','glb','--force','--component-filter','U202','--no-board-body','--output',OUT/'plus-fit.glb',plus_path])
run(['uv','run','--python','3.11','--with','numpy','python','scripts/audit-full-pico-mating.py','--plus'])
# Supplier view contains only the 46 physical placements; module/socket models
# are shown separately for customer assembly and are never added to the CPL.
factory=set()
for row in csv.DictReader((M/'bom-jlcpcb.csv').open()):factory.update(row['Designator'].split(','))
factory_board=base
for a,z,raw in list(sx['expressions'](factory_board))[::-1]:
 if not raw.startswith('(footprint '):continue
 node=sx['parse'](raw);ref=next(p[2] for p in sx['children'](node,'property') if p[1]=='Reference');replacement=raw
 for i,j,model in list(sx['expressions'](replacement))[::-1]:
  if not model.startswith('(model '):continue
  keep=(ref in factory) or (ref=='U202' and 'XKB-SMT-male-nominal.step' in model)
  if not keep and '(hide yes)' not in model:replacement=replacement[:i]+model.replace('(offset','(hide yes) (offset',1)+replacement[j:]
 factory_board=factory_board[:a]+replacement+factory_board[z:]
factory_path=OUT/'factory-preview.kicad_pcb';factory_path.write_text(factory_board)
for source,side,name in [(factory_path,'bottom','assembly-factory-back.png'),(factory_path,'top','assembly-factory-front.png'),(PCB,'bottom','assembly-with-pico.png'),(plus_path,'bottom','assembly-with-plus.png')]:
 run([cli,'pcb','render','--output',M/name,'--side',side,'--rotate','340,0,0','--width','1600','--height','900','--background','opaque','--quality','high',source])
run([cli,'sch','export','pdf','--output',M/'shieldsigner-full-pico-schematic.pdf',PCB.with_suffix('.kicad_sch')])
run(['bun','scripts/build-full-pico.tsx'])
receipts={}
for check in ['shorts','pcb-style']:
 result=subprocess.run(['bunx','tsci','check',check,str(OUT/'experimental/full-pico.circuit.json')],cwd=ROOT,capture_output=True,text=True,check=True)
 (P/f'{check}-check.txt').write_text(result.stdout+result.stderr);receipts[check]={'exitCode':result.returncode,'outputSha256':sha(P/f'{check}-check.txt')};print(result.stdout,flush=True)
board_sha=sha(PCB);receipt=dict(boardSha256=board_sha,circuitJsonSha256=sha(OUT/'experimental/full-pico.circuit.json'),checks=receipts)
(M/'experimental-checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
manifest=json.loads((M/'manifest.json').read_text());assert manifest['boardSha256']==board_sha
for name in ['gerber-audit.json','mating-audit.json','plus-mating-audit.json','header-placement-map.json','experimental-checks.json']:assert json.loads((M/name).read_text())['boardSha256']==board_sha
mating=json.loads((M/'plus-mating-audit.json').read_text());meta=json.loads((V/'source.json').read_text());meta.update(boardSha256=board_sha,nominalPlusPortProjectionMm=round(mating['envelopeBeyondNativeYMaxMm'],3),nominalModels={p.name:sha(p) for p in (V/'models').glob('*nominal.step')});(V/'source.json').write_text(json.dumps(meta,indent=2)+'\n')
summary=json.loads((OUT/'checks-summary.json').read_text());state={'status':'prototype_files_prepared_jlc_procurement_and_approval_pending','quantity':10,'boardSha256':board_sha,'mainBoardUnchanged':sha(ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb')==meta['mainBoardSha256'],'nativeChecks':summary,'mounting':meta['mounting'],'mechanicalChanges':json.loads((V/'local-placement.json').read_text()),'newHeaderStandardStock':manifest['headers']['standardStock'],'newHeadersInstalled':20,'stockBlockers':manifest['stockBlockers'],'nominalModuleUndersideMm':11.64,'plusEnvelopeBeyondEdgeMm':meta['nominalPlusPortProjectionMm'],'factoryPlacementPreviewApproved':False,'factoryPanelAndDfmApproved':False,'assemblyCheckoutReady':False,'qualification':'Digital prototype review only; physical mating, enclosure/cables, assembly process and powered firmware are unqualified.'}
(V/'study-status.json').write_text(json.dumps(state,indent=2)+'\n')
run(['uv','run','python','scripts/package-full-pico.py'])

#!/usr/bin/env python3
"""Validate/export the isolated eight-pin pill carrier before prototype quotation."""
import collections,csv,hashlib,json,runpy,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
config=runpy.run_path(str(ROOT/'scripts/kicad.py'));cli=config['cli']()
folder=ROOT/'variants/lcd-module-2.8';board=folder/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';out=ROOT/'dist/lcd-module-2.8';out.mkdir(parents=True,exist_ok=True)
for args in [['sch','erc','--format','json','--severity-all','--output',out/'erc.json',board.with_suffix('.kicad_sch')],['pcb','drc','--format','json','--schematic-parity','--severity-all','--refill-zones','--output',out/'drc.json',board]]:
 subprocess.run([str(cli),*[str(v) for v in args]],check=True)
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));tree=sx['parse'](board.read_text());fps={next(x[2] for x in sx['children'](f,'property') if x[1]=='Reference'):f for f in sx['children'](tree,'footprint')}
manifest=json.loads((folder/'header-map.json').read_text())
for ref in manifest['dnp']: assert 'dnp' in sx['one'](fps[ref],'attr'),ref+' must remain DNP'
# Assert the exact purchased-module pinout independently of schematic/PCB parity.
expected={'1':'RPI_BACKLIGHT','2':'LCD_RST','3':'LCD_DC','4':'RPI_SPI_CS','5':'LCD_SCLK','6':'LCD_MOSI','7':'GND','8':'LCD_3V3'}
pads=sx['children'](fps['J701'],'pad')
assert len(pads)==8
for pad in pads:
 assert sx['one'](pad,'net')[-1]==expected[pad[1]],(pad[1],sx['one'](pad,'net'))
assert not set(manifest['removedFromPcb']) & set(fps),'Old bare-panel/Pico-era lands returned'
for ref,nets in {'U701':{'1':'+5V','2':'GND','3':'+5V','5':'LCD_3V3'},'C701':{'1':'+5V','2':'GND'},'C702':{'1':'LCD_3V3','2':'GND'}}.items():
 for pad in sx['children'](fps[ref],'pad'):
  if pad[1] in nets:assert sx['one'](pad,'net')[-1]==nets[pad[1]],(ref,pad[1])

drc=json.loads((out/'drc.json').read_text())
assert not any(issue.get('excluded') for issue in drc['violations']),'Pill carrier has no permitted DRC exclusions'

summary={'boardSha256':hashlib.sha256(board.read_bytes()).hexdigest(),'qualification':'Development layout; not manufacturing or mechanical sign-off','checks':{}}
for kind in ['erc','drc']:
 j=json.loads((out/f'{kind}.json').read_text());allitems=j.get('violations',[])+[v for sh in j.get('sheets',[]) for v in sh['violations']];active=[v for v in allitems if not v.get('excluded')]
 summary['checks'][kind]={'active':dict(collections.Counter(v['severity'] for v in active)),'excluded':sum(bool(v.get('excluded')) for v in allitems),'unconnected':len(j.get('unconnected_items',[])),'parity':len(j.get('schematic_parity',[]))}
(folder/'check-results.json').write_text(json.dumps(summary,indent=2)+'\n')
for side,layers in [('top','F.Cu,F.SilkS,Edge.Cuts,Dwgs.User'),('bottom','B.Cu,B.SilkS,Edge.Cuts')]:
 subprocess.run([str(cli),'pcb','export','svg','--layers',layers,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--output',str(folder/f'pcb-{side}.svg'),str(board)],check=True)
print(json.dumps(summary,indent=2))
if any(v['active'].get('error',0) or v['active'].get('warning',0) or v['unconnected'] or v['parity'] for v in summary['checks'].values()):sys.exit(1)

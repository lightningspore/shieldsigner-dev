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
assert [n[1] for n in sx['one'](tree,'layers')[1:] if isinstance(n,list) and n[1].endswith('.Cu')]==['F.Cu','In1.Cu','In2.Cu','B.Cu']
for layer in ['In1.Cu','In2.Cu']:
 planes=[z for z in sx['children'](tree,'zone') if sx['one'](z,'layer')==['layer',layer]]
 assert len(planes)==1 and sx['one'](planes[0],'net')[-1]=='GND'
 assert sx['children'](planes[0],'filled_polygon'),layer+' plane must be filled'
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

# Factory-assembled power/test points replace the optional header.
service=json.loads((folder/'serviceability.json').read_text())
assert 'J302' not in fps
for point in service['testpoints']:
 f=fps[point['ref']];props={q[1]:q[2] for q in sx['children'](f,'property')}
 assert f[1]==service['part']['footprint']
 assert props['LCSC']=='C2906768' and props['MPN']=='5015'
 assert 'exclude_from_bom' not in sx['one'](f,'attr')
 assert sx['one'](sx['children'](f,'pad')[0],'net')[-1]==point['net']
 assert any('Paste' in layer for layer in sx['one'](sx['children'](f,'pad')[0],'layers')[1:])
assert next(p[2] for p in sx['children'](fps['J301'],'property') if p[1]=='MPN')=='USB4125-GF-A-0190'
drc=json.loads((out/'drc.json').read_text())
assert not any(issue.get('excluded') for issue in drc['violations']),'Pill carrier has no permitted DRC exclusions'

summary={'boardSha256':hashlib.sha256(board.read_bytes()).hexdigest(),'qualification':'Development layout; not manufacturing or mechanical sign-off','checks':{}}
for kind in ['erc','drc']:
 j=json.loads((out/f'{kind}.json').read_text());allitems=j.get('violations',[])+[v for sh in j.get('sheets',[]) for v in sh['violations']];active=[v for v in allitems if not v.get('excluded')]
 summary['checks'][kind]={'active':dict(collections.Counter(v['severity'] for v in active)),'excluded':sum(bool(v.get('excluded')) for v in allitems),'unconnected':len(j.get('unconnected_items',[])),'parity':len(j.get('schematic_parity',[]))}
(folder/'check-results.json').write_text(json.dumps(summary,indent=2)+'\n')
for side,layers in [('top','F.Cu,F.SilkS,Edge.Cuts,Dwgs.User'),('bottom','B.Cu,B.SilkS,Edge.Cuts')]:
 subprocess.run([str(cli),'pcb','export','svg','--layers',layers,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet',*(['--mirror'] if side=='bottom' else []),'--output',str(folder/f'pcb-{side}.svg'),str(board)],check=True)
for side in ['top','bottom']:
 path=folder/f'pcb-{side}.svg';path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
print(json.dumps(summary,indent=2))
if any(v['active'].get('error',0) or v['active'].get('warning',0) or v['unconnected'] or v['parity'] for v in summary['checks'].values()):sys.exit(1)

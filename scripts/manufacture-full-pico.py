"""Build a source-pinned ten-board prototype quotation kit for the full-size Pico."""
import csv,collections,datetime,hashlib,json,math,runpy,subprocess
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico';K=V/'kicad';PCB=K/'SeedSigner-Plus-smartcard-pico.kicad_pcb';M=V/'manufacturing';OUT=ROOT/'dist/full-size-pico/prototype';FAB=OUT/'gerbers'
M.mkdir(exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);FAB.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['mise','run','variant:pico-full:check'],cwd=ROOT,check=True)
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one,children=sx['one'],sx['children'];tree=sx['parse'](PCB.read_text());cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
board_sha=sha(PCB);assert list(map(float,one(one(tree,'setup'),'aux_axis_origin')[1:]))==[50,130]
fps={next(p[2] for p in children(f,'property') if p[1]=='Reference'):f for f in children(tree,'footprint')}
props={ref:{p[1]:p[2] for p in children(f,'property')} for ref,f in fps.items()}
catalog={p['code']:p for p in json.loads((V/'jlc-catalog.json').read_text())['parts']}
base=list(csv.DictReader((ROOT/'hardware/manufacturing/bom-jlcpcb.csv').open()))
factory={ref:r['LCSC Part #'] for r in base for ref in r['Designator'].split(',')};assert len(factory)==44
for ref,code in factory.items():
 p=catalog[code];assert p['componentModelEn']==props[ref]['MPN'] and props[ref]['LCSC']==code
 assert p['assemblyMode']=='smtWeld' and p['isBuyComponent']=='1' and not p.get('noBuyReason')
header=catalog['C2883777'];assert header['componentModelEn']=='X6511WVS-20H-C60D48R2' and header['assemblyMode']=='smtWeld'
# U202 is one logical module footprint with two separately placed physical strips.
# Explicit virtual assembly refs avoid asking the factory to place a 40-pin module.
sockets=[dict(ref='J203',nativeX=85.3475,nativeY=81.449,fullPins=list(range(40,20,-1))),dict(ref='J204',nativeX=103.1275,nativeY=81.449,fullPins=list(range(1,21)))]
assert not {'J203','J204'}&fps.keys()
modulepads={int(p[1]):p for p in children(fps['U202'],'pad')}
for item in sockets:
 for i,n in enumerate(item['fullPins']):
  pad=modulepads[n];x,y=map(float,one(pad,'at')[1:3]);x+=94.2375;y+=81.449
  assert abs(y-(57.319+i*2.54))<.000002
  assert abs(x-(item['nativeX']+(1.8 if i%2==0 else -1.8)))<.000002
  assert pad[2:4]==['smd','rect'] and list(map(float,one(pad,'size')[1:]))==[2.2,1.27]
  # C2883777 R2 pin 1 is at the high native-Y end in this 90deg B.Cu placement.
 item['headerPin1NativeMm']=[item['nativeX'],105.579]
 item['headerNativeRotationDeg']=90
(M/'header-placement-map.json').write_text(json.dumps(dict(boardSha256=board_sha,logicalReference='U202',physicalPlacements=sockets,mpn=header['componentModelEn'],lcsc='C2883777',catalogRotationApproved=False),indent=2)+'\n')
bom=base+[{'Comment':'XKB X6511WVS-20H-C60D48R2; 20P 2.54mm SMT male','Designator':'J203,J204','Footprint':'XKB_X6511WVS_20H_C60D48R2','LCSC Part #':'C2883777'}]
def csvwrite(path,rows,fields=None):
 with path.open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
csvwrite(M/'bom-jlcpcb.csv',bom)
def run(args):subprocess.run([str(cli),*map(str,args)],check=True)
run(['pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','--output',OUT/'positions-native.csv',PCB])
rows=[]
for row in csv.DictReader((OUT/'positions-native.csv').open()):
 if row['Ref'] not in factory:continue
 x,y=map(float,[row['PosX'],row['PosY']]);at=list(map(float,one(fps[row['Ref']],'at')[1:3]));assert math.dist([x,y],[at[0]-50,130-at[1]])<.000002
 rows.append({'Designator':row['Ref'],'Mid X':f'{x:.6f}','Mid Y':f'{y:.6f}','Layer':'Top' if row['Side']=='top' else 'Bottom','Rotation':f'{float(row["Rot"])%360:.6f}'})
assert len(rows)==44
# Audit proves every retained component's local lands/nets and all three
# previously calibrated supplier component poses match the pinned source.
for ref in ['J301','J601','U601']:
 assert one(fps[ref],'at')==one(next(f for f in children(sx['parse']((V/'source-board.kicad_pcb').read_text()),'footprint') if any(p[1:3]==['Reference',ref] for p in children(f,'property'))),'at')
native_rows=[dict(r) for r in rows]
rows=runpy.run_path(str(ROOT/'scripts/jlc-placement.py'))['correct'](rows,{ref:{'lcsc':props[ref].get('LCSC','')} for ref in fps})
for item in sockets:
 row={'Designator':item['ref'],'Mid X':f'{item["nativeX"]-50:.6f}','Mid Y':f'{130-item["nativeY"]:.6f}','Layer':'Bottom','Rotation':'90.000000'}
 rows.append(row);native_rows.append(dict(row))
assert len(rows)==46 and len({r['Designator'] for r in rows})==46
assert {r['Designator'] for r in rows}==set(factory)|{'J203','J204'}
csvwrite(M/'cpl-jlcpcb.csv',rows);csvwrite(M/'cpl-native-reference.csv',native_rows)
for file in FAB.iterdir():
 if file.is_file():file.unlink()
run(['pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','--check-zones','--output',str(FAB)+'/',PCB])
run(['pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path',M/'drill-report.txt','--output',str(FAB)+'/',PCB])
assert len([p for p in FAB.iterdir() if p.suffix in {'.gtl','.gbl','.g1','.g2','.g3','.g4','.gtp','.gbp','.gto','.gbo','.gts','.gbs','.gm1','.gbr'}])==11 and len(list(FAB.glob('*.drl')))==2
procurement=json.loads((M/'customer-procurement.json').read_text())
stock=[]
for row in bom:
 p=catalog[row['LCSC Part #']];refs=row['Designator'].split(',');required=10*len(refs)
 # Two header strips per board; six provisional spares. Supplier attrition wins.
 proposed=required+(6 if p['code']=='C2883777' else 2 if p['code']=='C5417011' else 0)
 stock.append(dict(code=p['code'],mpn=p['componentModelEn'],refs=refs,perBoard=len(refs),installedForTen=required,provisionalProcurementQuantity=proposed,standardAssemblyStock=p['canPresaleNumber'],overseasStockSeparate=p.get('overseasStockCount'),shortfallInstalled=max(0,required-p['canPresaleNumber']),shortfallProposed=max(0,proposed-p['canPresaleNumber']),minimumPurchase=p.get('preMinPurchaseNum'),supplierLossNumber=p.get('lossNumber'),checkedAt=p['checkedAt'],reserved=False))
for item in stock:
 if item['code'] in procurement:item['customerPreorder']=procurement[item['code']]
(M/'stock-for-ten.json').write_text(json.dumps(stock,indent=2)+'\n')
request=[{'MPN':p['mpn'],'JLCPCB Part #':p['code'],'References':','.join(p['refs']),'Installed quantity':p['installedForTen'],'Proposed purchase quantity':0 if p['code'] in procurement else p['provisionalProcurementQuantity'],'Already pre-ordered':procurement.get(p['code'],{}).get('quantityPreordered',0),'Action':'Existing user pre-order: 10; do not duplicate; verify receipt/destination and attrition' if p['code'] in procurement else 'Reserve standard stock' if not p['shortfallProposed'] else 'Pre-order / global sourcing; exact MPN; confirm attrition'} for p in stock]
csvwrite(M/'procurement-for-ten.csv',request)
vias=children(tree,'via');slots=[dict(ref=ref,pad=p[1],drillMm=one(p,'drill')[2:4]) for ref,f in fps.items() for p in children(f,'pad') if one(p,'drill')[1:2]==['oval']]
measure=dict(minimumTrackMm=min(float(one(t,'width')[1]) for t in children(tree,'segment')),minimumViaDrillMm=min(float(one(v,'drill')[1]) for v in vias),minimumViaAnnulusMm=min((float(one(v,'size')[1])-float(one(v,'drill')[1]))/2 for v in vias),platedSlots=slots)
assert measure['minimumTrackMm']>=.15 and measure['minimumViaDrillMm']>=.3 and measure['minimumViaAnnulusMm']>=.14999
files={f.name:sha(f) for f in FAB.iterdir() if f.is_file()}
manifest=dict(variant='full-size-pico-smt-male',quantity=10,boardSha256=board_sha,fittedSmtPieces=46,catalogLines=19,topPlacements=sum(r['Layer']=='Top' for r in rows),bottomPlacements=sum(r['Layer']=='Bottom' for r in rows),layers=4,thicknessMm=1.6,outlineMm=[160,70],originMm=[50,130],cplDatum='X = native X - 50; Y = 130 - native Y; bottom X not mirrored',measurements=measure,headers=dict(code='C2883777',requiredInstalled=20,proposedWithSpares=26,standardStock=header['canPresaleNumber']),stockBlockers=[p for p in stock if p['shortfallProposed']],stockReserved=False,uploadedPlacementPreviewApproved=False,factoryPanelAndDfmApproved=False,status='prototype_quote_ready_procurement_and_supplier_review_pending',files=files)
(M/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with ZipFile(OUT/'shieldsigner-full-pico-gerbers.zip','w',ZIP_DEFLATED) as z:
 for f in sorted(FAB.iterdir()):
  if f.is_file():z.write(f,f.name)
print('Matched 46 placements / 19 SKUs; ten-board sourcing audit and Gerber/drill archive generated.')
print('Installed-stock blockers:',[(p['code'],p['shortfallInstalled']) for p in manifest['stockBlockers']])

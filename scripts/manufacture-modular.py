#!/usr/bin/env python3
"""Build one matched prototype JLCPCB kit from the modular native board and dated catalog."""
import collections,csv,datetime,hashlib,json,math,re,runpy,subprocess,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/lcd-module-2.8';K=V/'kicad';PCB=K/'SeedSigner-Plus-smartcard-pico.kicad_pcb';OUT=ROOT/'dist/lcd-module-2.8';FAB=OUT/'fabrication';M=V/'manufacturing'
for script in ['check-lcd-module-variant.py','check-modular-mechanics.py']:subprocess.run([sys.executable,str(ROOT/'scripts'/script)],check=True)
cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one=sx['one'];children=sx['children'];tree=sx['parse'](PCB.read_text());values=runpy.run_path(str(ROOT/'scripts/part-values.py'))
assert list(map(float,one(one(tree,'setup'),'aux_axis_origin')[1:]))==[50,130],'Manufacturing origin changed'
selection=json.loads((ROOT/'docs/bom-selection.json').read_text());selection.update(json.loads((V/'bom-selection-extra.json').read_text()));catalog={p['code']:p for p in json.loads((V/'jlc-catalog.json').read_text())['parts']}
parts=[];groups=collections.defaultdict(list);expected=set()
for f in children(tree,'footprint'):
 props={p[1]:p[2] for p in children(f,'property')};ref=props['Reference'];dnp='dnp' in one(f,'attr')
 role='DNP' if dnp else 'PCB copper jumper' if ref.startswith('JP') else 'customer 1x8 display socket/header' if ref=='J701' else 'customer Luckfox module and headers' if ref=='U202' else 'customer M2.5 supports' if ref.startswith('H70') else 'JLCPCB SMT assembly'
 row={'ref':ref,'value':props['Value'],'footprint':f[1],'side':one(f,'layer')[1],'role':role,'lcsc':props.get('LCSC',''),'mpn':props.get('MPN','')};parts.append(row)
 if role=='JLCPCB SMT assembly':
  chosen=selection[ref];assert row['lcsc']==chosen['lcsc'] and row['mpn']==chosen['mpn'],f'{ref} purchase identity drift'
  p=catalog[row['lcsc']];assert p['status']=='public_catalog_snapshot' and p['componentModelEn']==row['mpn'],f'{ref} current catalog identity mismatch'
  assert p.get('assemblyMode')=='smtWeld' and p.get('isBuyComponent')=='1' and not p.get('noBuyReason'),f'{ref} not currently available for standard SMT sourcing'
  if ref[0] in {'C','R','L'}:
   key={'C':'Capacitance','R':'Resistance','L':'Inductance'}[ref[0]];attributes={a['attribute_name_en']:a['attribute_value_name'] for a in p['attributes']}
   normalize=lambda v:re.sub(r'\s+','',v.replace('µ','u').replace('μ','u')).casefold()
   assert normalize(values['nominal'](row['value'],[ref]))==normalize(attributes[key]),f'{ref} value/catalog mismatch'
  groups[row['lcsc']].append(row);expected.add(ref)
assert len(expected)==35 and len(groups)==17,(len(expected),len(groups))
assert len(parts)==47,len(parts)
M.mkdir(exist_ok=True,parents=True);OUT.mkdir(exist_ok=True,parents=True);FAB.mkdir(exist_ok=True,parents=True)
with (M/'bom-jlcpcb.csv').open('w',newline='') as file:
 writer=csv.writer(file,lineterminator='\n');writer.writerow(['Comment','Designator','Footprint','LCSC Part #'])
 for code,items in sorted(groups.items()):writer.writerow([values['nominal'](items[0]['value'],[p['ref'] for p in items])+'; '+items[0]['mpn'],','.join(sorted(p['ref'] for p in items)),items[0]['footprint'].split(':')[-1],code])
with (M/'population.csv').open('w',newline='') as file:
 writer=csv.DictWriter(file,fieldnames=list(parts[0]),lineterminator='\n');writer.writeheader();writer.writerows(sorted(parts,key=lambda p:p['ref']))
def run(args):subprocess.run([str(cli),*[str(a) for a in args]],check=True)
run(['pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','--output',OUT/'positions.csv',PCB])
rows=[];fps={p['ref']:p for p in parts};coordinates={next(x[2] for x in children(f,'property') if x[1]=='Reference'):list(map(float,one(f,'at')[1:3])) for f in children(tree,'footprint')}
for row in csv.DictReader((OUT/'positions.csv').open()):
 if row['Ref'] not in expected:continue
 x,y=map(float,[row['PosX'],row['PosY']]);source=coordinates[row['Ref']]
 assert abs(x-(source[0]-50))<.00001 and abs(y-(130-source[1]))<.00001,'Native placement export has different coordinate datum'
 rows.append({'Designator':row['Ref'],'Mid X':f'{x:.6f}','Mid Y':f'{y:.6f}','Layer':'Top' if row['Side']=='top' else 'Bottom','Rotation':f'{float(row["Rot"])%360:.6f}'})
assert {row['Designator'] for row in rows}==expected and len(rows)==35
with (M/'cpl-jlcpcb.csv').open('w',newline='') as file:
 writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
# Clear only this generator's dedicated fabrication directory, preventing stale layer files.
for p in FAB.iterdir():
 if p.is_file():p.unlink()
run(['pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','--check-zones','--output',str(FAB)+'/',PCB])
run(['pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path',OUT/'drill-report.txt','--output',str(FAB)+'/',PCB])
stock=[]
for code,items in sorted(groups.items()):
 p=catalog[code];need=len(items)*5;available=int(p.get('canPresaleNumber',0));assert available>=need,f'{code} insufficient catalog stock for five boards'
 stock.append({'code':code,'mpn':p['componentModelEn'],'refs':','.join(sorted(x['ref'] for x in items)),'perBoard':len(items),'forFiveBoards':need,'assemblyStock':available,'minimumPurchase':p.get('preMinPurchaseNum'),'checkedAt':p['checkedAt'],'library':p.get('componentLibraryType'),'reserved':False})
(M/'stock-for-five.json').write_text(json.dumps(stock,indent=2)+'\n')
lines=['# Modular carrier sourcing table','','35 fitted SMT pieces, 17 catalog lines. Values and ratings are explicit; availability is a dated public snapshot, not reserved stock. Customer headers/modules are in the separate shopping list.','','| References | Value | Rating | Qty | MPN | LCSC | Assembly stock | Checked UTC |','|---|---|---|---:|---|---|---:|---|']
for code,items in sorted(groups.items()):
 p=catalog[code];refs=[a['ref'] for a in items];lines.append(f"| {', '.join(refs)} | {values['nominal'](items[0]['value'],refs)} | {values['ratings'](p,refs) or '—'} | {len(refs)} | {p['componentModelEn']} | [{code}]({p['url']}) | {p['canPresaleNumber']} | {p['checkedAt'][:19]} |")
(M/'BOM.md').write_text('\n'.join(lines)+'\n')
manifest={'variant':'modular-lcd-2.8','boardSha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'fittedSmtPieces':35,'catalogLines':17,'bomCplRefsMatch':True,'layers':2,'thicknessMm':1.6,'originMm':{'x':50,'y':130,'cplY':'130 minus board y; bottom X is not mirrored'},'proposedPrototypeQuantity':5,'stockReserved':False,'catalogStockSufficientForFive':True,'placementRotationsQualifiedByAssembler':False,'status':'prototype_quote_files','nativeErcErrors':0,'nativeActiveDrcErrors':0,'nativeUnconnected':0,'nativeParityIssues':0,'dnpCourtyardExclusions':0,'mechanicalModelsVerified':19,'limitations':['Assembler placement preview/DFM/quote not submitted','Physical header/module fit and powered bring-up not tested','LCD, smartcard socket and spacer 3D models are dimensional envelopes','Stock snapshot is not a reservation'],'files':{}}
with ZipFile(OUT/'shieldsigner-modular-gerbers.zip','w',ZIP_DEFLATED) as z:
 for p in sorted(FAB.iterdir()):z.write(p,p.name)
for p in [OUT/'shieldsigner-modular-gerbers.zip',M/'bom-jlcpcb.csv',M/'cpl-jlcpcb.csv',M/'population.csv']:manifest['files'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(M/'readiness.json').write_text(json.dumps(manifest,indent=2)+'\n')
with ZipFile(OUT/'shieldsigner-modular-order.zip','w',ZIP_DEFLATED) as z:
 z.write(OUT/'shieldsigner-modular-gerbers.zip','shieldsigner-modular-gerbers.zip')
 for p in sorted(M.iterdir()):
  if p.is_file():z.write(p,p.name)
 z.write(V/'assembly-extras.csv','customer-parts.csv');z.write(OUT/'drill-report.txt','drill-report.txt')
print('Matched modular kit: 35 SMT placements, 17 current catalog lines; five-board stock check passed.')

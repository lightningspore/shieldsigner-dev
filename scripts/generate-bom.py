#!/usr/bin/env python3
"""Generate matching JLCPCB carrier BOM/CPL and a complete population audit."""
import collections,csv,datetime,json,runpy,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
m=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));parse,children,one=[m[k] for k in ['parse','children','one']]
pcb=parse((ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_text())
selection=json.loads((ROOT/'docs/bom-selection.json').read_text())
catalog={p['code']:p for p in json.loads((ROOT/'docs/jlc-catalog.json').read_text())['parts']}
parts=[];groups=collections.defaultdict(list)
for f in children(pcb,'footprint'):
 props={p[1]:p[2] for p in children(f,'property')};ref=props['Reference'];dnp='dnp' in one(f,'attr')
 role='PCB copper jumper' if ref.startswith('JP') else 'optional host module' if ref=='U202' else 'DNP' if dnp else 'JLCPCB carrier assembly'
 p={'ref':ref,'value':props['Value'],'footprint':f[1],'layer':one(f,'layer')[1],'population':role,'lcsc':props.get('LCSC'),'mpn':props.get('MPN'),'manufacturer':props.get('Manufacturer')}
 if role=='JLCPCB carrier assembly':
  chosen=selection[ref];assert p['lcsc']==chosen['lcsc'] and p['mpn']==chosen['mpn'], f'{ref} native BOM drift'
  record=catalog[p['lcsc']];assert record.get('status')=='public_catalog_snapshot',f'{ref} unknown catalog identity'
  assert record['componentModelEn']==p['mpn'],f'{ref} catalog MPN mismatch'
  groups[p['lcsc']].append(p)
 parts.append(p)
assert len(parts)==53
assembled=[p for p in parts if p['population']=='JLCPCB carrier assembly'];assert len(assembled)==43
assert {p['ref'] for p in parts if p['population']=='DNP'}=={'R404','R408','J302'}
OUT=ROOT/'manufacturing/jlcpcb';OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'bom-carrier-jlcpcb.csv').open('w',newline='') as file:
 writer=csv.writer(file);writer.writerow(['Comment','Designator','Footprint','LCSC Part #'])
 for code,items in sorted(groups.items()):
  chosen=catalog[code];writer.writerow([items[0]['value']+'; '+items[0]['mpn'],','.join(sorted(p['ref'] for p in items)),chosen['componentSpecificationEn'],code])
with (OUT/'population-audit.csv').open('w',newline='') as file:
 writer=csv.DictWriter(file,fieldnames=list(parts[0]));writer.writeheader();writer.writerows(sorted(parts,key=lambda p:p['ref']))
with (ROOT/'dist/kicad/positions.csv').open() as file:positions=list(csv.DictReader(file))
expected={p['ref'] for p in assembled};placed=[]
for row in positions:
 if row['Ref'] in expected:
  placed.append({'Designator':row['Ref'],'Mid X':row['PosX'],'Mid Y':row['PosY'],'Layer':'Top' if row['Side']=='top' else 'Bottom','Rotation':f"{float(row['Rot']) % 360:.6f}"})
assert len(placed)==43 and {p['Designator'] for p in placed}==expected,'BOM/CPL reference mismatch'
with (OUT/'cpl-carrier-jlcpcb.csv').open('w',newline='') as file:
 writer=csv.DictWriter(file,fieldnames=['Designator','Mid X','Mid Y','Layer','Rotation']);writer.writeheader();writer.writerows(placed)
lines=['# JLCPCB sourcing table','','Generated from the native KiCad PCB plus the public catalog snapshot. Counts are per carrier, excluding the optional Luckfox. All 43 fitted carrier pieces have identified JLCPCB catalog codes; this does not approve their footprints or reserve stock.','','| References | Qty / PCB | Manufacturer / MPN | C-code | Catalog available-to-order field | Basic/extended | Checked UTC |','|---|---:|---|---|---:|---|---|']
for code,items in sorted(groups.items()):
 p=catalog[code];lines.append(f"| {', '.join(x['ref'] for x in items)} | {len(items)} | {p['componentBrandEn']} / {p['componentModelEn']} | [{code}]({p['url']}) | {p.get('canPresaleNumber','unavailable')} | {p.get('componentLibraryType','unknown')} | {p['checkedAt'][:19]} |")
(ROOT/'docs/BOM-TABLE.md').write_text('\n'.join(lines)+'\n')
checks=json.loads((ROOT/'dist/kicad/checks-summary.json').read_text())
manifest={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variant':'carrier_without_luckfox','fittedPieces':43,'uniqueCatalogParts':len(groups),'bomCplRefsMatch':True,'stockReserved':False,'placementRotationsQualified':False,'activeDrcErrors':checks['drc']['bySeverity'].get('error',0),'documentedDnpExceptions':checks['drc'].get('excluded',0),'releaseStatus':'review_only','remainingItems':['XKB extended switch land/stencil and actuator-height qualification','LCD contact orientation and backlight current','SEC1210 UR2 runtime reader configuration','JLCPCB placement preview, quote/DFM and stock reservation','physical bring-up']}
(OUT/'readiness.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Generated carrier BOM/CPL: {len(groups)} catalog lines, 43 placed pieces, all 53 footprints accounted for.')

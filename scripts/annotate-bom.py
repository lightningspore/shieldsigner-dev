#!/usr/bin/env python3
"""Attach verified catalog identity to native parts without changing copper."""
import json,re,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
m=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));expressions=m['expressions']
selection=json.loads((ROOT/'docs/bom-selection.json').read_text())
renames={'Q401','D302','J301','U601',*[f'SW50{i}' for i in range(1,9)]}
for file in [ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb',*(ROOT/'kicad').glob('*.kicad_sch')]:
 text=file.read_text();changes=[]
 for start,end,expr in expressions(text):
  pcb=expr.startswith('(footprint ')
  if not pcb and not re.match(r'\(symbol\s*\(lib_id',expr):continue
  match=re.search(r'\(property\s+"Reference"\s+"([^"\n]+)"',expr)
  if not match or match[1] not in selection:continue
  ref=match[1];part=selection[ref]
  fields={'LCSC':part['lcsc'],'MPN':part['mpn'],'Manufacturer':part['manufacturer'],'Datasheet':part['datasheet']}
  if ref in renames:fields['Value']=part['mpn']
  changed=expr
  for key,value in fields.items():
   pattern=r'(\(property\s+"'+re.escape(key)+r'"\s+)"(?:\\.|[^"\\])*"'
   if re.search(pattern,changed):changed=re.sub(pattern,lambda match:match[1]+json.dumps(value),changed,count=1)
   else:
    layer='B.Fab' if '(layer "B.Cu")' in expr else 'F.Fab'
    effects='(effects (font (size 1 1))'+(')' if pcb else ' (hide yes))')
    prop=f'(property {json.dumps(key)} {json.dumps(value)} (at 0 0 0) '+(f'(layer "{layer}") (hide yes) ' if pcb else '')+effects+')'
    changed=changed.rstrip()[:-1]+'\n'+prop+'\n)'
  changes.append((start,end,changed))
 for start,end,new in sorted(changes,reverse=True):text=text[:start]+new+text[end:]
 file.write_text(text)
overrides=json.loads((ROOT/'docs/native-overrides.json').read_text())
for ref in renames|{'J401'}:
 part=selection[ref]
 overrides[ref]={'value':part['mpn'],'lcsc':part['lcsc'],'reason':('Corrected LCD supplier ID: C19273935 is a bottom-contact Hong Cheng connector; C2931360 is the intended top-contact Amphenol 62684-402100ALF.' if ref=='J401' else 'Native value now states the exact JLCPCB catalog part selected by its supplier ID; electrical copper is unchanged. Footprint and assembly qualification are tracked in BOM.md.')}
(ROOT/'docs/native-overrides.json').write_text(json.dumps(overrides,indent=2)+'\n')
print('Annotated',len(selection),'native catalog identities; corrected J401 supplier ID and explicit device values.')

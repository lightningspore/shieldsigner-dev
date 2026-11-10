#!/usr/bin/env python3
"""Visual-review refinements for the readable pill sheets."""
from pathlib import Path
import runpy,re,json
ROOT=Path(__file__).resolve().parents[1];K=ROOT/'variants/lcd-module-2.8/kicad'
s=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));o,c,p=s['one'],s['children'],s['parse']
def shift(e,dx,dy):return re.sub(r'\(at (-?[\d.]+) (-?[\d.]+)',lambda m:f'(at {float(m[1])+dx:.5f} {float(m[2])+dy:.5f}',e)
def hide(e):
 if '(hide yes)' not in e:
  pos=e.rfind(')');q=e[:pos].rstrip();last=q.rfind(')');e=q[:last]+' (hide yes)'+q[last:]+e[pos:]
 return e
audit=ROOT/'variants/lcd-module-2.8/schematic-readability-audit.json'
record=json.loads(audit.read_text())
assert not record.get('visualRefinementsApplied'),'Already refined; do not replay'
for path in K.glob('*.kicad_sch'):
 source=path.read_text();edits=[];end=-1
 for a,b,e in sorted(s['expressions'](source),key=lambda v:v[0]):
  if a==0:continue
  if a<end:continue
  end=b;n=p(e);new=e
  if n[0]=='symbol':
   props={q[1]:q[2] for q in c(n,'property')};ref=props['Reference']
   for aa,bb,ee in sorted(s['expressions'](new),reverse=True):
    q=p(ee)
    if q[0]!='property':continue
    changed=ee
    if q[:2]==['property','Value'] and (props['Value']=='GND' or ref.startswith('#FLG')):changed=hide(ee)
    if path.name=='buttons.kicad_sch' and ref.startswith('SW') and q[:2]==['property','Reference']:changed=shift(ee,0,3.81)
    if path.name=='lcd_module.kicad_sch' and ref=='C701' and q[1] in ['Reference','Value']:changed=shift(ee,59.69-float(o(q,'at')[1]),0)
    if changed!=ee:new=new[:aa]+changed+new[bb:]
  if n[0]=='text':
   if path.name=='SeedSigner-Plus-smartcard-pico.kicad_sch':
    if n[1].startswith(('+5V input','Luckfox Pico','8-pin SPI')):new=shift(e,0,-13.97)
    if n[1].startswith(('Active-low','UART reader')):new=shift(e,0,-13.97)
   if path.name=='rpi_interface.kicad_sch':
    if n[1].startswith('BACKLIGHT:'):new=shift(e,0,-3.81)
    if n[1]=='GPIO1_C0 FUNCTION':new=shift(e,0,12.7)
  if new!=e:edits.append((a,b,new))
 for a,b,e in sorted(edits,reverse=True):source=source[:a]+e+source[b:]
 p(source);path.write_text(source)

record['visualRefinementsApplied']=True
audit.write_text(json.dumps(record,indent=2)+'\n')

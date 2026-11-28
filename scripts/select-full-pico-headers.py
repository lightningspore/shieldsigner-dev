"""Select the stocked XKB R2 SMT male strips; sockets are fitted on the Pico."""
from pathlib import Path
import json,runpy,hashlib
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/full-size-pico';K=V/'kicad';PCB=K/'SeedSigner-Plus-smartcard-pico.kicad_pcb'
assert hashlib.sha256(PCB.read_bytes()).hexdigest()==hashlib.sha256((V/'history/harwin-socket-study.kicad_pcb').read_bytes()).hexdigest(),'One-time migration only: candidate has subsequent edits'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one=sx['one']
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
b=p.LoadBoard(str(PCB))
tp=next(q for q in b.GetFootprints() if q.GetReference()=='TP905');tp.Move(p.VECTOR2I(p.FromMM(.3),0))
p.SaveBoard(str(PCB),b)
text=PCB.read_text().replace('Luckfox_Pico_SMD_Sockets','Luckfox_Pico_SMD_Headers')
host=next(raw for _,_,raw in sx['expressions'](text) if raw.startswith('(footprint ') and '(property "Reference" "U202"' in raw)
import re
for a,z,raw in list(sx['expressions'](host))[::-1]:
 if raw.startswith('(model ') or (raw.startswith('(fp_rect') and any(f'(layer "{layer}")' in raw for layer in ['B.Fab','B.CrtYd'])):
  host=host[:a]+host[z:]
 elif raw.startswith('(pad '):
  node=sx['parse'](raw);n=int(node[1]);index=n-1 if n<=20 else 40-n
  x=(8.89 if n<=20 else -8.89)+(1.8 if index%2==0 else -1.8)
  y=-24.13+index*2.54
  newraw=re.sub(r'\(at [^)]+\)',f'(at {x:.6f} {y:.6f})',raw,count=1)
  newraw=re.sub(r'\(size [^)]+\)','(size 2.2 1.27)',newraw,count=1).replace('smd roundrect','smd rect')
  newraw=re.sub(r'\(roundrect_rratio [^)]+\)','',newraw)
  host=host[:a]+newraw+host[z:]
extra=''
for x in [-8.89,8.89]:
 for half,y,layer,width in [(3.15,25.65,'B.CrtYd',.05),(1.25,25.4,'B.Fab',.1)]:
  extra+=f'(fp_rect (start {x-half} {-y}) (end {x+half} {y}) (stroke (width {width}) (type default)) (fill none) (layer "{layer}"))'
for name,hidden in [('Luckfox-Pico.step',False),('Luckfox-Pico-Plus.step',True)]:
 extra+=f'(model "${{KIPRJMOD}}/../models/{name}" '+('(hide yes)' if hidden else '')+' (offset (xyz 10.5 -25.5 12.64)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 180)))'
for x in [-8.89,8.89]:extra+=f'(model "${{KIPRJMOD}}/../models/XKB-SMT-male-nominal.step" (offset (xyz {x} 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 90)))'
extra+='(model "${KIPRJMOD}/../models/Pico-female-sockets-nominal.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
new=host[:-1]+extra+')'
original=next(raw for _,_,raw in sx['expressions'](text) if raw.startswith('(footprint ') and '(property "Reference" "U202"' in raw)
PCB.write_text(text.replace(original,new,1))
(K/'LuckfoxFull.pretty/Luckfox_Pico_SMD_Headers.kicad_mod').write_text(new.replace('(footprint "LuckfoxFull:Luckfox_Pico_SMD_Headers"','(footprint "Luckfox_Pico_SMD_Headers"',1))
for path in [*K.glob('*.kicad_sch'),K/'LuckfoxFull.kicad_sym']:
 path.write_text(path.read_text().replace('Luckfox_Pico_SMD_Sockets','Luckfox_Pico_SMD_Headers'))
path=V/'local-placement.json';data=json.loads(path.read_text());data['TP905']['after']=[108.8,59.5];data['TP905']['reason']='Clear the wider XKB SMT header courtyard; same-net copper stays inside pad.';path.write_text(json.dumps(data,indent=2)+'\n')
print('Selected stocked XKB R2 male headers; reroute and native review required.')

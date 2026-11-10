#!/usr/bin/env python3
"""Convert the current pill carrier to four layers; back up, refill and audit."""
from pathlib import Path
import hashlib,json,runpy,subprocess,sys,time,uuid
ROOT=Path(__file__).resolve().parents[1]
BOARD=ROOT/'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
if '--worker' not in sys.argv:
 cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
 sys.exit(subprocess.call([str(cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'),__file__,'--worker']))
import wx
wx.Log.SetLogLevel(wx.LOG_Error)
app=wx.App(False)
import pcbnew as p
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one,children=sx['one'],sx['children']
before=BOARD.read_bytes();tree=sx['parse'](before.decode())
assert not any(x[1]=='In1.Cu' for x in children(tree,'layers')[0][1:]),'Already converted'
backup=ROOT/'.tools/pcb-edits'/f'four-layer-{time.time_ns()}';backup.mkdir(parents=True)
(backup/BOARD.name).write_bytes(before)
text=before.decode().replace('(0 "F.Cu" signal)','(0 "F.Cu" signal)\n\t\t(4 "In1.Cu" power)\n\t\t(6 "In2.Cu" power)',1)
old=next(expr for _,_,expr in sx['expressions'](text) if sx['parse'](expr)[:2]==['layer','dielectric 1'])
def dielectric(n,kind,thickness):
 return f'(layer "dielectric {n}" (type "{kind}") (thickness {thickness}) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))'
stack='\n'.join([dielectric(1,'prepreg',.2),'(layer "In1.Cu" (type "copper") (thickness 0.035))',dielectric(2,'core',1.04),'(layer "In2.Cu" (type "copper") (thickness 0.035))',dielectric(3,'prepreg',.2)])
text=text.replace(old,stack,1)
# New planes share the reviewed outer-zone boundary and thermal/clearance rules.
zone=next(expr for _,_,expr in sx['expressions'](text) if sx['parse'](expr)[0]=='zone' and one(sx['parse'](expr),'layer')==['layer','F.Cu'])
edits=[(a,b) for a,b,expr in sx['expressions'](zone) if sx['parse'](expr)[0]=='filled_polygon']
for a,b in sorted(edits,reverse=True):zone=zone[:a]+zone[b:]
for layer in ['In1.Cu','In2.Cu']:
 new=zone.replace('(layer "F.Cu")',f'(layer "{layer}")').replace(one(sx['parse'](zone),'uuid')[1],str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner:four-layer:'+layer)))
 text=text.rstrip()[:-1]+new+'\n)\n'
try:
 BOARD.write_text(text)
 b=p.LoadBoard(str(BOARD));assert b.GetCopperLayerCount()==4
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(BOARD),b)
 loaded=p.LoadBoard(str(BOARD));assert loaded.GetCopperLayerCount()==4
 for layer in [p.In1_Cu,p.In2_Cu]:
  zones=[z for z in loaded.Zones() if z.GetLayer()==layer]
  assert len(zones)==1 and zones[0].GetNetname()=='GND'
  assert zones[0].GetFilledPolysList(layer).OutlineCount()>0
 after=sx['parse'](BOARD.read_text())
 def normalized(node):
  if isinstance(node,list):
   if node==['fill','solid']:return ['fill','yes']
   return [normalized(x) for x in node]
  try:return float(node)
  except ValueError:return node
 for kind in ['footprint','segment','via','gr_line','gr_arc','gr_text','gr_poly']:
  assert normalized(sorted(children(tree,kind),key=lambda n:one(n,'uuid')))==normalized(sorted(children(after,kind),key=lambda n:one(n,'uuid'))),f'Unexpected {kind} change'
 audit={'beforeSha256':hashlib.sha256(before).hexdigest(),'afterSha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),'copperLayers':4,'innerNets':['GND','GND'],'thicknessMm':1.6,'nominalDielectricsMm':[.2,1.04,.2],'copperThicknessMm':.035,'supplierStackupApproved':False,'preserved':['footprints','tracks','vias','outline','silkscreen']}
 (ROOT/'variants/lcd-module-2.8/four-layer-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps(audit,indent=2))
except BaseException:
 (backup/'candidate.kicad_pcb').write_bytes(BOARD.read_bytes())
 BOARD.write_bytes(before)
 raise

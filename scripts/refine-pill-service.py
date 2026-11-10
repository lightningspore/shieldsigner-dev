#!/usr/bin/env python3
"""Resolve the first native DRC review of service spurs; retain baseline routing."""
from pathlib import Path
import runpy,subprocess,sys,json
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'variants/lcd-module-2.8';PCB=V/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));base=sorted((ROOT/'.tools/pcb-edits').glob('service-*'))[-1]/PCB.name;t=sx['parse'](base.read_text());ids={sx['one'](n,'uuid')[1] for k in ['segment','via'] for n in sx['children'](t,k)}
# Two standalone stitching vias occupy the new pad/spur; nearby planes and new GND points retain returns.
for n in sx['children'](t,'via'):
 if tuple(map(float,sx['one'](n,'at')[1:3])) in {(172.5,81.8),(174.193,80.264)}:
  assert sx['one'](n,'net')[-1]=='GND'
  ids.remove(sx['one'](n,'uuid')[1])
baseline_nodes={}
for _,_,expression in sx['expressions'](base.read_text()):
 node=sx['parse'](expression)
 if node[0] in ['segment','via']:baseline_nodes[sx['one'](node,'uuid')[1]]=expression
if '--worker' not in sys.argv:
 text=PCB.read_text();edits=[]
 for a,z,e in sx['expressions'](text):
  n=sx['parse'](e)
  if n[0] in ['segment','via']:
   key=sx['one'](n,'uuid')[1]
   edits.append((a,z,baseline_nodes[key] if key in ids else ''))
 for a,z,replacement in sorted(edits,reverse=True):text=text[:a]+replacement+text[z:]
 PCB.write_text(text)
 cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();sys.exit(subprocess.call([str(cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'),__file__,'--worker']))
import wx
wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
import pcbnew as p
b=p.LoadBoard(str(PCB));fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def route(points,net,layer=p.B_Cu,width=.25):
 for a,z in zip(points,points[1:]):
  tr=p.PCB_TRACK(b);tr.SetStart(vec(*a));tr.SetEnd(vec(*z));tr.SetLayer(layer);tr.SetWidth(p.FromMM(width));tr.SetNet(b.FindNet(net));b.Add(tr)
def via(x,y,net):
 v=p.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
config=json.loads((V/'serviceability.json').read_text())
for ref,x,y in [('TP903',174,79.5),('TP904',174,87)]:
 oldx,oldy=p.ToMM(fps[ref].GetX()),p.ToMM(fps[ref].GetY())
 fps[ref].SetPosition(vec(x,y))
 for item in b.GetDrawings():
  if isinstance(item,p.PCB_TEXT) and item.GetText() in [config['testpoints'][next(i for i,q in enumerate(config['testpoints']) if q['ref']==ref)]['label'],ref+'\n'+config['testpoints'][next(i for i,q in enumerate(config['testpoints']) if q['ref']==ref)]['label']] and abs(p.ToMM(item.GetPosition().x)-oldx)<.001 and abs(p.ToMM(item.GetPosition().y)-(oldy-2.5))<.001:item.Move(vec(x-oldx,y-oldy))
 for point in config['testpoints']:
  if point['ref']==ref:point['xy']=[x,y]
for item in b.GetDrawings():
 if isinstance(item,p.PCB_TEXT) and item.GetText()=='ShieldSigner' and item.GetLayer()==p.F_SilkS:item.SetPosition(vec(78,108))
for x,y,layer in [(112,120,p.F_Cu),(114,59.5,p.B_Cu),(174,87,p.B_Cu)]:route([[x,y],[x,y+1.7]],'GND',layer);via(x,y+1.7,'GND')
route([[108,59.5],[108,61.5],[110,63.5],[110,65.7]],'LCD_3V3');via(110,65.7,'LCD_3V3');route([[110,65.7],[110,65.4],[109.05,65.4],[109.05,64.8]],'LCD_3V3',p.F_Cu)
route([[120,59.5],[120,61.3]],'UART_TX');via(120,61.3,'UART_TX');route([[120,61.3],[118.5,62.8],[118.5,69.2]],'UART_TX',p.F_Cu);via(118.5,69.2,'UART_TX');route([[118.5,69.2],[120.1,69.2]],'UART_TX')
route([[126,59.5],[126,61.9],[123.1,64.8],[120.1,64.8],[120.1,67.2]],'UART_RX')
route([[166.1564,83.2866],[166.4,83.5302],[166.4,83.8]],'+3.3V');via(166.4,83.8,'+3.3V');route([[166.4,83.8],[166.4,84.2],[171.8,84.2],[174,82.0],[174,81.2]],'+3.3V',p.F_Cu);via(174,81.2,'+3.3V');route([[174,81.2],[174,79.5]],'+3.3V')
for item in b.GetDrawings():
 if isinstance(item,p.PCB_TEXT) and item.GetText() in ['HOST3V3','TP903\nHOST3V3']:item.SetPosition(vec(174,77))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(PCB),b);(V/'serviceability.json').write_text(json.dumps(config,indent=2)+'\n')

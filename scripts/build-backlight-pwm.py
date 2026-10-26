#!/usr/bin/env python3
"""Build a separately checked dedicated-PWM hardware revision candidate.

The released 0.0.7 board and its quote assets are never overwritten.
"""
from pathlib import Path
import hashlib,json,re,runpy,shutil,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'variants/lcd-module-2.8/kicad'
DEST=ROOT/'variants/lcd-backlight-pwm/kicad'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));children,one,parse=sx['children'],sx['one'],sx['parse']
def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-pwm:'+name))
R_ID=uid('R703')
BASE_SHA='b4eb7a7cef3f026bfc332a19980727a165de9ea826e4eb25dcc68e2c458004b7'
def node_text(text,predicate):
 return next(expr for _,_,expr in sx['expressions'](text) if predicate(parse(expr)))
def update(text,callback):
 edits=[]
 for a,b,expr in sx['expressions'](text):
  result=callback(parse(expr),expr)
  if result!=expr:edits.append((a,b,result))
 for a,b,expr in sorted(edits,reverse=True):text=text[:a]+expr+text[b:]
 return text

def prepare():
 DEST.mkdir(parents=True,exist_ok=True)
 for path in SOURCE.iterdir():
  if path.name in {'3dmodels','.DS_Store'} or path.suffix in {'.kicad_prl','.md','.json'}:continue
  target=DEST/path.name
  if path.is_dir():shutil.copytree(path,target,dirs_exist_ok=True)
  else:shutil.copyfile(path,target)
 # Reuse the same pinned models without duplicating supplier CAD in Git LFS.
 for path in [*DEST.glob('*.kicad_pcb'),*(DEST/'Footprints').rglob('*.kicad_mod')]:
  path.write_text(path.read_text().replace('${KIPRJMOD}/3dmodels/','${KIPRJMOD}/../../lcd-module-2.8/kicad/3dmodels/'))
 rpi=DEST/'rpi_interface.kicad_sch';text=rpi.read_text()
 def change(node,expr):
  if node[0]=='global_label' and node[1]=='MCU_BACKLIGHT' and one(node,'at')[1:3]==['146.05','101.6']:return ''
  if node[0]=='wire' and one(node,'uuid')[1:] == ['db1c0db3-b224-40ef-bc5d-488ca98e8720']:return ''
  if node[0]=='global_label' and (node[1]=='I2C-SDA' or (node[1]=='MCU_BACKLIGHT' and one(node,'at')[1:3]==['128.27','43.18'])):
   return expr.replace('"'+node[1]+'"','"LCD_PWM"',1)
  return expr
 text=update(text,change)
 text=text.rstrip()[:-1]+'\n(no_connect (at 157.48 101.6) (uuid "'+uid('JP204-unused')+'"))\n)\n'
 power=(SOURCE/'Power.kicad_sch').read_text()
 lib=node_text(power,lambda n:n[:2]==['symbol','Device:R_US'])
 libs=node_text(text,lambda n:n[0]=='lib_symbols')
 text=text.replace(libs,libs[:-1]+'\n'+lib+'\n)',1)
 resistor=node_text(power,lambda n:n[0]=='symbol' and any(p[1:3]==['Reference','R301'] for p in children(n,'property')))
 oldxy=[154.94,96.52];newxy=[190.5,43.18]
 def shift(n,expr):
  if n[0]=='at':
   vals=n[1:];return '(at '+str(round(float(vals[0])+newxy[0]-oldxy[0],4))+' '+str(round(float(vals[1])+newxy[1]-oldxy[1],4))+' '+' '.join(vals[2:])+')'
  return expr
 resistor=update(resistor,shift).replace('R301','R703')
 old_id=one(parse(resistor),'uuid')[1]
 resistor=resistor.replace(old_id,R_ID)
 resistor=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+uid('resistor:'+m[1])+'")' if m[1]!=R_ID else m[0],resistor)
 rpi_path=one(one(one(next(n for n in children(parse(text),'symbol') if any(p[1:3]==['Reference','JP202'] for p in children(n,'property'))),'instances'),'project'),'path')[1]
 resistor=re.sub(r'\(path "[^"]+"','(path "'+rpi_path+'"',resistor)
 def label(name,x,y):
  return f'(global_label "{name}" (shape input) (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid(name+str(x)+str(y))}"))'
 text=text.rstrip()[:-1]+'\n'+resistor+'\n'+label('LCD_PWM',190.5,39.37)+'\n'+label('GND',190.5,46.99)+'\n)\n'
 rpi.write_text(text)
 board=DEST/'SeedSigner-Plus-smartcard-pico.kicad_pcb'
 def pcb_change(n,expr):
  if n[0] in {'segment','via'} and one(n,'net')[-1:] == ['MCU_BACKLIGHT']:return ''
  if n[0]=='net' and n[-1]=='I2C-SDA':return expr.replace('"I2C-SDA"','"LCD_PWM"')
  if n[0]=='footprint' and any(p[1:3]==['Reference','JP202'] for p in children(n,'property')):
   return expr.replace('"MCU_BACKLIGHT"','"LCD_PWM"')
  return expr
 board_text=update(board.read_text(),pcb_change).replace('0.0.7-dev','0.0.8-dev').replace('"MCU_BACKLIGHT"','"unconnected-(JP204-A-Pad1)"')
 original=node_text(board_text,lambda n:n[0]=='footprint' and any(p[1:3]==['Reference','R301'] for p in children(n,'property')))
 original_node=parse(original);old_path=one(original_node,'path')[1]
 cloned=original.replace('"R301"','"R703"').replace(old_path,rpi_path+'/'+R_ID)
 old_uuid=one(original_node,'uuid')[1]
 cloned=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+(R_ID if m[1]==old_uuid else uid('footprint:'+m[1]))+'")',cloned)
 # Assign new pad nets before loading the native model.
 def pad_change(n,expr):
  if n[0]=='pad':
   old=one(n,'net')[-1];new='LCD_PWM' if n[1]=='1' else 'GND'
   return expr.replace('"'+old+'"','"'+new+'"')
  return expr
 cloned=update(cloned,pad_change)
 board.write_text(board_text.rstrip()[:-1]+'\n'+cloned+'\n)\n')
 return rpi_path

if '--worker' in sys.argv:
 import wx
 wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
 import pcbnew as p
 board=DEST/'SeedSigner-Plus-smartcard-pico.kicad_pcb';b=p.LoadBoard(str(board));fps={f.GetReference():f for f in b.GetFootprints()}
 def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
 net=b.FindNet('LCD_PWM')
 resistor=fps['R703']
 resistor.SetPosition(vec(150,107));resistor.SetOrientationDegrees(90)
 if resistor.GetLayer()!=p.F_Cu:resistor.Flip(resistor.GetPosition(),False)
 resistor.SetOrientationDegrees(90)
 for pad in resistor.Pads():pad.SetNet(net if pad.GetNumber()=='1' else b.FindNet('GND'))
 resistor.Reference().SetPosition(vec(150,104.5));resistor.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 def route(points,n,layer=p.F_Cu):
  for a,z in zip(points,points[1:]):
   t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetNet(n);b.Add(t)
 route([[85.3475,94.44],[82,94.44],[80.5,95.94],[80.5,106],[82.5,108]],net,p.B_Cu)
 route([[82.5,108],[95,108],[97,106],[104,106],[106,108],[150,108],[157,108],[157,103]],net)
 route([[157,103],[157,100.8]],net,p.B_Cu)
 route([[157,100.8],[157,91.2]],net)
 route([[157,91.2],[157,88.5]],net,p.B_Cu)
 route([[157,88.5],[157,86.2]],net)
 route([[157,86.2],[157,84.6],[158.989,83.2866]],net,p.B_Cu)
 def via(x,y,n):
  v=p.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(n);b.Add(v)
 for x,y in [(82.5,108),(157,103),(157,100.8),(157,91.2),(157,88.5),(157,86.2)]:via(x,y,net)
 # Resistor pad 2 gets a local ground via, connected into the existing plane.
 pad2=next(pad for pad in resistor.Pads() if pad.GetNumber()=='2');xy=pad2.GetPosition();x,y=p.ToMM(xy.x),p.ToMM(xy.y)
 route([[x,y],[x+2,y]],b.FindNet('GND'));via(x+2,y,b.FindNet('GND'))
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(board),b)
 sys.exit(0)

if __name__=='__main__':
 base_sha=hashlib.sha256((SOURCE/'SeedSigner-Plus-smartcard-pico.kicad_pcb').read_bytes()).hexdigest()
 assert base_sha==BASE_SHA,'Released baseline changed; review recipe before rebuilding'
 path=prepare()
 python=ROOT/'.tools/kicad-10/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3'
 subprocess.run([str(python),__file__,'--worker',path],check=True)
 cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
 out=ROOT/'dist/backlight-pwm';out.mkdir(parents=True,exist_ok=True)
 board=DEST/'SeedSigner-Plus-smartcard-pico.kicad_pcb'
 for args in [['sch','erc','--format','json','--severity-all','--output',out/'erc.json',board.with_suffix('.kicad_sch')],['pcb','drc','--format','json','--schematic-parity','--severity-all','--refill-zones','--output',out/'drc.json',board]]:
  subprocess.run([str(cli),*map(str,args)],check=True)
 assert hashlib.sha256((SOURCE/'SeedSigner-Plus-smartcard-pico.kicad_pcb').read_bytes()).hexdigest()==base_sha

 # Independent preservation and backlight-mode assertions, beyond native parity.
 old=parse((SOURCE/board.name).read_text());new=parse(board.read_text())
 def footprints(tree):return {next(p[2] for p in children(f,'property') if p[1]=='Reference'):f for f in children(tree,'footprint')}
 original=footprints(old);current=footprints(new)
 assert set(current)==set(original)|{'R703'}
 def pads(f):return {p[1]:one(p,'net')[-1] for p in children(f,'pad') if one(p,'net')}
 exceptions={('U202','14'):'LCD_PWM',('JP202','1'):'LCD_PWM',('JP204','1'):'unconnected-(JP204-A-Pad1)'}
 for ref,f in original.items():
  assert one(f,'at')==one(current[ref],'at') and one(f,'layer')==one(current[ref],'layer'),ref+' moved'
  for number,name in pads(f).items():assert pads(current[ref])[number]==exceptions.get((ref,number),name),(ref,number)
 def copper(tree):return {one(t,'uuid')[1]:t for key in ('segment','via') for t in children(tree,key)}
 newer=copper(new)
 removed=[]
 for identifier,t in copper(old).items():
  name=one(t,'net')[-1]
  if name=='MCU_BACKLIGHT':
   assert identifier not in newer;removed.append(identifier);continue
  assert identifier in newer,'Original copper dropped'
  assert one(newer[identifier],'net')[-1]==('LCD_PWM' if name=='I2C-SDA' else name),'Original copper changed net'
  for key in ('start','end','at','width','size','drill','layer','layers'):
   assert one(t,key)==one(newer[identifier],key),'Original copper geometry changed'
 assert pads(current['R703'])=={'1':'LCD_PWM','2':'GND'}
 assert 'Bridged' in current['JP201'][1] and '_Open_' in current['JP202'][1]
 def joined(a,z,closed):
  graph={}
  for ref in closed:
   n=pads(current[ref]);x,y=n['1'],n['2'];graph.setdefault(x,set()).add(y);graph.setdefault(y,set()).add(x)
  todo=[a];seen=set()
  while todo:
   x=todo.pop()
   if x==z:return True
   if x not in seen:seen.add(x);todo.extend(graph.get(x,set()))
  return False
 default=['JP201','JP203','JP205'];pwm=['JP202','JP203','JP205']
 assert joined('+3.3V','RPI_BACKLIGHT',default)
 assert not joined('LCD_PWM','RPI_BACKLIGHT',default)
 assert joined('LCD_PWM','RPI_BACKLIGHT',pwm)
 assert not joined('+3.3V','RPI_BACKLIGHT',pwm)
 assert joined(pads(current['U202'])['6'],pads(current['J701'])['4'],default)
 assert joined(pads(current['U202'])['6'],pads(current['J701'])['4'],pwm)
 checks={}
 for kind in ('erc','drc'):
  report=json.loads((out/f'{kind}.json').read_text())
  violations=report.get('violations',[])+[v for sh in report.get('sheets',[]) for v in sh['violations']]
  checks[kind]={'violations':len(violations),'unconnected':len(report.get('unconnected_items',[])),'parity':len(report.get('schematic_parity',[]))}
  assert not violations and not report.get('unconnected_items') and not report.get('schematic_parity'),kind+' failed'
 summary={'revision':'0.0.8-dev candidate','baseBoardSha256':base_sha,'boardSha256':hashlib.sha256(board.read_bytes()).hexdigest(),
  'nativeChecks':checks,'preservedExistingComponentPoses':len(original),'preservedOriginalCopperNetAssignments':True,
  'obsoleteBacklightSegmentsRemoved':len(removed),'defaultMode':'Always on: JP201 closed, JP202 open',
  'optionalMode':'PWM: JP201 open, JP202 closed; JP203/JP205 closed and JP204/JP206 open in both modes',
  'pwm':{'moduleHeaderPin':14,'gpio':'GPIO1_D2','function':'PWM0_M1','logicVolts':3.3,'pullDown':'R703 5.1 kohm 0805, C27834; 0.647 mA at 3.3 V'},
  'qualification':'Hardware route and topology verified; module PWM frequency/duty response and final OS pinmux require bench qualification. Existing released PCB/cart assets unchanged.'}
 (DEST.parent/'check-results.json').write_text(json.dumps(summary,indent=2)+'\n')
 for side,layers in [('top','F.Cu,F.SilkS,Edge.Cuts'),('bottom','B.Cu,B.SilkS,Edge.Cuts')]:
  subprocess.run([str(cli),'pcb','export','svg','--layers',layers,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--output',str(out/f'pcb-{side}.svg'),str(board)],check=True)
 print(json.dumps(summary,indent=2))

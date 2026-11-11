#!/usr/bin/env python3
"""Recorded native serviceability revision: SMT Keystone points and bracket mounts."""
from pathlib import Path
import hashlib,json,math,re,runpy,shutil,subprocess,sys,time,uuid
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'hardware';K=V/'kicad';PCB=K/'SeedSigner-Plus-smartcard-pico.kicad_pcb'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));parse,one,children=sx['parse'],sx['one'],sx['children']
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-service:'+key))
POINTS=[('TP901','+5V','+5V',105,120,'F.Cu'),('TP902','GND','GND',112,120,'F.Cu'),('TP903','HOST3V3','+3.3V',174,79.5,'B.Cu'),('TP904','GND','GND',174,85.5,'B.Cu'),('TP905','LCD3V3','LCD_3V3',108,59.5,'B.Cu'),('TP906','GND','GND',114,59.5,'B.Cu'),('TP907','TX>SC','UART_TX',120,59.5,'B.Cu'),('TP908','RX<SC','UART_RX',126,59.5,'B.Cu')]
MOUNTS=[('H705',78,65.679),('H706',187,65.679),('H707',78,113.479),('H708',187,113.479)]
def expression(text,predicate):return next(e for _,_,e in sx['expressions'](text) if predicate(parse(e)))
def replace_nodes(text,callback):
 edits=[]
 for a,b,e in sx['expressions'](text):
  n=parse(e);changed=callback(n,e)
  if changed!=e:edits.append((a,b,changed))
 # Only non-overlapping replacements are allowed.
 selected=[]
 for a,b,e in sorted(edits):
  if selected and a<selected[-1][1]:continue
  selected.append((a,b,e))
 for a,b,e in reversed(selected):text=text[:a]+e+text[b:]
 return text

def prepare():
 before=PCB.read_bytes();assert b'TP901' not in before,'Service revision already applied'
 backup=ROOT/'.tools/pcb-edits'/f'service-{time.time_ns()}';backup.mkdir(parents=True)
 for f in [PCB,*K.glob('*.kicad_sch')]:shutil.copyfile(f,backup/f.name)
 (V/'service-baseline.json').write_text(json.dumps({'boardSha256':hashlib.sha256(before).hexdigest(),'retainedFittedRefs':[f'SW{i}' for i in range(501,509)]+['J301','J601','U601','U701'],'previousRevision':'0.0.9-dev base artwork with four-layer conversion'},indent=2)+'\n')
 source=ROOT/'.tools/kicad-10/KiCad/KiCad.app/Contents/SharedSupport/footprints/TestPoint.pretty/TestPoint_Keystone_5015_Micro_Mini.kicad_mod'
 fp=source.read_text().replace('"TestPoint_Keystone_5015_Micro_Mini"','"Keystone_5015"',1).replace('${KICAD10_3DMODEL_DIR}/TestPoint.3dshapes/TestPoint_Keystone_5015_Micro_Mini.step','${KIPRJMOD}/3dmodels/vendor/Keystone-5015-envelope.step')
 (K/'Footprints/ShieldSigner.pretty/Keystone_5015.kicad_mod').write_text(fp)
 text=before.decode();j302=expression(text,lambda n:n[0]=='footprint' and any(q[1:3]==['Reference','J302'] for q in children(n,'property')));text=text.replace(j302,'',1)
 power=K/'Power.kicad_sch';sch=power.read_text();j=expression(sch,lambda n:n[0]=='symbol' and any(q[1:3]==['Reference','J302'] for q in children(n,'property')));schpath=one(one(one(parse(j),'instances'),'project'),'path')[1]
 remove={'39c2fec7-2069-4455-8fe3-33a7d34f01f0','a9a068c0-3419-4f3f-b395-6ea1a92c3115','d6c0be07-f72e-45f5-9ea7-1f1450e9adbc'}
 def clean(n,e):
  if n[0]=='symbol' and any(q[1:3] in [['Reference','J302'],['Reference','#PWR0309']] for q in children(n,'property')):return ''
  if n[0]=='wire' and one(n,'uuid')[1] in remove:return ''
  if n[0]=='text' and n[1].startswith(('Power indication','J302 shares')):return ''
  return e
 sch=replace_nodes(sch,clean)
 rpi=(K/'rpi_interface.kicad_sch').read_text();lib=expression(rpi,lambda n:n[:2]==['symbol','Connector:TestPoint']);libs=expression(sch,lambda n:n[0]=='lib_symbols');sch=sch.replace(libs,libs[:-1]+'\n'+lib+'\n)',1)
 additions=[]
 for i,(ref,label,net,x,y,layer) in enumerate(POINTS):
  xx=35.56+i*30.48;yy=139.7;sid=uid(ref+':symbol')
  props=f'(property "Reference" "{ref}" (at {xx+2.54} {yy-5.08} 0) (effects (font (size 1.1 1.1)) (justify left))) (property "Value" "5015" (at {xx+2.54} {yy-2.54} 0) (effects (font (size 1.1 1.1)) (justify left))) (property "Footprint" "ShieldSigner:Keystone_5015" (at {xx} {yy} 0) (effects (font (size 1 1)) (hide yes))) (property "LCSC" "C2906768" (at {xx} {yy} 0) (effects (font (size 1 1)) (hide yes))) (property "MPN" "5015" (at {xx} {yy} 0) (effects (font (size 1 1)) (hide yes)))'
  additions.append(f'(symbol (lib_id "Connector:TestPoint") (at {xx} {yy} 0) (unit 1) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{sid}") {props} (pin "1" (uuid "{uid(ref+":pin")}")) (instances (project "SeedSigner-Plus-smartcard-pico" (path "{schpath}" (reference "{ref}") (unit 1)))))')
  additions.append(f'(wire (pts (xy {xx} {yy}) (xy {xx} {yy+5.08})) (stroke (width 0) (type default)) (uuid "{uid(ref+":wire")}"))')
  additions.append(f'(global_label "{net}" (shape bidirectional) (at {xx} {yy+5.08} 0) (effects (font (size 1.0 1.0)) (justify left)) (uuid "{uid(ref+":net")}"))')
  part=fp.replace('(footprint "Keystone_5015"','(footprint "ShieldSigner:Keystone_5015"',1).replace('(layer "F.Cu")',f'(layer "F.Cu")\n(at {x} {y})',1).replace('"REF**"',f'"{ref}"',1).replace('"TestPoint_Keystone_5015_Micro_Mini"','"5015"')
  part=part.replace('(property "Value" "Keystone_5015"','(property "Value" "5015"')
  part=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+uid(ref+':'+m[1])+'")',part)
  extra=f'(uuid "{uid(ref+":footprint")}") (path "{schpath}/{sid}") (property "LCSC" "C2906768" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1)))) (property "MPN" "5015" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1))))'
  text=text.rstrip()[:-1]+part.rstrip()[:-1]+extra+'\n)\n)\n'
 additions.append(f'(text "FACTORY-ASSEMBLED SERVICE POINTS: Keystone 5015 / C2906768" (at 25.4 124.46 0) (effects (font (size 1.4 1.4) (bold yes)) (justify left)) (uuid "{uid("heading")}"))')
 additions.append(f'(text "TP901 / TP902 replace the optional J302 header: regulated 5 V bench input only. Disconnect all USB power before injection.\nNo source selection or reverse-polarity protection. Use current limiting; probe loops are not a strain-relieved power connector.\nTP903-TP908 are on the rear service edge: 3.3 V rails, host UART and local grounds. All eight loops are factory SMT placements." (at 25.4 162.56 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid("power-note")}"))')
 sch=sch.rstrip()[:-1]+'\n'+'\n'.join(additions)+'\n)\n'
 sch=re.sub(r'"(?:\\.|[^"\\])*"',lambda m:m[0].replace('\n','\\n'),sch,flags=re.S)
 power.write_text('\n'.join(line.rstrip() for line in sch.splitlines())+'\n')
 hole=(K/'Footprints/MountingHole.pretty/MountingHole_2.7mm_M2.5.kicad_mod').read_text()
 hole=replace_nodes(hole,lambda n,e:'' if n[0]=='model' else e)
 for ref,x,y in MOUNTS:
  part=hole.replace('(footprint "MountingHole_2.7mm_M2.5"','(footprint "MountingHole:MountingHole_2.7mm_M2.5"',1).replace('(layer "F.Cu")',f'(layer "F.Cu")\n(at {x} {y})',1).replace('"H701"',f'"{ref}"',1)
  part=re.sub(r'\(uuid "([^"]+)"\)',lambda m:'(uuid "'+uid(ref+':'+m[1])+'")',part)
  part=re.sub(r'\(attr[^)]*\)','(attr board_only exclude_from_bom exclude_from_pos_files)',part)
  part=part.rstrip()[:-1]+f'(uuid "{uid(ref)}")\n)'
  points=' '.join(f'(xy {x+3*math.cos(i*math.tau/64):.6f} {y+3*math.sin(i*math.tau/64):.6f})' for i in range(64))
  zone=f'(zone (layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu") (uuid "{uid(ref+":keepout")}") (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) (fill (thermal_gap .5) (thermal_bridge_width .5)) (polygon (pts {points})))'
  text=text.rstrip()[:-1]+part+'\n'+zone+'\n)\n'
 PCB.write_text(text)
 config={'revision':'0.0.11-dev','part':{'manufacturer':'Keystone','mpn':'5015','lcsc':'C2906768','footprint':'ShieldSigner:Keystone_5015','assembly':'factory SMT','source':'https://www.keyelco.com/product-pdf.cfm?p=1353'},'testpoints':[{'ref':r,'label':l,'net':n,'xy':[x,y],'layer':side} for r,l,n,x,y,side in POINTS],'bracketMounts':[{'ref':r,'xy':[x,y],'drillMm':2.7,'keepoutDiameterMm':6,'fastener':'M2.5; head/washer OD <= 5 mm'} for r,x,y in MOUNTS],'mountSpacingMm':[109,47.8],'existingEnclosure':'Existing four LCD support holes unchanged; new mounts are for custom brackets, not new posts in the existing shell.'}
 (V/'serviceability.json').write_text(json.dumps(config,indent=2)+'\n')
 selection=V/'bom-selection-extra.json';data=json.loads(selection.read_text());data.update({r:{'lcsc':'C2906768','mpn':'5015'} for r,*_ in POINTS});selection.write_text(json.dumps(data,indent=2)+'\n')
 return backup

if '--worker' in sys.argv:
 import wx
 wx.Log.SetLogLevel(wx.LOG_Error);app=wx.App(False)
 import pcbnew as p
 b=p.LoadBoard(str(PCB));fps={f.GetReference():f for f in b.GetFootprints()}
 def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
 def route(points,net,layer=p.F_Cu,width=.25):
  for a,z in zip(points,points[1:]):
   t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNet(b.FindNet(net));b.Add(t)
 def via(x,y,net):
  v=p.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
 for ref,label,net,x,y,layer in POINTS:
  f=fps[ref]
  if layer=='B.Cu':f.Flip(f.GetPosition(),False)
  f.SetOrientationDegrees(0)
  next(iter(f.Pads())).SetNet(b.FindNet(net));f.Reference().SetVisible(False);f.Value().SetVisible(False)
  # Net-first labels remain legible when fitted; designators are in fabrication data.
  item=p.PCB_TEXT(b);item.SetText(label);item.SetLayer(p.F_SilkS if layer=='F.Cu' else p.B_SilkS);item.SetMirrored(layer=='B.Cu');item.SetPosition(vec(x,y+(2.4 if layer=='F.Cu' else -2.5)));item.SetTextSize(vec(.8,.8));item.SetTextThickness(p.FromMM(.13));b.Add(item)
 for ref,x,y in MOUNTS:
  f=fps[ref];f.Reference().SetVisible(False);f.Value().SetVisible(False)
  for layer in [p.F_SilkS,p.B_SilkS]:
   label=p.PCB_TEXT(b);label.SetText(ref+' M2.5');label.SetPosition(vec(x,y+4.1));label.SetTextSize(vec(.8,.8));label.SetTextThickness(p.FromMM(.13));label.SetLayer(layer);label.SetMirrored(layer==p.B_SilkS);b.Add(label)
 # Preserve branding shapes, relocating the complete right rear group by 7 mm.
 for item in b.GetDrawings():
  if item.GetLayer()!=p.B_SilkS:continue
  if isinstance(item,p.PCB_TEXT) and item.GetText() in ['LightningSpore','OPEN HARDWARE','denver.space']:item.Move(vec(0,-7));continue
  if isinstance(item,p.PCB_SHAPE):
   bb=item.GetBoundingBox()
   if p.ToMM(bb.GetX())>169 and p.ToMM(bb.GetY())>75:item.Move(vec(0,-7))
 for item in b.GetDrawings():
  if isinstance(item,p.PCB_TEXT):
   if '0.0.9-dev' in item.GetText():item.SetText(item.GetText().replace('0.0.9-dev','0.0.11-dev 4L'))
   if item.GetText() in ['5V USB-C','POWER ONLY']:pass
 # Remove the obsolete header labels, retaining all unrelated artwork.
 for item in list(b.GetDrawings()):
  if isinstance(item,p.PCB_TEXT) and item.GetText() in ['5V','GND']:
   at=item.GetPosition()
   if p.ToMM(at.y)>118 and 102<p.ToMM(at.x)<111:b.Remove(item)
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(PCB),b)
 print('Saved serviceability layout candidate with',len(list(b.GetFootprints())),'footprints')
 sys.exit(0)
if __name__=='__main__':
 backup=prepare();cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']();python=cli.parent.parent/'Frameworks/Python.framework/Versions/3.9/bin/python3'
 subprocess.run([str(python),__file__,'--worker'],check=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/refine-pill-service.py')],check=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/label-pill-service.py')],check=True)
 print('Original files:',backup)

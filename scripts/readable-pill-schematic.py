#!/usr/bin/env python3
"""One-time, presentation-only native schematic cleanup, retaining symbol UUIDs."""
from pathlib import Path
import hashlib,json,re,runpy,time,uuid
ROOT=Path(__file__).resolve().parents[1];K=ROOT/'hardware/kicad'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));parse,one,children=sx['parse'],sx['one'],sx['children']
backup=ROOT/'.tools/schematic-edits'/str(time.time_ns());backup.mkdir(parents=True)
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-readable:'+key))
def quote(s):return json.dumps(s)
def text(key,value,x,y,size=1.27,bold=False):
 return f'(text {quote(value)} (at {x} {y} 0) (effects (font (size {size} {size}) {"(bold yes)" if bold else ""}) (justify left)) (uuid "{uid(key)}"))'
def line(key,x,y,xx,yy):
 return f'(polyline (pts (xy {x} {y}) (xy {xx} {yy})) (stroke (width 0.254) (type default)) (uuid "{uid(key)}"))'
def shift(expr,dx,dy):
 return re.sub(r'\((at|xy) (-?[\d.]+) (-?[\d.]+)',lambda m:f'({m[1]} {float(m[2])+dx:.5f} {float(m[3])+dy:.5f}',expr)
def prop_hide(expr,name):
 for a,b,e in sorted(sx['expressions'](expr),reverse=True):
  n=parse(e)
  if n[:2]==['property',name] and '(hide yes)' not in e:
   pos=e.rfind(')');q=e[:pos].rstrip();last=q.rfind(')');q=q[:last]+' (hide yes)'+q[last:]+e[pos:];expr=expr[:a]+q+expr[b:]
 return expr
notes={}
notes['Power.kicad_sch']=[
 text('power-head','USB-C 5 V input, bypass and protection',25.4,25.4,2,True),
 text('power-sub','Power only: USB data is not connected. Follow +5V to the host, reader and display regulator.',25.4,33.02),
 text('power-cc','USB-C sink identification\nR301 / R302: 5.1 kOhm to GND\nEach CC pin has its own pull-down.',25.4,109.22),
 text('power-protect','Input bypass and transient protection\nC301: 100 nF; C302: 10 uF\nD301: SMF5.0CA TVS across the 5 V rail.',104.14,109.22),
 text('power-led','Power indication\nD302 + R303: 560 Ohm LED branch\nJ302: optional customer power header.',190.5,109.22),
 text('power-caution','J302 shares +5V directly with USB VBUS. No source selection or reverse-current isolation is provided.\nUse one external 5 V source at a time. The USB input does not negotiate USB-PD voltages.',25.4,144.78),
]
notes['buttons.kicad_sch']=[
 text('buttons-head','User controls: five navigation contacts + three keys',25.4,25.4,2,True),
 text('buttons-sub','Every switch pulls its named host signal to GND when pressed. Configure host pull-ups and software debounce.',25.4,33.02),
 text('buttons-nav','NAVIGATION',38.1,48.26,1.5,True),text('buttons-keys','ACTION KEYS',203.2,48.26,1.5,True),
 text('buttons-foot','SW501-SW508: C&K PTS636SK25SMTRLFS momentary switches.\nThe placement below follows the physical control arrangement. Net names match the host sheet.',25.4,152.4),
]
notes['smartcard_reader.kicad_sch']=[
 text('card-head','SEC1210 UART reader and smartcard contacts',17.78,22.86,2,True),
 text('card-sub','Host UART at left; card channel 1 at right. Channel 2, USB and JTAG pins are intentionally unused.',17.78,30.48),
 text('card-reset','RESET AND TEST\nR601 / C601: reset pull-up and delay\nR607: TEST pull-down',17.78,155),
 text('card-decouple','LOCAL BYPASS\nC602: 5 V input, 1 uF\nC603: VDD33 output, 1 uF\nC604: card supply, 1 uF',91.44,158.75),
 text('card-filter','CARD INTERFACE\nR604: 47 Ohm clock series damping\nC605 / C606: 33 pF; R605 / R606: bias\nJ601: combined SIM / full-size card socket',167.64,155),
]
notes['lcd_module.kicad_sch']=[
 text('lcd-head','Eight-pin SPI display and dedicated 3.3 V supply',25.4,25.4,2,True),
 text('lcd-sub','J701 is the module header, not a 40-pin bare-panel FPC. Display power is independent of the Luckfox 3.3 V output.',25.4,33.02),
 text('lcd-reg','DISPLAY SUPPLY',45.72,48.26,1.5,True),text('lcd-header','J701: CARRIER PIN NUMBERS',177.8,48.26,1.5,True),
 text('lcd-bypass','C701 / C702: 10 uF, 25 V X5R\nMaintain at least 1 uF effective capacitance.\nMeasure regulator dissipation during bring-up.',38.1,109.22),
 text('lcd-map','MODULE MATING / NUMBERING\nCarrier pin 1 (BL) mates to module J1 pin 8 (BL_E).\nCarrier pin 8 (3V3) mates to module J1 pin 1 (VCC).\nUse the 2.54 mm J1 row, not the 2 mm J2 connector.',154.94,109.22),
 text('lcd-straps','Factory straps: JP201 / JP203 / JP205 closed; JP202 / JP204 / JP206 open.\nBacklight is always on. The separate PWM candidate has different hardware; see its own schematic.',38.1,147.32),
]
# Root page: actual hierarchical blocks plus a non-electrical reading guide.
root='SeedSigner-Plus-smartcard-pico.kicad_sch'
notes[root]=[
 text('overview-head','ShieldSigner | eight-pin pill carrier',22.86,22.86,2.54,True),
 text('overview-sub','Native KiCad reference | 160 x 70 mm | four copper layers | 1.6 mm nominal thickness',22.86,33.02),
 text('overview-read','READING MAP  (lines below describe system flow; connections use named nets on the circuit sheets)',22.86,44.45,1.1),
 text('overview-power','+5V input, USB-C CC, TVS\nand optional power header',30.48,77.47),
 text('overview-host','Luckfox Pico Mini, I/O map\nand factory configuration straps',109.22,77.47),
 text('overview-display','8-pin SPI module + AP2112\nDedicated LCD_3V3 supply',203.2,77.47),
 text('overview-buttons','Active-low navigation and keys\nUse host pull-ups and debounce',30.48,125.73),
 text('overview-card','UART reader, reset, bypass\nand combined smartcard socket',109.22,125.73),
 line('flow-power',85.09,63.5,101.6,63.5),text('flow-power-name','+5V',87.63,58.42,1),
 line('flow-spi',166.37,63.5,195.58,63.5),text('flow-spi-name','SPI / control',170.18,58.42,1),
 line('flow-keys',63.5,99.06,63.5,91.44),line('flow-keys2',63.5,91.44,133.35,91.44),line('flow-keys3',133.35,91.44,133.35,73.66),
 text('flow-keys-name','button GPIO',68.58,88.9,1),line('flow-uart',147.32,73.66,147.32,99.06),text('flow-uart-name','UART',149.86,88.9,1),
 text('overview-default','ASSEMBLY DEFAULT\nJP201 / JP203 / JP205 closed\nJP202 / JP204 / JP206 open\nBacklight always on; eight-pin J701.',203.2,104.14),
 text('overview-stack','STACKUP / REVIEW\nF.Cu signals / In1.Cu GND / In2.Cu GND / B.Cu signals. Confirm the nominal stackup with the fabricator.\nThe 0.0.9-dev silkscreen is the base artwork; historical two-layer quote kits do not describe this working PCB.\nERC / DRC are software checks. Module fit, powered operation and supplier assembly remain unqualified.',22.86,153.67,1.1),
]
notes['rpi_interface.kicad_sch']=[
 text('host-head','Host module, signal mapping and assembly straps',17.78,20.32,2,True),
 text('host-sub','U202 is fitted. U201 is a schematic-only legacy interface reference; it is not a second module or an assembly part.',17.78,27.94,1.1),
 text('host-legacy','LEGACY INTERFACE REFERENCE ONLY\nU201 and TP201 have no PCB footprint.',17.78,58.42,1.1,True),
 text('host-default','FACTORY STRAP TABLE\nJP201 closed / JP202 open: backlight held high\nJP203 closed / JP204 open: GPIO1_C0 drives CS\nJP205 closed / JP206 open: GPIO-controlled CS\nNever close both alternatives in a strap pair.',17.78,151.13,1.1),
 text('host-bl','BACKLIGHT SOURCE\nJP202 selects MCU_BACKLIGHT only in an alternate configuration.\nThis PCB has no dedicated host PWM path; use the separate PWM candidate.',116.84,152.4,1.0),
 text('host-firmware','HOST FIRMWARE\nUse the carrier GPIO map and 320 x 240 display profile.\nThe 240 x 240 bench image conflicts with two button nets.',116.84,172.72,1.0),
 text('host-jp201','BACKLIGHT: default high',116.84,38.1,1.1,True),
 text('host-jp205','CHIP SELECT: default GPIO',203.2,38.1,1.1,True),
 text('host-jp203','GPIO1_C0 FUNCTION',124.46,80.01,1.1,True),
]
titles={root:'System overview and reading map','rpi_interface.kicad_sch':'Host module and configuration','Power.kicad_sch':'USB-C power input and protection','buttons.kicad_sch':'Navigation and action keys','smartcard_reader.kicad_sch':'SEC1210 UART smartcard reader','lcd_module.kicad_sch':'Eight-pin SPI display and regulator'}
assert not any(uid('overview-head') in f.read_text() for f in K.glob('*.kicad_sch')),'Already cleaned; do not replay'
audit={}
for filename,title in titles.items():
 path=K/filename;before=path.read_text();(backup/filename).write_text(before)
 assert uid('overview-head') not in before,'Already cleaned'
 spans=[]
 # Only mutate direct children; cached library symbol geometry stays untouched.
 tree=parse(before)
 # Span scanner yields nested nodes too; depth-one spans are selected by containment.
 allspans=list(sx['expressions'](before));outer=sorted([(a,b,e) for a,b,e in allspans if a>0],key=lambda x:x[0]);end=-1
 for a,b,expr in outer:
  if a<end:continue
  end=b;n=parse(expr);kind=n[0];new=expr
  if kind=='title_block':new=''
  if kind=='text':new='' # Superseded by reviewed, current annotations.
  if filename==root and kind=='sheet':
   prop=next(p for p in children(n,'property') if p[1]=='Sheetfile');target={'Power.kicad_sch':(25.4,53.34,59.69,20.32),'rpi_interface.kicad_sch':(101.6,53.34,64.77,20.32),'lcd_module.kicad_sch':(195.58,53.34,73.66,20.32),'buttons.kicad_sch':(25.4,99.06,59.69,20.32),'smartcard_reader.kicad_sch':(101.6,99.06,64.77,20.32)}[prop[2]]
   x,y,w,h=target;ox,oy=map(float,one(n,'at')[1:3]);new=shift(expr,x-ox,y-oy);new=re.sub(r'\(size [\d.]+ [\d.]+\)',f'(size {w} {h})',new,count=1)
   # File property sits beneath each sheet regardless of its old height.
   for aa,bb,ee in sorted(sx['expressions'](new),reverse=True):
    pn=parse(ee)
    if pn[:2]==['property','Sheetfile']:
     ee=re.sub(r'\(at [\d.-]+ [\d.-]+ 0\)',f'(at {x} {y+h+1.27} 0)',ee);new=new[:aa]+ee+new[bb:]
  circuit=kind in ['symbol','wire','junction','label','global_label','no_connect']
  if circuit and filename=='Power.kicad_sch':new=shift(new,-83.82,-5.08)
  if circuit and filename=='buttons.kicad_sch':
   # Show each switch reference; the shared MPN is stated once in a note.
   if kind=='symbol':
    ref=next(p[2] for p in children(n,'property') if p[1]=='Reference')
    if ref.startswith('SW'):new=prop_hide(new,'Value')
   # Whole sheet is placed higher without scaling symbols.
   new=shift(new,-20.32,-10.16)
  if circuit and filename=='smartcard_reader.kicad_sch':
   def dx(x):return 0 if x<=151.13 else 5.08 if x<=163.83 else 12.7 if x<=173.99 else 20.32 if x<=185.42 else 25.4
   if kind=='symbol':
    x=float(one(n,'at')[1]);new=shift(new,dx(x),0)
   else:
    new=re.sub(r'\((at|xy) (-?[\d.]+) (-?[\d.]+)',lambda m:f'({m[1]} {float(m[2])+dx(float(m[2])):.5f} {m[3]}',new)
   if kind=='label':new=new.replace('(size 1.27 1.27)','(size 0.95 0.95)')
   if kind=='symbol':
    ref=next(p[2] for p in children(n,'property') if p[1]=='Reference')
    if ref.startswith(('C','R')):new=new.replace('(size 1.27 1.27)','(size 1.05 1.05)')
  if circuit and filename=='lcd_module.kicad_sch':
   new=shift(new,-7.62,0)
   if kind=='symbol':
    ref=next(p[2] for p in children(n,'property') if p[1]=='Reference')
    if ref in ['C701','C702']:
     # Put capacitor fields right of their body, clear of the wire at the top pin.
     for aa,bb,ee in sorted(sx['expressions'](new),reverse=True):
      pn=parse(ee)
      if pn[:2] in [['property','Reference'],['property','Value']]:ee=shift(ee,13.97,0);new=new[:aa]+ee+new[bb:]
  if circuit and filename=='rpi_interface.kicad_sch':
   if kind=='symbol':
    ref=next(p[2] for p in children(n,'property') if p[1]=='Reference')
    if ref.startswith('JP'):new=prop_hide(new,'Value')
   # Add room above the circuit for a readable heading; keep all wiring on grid.
   new=shift(new,-5.08,12.7)
  if new!=expr:spans.append((a,b,new))
 for a,b,e in sorted(spans,reverse=True):before=before[:a]+e+before[b:]
 tb=f'(title_block (title {quote(title)}) (date "2026-11-08") (rev "4L working") (company "ShieldSigner / LightningSpore") (comment 1 "Derived from 3rdIteration/SeedSigner; original design: Stephen Rothy") (comment 2 "Prototype: physical fit, powered operation and assembly not qualified"))'
 before=before.rstrip()[:-1]+'\n'+tb+'\n'+'\n'.join(notes[filename])+'\n)\n'
 path.write_text('\n'.join(line.rstrip() for line in before.splitlines())+'\n')
 audit[filename]={'beforeSha256':hashlib.sha256((backup/filename).read_bytes()).hexdigest(),'afterSha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(ROOT/'hardware/schematic-readability-audit.json').write_text(json.dumps({'files':audit,'scope':'Presentation only; native ERC, PCB parity and independent netlist comparison required'},indent=2)+'\n')
print('Updated six native sheets; originals at',backup)

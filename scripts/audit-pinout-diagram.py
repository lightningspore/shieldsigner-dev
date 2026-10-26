"""Verify public pinout data against pinned SDK muxes, both native boards and app."""
from pathlib import Path
import hashlib,json,re,runpy
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'docs/luckfox-mini-pinout.json').read_text())
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'));one,children=sx['one'],sx['children']
for source in data['sources']:
 assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256'],source['name']+' changed'
sdk=(ROOT/'reference/pinouts/rv1106-pinctrl-824b817.dtsi').read_text()
muxes={m[1]:(int(m[2]),(ord(m[3])-65)*8+int(m[4]),int(m[5])) for m in re.finditer(r'/\*\s*(\w+)\s*\*/\s*<(\d) RK_P([A-D])(\d) (\d)',sdk)}
assert [p['pin'] for p in data['pins']]==list(range(1,23))
for pin in data['pins']:
 if pin['bank'] is None:continue
 gpio=re.fullmatch(r'GPIO(\d)_([A-D])(\d)',pin['name']);assert gpio
 assert (int(gpio[1]),(ord(gpio[2])-65)*8+int(gpio[3]))==(pin['bank'],pin['offset'])
 assert pin['legacyGpio']==pin['bank']*32+pin['offset']
 assert pin['volts']==(1.8 if pin['bank']==4 else 3.3)
 for alt in pin['alternatives']:
  assert muxes[alt['sourceToken']][:2]==(pin['bank'],pin['offset']),(pin['pin'],alt)
 assert 'GPIO' in pin['functions']
boards={};gpio_count=0
for revision,folder in [('released','lcd-module-2.8'),('candidate','lcd-backlight-pwm')]:
 path=ROOT/f'variants/{folder}/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb';tree=sx['parse'](path.read_text())
 fps={next(x[2] for x in children(f,'property') if x[1]=='Reference'):f for f in children(tree,'footprint')}
 nets={};count=0
 for f in fps.values():
  ref=next(x[2] for x in children(f,'property') if x[1]=='Reference')
  for pad in children(f,'pad'):
   if one(pad,'net'):nets.setdefault(one(pad,'net')[-1],set()).add(ref+'.'+pad[1])
 for pin in data['pins']:
  pads=[p for p in children(fps['U202'],'pad') if p[1]==str(pin['pin'])]
  assert len(pads)==2,(revision,pin['pin'])
  assert all(one(p,'net')[-1]==pin['net'][revision] for p in pads),(revision,pin['pin'])
  count+=len(pads)
  switch=re.search(r'SW\d+',pin['note'][revision])
  if switch:
   ref=switch[0];assert nets[pin['net'][revision]]=={'U202.'+str(pin['pin']),ref+'.1'}
   assert next(one(p,'net')[-1] for p in children(fps[ref],'pad') if p[1]=='2')=='GND'
 # Both independent diagrams use the same footprint/pad orientation.
 host=fps['U202'];assert one(host,'at')[1:]==['103.1275','74.12','180']
 for pin in data['pins']:
  pad=next(p for p in children(host,'pad') if p[1]==str(pin['pin']) and abs(float(one(p,'at')[1])-(0 if pin['pin']<=11 else 17.78))<.001)
  expected=-(pin['pin']-1)*2.54 if pin['pin']<=11 else -(22-pin['pin'])*2.54
  assert abs(float(one(pad,'at')[2])-expected)<.001
 for a,b in [('R602','11'),('R603','14')]:
  expected_pin='4' if a=='R602' else '5'
  assert next(one(p,'net')[-1] for p in children(fps[a],'pad') if p[1]=='1')==data['pins'][int(expected_pin)-1]['net'][revision]
  assert next(one(p,'net')[-1] for p in children(fps[a],'pad') if p[1]=='2')==next(one(p,'net')[-1] for p in children(fps['U601'],'pad') if p[1]==b)
 assert nets['LCD_3V3']=={'U701.5','C702.1','J701.8','TP803.1'}
 if revision=='candidate':
  assert nets['LCD_PWM']=={'U202.14','JP202.1','R703.1'}
 boards[revision]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'physicalPins':22,'padInstancesChecked':count}
upstream=sx['parse']((ROOT/'reference/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_text())
upstream_fps={next(x[2] for x in children(f,'property') if x[1]=='Reference'):f for f in children(upstream,'footprint')}
for n,ref in [(19,'SW506'),(20,'SW507')]:
 expected=data['pins'][n-1]['net']['released']
 assert all(one(p,'net')[-1]==expected for p in children(upstream_fps['U202'],'pad') if p[1]==str(n))
 assert {p[1]:one(p,'net')[-1] for p in children(upstream_fps[ref],'pad')}=={'1':expected,'2':'GND'}
app=json.loads((ROOT/'reference/research/firmware/io-config-efdd1cfd.json').read_text())
fox=next(p for p in app['models'] if p['shortname']=='FOX_22')
buttons={11:'KEY3',12:'KEY_LEFT',13:'KEY_UP',16:'KEY_PRESS',17:'KEY_DOWN',18:'KEY_RIGHT',19:'KEY1',20:'KEY2'}
for n,key in buttons.items():
 pin=data['pins'][n-1];assert fox['buttons'][key]==[f"/dev/gpiochip{pin['bank']}",pin['offset'],'pull_up']
for key,n in [('rst',9),('dc',10)]:
 pin=data['pins'][n-1];assert fox['display'][key]==[f"/dev/gpiochip{pin['bank']}",pin['offset']]
report={'reviewed':data['reviewed'],'boards':boards,'sdkMuxAlternativesChecked':sum(len(p['alternatives']) for p in data['pins']),
 'gpioNumberingChecked':sum(p['bank'] is not None for p in data['pins']),'appButtonMappingsChecked':len(buttons),'appDisplayGpioMappingsChecked':2,'upstream1v8ButtonTopologyMatches':True,
 'findings':[{'kind':'manufacturer_diagram_discrepancy','detail':'Official Mini GPIO image places SPI0_CS1_M0 on pin 15 / GPIO1_D3. Retained schematic and pinned SDK spi0m0_cs1 assign GPIO1_D2 / physical pin 14. Diagram uses the corroborated pin 14 assignment; neither ShieldSigner revision uses a second SPI CS.'},
 {'kind':'documentation_correction','detail':'LCD_3V3 has four component endpoints including TP803, not three.'}],
 'remaining':['Confirm live GPIO chip identities, device-tree muxes and SPI timing on the final image.','Physical voltage/continuity, module revision and optional BL_E PWM response remain bench checks.']}
(ROOT/'docs/luckfox-pinout-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

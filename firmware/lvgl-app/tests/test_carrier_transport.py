"""Pinned real driver classes with simulated periphery, never physical devices."""
import array,ast,dataclasses,errno,hashlib,json,logging,os,re,runpy,stat,sys,threading,types,typing,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'python'))
import hothmi
from luckfox import LuckfoxHardware
from runtime import Runtime,KEYS
import runtime as runtime_module

class CarrierTransportTests(unittest.TestCase):
 def setUp(self):
  source=ROOT/'dist/firmware/sources/lvgl/application/src/seedsigner'
  hashes=json.loads((ROOT/'reference/research/firmware/carrier-runtime-sources.json').read_text())
  self.sources={}
  for name,relative in [('display_driver.py','hardware/displays/display_driver.py'),('ST7789.py','hardware/displays/ST7789.py'),('buttons.py','hardware/buttons.py')]:
   data=(source/relative).read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),hashes[name]['sha256']);self.sources[name]=data.decode()
  self.profile=json.loads((ROOT/'reference/research/firmware/io-config-efdd1cfd.json').read_text())
  # Apply the real profile transform to its exact pinned input, not a recreated
  # pin fixture. Hardware model detection itself remains outside this test.
  import tempfile
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  path=Path(temporary.name)/'io.json';path.write_text((ROOT/'reference/research/firmware/io-config-efdd1cfd.json').read_text())
  helper=runpy.run_path(str(ROOT/'scripts/configure-image-io-profile.py'))
  helper['configure'](path,'carrier');self.profile=helper['selected'](json.loads(path.read_text()))
  self.clock=[0.0];self.pins=[];self.spi=[];self.transfers=[]
  owner=self
  class GPIO:
   def __init__(self,chip,line,direction,**kwargs):
    self.chip=chip;self.line=line;self.direction=direction;self.bias=kwargs.get('bias');self.state=direction=='in';self.closed=False;owner.pins.append(self)
   def write(self,value):self.state=value
   def read(self):return self.state
   def close(self):self.closed=True
  class SPI:
   def __init__(self,*args,**kwargs):self.args=args;self.kwargs=kwargs;self.closed=False;owner.spi.append(self)
   def transfer(self,data):
    dc=next(p for p in owner.pins if p.direction=='out' and p.line==20)
    owner.transfers.append((owner.clock[0],dc.state,bytes(data)));return list(data)
   def close(self):self.closed=True
  self.GPIO=GPIO
  self.fake_time=types.SimpleNamespace(time=lambda:self.clock[0],sleep=lambda t:self.clock.__setitem__(0,self.clock[0]+t))
  module=types.ModuleType('_carrier_real_driver_test');self.addCleanup(sys.modules.pop,module.__name__,None);sys.modules[module.__name__]=module
  module.__dict__.update(dataclass=dataclasses.dataclass,GPIO=GPIO,SPI=SPI,time=self.fake_time,array=array,errno=errno,
    logger=logging.getLogger('carrier-driver-test'),Settings=types.SimpleNamespace(get_platform_default_hardware_config=lambda:'FOX_22'),
    get_hardware_pin_mapping=lambda config:self.profile)
  for filename,name in [('display_driver.py','BaseDisplayDriver'),('ST7789.py','ST7789')]:
   node=next(n for n in ast.parse(self.sources[filename]).body if isinstance(n,ast.ClassDef) and n.name==name)
   exec(compile(ast.Module(body=[node],type_ignores=[]),filename,'exec'),module.__dict__)
  self.Driver=module.ST7789

 def test_real_spi_driver_initializes_hothmi_and_writes_rightmost_rgbw_pixels(self):
  module=types.ModuleType('seedsigner.hardware.displays.ST7789');module.ST7789=self.Driver
  hw=LuckfoxHardware.__new__(LuckfoxHardware);hw.panel_profile=hothmi.PROFILE;hw.lock=threading.Lock();hw.lcd=hw.scaler=hw.buttons=None
  self.addCleanup(hw.close)
  with patch.dict(sys.modules,{module.__name__:module}),patch.object(hothmi.time,'sleep',side_effect=self.fake_time.sleep):hw.configure_display(320,240,False)
  self.assertEqual([(p.chip,p.line,p.direction) for p in self.pins],[('/dev/gpiochip-bank1',20,'out'),('/dev/gpiochip-bank1',19,'out')])
  self.assertEqual(self.spi[0].args,('/dev/spidev0.0',0,10_000_000));self.assertEqual(self.spi[0].kwargs,{'extra_flags':0})
  transactions=[]
  for t,data_mode,data in self.transfers:
   if not data_mode:
    self.assertEqual(len(data),1);transactions.append({'command':data[0],'data':[]})
   else:transactions[-1]['data'].extend(data)
  fixture=json.loads((ROOT/'reference/research/firmware/hothmi-init.json').read_text())
  self.assertEqual(transactions[:-1],[{k:r[k] for k in ('command','data')} for r in fixture['commands']])
  self.assertEqual(transactions[-1],{'command':0x21,'data':[]}) # Normal-color inversion policy.
  rgbw=bytes.fromhex('f80007e0001fffff')
  for left,right,window in [(254,257,bytes.fromhex('00fe0101')),(316,319,bytes.fromhex('013c013f'))]:
   self.transfers.clear();hw.pixels((left,239,right,239),rgbw)
   self.assertEqual([(mode,data) for t,mode,data in self.transfers],
     [(False,b'\x2a'),(True,window),(False,b'\x2b'),(True,bytes.fromhex('00ef00ef')),(False,b'\x2c'),(True,rgbw)])
  hw.close();self.assertTrue(all(p.closed for p in self.pins));self.assertTrue(self.spi[0].closed)

 def test_real_button_allocator_and_lvgl_debounce_cover_all_eight_inputs(self):
  namespace=dict(GPIO=self.GPIO,USING_GPIO=True,Singleton=type('Singleton',(),{'_instance':None}),threading=threading,
    time=self.fake_time,os=os,re=re,stat=stat,Dict=typing.Dict,List=typing.List,Tuple=typing.Tuple,
    Settings=types.SimpleNamespace(get_platform_default_hardware_config=lambda:'FOX_22'),
    get_hardware_pin_mapping=lambda config:self.profile,logger=logging.getLogger('carrier-button-test'))
  node=next(n for n in ast.parse(self.sources['buttons.py']).body if isinstance(n,ast.ClassDef) and n.name=='HardwareButtons')
  exec(compile(ast.Module(body=[node],type_ignores=[]),'pinned buttons.py','exec'),namespace)
  buttons=namespace['HardwareButtons'].get_instance()
  self.addCleanup(lambda:[p.close() for p in self.pins])
  self.assertEqual(len(self.pins),8)
  expected={(v[0],v[1],'in','pull_up') for v in self.profile['buttons'].values()}
  self.assertEqual({(p.chip,p.line,p.direction,p.bias) for p in self.pins},expected)
  hardware=LuckfoxHardware.__new__(LuckfoxHardware);hardware.buttons=buttons
  events=[];rt=Runtime.__new__(Runtime)
  rt.lifecycle_check=None;rt.read_buttons=hardware.read_buttons;rt.waiting_release=False;rt.current=None;rt.low_since={}
  rt.host=types.SimpleNamespace(send=lambda *args,**kwargs:events.append((args,kwargs)));rt.activity_sink=None;rt.last_activity=-float('inf');rt.input_hold=None
  with patch.object(runtime_module.time,'monotonic',side_effect=lambda:self.clock[0]):
   # A 5 ms electrical bounce must not become a native key event.
   for bounce in (.005,.010):
    pin=buttons._gpio_pins['KEY_UP'];pin.state=False;rt.poll_input();self.clock[0]+=bounce;pin.state=True;rt.poll_input();self.assertEqual(events,[])
   for name in buttons.BUTTON_NAMES:
    events.clear();self.assertEqual(hardware.read_buttons(),set());pin=buttons._gpio_pins[name];pin.state=False
    self.clock[0]+=.010;rt.poll_input();self.assertEqual(events,[])
    self.clock[0]+=.030;rt.poll_input();pin.state=True;self.clock[0]+=.002;rt.poll_input()
    # Release chatter stays within the switch's 10 ms bounce specification.
    pin.state=False;self.clock[0]+=.003;rt.poll_input();pin.state=True;self.clock[0]+=.003;rt.poll_input()
    self.assertEqual(events,[(('key',),{'key':KEYS[name],'pressed':True}),(('key',),{'key':KEYS[name],'pressed':False})],name)

if __name__=='__main__':unittest.main()

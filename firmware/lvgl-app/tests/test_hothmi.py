import hashlib,json,sys,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace,ModuleType
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'python'))
import hothmi
from luckfox import LuckfoxHardware

class HothmiTests(unittest.TestCase):
 def test_direct_hardware_diagnostics_use_installed_panel_profile(self):
  module=ModuleType('seedsigner.hardware.buttons')
  module.HardwareButtons=SimpleNamespace(get_instance=lambda:SimpleNamespace())
  with patch.dict(sys.modules,{module.__name__:module}),patch.object(hothmi,'image_profile',return_value=hothmi.PROFILE),patch.object(LuckfoxHardware,'configure_display') as configure:
   hw=LuckfoxHardware()
  self.assertEqual(hw.panel_profile,hothmi.PROFILE)
  configure.assert_called_once_with(320,240,False)
 def test_manufacturer_command_bytes_and_waits(self):
  fixture=json.loads((ROOT/'reference/research/firmware/hothmi-init.json').read_text())
  self.assertEqual(hashlib.sha256((ROOT/fixture['source']).read_bytes()).hexdigest(),fixture['sha256'])
  clock=[0.0];trace=[]
  def command(value):trace.append({'command':value,'data':[],'time':clock[0]})
  def reset():clock[0]+=.170
  display=SimpleNamespace(width=320,height=240,_display_initialized=False,reset=reset,command=command,data=lambda v:trace[-1]['data'].append(v))
  with patch.object(hothmi.time,'sleep',side_effect=lambda t:clock.__setitem__(0,clock[0]+t)):
   hothmi.install(display);display.init()
  self.assertEqual([{k:r[k] for k in ('command','data')} for r in trace],
                   [{k:r[k] for k in ('command','data')} for r in fixture['commands']])
  for i,row in enumerate(fixture['commands']):
   end=trace[i+1]['time'] if i+1<len(trace) else clock[0]
   self.assertGreaterEqual(round((end-trace[i]['time'])*1000,5),row['minimumDelayMs'])
  self.assertEqual(trace[0]['command'],0x11)
  self.assertEqual(next(r['data'] for r in trace if r['command']==0x36),[0xA0])
  self.assertEqual(next(r['data'] for r in trace if r['command']==0x3A),[0x55])

 def test_profile_installs_before_first_lazy_initialization(self):
  calls=[]
  class Driver:
   def __init__(self,w,h):self.width=w;self.height=h;self._display_initialized=False
   def init(self):raise AssertionError('Generic panel init must not run')
   def _ensure_initialized(self):self.init();self._display_initialized=True
   def reset(self):calls.append('reset')
   def command(self,v):calls.append(v)
   def data(self,v):pass
   def set_color_inversion(self,v):calls.append(('inversion',v))
   def close(self):pass
  module=ModuleType('seedsigner.hardware.displays.ST7789');module.ST7789=Driver
  hw=LuckfoxHardware.__new__(LuckfoxHardware);hw.panel_profile=hothmi.PROFILE
  hw.lock=threading.Lock();hw.lcd=None;hw.scaler=None;hw.buttons=None
  with patch.dict(sys.modules,{module.__name__:module}),patch.object(hothmi.time,'sleep'):
   hw.configure_display(320,240,False)
  self.assertEqual(calls[:2],['reset',0x11]);self.assertTrue(hw.lcd._display_initialized)
  with self.assertRaises(ValueError):hw.configure_display(240,240,False)

 def test_wrong_geometry_and_late_install_are_rejected(self):
  for width,initialized in ((240,False),(320,True)):
   with self.assertRaises(ValueError):hothmi.install(SimpleNamespace(width=width,height=240,_display_initialized=initialized))

 def test_image_profile_is_explicit_and_validated(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'profile.json';self.assertIsNone(hothmi.image_profile(p))
   p.write_text(json.dumps({'profile':hothmi.PROFILE}));self.assertEqual(hothmi.image_profile(p),hothmi.PROFILE)
   p.write_text('{"profile":"other"}')
   with self.assertRaises(ValueError):hothmi.image_profile(p)

"""Original Controller/display-setting View, real native host, fake LCD only."""
import json,sys,tempfile,time,threading,importlib
from pathlib import Path
from contextlib import ExitStack
from types import SimpleNamespace
sys.path.insert(0,'/opt/src')
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C,SettingsDefinition
from seedsigner.gui.renderer import Renderer
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as renderer
from microsd_lifecycle import install as microsd
from startup_policy import install as startup
from app import stop_workers
from seedsigner.views.view import Destination,View
recovery='--home-recovery' in sys.argv
small='--st7735' in sys.argv or recovery;physical_states=[];drivers=[];buffers=[]
seen=[];states=[];previous=[None];calls=[];controller=None
class Hardware:
 def __init__(self):self.buttons=SimpleNamespace(override_ind=False);self.lcd=self.make(240,240);self.extents=[-1,-1]
 def make(self,width,height):return SimpleNamespace(width=width,height=height,set_color_inversion=lambda value:None)
 def configure_display(self,width,height,inverted):
  assert previous[0].poll() is not None
  self.lcd=self.make(width,height);self.extents=[-1,-1];calls.append([width,height])
 def pixels(self,area,data):
  x1,y1,x2,y2=area;assert x2<self.lcd.width and y2<self.lcd.height
  self.extents[0]=max(self.extents[0],x2);self.extents[1]=max(self.extents[1],y2)
from luckfox import LuckfoxHardware
from diagnostic_scope import attribute
class Driver:
 def __init__(self,width,height):self.width=width;self.height=height;self.closed=False;self.shown=0;self._dc=SimpleNamespace(write=lambda value:None);drivers.append(self)
 def _ensure_initialized(self):pass
 def set_color_inversion(self,value):pass
 def close(self):self.closed=True
 def command(self,value):pass
 def data(self,value):pass
 def _chunked_transfer(self,data):pass
 def show_image(self,image,x,y):assert image.size==(128,128);self.shown+=1
class SmallHardware(LuckfoxHardware):
 def __init__(self):
  self.lock=threading.Lock();self.lcd=None;self.scaler=None;self.buttons=SimpleNamespace(override_ind=False,_gpio_pins={});self.extents=[-1,-1]
  self.configure_display(240,240,False)
 def configure_display(self,width,height,inverted):
  if self.lcd is not None:
   assert previous[0].poll() is not None
   calls.append([width,height])
   if self.scaler is not None:
    assert not any(self.scaler.buffer);buffers.append(self.scaler.buffer)
  super().configure_display(width,height,inverted);self.extents=[-1,-1]
 def pixels(self,area,data):
  super().pixels(area,data)
  self.extents[0]=max(self.extents[0],area[2]);self.extents[1]=max(self.extents[1],area[3])
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None
 def __call__(self):
  if self.start is None:self.start=time.monotonic()
  elapsed=time.monotonic()-self.start-.3
  if elapsed<0:return set()
  if recovery:
   if self.keys==['DONE']:
    if elapsed>.5:raise StopFlowBasedTest()
    return set()
   if elapsed>8:raise FlowBasedTestException('Home recovery hold stalled')
   return set(self.keys)
  index=int(elapsed/.4)
  if index>=len(self.keys):
   if elapsed>len(self.keys)*.4+5:raise FlowBasedTestException('Geometry UI input stalled')
   return set()
  return {self.keys[index]} if elapsed%.4<.22 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-display-setting-') as temporary,ExitStack() as scope:
 if small:
  for module,name in [('seedsigner.hardware.displays.ST7789','ST7789'),('seedsigner.hardware.displays.ST7735','ST7735')]:
   scope.enter_context(attribute(importlib.import_module(module),name,Driver))
  hardware=SmallHardware();scope.callback(hardware.close)
 else:hardware=Hardware()
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 settings.set_value(C.SETTING__DISPLAY_CONFIGURATION,'st7789_240x240',save=False)
 buttons=Buttons();runtime=Runtime(sys.argv[1],hardware.pixels,buttons);scope.callback(runtime.close)
 guards=Path(__file__).parent/'source-guards.json'
 scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.hardware.microsd import MicroSD
 from seedsigner.hardware.buttons import HardwareButtons
 scope.callback(microsd(MicroSD,'/opt/src',guards))
 from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
 from seedsigner.views.settings_views import SettingsMenuView
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 original_initialize=View._initialize;original_run=runtime.run
 def run(screen,args):
  name=screen.__name__;seen.append(name)
  if recovery:
   if name!='MainMenuScreen':raise FlowBasedTestException('Unexpected recovery screen '+name)
   width=Renderer.get_instance().canvas_width
   states.append(width);physical_states.append([hardware.lcd.width,hardware.lcd.height])
   assert width==runtime.width
   buttons.load([['KEY_RIGHT'],['KEY_DOWN'],['KEY_UP'],['DONE']][len(states)-1])
   previous[0]=runtime.host.child
   started=time.monotonic();value=original_run(screen,args)
   assert value==1002 and time.monotonic()-started>=5
   return value
  if name=='ButtonListScreen':
   if not states:
    entry=SettingsDefinition.get_settings_entry(C.SETTING__DISPLAY_CONFIGURATION)
    index=next(i for i,option in enumerate(args['button_data']) if option.button_label==entry.display_name)
    delta=index-(args.get('selected_button',0) or 0)
    buttons.load((['KEY_DOWN']*delta if delta>=0 else ['KEY_UP']*(-delta))+['KEY_PRESS'])
    return original_run(screen,args)
   assert states==([240,240,240] if small else [240,320,240]) and calls==([[128,128],[240,240]] if small else [[320,240],[240,240]])
   raise StopFlowBasedTest()
  if name!='SettingsEntryUpdateSelectionScreen':raise FlowBasedTestException('Unexpected geometry screen '+name)
  width=Renderer.get_instance().canvas_width
  assert width==runtime.width
  assert Renderer.get_instance()._display_size==(hardware.lcd.width,hardware.lcd.height)
  physical_states.append([hardware.lcd.width,hardware.lcd.height])
  states.append(width);entry=SettingsDefinition.get_settings_entry(C.SETTING__DISPLAY_CONFIGURATION)
  current=args['selected_button']
  if len(states)==3:keys=['KEY_UP']*(current+2)+['KEY_PRESS']
  else:
   target=('st7735_128x128' if small else 'st7789_320x240') if len(states)==1 else 'st7789_240x240'
   index=next(i for i,option in enumerate(entry.selection_options) if (option[0] if isinstance(option,tuple) else option)==target)
   delta=index-current;keys=(['KEY_DOWN']*delta if delta>=0 else ['KEY_UP']*(-delta))+['KEY_PRESS']
  previous[0]=runtime.host.child;buttons.load(keys)
  return original_run(screen,args)
 runtime.run=run
 try:
  if recovery:
   from seedsigner.views.view import MainMenuView
   destination=Destination(MainMenuView)
  else:destination=Destination(SettingsMenuView,view_args=dict(visibility=C.VISIBILITY__HARDWARE))
  controller.start(initial_destination=destination,skip_startup_interstitials=True)
  assert View._initialize is original_initialize and settings.get_value(C.SETTING__DISPLAY_CONFIGURATION)=='st7789_240x240'
  assert hardware.extents==[239,239] and not Path(Settings.SETTINGS_FILENAME).exists()
  if small:
   assert physical_states==([[240,240],[320,240],[128,128],[240,240]] if recovery else [[240,240],[128,128],[240,240]])
   assert hardware.scaler is None and buffers and all(not any(buffer) for buffer in buffers)
   assert sum(driver.shown for driver in drivers)>0
 finally:
  stop_workers(controller);settings.flush_save()
  for pin in HardwareButtons.get_instance()._gpio_pins.values():pin.close()
 print(json.dumps(dict(passed=True,originalController=True,originalSelectionView=not recovery,homeDirectionalRecovery=recovery,originalViewInitialization=True,canvasWidths=states,physicalTargets=physical_states,realScalerAndHardwareAdapter=small,oldScalerBuffersZeroed=small,hardwareCallbacks=calls,returnedToSettings=not recovery,physicalDisplay=False,lcdFixture=True,physicalButtons=False,originalSettingsFileNotUsed=True)),flush=True)

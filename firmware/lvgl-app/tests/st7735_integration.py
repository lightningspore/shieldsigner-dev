"""Real native/scaler/hardware adapter, original Renderer model; fake drivers."""
import importlib,json,sys,tempfile,threading
from pathlib import Path
from types import SimpleNamespace
from contextlib import ExitStack
sys.path.insert(0,'/opt/src')
from diagnostic_scope import attribute
from guards import verify
from luckfox import LuckfoxHardware
from runtime import Runtime
from renderer_bridge import install
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
verify('/opt/src',Path(__file__).parent/'source-guards.json')
class Driver:
 def __init__(self,width,height):self.width=width;self.height=height;self.closed=False;self.shown=0;self._dc=SimpleNamespace(write=lambda value:None)
 def _ensure_initialized(self):pass
 def set_color_inversion(self,value):pass
 def close(self):self.closed=True
 def command(self,value):pass
 def data(self,value):pass
 def _chunked_transfer(self,data):pass
 def show_image(self,image,x,y):
  assert image.size==(128,128) and (x,y)==(0,0)
  self.shown+=1
with tempfile.TemporaryDirectory(prefix='lvgl-st7735-') as temporary,ExitStack() as scope:
 for module,name in [('seedsigner.hardware.displays.ST7789','ST7789'),('seedsigner.hardware.displays.ST7735','ST7735')]:
  scope.enter_context(attribute(importlib.import_module(module),name,Driver))
 hardware=LuckfoxHardware.__new__(LuckfoxHardware);hardware.lock=threading.Lock();hardware.lcd=None;hardware.scaler=None;hardware.buttons=SimpleNamespace(override_ind=False,_gpio_pins={})
 hardware.configure_display(240,240,False);old_display=hardware.lcd
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__DISPLAY_CONFIGURATION,'st7735_128x128',save=False)
 runtime=Runtime(sys.argv[1],hardware.pixels,lambda:set());restore=install(runtime,hardware,Renderer)
 try:
  old_child=runtime.host.child
  Renderer.configure_instance();renderer=Renderer.get_instance()
  assert old_child.poll() is not None and old_display.closed
  assert (renderer.canvas_width,renderer.canvas_height)==(240,240)
  assert renderer._needs_resize and renderer._display_size==(128,128) and renderer.display_type=='st7735'
  assert (runtime.width,runtime.height)==(240,240) and hardware.scaler is not None
  runtime.host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
  assert runtime.host.next_event()==dict(event='screen_ready',request=1)
  assert hardware.lcd.shown>0
  old_buffer=hardware.scaler.buffer;old_small=hardware.lcd
  settings.set_value(C.SETTING__DISPLAY_CONFIGURATION,'st7789_240x240',save=False);renderer.initialize_display()
  assert hardware.scaler is None and old_small.closed and not any(old_buffer)
  assert not renderer._needs_resize and renderer._display_size==(240,240)
  settings.set_value(C.SETTING__DISPLAY_CONFIGURATION,'st7735_128x128',save=False);renderer.initialize_display()
  runtime.host.send('screen',name='main_menu_screen',request=2,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
  assert runtime.host.next_event()==dict(event='screen_ready',request=2)
  buffer=hardware.scaler.buffer;assert any(buffer)
  shown=hardware.lcd.shown;runtime.close()
  assert not any(buffer) and not hardware.scaler.dirty
  assert hardware.scaler.buffer is buffer and not Path(Settings.SETTINGS_FILENAME).exists()
  print(json.dumps(dict(passed=True,originalSettingsModel=True,logicalCanvas=[240,240],physicalTarget=[128,128],downsizedFrames=shown,oldHostAndDisplayClosed=True,automaticBufferWipeAfterHostClose=True,returnToST7789DropsZeroedBuffer=True,realNativeScalerAndHardwareAdapter=True,fakeDrivers=True,physicalDisplay=False)),flush=True)
 finally:runtime.close();restore();hardware.close()

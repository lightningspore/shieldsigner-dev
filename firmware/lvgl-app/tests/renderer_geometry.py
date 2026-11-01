"""Original Renderer bridge geometry changes with real native host, fake LCD."""
import json,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,'/opt/src')
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from renderer_bridge import install
from runtime import Runtime
from guards import verify
verify('/opt/src',Path(__file__).parent/'source-guards.json')
class Hardware:
 def __init__(self):
  self.buttons=SimpleNamespace(override_ind=False);self.calls=[];self.extents=[-1,-1]
  self.lcd=self.make(240,240)
 def make(self,width,height):return SimpleNamespace(width=width,height=height,set_color_inversion=lambda value:self.calls.append(('invert',value)))
 def configure_display(self,width,height,inverted):
  assert previous[0].poll() is not None
  self.calls.append(('configure',width,height,inverted));self.lcd=self.make(width,height);self.extents=[-1,-1]
 def pixels(self,area,data):
  x1,y1,x2,y2=area
  assert x2<self.lcd.width and y2<self.lcd.height
  self.extents[0]=max(self.extents[0],x2);self.extents[1]=max(self.extents[1],y2)
hardware=Hardware();previous=[None];checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-renderer-geometry-') as temporary:
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__DISPLAY_CONFIGURATION,'st7789_240x240',save=False)
 settings.set_value(C.SETTING__DISPLAY_COLOR_INVERTED,C.OPTION__DISABLED,save=False)
 runtime=Runtime(sys.argv[1],hardware.pixels,lambda:set());restore=install(runtime,hardware,Renderer)
 try:
  Renderer.configure_instance();renderer=Renderer.get_instance()
  for width,height in ((320,240),(240,240)):
   previous[0]=runtime.host.child
   settings.set_value(C.SETTING__DISPLAY_CONFIGURATION,f'st7789_{width}x{height}',save=False)
   renderer.initialize_display()
   assert (renderer.canvas_width,renderer.canvas_height)==(width,height)
   assert renderer.disp is hardware.lcd and renderer.canvas is None
   runtime.host.send('screen',name='main_menu_screen',request=1,config=dict(top_nav=dict(title='Home',show_power_button=True),button_list=['Scan','Seeds','Tools','Settings']))
   assert runtime.host.next_event()==dict(event='screen_ready',request=1)
   assert hardware.extents==[width-1,height-1]
   checks.append(dict(width=width,height=height,nativeAndRendererAgree=True,previousProcessReaped=True))
  assert not Path(Settings.SETTINGS_FILENAME).exists()
  print(json.dumps(dict(passed=True,cases=checks,hardwareCallbacks=hardware.calls,physicalDisplay=False,originalSettingsModel=True,settingsUIQualified=False)),flush=True)
 finally:restore();runtime.close()

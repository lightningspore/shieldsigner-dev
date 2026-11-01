"""Public original LocaleSelectionView navigation through the native picker."""
import sys,json,tempfile,time,os
from pathlib import Path
from contextlib import ExitStack
sys.path.insert(0,'/opt/src')
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as renderer
from microsd_lifecycle import install as microsd
from startup_policy import install as startup
from app import stop_workers
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import Destination,View
from luckfox import LuckfoxHardware
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None
 def __call__(self):
  if self.start is None:self.start=time.monotonic()
  elapsed=time.monotonic()-self.start-.3
  if elapsed<0:return set()
  index=int(elapsed/.4)
  if index>=len(self.keys):
   if elapsed>len(self.keys)*.4+8:raise RuntimeError('Locale input stalled')
   return set()
  return {self.keys[index]} if elapsed%.4<.22 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-language-') as temporary,ExitStack() as scope:
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 settings.set_value(C.SETTING__LOCALE,'en',save=False)
 hardware=LuckfoxHardware();scope.callback(hardware.close)
 buttons=Buttons();runtime=Runtime(sys.argv[1],hardware.pixels,buttons,locale_root='/userdata/shieldsigner-lvgl-locales');scope.callback(runtime.close)
 guards=Path(__file__).parent/'source-guards.json'
 scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.hardware.microsd import MicroSD
 from seedsigner.hardware.buttons import HardwareButtons
 scope.callback(microsd(MicroSD,'/opt/src',guards))
 from seedsigner.controller import Controller,StopFlowBasedTest
 from seedsigner.views.settings_views import LocaleSelectionView,SettingsMenuView
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 targets=['ja','fa','en'];observed=[];original_run=runtime.run;initialize=View._initialize
 def run(screen,args):
  if screen.__name__=='SettingsEntryUpdateSelectionScreen':
   target=targets[len(observed)]
   index=next(i for i,option in enumerate(args['button_data']) if option.return_data==target)
   delta=index-args['selected_button'];buttons.load((['KEY_DOWN']*delta if delta>=0 else ['KEY_UP']*(-delta))+['KEY_PRESS'])
   value=original_run(screen,args);assert value==index
   return value
  if screen.__name__=='ButtonListScreen':
   value=settings.get_value(C.SETTING__LOCALE);assert value==targets[len(observed)];observed.append(value)
   # Render original translated settings, then re-enter the original language View.
   buttons.load(['KEY_PRESS']);original_run(screen,args)
   if len(observed)==len(targets):raise StopFlowBasedTest()
   index=next(i for i,item in enumerate(args['button_data']) if getattr(item,'button_label',None)=='Language')
   return index
  raise RuntimeError('Unexpected locale screen '+screen.__name__)
 runtime.run=run
 try:
  controller.start(initial_destination=Destination(LocaleSelectionView),skip_startup_interstitials=True)
  assert observed==targets and View._initialize is initialize
  assert not Path(Settings.SETTINGS_FILENAME).exists()
 finally:
  stop_workers(controller);settings.flush_save()
  for pin in HardwareButtons.get_instance()._gpio_pins.values():pin.close()
 print(json.dumps(dict(passed=True,originalController=True,originalLocaleSelectionView=True,locales=observed,physicalDisplay=True,scriptedButtons=True,originalSettingsUntouched=True,translatedScreenVisualParity=False)),flush=True)

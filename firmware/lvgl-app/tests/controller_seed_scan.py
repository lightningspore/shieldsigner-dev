"""Original Home/Scan/pending/finalize/seed-options flow, public compact SeedQR."""
import json,sys,tempfile,time
from pathlib import Path
from contextlib import ExitStack
sys.path[:0]=[str(Path(__file__).parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View,Destination,MainMenuView
from embit import bip39
from synthetic_frames import Source
from runtime import Runtime,install_view_dispatch
from luckfox import LuckfoxHardware
from renderer_bridge import install as renderer
from toast_bridge import install as toasts
from microsd_lifecycle import install as microsd
from startup_policy import install as startup
from diagnostic_scope import attribute
from app import stop_workers
entropy=bytes(range(32 if '--24' in sys.argv else 16));expected=bip39.mnemonic_from_bytes(entropy).split()
seen=[];homes=0;original_initialize=View._initialize;controller=None
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None
 def __call__(self):
  if self.start is None:self.start=time.monotonic()
  elapsed=time.monotonic()-self.start-.3
  if self.keys is None:
   if elapsed>20:raise TimeoutError('Seed scan stalled')
   return set()
  if elapsed<0:return set()
  index=int(elapsed/.4)
  if index>=len(self.keys):
   if elapsed>len(self.keys)*.4+6:raise TimeoutError('Seed input stalled at '+seen[-1])
   return set()
  return {self.keys[index]} if elapsed%.4<.22 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-seed-scan-') as temporary,ExitStack() as scope:
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 hardware=LuckfoxHardware();scope.callback(hardware.close);buttons=Buttons()
 runtime=Runtime(sys.argv[1],hardware.pixels,buttons,hardware.buttons.update_last_input_time);scope.callback(runtime.close)
 guards=Path(__file__).parent/'source-guards.json'
 scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
 import seedsigner.gui.toast as toast
 from seedsigner.hardware.microsd import MicroSD
 scope.callback(toasts(runtime,toast));scope.callback(microsd(MicroSD,'/opt/src',guards))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
 import shieldsigner_native_stream
 source=Source([entropy]);scope.enter_context(attribute(shieldsigner_native_stream,'NativeVideoStream',lambda **kwargs:source))
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 assert controller.storage.num_seeds()==0 and controller.storage.get_pending_seed() is None
 original_run=runtime.run
 def run(screen,args):
  global homes
  name=screen.__name__;seen.append(name);print(json.dumps(dict(event='diagnostic-stage',screen=name)),flush=True)
  if name=='MainMenuScreen':
   homes+=1
   if homes==2:raise StopFlowBasedTest()
   buttons.load(['KEY_PRESS'])
  elif name=='ScanScreen':buttons.load(None)
  elif name=='SeedFinalizeScreen':
   seed=controller.storage.get_pending_seed()
   assert seed.mnemonic_list==expected and controller.storage.num_seeds()==0
   assert args['fingerprint']==seed.get_fingerprint(settings.get_value(C.SETTING__NETWORK))
   buttons.load(['KEY_PRESS'])
  elif name=='SeedOptionsScreen':
   assert controller.storage.get_pending_seed() is None and controller.storage.num_seeds()==1
   buttons.load(['KEY_UP']*15+['KEY_PRESS'])
  else:raise FlowBasedTestException('Unexpected seed screen '+name)
  return original_run(screen,args)
 runtime.run=run
 try:
  controller.start(initial_destination=Destination(MainMenuView),skip_startup_interstitials=True)
  assert seen==['MainMenuScreen','ScanScreen','SeedFinalizeScreen','SeedOptionsScreen','MainMenuScreen'],seen
  seed=controller.storage.seeds[0]
  assert seed.mnemonic_list==expected and bytes(seed.seed_bytes)==bip39.mnemonic_to_seed(' '.join(expected))
  assert source.is_stopped and source.index>0 and View._initialize is original_initialize
  assert not Path(Settings.SETTINGS_FILENAME).exists()
 except BaseException:
  print(json.dumps(dict(passed=False,screenSequence=seen)),flush=True);raise
 finally:
  stop_workers(controller)
  for public_seed in controller.storage.seeds:public_seed.wipe()
  controller.storage.clear_pending_seed()
 print(json.dumps(dict(passed=True,wordCount=len(expected),originalController=True,originalViewInitialization=True,initialStorageEmpty=True,pendingThenFinalized=True,originalBIP39SeedBytesExact=True,homeReturnRetainedSeed=True,sourceStopped=True,workersStopped=True,screenSequence=seen,physicalDisplay=True,physicalButtons=False,syntheticCompactSeedQR=True,opticalQualified=False)),flush=True)

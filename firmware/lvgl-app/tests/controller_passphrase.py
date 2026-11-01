"""Full Controller seed import, passphrase scan/edit/review and finalization."""
import hashlib,json,sys,tempfile,time,unicodedata
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
entropy=bytes(range(16));expected=bip39.mnemonic_from_bytes(entropy).split()
passphrase=' public\0 literal\\0 café e\u0301 '
expected_bytes=hashlib.pbkdf2_hmac('sha512',unicodedata.normalize('NFKD',' '.join(expected)).encode(),b'mnemonic'+unicodedata.normalize('NFKD',passphrase).encode(),2048)
seen=[];homes=0;reviews=0;original_initialize=View._initialize;controller=None
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
 sources=[Source([entropy]),Source([passphrase.encode()])]
 source_queue=iter(sources)
 scope.enter_context(attribute(shieldsigner_native_stream,'NativeVideoStream',lambda **kwargs:next(source_queue)))
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 assert controller.storage.num_seeds()==0 and controller.storage.get_pending_seed() is None
 original_run=runtime.run
 def run(screen,args):
  global homes,reviews
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
   assert [item.button_label for item in args['button_data']][:3]==['Done','Type Passphrase','Scan Passphrase']
   buttons.load(['KEY_DOWN','KEY_DOWN','KEY_PRESS'])
  elif name=='SeedReviewPassphraseScreen':
   reviews+=1
   seed=controller.storage.get_pending_seed()
   assert seed.passphrase==unicodedata.normalize('NFKD',passphrase)
   assert bytes(seed.seed_bytes)==expected_bytes
   assert args['passphrase']==seed.passphrase_display
   assert args['fingerprint_with']==seed.get_fingerprint(settings.get_value(C.SETTING__NETWORK))
   assert args['fingerprint_without']!=args['fingerprint_with']
   buttons.load(['KEY_DOWN','KEY_PRESS'] if reviews==1 else ['KEY_PRESS'])
  elif name=='SeedAddPassphraseScreen':
   assert args['passphrase']==unicodedata.normalize('NFC',passphrase)
   buttons.load(['KEY3'])
  elif name=='SeedOptionsScreen':
   assert controller.storage.get_pending_seed() is None and controller.storage.num_seeds()==1
   buttons.load(['KEY_UP']*15+['KEY_PRESS'])
  else:raise FlowBasedTestException('Unexpected seed screen '+name)
  return original_run(screen,args)
 runtime.run=run
 try:
  controller.start(initial_destination=Destination(MainMenuView),skip_startup_interstitials=True)
  assert seen==['MainMenuScreen','ScanScreen','SeedFinalizeScreen','ScanScreen','SeedReviewPassphraseScreen','SeedAddPassphraseScreen','SeedReviewPassphraseScreen','SeedOptionsScreen','MainMenuScreen'],seen
  seed=controller.storage.seeds[0]
  assert seed.mnemonic_list==expected and bytes(seed.seed_bytes)==expected_bytes and seed.passphrase==unicodedata.normalize('NFKD',passphrase)
  assert all(source.is_stopped and source.index>0 for source in sources) and View._initialize is original_initialize
  assert not Path(Settings.SETTINGS_FILENAME).exists()
 except BaseException:
  print(json.dumps(dict(passed=False,screenSequence=seen)),flush=True);raise
 finally:
  stop_workers(controller)
  for public_seed in controller.storage.seeds:public_seed.wipe()
  controller.storage.clear_pending_seed()
 print(json.dumps(dict(passed=True,wordCount=len(expected),originalController=True,originalViewInitialization=True,initialStorageEmpty=True,pendingThenFinalized=True,originalBIP39SeedBytesExact=True,homeReturnRetainedSeed=True,sourcesStopped=True,passphraseScanEditReview=True,nulAndLiteralEscapeExact=True,independentPBKDF2=True,workersStopped=True,screenSequence=seen,physicalDisplay=True,physicalButtons=False,syntheticCompactSeedQR=True,opticalQualified=False)),flush=True)

"""Original Controller BIP85 review/quiz/finalization; public mnemonic only."""
import hashlib,hmac,json,sys,tempfile,time
from pathlib import Path
from contextlib import ExitStack
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
restore_policy=install('/opt/src',Path(__file__).parent/'source-guards.json')
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as renderer
from microsd_lifecycle import install as microsd
from startup_policy import install as startup
from app import stop_workers
from luckfox import LuckfoxHardware
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.models.seed import Seed
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View,Destination
from embit import bip39
count=int(sys.argv[2]) if len(sys.argv)>2 else 18
assert count in (12,18,24)
seen=[];words_seen=[];quiz_indices=[];prompts=0;finished=False
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None
 def __call__(self):
  if self.start is None:self.start=time.monotonic()
  elapsed=time.monotonic()-self.start-.25
  if elapsed<0:return set()
  index=int(elapsed/.3)
  if index>=len(self.keys):
   if elapsed>len(self.keys)*.3+8:raise TimeoutError('BIP85 input stalled at '+seen[-1])
   return set()
  return {self.keys[index]} if elapsed%.3<.17 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-bip85-') as temporary,ExitStack() as scope:
 scope.callback(restore_policy)
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 parent=Seed(['abandon']*11+['about']);scope.callback(parent.wipe)
 # Independent expansion of the BIP85 HMAC/entropy step; no replacement of app code.
 private=parent.get_root(C.MAINNET).derive(f'm/83696968h/39h/0h/{count}h/0h').key.secret
 entropy=hmac.new(b'bip-entropy-from-k',private,hashlib.sha512).digest()[:count*4//3]
 expected=bip39.mnemonic_from_bytes(entropy).split()
 assert parent.get_bip85_child_mnemonic(0,count).split()==expected
 hardware=LuckfoxHardware();scope.callback(hardware.close);buttons=Buttons()
 runtime=Runtime(sys.argv[1],hardware.pixels,buttons,hardware.buttons.update_last_input_time);scope.callback(runtime.close)
 guards=Path(__file__).parent/'source-guards.json'
 scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.hardware.microsd import MicroSD
 from seedsigner.hardware.buttons import HardwareButtons
 scope.callback(microsd(MicroSD,'/opt/src',guards))
 from seedsigner.controller import Controller,StopFlowBasedTest
 from seedsigner.views.seed_views import SeedOptionsView
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 assert controller.storage.num_seeds()==0
 controller.storage.seeds.append(parent);original_run=runtime.run;initialize=View._initialize
 def select(args,label):
  index=next(i for i,item in enumerate(args['button_data']) if item.button_label==label)
  current=args.get('selected_button',0) or 0;delta=index-current
  return (['KEY_DOWN']*delta if delta>=0 else ['KEY_UP']*(-delta))+['KEY_PRESS']
 def run(screen,args):
  global prompts,finished
  name=screen.__name__;seen.append(name)
  if name=='SeedOptionsScreen':
   if finished:
    assert controller.storage.num_seeds()==2 and controller.storage.get_pending_seed() is None
    child=controller.storage.seeds[1];assert child.mnemonic_list==expected
    assert bytes(child.seed_bytes)==hashlib.pbkdf2_hmac('sha512',' '.join(expected).encode(),b'mnemonic',2048)
    assert parent.mnemonic_list==['abandon']*11+['about']
    raise StopFlowBasedTest()
   keys=select(args,'BIP-85 child seed')
  elif name=='ButtonListScreen' and args.get('title')=='BIP-85 Num Words':keys=select(args,f'{count} Words')
  elif name=='SeedBIP85SelectChildIndexScreen':keys=['KEY_PRESS','KEY3']
  elif name=='SeedWordsBackupTestPromptScreen':
   keys=select(args,'Review' if prompts==0 else 'Verify');prompts+=1
  elif name=='DireWarningScreen':keys=['KEY_PRESS']
  elif name=='SeedWordsScreen':
   assert args['words']==expected[args['page_index']*4:(args['page_index']+1)*4]
   assert args['num_pages']==(count+3)//4
   words_seen.extend(args['words']);keys=['KEY_PRESS']
  elif name=='ButtonListScreen' and args.get('title','').startswith('Verify Word #'):
   index=int(args['title'].rsplit('#',1)[1])-1;assert index not in quiz_indices;quiz_indices.append(index)
   keys=select(args,expected[index])
  elif name=='LargeIconStatusScreen':
   assert args.get('title')=='Backup Verified';assert sorted(quiz_indices)==list(range(count));keys=['KEY_PRESS']
  elif name=='SeedFinalizeScreen':
   assert words_seen==expected and controller.storage.get_pending_seed().mnemonic_list==expected
   finished=True;keys=['KEY_PRESS']
  else:raise RuntimeError('Unexpected BIP85 screen '+name)
  buttons.load(keys);return original_run(screen,args)
 runtime.run=run
 try:
  controller.start(initial_destination=Destination(SeedOptionsView,view_args={'seed':parent}),skip_startup_interstitials=True)
  assert finished and View._initialize is initialize and not Path(Settings.SETTINGS_FILENAME).exists()
  print(json.dumps(dict(passed=True,wordCount=count,reviewedWords=len(words_seen),quizAnswers=len(quiz_indices),originalController=True,originalViews=True,originalCrypto=True,childIndex=0,independentHmacEntropyMatches=True,childStored=True,parentUnchanged=True,physicalDisplay=True,physicalButtons=False,screenSequence=seen)),flush=True)
 finally:
  stop_workers(controller)
  for seed in controller.storage.seeds:seed.wipe()
  controller.storage.seeds=[];controller.storage.clear_pending_seed()
  for pin in HardwareButtons.get_instance()._gpio_pins.values():pin.close()

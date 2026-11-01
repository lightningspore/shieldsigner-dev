"""Public SLIP39 QR recovery plus complete share review/quiz, original Controller."""
import json,sys,tempfile,time
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
from seedsigner.models.seed import Slip39Seed
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View,Destination
from diagnostic_scope import attribute
from synthetic_frames import LazySource
import shamir_mnemonic
count=int(sys.argv[2]) if len(sys.argv)>2 else 33
assert count in (20,33)
discard='--discard' in sys.argv;stored_refs=[]
secret=bytes(range(16 if count==20 else 32))
shares=shamir_mnemonic.generate_mnemonics(1,[(2,2)],secret,extendable=True)[0]
assert all(len(share.split())==count for share in shares)
assert shamir_mnemonic.combine_mnemonics(shares)==secret
seen=[];sources=[];review_share=-1;reviewed=[[],[]];quizzes=[[],[]];successes=0
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None
 def __call__(self):
  if self.start is None:self.start=time.monotonic()
  elapsed=time.monotonic()-self.start-.25
  if elapsed<0:return set()
  if self.keys is None:
   if elapsed>30:raise TimeoutError('SLIP39 scan stalled')
   return set()
  index=int(elapsed/.3)
  if index>=len(self.keys):
   if elapsed>len(self.keys)*.3+8:raise TimeoutError('SLIP39 input stalled at '+seen[-1])
   return set()
  return {self.keys[index]} if elapsed%.3<.17 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-slip39-') as temporary,ExitStack() as scope:
 scope.callback(restore_policy)
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 hardware=LuckfoxHardware();scope.callback(hardware.close);buttons=Buttons()
 runtime=Runtime(sys.argv[1],hardware.pixels,buttons,hardware.buttons.update_last_input_time);scope.callback(runtime.close)
 guards=Path(__file__).parent/'source-guards.json'
 scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.hardware.microsd import MicroSD
 from seedsigner.hardware.buttons import HardwareButtons
 scope.callback(microsd(MicroSD,'/opt/src',guards))
 from seedsigner.controller import Controller,StopFlowBasedTest
 from seedsigner.views.seed_views import SeedSlip39MnemonicStartView
 import shieldsigner_native_stream
 def source(**kwargs):
  assert len(sources)<2
  value=LazySource([shares[len(sources)].encode()]);sources.append(value);return value
 scope.enter_context(attribute(shieldsigner_native_stream,'NativeVideoStream',source))
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 assert controller.storage.num_seeds()==0 and controller.storage.get_pending_seed() is None
 original_run=runtime.run;initialize=View._initialize
 def select(args,label):
  index=next(i for i,item in enumerate(args['button_data']) if item.button_label==label)
  current=args.get('selected_button',0) or 0;delta=index-current
  return (['KEY_DOWN']*delta if delta>=0 else ['KEY_UP']*(-delta))+['KEY_PRESS']
 def run(screen,args):
  global review_share,successes
  name=screen.__name__;seen.append(name)
  print(json.dumps(dict(event='diagnostic-stage',screen=name)),flush=True)
  if name=='ButtonListScreen':
   title=args.get('title','')
   if title=='Load Share':keys=select(args,'Scan QR')
   elif title=='1 of 2 needed':
    assert controller.storage.slip39_shares_entered==1 and controller.storage.get_pending_seed() is None
    keys=select(args,'Scan share')
   elif title=='2 of 2 needed':
    assert controller.storage.slip39_shares_entered==2;keys=select(args,'Combine shares')
   elif title=='Backup Seed':keys=select(args,'View seed words')
   elif title=='Select Share':keys=select(args,'Share 1')
   elif title.startswith('Verify Word #'):
    index=int(title.rsplit('#',1)[1])-1;assert index not in quizzes[review_share]
    quizzes[review_share].append(index);keys=select(args,shares[review_share].split()[index])
   else:raise RuntimeError('Unexpected SLIP39 menu '+title)
  elif name=='ScanScreen':keys=None
  elif name=='SeedFinalizeScreen':
   seed=controller.storage.get_pending_seed()
   assert isinstance(seed,Slip39Seed) and bytes(seed.seed_bytes)==secret and bytes(seed.master_secret)==secret
   assert seed.mnemonic_list==shares and controller.storage.slip39_shares_entered==0
   stored_refs.append(seed);keys=['KEY_PRESS']
  elif name=='SeedOptionsScreen':
   assert controller.storage.num_seeds()==1 and controller.storage.get_pending_seed() is None
   assert bytes(controller.storage.seeds[0].seed_bytes)==secret
   if successes==2:
    if not discard:raise StopFlowBasedTest()
    keys=select(args,'Discard seed')
   else:keys=select(args,'Backup seed')
  elif name=='WarningScreen' and discard:
   assert args.get('title')=='Discard Seed?';keys=select(args,'Discard')
  elif name=='MainMenuScreen' and discard:
   assert controller.storage.num_seeds()==0 and stored_refs and stored_refs[0].seed_bytes is None
   assert stored_refs[0]._shares==[] and stored_refs[0].master_secret is None
   raise StopFlowBasedTest()
  elif name=='DireWarningScreen':keys=['KEY_PRESS']
  elif name=='SeedWordsScreen':
   if args['page_index']==0:review_share+=1
   assert 0<=review_share<2 and args['num_pages']==(count+3)//4
   assert args['words']==shares[review_share].split()[args['page_index']*4:(args['page_index']+1)*4]
   reviewed[review_share].extend(args['words']);keys=['KEY_PRESS']
  elif name=='SeedWordsBackupTestPromptScreen':
   assert reviewed[review_share]==shares[review_share].split();keys=select(args,'Verify')
  elif name=='LargeIconStatusScreen':
   assert args.get('title')=='Backup Verified' and sorted(quizzes[review_share])==list(range(count))
   successes+=1;keys=['KEY_PRESS']
  else:raise RuntimeError('Unexpected SLIP39 screen '+name)
  buttons.load(keys);return original_run(screen,args)
 runtime.run=run
 try:
  controller.start(initial_destination=Destination(SeedSlip39MnemonicStartView),skip_startup_interstitials=True)
  assert successes==2 and len(sources)==2 and all(item.is_stopped and item.index>0 for item in sources)
  assert View._initialize is initialize and not Path(Settings.SETTINGS_FILENAME).exists()
  result=dict(passed=True,shareWords=count,threshold=2,sharesScanned=2,reviewedWords=[len(row) for row in reviewed],quizAnswers=[len(row) for row in quizzes],originalController=True,originalViewsWithPaginationFix=True,originalSlip39Combine=True,recoveredSecretExact=True,storedSeed=True,discardedThroughOriginalUi=discard,nativeQrDecoder=True,syntheticNv12=True,opticalQualified=False,sourceOwnersStopped=True,physicalDisplay=True,physicalButtons=False,screenSequence=seen)
 finally:
  stop_workers(controller)
  for seed in stored_refs:
   seed.wipe();seed.wipe() # Both original wipe passes must complete.
   assert seed.seed_bytes is None and seed.master_secret is None and seed._shares==[]
   assert seed._initial_master_secret is None and seed._creation_passphrase=='' and seed._slip39_passphrase==''
   assert seed._mnemonic==[] and seed._passphrase==''
  controller.storage.seeds=[];controller.storage.clear_pending_seed();controller.storage.discard_pending_slip39_shares()
  for pin in HardwareButtons.get_instance()._gpio_pins.values():pin.close()

 print(json.dumps(dict(result,originalWipeCompletedTwice=True,cleanupCompleted=True)),flush=True)

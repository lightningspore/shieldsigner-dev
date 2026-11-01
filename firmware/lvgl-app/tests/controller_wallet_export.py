"""Full Controller public wallet export, pixel-decoded QR and address handshake."""
import json,sys,tempfile,time,threading
from pathlib import Path
from contextlib import ExitStack
sys.path[:0]=[str(Path(__file__).parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View,Destination,MainMenuView
from embit import bip39,bip32,script
from embit.networks import NETWORKS
from shieldsigner_lcd import QrWorker
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
change=False
root=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(expected)))
fingerprint=root.child(0).fingerprint.hex()
xpub=root.derive("m/84'/0'/0'").to_public().to_string(version=NETWORKS['main']['zpub'])
expected_qr=("["+fingerprint+"/84'/0'/0']"+xpub).encode()
frame=bytearray(240*240*2);frame_lock=threading.Lock();decoded=False
public_key=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(expected))).derive("m/84'/0'/0'/"+str(int(change))+'/7').key.get_public_key()
expected_address=script.p2wpkh(public_key).address()
seen=[];homes=0;original_initialize=View._initialize;controller=None
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None;self.capture=False
 def capture_qr(self):self.load(None);self.capture=True;self.last=0
 def __call__(self):
  global decoded
  if getattr(self,'capture',False):
   now=time.monotonic()
   if self.start is None:self.start=now
   if now-self.start>20:raise TimeoutError('Export QR did not decode')
   if decoded:return {'KEY_PRESS'}
   if now-self.last<.15:return set()
   self.last=now
   with frame_lock:luma=bytes(frame[0::2])
   value=reader.decode_luma(luma,240,240)
   if value is not None:
    assert value==expected_qr,'Displayed wallet export differs from independently derived bytes'
    decoded=True
   return set()
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
 for setting,value in [(C.SETTING__SIG_TYPES,[C.SINGLE_SIG]),(C.SETTING__SCRIPT_TYPES,[C.NATIVE_SEGWIT]),(C.SETTING__XPUB_QR_FORMAT,[C.XPUB_QR_FORMAT__STATIC]),(C.SETTING__ACCOUNT_PROMPT,C.OPTION__DISABLED),(C.SETTING__XPUB_DETAILS,C.OPTION__ENABLED),(C.SETTING__PRIVACY_WARNINGS,C.OPTION__ENABLED)]:settings.set_value(setting,value,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 hardware=LuckfoxHardware();scope.callback(hardware.close);buttons=Buttons()
 reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5);scope.callback(reader.close)
 def pixels(area,data):
  x1,y1,x2,y2=area;stride=(x2-x1+1)*2
  with frame_lock:
   for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
  hardware.pixels(area,data)
 runtime=Runtime(sys.argv[1],pixels,buttons,hardware.buttons.update_last_input_time);scope.callback(runtime.close)
 guards=Path(__file__).parent/'source-guards.json'
 scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
 import seedsigner.gui.toast as toast
 from seedsigner.hardware.microsd import MicroSD
 scope.callback(toasts(runtime,toast));scope.callback(microsd(MicroSD,'/opt/src',guards))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
 import shieldsigner_native_stream
 sources=[Source([entropy]),Source([expected_address.encode()])]
 source_queue=iter(sources)
 scope.enter_context(attribute(shieldsigner_native_stream,'NativeVideoStream',lambda **kwargs:next(source_queue)))
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
   buttons.load(['KEY_DOWN','KEY_PRESS'])
  elif name=='WarningScreen':
   assert args['status_headline']=='Privacy Leak!'
   buttons.load(['KEY_PRESS'])
  elif name=='SeedExportXpubDetailsScreen':
   assert args['fingerprint']==fingerprint and args['derivation_path']=="m/84'/0'/0'" and args['xpub']==xpub
   buttons.load(['KEY_PRESS'])
  elif name=='QRDisplayScreen':
   assert args['qr_encoder'].next_part().encode()==expected_qr
   buttons.capture_qr()
  elif name=='LargeIconStatusScreen':
   assert args['title'] in ('Verify Address','Wallet Export')
   if args['title']=='Wallet Export':
    assert controller.unverified_address['verified_index']==7
    assert controller.unverified_address['verified_index_is_change'] is False
   buttons.load(['KEY_PRESS'])
  elif name=='SeedAddressVerificationScreen':
   assert args['address']==expected_address
   buttons.load(None)
  else:raise FlowBasedTestException('Unexpected seed screen '+name)
  return original_run(screen,args)
 runtime.run=run
 try:
  controller.start(initial_destination=Destination(MainMenuView),skip_startup_interstitials=True)
  assert seen==['MainMenuScreen','ScanScreen','SeedFinalizeScreen','SeedOptionsScreen','WarningScreen','SeedExportXpubDetailsScreen','QRDisplayScreen','LargeIconStatusScreen','ScanScreen','SeedAddressVerificationScreen','LargeIconStatusScreen','MainMenuScreen'],seen
  assert decoded
  assert controller.multisig_wallet_descriptor is None
  seed=controller.storage.seeds[0]
  assert seed.mnemonic_list==expected and bytes(seed.seed_bytes)==bip39.mnemonic_to_seed(' '.join(expected))
  assert all(source.is_stopped and source.index>0 for source in sources) and View._initialize is original_initialize
  assert not Path(Settings.SETTINGS_FILENAME).exists()
 except BaseException:
  print(json.dumps(dict(passed=False,screenSequence=seen)),flush=True);raise
 finally:
  stop_workers(controller)
  for public_seed in controller.storage.seeds:public_seed.wipe()
  controller.storage.clear_pending_seed()
 print(json.dumps(dict(passed=True,wordCount=len(expected),originalController=True,originalViewInitialization=True,initialStorageEmpty=True,pendingThenFinalized=True,originalBIP39SeedBytesExact=True,homeReturnRetainedSeed=True,sourcesStopped=True,verifiedAddressIndex=7,verifiedChange=change,originalAddressWorker=True,walletQRBytesExact=True,pixelDecodedWithZXing=True,workersStopped=True,screenSequence=seen,physicalDisplay=True,physicalButtons=False,syntheticCompactSeedQR=True,opticalQualified=False)),flush=True)

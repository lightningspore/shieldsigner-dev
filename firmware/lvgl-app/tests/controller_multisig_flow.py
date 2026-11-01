"""Original Controller multisig review/sign/export; public regtest fixture only."""
import json,os,sys,tempfile,time,threading
from contextlib import ExitStack
from pathlib import Path
sys.path[:0]=[str(Path(__file__).parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from multisig_fixture import build
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View,Destination,MainMenuView
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as renderer
from toast_bridge import install as toasts
from microsd_lifecycle import install as microsd
from startup_policy import install as startup
from luckfox import LuckfoxHardware
from shieldsigner_lcd import QrWorker
from seedsigner.models.decode_qr import DecodeQR
from seedsigner.models.psbt_parser import PSBTParser
from embit.ec import Signature
from resources import process_snapshot,system_snapshot
from app import stop_workers
import_seed='--import-seed' in sys.argv;seed_source=None
mismatch='--mismatch' in sys.argv;mismatch_warning=[]
cancel='--cancel' in sys.argv;select_seed='--select-seed' in sys.argv;load_descriptor='--load-descriptor' in sys.argv;scan_psbt='--scan-psbt' in sys.argv;unrelated=None;descriptor_source=None;psbt_source=None;change_verified=[];input_exact=False;source_queue=[]
frame=bytearray(115200);lock=threading.Lock();seen=[];snapshots=[];exported=None;decoded=None;controller=None
seeds,roots,descriptor,psbt=build();before=psbt.serialize();original_initialize=View._initialize
class Buttons:
 def load(self,keys):self.keys=keys;self.start=None;self.capture=False
 def __call__(self):
  now=time.monotonic()
  if self.start is None:self.start=now
  elapsed=now-self.start
  if self.capture:
   if self.decoder.is_complete:return {'KEY_PRESS'}
   if elapsed>35:raise TimeoutError('Controller signed QR did not decode')
   if now-self.last<.15:return set()
   self.last=now
   with lock:luma=bytes(frame[0::2])
   data=reader.decode_luma(luma,240,240)
   if data is not None:self.decoder.add_data(data)
   return set()
  if self.keys is None:
   if elapsed>25:raise TimeoutError('Descriptor input stalled')
   return set()
  elapsed-=.3
  if elapsed<0:return set()
  index=int(elapsed/.4)
  if index>=len(self.keys):
   if elapsed>len(self.keys)*.4+8:raise TimeoutError('Controller multisig input stalled at '+seen[-1])
   return set()
  return {self.keys[index]} if elapsed%.4<.22 else set()
buttons=Buttons()
with tempfile.TemporaryDirectory(prefix='lvgl-controller-multisig-') as temporary,ExitStack() as scope:
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 settings.set_value(C.SETTING__NETWORK,C.REGTEST,save=False)
 hardware=LuckfoxHardware();scope.callback(hardware.close)
 reader=None
 if not cancel and not mismatch:
  reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5);scope.callback(reader.close)
 def pixels(area,data):
  x1,y1,x2,y2=area;stride=(x2-x1+1)*2
  with lock:
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
 from seedsigner.views.psbt_views import PSBTOverviewView,PSBTFinalizeView,PSBTSelectSeedView
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 controller.psbt=None if scan_psbt else psbt;controller.psbt_seed=seeds[0];controller.psbt_parser=PSBTParser(psbt,seeds[0],network=C.REGTEST,multisig_descriptor=descriptor) if cancel else None;controller.multisig_wallet_descriptor=None if load_descriptor else descriptor
 if mismatch:
  from embit.descriptor import Descriptor
  controller.psbt_parser=PSBTParser(psbt,seeds[0],network=C.REGTEST,multisig_descriptor=descriptor)
  wrong=descriptor.to_string().replace('sortedmulti(2,','sortedmulti(3,')
  assert wrong!=descriptor.to_string()
  controller.multisig_wallet_descriptor=Descriptor.from_string(wrong)
 if select_seed and not import_seed:
  from seedsigner.models.seed import Seed
  unrelated=Seed(['abandon']*11+['about'])
  for public_seed in (unrelated,seeds[0]):
   controller.storage.set_pending_seed(public_seed);controller.storage.finalize_pending_seed()
  controller.psbt_seed=None
 if import_seed:
  assert select_seed and scan_psbt and load_descriptor
  assert controller.storage.num_seeds()==0 and controller.storage.get_pending_seed() is None
  controller.psbt_seed=None
 if load_descriptor or scan_psbt:
  from synthetic_frames import Source,LazySource
  from diagnostic_scope import attribute
  import shieldsigner_native_stream
  if scan_psbt:
   from seedsigner.helpers.ur2.ur import UR
   from seedsigner.helpers.ur2.ur_encoder import UREncoder
   from urtypes.crypto import PSBT as UR_PSBT
   encoder=UREncoder(UR('crypto-psbt',UR_PSBT(before).to_cbor()),max_fragment_len=80)
   parts=[]
   while True:
    parts.append(encoder.next_part().encode())
    if encoder.is_complete():break
    assert len(parts)<100
   psbt_source=LazySource(parts);source_queue.append(psbt_source)
  if import_seed:
   from embit import bip39
   seed_source=Source([bip39.mnemonic_to_bytes(' '.join(seeds[0].mnemonic_list))]);source_queue.append(seed_source)
  if load_descriptor:
   descriptor_source=Source([descriptor.to_string().encode()]);source_queue.append(descriptor_source)
  def stream_factory(**kwargs):
   assert source_queue,'Unexpected extra scan'
   return source_queue.pop(0)
  scope.enter_context(attribute(shieldsigner_native_stream,'NativeVideoStream',stream_factory))
 original_run=runtime.run
 def run(screen,args):
  global exported,decoded,psbt,input_exact
  name=screen.__name__;seen.append(name)
  print(json.dumps(dict(event='diagnostic-stage',screen=name)),flush=True)
  if scan_psbt and name=='PSBTOverviewScreen':
   assert controller.psbt.serialize()==before
   psbt=controller.psbt;input_exact=True
  snapshots.append(dict(screen=name,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid),system=system_snapshot()))
  if name=='PSBTChangeDetailsScreen':
   change_verified.append(args['is_change_addr_verified'])
   if mismatch:
    assert controller.multisig_wallet_descriptor is None and not args['is_change_addr_verified']
    raise StopFlowBasedTest()
  if name=='MainMenuScreen':
   if scan_psbt and len(seen)==1:
    buttons.load(['KEY_PRESS'])
    return original_run(screen,args)
   raise StopFlowBasedTest()
  if name=='QRDisplayScreen':
   exported=controller.psbt.serialize();buttons.load([]);buttons.capture=True;buttons.decoder=DecodeQR();buttons.last=0
  elif name=='ScanScreen' and (load_descriptor or scan_psbt):buttons.load(None)
  elif name=='LoadMultisigWalletDescriptorScreen' and load_descriptor:buttons.load(['KEY_DOWN']*20+['KEY_UP']*(len(args['button_data'])-1)+['KEY_PRESS'])
  elif name=='MultisigWalletDescriptorScreen' and load_descriptor:buttons.load(['KEY_DOWN']*20+['KEY_PRESS'])
  elif name=='SeedFinalizeScreen' and import_seed:
   assert controller.storage.num_seeds()==0
   assert controller.storage.get_pending_seed().mnemonic_list==seeds[0].mnemonic_list
   buttons.load(['KEY_PRESS'])
  elif name=='PSBTFinalizeScreen':buttons.load((['KEY_UP']*6 if cancel else ['KEY_DOWN']*4)+['KEY_PRESS'])
  elif name=='ButtonListScreen' and select_seed:
   assert args['title']=='Select Signer'
   assert controller.psbt_seed is None
   if import_seed:
    assert controller.storage.num_seeds()==0
    index=next(index for index,option in enumerate(args['button_data']) if option==PSBTSelectSeedView.SCAN_SEED)
    buttons.load(['KEY_DOWN']*index+['KEY_PRESS'])
   else:
    assert args['button_data'][0].button_label.endswith('(?)')
    assert args['button_data'][1].button_label==seeds[0].get_fingerprint(C.REGTEST)
    buttons.load(['KEY_DOWN','KEY_PRESS'])
  elif name=='WarningScreen':
   if mismatch:
    assert args['title']=='Descriptor mismatch' and args['status_headline']=='Descriptor cleared'
    assert controller.multisig_wallet_descriptor is None
    mismatch_warning.append(True)
   buttons.load(['KEY_DOWN']*16+['KEY_PRESS'])
  elif name in ('PSBTOverviewScreen','PSBTMathScreen','PSBTAddressDetailsScreen','PSBTChangeDetailsScreen'):buttons.load(['KEY_PRESS'])
  else:raise FlowBasedTestException('Unexpected multisig screen '+name)
  result=original_run(screen,args)
  if name=='QRDisplayScreen':decoded=buttons.decoder.get_data_psbt()
  return result
 runtime.run=run
 try:
  from seedsigner.views.scan_views import ScanPSBTView
  controller.start(initial_destination=Destination(MainMenuView if scan_psbt else (PSBTSelectSeedView if select_seed else (PSBTFinalizeView if cancel else PSBTOverviewView))),skip_startup_interstitials=True)
  assert View._initialize is original_initialize
  if load_descriptor:
   assert descriptor_source.is_stopped and descriptor_source.index>0
   assert 'ScanScreen' in seen and 'MultisigWalletDescriptorScreen' in seen
   assert change_verified==[False,True],change_verified
  assert seen[-1]==('PSBTChangeDetailsScreen' if mismatch else 'MainMenuScreen')
  if mismatch:
   assert mismatch_warning==[True] and change_verified==[False]
   assert controller.multisig_wallet_descriptor is None
  if select_seed:assert seen[2 if scan_psbt else 0]=='ButtonListScreen' and controller.storage.num_seeds()==(1 if import_seed else 2)
  if import_seed:
   assert seed_source.is_stopped and seed_source.index>0 and 'SeedFinalizeScreen' in seen
   assert controller.storage.seeds[0].mnemonic_list==seeds[0].mnemonic_list and controller.storage.get_pending_seed() is None
  if scan_psbt:assert input_exact and psbt_source.is_stopped and psbt_source.index>=len(parts) and not source_queue
  if cancel:
   assert seen==['PSBTFinalizeScreen','MainMenuScreen']
   assert exported is None and decoded is None and psbt.serialize()==before and PSBTParser.sig_count(psbt)==0
  elif mismatch:
   assert exported is None and decoded is None and psbt.serialize()==before and PSBTParser.sig_count(psbt)==0
  else:
   assert exported==decoded and exported is not None
   assert PSBTParser.sig_count(psbt)==1 and psbt.serialize()!=before
  for index,inp in enumerate(psbt.inputs):
   for pub,sig in inp.partial_sigs.items():assert pub.verify(Signature.parse(sig[:-1]),psbt.sighash(index,sighash=sig[-1]))
  if not mismatch:assert controller.psbt is None and controller.psbt_parser is None and controller.psbt_seed is None
  assert not Path(Settings.SETTINGS_FILENAME).exists()
 except BaseException:
  print(json.dumps(dict(passed=False,screenSequence=seen,changeVerificationStates=change_verified)),flush=True)
  raise
 finally:
  stop_workers(controller)
  for seed in [*seeds,*controller.storage.seeds]:seed.wipe()
  if unrelated is not None:unrelated.wipe()
 print(json.dumps(dict(passed=True,originalController=True,originalViewInitialization=True,psbtScannedThroughOriginalUI=scan_psbt,inputPSBTBytesExact=input_exact,syntheticInputFrames=scan_psbt,descriptorScannedThroughOriginalUI=load_descriptor,syntheticDescriptorFrames=load_descriptor,changeVerificationStates=change_verified,signerChosenThroughOriginalUI=select_seed,signerImportedThroughOriginalUI=import_seed,seedStorageInitiallyEmpty=import_seed,nonmatchingSeedMarked=select_seed and not import_seed,publicWalletFixture=True,descriptorPreloadedInController=not load_descriptor,screenSequence=seen,descriptorMismatchCleared=mismatch,approvalCancelled=cancel,unsignedBytesPreserved=cancel or mismatch,oneSignatureVerified=not(cancel or mismatch),exportedQRBytesExact=not(cancel or mismatch),ephemeralTransactionCleared=not mismatch,workerCleanup=True,resourceSnapshots=snapshots,matchedPerformanceComparison=False,physicalDisplay=True,physicalButtons=False,opticalQualified=False)),flush=True)

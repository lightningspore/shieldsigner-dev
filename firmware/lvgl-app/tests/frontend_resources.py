"""Same original Controller/GPIO script with PIL or LVGL; metadata-only benchmark."""
import json,os,sys,tempfile,time
from pathlib import Path
from contextlib import ExitStack
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from resources import process_snapshot,system_snapshot
from diagnostic_scope import attribute
from startup_policy import install as startup
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
legacy='--legacy' in sys.argv
dependency_restore=None
if not legacy:
 from dependency_policy import install as dependencies
 dependency_restore=dependencies('/opt/src',Path(__file__).parent/'source-guards.json')
 if '--eager-stream' in sys.argv:
  matches=[finder for finder in sys.meta_path if type(finder).__module__=='stream_imports' and type(finder).__qualname__=='install.<locals>.Finder']
  if len(matches)!=1:raise RuntimeError('Expected one isolated stream import policy')
  sys.meta_path.remove(matches[0])

pillow_import_edges=[]
if '--dependencies' in sys.argv:
 import builtins
 original_import=builtins.__import__
 def traced_import(name,*args,**kwargs):
  if name.startswith('PIL'):
   caller=sys._getframe(1)
   pillow_import_edges.append(dict(module=name,caller=caller.f_code.co_filename,line=caller.f_lineno,coreAlreadyLoaded='PIL.Image' in sys.modules))
  return original_import(name,*args,**kwargs)
 builtins.__import__=traced_import
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View,Destination,MainMenuView
from app import stop_workers
legacy='--legacy' in sys.argv;mode='pil' if legacy else 'lvgl';samples=[];dependency_audit=[];seen=[];homes=0;runtime=None;controller=None
camera_workload='--camera' in sys.argv
camera_backend=None
camera_stats=None
def pipeline_owners():
 result=[]
 for entry in Path('/proc').iterdir():
  if not entry.name.isdigit() or int(entry.name)==os.getpid():continue
  try:
   command=(entry/'cmdline').read_bytes().split(b'\0')[0].decode(errors='replace')
   if Path(command).name not in ('camera-probe','shieldsigner-camera','shieldsigner-camera-owner','shieldsigner-qr-reader'):continue
   result.append(dict(pid=int(entry.name),executable=Path(command).name,process=process_snapshot(int(entry.name))))
  except (OSError,ValueError):continue
 return result
def dma_summary():
 try:return Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]
 except (OSError,IndexError):return None
profiler=None;profile_started=False;profile_done=False
if '--profile' in sys.argv:
 import cProfile
 profiler=cProfile.Profile()
started=time.monotonic();clock_ticks=os.sysconf('SC_CLK_TCK');first_input=None
class Script:
 def load(self,phase,keys,idle=0):self.phase=phase;self.keys=keys;self.idle=idle;self.start=None;self.last=-1
 def active(self):
  global first_input,profile_started,profile_done
  now=time.monotonic()
  if self.start is None:self.start=now
  if first_input is None:first_input=now-started
  elapsed=now-self.start;second=int(elapsed)
  if profiler is not None and self.phase=='home-idle':
   if not profile_started:profiler.enable();profile_started=True
   if elapsed>=8 and not profile_done:profiler.disable();profile_done=True
  if second!=self.last:
   self.last=second
   if '--dependencies' in sys.argv and self.phase not in {item['phase'] for item in dependency_audit}:
    from seedsigner.gui.components import Fonts
    roots=('datetime','seedsigner.helpers.version','seedsigner.models.aezeed','decimal','_decimal','PIL','qrcode','embit','urtypes','Cryptodome','cryptography','pgpy','pyasn1','pysatochip','smartcard','pygp','ecdsa','pyaes','ndef','shamir_mnemonic','numpy','cv2','pyzbar')
    loaded={root:sum(name==root or name.startswith(root+'.') for name in sys.modules) for root in roots}
    dependency_audit.append(dict(phase=self.phase,loadedPackageModuleCounts=loaded,fontCache={name:sorted(sizes) for name,sizes in Fonts.fonts.items()},screenModules=sorted(name for name in sys.modules if name.startswith('seedsigner.gui.')),python=process_snapshot(os.getpid())))
   samples.append(dict(phase=self.phase,elapsed=round(elapsed,4),wall=round(now,4),python=process_snapshot(os.getpid()),native=None if runtime is None else process_snapshot(runtime.host.child.pid),pipelineOwners=pipeline_owners(),dma=dma_summary(),system=system_snapshot()))
  if elapsed<self.idle:return set()
  if self.phase=='camera-live':
   if elapsed>self.idle+30:raise FlowBasedTestException('Held camera cancellation stalled')
   return {'KEY_LEFT'}
  offset=elapsed-self.idle;index=int(offset/.4)
  if index>=len(self.keys):
   if offset>len(self.keys)*.4+5:raise FlowBasedTestException('Resource script stalled at '+self.phase)
   return set()
  return {self.keys[index]} if offset%.4<.22 else set()
script=Script()
with tempfile.TemporaryDirectory(prefix='lvgl-resource-pair-') as temporary,ExitStack() as scope:
 if dependency_restore is not None:scope.callback(dependency_restore)
 Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
 settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
 settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
 guards=Path(__file__).parent/'source-guards.json'
 from guards import verify
 verify('/opt/src',guards)
 if not legacy:
  from luckfox import LuckfoxHardware
  from runtime import Runtime,install_view_dispatch
  from renderer_bridge import install as renderer
  from toast_bridge import install as toasts
  import seedsigner.gui.toast as toast
  hardware=LuckfoxHardware();scope.callback(hardware.close)
  runtime=Runtime(sys.argv[1],hardware.pixels,hardware.read_buttons,hardware.buttons.update_last_input_time);scope.callback(runtime.close)
  scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer));scope.callback(toasts(runtime,toast))
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 if legacy and camera_workload:
  # Match the working Rust camera/QR/LCD launch, not stock V4L2 /dev/video12.
  # startup() above verifies this integration module's pinned digest first.
  import shieldsigner_integration as integration
  os.environ['SHIELDSIGNER_FRONTEND_BACKEND']='rust'
  os.environ['SHIELDSIGNER_CAMERA_CONFIG']='/usr/lib/shieldsigner-camera/owner.json'
  os.environ['SHIELDSIGNER_QR_READER']='/usr/lib/shieldsigner-camera/shieldsigner-qr-reader'
  lcd_backend=integration.configure_lcd_backend('/opt/src','rust')
  camera_module=integration.install_camera_backend('/opt/src')
  camera_backend=dict(camera=camera_module.__shieldsigner_camera_patch__,lcd=lcd_backend)
 from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
 from seedsigner.hardware.microsd import MicroSD
 from seedsigner.hardware.buttons import HardwareButtons
 from microsd_lifecycle import install as microsd
 scope.callback(microsd(MicroSD,'/opt/src',guards))
 controller=Controller.get_instance();controller.boot_failover_cleared=True
 buttons=HardwareButtons.get_instance()
 if legacy:
  scope.callback(Renderer.get_instance().disp.cleanup)
  original_pins=dict(buttons._gpio_pins)
  scope.callback(lambda:[pin.close() for pin in original_pins.values()])
 fake_pins={name:SimpleNamespace(read=lambda name=name:name not in script.active()) for name in buttons._gpio_pins}
 scope.enter_context(attribute(buttons,'_gpio_pins',fake_pins))
 original_screen=View.run_screen;original_initialize=View._initialize
 def screen(view,cls,**kwargs):
  global homes
  name=cls.__name__;seen.append(name)
  print(json.dumps(dict(event='diagnostic-stage',mode=mode,screen=name)),flush=True)
  if name=='MainMenuScreen':
   homes+=1
   if homes==2:raise StopFlowBasedTest()
   script.load('home-idle',['KEY_PRESS'] if camera_workload else ['KEY_DOWN','KEY_RIGHT','KEY_PRESS'],idle=8)
  elif name=='ScanScreen' and camera_workload:
   # Fixed-duration lifecycle/resource workload even if a QR happens to be in
   # view. Original camera/decoder processing runs; payload completion is blocked.
   from seedsigner.models.decode_qr import DecodeQRStatus
   script.load('camera-live',['KEY_LEFT'],idle=15)
   with attribute(kwargs['decoder'],'add_data',lambda payload:DecodeQRStatus.FALSE):
    return original_screen(view,cls,**kwargs)
  elif name=='ButtonListScreen':
   assert kwargs['title']=='Settings',kwargs['title']
   script.load('settings',['KEY_UP']*10+['KEY_PRESS'])
  else:raise FlowBasedTestException('Unexpected benchmark screen '+name)
  return original_screen(view,cls,**kwargs)
 scope.enter_context(attribute(View,'run_screen',screen))
 try:
  controller.start(initial_destination=Destination(MainMenuView),skip_startup_interstitials=True)
  assert seen==['MainMenuScreen','ScanScreen' if camera_workload else 'ButtonListScreen','MainMenuScreen'] and View._initialize is original_initialize
  idle=[sample for sample in samples if sample['phase']=='home-idle' and 1<=sample['elapsed']<8]
  assert len(idle)>=6
  if camera_workload:
   camera_stats=(dict(qr=dict(camera_module.__shieldsigner_qr_client__.stats)) if legacy else runtime.camera_stats)
   assert camera_stats['qr']['calls']>0,camera_stats
   if not legacy:assert camera_stats['frames']>0 and camera_stats['cameraStopped'] and camera_stats['ownerExitCode']==0,camera_stats
   live=[sample for sample in samples if sample['phase']=='camera-live' and 5<=sample['elapsed']<15]
   assert len(live)>=8
   assert any(any(owner['executable']=='camera-probe' for owner in sample['pipelineOwners']) for sample in live)
   assert not pipeline_owners(),pipeline_owners()
   assert dma_summary()=='Total 0 objects, 0 bytes',dma_summary()
  assert not Path(Settings.SETTINGS_FILENAME).exists()
 finally:stop_workers(controller)
 profile_rows=[]
 if profiler is not None:
  profiler.disable()
  import pstats
  stats=pstats.Stats(profiler)
  for (file,line,name),(cc,nc,tt,ct,callers) in sorted(stats.stats.items(),key=lambda item:item[1][2],reverse=True)[:30]:
   profile_rows.append(dict(file=Path(file).name,function=name,line=line,calls=nc,ownSeconds=round(tt,6),cumulativeSeconds=round(ct,6)))
 print(json.dumps(dict(passed=True,originalEagerStreamImportDiagnostic='--eager-stream' in sys.argv,pillowImportEdges=pillow_import_edges,dependencyAudit=dependency_audit,idleProfile=profile_rows,profilingOverheadIncluded=profiler is not None,frontend=mode,cameraBackend=camera_backend,cameraStats=camera_stats,originalController=True,sameSmallRamPolicy=True,sameGPIOScript=True,idleSeconds=8,cameraSeconds=15 if camera_workload else 0,clockTicks=clock_ticks,secondsToFirstInputPoll=round(first_input,4),screenSequence=seen,samples=samples,physicalDisplay=True,physicalButtons=False,cameraStarted=camera_workload,cameraCompletionSuppressed=camera_workload,bootCounterOverrideDiagnosticOnly=True,matchedColdStart=False,totalMemoryNotRSSSum=True)),flush=True)

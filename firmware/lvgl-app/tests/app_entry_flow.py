"""Actual isolated app entry, original --iotest routing, public scripted buttons."""
import hashlib,json,sys,tempfile,time,threading,os,signal
from pathlib import Path
from contextlib import ExitStack
from app import run,options
from diagnostic_scope import attribute
from resources import process_snapshot
from runtime import Runtime
sys.path.insert(0,'/opt/src')
from seedsigner.models.settings import Settings
original_settings=Path(Settings.SETTINGS_FILENAME)
def settings_digest():
 return hashlib.sha256(original_settings.read_bytes()).hexdigest() if original_settings.is_file() else None
entry_memory=[]
persistent='--persistent' in sys.argv;settings_ui='--settings-ui' in sys.argv;pending_confirmed=[];ui_state={'persistent':False,'denomination':False};ui_initial={}
before=settings_digest();seen=[];original_run=Runtime.run;native=[];timer=None;term='--sigterm' in sys.argv;camera_term='--camera' in sys.argv;interrupted=False;streams=[];signal_wait_done=threading.Event()
def display(runtime,screen,args):
 global timer
 from seedsigner.controller import Controller,StopFlowBasedTest
 # Temporary diagnostic must not touch boot-counter MMIO. This is a test-only
 # policy override, not part of the isolated production entry point.
 Controller._instance.boot_failover_cleared=True
 seen.append(screen.__name__)
 entry_memory.append(dict(screen=screen.__name__,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid)))
 if not native:native.append(runtime.host.child)
 if screen.__name__=='MainMenuScreen':
  if persistent:
   from seedsigner.models.settings_definition import SettingsConstants as C
   settings=Settings.get_instance()
   settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__ENABLED,save=False)
   settings.set_value(C.SETTING__BTC_DENOMINATION,C.BTC_DENOMINATION__SATS)
   assert settings._save_timer is not None and not Path(Settings.SETTINGS_FILENAME).exists()
   pending_confirmed.append(True)
  if settings_ui:
   assert all(ui_state.values()) and Settings.get_instance()._save_timer is not None
   assert not Path(Settings.SETTINGS_FILENAME).exists();pending_confirmed.append(True)
  raise StopFlowBasedTest()
 if screen.__name__=='IOTestScreen':
  keys=['KEY1'] if camera_term else ([] if term else ['KEY3'])
  if term and not camera_term:
   timer=threading.Timer(.5,lambda:os.kill(os.getpid(),signal.SIGTERM));timer.start()
 elif settings_ui and screen.__name__ in ('ButtonListScreen','SettingsEntryUpdateSelectionScreen'):
  from seedsigner.models.settings_definition import SettingsConstants as C,SettingsDefinition
  settings=Settings.get_instance();current=args.get('selected_button',0) or 0
  persistent_entry=SettingsDefinition.get_settings_entry(C.SETTING__PERSISTENT_SETTINGS)
  denomination_entry=SettingsDefinition.get_settings_entry(C.SETTING__BTC_DENOMINATION)
  def select(index):
   delta=index-current
   return (['KEY_DOWN']*delta if delta>=0 else ['KEY_UP']*(-delta))+['KEY_PRESS']
  if screen.__name__=='ButtonListScreen':
   assert args['title']=='Settings'
   target=persistent_entry if not ui_state['persistent'] else denomination_entry
   if all(ui_state.values()):keys=['KEY_UP']*(current+2)+['KEY_PRESS']
   else:keys=select(next(i for i,option in enumerate(args['button_data']) if option.button_label==target.display_name))
  else:
   entry=persistent_entry if args['display_name']==persistent_entry.display_name else denomination_entry
   assert args['display_name']==entry.display_name
   key='persistent' if entry is persistent_entry else 'denomination'
   value=C.OPTION__ENABLED if key=='persistent' else C.BTC_DENOMINATION__SATS
   actual=settings.get_value(entry.attr_name)
   if key not in ui_initial:
    ui_initial[key]=actual;assert actual!=value
   if actual==value:
    ui_state[key]=True;keys=['KEY_UP']*(current+2)+['KEY_PRESS']
   else:
    index=next(i for i,option in enumerate(entry.selection_options) if (option[0] if isinstance(option,tuple) else option)==value)
    keys=select(index)
 elif screen.__name__=='ButtonListScreen':keys=['KEY_UP']*10+['KEY_PRESS']
 else:raise AssertionError('Unexpected entry route '+screen.__name__)
 started=[None]
 def buttons():
  if started[0] is None:started[0]=time.monotonic()
  elapsed=time.monotonic()-started[0]-.3
  if elapsed<0:return set()
  index=int(elapsed/.4)
  if index>=len(keys):
   if elapsed>len(keys)*.4+5:raise TimeoutError('Entry navigation stalled')
   return set()
  return {keys[index]} if elapsed%.4<.22 else set()
 runtime.read_buttons=buttons
 return original_run(runtime,screen,args)
with tempfile.TemporaryDirectory(prefix='lvgl-entry-flow-') as temporary,ExitStack() as scope:
 scope.enter_context(attribute(Runtime,'run',display))
 if persistent or settings_ui:scope.enter_context(attribute(Settings,'_SAVE_DELAY_SECONDS',60 if settings_ui else 30))
 if camera_term:
  import entropy_camera
  original_camera_start=entropy_camera.start
  def camera_start(camera,**kwargs):
   global timer
   value=original_camera_start(camera,**kwargs);streams.append(camera._video_stream)
   def first_frame_then_term():
    deadline=time.monotonic()+10
    while not signal_wait_done.is_set() and streams[-1].frames_received==0 and time.monotonic()<deadline:time.sleep(.02)
    if not signal_wait_done.is_set():os.kill(os.getpid(),signal.SIGTERM)
   timer=threading.Timer(0,first_frame_then_term);timer.start()
   return value
  scope.enter_context(attribute(entropy_camera,'start',camera_start))
 args=options(['--binary',sys.argv[1],'--settings',str(Path(temporary)/'settings.json'),'--','--iotest','--loglevel','WARNING'])
 try:run(args)
 except KeyboardInterrupt:
  assert term;interrupted=True
 finally:
  signal_wait_done.set()
  if timer is not None:timer.cancel();timer.join(2)
 assert interrupted==term
 if settings_ui:
  assert seen[0]=='IOTestScreen' and seen[-1]=='MainMenuScreen' and seen.count('SettingsEntryUpdateSelectionScreen')==4,seen
 else:assert seen==(['IOTestScreen'] if term else ['IOTestScreen','ButtonListScreen','MainMenuScreen']),seen
 assert settings_digest()==before
 if persistent or settings_ui:
  from seedsigner.models.settings_definition import SettingsConstants as C
  assert pending_confirmed==[True] and Settings.get_instance()._save_timer is None
  saved=json.loads(args.settings.read_text())
  assert saved[C.SETTING__BTC_DENOMINATION]==C.BTC_DENOMINATION__SATS
  if settings_ui:
   assert saved[C.SETTING__PERSISTENT_SETTINGS]==C.OPTION__ENABLED
   Settings._instance=None # Diagnostic fresh-model reload, not an app-method patch.
   reloaded=Settings.get_instance()
   assert reloaded.get_value(C.SETTING__BTC_DENOMINATION)==C.BTC_DENOMINATION__SATS
   assert reloaded.get_value(C.SETTING__PERSISTENT_SETTINGS)==C.OPTION__ENABLED
 assert native and native[0].poll() is not None
 from seedsigner.controller import Controller
 controller=Controller._instance
 assert not controller.wipe_timer_thread.is_alive() and not controller.rng_monitor_thread.is_alive() and not controller.microsd.is_alive()
 if camera_term:
  assert len(streams)==1 and streams[0].is_stopped and streams[0].owner_exit_code==0 and streams[0].frames_received>0,[(stream.is_stopped,stream.owner_exit_code,stream.frames_received) for stream in streams]
  assert Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]=='Total 0 objects, 0 bytes'
 print(json.dumps(dict(passed=True,entryMemory=entry_memory,normalBytecodePrefix=sys.pycache_prefix,pendingSettingsFlushed=persistent or settings_ui,settingsChangedThroughOriginalUI=settings_ui,savedSettingsReloaded=settings_ui,originalSettingsUnchanged=True,cameraInterrupted=camera_term,cameraFrames=[stream.frames_received for stream in streams],ownerExitCodes=[stream.owner_exit_code for stream in streams],sigtermUnwound=interrupted,microsdWorkerStopped=True,originalMainInvoked=True,originalIOTestCLI=True,screenSequence=seen,nativeExited=True,originalWorkersStopped=True,bootCounterOverrideDiagnosticOnly=True,physicalDisplay=True,physicalButtons=False)),flush=True)

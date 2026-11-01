"""Pinned microSD callbacks with private real FIFO; metadata/toast fixtures."""
import json,os,sys,tempfile,time
from pathlib import Path
from contextlib import ExitStack
from types import SimpleNamespace
sys.path.insert(0,'/opt/src')
from diagnostic_scope import attribute
from microsd_lifecycle import install
from seedsigner.hardware.microsd import MicroSD
from seedsigner.models.settings import Settings
from seedsigner.controller import Controller
import seedsigner.gui.toast as toast
settings=[];toasts=[]
def until(condition):
 deadline=time.monotonic()+3
 while not condition():
  assert time.monotonic()<deadline,'microSD event deadline'
  time.sleep(.01)
with tempfile.TemporaryDirectory(prefix='lvgl-microsd-events-') as temporary,ExitStack() as scope:
 path=Path(temporary)/'events';worker=MicroSD.get_instance();original=MicroSD.run
 scope.callback(install(MicroSD,'/opt/src',Path(__file__).parent/'source-guards.json'))
 scope.enter_context(attribute(MicroSD,'FIFO_PATH',str(path)))
 scope.enter_context(attribute(MicroSD,'is_inserted',property(lambda self:True)))
 scope.enter_context(attribute(Settings,'is_seedsigner_os',classmethod(lambda cls:True)))
 scope.enter_context(attribute(Settings,'handle_microsd_state_change',classmethod(lambda cls,action:settings.append(action))))
 scope.enter_context(attribute(Controller,'get_instance',classmethod(lambda cls:SimpleNamespace(activate_toast=toasts.append))))
 scope.enter_context(attribute(toast,'SDCardStateChangeToastManagerThread',lambda action:action))
 try:
  worker.start_detection();until(path.exists)
  for index,message in enumerate((b'add',b'remove')):
   deadline=time.monotonic()+3
   while True:
    try:descriptor=os.open(path,os.O_WRONLY|os.O_NONBLOCK);break
    except OSError:
     assert time.monotonic()<deadline,'FIFO reader did not open';time.sleep(.01)
   with os.fdopen(descriptor,'wb',buffering=0) as writer:
    writer.write(message[:1]);time.sleep(.02);writer.write(message[1:])
   until(lambda:len(toasts)==index+1)
  before=(list(settings),list(toasts));worker.stop();worker.join(2)
  assert not worker.is_alive() and before==(settings,toasts)
  assert settings==['add','add','remove'] and toasts==['add','remove'],(settings,toasts)
 finally:
  worker.stop();worker.join(2)
assert MicroSD.run is original
print(json.dumps(dict(passed=True,pinnedOriginalRun=True,privateFIFO=True,chunkedMessagesPreserved=True,initialStorageCallback=True,settingsActions=settings,toastActions=toasts,stopAddedNoEvent=True,workerStopped=True,methodRestored=True,physicalHotplug=False,physicalDisplay=False)),flush=True)

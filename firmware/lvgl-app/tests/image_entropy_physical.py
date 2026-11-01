"""Public exact-text encrypted entry contracts and original discard routes."""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from runtime import Runtime,install_view_dispatch
from seedsigner.gui.screens.seed_screens import SeedAddPassphraseScreen
from seedsigner.models.seed import Seed
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        t=now-self.start-.5
        if t<0:return set()
        i=int(t/.35)
        if i>=len(self.keys):
            if t>len(self.keys)*.35+5:raise TimeoutError('Passphrase navigation did not finish')
            return set()
        return {self.keys[i]} if t%.35<.22 else set()
buttons=Buttons();rectangles=0;hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
import os,faulthandler
from resources import process_snapshot,system_snapshot
os.environ['SHIELDSIGNER_SMALL_RAM']='1'
from seedsigner.controller import Controller
from seedsigner.views.tools_views import ToolsImageEntropyLivePreviewView,ToolsImageEntropyFinalImageView
from seedsigner.views.view import BackStackView
from diagnostic_scope import attribute
import image_entropy,entropy_camera
original_initialize=View._initialize;original_controller=Controller._instance
original_start=entropy_camera.start;original_display=image_entropy.display_image
scripted=buttons.__call__;frames=0;streams=[];checks=[];display_durations=[];snapshots=[]
def start(camera,**kwargs):
    result=original_start(camera,**kwargs);streams.append(camera._video_stream);return result
def display(*args,**kwargs):
    global frames
    before=time.monotonic()
    if len(snapshots)<12:
        snapshots.append(dict(stage='before-display',frames=frames,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid),system=system_snapshot()))
    try:result=None if '--no-display-updates' in sys.argv else original_display(*args,**kwargs);frames+=1;return result
    finally:display_durations.append(time.monotonic()-before)
with tempfile.TemporaryDirectory(prefix='lvgl-physical-entropy-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    controller=SimpleNamespace(hardware_rng_is_healthy=True,hardware_rng_failure_reason=None,image_entropy_preview_frames=None,image_entropy_final_image=None)
    Controller._instance=controller
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        with attribute(entropy_camera,'start',start),attribute(image_entropy,'display_image',display):
            for cancel in (False,True):
                frames=0;started=time.monotonic();ready_frame=None
                def keys():
                    global ready_frame
                    if time.monotonic()-started>60:raise TimeoutError('Physical entropy acquisition stalled: '+str(getattr(runtime,'entropy_stats',{})))
                    if frames>=30:return {'KEY_LEFT'}
                    if cancel:return {'KEY_LEFT'} if frames>=3 else set()
                    if getattr(runtime,'entropy_stats',{}).get('poolFrames')==5:
                        if ready_frame is None:ready_frame=frames
                        if frames>ready_frame:return {'KEY_PRESS'}
                    return set()
                runtime.read_buttons=keys
                print(json.dumps(dict(stage='physical-entropy',cancel=cancel)),flush=True)
                destination=ToolsImageEntropyLivePreviewView().run()
                assert streams[-1].is_stopped and streams[-1].owner_exit_code==0
                dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]
                assert dma=='Total 0 objects, 0 bytes',dma
                if cancel:
                    assert destination.View_cls is BackStackView
                    assert controller.image_entropy_final_image is None and controller.image_entropy_preview_frames is None
                else:
                    assert destination.View_cls is ToolsImageEntropyFinalImageView
                    assert len(controller.image_entropy_preview_frames)==5
                    assert controller.image_entropy_final_image.mode=='RGB'
                    assert controller.image_entropy_final_image.size in ((640,480),(480,640))
                    runtime.read_buttons=scripted;buttons.load(['KEY_LEFT'])
                    destination=destination.View_cls(**destination.view_args).run()
                    assert destination.View_cls is BackStackView and controller.image_entropy_final_image is None
                controller.image_entropy_preview_frames=None;controller.image_entropy_final_image=None
                checks.append(dict(cancel=cancel,entropyStats=dict(runtime.entropy_stats),displayedFrames=frames,ownerExitCode=0,dma=dma,seconds=round(time.monotonic()-started,3)))
        print(json.dumps(dict(passed=True,checks=checks,resourceSnapshots=snapshots,originalSampleReads=True,mockFrameworkLoaded=any(name.startswith('unittest') for name in sys.modules),displayUpdatesDisabled='--no-display-updates' in sys.argv,physicalCamera=True,physicalDisplay=hardware is not None,physicalButtons=False,rngHealthStatusInjected=True,dependencyInitializationInjected=True,walletGenerated=False,pixelsSaved=False,mixerQualified=False)),flush=True)
    except BaseException:
        faulthandler.dump_traceback()
        print(json.dumps(dict(stage='physical-entropy-failure',displayDurations=display_durations,resourceSnapshots=snapshots,hostError=str(runtime.host.error),hostExitCode=runtime.host.child.poll(),entropyStats=getattr(runtime,'entropy_stats',{}),displayedFrames=frames,ownerExitCodes=[stream.owner_exit_code for stream in streams])),flush=True)
        raise
    finally:
        controller.image_entropy_preview_frames=None;controller.image_entropy_final_image=None
        Controller._instance=original_controller;View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()

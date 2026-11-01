"""Original final-image fallback with physical Rust camera and native review."""
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
    original_run=ToolsImageEntropyFinalImageView.run
    try:
        with attribute(entropy_camera,'start',start):
            for key in ('KEY_LEFT','KEY_PRESS'):
                controller.image_entropy_final_image=None
                buttons.load([key]);runtime.read_buttons=scripted
                began=time.monotonic()
                view=ToolsImageEntropyFinalImageView()
                assert ToolsImageEntropyFinalImageView.run is not original_run
                destination=view.run()
                stream=streams[-1]
                assert stream.is_stopped and stream.owner_exit_code==0
                dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]
                assert dma=='Total 0 objects, 0 bytes',dma
                if key=='KEY_LEFT':
                    assert destination.View_cls is BackStackView
                    assert controller.image_entropy_final_image is None
                else:
                    from seedsigner.views.tools_views import ToolsImageEntropyMnemonicLengthView
                    assert destination.View_cls is ToolsImageEntropyMnemonicLengthView
                    image=controller.image_entropy_final_image
                    assert image.mode=='RGB' and image.size in ((640,480),(480,640))
                checks.append(dict(key=key,ownerExitCode=stream.owner_exit_code,dma=dma,seconds=round(time.monotonic()-began,3)))
    finally:
        controller.image_entropy_preview_frames=None;controller.image_entropy_final_image=None
        Controller._instance=original_controller;View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()
    assert ToolsImageEntropyFinalImageView.run is original_run
    print(json.dumps(dict(passed=True,checks=checks,originalMethodRestored=True,physicalCamera=True,physicalDisplay=hardware is not None,physicalButtons=False,dependencyInitializationInjected=True,walletGenerated=False,pixelsSaved=False)),flush=True)

"""Original entropy Views with full-resolution synthetic images and resource metrics."""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
import os
from resources import process_snapshot,system_snapshot
started=time.monotonic();snapshots=[];preview_seconds=[];pixel_seconds=0.0;pixel_bytes=0
import faulthandler,signal
faulthandler.register(signal.SIGUSR1,all_threads=True)
def record(stage,**details):
    item=dict(stage=stage,seconds=round(time.monotonic()-started,3),python=process_snapshot(os.getpid()),system=system_snapshot(),**details)
    snapshots.append(item);print(json.dumps(item),flush=True)
record('before-app-imports')
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
    global rectangles,pixel_seconds,pixel_bytes
    rectangles+=1;pixel_bytes+=len(data);before=time.monotonic()
    if hardware is not None:hardware.pixels(area,data)
    pixel_seconds+=time.monotonic()-before
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
from seedsigner.controller import Controller
from seedsigner.views.tools_views import ToolsImageEntropyLivePreviewView,ToolsImageEntropyFinalImageView,ToolsImageEntropyMnemonicLengthView
from seedsigner.views.seed_views import SeedWordsWarningView
from seedsigner.views.view import BackStackView
from unittest.mock import patch
from PIL import Image
from embit import bip39
import hashlib
class Camera:
    def __init__(self):self._video_stream=None;self.reads=0;self.started=False;self.stopped=False
    def start_video_stream_mode(self):self.started=True;self.stopped=False
    def stop_video_stream_mode(self):self.stopped=True
    def read_video_stream(self,as_image=True,preview=False):
        self.reads+=1
        pixels=hashlib.shake_256(b'public synthetic camera '+str(self.reads).encode()).digest(640*480*3)
        return Image.frombytes('RGB',(640,480),pixels)
import image_entropy
original_display=image_entropy.display_image
def measured_display(*args,**kwargs):
    before=time.monotonic()
    try:return original_display(*args,**kwargs)
    finally:preview_seconds.append(time.monotonic()-before)
image_entropy.display_image=measured_display
record('app-imports-complete')
original_initialize=View._initialize;original_controller=Controller._instance;scripted=buttons.__call__
with tempfile.TemporaryDirectory(prefix='lvgl-image-entropy-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__SEED_WORD_LENGTHS,[12],save=False)
    storage=SeedStorage();controller=SimpleNamespace(storage=storage,settings=settings,hardware_rng_is_healthy=False,hardware_rng_failure_reason='Public RNG failure fixture',image_entropy_preview_frames=None,image_entropy_final_image=None,create_slip39=False)
    Controller._instance=controller
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        record("rng-refusal")
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS'])
        with patch('entropy_camera.create',side_effect=AssertionError('RNG gate opened camera')):destination=ToolsImageEntropyLivePreviewView().run()
        assert destination.View_cls is BackStackView
        controller.hardware_rng_is_healthy=True
        for reshoot in (True,False):
            record("acquire",reshoot=reshoot)
            camera=Camera()
            def acquisition_buttons():
                if camera.reads<6:return {'KEY_PRESS'}
                return {'KEY_PRESS'} if camera.reads>=18 else set()
            runtime.read_buttons=acquisition_buttons
            with patch('entropy_camera.create',return_value=camera):destination=ToolsImageEntropyLivePreviewView().run()
            record("acquired",reads=camera.reads)
            assert destination.View_cls is ToolsImageEntropyFinalImageView
            assert camera.started and camera.stopped and camera.reads>=19
            assert len(controller.image_entropy_preview_frames)==5
            assert all(frame.size==(96,96) and frame.mode=='L' for frame in controller.image_entropy_preview_frames)
            final=controller.image_entropy_final_image;before=hashlib.sha256(final.tobytes()).digest()
            runtime.read_buttons=scripted;buttons.load(['KEY_LEFT' if reshoot else 'KEY_PRESS'])
            destination=destination.View_cls(**destination.view_args).run()
            assert hashlib.sha256(final.tobytes()).digest()==before
            final=None  # Do not retain the old reshoot frame across the next acquisition.
            if reshoot:
                assert destination.View_cls is BackStackView and controller.image_entropy_final_image is None
            else:assert destination.View_cls is ToolsImageEntropyMnemonicLengthView
        record('mix-original-entropy')
        buttons.load(['KEY_DOWN']*12+['KEY_PRESS']);destination=destination.View_cls(**(destination.view_args or {})).run()
        assert destination.View_cls is SeedWordsWarningView
        seed=storage.get_pending_seed();assert seed is not None and len(seed.mnemonic_list)==12
        assert len(bip39.mnemonic_to_bytes(seed.mnemonic_str))==16
        assert controller.image_entropy_preview_frames is None and controller.image_entropy_final_image is None
        record("complete")
        print(json.dumps(dict(passed=True,resourceSnapshots=snapshots,previewSeconds=preview_seconds,pixelWriteSeconds=pixel_seconds,pixelBytes=pixel_bytes,rngFailureRefusedBeforeCamera=True,heldCaptureGate=True,previewPool=5,finalPixelsUnmodified=True,reshootAndAccept=True,originalMixerAndSystemRng=True,originalPendingSeed=True,imageReferencesCleared=True,physicalDisplay=hardware is not None,physicalCamera=False,physicalButtons=False,dependencyInitializationInjected=True,rngHealthStatusInjected=True)),flush=True)
    finally:
        storage.clear_pending_seed();controller.image_entropy_preview_frames=None;controller.image_entropy_final_image=None
        image_entropy.display_image=original_display
        Controller._instance=original_controller;View._initialize=original_initialize;restore();runtime.close()
        if hardware is not None:hardware.close()

# SPDX-License-Identifier: MIT
"""Native foreground camera capture/review; source keys and held-key semantics."""
import time
from seedsigner_port.camera_entropy import CameraFrame,CameraPool,PREVIEW_POOL_SIZE,clear_images

RET_CODE__BACK_BUTTON=1000
CLICKS=('KEY_PRESS','KEY1','KEY2','KEY3')
REVIEW_KEYS=('KEY_LEFT','KEY_RIGHT')+CLICKS

def _runtime(camera,buttons,backend,service,sleep):
    if camera is None or buttons is None or backend is None or service is None:
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.controller import Controller
        renderer=Renderer.get_instance()
        if camera is None:camera=Controller.get_instance().camera
        if buttons is None:buttons=renderer.buttons
        if backend is None:backend=renderer.backend
        if service is None:service=renderer.service
    return camera,buttons,backend,service,sleep if sleep is not None else time.sleep_ms

class ToolsImageEntropyLivePreviewScreen:
    PREVIEW_POOL_SIZE=PREVIEW_POOL_SIZE
    def __init__(self,camera=None,buttons=None,backend=None,service=None,sleep=None):
        self.camera,self.buttons,self.backend,self.service,self.sleep=_runtime(camera,buttons,backend,service,sleep)
    def display(self):
        from seedsigner_port.localization import gettext as _
        pool=CameraPool();transferred=False;surface=False;pending_samples=None;pending_final=None
        self.buttons.reset_input()
        try:
            self.backend.scan_begin('< '+_('back')+' | '+_('click a button'));surface=True
            self.camera.start_video_stream_mode()
            is_maybe_still_holding=True
            while True:
                self.service()
                if self.buttons.check_for_low('KEY_LEFT'):return RET_CODE__BACK_BUTTON
                frame=self.camera.read_video_stream()
                if frame is None:self.sleep(10);continue
                self.backend.scan_frame(frame)
                # Same source order: the pool must already be full, then observe
                # all click keys released, then a deliberate fresh click captures.
                if pool.ready:
                    if not self.buttons.check_for_low(keys=CLICKS):is_maybe_still_holding=False
                    elif not is_maybe_still_holding:
                        pending_final=CameraFrame(self.camera.read_video_stream())
                        pending_samples=pool.transfer();transferred=True
                        return pending_samples,pending_final
                pool.add(frame)
        finally:
            try:
                try:self.camera.stop_video_stream_mode()
                finally:
                    if surface:self.backend.scan_end()
            except BaseException:
                clear_images(pending_samples,pending_final)
                raise
            finally:
                if not transferred:pool.clear()

class ToolsImageEntropyFinalImageScreen:
    def __init__(self,final_image,buttons=None,backend=None,service=None,sleep=None):
        _,self.buttons,self.backend,self.service,self.sleep=_runtime(object(),buttons,backend,service,sleep)
        self.image=final_image
    def display(self):
        from seedsigner_port.localization import gettext as _
        self.buttons.reset_input();surface=False
        try:
            self.backend.scan_begin('< '+_('reshoot')+' | '+_('accept')+' >');surface=True
            self.backend.scan_frame(self.image.tobytes())
            # Existing ButtonInput blocks keys held at reset until released. The
            # explicit source release gate is retained as well for injected inputs.
            while self.buttons.check_for_low(keys=REVIEW_KEYS):self.service();self.backend.tick();self.sleep(10)
            while True:
                self.service();self.backend.tick()
                key=self.buttons.poll(REVIEW_KEYS)
                if key is not None:return RET_CODE__BACK_BUTTON if key in ('KEY_LEFT',RET_CODE__BACK_BUTTON) else None
                self.sleep(10)
        finally:
            if surface:self.backend.scan_end()

def __getattr__(name):
    if name=='ToolsDiceEntropyEntryScreen':
        from seedsigner_port.camera_entropy_dice import ToolsDiceEntropyEntryScreen
        return ToolsDiceEntropyEntryScreen
    if name=='ToolsCoinFlipEntryScreen':
        from seedsigner_port.final_word import ToolsCoinFlipEntryScreen
        return ToolsCoinFlipEntryScreen
    if name in ('ToolsCalcFinalWordFinalizePromptScreen','ToolsCalcFinalWordScreen','ToolsCalcFinalWordDoneScreen'):
        from seedsigner_port import app_screens
        return getattr(app_screens,name)
    raise AttributeError(name)

# SPDX-License-Identifier: MIT
"""Cooperative runtime for the original ScanScreen._run method.

The original completion/invalid/fragment/back loop is source-generated. Sensor,
clock, input and preview ownership live here. Native instruction/progress overlays
and the original BaseScreen/View dispatcher remain separate unfinished work.
"""
import time
from seedsigner_port.scan_loop import run_source
from seedsigner_port.buttons import ButtonInput

class ElapsedClock:
    def __init__(self):
        self.last=time.ticks_ms()
        self.total=0
    def time(self):
        now=time.ticks_ms()
        self.total+=(now-self.last)&0xffffffff
        self.last=now
        return self.total/1000

class NativeVideoStream:
    def __init__(self,backend=None):
        if backend is None:
            import camera
            backend=camera
        self.backend=backend
        self.active=False
    def start_video_stream_mode(self):
        if self.active:raise RuntimeError('Scan camera already started')
        self.backend.init()
        self.backend.start_preview()
        self.active=True
    def read_video_stream(self):
        if not self.active:raise RuntimeError('Scan camera not started')
        return self.backend.next_preview()
    def stop_video_stream_mode(self):
        if self.active:
            self.active=False
            self.backend.stop_preview()

class CooperativePreview:
    def __init__(self,render=None):
        if render is None:
            import ui
            import display
            ui.init()
            render=display.blit_nv12
        self.render=render
        self.decoder_fps='0.00'
        self.frame_status=3
        self.frames=0
    def show(self,frame):
        self.render(frame)
        self.frames+=1
    def set_value(self,status):
        self.frame_status=status

class PreviewStream:
    def __init__(self,source,preview):
        self.source=source
        self.preview=preview
    def start_video_stream_mode(self):self.source.start_video_stream_mode()
    def read_video_stream(self):
        frame=self.source.read_video_stream()
        if frame is not None:self.preview.show(frame)
        return frame
    def stop_video_stream_mode(self):self.source.stop_video_stream_mode()

class NativeScanScreen:
    FRAME__ADDED_PART=1
    FRAME__REPEATED_PART=2
    FRAME__MISS=3
    _run=run_source
    def __init__(self,decoder,instructions_text=None,camera=None,preview=None,buttons=None,clock=None):
        if decoder is None:raise ValueError('ScanScreen requires its original decoder')
        self.decoder=decoder
        self.instructions_text=instructions_text
        self.preview=preview if preview is not None else CooperativePreview()
        self.frames_decode_status=self.preview
        self.camera=PreviewStream(camera if camera is not None else NativeVideoStream(),self.preview)
        self.hw_inputs=buttons if buttons is not None else ButtonInput()
        self.clock=clock if clock is not None else ElapsedClock()
    def run(self):
        self.hw_inputs.reset_input()
        try:
            self.camera.start_video_stream_mode()
            return self._run()
        finally:
            self.camera.stop_video_stream_mode()

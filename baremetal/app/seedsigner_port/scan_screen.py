# SPDX-License-Identifier: MIT
"""Cooperative runtime for the original ScanScreen._run method.

The original completion/invalid/fragment/back loop is source-generated. Sensor,
clock, input and preview ownership live here. Original native instruction/progress
widgets composite with an owned RGB preview; no PIL/OS/thread rendering is used.
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
            self.backend.stop_preview()
            self.active=False

class CooperativePreview:
    def __init__(self,render=None):
        self.render=render
        self.native=render is None
        self.backend=None
        if self.native:
            import ui
            ui.init();self.backend=ui
        self.decoder=None;self.instructions_text=None;self.active=False
        self.decoder_fps='0.00';self.frame_status=3;self.frames=0
    def configure(self,decoder,instructions_text):
        self.decoder=decoder;self.instructions_text=instructions_text
    def begin(self):
        if self.active:raise RuntimeError('Preview already active')
        if self.native:
            from seedsigner_port.localization import gettext as _
            caption='< '+_('back')+'\n'+_(self.instructions_text or 'Scan a QR code')
            self.backend.scan_begin(caption)
        self.active=True
    def _status(self):
        if not self.native or not self.active:return
        percent=self.decoder.get_percent_complete() if self.decoder is not None else 0
        weighted=self.decoder.get_percent_complete(weight_mixed_frames=True) if self.decoder is not None else 0
        self.backend.scan_status(weighted,self.frame_status,percent>0)
    def show(self,frame):
        if self.native:
            if not self.active:raise RuntimeError('Begin preview first')
            self.backend.scan_frame(frame);self._status()
        else:self.render(frame)
        self.frames+=1
    def set_value(self,status):
        self.frame_status=status;self._status()
    def close(self):
        if self.active:
            self.active=False
            if self.native:self.backend.scan_end()

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
        if hasattr(self.preview,'configure'):self.preview.configure(decoder,instructions_text)
        self.frames_decode_status=self.preview
        self.camera=PreviewStream(camera if camera is not None else NativeVideoStream(),self.preview)
        self.hw_inputs=buttons if buttons is not None else ButtonInput()
        self.clock=clock if clock is not None else ElapsedClock()
    def run(self):
        self.hw_inputs.reset_input()
        try:
            if hasattr(self.preview,'begin'):self.preview.begin()
            self.camera.start_video_stream_mode()
            return self._run()
        finally:
            try:self.camera.stop_video_stream_mode()
            finally:
                if hasattr(self.preview,'close'):self.preview.close()

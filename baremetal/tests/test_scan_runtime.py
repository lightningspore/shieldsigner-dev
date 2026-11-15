# SPDX-License-Identifier: MIT
"""Original scan-loop integration and preview ownership across error paths."""
from pathlib import Path
import sys,unittest
sys.path.append(str(Path(__file__).resolve().parents[1]/'app'))
from seedsigner_port.scan_screen import NativeScanScreen,CooperativePreview,NativeVideoStream
from seedsigner_port.decode_qr import DecodeQRStatus as S
class Clock:
 def __init__(self):self.now=0
 def time(self):self.now+=0.1;return self.now
class Buttons:
 def reset_input(self):pass
 def check_for_low(self,key):return False
class Source:
 def __init__(self,fail=None):self.active=False;self.starts=0;self.stops=0;self.fail=fail
 def start_video_stream_mode(self):
    if self.fail=='start':raise RuntimeError('start failed')
    self.active=True;self.starts+=1
 def read_video_stream(self):
    if self.fail=='read':raise RuntimeError('read failed')
    return b'public frame'
 def stop_video_stream_mode(self):
    if self.active:self.active=False;self.stops+=1
    if self.fail=='stop':raise RuntimeError('stop failed')
class Decoder:
 def __init__(self,statuses):self.statuses=iter(statuses)
 def add_image(self,image):return next(self.statuses)
class ScanRuntimeTest(unittest.TestCase):
 def screen(self,source,statuses,render=None):
    preview=CooperativePreview(render=render if render is not None else lambda frame:None)
    screen=NativeScanScreen(decoder=Decoder(statuses),camera=source,preview=preview,buttons=Buttons(),clock=Clock())
    return screen,preview
 def test_original_partial_repeat_complete_lifecycle(self):
    source=Source();frames=[];screen,preview=self.screen(source,[S.PART_COMPLETE,S.PART_EXISTING,S.COMPLETE],frames.append)
    self.assertIsNone(screen.run())
    self.assertEqual(frames,[b'public frame']*3)
    self.assertEqual((source.starts,source.stops,preview.frames,preview.frame_status),(1,1,3,2))
    self.assertFalse(preview.active);self.assertFalse(source.active)
 def test_camera_errors_always_close_preview(self):
    for failure in ('start','read','stop'):
        with self.subTest(failure=failure):
            source=Source(failure);screen,preview=self.screen(source,[S.COMPLETE])
            with self.assertRaisesRegex(RuntimeError,failure+' failed'):screen.run()
            self.assertFalse(preview.active);self.assertFalse(source.active)
 def test_render_error_unwinds_camera_and_preview(self):
    def fail(frame):raise ValueError('render failed')
    source=Source();screen,preview=self.screen(source,[S.COMPLETE],fail)
    with self.assertRaisesRegex(ValueError,'render failed'):screen.run()
    self.assertEqual(source.stops,1);self.assertFalse(preview.active)
 def test_keyboard_interrupt_unwinds_camera_and_preview(self):
    def stop(frame):raise KeyboardInterrupt()
    source=Source();screen,preview=self.screen(source,[S.COMPLETE],stop)
    with self.assertRaises(KeyboardInterrupt):screen.run()
    self.assertEqual(source.stops,1);self.assertFalse(preview.active)

 def test_stream_stop_failure_keeps_ownership_for_retry(self):
    class Backend:
        fail=True
        def init(self):pass
        def start_preview(self):pass
        def stop_preview(self):
            if self.fail:raise RuntimeError('stop not confirmed')
    backend=Backend();stream=NativeVideoStream(backend)
    stream.start_video_stream_mode()
    with self.assertRaisesRegex(RuntimeError,'stop not confirmed'):stream.stop_video_stream_mode()
    self.assertTrue(stream.active)
    backend.fail=False;stream.stop_video_stream_mode();self.assertFalse(stream.active)

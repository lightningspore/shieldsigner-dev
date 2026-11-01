import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from transport import NativeHost
class TransportTests(unittest.TestCase):
    def helper(self,code):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        path=Path(directory.name)/'host'
        path.write_text('#!/usr/bin/env python3\nimport os,struct,time\n'+code)
        path.chmod(0o700)
        return path
    def test_invalid_handshake_fails_and_reaps(self):
        binary=self.helper("os.write(1, b'badmagic')\ntime.sleep(10)\n")
        with self.assertRaises(RuntimeError):NativeHost(binary,lambda *a:None,timeout=1)
    def test_ready_then_invalid_rectangle_poisoned(self):
        code="p=b'{\"event\":\"ready\",\"protocol\":1}';os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(.1)\nos.write(1,b'SL'+bytes([1,1])+struct.pack('<I',10)+struct.pack('<4H',240,0,240,0)+b'xx')\ntime.sleep(10)\n"
        host=NativeHost(self.helper(code),lambda *a:None,timeout=1)
        try:
            with self.assertRaises(RuntimeError):host.next_event(timeout=1)
        finally:host.close()
        self.assertIsNotNone(host.child.poll());self.assertFalse(host.reader.is_alive())
    def test_sink_failure_is_visible_and_reapable(self):
        code="p=b'{\"event\":\"ready\",\"protocol\":1}';os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(.1)\nos.write(1,b'SL'+bytes([1,1])+struct.pack('<I',10)+struct.pack('<4H',0,0,0,0)+b'xx')\ntime.sleep(10)\n"
        def fail(*args):raise OSError('SPI failed')
        host=NativeHost(self.helper(code),fail,timeout=1)
        try:
            with self.assertRaises(RuntimeError):host.next_event(timeout=1)
        finally:host.close()
        self.assertIsInstance(host.error,OSError);self.assertIsNotNone(host.child.poll())
    def test_overlay_state_does_not_displace_acknowledgements(self):
        code="import json\nfor event in [dict(event='ready',protocol=1),dict(event='overlay_changed',screensaver=True),dict(event='screen_ready',request=7)]:\n p=json.dumps(event).encode();os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(10)\n"
        host=NativeHost(self.helper(code),lambda *a:None,timeout=1)
        try:
            self.assertEqual(host.next_event(),dict(event='screen_ready',request=7))
            self.assertTrue(host.screensaver_active)
        finally:host.close()
    def test_request_size_bound(self):
        code="p=b'{\"event\":\"ready\",\"protocol\":1}';os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(10)\n"
        host=NativeHost(self.helper(code),lambda *a:None,timeout=1)
        try:
            with self.assertRaises(ValueError):host.send('screen',config={'text':'x'*(1024*1024)})
        finally:host.close()

class PreviewTransportTests(unittest.TestCase):
    def test_binary_pixels_are_not_interleaved_with_next_json_command(self):
        import io,json,threading
        from types import SimpleNamespace
        host=NativeHost.__new__(NativeHost)
        sink=io.BytesIO();host.child=SimpleNamespace(stdin=sink)
        host._write_lock=threading.Lock();host._closed=False;host.error=None
        pixels=(bytes(range(256))*507)[:129600]
        host.send_preview(240,180,pixels)
        host.send('key',key=20,pressed=True)
        wire=sink.getvalue();header,body=wire.split(b'\n',1)
        self.assertEqual(json.loads(header)['bytes'],129600)
        self.assertEqual(body[:129600],pixels)
        self.assertEqual(json.loads(body[129600:]),dict(op='key',key=20,pressed=True))
    def test_preview_geometry_and_status_bounds_are_checked_before_writing(self):
        import io,threading
        from types import SimpleNamespace
        host=NativeHost.__new__(NativeHost);sink=io.BytesIO();host.child=SimpleNamespace(stdin=sink)
        host._write_lock=threading.Lock();host._closed=False;host.error=None
        for width,height,pixels,percent,status in [(240,180,b'',0,0),(241,180,bytes(129600),0,0),(240.0,180,bytes(129600),0,0),(240,180,bytes(129600),101,0),(240,180,bytes(129600),0,4)]:
            with self.assertRaises(ValueError):host.send_preview(width,height,pixels,percent,status)
        self.assertEqual(sink.getvalue(),b'')

    def test_geometry_rejected_before_process_start(self):
        for width,height in [(128,128),(240,320),(True,240),(321,240)]:
            with self.assertRaises(ValueError):NativeHost('/missing/executable',lambda *args:None,width=width,height=height)

class FrameCompletionTests(unittest.TestCase):
    helper=TransportTests.helper
    def test_frame_completion_callback_does_not_displace_command_ack(self):
        code="import json\nfor event in [dict(event='ready',protocol=1),dict(event='frame_complete'),dict(event='screen_ready',request=9)]:\n p=json.dumps(event).encode();os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(10)\n"
        seen=[];host=NativeHost(self.helper(code),lambda *args:None,frame_sink=lambda:seen.append('frame'))
        try:
            self.assertEqual(host.next_event(),dict(event='screen_ready',request=9));self.assertEqual(seen,['frame'])
        finally:host.close()
    def test_frame_callback_failure_poisoned_client(self):
        code="import json\nfor event in [dict(event='ready',protocol=1),dict(event='frame_complete')]:\n p=json.dumps(event).encode();os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(10)\n"
        def fail():raise OSError('public frame fixture')
        host=None
        try:
            with self.assertRaises(RuntimeError):
                host=NativeHost(self.helper(code),lambda *args:None,frame_sink=fail)
                host.next_event(timeout=1)
        finally:
            if host is not None:host.close()
        if host is not None:self.assertIsInstance(host.error,OSError)

    def test_frame_reset_runs_once_after_process_and_reader_stop(self):
        code="p=b'{\"event\":\"ready\",\"protocol\":1}';os.write(1,b'SL'+bytes([1,2])+struct.pack('<I',len(p))+p)\ntime.sleep(10)\n"
        seen=[]
        def reset():
            self.assertIsNotNone(host.child.poll());self.assertFalse(host.reader.is_alive());seen.append('reset')
        host=NativeHost(self.helper(code),lambda *args:None,frame_reset=reset)
        host.close();host.close();self.assertEqual(seen,['reset'])

if __name__=='__main__':unittest.main()

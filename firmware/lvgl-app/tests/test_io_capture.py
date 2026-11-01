import ast,sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from io_test import compile_capture,CaptureInterrupted,check
class IOCaptureTests(unittest.TestCase):
    def source(self):
        source=(Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/gui/screens/settings_screens.py').read_text()
        cls=next(node for node in ast.parse(source).body if isinstance(node,ast.ClassDef) and node.name=='IOTestScreen')
        method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='_run')
        return ast.get_source_segment(source,method)
    def test_original_profile_order_retry_bound_and_finally_stop(self):
        for success in (False,True):
            calls=[];reads=[];frame=object()
            class Camera:
                def start_video_stream_mode(self,**kwargs):calls.append(kwargs)
                def read_video_stream(self,**kwargs):reads.append(kwargs);return frame if success and len(calls)==2 else None
                def stop_video_stream_mode(self):calls[-1]['stopped']=True
            fn=compile_capture(self.source(),dict(time=SimpleNamespace(sleep=lambda seconds:None),logger=SimpleNamespace(info=lambda *args:None)))
            self.assertIs(fn(Camera()),frame if success else None)
            self.assertEqual([row['resolution'] for row in calls],[(640,480),(480,480)] if success else [(640,480),(480,480),(1280,720),(320,240)])
            self.assertEqual(len(reads),11 if success else 40)
            self.assertTrue(all(row['stopped'] and row['format']=='bgr' for row in calls))
            self.assertTrue(all(row==dict(as_image=True,preview=True) for row in reads))
    def test_wipe_escapes_profile_exception_handler_and_stops_camera(self):
        from lifecycle import WipeInterrupted
        stopped=[];error=WipeInterrupted('public wipe')
        def fail():raise error
        runtime=SimpleNamespace(lifecycle_check=fail)
        camera=SimpleNamespace(start_video_stream_mode=lambda **kwargs:check(runtime),stop_video_stream_mode=lambda:stopped.append(True))
        fn=compile_capture(self.source(),dict(time=SimpleNamespace(sleep=lambda seconds:None),logger=SimpleNamespace(info=lambda *args:self.fail('wipe swallowed'))))
        with self.assertRaises(CaptureInterrupted) as caught:fn(camera)
        self.assertIs(caught.exception.error,error);self.assertEqual(stopped,[True])
    def test_changed_capture_structure_rejected(self):
        with self.assertRaises(ValueError):compile_capture('def _run(self): pass',{})
    def test_profile_start_failure_advances_and_stops_each_profile(self):
        calls=[];stops=[];frame=object();messages=[]
        def start(**kwargs):
            calls.append(kwargs)
            if len(calls)==1:raise OSError('public fixture camera failure')
        camera=SimpleNamespace(start_video_stream_mode=start,read_video_stream=lambda **kwargs:frame,stop_video_stream_mode=lambda:stops.append(True))
        fn=compile_capture(self.source(),dict(time=SimpleNamespace(sleep=lambda seconds:None),logger=SimpleNamespace(info=lambda *args:messages.append(args))))
        self.assertIs(fn(camera),frame);self.assertEqual(len(calls),2);self.assertEqual(len(stops),2);self.assertEqual(len(messages),1)

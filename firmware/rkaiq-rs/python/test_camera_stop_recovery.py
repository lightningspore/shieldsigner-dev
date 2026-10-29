"""Exercise actual pinned Camera start/stop transforms without camera hardware."""
import ast
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from shieldsigner_integration import camera_source


class CameraStopRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[3]/'dist/os/camera-review/pinned-app-src'
        if not root.exists():raise unittest.SkipTest('Pinned public app checkout not staged')
        _,_,source=camera_source(root)
        camera=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='Camera')
        methods=[n for n in camera.body if isinstance(n,ast.FunctionDef) and n.name in ('start_video_stream_mode','stop_video_stream_mode')]
        namespace={}
        exec(compile(ast.Module(body=methods,type_ignores=[]),'actual-patched-camera','exec'),namespace)
        cls.camera_type=type('Camera',(),{**namespace,'_is_luckfox_profile':staticmethod(lambda profile:True)})

    def camera(self, stream):
        camera=self.camera_type()
        camera._video_stream=stream
        camera._hardware_camera_config={}
        camera._runtime_profile='luckfox_22'
        camera._camera_index=0
        return camera

    def test_failed_stop_detaches_exact_stream_preserves_exception_and_reopens(self):
        error=RuntimeError('original owner failure')
        class Failed:
            def stop(self):raise error
        camera=self.camera(Failed())
        with self.assertRaises(RuntimeError) as raised:camera.stop_video_stream_mode()
        self.assertIs(raised.exception,error)
        self.assertIsNone(camera._video_stream)
        calls=[]
        class Fresh:
            def __init__(self,**kwargs):calls.append('new')
            def start(self):calls.append('start')
        module=types.ModuleType('shieldsigner_camera_compat');module.VideoStream=Fresh
        with patch.dict(sys.modules,{'shieldsigner_camera_compat':module}):camera.start_video_stream_mode()
        self.assertEqual(calls,['new','start'])
        self.assertIsInstance(camera._video_stream,Fresh)

    def test_normal_stop_and_empty_stop_remain_idempotent(self):
        calls=[]
        camera=self.camera(types.SimpleNamespace(stop=lambda:calls.append('stop')))
        camera.stop_video_stream_mode();camera.stop_video_stream_mode()
        self.assertEqual(calls,['stop'])
        self.assertIsNone(camera._video_stream)

    def test_old_stop_cannot_detach_a_replacement_stream(self):
        replacement=object()
        camera=self.camera(None)
        def stop():camera._video_stream=replacement
        camera._video_stream=types.SimpleNamespace(stop=stop)
        camera.stop_video_stream_mode()
        self.assertIs(camera._video_stream,replacement)

    def test_failed_stop_does_not_start_another_owner_and_busy_start_still_propagates(self):
        class Failed:
            def stop(self):raise RuntimeError('stop failed')
        camera=self.camera(Failed());calls=[]
        class Guarded:
            def __init__(self,**kwargs):calls.append('construct')
            def start(self):raise RuntimeError('existing native owner lock held')
        module=types.ModuleType('shieldsigner_camera_compat');module.VideoStream=Guarded
        with patch.dict(sys.modules,{'shieldsigner_camera_compat':module}):
            with self.assertRaisesRegex(RuntimeError,'stop failed'):camera.start_video_stream_mode()
            self.assertEqual(calls,[])  # that failed attempt never launches a replacement
            with self.assertRaisesRegex(RuntimeError,'owner lock held'):camera.start_video_stream_mode()
        self.assertIsNone(camera._video_stream)
        self.assertEqual(calls,['construct'])

if __name__=='__main__':unittest.main()

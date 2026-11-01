import os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from entropy_camera import start
class EntropyCameraTests(unittest.TestCase):
    def test_explicit_config_and_environment_restored_on_success_and_failure(self):
        with tempfile.NamedTemporaryFile() as config:
            for fail in (False,True):
                def launch():
                    self.assertEqual(os.environ['SHIELDSIGNER_FRONTEND_BACKEND'],'rust')
                    self.assertEqual(os.environ['SHIELDSIGNER_CAMERA_CONFIG'],config.name)
                    if fail:raise RuntimeError('fixture startup failure')
                    return 'started'
                with patch.dict(os.environ,{'SHIELDSIGNER_FRONTEND_BACKEND':'python','SHIELDSIGNER_CAMERA_CONFIG':config.name}):
                    if fail:
                        with self.assertRaises(RuntimeError):start(SimpleNamespace(start_video_stream_mode=launch))
                    else:self.assertEqual(start(SimpleNamespace(start_video_stream_mode=launch)),'started')
                    self.assertEqual(os.environ['SHIELDSIGNER_FRONTEND_BACKEND'],'python')
                    self.assertEqual(os.environ['SHIELDSIGNER_CAMERA_CONFIG'],config.name)
    def test_missing_config_fails_before_start(self):
        with patch.dict(os.environ,{'SHIELDSIGNER_CAMERA_CONFIG':'/missing-public-fixture.json'}):
            with self.assertRaises(ValueError):start(SimpleNamespace(start_video_stream_mode=lambda:self.fail('started without owner config')))

    def test_pairing_reuses_preview_frame_and_empty_preview_does_not_steal_next(self):
        from experimental_entropy_samples import _enable_pairing,_sample_native_frame,release_pair
        class Stream:
            transport='nv12'
            def _prepare(self,frame,preview=False,display=False,rotation=0):return frame
        stream=Stream();camera=SimpleNamespace(_video_stream=stream)
        _enable_pairing(camera)
        public=object();self.assertIs(stream._prepare(public,True),public)
        self.assertIs(_sample_native_frame(camera),public)
        self.assertIsNone(camera._lvgl_pair_frame)
        stream._prepare(None,True)
        self.assertIsNone(_sample_native_frame(camera))
        self.assertEqual(camera._lvgl_pair_hits,1);self.assertEqual(camera._lvgl_pair_misses,1)
        # A final/display read does not fill the preview/sample cache.
        stream._prepare(public,False,True)
        self.assertFalse(camera._lvgl_pair_ready)
        release_pair(camera);self.assertNotIn('_prepare',vars(stream))
        self.assertIsNone(camera._lvgl_pair_stream)

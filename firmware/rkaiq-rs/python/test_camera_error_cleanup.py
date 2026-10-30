import hashlib
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from shieldsigner_integration import install_camera_error_cleanup

class ErrorCleanupTests(unittest.TestCase):
 def test_cleanup_before_error_destination_and_primary_error_preserved(self):
  for fail in (False,True):
   with self.subTest(cleanupFails=fail),tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'seedsigner/controller.py';path.parent.mkdir();path.write_text('# fixture')
    calls=[];failure=ValueError('original')
    class Controller:
     def handle_exception(self,error):calls.append(('handler',error));return 'error-screen'
    class Camera:
     _video_stream=object()
     def stop_video_stream_mode(self):
      calls.append(('stop',None));self._video_stream=None
      if fail:raise RuntimeError('cleanup')
    module=types.SimpleNamespace(__file__=str(path),Controller=Controller)
    camera=types.SimpleNamespace(Camera=types.SimpleNamespace(_instance=Camera()))
    with patch('shieldsigner_integration.SMALL_RAM_CONTROLLER_SHA256',hashlib.sha256(path.read_bytes()).hexdigest()),patch('shieldsigner_integration.importlib.import_module',return_value=module):
     install_camera_error_cleanup(directory,camera);install_camera_error_cleanup(directory,camera)
     self.assertEqual(Controller().handle_exception(failure),'error-screen')
    self.assertEqual(calls,[('stop',None),('handler',failure)])

if __name__=='__main__':unittest.main()

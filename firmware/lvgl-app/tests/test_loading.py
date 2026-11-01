import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from loading import install
class LoadingTests(unittest.TestCase):
    def test_native_lifecycle_and_context_manager_preserve_class(self):
        class Loader:
            def __init__(self,text):self.text=text
            def start(self):raise AssertionError('PIL thread started')
            def stop(self):raise AssertionError('PIL thread stopped')
            def is_alive(self):return False
            def join(self,timeout=None):pass
            def __enter__(self):self.start();return self
            def __exit__(self,*args):self.stop()
        original=Loader.start;calls=[]
        runtime=SimpleNamespace(show_loading=lambda text:calls.append(('start',text)) or 7,hide_loading=lambda token:calls.append(('stop',token)))
        restore=install(runtime,Loader)
        try:
            with Loader('Signing') as loader:self.assertTrue(loader.is_alive());self.assertTrue(loader.keep_running)
            self.assertFalse(loader.is_alive());self.assertFalse(loader.keep_running)
            loader.join(timeout=.01);loader.stop()
            self.assertEqual(calls,[('start','Signing'),('stop',7)])
            with self.assertRaises(RuntimeError):loader.start()
        finally:restore()
        self.assertIs(Loader.start,original)
    def test_start_failure_does_not_leave_indicator_alive(self):
        class Loader:
            def __init__(self):self.text='Test'
        def fail(text):raise OSError('display unavailable')
        restore=install(SimpleNamespace(show_loading=fail),Loader)
        try:
            loader=Loader()
            with self.assertRaises(OSError):loader.start()
            self.assertFalse(loader.is_alive());self.assertFalse(loader.keep_running)
        finally:restore()
if __name__=='__main__':unittest.main()

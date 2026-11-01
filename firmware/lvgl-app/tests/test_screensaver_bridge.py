import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from screensaver_bridge import install
class ScreensaverTests(unittest.TestCase):
    def test_facade_observes_current_host_after_restart_and_restores(self):
        calls=[];previous=object()
        runtime=SimpleNamespace(host=SimpleNamespace(screensaver_active=False,send=lambda op:calls.append(op)),configure_screensaver=lambda ms:calls.append(ms))
        controller=SimpleNamespace(screensaver=previous,screensaver_activation_ms=120000,reset_screensaver_timeout=lambda:calls.append("reset"))
        restore=install(runtime,controller)
        try:
            controller.reset_screensaver_timeout()
            self.assertFalse(controller.screensaver.is_running)
            controller.screensaver.start()
            runtime.host=SimpleNamespace(screensaver_active=True,send=lambda op:calls.append(op))
            self.assertTrue(controller.screensaver.is_running)
            controller.screensaver.stop()
        finally:restore()
        self.assertIs(controller.screensaver,previous)
        self.assertEqual(calls,[120000,'reset','activity','screensaver_show','screensaver_dismiss',0])

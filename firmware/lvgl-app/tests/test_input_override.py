import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from runtime import Runtime
class InputOverrideTests(unittest.TestCase):
    def test_new_native_screen_consumes_legacy_toast_wakeup(self):
        hardware=SimpleNamespace(override_ind=True)
        runtime=Runtime.__new__(Runtime);runtime.low_since={'KEY1':1};runtime.current=49
        runtime.consume_input_override=lambda:setattr(hardware,'override_ind',False)
        runtime.reset_input()
        self.assertFalse(hardware.override_ind);self.assertIsNone(runtime.current)
        self.assertTrue(runtime.waiting_release);self.assertEqual(runtime.low_since,{})

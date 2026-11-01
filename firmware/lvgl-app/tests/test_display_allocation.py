import sys,threading,unittest
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from luckfox import LuckfoxHardware

class DisplayAllocationTests(unittest.TestCase):
    def test_scaler_allocation_failure_closes_new_driver_and_drops_old_state(self):
        events=[]
        class Driver:
            def __init__(self,*args):events.append('new')
            def _ensure_initialized(self):events.append('init')
            def set_color_inversion(self,value):events.append('invert')
            def close(self):events.append('new-close')
        module=ModuleType('seedsigner.hardware.displays.ST7735');module.ST7735=Driver
        hardware=LuckfoxHardware.__new__(LuckfoxHardware)
        hardware.lock=threading.Lock();hardware.buttons=None
        hardware.lcd=SimpleNamespace(width=240,height=240,close=lambda:events.append('old-close'))
        hardware.scaler=SimpleNamespace(wipe=lambda:events.append('wipe'))
        with patch.dict(sys.modules,{module.__name__:module}),patch('display_scaler.FrameScaler',side_effect=MemoryError('fixture')):
            with self.assertRaises(MemoryError):hardware.configure_display(128,128,False)
        self.assertEqual(events,['wipe','old-close','new','init','invert','new-close'])
        self.assertIsNone(hardware.lcd);self.assertIsNone(hardware.scaler)
        hardware.close()  # Failed acquisition remains safe to unwind.

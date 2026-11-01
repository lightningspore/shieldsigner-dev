import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from home_battery import sample
class HomeBatteryTests(unittest.TestCase):
    def test_disabled_or_absent_never_reads_sensor(self):
        for enabled,detected in [(False,False),(False,True),(True,False)]:
            hat=SimpleNamespace(is_enabled=lambda:enabled,detected=detected)
            self.assertEqual(sample(hat),dict(visible=False) if enabled else None)
    def test_original_truncation_unknown_and_charge_sign(self):
        for percent,current,expected in [(49.9,1,(49,True)),(None,None,(None,False)),(0,0,(0,False)),(99.9,-1,(99,False))]:
            hat=SimpleNamespace(is_enabled=lambda:True,detected=True,get_percent=lambda:percent,get_current=lambda:current)
            self.assertEqual(sample(hat),dict(visible=True,percent=expected[0],charging=expected[1]))

    def test_lost_sensor_preserves_visible_unknown_and_disabled_skips_updates(self):
        hat=SimpleNamespace(is_enabled=lambda:True,detected=False)
        self.assertEqual(sample(hat,shown=True),dict(visible=True,percent=None,charging=False))
        hat.is_enabled=lambda:False
        self.assertIsNone(sample(hat,shown=True))

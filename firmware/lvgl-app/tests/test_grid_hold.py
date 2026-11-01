import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from grid_hold import Hold
class GridHoldTests(unittest.TestCase):
    def test_short_hold_selects_only_on_release(self):
        h=Hold(51,5000,1003)
        self.assertEqual(h.poll(51,None,0),(None,None,None,True))
        self.assertEqual(h.poll(51,None,4.99),(None,None,None,True))
        self.assertEqual(h.poll(None,None,5),(None,51,None,False))
        self.assertEqual(h.poll(None,None,6),(None,None,None,False))
    def test_threshold_returns_original_code_without_tap(self):
        h=Hold(51,5000,1003);h.poll(51,None,1)
        self.assertEqual(h.poll(51,None,6),(None,None,1003,True))
    def test_other_keys_pass_and_hold_blocks_simultaneous_selection(self):
        h=Hold(51,5000,1003)
        self.assertEqual(h.poll(19,None,0),(19,None,None,False))
        h.poll(51,None,1)
        self.assertEqual(h.poll(10,None,2),(None,51,None,False))
    def test_invalid_contract_rejects(self):
        for ms,ret in [(0,1003),(True,1003),(5000,None)]:
            with self.assertRaises(ValueError):Hold(51,ms,ret)

    def test_wake_hold_passes_to_native_without_becoming_loader_action(self):
        h=Hold(51,5000,1003)
        self.assertEqual(h.poll(51,None,0,wake=True),(51,None,None,False))
        self.assertEqual(h.poll(51,None,6),(51,None,None,False))
        self.assertEqual(h.poll(None,None,7),(None,None,None,False))
        self.assertEqual(h.poll(51,None,8),(None,None,None,True))
        self.assertEqual(h.poll(51,None,13),(None,None,1003,True))

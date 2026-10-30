import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('button_control',Path(__file__).resolve().parents[2]/'firmware/bench-profiles/button_control.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ButtonTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.now=1.;self.c=m.ButtonControl(Path(self.tmp.name)/'session',clock=lambda:self.now)
 def tearDown(self):self.tmp.cleanup()
 def request(self,**changes):
  data={'key':'KEY_LEFT','holdMs':120,'id':'once'};data.update(changes);(self.c.directory/'request.json').write_text(json.dumps(data))
 def test_press_release_and_no_replay(self):
  self.request();self.assertTrue(self.c.pressed('KEY_LEFT'));self.assertFalse(self.c.pressed('KEY_PRESS'));self.now+=.2;self.assertFalse(self.c.pressed('KEY_LEFT'));self.request();self.now+=.1;self.assertFalse(self.c.pressed('KEY_LEFT'))
 def test_physical_input_preserved(self):
  class Pin:
   level=False
   def read(self):return self.level
  pin=Pin();overlay=m.PinOverlay(pin,'KEY_LEFT',self.c);self.assertFalse(overlay.read());pin.level=True;self.assertTrue(overlay.read());self.request();self.now+=.1;self.assertFalse(overlay.read());self.now+=.2;self.assertTrue(overlay.read())
 def test_unknown_keys_and_unbounded_hold_rejected(self):
  for change in [{'key':'GPIO42'},{'holdMs':999999},{'holdMs':True},{'id':'$(secret)'}]:
   self.request(**change);self.now+=.1;self.assertFalse(self.c.pressed('KEY_LEFT'));self.assertEqual(json.loads((self.c.directory/'status.json').read_text())['state'],'rejected')
if __name__=='__main__':unittest.main()

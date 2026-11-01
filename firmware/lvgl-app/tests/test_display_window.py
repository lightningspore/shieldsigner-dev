import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from luckfox import set_window
class DisplayWindowTests(unittest.TestCase):
 def display(self,width=320,height=240):
  calls=[];parameters=[]
  def transfer(data):
   parameters.append(bytes(data));calls.extend(('data',value) for value in data)
  return SimpleNamespace(width=width,height=height,command=lambda value:calls.append(('command',value)),_dc=SimpleNamespace(write=lambda value:self.assertTrue(value)),_chunked_transfer=transfer,parameters=parameters),calls
 def test_wide_partial_rectangle_preserves_high_coordinate_bytes(self):
  display,calls=self.display();set_window(display,(250,10,319,29))
  self.assertEqual(calls,[('command',0x2a),('data',0),('data',250),('data',1),('data',63),('command',0x2b),('data',0),('data',10),('data',0),('data',29),('command',0x2c)])
  self.assertEqual(display.parameters,[bytes((0,250,1,63)),bytes((0,10,0,29))])
 def test_default_240_window_matches_original_byte_sequence(self):
  display,calls=self.display(240,240);set_window(display,(0,0,239,239))
  self.assertEqual(calls,[('command',0x2a),('data',0),('data',0),('data',0),('data',239),('command',0x2b),('data',0),('data',0),('data',0),('data',239),('command',0x2c)])
 def test_invalid_rectangles_write_nothing(self):
  for area in [(-1,0,1,1),(0,0,320,1),(3,0,2,1),(0,0,1,240),(False,0,1,1)]:
   display,calls=self.display()
   with self.assertRaises(ValueError):set_window(display,area)
   self.assertEqual(calls,[])

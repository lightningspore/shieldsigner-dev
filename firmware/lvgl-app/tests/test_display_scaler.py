import sys,unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from display_scaler import FrameScaler
class DisplayScalerTests(unittest.TestCase):
 def test_partial_updates_match_full_canvas_lanczos_and_clean_completion_skips(self):
  scaler=FrameScaler();self.assertIsNone(scaler.complete())
  scaler.update((0,0,239,119),b'\xf8\x00'*(240*120))
  scaler.update((0,120,239,239),b'\x00\x1f'*(240*120))
  reference=Image.new('RGB',(240,240),'red');reference.paste((0,0,255),(0,120,240,240))
  expected=reference.resize((128,128),Image.Resampling.LANCZOS);actual=scaler.complete()
  try:self.assertEqual(actual.tobytes(),expected.tobytes())
  finally:actual.close();expected.close();reference.close()
  self.assertIsNone(scaler.complete())
 def test_incremental_patch_preserves_unmodified_canvas(self):
  scaler=FrameScaler();scaler.update((0,0,239,239),b'\xf8\x00'*(240*240));image=scaler.complete();image.close()
  scaler.update((80,80,159,159),b'\x07\xe0'*(80*80));image=scaler.complete()
  try:
   self.assertEqual(image.getpixel((0,0)),(255,0,0));self.assertEqual(image.getpixel((64,64)),(0,255,0))
  finally:image.close()
 def test_wipe_zeroes_retained_buffer_in_place(self):
  scaler=FrameScaler();buffer=scaler.buffer;scaler.update((0,0,0,0),b'\xff\xff');scaler.wipe()
  self.assertIs(buffer,scaler.buffer);self.assertFalse(any(buffer));self.assertIsNone(scaler.complete())
 def test_invalid_updates_leave_canvas_unchanged(self):
  scaler=FrameScaler()
  for area,raw in [((0,0,240,0),b''),((0,0,0,0),b''),((-1,0,0,0),b'\0'*4)]:
   with self.assertRaises(ValueError):scaler.update(area,raw)
   self.assertFalse(any(scaler.buffer));self.assertFalse(scaler.dirty)

# SPDX-License-Identifier: MIT
"""Snapshot integrity checks prevent assembling different captures into one image."""
import hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'tools'))
from decode_camera_luma import decode_snapshot
class LumaSnapshotTest(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
  self.root=Path(self.folder.name)
  self.pixels=b''.join(bytes([y%256])*640 for y in range(480))
  self.digest=hashlib.sha256(self.pixels).hexdigest()
 def chunk(self,name,start,end,digest=True,pixels=None):
  pixels=self.pixels if pixels is None else pixels
  identity=self.digest if digest is True else digest
  header='@@LUMA_BEGIN 640 480'+(' SHA256 '+identity if identity else '')+'\n'
  path=self.root/name
  path.write_text(header+''.join('@@LUMA '+str(y)+' '+pixels[y*640:(y+1)*640].hex()+'\n' for y in range(start,end))+'@@LUMA_END\n')
  return path
 def test_chunk_order_and_matching_overlap_are_supported(self):
  chunks=[self.chunk('tail',200,480),self.chunk('head',0,240)]
  self.assertEqual(decode_snapshot(chunks,True),(self.pixels,self.digest))
 def test_different_snapshot_ids_are_rejected_even_without_overlapping_rows(self):
  chunks=[self.chunk('a',0,240),self.chunk('b',240,480,'0'*64)]
  with self.assertRaisesRegex(ValueError,'different snapshots'):decode_snapshot(chunks,True)
 def test_matching_header_cannot_hide_corrupt_pixel_data(self):
  changed=bytearray(self.pixels);changed[-1]^=1
  with self.assertRaisesRegex(ValueError,'checksum mismatch'):
   decode_snapshot([self.chunk('bad',0,480,pixels=changed)],True)
 def test_missing_rows_are_not_saved_as_a_complete_image(self):
  with self.assertRaisesRegex(ValueError,'Incomplete snapshot'):decode_snapshot([self.chunk('partial',0,479)],True)
 def test_conflicting_overlap_is_rejected(self):
  changed=bytearray(self.pixels);changed[240*640]^=1
  with self.assertRaisesRegex(ValueError,'Conflicting snapshots'):
   decode_snapshot([self.chunk('a',0,241),self.chunk('b',240,480,pixels=changed)],True)
 def test_legacy_exports_require_explicitly_unverified_mode(self):
  path=self.chunk('legacy',0,480,digest=None)
  self.assertEqual(decode_snapshot([path]),(self.pixels,None))
  with self.assertRaisesRegex(ValueError,'checksum required'):decode_snapshot([path],True)
 def test_hashed_and_legacy_chunks_cannot_mix(self):
  with self.assertRaisesRegex(ValueError,'Cannot mix'):
   decode_snapshot([self.chunk('a',0,240),self.chunk('b',240,480,None)])
 def test_out_of_range_row_rejected(self):
  path=self.chunk('a',0,480)
  path.write_text(path.read_text()+'@@LUMA 480 '+'00'*640+'\n')
  with self.assertRaisesRegex(ValueError,'outside snapshot'):decode_snapshot([path],True)

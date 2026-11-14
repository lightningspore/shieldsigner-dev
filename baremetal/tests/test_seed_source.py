# SPDX-License-Identifier: MIT
"""Original Seed source/class coverage, without pretending native memory runs on host."""
import ast,hashlib,json,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
class SeedSourceTests(unittest.TestCase):
 def test_original_class_and_method_coverage(self):
  original=(root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models/seed.py').read_bytes()
  receipt=json.loads((root/'app/seed-provenance.json').read_text())
  self.assertEqual(hashlib.sha256(original).hexdigest(),receipt['sourceSha256'])
  output=(root/'app/seedsigner_port/seed.py').read_bytes()
  self.assertEqual(hashlib.sha256(output).hexdigest(),receipt['outputSha256'])
  def methods(raw):return {n.name:[m.name for m in n.body if isinstance(m,ast.FunctionDef)] for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)}
  self.assertEqual(methods(original),methods(output))
  self.assertEqual(set(methods(original)),set(receipt['classes']))

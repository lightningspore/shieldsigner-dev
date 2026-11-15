# SPDX-License-Identifier: MIT
import ast,bisect,hashlib,json,re,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.append(str(root/'app'))
from seedsigner_port import qr_bisect,qr_regex,qr_strings
class QrExportTests(unittest.TestCase):
 def test_original_encoder_coverage_and_generated_hashes(self):
  receipt=json.loads((root/'app/encode-qr-provenance.json').read_text())
  source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models/encode_qr.py'
  raw=source.read_bytes();out=(root/'app/seedsigner_port/encode_qr.py').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),receipt['sourceSha256'])
  self.assertEqual(hashlib.sha256(out).hexdigest(),receipt['outputSha256'])
  original={n.name:n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)}
  actual={n.body[0].name:n.body[0] for n in ast.parse(out).body if isinstance(n,ast.FunctionDef) and n.name.startswith('_make_')}
  self.assertEqual(set(original),set(actual))
  for name,node in original.items():
   self.assertLessEqual({n.name for n in node.body if isinstance(n,ast.FunctionDef)},{n.name for n in actual[name].body if isinstance(n,ast.FunctionDef)})
  for name,entry in json.loads((root/'app/qrcode-provenance.json').read_text())['files'].items():
   self.assertEqual(hashlib.sha256((root/'app/qrcode'/name).read_bytes()).hexdigest(),entry['outputSha256'])
 def test_boundary_adapters_against_cpython(self):
  for values in ([],[0],[1,1,2,4,9],list(range(50))):
   for value in range(-1,52):
    self.assertEqual(qr_bisect.bisect_left(values,value),bisect.bisect_left(values,value))
  for value in ('','0','10101','+101','-101'):
   for width in range(-2,20):self.assertEqual(qr_strings.zfill(value,width),value.zfill(width))
  data=bytes(range(256));self.assertEqual(qr_regex.escape(data),re.escape(data))
  for subject in (b'ABC',b'ABC\n',b'ABC\0',b''):
   pattern=b'^[A-Z]*\\Z'
   self.assertEqual(qr_regex.compile(pattern).match(subject) is not None,re.match(pattern,subject) is not None)

# SPDX-License-Identifier: MIT
import ast,hashlib,json,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
class MnemonicSources(unittest.TestCase):
 def test_shamir_archive_and_all_outputs(self):
  p=json.loads((root/'app/shamir-provenance.json').read_text())
  self.assertEqual(p['archiveSha256'],'6fdcfb8d4380a8427ba28805eea63511a793fdfc6732d5c44d0f91a6b273445b')
  self.assertEqual(p['wordlistSha256'],'bcc4555340332d169718aed8bf31dd9d5248cb7da6e5d355140ef4f1e601eec3')
  for name,item in p['files'].items():
   self.assertEqual(hashlib.sha256((root/'app/shamir_mnemonic'/(name+'.py')).read_bytes()).hexdigest(),item['outputSha256'])
  self.assertEqual(len(json.loads((root/'app/shamir-vectors.json').read_text())),45)
 def test_whole_aezeed_function_coverage(self):
  raw=(root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models/aezeed.py').read_bytes()
  output=(root/'app/seedsigner_port/aezeed.py').read_bytes()
  receipt=json.loads((root/'app/aezeed-provenance.json').read_text())
  self.assertEqual(hashlib.sha256(raw).hexdigest(),receipt['sourceSha256'])
  self.assertEqual(hashlib.sha256(output).hexdigest(),receipt['outputSha256'])
  def names(raw):return [n.name for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and n.name not in ('__setattr__','__delattr__','__eq__','__ne__','__hash__')]
  self.assertEqual(names(raw),names(output))

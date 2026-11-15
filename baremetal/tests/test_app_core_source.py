# SPDX-License-Identifier: MIT
import ast,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
class AppCoreSources(unittest.TestCase):
 def test_provenance_and_whole_storage_methods(self):
  receipt=json.loads((root/'app/app-core-provenance.json').read_text())
  source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner'
  for name,item in receipt['files'].items():
   self.assertEqual(hashlib.sha256((source/item['source']).read_bytes()).hexdigest(),item['sourceSha256'])
   self.assertEqual(hashlib.sha256((root/'app/seedsigner_port'/name).read_bytes()).hexdigest(),item['outputSha256'])
  for name,cls in [('seed_storage.py','SeedStorage'),('encrypted_storage.py','EncryptedQRStorage')]:
   original=ast.parse((source/receipt['files'][name]['source']).read_text())
   port=ast.parse((root/'app/seedsigner_port'/name).read_text())
   methods=lambda tree:[n.name for c in tree.body if isinstance(c,ast.ClassDef) and c.name==cls for n in c.body if isinstance(n,ast.FunctionDef)]
   self.assertEqual(methods(original),methods(port))
 def test_transform_preserves_local_import_binding(self):
  spec=importlib.util.spec_from_file_location('source_port',root/'tools/source_port.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  tree=ast.parse('from first import x\ndef f():\n from second import x\n return x\ndef g():\n return x\n')
  port=module.Port(tree,'example.module')
  output=ast.unparse(ast.fix_missing_locations(ast.Module(body=[port.visit(n) for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])))
  calls=[]
  namespace={'_dependency':lambda package,name:calls.append((package,name)) or package}
  exec(output,namespace)
  self.assertEqual(namespace['f'](),'second')
  self.assertEqual(namespace['g'](),'first')
  self.assertEqual(calls,[('second','x'),('first','x')])
 def test_clock_uses_actual_available_millisecond_api_and_unwraps(self):
  import types
  ticks=iter([0xfffffff0,0xfffffff8,0x00000010])
  calls=[]
  fake=types.ModuleType('time');fake.ticks_ms=lambda:next(ticks);fake.sleep_ms=calls.append
  saved=sys.modules.get('time');sys.modules['time']=fake
  try:
   spec=importlib.util.spec_from_file_location('app_clock',root/'app/seedsigner_port/clock.py')
   module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  finally:
   if saved is None:sys.modules.pop('time',None)
   else:sys.modules['time']=saved
  self.assertEqual(module.time(),0xfffffff8/1000)
  self.assertEqual(module.time(),0x100000010/1000)
  module.sleep(.125)
  self.assertEqual(calls,[125])
  with self.assertRaises(ValueError):module.sleep(-1)

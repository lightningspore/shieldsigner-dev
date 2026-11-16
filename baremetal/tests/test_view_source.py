# SPDX-License-Identifier: MIT
import ast,hashlib,json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.append(str(root/'tools'))
from view_source_port import LazyPort
class ViewSourceTest(unittest.TestCase):
 def test_original_classes_methods_and_receipts(self):
  receipt=json.loads((root/'app/views-provenance.json').read_text())
  source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner'
  for name,item in receipt['files'].items():
   raw=(source/item['source']).read_bytes();out=(root/'app/seedsigner_port'/name).read_bytes()
   self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sourceSha256'])
   self.assertEqual(hashlib.sha256(out).hexdigest(),item['outputSha256'])
   original={n.name:n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)}
   actual={n.body[0].name:n.body[0] for n in ast.parse(out).body if isinstance(n,ast.FunctionDef) and n.name.startswith('_make_')}
   self.assertEqual(set(actual),set(item['classes']))
   for cls in item['classes']:
    methods=lambda n:{x.name for x in n.body if isinstance(x,ast.FunctionDef)}
    self.assertTrue(methods(original[cls])<=methods(actual[cls]),cls)
  item=json.loads((root/'app/controller-provenance.json').read_text())
  self.assertEqual(hashlib.sha256((source/'controller.py').read_bytes()).hexdigest(),item['sourceSha256'])
  self.assertEqual(hashlib.sha256((root/'app/seedsigner_port/controller.py').read_bytes()).hexdigest(),item['outputSha256'])
 def test_lazy_imports_do_not_resolve_unused_features(self):
  tree=ast.parse('from optional import Top\ndef f(flag):\n from optional import Local\n if flag:return Local\n return 7\ndef g():return Top\n')
  port=LazyPort(tree,'example.module')
  code=ast.fix_missing_locations(ast.Module(body=[port.visit(n) for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]))
  calls=[];scope={'_dependency':lambda module,name:calls.append((module,name)) or name}
  exec(compile(code,'<lazy source>','exec'),scope)
  self.assertEqual(scope['f'](False),7);self.assertEqual(calls,[])
  self.assertEqual(scope['f'](True),'Local');self.assertEqual(scope['g'](),'Top')
  self.assertEqual(calls,[('optional','Local'),('optional','Top')])
 def test_fstring_conversion_preserves_original_output_and_evaluation_order(self):
  text='def f(x):return f"quoted {x[\"value\"]!r} {x[\"number\"]:08x} {{literal}}"'
  original={};exec(text,original)
  tree=ast.parse(text);port=LazyPort(tree,'example.module')
  node=ast.fix_missing_locations(port.visit(tree));actual={};exec(compile(node,'<native format>','exec'),actual)
  data={'value':'é"abc','number':31}
  self.assertEqual(actual['f'](data),original['f'](data))

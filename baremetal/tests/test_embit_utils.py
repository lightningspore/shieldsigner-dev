# SPDX-License-Identifier: MIT
import ast,hashlib,json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.append(str(root/'app'))
from seedsigner_port import embit_utils
from seedsigner_port.settings_schema import SettingsConstants as C
class HelperTest(unittest.TestCase):
 def test_original_helper_function_coverage_and_hashes(self):
    raw=(root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/helpers/embit_utils.py').read_bytes()
    out=(root/'app/seedsigner_port/embit_utils.py').read_bytes();r=json.loads((root/'app/embit-utils-provenance.json').read_text())
    self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sourceSha256']);self.assertEqual(hashlib.sha256(out).hexdigest(),r['outputSha256'])
    functions=lambda data:{n.name for n in ast.parse(data).body if isinstance(n,ast.FunctionDef)}
    self.assertEqual(functions(raw),functions(out));self.assertEqual(functions(out),set(r['functions']))
 def test_original_standard_derivation_paths_and_errors(self):
    raw=(root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/helpers/embit_utils.py').read_text()
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='get_standard_derivation_path')
    scope={'SettingsConstants':C};exec(compile(ast.Module(body=[node],type_ignores=[]),'<original path helper>','exec'),scope)
    for network in (C.MAINNET,C.TESTNET,C.REGTEST,'invalid'):
     for sig in (C.SINGLE_SIG,C.MULTISIG,'invalid'):
      for kind in (C.LEGACY_P2PKH,C.NESTED_SEGWIT,C.NATIVE_SEGWIT,C.TAPROOT,'invalid'):
       for account in (0,7,2**31-1):
        args=(network,sig,kind,account)
        try:expected=scope['get_standard_derivation_path'](*args)
        except Exception as error:
         with self.assertRaises(type(error)) as actual:embit_utils.get_standard_derivation_path(*args)
         self.assertEqual(str(actual.exception),str(error))
        else:self.assertEqual(embit_utils.get_standard_derivation_path(*args),expected)
 def test_static_xpub_materialized_methods_preserve_original_bodies(self):
    original=ast.parse((root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models/encode_qr.py').read_text())
    base=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='BaseStaticQrEncoder')
    actual=ast.parse((root/'app/seedsigner_port/encode_qr.py').read_text())
    cls=next(n.body[0] for n in actual.body if isinstance(n,ast.FunctionDef) and n.name=='_make_StaticXpubQrEncoder')
    for name in ('cur_part','seq_len','is_complete'):
     a=next(n for n in base.body if isinstance(n,ast.FunctionDef) and n.name==name)
     b=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
     a.returns=None # Annotation removal is the shared reviewed port transform.
     self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))

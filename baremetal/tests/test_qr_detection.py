# SPDX-License-Identifier: MIT
import ast, hashlib, json, sys, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root / 'app'))
from seedsigner_port import base43


class DetectionSourceTest(unittest.TestCase):
    def test_original_class_methods_and_function_coverage(self):
        receipt = json.loads((root / 'app/qr-detection-provenance.json').read_text())
        source = root.parent / 'dist/firmware/sources/lvgl/application/src/seedsigner'
        for name, entry in receipt['files'].items():
            raw = (source / entry['source']).read_bytes()
            out = (root / 'app/seedsigner_port' / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sourceSha256'])
            self.assertEqual(hashlib.sha256(out).hexdigest(), entry['outputSha256'])
            original = ast.parse(raw)
            actual = ast.parse(out)
            self.assertEqual(
                {n.name for n in original.body if isinstance(n, ast.FunctionDef)},
                {n.name for n in actual.body if isinstance(n, ast.FunctionDef)},
            )
            a = {n.name: n for n in actual.body if isinstance(n, ast.ClassDef)}
            for c in [n for n in original.body if isinstance(n, ast.ClassDef)]:
                self.assertEqual(
                    {n.name for n in c.body if isinstance(n, ast.FunctionDef)},
                    {n.name for n in a[c.name].body if isinstance(n, ast.FunctionDef)},
                )

    def test_base43_against_unmodified_original(self):
        source = (
            root.parent / 'dist/firmware/sources/lvgl/application/src/seedsigner/helpers/base43.py'
        )
        scope = {}
        exec(compile(source.read_text(), '<original base43>', 'exec'), scope)
        vectors = [b'', bytes(range(256)), b'\0' * 16, b'\0\0public'] + [
            bytes([n]) for n in range(256)
        ]
        for value in vectors:
            encoded = scope['base43_encode'](value)
            self.assertEqual(base43.base43_encode(value), encoded)
            self.assertEqual(base43.base43_decode(encoded), scope['base43_decode'](encoded))

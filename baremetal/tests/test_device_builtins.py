# SPDX-License-Identifier: MIT
"""Frozen modules must not use CPython builtins absent from the device runtime.

Host CPython masks missing names such as format() or UnicodeDecodeError, which
raise NameError only on device (same defect class as math.log2/time.time).
"""

import ast, builtins, re, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
REVIEWED = {
    ('DeprecationWarning', 'base64.py')
}  # base64 CLI deprecated aliases; not called by the app


class DeviceBuiltinsTest(unittest.TestCase):
    def test_frozen_names_exist_on_device(self):
        lines = (root / 'tests/device-builtins.txt').read_text().splitlines()
        device = {l.strip() for l in lines if l.strip() and not l.startswith('#')}
        self.assertIn('print', device)
        missing = set(dir(builtins)) - device
        text = (root / 'micropython/manifest.py').read_text()
        modules = sorted({a or b for a, b in re.findall(r'"([\w/]+\.py)"|\'([\w/]+\.py)\'', text)})
        hits = []
        for m in modules:
            tree = ast.parse((root / 'app' / m).read_text())
            defined = {
                n.id
                for n in ast.walk(tree)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
            }
            defined |= {
                n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))
            }
            defined |= {
                a.asname or a.name.split('.')[0]
                for n in ast.walk(tree)
                if isinstance(n, (ast.Import, ast.ImportFrom))
                for a in n.names
            }
            defined |= {
                a.arg
                for n in ast.walk(tree)
                if isinstance(n, ast.arguments)
                for a in n.args + n.kwonlyargs + n.posonlyargs
            }
            for n in ast.walk(tree):
                if (
                    isinstance(n, ast.Name)
                    and isinstance(n.ctx, ast.Load)
                    and n.id in missing
                    and n.id not in defined
                    and (n.id, m) not in REVIEWED
                ):
                    hits.append((m, n.lineno, n.id))
        self.assertEqual(hits, [])


if __name__ == '__main__':
    unittest.main()

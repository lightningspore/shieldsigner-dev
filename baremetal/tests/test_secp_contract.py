# SPDX-License-Identifier: MIT
"""Source/API and public-corpus coverage; primitive correctness runs on the DUT."""

import ast, hashlib, json, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]


class CurveContractTests(unittest.TestCase):
    def test_actual_embit_required_api_is_declared(self):
        required = set()
        for name in ('ec', 'bip32'):
            tree = ast.parse((root / 'app/embit' / (name + '.py')).read_text())
            required.update(
                n.attr
                for n in ast.walk(tree)
                if isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == 'secp256k1'
            )
        tree = ast.parse((root / 'app/secp256k1.py').read_text())
        declared = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        declared.update(
            t.id
            for n in tree.body
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name)
        )
        self.assertEqual(required - declared, set())

    def test_published_vector_scope_and_generated_hash(self):
        receipt = json.loads((root / 'app/secp-vectors-provenance.json').read_text())
        self.assertEqual(
            (
                receipt['bip32ValidPaths'],
                receipt['bip32InvalidKeys'],
                receipt['bip340Rows'],
                receipt['bip39FingerprintCases'],
            ),
            (17, 16, 19, 24),
        )
        self.assertEqual(
            hashlib.sha256((root / 'micropython/secp_gate.py').read_bytes()).hexdigest(),
            receipt['generatedSha256'],
        )
        pin = json.loads((root / 'secp/source.json').read_text())
        self.assertEqual(pin['commit'], 'a660a4976efe880bae7982ee410b9e0dc59ac983')

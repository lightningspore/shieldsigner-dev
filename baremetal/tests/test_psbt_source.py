# SPDX-License-Identifier: MIT
"""Check full framing source coverage and independently generated refusal fixtures."""

import ast, hashlib, json, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]


class FramingSourceTests(unittest.TestCase):
    def test_whole_original_checker_retained(self):
        source = (
            root.parent
            / 'dist/firmware/sources/lvgl/application/src/seedsigner/models/psbt_framing.py'
        )
        raw = source.read_bytes()
        output = (root / 'app/seedsigner_port/psbt_framing.py').read_bytes()
        receipt = json.loads((root / 'app/psbt-framing-provenance.json').read_text())[
            'psbt_framing.py'
        ]
        self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt['sourceSha256'])
        self.assertEqual(hashlib.sha256(output).hexdigest(), receipt['outputSha256'])

        def functions(b):
            return {n.name for n in ast.parse(b).body if isinstance(n, ast.FunctionDef)}

        self.assertEqual(functions(raw), functions(output) - {'_stream_length'})

    def test_refusal_fixture_scope(self):
        cases = json.loads((root / 'app/psbt-framing-vectors.json').read_text())['cases']
        self.assertEqual(len(cases), 15)
        self.assertEqual(sum(c['expected'] == 'ok' for c in cases), 2)
        self.assertTrue(any(c['expected'] == 'reject:WRONG_VERSION_FIELD' for c in cases))
        self.assertTrue(any(c['expected'] == 'reject:MALFORMED_ENCODING' for c in cases))

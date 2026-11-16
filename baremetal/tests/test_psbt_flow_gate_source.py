# SPDX-License-Identifier: MIT
"""Reproducible public native gate preparation; no hardware executed."""

import ast
import json, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]


class PSBTFlowGateSourceTest(unittest.TestCase):
    def test_gate_fixture_matches_independent_signing_oracle_and_template(self):
        oracle = json.loads((root / 'app/psbt-review-public-oracle.json').read_text())
        fixture = next(c for c in oracle['signingData'] if c['name'] == 'NORMAL-1_p2wpkh')
        template = (root / 'tools/psbt_flow_gate_template.py').read_text()
        gate = (root / 'micropython/psbt_flow_gate.py').read_text()
        # The generated gate is ruff-formatted on write: compare structure, not layout.
        expected = template.replace('PUBLIC_FIXTURE = None', 'PUBLIC_FIXTURE = ' + repr(fixture))
        self.assertEqual(ast.dump(ast.parse(gate)), ast.dump(ast.parse(expected)))
        compile(gate, 'psbt_flow_gate.py', 'exec')
        self.assertEqual(fixture['inputs'], 1)
        flat = ''.join(gate.split())  # whitespace-insensitive source checks
        self.assertIn("original.sighash(index,sighash=sig[-1])", flat)
        self.assertIn('assertdecoded_frame()==bytes(payload)', flat)
        self.assertNotIn('run_screen=lambda', flat)

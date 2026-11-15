# SPDX-License-Identifier: MIT
"""Reproducible public native gate preparation; no hardware executed."""
import json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
class PSBTFlowGateSourceTest(unittest.TestCase):
 def test_gate_fixture_matches_independent_signing_oracle_and_template(self):
    oracle=json.loads((root/'app/psbt-review-public-oracle.json').read_text())
    fixture=next(c for c in oracle['signingData'] if c['name']=='NORMAL-1_p2wpkh')
    template=(root/'tools/psbt_flow_gate_template.py').read_text()
    gate=(root/'micropython/psbt_flow_gate.py').read_text()
    self.assertEqual(gate,template.replace('PUBLIC_FIXTURE = None','PUBLIC_FIXTURE = '+repr(fixture)))
    compile(gate,'psbt_flow_gate.py','exec')
    self.assertEqual(fixture['inputs'],1)
    self.assertIn("original.sighash(index,sighash=sig[-1])",gate)
    self.assertIn('assert decoded_frame()==bytes(payload)',gate)
    self.assertNotIn('run_screen=lambda',gate)

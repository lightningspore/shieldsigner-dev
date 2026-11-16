# SPDX-License-Identifier: MIT
"""Source coverage and public oracle scope for the complete original review model."""

import ast, hashlib, json, sys, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root / 'app'))


class PsbtReviewSourceTest(unittest.TestCase):
    def test_complete_original_policy_methods_and_shared_error_identity(self):
        raw = (
            root.parent
            / 'dist/firmware/sources/lvgl/application/src/seedsigner/models/psbt_parser.py'
        ).read_bytes()
        out = (root / 'app/seedsigner_port/psbt_parser.py').read_bytes()
        receipt = json.loads((root / 'app/psbt-review-provenance.json').read_text())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt['sourceSha256'])
        self.assertEqual(hashlib.sha256(out).hexdigest(), receipt['outputSha256'])
        classes = lambda data: {
            n.name: n for n in ast.parse(data).body if isinstance(n, ast.ClassDef)
        }
        original = classes(raw)
        actual = classes(out)
        self.assertEqual(set(actual), set(original) - {'RejectCode', 'InvalidPSBTError'})
        for name in actual:
            methods = lambda c: {n.name for n in c.body if isinstance(n, ast.FunctionDef)}
            self.assertEqual(methods(actual[name]), methods(original[name]), name)
        from seedsigner_port import psbt_parser, psbt_errors

        self.assertIs(psbt_parser.InvalidPSBTError, psbt_errors.InvalidPSBTError)
        self.assertIs(psbt_parser.RejectCode, psbt_errors.RejectCode)

    def test_original_finalizer_and_public_oracle_provenance(self):
        receipt = json.loads((root / 'app/psbt-review-provenance.json').read_text())['finalizer']
        data = (root / 'app/embit/finalizer.py').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), receipt['outputSha256'])
        self.assertEqual(
            hashlib.sha256(data.split(b'\n', 1)[1]).hexdigest(), receipt['sourceSha256']
        )
        oracle = json.loads((root / 'app/psbt-review-public-oracle.json').read_text())
        self.assertEqual(oracle['cases'], 116)
        self.assertEqual((oracle['parsed'], oracle['rejected']), (45, 71))
        self.assertEqual(len(oracle['signingData']), 8)
        self.assertTrue(
            any(
                c['name'] == 'TX-21.claims_us_pays_other' and c['expected']['status'] == 'reject'
                for c in oracle['casesData']
            )
        )
        self.assertTrue(any(c['needsWallClock'] for c in oracle['casesData']))

    def test_clock_boundary_delegates_real_provider_or_fails_explicitly(self):
        from unittest.mock import patch
        import types
        from seedsigner_port import psbt_clock
        from seedsigner_port.decode_platform import FeatureUnavailable

        with patch.object(psbt_clock, '_time', types.SimpleNamespace(time=lambda: 1787616000)):
            self.assertEqual(psbt_clock.time(), 1787616000)
            with self.assertRaises(FeatureUnavailable):
                psbt_clock.gmtime(0)
        with patch.object(psbt_clock, '_time', types.SimpleNamespace(ticks_ms=lambda: 12345)):
            with self.assertRaisesRegex(FeatureUnavailable, 'time.time'):
                psbt_clock.time()

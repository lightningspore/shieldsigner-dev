# SPDX-License-Identifier: MIT
"""Independent protocol failures must reject an otherwise completed ISP run."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_isp_capture import audit


class IspCaptureAuditTest(unittest.TestCase):
    def test_missing_association_measurement_and_unsettled_tail_rejected(self):
        text = ''
        for i in range(32):
            if i:
                text += f'@@ISP_FEEDBACK_FRAME frame={i} measured_parameters={i - 1} boundary_updates={i}\n'
                text += '@@ISP_GAIN_READBACK matched=6 checked=6 unresolved_gain2=2\n'
            text += '@@ISP_STATS mask=0x1120\n'
            text += f'@@ISP_3A_AE frame={i} mean_q8=100 proposed_lines=122 proposed_gain=128\n'
            text += f'@@ISP_3A_AWB frame={i} complete=true gain=[1.0, 1.0, 1.0, 1.0]\n'
        text += '@@ISP_3A_FEEDBACK_DIAGNOSTIC 32-frames; normal-timeshare; not-full-gate\n'
        self.assertEqual(audit(text)['exactStableTailFrames'], 12)
        mutations = [
            ('measured_parameters=8', 'measured_parameters=7'),
            ('matched=6', 'matched=5'),
            ('mask=0x1120', 'mask=0x20'),
            ('AE frame=9', 'AE frame=8'),
            ('AWB frame=31 complete=true gain=[1.0', 'AWB frame=31 complete=true gain=[2.0'),
        ]
        for before, after in mutations:
            with self.subTest(change=before), self.assertRaises(ValueError):
                audit(text.replace(before, after, 1))

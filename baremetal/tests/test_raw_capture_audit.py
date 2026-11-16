"""Reject forged pass markers when independent frame/control evidence disagrees."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_raw_capture import audit


class RawCaptureAuditTest(unittest.TestCase):
    def test_independent_rejections(self):
        sensor = {
            0x320E: 0x7F,
            0x320F: 0xFF,
            0x3E00: 2,
            0x3E01: 0,
            0x3E02: 0,
            0x3E06: 0,
            0x3E07: 0x80,
            0x3E09: 0,
            0x4501: 0xC4,
        }
        text = '@@CAM_SETTINGS named-driver exposure_lines=8192 vts=32767 pattern=false\n'
        text += ''.join(
            f'@@CAM_SENSOR_REG {reg:#06x} {value:#04x}\n' for reg, value in sensor.items()
        )
        text += ''.join(
            f'@@CAM_FRAME {i} status={0x101 if i % 2 == 0 else 0x202:#x} buffer={i % 2} us=799203\n'
            for i in range(10)
        )
        text += '@@CAM_DMA changed_words=933120\n@@RGB_BEGIN 192 108\n@@RGB_END\n@@PASS camera-raw-ten-frames\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'serial.bin'
            path.write_text(text)
            self.assertTrue(audit(path)['mechanicalCapturePassed'])
            self.assertTrue(audit(path)['visualReviewRequired'])
            for old, new in [
                ('status=0x101', 'status=0x10101'),
                ('buffer=0', 'buffer=1'),
                ('buffer=1 us=799203', 'buffer=1 us=2000000'),
                ('0x3e00 0x02', '0x3e00 0x03'),
                ('pattern=false', 'pattern=true'),
                ('changed_words=933120', 'changed_words=0'),
            ]:
                path.write_text(text.replace(old, new, 1))
                with self.subTest(change=(old, new)), self.assertRaises(ValueError):
                    audit(path)

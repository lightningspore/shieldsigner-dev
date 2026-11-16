"""Ensure comparison catches real mismatches and preserves intentional differences."""

import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from compare_camera_readbacks import compare


class CameraComparisonTest(unittest.TestCase):
    def test_mismatch_and_manifest_sensitivity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = bytearray(65536)
            struct.pack_into('<I', raw, 0x120, 0x7075)
            struct.pack_into('<I', raw, 0x124, 0x03400000)
            (root / 'vicap.bin').write_bytes(raw)
            (root / 'manifest.json').write_text(
                json.dumps(
                    [
                        {
                            'block': 'vicap',
                            'base': 0xFFA10000,
                            'bytes': len(raw),
                            'sha256': hashlib.sha256(raw).hexdigest(),
                        }
                    ]
                )
            )
            serial = root / 'serial.bin'
            serial.write_bytes(
                b'@@CAM_REG 0xffa10120 0x00007075\r\n@@CAM_REG 0xffa10124 0x03000000\r\n'
            )
            self.assertEqual(compare(serial, root)['mismatches'], 0)
            serial.write_bytes(serial.read_bytes().replace(b'0x00007075', b'0x00007074'))
            self.assertEqual(compare(serial, root)['mismatches'], 1)
            raw[0] ^= 1
            (root / 'vicap.bin').write_bytes(raw)
            with self.assertRaises(ValueError):
                compare(serial, root)

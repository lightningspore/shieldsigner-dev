"""Reject incomplete or out-of-scope write facts before generating DUT replay."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from reference_camera_data import generate, parse_trace


class ReferenceDataTest(unittest.TestCase):
    def trace(self, lines, header=None):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / 'trace.txt'
        path.write_text(
            (header or f'# applied=0 count={len(lines)} dropped=0 errors=0')
            + '\n'
            + '\n'.join(lines)
            + '\n'
        )
        return path

    def test_dma_and_grf_translation(self):
        path = self.trace(
            [
                '0 100 0 0 0xffa10124 0x03400000 4',
                '1 200 0 0 0xffa10128 0x037cc000 4',
                '2 300 1 16 0x50014 0x00f00030 4',
                '3 400 2 17 0x100 1 1',
            ]
        )
        facts = generate(path)
        self.assertEqual([e['value'] for e in facts['setup'][:2]], facts['dmaBuffers'])
        self.assertEqual(facts['setup'][2]['address'], 0xFF050014)

    def test_trace_integrity_rejected(self):
        line = '0 100 2 17 0x100 1 1'
        for header in [
            '# applied=1 count=1 dropped=0 errors=0',
            '# applied=0 count=1 dropped=1 errors=0',
            '# applied=0 count=1 dropped=0 errors=1',
            '# applied=0 count=2 dropped=0 errors=0',
        ]:
            with self.subTest(header=header), self.assertRaises(ValueError):
                parse_trace(self.trace([line], header))
        with self.assertRaises(ValueError):
            parse_trace(self.trace(['1 100 2 17 0x100 1 1']))

    def test_out_of_scope_writes_rejected(self):
        for bad in [
            '0 100 0 0 0xffac0000 1 4',  # SPI flash is out of scope
            '0 100 1 3 0x50014 1 4',
            '0 100 2 17 0x3000 0x100 1',
            '0 100 2 17 0x3000 1 4',
            '0 100 3 0 0xffa10000 1 4',
        ]:
            with self.subTest(write=bad), self.assertRaises(ValueError):
                generate(self.trace([bad, '1 200 2 17 0x100 1 1']))

"""Exercise actual C page-table walker; forbid reads from mapped device targets."""

import ctypes as C
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Reader = C.CFUNCTYPE(C.c_int, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p)


class TranslationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = ROOT / 'build/trace-translate-test'
        folder.mkdir(parents=True, exist_ok=True)
        library = folder / 'translate.so'
        subprocess.run(
            [
                'cc',
                '-shared',
                '-fPIC',
                '-Wall',
                '-Wextra',
                '-Werror',
                str(ROOT / 'tools/kernel-trace/live_translate.c'),
                '-o',
                str(library),
            ],
            check=True,
        )
        cls.lib = C.CDLL(str(library))
        cls.lib.bm_translate_short.argtypes = [
            C.c_uint32,
            C.c_uint32,
            Reader,
            C.c_void_p,
            C.POINTER(C.c_uint32),
        ]

    def walk(self, words, va, pgd=0x4000):
        reads = []

        @Reader
        def read(address, out, context):
            reads.append(address)
            if address not in words:
                return -1
            out[0] = words[address]
            return 0

        result = C.c_uint32(0xDEADBEEF)
        status = self.lib.bm_translate_short(pgd, va, read, None, C.byref(result))
        return status, result.value, reads

    def test_section_and_pages(self):
        for va in [0xB0000000, 0xB0123456, 0xE1234567, 0xFFA1FFFC]:
            l1 = 0x4000 + (va >> 20) * 4
            l2 = 0x18000 + ((va >> 12) & 255) * 4
            self.assertEqual(
                self.walk({l1: 0xFFA00002}, va), (0, 0xFFA00000 | (va & 0xFFFFF), [l1])
            )
            for flags in [2, 3]:
                self.assertEqual(
                    self.walk({l1: 0x18001, l2: 0xFFA10000 | flags}, va),
                    (0, 0xFFA10000 | (va & 4095), [l1, l2]),
                )
            self.assertEqual(
                self.walk({l1: 0x18001, l2: 0xFFA10001}, va),
                (0, 0xFFA10000 | (va & 65535), [l1, l2]),
            )

    def test_faults_do_not_read_targets(self):
        va = 0xE1234567
        l1 = 0x4000 + (va >> 20) * 4
        l2 = 0x18000 + ((va >> 12) & 255) * 4
        for words in [{}, {l1: 0}, {l1: 3}, {l1: 0xFFA40002}, {l1: 0x18001}, {l1: 0x18001, l2: 0}]:
            status, value, reads = self.walk(words, va)
            self.assertEqual((status, value), (-1, 0xDEADBEEF))
            self.assertTrue(set(reads) <= {l1, l2})
        self.assertEqual(self.walk({}, va, pgd=0x4004), (-1, 0xDEADBEEF, []))

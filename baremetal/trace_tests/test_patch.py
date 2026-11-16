"""Check the actual batch patch core rejects all reads before making any write."""

import ctypes as C
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Reader = C.CFUNCTYPE(C.c_int, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p)
Writer = C.CFUNCTYPE(None, C.c_uint32, C.c_uint32, C.c_void_p)


class PatchTest(unittest.TestCase):
    def test_apply_restore_and_fail_closed(self):
        folder = ROOT / 'build/trace-patch-test'
        folder.mkdir(parents=True, exist_ok=True)
        library = folder / 'patch.so'
        subprocess.run(
            [
                'cc',
                '-shared',
                '-fPIC',
                '-Wall',
                '-Wextra',
                '-Werror',
                str(ROOT / 'tools/kernel-trace/live_patch.c'),
                '-o',
                str(library),
            ],
            check=True,
        )
        lib = C.CDLL(str(library))
        ptr = C.POINTER(C.c_uint32)
        lib.bm_patch_batch.argtypes = [ptr, ptr, ptr, C.c_uint32, Reader, Writer, C.c_void_p]
        pcs = (C.c_uint32 * 18)(*[0x100002 + i * 8 for i in range(18)])
        before = (C.c_uint32 * 18)(*range(18))
        after = (C.c_uint32 * 18)(*range(100, 118))
        words = dict(zip(pcs, before))
        operations = []
        unreadable = set()

        @Reader
        def read(pc, out, context):
            operations.append(('read', pc))
            if pc in unreadable:
                return -1
            out[0] = words[pc]
            return 0

        @Writer
        def write(pc, word, context):
            operations.append(('write', pc))
            words[pc] = word

        for bad in range(18):
            for fault in ['mismatch', 'unreadable']:
                words = dict(zip(pcs, before))
                operations.clear()
                unreadable.clear()
                if fault == 'mismatch':
                    words[pcs[bad]] = 999
                else:
                    unreadable.add(pcs[bad])
                self.assertEqual(lib.bm_patch_batch(pcs, before, after, 18, read, write, None), -1)
                self.assertFalse(any(kind == 'write' for kind, pc in operations))
        words = dict(zip(pcs, before))
        unreadable.clear()
        for source, target in [(before, after), (after, before)]:
            operations.clear()
            self.assertEqual(lib.bm_patch_batch(pcs, source, target, 18, read, write, None), 0)
            self.assertEqual([kind for kind, pc in operations], ['read'] * 18 + ['write'] * 18)
            self.assertEqual(words, dict(zip(pcs, target)))

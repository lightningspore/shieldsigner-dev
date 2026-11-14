# SPDX-License-Identifier: MIT
"""Exercise rejection of corrupted boot artifacts before any card can be used."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location('sd_image', Path(__file__).resolve().parents[1] / 'tools/sd_image.py')
sd_image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd_image)


class SdImageTests(unittest.TestCase):
    def fixture(self):
        stages = [b'unchanged-ddr', b'original-runtime']
        data = bytearray(6144)
        struct.pack_into('<4I', data, 0, 0x534e4b52, 0, (2 << 16) | 384, 1)
        for index, source in enumerate(stages):
            offset = 2048 + index * 2048
            data[offset:offset + len(source)] = source
            at = 120 + index * 88
            struct.pack_into('<4I', data, at, (4 << 16) | (offset // 512), 0xffffffff, 0, index + 1)
            data[at + 24:at + 56] = hashlib.sha256(data[offset:offset + 2048]).digest()
        self.rehash(data)
        return data, stages

    def rehash(self, data):
        data[1536:1568] = hashlib.sha256(data[:1536]).digest()

    def test_two_exact_stages(self):
        data, stages = self.fixture()
        self.assertEqual(len(sd_image.inspect_idblock(data, stages)), 2)

    def test_corrupt_header_or_stage_rejected(self):
        for position in [0, 12, 120, 1536, 2048, 4096, 6143]:
            with self.subTest(position=position):
                data, stages = self.fixture()
                data[position] ^= 1
                with self.assertRaises(ValueError):
                    sd_image.inspect_idblock(data, stages)

    def test_rehashed_overlap_or_truncation_rejected(self):
        for offset in [0, 4, 9, 65535]:
            data, stages = self.fixture()
            struct.pack_into('<I', data, 208, (4 << 16) | offset)
            self.rehash(data)
            with self.assertRaises(ValueError):
                sd_image.inspect_idblock(data, stages)
        data, stages = self.fixture()
        for truncated in [data[:10], data[:-1], data + bytes(512)]:
            with self.assertRaises(ValueError):
                sd_image.inspect_idblock(truncated, stages)

    def test_valid_hash_cannot_substitute_input(self):
        data, stages = self.fixture()
        with self.assertRaises(ValueError):
            sd_image.inspect_idblock(data, [stages[0], b'vendor-spl'])

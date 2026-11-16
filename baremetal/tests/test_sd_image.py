# SPDX-License-Identifier: MIT
"""Exercise rejection of corrupted boot artifacts before any card can be used."""

import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location(
    'sd_image', Path(__file__).resolve().parents[1] / 'tools/sd_image.py'
)
sd_image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd_image)


class SdImageTests(unittest.TestCase):
    def fixture(self):
        stages = [b'unchanged-ddr', b'original-runtime']
        data = bytearray(6144)
        struct.pack_into('<4I', data, 0, 0x534E4B52, 0, (2 << 16) | 384, 1)
        for index, source in enumerate(stages):
            offset = 2048 + index * 2048
            data[offset : offset + len(source)] = source
            at = 120 + index * 88
            struct.pack_into('<4I', data, at, (4 << 16) | (offset // 512), 0xFFFFFFFF, 0, index + 1)
            data[at + 24 : at + 56] = hashlib.sha256(data[offset : offset + 2048]).digest()
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

    def test_large_native_app_image_keeps_complete_idblock(self):
        data = bytes([0xA5]) * (2900000)
        image = sd_image.compose_sd_image(data)
        self.assertEqual(len(image), 3 * 1024 * 1024)
        self.assertFalse(any(image[: sd_image.SD_OFFSET]))
        self.assertEqual(image[sd_image.SD_OFFSET : sd_image.SD_OFFSET + len(data)], data)
        self.assertFalse(any(image[sd_image.SD_OFFSET + len(data) :]))
        self.assertEqual(len(sd_image.compose_sd_image(b'public')), 2 * 1024 * 1024)

    def test_app_profile_rejects_wrong_board_fault_profile_or_payload(self):
        payload = b'public'
        manifest = {
            'features': 'app-autostart',
            'usbSerial': 'rv1103-dut1',
            'files': {'build/hello.bin': sd_image.sha(payload)},
        }
        sd_image.validate_payload(payload, manifest, 'app')
        for field, value in (
            ('usbSerial', 'rv1103-dev-001'),
            ('features', 'app-ui,fault-probe'),
            ('features', 'fast-boot'),
        ):
            with self.assertRaises(ValueError):
                sd_image.validate_payload(payload, {**manifest, field: value}, 'app')
        with self.assertRaises(ValueError):
            sd_image.validate_payload(payload + b'changed', manifest, 'app')

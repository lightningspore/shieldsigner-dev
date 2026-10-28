"""Contract checks for the process-local QR retry, without a native ZBar dependency."""
import unittest
from PIL import Image
from shieldsigner_integration import install_qr_fallback


class QrFallbackTests(unittest.TestCase):
    def decoder(self, answers):
        calls = []

        class Decoder:
            @staticmethod
            def extract_qr_data(image, is_binary=False):
                calls.append((image, is_binary, getattr(image, "format", None)))
                return next(answers)

        return Decoder, calls

    def test_raw_success_preserves_bytes_and_skips_retry(self):
        payload = b"\x00\xffUR:binary"
        decoder, calls = self.decoder(iter([payload]))
        stats = install_qr_fallback(decoder)
        frame = Image.new("RGB", (40, 40))
        self.assertIs(decoder.extract_qr_data(frame, is_binary=True), payload)
        self.assertEqual(calls, [(frame, True, None)])
        self.assertEqual(stats["attempts"], 0)

    def test_miss_retries_once_and_preserves_binary_flag(self):
        for mode in ("RGB", "L", "RGBA"):
            with self.subTest(mode=mode):
                payload = b"\x00\xff"
                decoder, calls = self.decoder(iter([None, payload]))
                stats = install_qr_fallback(decoder)
                method = decoder.extract_qr_data
                self.assertIs(install_qr_fallback(decoder), stats)
                self.assertIs(decoder.extract_qr_data, method)
                frame = Image.new(mode, (40, 40))
                self.assertIs(decoder.extract_qr_data(frame, is_binary=True), payload)
                self.assertEqual(calls[0], (frame, True, None))
                self.assertEqual(calls[1][1:], (True, "JPEG"))
                self.assertEqual(stats["attempts"], 1)
                self.assertEqual(stats["successes"], 1)

    def test_failed_retry_returns_none(self):
        decoder, calls = self.decoder(iter([None, None]))
        stats = install_qr_fallback(decoder)
        self.assertIsNone(decoder.extract_qr_data(Image.new("RGB", (40, 40))))
        self.assertEqual(len(calls), 2)
        self.assertEqual(stats["successes"], 0)
        self.assertFalse(calls[1][1])

    def test_non_pillow_inputs_only_use_original(self):
        for frame in (None, (b"data", 2, 2)):
            decoder, calls = self.decoder(iter([None]))
            stats = install_qr_fallback(decoder)
            self.assertIsNone(decoder.extract_qr_data(frame))
            self.assertEqual(len(calls), 1)
            self.assertEqual(stats["attempts"], 0)


if __name__ == "__main__":
    unittest.main()

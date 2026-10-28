"""Wire-format checks: uv run --with pillow python demo/test_server.py."""
import random
import unittest

from server import HEADER, read_frame


class Feed:
    def __init__(self, data):
        self.data = data

    def recv(self, count):
        block = self.data[: min(count, 137)]
        self.data = self.data[len(block):]
        return block


class TransportTests(unittest.TestCase):
    def test_nv12_matches_board_color_matrix_and_rgb_is_unchanged(self):
        rng = random.Random(731)
        width = height = 64
        y = bytes(rng.randrange(256) for _ in range(width * height))
        uv = bytes(rng.randrange(256) for _ in range(width * height // 2))
        packet = HEADER.pack(b"SSNV12F1", width, height, 7, len(y + uv)) + y + uv
        w, h, sequence, rgb = read_frame(Feed(packet))
        self.assertEqual((w, h, sequence), (width, height, 7))
        expected = []
        for row in range(height):
            for col in range(width):
                c = y[row * width + col]
                offset = row // 2 * width + (col & ~1)
                d, e = uv[offset] - 128, uv[offset + 1] - 128
                expected.extend(max(0, min(255, (v + 128) >> 8)) for v in (
                    256 * c + 359 * e, 256 * c - 88 * d - 183 * e, 256 * c + 454 * d
                ))
        # Pillow uses higher-precision BT.601 coefficients than the board's Q8
        # conversion. Only this optional desktop preview uses Pillow rounding.
        self.assertLessEqual(max(abs(a - b) for a, b in zip(rgb, expected)), 1)
        packet = HEADER.pack(b"SSRGB001", width, height, 8, len(rgb)) + rgb
        self.assertEqual(read_frame(Feed(packet))[3], rgb)

    def test_rejects_odd_nv12_wrong_size_and_truncation(self):
        for magic, width, height, size, data in (
            (b"SSNV12F1", 3, 2, 9, bytes(9)),
            (b"SSNV12F1", 2, 2, 5, bytes(5)),
            (b"SSRGB001", 2, 2, 12, bytes(5)),
        ):
            with self.subTest(magic=magic, width=width, size=size):
                with self.assertRaises((ValueError, EOFError)):
                    read_frame(Feed(HEADER.pack(magic, width, height, 1, size) + data))


if __name__ == "__main__":
    unittest.main()

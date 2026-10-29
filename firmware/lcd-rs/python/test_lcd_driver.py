import unittest
from types import SimpleNamespace
from PIL import Image
from shieldsigner_lcd_driver import native_driver_class


class DriverTests(unittest.TestCase):
    def fixture(self):
        calls = []
        class Original:
            NORMAL_COLORS_REQUIRE_INVERSION = True
            def __init__(self): self.width = self.height = 240; self.__post_init__()
            def __post_init__(self):
                self._spi = SimpleNamespace(fd=42)
                self._dc = SimpleNamespace(write=lambda value: calls.append(('dc', value)))
                calls.append('gpio/init-policy-preserved')
            def _ensure_initialized(self): calls.append('init')
            def SetWindows(self, *args): calls.append(('window', args))
            def invert(self, enabled): calls.append(('invert', enabled))
            def close(self): calls.append('close')
        class Writer:
            def __init__(self, *args): calls.append(('writer', args))
            def write_rgb(self, rgb): calls.append(('rgb', len(rgb), rgb[:3]))
            def clear_white(self): calls.append('white')
        return native_driver_class(Original, Writer), calls

    def test_rgb_luma_windows_inversion_and_lifecycle(self):
        cls, calls = self.fixture(); display = cls()
        self.assertTrue(display.NORMAL_COLORS_REQUIRE_INVERSION)
        display.show_image(Image.new('RGB', (240, 240), (255, 128, 16)))
        self.assertEqual(calls[-3:], [('window', (0, 0, 240, 240)), ('dc', True), ('rgb', 172800, bytes([255,128,16]))])
        display.show_image(Image.new('L', (240, 240), 7))
        self.assertEqual(calls[-1], ('rgb', 172800, bytes([7,7,7])))
        display.clear(); self.assertEqual(calls[-1], 'white')
        display.invert(False); self.assertEqual(calls[-1], ('invert', False))
        display.close(); self.assertEqual(calls[-1], 'close')
        self.assertIsNone(display._rust_writer)
        before = list(calls)
        for operation in [lambda: display.show_image(Image.new('RGB', (240,240))), display.clear, lambda: display.invert(True)]:
            with self.assertRaisesRegex(RuntimeError, 'closed'): operation()
        self.assertEqual(calls, before)

    def test_invalid_frames_do_not_touch_gpio_or_spi(self):
        cls, calls = self.fixture(); display = cls(); before = list(calls)
        for image, x, y in [(Image.new('RGB', (1, 1)), 0, 0), (Image.new('RGB', (240,240)),1,0)]:
            with self.assertRaises(ValueError): display.show_image(image,x,y)
            self.assertEqual(calls,before)

if __name__ == '__main__': unittest.main()

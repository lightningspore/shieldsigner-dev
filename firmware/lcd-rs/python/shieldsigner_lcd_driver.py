"""Opt-in native frame transport; keep the reviewed ST7789 GPIO/init policy.

Call install(app_root) before constructing Renderer/the display. This changes
only process-local class selection, never installed files or GPIO mappings.
"""
import hashlib
import importlib
from pathlib import Path
import threading

REVIEWED_ST7789_SHA256 = '2d208968bfaad3b5aaaf4de18aca3aa44c786d2dd6a297a33919b9cea720255d'


def native_driver_class(original, frame_writer):
    class RustST7789(original):
        def __post_init__(self):
            self._rust_lock = threading.Lock()
            self._rust_writer = None
            super().__post_init__()
            try:
                if (self.width, self.height) != (240, 240):
                    raise ValueError('Reviewed Rust LCD profile supports only 240x240')
                self._rust_writer = frame_writer(self._spi.fd, self.width, self.height)
            except BaseException:
                super().close()
                raise

        def show_image(self, image, Xstart=0, Ystart=0):
            if image.size != (self.width, self.height):
                raise ValueError('Image must match the display dimensions')
            if (Xstart, Ystart) != (0, 0):
                raise ValueError('Reviewed LCD profile writes complete frames at 0,0')
            # Serialize the complete GPIO command+pixel transaction, including
            # while Rust releases the GIL during packing and SPI DMA waits.
            with self._rust_lock:
                if self._rust_writer is None:
                    raise RuntimeError('LCD driver is closed')
                self._ensure_initialized()
                self.SetWindows(0, 0, self.width, self.height)
                self._dc.write(True)
                self._rust_writer.write_rgb(image.convert('RGB').tobytes())

        def clear(self):
            with self._rust_lock:
                if self._rust_writer is None:
                    raise RuntimeError('LCD driver is closed')
                self._ensure_initialized()
                self.SetWindows(0, 0, self.width, self.height)
                self._dc.write(True)
                self._rust_writer.clear_white()

        def invert(self, enabled=True):
            with self._rust_lock:
                if self._rust_writer is None:
                    raise RuntimeError('LCD driver is closed')
                super().invert(enabled)

        def close(self):
            lock = getattr(self, '_rust_lock', None)
            if lock is None:
                return super().close()
            with lock:
                self._rust_writer = None  # close only the duplicated Rust fd
                super().close()

    RustST7789.__name__ = 'RustST7789'
    return RustST7789


def install(app_root):
    path = Path(app_root).resolve() / 'seedsigner/hardware/displays/ST7789.py'
    if hashlib.sha256(path.read_bytes()).hexdigest() != REVIEWED_ST7789_SHA256:
        raise ValueError('Unreviewed ST7789 source; review before native LCD integration')
    module = importlib.import_module('seedsigner.hardware.displays.ST7789')
    if Path(module.__file__).resolve() != path:
        raise RuntimeError('Imported display driver is outside the requested app root')
    if getattr(module, '__shieldsigner_native_lcd__', None):
        return module.__shieldsigner_native_lcd__
    from shieldsigner_lcd import FrameWriter
    module.ST7789 = native_driver_class(module.ST7789, FrameWriter)
    info = {'kind': 'rust-pyo3-lcd-frame-transport', 'sourceSha256': REVIEWED_ST7789_SHA256,
            'geometry': [240, 240], 'gpioInitAndSpiSettings': 'existing-reviewed-driver',
            'wireFormat': 'RGB565-big-endian', 'conversionAndSpiReleaseGil': True,
            'installedFilesModified': False, 'hardwareQualified': False}
    module.__shieldsigner_native_lcd__ = info
    return info

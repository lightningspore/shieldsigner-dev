"""Explicit native frontend adapter; preserves RGB still and entropy contracts."""
from PIL import Image
from shieldsigner_camera_compat import _VideoContract
from shieldsigner_native_stream import NativeVideoStream


class NativeCameraStream(_VideoContract, NativeVideoStream):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from shieldsigner_lcd import PreviewRenderer
        self._preview_renderer = PreviewRenderer()
        self.backend_info["frontend"] = "rust"
        self.backend_info["returnedImageMode"] = "NativeFrame" if self.transport == "nv12" else "RGB"

    def _prepare(self, frame, preview=False, display=False, rotation=0):
        if frame is None:
            return None
        if frame.format == "rgb":
            return Image.frombytes("RGB", frame.size, frame.pixel_bytes())
        if preview:
            width, height, pixels = self._preview_renderer.render_frame(frame, rotation % 360)
            return Image.frombytes("RGB", (width, height), pixels)
        if display:
            return Image.frombytes("L", frame.size, frame.luma_bytes()).convert("RGB")
        return frame

    def read(self, preview=False, display=False):
        frame = NativeVideoStream.read(self, preview=preview, display=display)
        return self._prepare(frame, preview, display)

    def read_native_preview(self, rotation):
        # RGB/non-small-RAM retains the existing full-resolution Camera path.
        if self.transport != "nv12":
            raise ValueError("Native reduced preview requires NV12")
        return self._prepare(NativeVideoStream.read(self, preview=True), preview=True, rotation=rotation)

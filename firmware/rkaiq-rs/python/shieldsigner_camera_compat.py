"""Pinned cross-platform Camera adapter for the single SC3336 Rust pipeline.

The application may request another resolution, frame rate or a legacy V4L2
node. This backend publishes native 640x480 pixels (RGB, or opt-in small-RAM video
luma); it does
not claim to reconfigure the fixed sensor/ISP graph or synthesize a BGR array.
Camera handles display rotation/preview conversion after read().
"""
import os
from PIL import Image
from shieldsigner_video_stream import PiVideoStream


class _VideoContract:
    def __init__(self, resolution=(512, 384), framerate=12, format="bgr",
                 device_index=0, camera_config=None, prefer_v4l2=False, for_still=False):
        if device_index not in (0, None):
            raise ValueError("Rust camera backend supports only the fixed SC3336 camera (index 0)")
        self._small_ram_preview = os.environ.get("SHIELDSIGNER_SMALL_RAM") == "1" and not for_still
        transport = "nv12" if self._small_ram_preview else "rgb"
        self.backend_info = {
            "backend": "rust-sc3336-fixed-native",
            "nativeResolution": [640, 480],
            "returnedImageMode": "L" if transport == "nv12" else "RGB",
            "displayImageMode": "RGB",
            "transport": transport,
            "forStill": bool(for_still),
            "requestedResolution": list(resolution),
            "requestedFramerate": framerate,
            "requestedFormat": format,
            "requestedV4l2": prefer_v4l2,
            "legacyCameraConfig": dict(camera_config or {}),
            "resamplingPerformed": False,
            "consumerFramerateLimit": framerate,
            "sensorFramerateChanged": False,
            "previewResolutionBeforeRotation": [240, 180] if self._small_ram_preview else [640, 480],
            "previewOnlyResampling": self._small_ram_preview,
            "decodeResolution": [640, 480],
        }
        super().__init__(width=640, height=480, consumer_framerate=framerate, transport=transport)

    def read(self, preview=False, display=False):
        # Both flags are accepted for the pinned application's VideoStream API.
        # Only the optional display preview is reduced. The pinned Camera
        # performs grayscale/rotation next; decoding and still reads retain the
        # full native pixels. Still captures explicitly retain RGB. This is
        # separate from requested FPS pacing.
        frame = super().read(preview=preview, display=display)
        if self._small_ram_preview and preview and frame is not None:
            return frame.resize((240, 180), resample=Image.Resampling.NEAREST)
        # Camera.read_video_stream(as_image=True, preview=False) uses display
        # reads for image/entropy workflows. Those callers expect RGB channel
        # tuples, while QR's ordinary read must retain exact full-resolution Y.
        if self._small_ram_preview and display and frame is not None and frame.mode != "RGB":
            return frame.convert("RGB")
        return frame


class VideoStream(_VideoContract, PiVideoStream):
    def __new__(cls, *args, **kwargs):
        backend = os.environ.get("SHIELDSIGNER_FRONTEND_BACKEND", "python")
        if backend not in ("python", "rust"):
            raise ValueError("Frontend backend must be python or rust")
        if cls is VideoStream and backend == "rust":
            from shieldsigner_native_camera import NativeCameraStream
            return NativeCameraStream(*args, **kwargs)
        return super().__new__(cls)

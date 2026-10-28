"""Pinned cross-platform Camera adapter for the single SC3336 Rust pipeline.

The application may request another resolution, frame rate or a legacy V4L2
node. This backend explicitly publishes the native 640x480 RGB stream; it does
not claim to reconfigure the fixed sensor/ISP graph or synthesize a BGR array.
Camera handles display rotation/preview conversion after read().
"""
from shieldsigner_video_stream import PiVideoStream


class VideoStream(PiVideoStream):
    def __init__(self, resolution=(512, 384), framerate=12, format="bgr",
                 device_index=0, camera_config=None, prefer_v4l2=False):
        if device_index not in (0, None):
            raise ValueError("Rust camera backend supports only the fixed SC3336 camera (index 0)")
        self.backend_info = {
            "backend": "rust-sc3336-fixed-native",
            "nativeResolution": [640, 480],
            "returnedImageMode": "RGB",
            "requestedResolution": list(resolution),
            "requestedFramerate": framerate,
            "requestedFormat": format,
            "requestedV4l2": prefer_v4l2,
            "legacyCameraConfig": dict(camera_config or {}),
            "resamplingPerformed": False,
        }
        super().__init__(width=640, height=480)

    def read(self, preview=False, display=False):
        # Both flags are accepted for the pinned application's VideoStream API.
        # Pixel conversions belong to Camera; keep scan pixels unmodified here.
        return super().read()

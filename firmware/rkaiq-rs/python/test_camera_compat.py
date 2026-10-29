"""Fixed-native geometry and pixel contracts for the pinned Camera API adapter."""
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image
from shieldsigner_camera_compat import VideoStream
from shieldsigner_video_stream import PiVideoStream


class CameraCompatibilityTests(unittest.TestCase):
    def test_requested_vendor_profile_is_explicit_and_pixels_are_preserved(self):
        with patch.dict(os.environ, {}, clear=True):
            stream = VideoStream(resolution=(480, 480), framerate=6, format="bgr",
                                 camera_config={"device": "/dev/video12", "pixelformat": "GREY"},
                                 prefer_v4l2=True)
        frame = Image.new("RGB", (640, 480), (7, 83, 231))
        with stream._lock:
            stream.frame = frame
        self.assertEqual((stream.width, stream.height), (640, 480))
        self.assertEqual(stream.backend_info["requestedResolution"], [480, 480])
        self.assertFalse(stream.backend_info["resamplingPerformed"])
        for flags in ({}, {"preview": True}, {"display": True}, {"preview": True, "display": True}):
            self.assertIs(stream.read(**flags), frame)
            self.assertEqual(stream.read(**flags).getpixel((0, 0)), (7, 83, 231))
        stream.stop()

    def test_first_use_creates_output_parent_and_preserves_filesystem_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp) / "missing" / "sessions"
            config = dict(output_directory=str(parent), binary="/nonexistent-camera-owner",
                          plan="plan", iq="iq", parameters="params", image="image", statistics="stats")
            stream = PiVideoStream(owner_config=config)
            # Reaching the owner launch proves first-use session creation worked;
            # no camera hardware or fabricated live frames are involved.
            with self.assertRaises(FileNotFoundError):
                stream.start()
            self.assertTrue(Path(stream.session_directory).is_dir())
            self.assertTrue(parent.is_dir())
            self.assertIsNone(stream._owner)
            blocker = Path(temp) / "regular-file"
            blocker.write_text("not a directory")
            rejected = PiVideoStream(owner_config=dict(config, output_directory=str(blocker)))
            with self.assertRaises(FileExistsError):
                rejected.start()
            self.assertIsNone(rejected._owner)

    def test_another_camera_is_not_silently_selected(self):
        with self.assertRaisesRegex(ValueError, "index 0"):
            VideoStream(device_index=1)


if __name__ == "__main__":
    unittest.main()

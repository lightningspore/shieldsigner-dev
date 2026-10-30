"""Fixed-native geometry and pixel contracts for the pinned Camera API adapter."""
import os
import tempfile
import threading
import time
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image
from shieldsigner_camera_compat import VideoStream
from shieldsigner_video_stream import PiVideoStream, diagnostic_log_policy
from shieldsigner_process_log import ProcessLog, record_finished_session, MARKER


class CameraCompatibilityTests(unittest.TestCase):
    def test_requested_vendor_profile_is_explicit_and_pixels_are_preserved(self):
        with patch.dict(os.environ, {}, clear=True):
            stream = VideoStream(resolution=(480, 480), framerate=6, format="bgr",
                                 camera_config={"device": "/dev/video12", "pixelformat": "GREY"},
                                 prefer_v4l2=True)
        frame = Image.new("RGB", (640, 480), (7, 83, 231))
        with stream._lock:
            stream.frame = frame
            stream.is_stopped = False
        self.assertEqual((stream.width, stream.height), (640, 480))
        self.assertEqual(stream.backend_info["requestedResolution"], [480, 480])
        self.assertFalse(stream.backend_info["resamplingPerformed"])
        for flags in ({}, {"preview": True}, {"display": True}, {"preview": True, "display": True}):
            with stream._frame_ready:
                stream.frames_received += 1
                stream._frame_ready.notify_all()
            result = stream.read(**flags)
            self.assertIs(result, frame)
            self.assertEqual(result.getpixel((0, 0)), (7, 83, 231))
        stream.stop()

    def test_each_consumer_receives_each_generation_without_duplicate_work(self):
        stream = PiVideoStream()
        stream.is_stopped = False
        first, second = Image.new("RGB", (1, 1)), Image.new("RGB", (1, 1))
        barrier = threading.Barrier(3)
        results = []
        def consume():
            barrier.wait()
            a = stream.read(preview=True)
            barrier.wait()
            b = stream.read(display=True)
            results.append((a, b))
        threads = [threading.Thread(target=consume) for _ in range(2)]
        for thread in threads: thread.start()
        with stream._frame_ready:
            stream.frame, stream.frames_received = first, 1
        barrier.wait()
        barrier.wait()
        with stream._frame_ready:
            stream.frame, stream.frames_received = second, 2
            stream._frame_ready.notify_all()
        for thread in threads:
            thread.join(1)
            self.assertFalse(thread.is_alive())
        self.assertEqual(results, [(first, second), (first, second)])
        self.assertIs(stream.read(), second)
        started = time.monotonic()
        self.assertIsNone(stream.read())
        self.assertGreaterEqual(time.monotonic()-started, 0.15)
        self.assertLess(time.monotonic()-started, 0.4)
        # A restarted session can reuse the same wire sequence/counter.
        with stream._frame_ready:
            stream._read_epoch += 1
        self.assertIs(stream.read(), second)

    def test_requested_rate_paces_each_consumer_and_selects_latest_frame(self):
        stream = PiVideoStream(consumer_framerate=10)
        stream.is_stopped = False
        frames = [Image.new("RGB", (1, 1), (n, 0, 0)) for n in range(3)]
        stream.frame, stream.frames_received = frames[0], 1
        first_read = threading.Barrier(3)
        results = []
        def consume():
            self.assertIs(stream.read(), frames[0])
            started = time.monotonic()
            first_read.wait()
            frame = stream.read()
            results.append((frame, time.monotonic()-started))
        threads = [threading.Thread(target=consume) for _ in range(2)]
        for thread in threads: thread.start()
        first_read.wait()
        with stream._frame_ready:
            stream.frame, stream.frames_received = frames[1], 2
            stream._frame_ready.notify_all()
        time.sleep(0.02)
        with stream._frame_ready:
            stream.frame, stream.frames_received = frames[2], 3
            stream._frame_ready.notify_all()
        for thread in threads:
            thread.join(1)
            self.assertFalse(thread.is_alive())
        self.assertEqual(len(results), 2)
        for frame, elapsed in results:
            self.assertIs(frame, frames[2])
            self.assertGreaterEqual(elapsed, 0.08)
            self.assertLess(elapsed, 0.3)
        # Restart resets the per-consumer pacing deadline immediately.
        self.assertIs(stream.read(), frames[2])
        with stream._frame_ready: stream._read_epoch += 1
        started = time.monotonic()
        self.assertIs(stream.read(), frames[2])
        self.assertLess(time.monotonic()-started, 0.05)

    def test_consumer_rate_rejects_nonfinite_or_unbounded_values(self):
        for value in (0, -1, float("nan"), float("inf"), 121, True, "6"):
            with self.assertRaises(ValueError): PiVideoStream(consumer_framerate=value)

    def test_stop_and_error_wake_all_waiting_consumers(self):
        for failure in (False, True):
            stream = PiVideoStream()
            stream.is_stopped = False
            ready = threading.Barrier(3)
            results = []
            def consume():
                ready.wait()
                try: results.append(stream.read())
                except RuntimeError: results.append("error")
            threads = [threading.Thread(target=consume) for _ in range(2)]
            for thread in threads: thread.start()
            ready.wait()
            if failure:
                with stream._frame_ready:
                    stream.error = ValueError("reader failed")
                    stream._frame_ready.notify_all()
            else:
                stream.stop()
            for thread in threads:
                thread.join(0.15)
                self.assertFalse(thread.is_alive())
            self.assertEqual(results, ["error", "error"] if failure else [None, None])

    def test_small_ram_log_policy_bounds_and_full_override(self):
        cases = [({}, {"full": False}, 3),
                 ({"SHIELDSIGNER_SMALL_RAM": "1"}, {"full": False, "head_bytes": 16384, "tail_bytes": 49152}, 1),
                 ({"SHIELDSIGNER_SMALL_RAM": "true"}, {"full": False}, 3),
                 ({"SHIELDSIGNER_SMALL_RAM": "1", "SHIELDSIGNER_CAMERA_LOG_FULL": "1"}, {"full": True}, 3)]
        for environment, expected, retention in cases:
            with patch.dict(os.environ, environment, clear=True):
                options, keep = diagnostic_log_policy()
            self.assertEqual((options, keep), (expected, retention))
        with tempfile.TemporaryDirectory() as root:
            payload = b"startup\n" + b"a" * (128*1024) + b"\nshutdown\n"
            with patch.dict(os.environ, {"SHIELDSIGNER_SMALL_RAM": "1"}, clear=True):
                options, keep = diagnostic_log_policy()
            sessions = []
            for index in range(3):
                path = Path(root) / ("camera-" + str(index))
                path.mkdir()
                log = ProcessLog(path / "owner.log", **options)
                log._append(payload)
                info = log.finish()
                record_finished_session(path, 0, info, keep=keep)
                sessions.append(path)
            self.assertFalse(sessions[0].exists())
            self.assertFalse(sessions[1].exists())
            saved = (sessions[2] / "owner.log").read_bytes()
            self.assertEqual(info["maxRetainedPayloadBytes"], 65536)
            self.assertLess(len(saved), 65792)  # small omission marker overhead
            self.assertTrue(saved.startswith(b"startup\n"))
            self.assertTrue(saved.endswith(b"shutdown\n"))
            diagnostic = Path(root) / "camera-full"
            diagnostic.mkdir()
            log = ProcessLog(diagnostic / "owner.log", full=True)
            log._append(payload)
            full_info = log.finish()
            record_finished_session(diagnostic, 0, full_info, keep=1)
            self.assertEqual((diagnostic / "owner.log").read_bytes(), payload)
            self.assertTrue(sessions[2].exists())  # full mode performs no pruning

    def test_small_ram_preview_only_resize_preserves_rendered_quadrants(self):
        def rendered(image, rotation):
            image = image.convert("L").convert("RGB").rotate(90 + rotation, expand=True)
            scale = min(240 / image.width, 240 / image.height)
            resized = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.NEAREST)
            canvas = Image.new("RGB", (240, 240))
            canvas.paste(resized, ((240-resized.width)//2, (240-resized.height)//2))
            return canvas
        frame = Image.new("RGB", (640, 480))
        for box, color in [((0, 0, 320, 240), "red"), ((320, 0, 640, 240), "green"),
                           ((0, 240, 320, 480), "blue"), ((320, 240, 640, 480), "white")]:
            frame.paste(color, box)
        original_bytes = frame.tobytes()
        for enabled in (False, True):
            with patch.dict(os.environ, {"SHIELDSIGNER_SMALL_RAM": "1"} if enabled else {}, clear=True):
                stream = VideoStream(framerate=6)
            with patch.object(PiVideoStream, "read", return_value=frame):
                preview = stream.read(preview=True)
                self.assertEqual(preview.size, (240, 180) if enabled else (640, 480))
                for rotation in (0, 90, 180, 270):
                    self.assertEqual(rendered(preview, rotation).tobytes(), rendered(frame, rotation).tobytes())
                self.assertIs(stream.read(), frame)
                self.assertIs(stream.read(display=True), frame)
                self.assertEqual(stream.backend_info["decodeResolution"], [640, 480])
                self.assertEqual(stream.backend_info["previewOnlyResampling"], enabled)
            self.assertEqual(frame.tobytes(), original_bytes)

    def test_nv12_exact_luma_bounds_and_still_rgb_contract(self):
        with patch.dict(os.environ, {"SHIELDSIGNER_SMALL_RAM": "1"}, clear=True):
            video, still = VideoStream(framerate=6), VideoStream(for_still=True)
        self.assertEqual((video.transport, still.transport), ("nv12", "rgb"))
        self.assertEqual(video.backend_info["returnedImageMode"], "L")
        self.assertEqual(still.backend_info["returnedImageMode"], "RGB")
        y = bytes(range(256)) * 1200
        payload = y + b"\x11\xee" * (640*480//4)
        image = video._frame_from_payload(640, 480, payload)
        self.assertEqual((image.mode, image.size), ("L", (640, 480)))
        self.assertEqual(image.tobytes(), y)
        # Chroma changes cannot alter decode Y pixels.
        self.assertEqual(video._frame_from_payload(640, 480, y + bytes(640*480//2)).tobytes(), y)
        rgb = bytes((7, 83, 231)) * (640*480)
        self.assertEqual(still._frame_from_payload(640, 480, rgb).tobytes(), rgb)
        with patch.object(PiVideoStream, "read", return_value=image):
            self.assertIs(video.read(), image)
            self.assertEqual(video.read(preview=True).size, (240, 180))
            entropy_frame = video.read(display=True)
            self.assertEqual((entropy_frame.mode, entropy_frame.size), ("RGB", (640, 480)))
            self.assertEqual(entropy_frame.convert("L").tobytes(), y)
            self.assertTrue(any(low != high for low, high in entropy_frame.getextrema()))
            self.assertIs(video.read(), image)  # Display conversion never changes QR pixels.
        for magic, width, height, size in [(b"SSRGB001", 640, 480, len(payload)),
                (b"SSNV12F1", 640, 480, len(payload)-1),
                (b"SSNV12F1", 640, 480, len(payload)+1),
                (b"SSNV12F1", 4097, 480, len(payload)),
                (b"SSNV12F1", 0, 480, 0)]:
            with self.assertRaises(ValueError): video._validate_frame_header(magic, width, height, size)
        with self.assertRaises(ValueError):
            PiVideoStream(width=3, height=2, transport="nv12")._validate_frame_header(b"SSNV12F1", 3, 2, 9)
        with self.assertRaises(ValueError): video._frame_from_payload(640, 480, payload[:-1])

    def test_managed_child_transport_is_explicit_and_parent_environment_unchanged(self):
        for for_still, expected in ((False, "nv12"), (True, "rgb")):
            with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"SHIELDSIGNER_SMALL_RAM": "1", "SHIELDSIGNER_CAMERA_STREAM_FORMAT": "nv12"}, clear=True):
                stream = VideoStream(for_still=for_still)
                stream.owner_config = dict(output_directory=root, binary="owner", plan="plan", iq="iq", parameters="params", image="image", statistics="stats")
                with patch("shieldsigner_video_stream.subprocess.Popen", side_effect=RuntimeError("launch intercepted")) as launch:
                    with self.assertRaisesRegex(RuntimeError, "intercepted"): stream.start()
                self.assertEqual(launch.call_args.kwargs["env"].get("SHIELDSIGNER_CAMERA_STREAM_FORMAT"), expected)
                self.assertEqual(os.environ["SHIELDSIGNER_CAMERA_STREAM_FORMAT"], "nv12")

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

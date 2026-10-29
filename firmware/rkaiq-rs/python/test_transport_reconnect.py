"""Real Unix sockets, tiny public pixels, and a fake managed-owner lifecycle."""
import os
import socket
import struct
import tempfile
import threading
import time
import unittest

from shieldsigner_video_stream import PiVideoStream


def packet(sequence=7):
    return struct.pack('<8sIIII', b'SSRGB001', 2, 2, sequence, 12) + bytes(range(12))


class Owner:
    def __init__(self): self.code = None
    def poll(self): return self.code
    def terminate(self): self.code = 0
    def wait(self, timeout=None): return self.code
    def kill(self): self.code = -9


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, 'camera.sock')
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(self.path)
        self.listener.listen(5)
        self.listener.settimeout(1)
        self.done = threading.Event()
        self.server_errors = []
        self.server = None
        self.stream = None

    def tearDown(self):
        if self.stream is not None:
            try: self.stream.stop()
            except RuntimeError:
                if self.stream.error is None: raise
        self.done.set()
        self.listener.close()
        if self.server: self.server.join(2)
        self.temp.cleanup()
        self.assertFalse(self.server and self.server.is_alive())
        if self.server_errors: raise self.server_errors[0]

    def run_stream(self, serve, **options):
        stream = self.stream = PiVideoStream(socket_path=self.path, width=2, height=2,
                                             connect_timeout=.15, frame_timeout=.15,
                                             **options)
        stream._owner = Owner()
        stream.is_stopped = False
        def target():
            try: serve(stream)
            except (OSError, TimeoutError) as exc:
                if not self.done.is_set(): self.server_errors.append(exc)
            except Exception as exc: self.server_errors.append(exc)
        self.server = threading.Thread(target=target, daemon=True)
        self.server.start()
        stream._thread = threading.Thread(target=stream._update, daemon=True)
        stream._thread.start()
        return stream

    def wait_for(self, predicate, timeout=2):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline: time.sleep(.005)
        self.assertTrue(predicate())

    def assert_partial_eof_recovers(self, cut):
        def serve(stream):
            with self.listener.accept()[0] as peer: peer.sendall(packet()[:cut])
            with self.listener.accept()[0] as peer:
                peer.sendall(packet(9)); self.done.wait(1)
        stream = self.run_stream(serve)
        self.wait_for(lambda: stream.frames_received == 1)
        self.assertEqual(stream.sequence, 9)
        self.assertEqual(stream.frame.tobytes(), bytes(range(12)))
        self.assertEqual(stream.reconnects, 1)
        self.assertIsNone(stream.error)

    def test_partial_header_eof_reconnects_at_fresh_header(self):
        self.assert_partial_eof_recovers(5)

    def test_partial_payload_eof_reconnects_at_fresh_header(self):
        self.assert_partial_eof_recovers(27)

    def test_owner_exit_is_fatal_without_reconnect(self):
        def serve(stream):
            with self.listener.accept()[0] as peer:
                stream._owner.code = 17
                peer.sendall(packet()[:5])
        stream = self.run_stream(serve)
        self.wait_for(lambda: stream.is_stopped)
        self.assertIn('owner exited', str(stream.error))
        self.assertEqual(stream.reconnects, 0)

    def test_stop_while_reconnecting_is_prompt_and_not_error(self):
        def serve(stream):
            with self.listener.accept()[0] as peer: peer.sendall(packet()[:5])
            self.listener.close()
        stream = self.run_stream(serve)
        self.wait_for(lambda: stream.reconnects == 1)
        started = time.monotonic(); stream.stop()
        self.assertLess(time.monotonic()-started, .5)
        self.assertIsNone(stream.error)
        self.assertTrue(stream.is_stopped)

    def test_sustained_eof_exhausts_retry_budget(self):
        def serve(stream):
            for _ in range(3):
                with self.listener.accept()[0] as peer: peer.sendall(packet()[:5])
        stream = self.run_stream(serve, reconnect_attempts=2)
        self.wait_for(lambda: stream.is_stopped)
        self.assertIn('retry budget exhausted', str(stream.error))
        self.assertEqual(stream.reconnects, 2)
        self.assertEqual(stream.frames_received, 0)

    def test_stalled_frame_has_deadline_even_without_eof(self):
        def serve(stream):
            with self.listener.accept()[0] as peer:
                peer.sendall(packet()[:5]); self.done.wait(1)
        stream = self.run_stream(serve, reconnect_attempts=0)
        self.wait_for(lambda: stream.is_stopped)
        self.assertIsInstance(stream.error.__cause__, TimeoutError)
        self.assertIn('frame stalled', str(stream.error.__cause__))

    def test_complete_frame_resets_consecutive_failure_budget(self):
        def serve(stream):
            with self.listener.accept()[0] as peer: peer.sendall(packet()[:5])
            with self.listener.accept()[0] as peer: peer.sendall(packet(11)+packet()[:5])
            with self.listener.accept()[0] as peer:
                peer.sendall(packet(12)); self.done.wait(1)
        stream = self.run_stream(serve, reconnect_attempts=1)
        self.wait_for(lambda: stream.frames_received == 2)
        self.assertEqual(stream.sequence, 12)
        self.assertEqual(stream.reconnects, 2)
        self.assertIsNone(stream.error)


if __name__ == '__main__': unittest.main()

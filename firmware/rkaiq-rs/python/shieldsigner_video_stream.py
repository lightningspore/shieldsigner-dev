"""Opt-in PiVideoStream replacement for the Rust camera socket (no vendor SDK).

The camera owner must already be running with SHIELDSIGNER_CAMERA_SOCKET set.
Returns Pillow RGB images, as accepted by SeedSigner's Camera.read_video_stream.
Does not change boot services or start a second owner of the V4L2 nodes.
"""
import os
import socket
import struct
import threading
import time

from PIL import Image


class PiVideoStream:
    def __init__(self, socket_path=None, width=640, height=480, connect_timeout=10):
        self.socket_path = socket_path or os.environ.get(
            "SHIELDSIGNER_CAMERA_SOCKET", "/tmp/shieldsigner-camera.sock"
        )
        self.width, self.height = width, height
        self.connect_timeout = connect_timeout
        self.frame = None
        self.sequence = None
        self.frames_received = 0
        self.error = None
        self.is_stopped = True
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._socket = None
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Camera reader is already running")
        self._stop.clear()
        self.frame = self.sequence = self.error = None
        self.frames_received = 0
        self.is_stopped = False
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return self

    def _receive(self, connection, size):
        data = bytearray()
        while len(data) < size and not self._stop.is_set():
            try:
                chunk = connection.recv(size - len(data))
            except socket.timeout:
                continue
            if not chunk:
                raise EOFError("Rust camera stream ended")
            data.extend(chunk)
        if self._stop.is_set():
            raise InterruptedError("Camera reader stopped")
        return bytes(data)

    def _update(self):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(0.2)
        with self._lock:
            self._socket = connection
        try:
            deadline = time.monotonic() + self.connect_timeout
            while not self._stop.is_set():
                try:
                    connection.connect(self.socket_path)
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Rust camera socket did not become ready")
                    self._stop.wait(0.05)
            while not self._stop.is_set():
                magic, width, height, sequence, size = struct.unpack(
                    "<8sIIII", self._receive(connection, 24)
                )
                if magic != b"SSRGB001" or (width, height) != (self.width, self.height):
                    raise ValueError("Unexpected camera protocol or dimensions")
                if size != width * height * 3 or size > 4096 * 4096 * 3:
                    raise ValueError("Invalid RGB payload length")
                frame = Image.frombytes("RGB", (width, height), self._receive(connection, size))
                with self._lock:
                    self.frame, self.sequence = frame, sequence
                    self.frames_received += 1
        except Exception as exc:
            if not self._stop.is_set():
                with self._lock:
                    self.error = exc
        finally:
            with self._lock:
                self._socket = None
            connection.close()
            self.is_stopped = True

    def read(self):
        with self._lock:
            if self.error is not None:
                raise RuntimeError("Rust camera reader failed") from self.error
            return self.frame

    def stop(self):
        self._stop.set()
        with self._lock:
            if self._socket:
                try:
                    self._socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
        if self._thread:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                raise TimeoutError("Camera reader failed to stop")

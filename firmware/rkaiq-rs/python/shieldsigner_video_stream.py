"""Opt-in PiVideoStream replacement for the Rust camera socket (no vendor SDK).

Use an existing camera socket, or set SHIELDSIGNER_CAMERA_CONFIG to a JSON
configuration so start/stop owns the Rust process for each camera session.
Returns Pillow RGB images, as accepted by SeedSigner's Camera.read_video_stream.
Does not change boot services or start a second owner of the V4L2 nodes.
"""
import json
import os
import select
import socket
import struct
import subprocess
import tempfile
import threading
import time

from PIL import Image


class PiVideoStream:
    def __init__(self, socket_path=None, width=640, height=480, connect_timeout=10, owner_config=None):
        self.socket_path = socket_path or os.environ.get(
            "SHIELDSIGNER_CAMERA_SOCKET", "/tmp/shieldsigner-camera.sock"
        )
        if owner_config is None and os.environ.get("SHIELDSIGNER_CAMERA_CONFIG"):
            with open(os.environ["SHIELDSIGNER_CAMERA_CONFIG"]) as source:
                owner_config = json.load(source)
        if owner_config is not None:
            required = {"binary", "plan", "iq", "parameters", "image", "statistics", "output_directory"}
            if not isinstance(owner_config, dict) or set(owner_config) != required:
                raise ValueError("Camera owner configuration must contain exactly: " + ", ".join(sorted(required)))
            if any(not isinstance(value, str) or not value for value in owner_config.values()):
                raise ValueError("Camera owner paths must be nonempty strings")
        self.owner_config = owner_config
        self.session_directory = None
        self.owner_exit_code = None
        self._owner = None
        self._owner_log = None
        self._ready_fd = None
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
        if self._owner is not None and self._owner.poll() is None:
            raise RuntimeError("Previous camera owner has not stopped")
        self._stop.clear()
        self.frame = self.sequence = self.error = None
        self.frames_received = 0
        if self.owner_config is not None:
            config = self.owner_config
            self.session_directory = tempfile.mkdtemp(prefix="camera-", dir=config["output_directory"])
            self.socket_path = os.path.join(self.session_directory, "camera.sock")
            self.owner_exit_code = None
            self._owner_log = open(os.path.join(self.session_directory, "owner.log"), "xb")
            command = [config["binary"], "stream-sc3336", config["plan"], config["iq"],
                       config["parameters"], config["image"], os.path.join(self.session_directory, "frame"),
                       config["statistics"], self.socket_path]
            ready_read, ready_write = os.pipe()
            self._ready_fd = ready_read
            try:
                environment = dict(os.environ, SHIELDSIGNER_CAMERA_PARENT_PID=str(os.getpid()),
                                   SHIELDSIGNER_CAMERA_READY_FD=str(ready_write))
                self._owner = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                               stdout=self._owner_log, stderr=self._owner_log,
                                               env=environment, start_new_session=True, pass_fds=(ready_write,))
            except Exception:
                os.close(ready_read)
                self._ready_fd = None
                self._owner_log.close()
                self._owner_log = None
                self.is_stopped = True
                raise
            finally:
                os.close(ready_write)
        self.is_stopped = False
        self._thread = threading.Thread(target=self._update, daemon=True)
        try:
            self._thread.start()
        except Exception:
            self._finish_owner()
            self.is_stopped = True
            raise
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
        connection = None
        try:
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.settimeout(0.2)
            with self._lock:
                self._socket = connection
            if self._ready_fd is not None:
                ready = self._ready_fd
                self._ready_fd = None
                try:
                    if not select.select([ready], [], [], 2)[0] or os.read(ready, 1) != b"1":
                        raise RuntimeError("Rust owner did not arm managed shutdown")
                finally:
                    os.close(ready)
            deadline = time.monotonic() + self.connect_timeout
            while not self._stop.is_set():
                try:
                    connection.connect(self.socket_path)
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    if self._owner is not None and self._owner.poll() is not None:
                        raise RuntimeError("Rust camera owner exited before its socket was ready")
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
            if connection is not None:
                connection.close()
            try:
                self._finish_owner()
            except Exception as exc:
                with self._lock:
                    if self.error is None:
                        self.error = exc
            self.is_stopped = True

    def _finish_owner(self):
        try:
            if self._owner is not None:
                if self._owner.poll() is None:
                    self._owner.terminate()
                try:
                    self.owner_exit_code = self._owner.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._owner.kill()
                    self.owner_exit_code = self._owner.wait(timeout=2)
                    raise TimeoutError("Rust camera owner required forced termination")
                if self.owner_exit_code != 0:
                    raise RuntimeError("Rust camera owner exited with code {} (see owner.log)".format(self.owner_exit_code))
        finally:
            if self._ready_fd is not None:
                os.close(self._ready_fd)
                self._ready_fd = None
            if self._owner_log is not None:
                self._owner_log.close()
                self._owner_log = None

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
            self._thread.join(timeout=8)
            if self._thread.is_alive():
                raise TimeoutError("Camera reader failed to stop")
        if self.owner_exit_code is not None and self.owner_exit_code != 0:
            raise RuntimeError("Rust camera owner did not stop cleanly (see owner.log)")

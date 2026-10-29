"""Opt-in PiVideoStream replacement for the Rust camera socket (no vendor SDK).

Use an existing camera socket, or set SHIELDSIGNER_CAMERA_CONFIG to a JSON
configuration so start/stop owns the Rust process for each camera session.
Returns Pillow RGB images, or exact NV12 Y-plane L images when explicitly
requested by the small-RAM video adapter.
Does not change boot services or start a second owner of the V4L2 nodes.
"""
import json
import math
import os
import select
import socket
import struct
import subprocess
import tempfile
import threading
import time

from PIL import Image
from shieldsigner_process_log import ProcessLog, record_finished_session


def diagnostic_log_policy():
    """Snapshot explicit diagnostic policy once for each managed session."""
    full = os.environ.get("SHIELDSIGNER_CAMERA_LOG_FULL") == "1"
    options = {"full": full}
    small = os.environ.get("SHIELDSIGNER_SMALL_RAM") == "1" and not full
    if small:
        options.update(head_bytes=16 * 1024, tail_bytes=48 * 1024)
    return options, 1 if small else 3


class PiVideoStream:
    def __init__(self, socket_path=None, width=640, height=480, connect_timeout=10, owner_config=None, consumer_framerate=None, transport="rgb", frame_timeout=3.0, reconnect_attempts=3):
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
        if consumer_framerate is not None:
            if (not isinstance(consumer_framerate, (int, float)) or
                    isinstance(consumer_framerate, bool) or
                    not math.isfinite(consumer_framerate) or not 0 < consumer_framerate <= 120):
                raise ValueError("Consumer frame rate must be finite and within (0, 120]")
        if (isinstance(frame_timeout, bool) or not isinstance(frame_timeout, (int, float))
                or not math.isfinite(frame_timeout) or frame_timeout <= 0):
            raise ValueError("Frame timeout must be finite and positive")
        if isinstance(reconnect_attempts, bool) or not isinstance(reconnect_attempts, int) or not 0 <= reconnect_attempts <= 10:
            raise ValueError("Reconnect attempts must be an integer within [0, 10]")
        self.frame_timeout = frame_timeout
        self.reconnect_attempts = reconnect_attempts
        self.reconnects = 0
        self.consumer_frame_period = 0 if consumer_framerate is None else 1 / consumer_framerate
        if transport not in ("rgb", "nv12"):
            raise ValueError("Camera transport must be rgb or nv12")
        self.transport = transport
        self.owner_config = owner_config
        self.session_directory = None
        self.owner_exit_code = None
        self._owner = None
        self._owner_log = None
        self.log_info = None
        self._log_keep = 3
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
        self._frame_ready = threading.Condition(self._lock)
        self._consumer = threading.local()
        self._read_epoch = 0
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
        self.reconnects = 0
        self._read_epoch += 1
        if self.owner_config is not None:
            config = self.owner_config
            os.makedirs(config["output_directory"], exist_ok=True)
            self.session_directory = tempfile.mkdtemp(prefix="camera-", dir=config["output_directory"])
            self.socket_path = os.path.join(self.session_directory, "camera.sock")
            self.owner_exit_code = None
            self._owner = None
            log_options, self._log_keep = diagnostic_log_policy()
            self._owner_log = ProcessLog(os.path.join(self.session_directory, "owner.log"), **log_options)
            command = [config["binary"], "stream-sc3336", config["plan"], config["iq"],
                       config["parameters"], config["image"], os.path.join(self.session_directory, "frame"),
                       config["statistics"], self.socket_path]
            ready_read, ready_write = os.pipe()
            self._ready_fd = ready_read
            try:
                environment = dict(os.environ, SHIELDSIGNER_CAMERA_PARENT_PID=str(os.getpid()),
                                   SHIELDSIGNER_CAMERA_READY_FD=str(ready_write))
                if self.transport == "nv12":
                    environment["SHIELDSIGNER_CAMERA_STREAM_FORMAT"] = "nv12"
                else:
                    environment["SHIELDSIGNER_CAMERA_STREAM_FORMAT"] = "rgb"
                self._owner = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               env=environment, start_new_session=True, pass_fds=(ready_write,))
                self._owner_log.start(self._owner.stdout)
            except Exception:
                self._finish_owner()
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

    def _check_owner_alive(self):
        if self._owner is not None and self._owner.poll() is not None:
            raise RuntimeError("Rust camera owner exited (see owner.log)")

    def _connect(self, deadline):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(min(0.2, self.frame_timeout))
        with self._lock:
            self._socket = connection
        try:
            while not self._stop.is_set():
                self._check_owner_alive()
                try:
                    connection.connect(self.socket_path)
                    return connection
                except (FileNotFoundError, ConnectionRefusedError, socket.timeout):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Rust camera socket did not become ready")
                    self._stop.wait(0.05)
            raise InterruptedError("Camera reader stopped")
        except Exception:
            connection.close()
            with self._lock:
                if self._socket is connection:
                    self._socket = None
            raise

    def _receive(self, connection, size, deadline):
        data = bytearray()
        while len(data) < size and not self._stop.is_set():
            self._check_owner_alive()
            if time.monotonic() >= deadline:
                raise TimeoutError("Rust camera frame stalled")
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

    def _validate_frame_header(self, magic, width, height, size):
        expected_magic = b"SSNV12F1" if self.transport == "nv12" else b"SSRGB001"
        if magic != expected_magic or (width, height) != (self.width, self.height):
            raise ValueError("Unexpected camera protocol or dimensions")
        if not 0 < width <= 4096 or not 0 < height <= 4096:
            raise ValueError("Invalid camera dimensions")
        if self.transport == "nv12":
            if width % 2 or height % 2:
                raise ValueError("NV12 dimensions must be even")
            expected = width * height * 3 // 2
        else:
            expected = width * height * 3
        if size != expected:
            raise ValueError("Invalid camera payload length")

    def _frame_from_payload(self, width, height, payload):
        # Native SSNV12F1 is packed Y followed by interleaved UV. Preserve the
        # full-resolution Y bytes exactly for QR; no RGB expansion/chroma copy.
        self._validate_frame_header(b"SSNV12F1" if self.transport == "nv12" else b"SSRGB001", width, height, len(payload))
        if self.transport == "nv12":
            return Image.frombytes("L", (width, height), payload[:width * height])
        return Image.frombytes("RGB", (width, height), payload)

    def _update(self):
        connection = None
        try:
            if self._ready_fd is not None:
                ready = self._ready_fd
                self._ready_fd = None
                try:
                    if not select.select([ready], [], [], 2)[0] or os.read(ready, 1) != b"1":
                        raise RuntimeError("Rust owner did not arm managed shutdown")
                finally:
                    os.close(ready)
            failures = 0
            connected_once = False
            while not self._stop.is_set():
                try:
                    if connection is None:
                        timeout = min(self.connect_timeout, self.frame_timeout) if connected_once else self.connect_timeout
                        connection = self._connect(time.monotonic() + timeout)
                        connected_once = True
                    # One deadline covers the entire header and body. A trickle
                    # of partial bytes cannot keep a dead frame alive forever.
                    deadline = time.monotonic() + self.frame_timeout
                    magic, width, height, sequence, size = struct.unpack(
                        "<8sIIII", self._receive(connection, 24, deadline)
                    )
                    self._validate_frame_header(magic, width, height, size)
                    frame = self._frame_from_payload(width, height, self._receive(connection, size, deadline))
                except (EOFError, TimeoutError, ConnectionResetError, ConnectionAbortedError) as exc:
                    if self._stop.is_set():
                        raise InterruptedError("Camera reader stopped") from exc
                    # Only a live managed owner can promise a fresh connection
                    # begins with a new header. Never resync inside partial data.
                    self._check_owner_alive()
                    if self._owner is None or not connected_once:
                        raise
                    failures += 1
                    if failures > self.reconnect_attempts:
                        raise RuntimeError("Rust camera transport retry budget exhausted") from exc
                    self.reconnects += 1
                    if connection is not None:
                        connection.close()
                        with self._lock:
                            if self._socket is connection:
                                self._socket = None
                        connection = None
                    self._stop.wait(0.05)
                    continue
                failures = 0
                with self._lock:
                    self.frame, self.sequence = frame, sequence
                    self.frames_received += 1
                    self._frame_ready.notify_all()
        except Exception as exc:
            if not self._stop.is_set():
                with self._lock:
                    self.error = exc
                    self._frame_ready.notify_all()
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
            with self._frame_ready:
                self.is_stopped = True
                self._frame_ready.notify_all()

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
                try:
                    self.log_info = self._owner_log.finish()
                    if self._owner is not None:
                        record_finished_session(self.session_directory, self.owner_exit_code, self.log_info, keep=self._log_keep)
                finally:
                    self._owner_log = None

    def read(self, preview=False, display=False):
        # Decode and preview are independent consumers. Each thread observes a
        # generation once; neither steals the other's frame. Pixel conversion
        # remains the application's responsibility.
        deadline = time.monotonic() + 0.2
        with self._frame_ready:
            while True:
                if self.error is not None:
                    raise RuntimeError("Rust camera reader failed") from self.error
                if self._stop.is_set() or self.is_stopped:
                    return None
                generation = (self._read_epoch, self.frames_received)
                now = time.monotonic()
                previous = getattr(self._consumer, "generation", None)
                # A session restart resets both generation and pacing. Late
                # readers take the current latest frame, never catch up a queue.
                due = getattr(self._consumer, "next_read", 0) if previous and previous[0] == self._read_epoch else 0
                fresh = self.frame is not None and previous != generation
                if fresh and now >= due:
                    self._consumer.generation = generation
                    self._consumer.next_read = now + self.consumer_frame_period
                    return self.frame
                remaining = deadline - now
                if remaining <= 0:
                    return None
                self._frame_ready.wait(min(remaining, due-now) if fresh and due > now else remaining)

    def stop(self):
        self._stop.set()
        with self._frame_ready:
            self._frame_ready.notify_all()
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

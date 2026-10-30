"""Persistent native QR client: Pillow pixels in, unchanged binary payload out."""
import atexit
import hashlib
import os
from pathlib import Path
import socket
import struct
import subprocess
import threading
import time


class NativeQrReader:
    def __init__(self, binary, timeout=5):
        self.binary = Path(binary)
        if not self.binary.is_absolute() or not self.binary.is_file() or not os.access(self.binary, os.X_OK):
            raise ValueError("Native QR reader must be an absolute executable path")
        self.timeout = timeout
        self._lock = threading.RLock()
        self._process = self._socket = None
        # The ARM worker is several MiB. Hash incrementally so startup does
        # not allocate a worker-sized Python bytes object on the 64 MiB Mini.
        digest = hashlib.sha256()
        with self.binary.open("rb") as worker:
            for chunk in iter(lambda: worker.read(65536), b""):
                digest.update(chunk)
        self.stats = {"kind": "native-zxing-3.1.1-local-average", "binarySha256": digest.hexdigest(),
                      "starts": 0, "calls": 0, "decoded": 0, "errors": 0, "lastRoundTripSeconds": None,
                      "lastExitCode": None}
        atexit.register(self.close)

    def _receive(self, size):
        result = bytearray()
        while len(result) < size:
            data = self._socket.recv(size-len(result))
            if not data:
                raise RuntimeError("Native QR reader closed its connection")
            result.extend(data)
        return bytes(result)

    def _start(self):
        if self._process is not None and self._process.poll() is None:
            return
        self.close()
        parent, child = socket.socketpair()
        try:
            parent.settimeout(self.timeout)
            self._process = subprocess.Popen([str(self.binary)], stdin=child, stdout=child,
                                             stderr=subprocess.DEVNULL, start_new_session=True)
            self._socket = parent
            if self._receive(8) != b"SSQR001\n":
                raise RuntimeError("Unsupported native QR protocol")
            self.stats["starts"] += 1
        except BaseException:
            parent.close()
            self.close()
            raise
        finally:
            child.close()

    def decode(self, image):
        with self._lock:
            width, height = image.size
            if not 0 < width <= 1920 or not 0 < height <= 1920 or width*height > 2073600:
                raise ValueError("Native QR image dimensions exceed protocol bounds")
            started = time.monotonic()
            try:
                self._start()
                pixels = image.convert("L").tobytes()
                self._socket.sendall(struct.pack("<4sII", b"QRI1", width, height)+pixels)
                magic, size = struct.unpack("<4sI", self._receive(8))
                if magic != b"QRO1" or size != 0xffffffff and size > 8192:
                    raise RuntimeError("Malformed native QR response")
                data = None if size == 0xffffffff else self._receive(size)
                self.stats["calls"] += 1
                self.stats["decoded"] += data is not None
                self.stats["lastRoundTripSeconds"] = time.monotonic()-started
                return data
            except BaseException:
                self.stats["errors"] += 1
                self.close()
                raise

    def close(self):
        with self._lock:
            if self._socket is not None:
                self._socket.close()
                self._socket = None
            process, self._process = self._process, None
            if process is not None:
                try:
                    process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=.5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                self.stats["lastExitCode"] = process.returncode


class RustTransportQrReader(NativeQrReader):
    """Retain executable validation/hash policy; delegate IPC and pixels to Rust."""
    def __init__(self, binary, timeout=5):
        # No child is spawned by this constructor. The parent establishes the
        # same streaming executable digest and registers dynamic self.close.
        self._native_worker = None
        super().__init__(binary, timeout)
        from shieldsigner_lcd import QrWorker
        self._native_worker = QrWorker(str(self.binary), timeout)
        self.stats["transport"] = "rust"

    def _update_statistics(self):
        values = self._native_worker.statistics()
        for key, value in zip(("starts", "calls", "decoded", "errors", "lastRoundTripSeconds", "lastExitCode"), values):
            self.stats[key] = value

    def decode(self, image):
        from shieldsigner_lcd import NativeFrame
        with self._lock:
            try:
                if isinstance(image, NativeFrame):
                    return self._native_worker.decode_frame(image)
                width, height = image.size
                return self._native_worker.decode_luma(image.convert("L").tobytes(), width, height)
            finally:
                self._update_statistics()

    def close(self):
        with self._lock:
            if self._native_worker is not None:
                self._native_worker.close()
                self._update_statistics()

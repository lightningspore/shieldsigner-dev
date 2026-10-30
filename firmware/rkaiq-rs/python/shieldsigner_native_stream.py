"""Native frame reception with the existing managed camera ownership policy.

Python coordinates owner readiness/reconnect/termination; Rust receives pixels,
retains latest frames, paces consumers and cancels blocked socket reads.
"""
import select
import os
import threading
import time
from shieldsigner_video_stream import PiVideoStream as ManagedStream


class NativeVideoStream(ManagedStream):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from shieldsigner_lcd import FrameReceiver
        self._receiver_class = FrameReceiver
        self._native_receiver = None
        self._native_consumers = {}

    def start(self):
        self._native_consumers.clear()
        self._native_receiver = None
        return super().start()

    def _update(self):
        connection = receiver = None
        completed = 0
        try:
            if self._ready_fd is not None:
                ready, self._ready_fd = self._ready_fd, None
                try:
                    if not select.select([ready], [], [], 2)[0] or os.read(ready, 1) != b"1":
                        raise RuntimeError("Rust owner did not arm managed shutdown")
                finally:
                    os.close(ready)
            failures = 0
            connected_once = False
            while not self._stop.is_set():
                timeout = min(self.connect_timeout, self.frame_timeout) if connected_once else self.connect_timeout
                connection = self._connect(time.monotonic() + timeout)
                connected_once = True
                receiver = self._receiver_class(connection.fileno(), self.width, self.height,
                                                self.transport, self.frame_timeout,
                                                1 / self.consumer_frame_period if self.consumer_frame_period else 120)
                with self._frame_ready:
                    self._native_receiver = receiver
                    self._frame_ready.notify_all()
                received = 0
                try:
                    while not self._stop.wait(.02):
                        self._check_owner_alive()
                        generation, dropped, stopped = receiver.statistics()
                        if generation > received:
                            received = generation
                            failures = 0
                        self.frames_received = completed + received
                        if stopped:
                            # Surface native protocol/EOF/deadline failures.
                            receiver.read(7, 0)
                            raise EOFError("Native camera receiver stopped")
                except OSError as exc:
                    # A fresh connection is safe only with a live managed owner.
                    self._check_owner_alive()
                    if self._owner is None or not connected_once:
                        raise
                    failures += 1
                    if failures > self.reconnect_attempts:
                        raise RuntimeError("Rust camera transport retry budget exhausted") from exc
                    self.reconnects += 1
                finally:
                    with self._frame_ready:
                        self._native_receiver = None
                        self._frame_ready.notify_all()
                    receiver.close()
                    receiver = None
                    completed += received
                    connection.close()
                    connection = None
                    with self._lock:
                        self._socket = None
                self._stop.wait(.05)
        except Exception as exc:
            if not self._stop.is_set():
                with self._frame_ready:
                    self.error = exc
                    self._frame_ready.notify_all()
        finally:
            if receiver is not None:
                receiver.close()
            if connection is not None:
                connection.close()
            with self._frame_ready:
                self._native_receiver = self._socket = None
            try:
                self._finish_owner()
            except Exception as exc:
                with self._lock:
                    if self.error is None:
                        self.error = exc
            with self._frame_ready:
                self.is_stopped = True
                self._frame_ready.notify_all()

    def read(self, preview=False, display=False):
        deadline = time.monotonic() + .2
        with self._frame_ready:
            ident = threading.get_ident()
            if ident not in self._native_consumers:
                if len(self._native_consumers) >= 7:
                    raise RuntimeError("Native camera consumer limit exceeded")
                self._native_consumers[ident] = len(self._native_consumers)
            consumer = self._native_consumers[ident]
            while self._native_receiver is None:
                if self.error is not None:
                    raise RuntimeError("Rust camera reader failed") from self.error
                if self._stop.is_set() or self.is_stopped:
                    return None
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._frame_ready.wait(remaining)
            receiver = self._native_receiver
        try:
            return receiver.read(consumer, max(0, deadline - time.monotonic()))
        except OSError:
            # Coordinator determines whether owner/retry policy allows recovery.
            # A failed receiver never resynchronizes within partial frame data.
            if self._owner is None:
                raise
            self._stop.wait(.02)
            with self._lock:
                if self.error is not None:
                    raise RuntimeError("Rust camera reader failed") from self.error
            return None

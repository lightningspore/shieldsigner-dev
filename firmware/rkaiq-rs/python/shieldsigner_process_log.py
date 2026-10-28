"""Disk-bounded camera diagnostics; keep startup and the newest shutdown records."""
import json
import os
from pathlib import Path
import shutil
import threading

HEAD_BYTES = 256 * 1024
TAIL_BYTES = 768 * 1024
MARKER = '.shieldsigner-finished.json'
OWNER = 'shieldsigner-managed-session-v1'


class ProcessLog:
    def __init__(self, path, full=False, head_bytes=HEAD_BYTES, tail_bytes=TAIL_BYTES):
        if head_bytes <= 0 or tail_bytes <= 0:
            raise ValueError('Log bounds must be positive')
        self.path = Path(path)
        self.full = full
        self.head_limit, self.tail_limit = head_bytes, tail_bytes
        self.head_size = self.tail_size = self.tail_position = self.total = 0
        self.error_type = None
        self._file = self.path.open('xb+', buffering=0)
        self._pipe = self._thread = None
        self._finished = False

    def start(self, pipe):
        self._pipe = pipe
        self._thread = threading.Thread(target=self._drain, name='camera-log-drainer', daemon=True)
        try:
            self._thread.start()
        except Exception:
            self._thread = None
            pipe.close()
            raise

    def _write(self, data):
        remaining = memoryview(data)
        while remaining:
            written = self._file.write(remaining)
            if not written:
                raise OSError('Short camera log write')
            remaining = remaining[written:]

    def _append(self, data):
        self.total += len(data)
        if self.error_type is not None:
            return
        try:
            if self.full:
                self._write(data)
                return
            remaining = memoryview(data)
            if self.head_size < self.head_limit:
                size = min(len(remaining), self.head_limit-self.head_size)
                self._file.seek(self.head_size)
                self._write(remaining[:size])
                self.head_size += size
                remaining = remaining[size:]
            while remaining:
                size = min(len(remaining), self.tail_limit-self.tail_position)
                self._file.seek(self.head_limit+self.tail_position)
                self._write(remaining[:size])
                self.tail_position = (self.tail_position+size) % self.tail_limit
                self.tail_size = min(self.tail_limit, self.tail_size+size)
                remaining = remaining[size:]
        except OSError as exc:
            # Always continue draining the pipe: failed SD writes must not make
            # Rust block forever trying to print diagnostics.
            self.error_type = type(exc).__name__

    def _drain(self):
        try:
            while True:
                data = os.read(self._pipe.fileno(), 64 * 1024)
                if not data:
                    break
                self._append(data)
        except OSError as exc:
            self.error_type = type(exc).__name__
        finally:
            self._pipe.close()

    def finish(self):
        if self._finished:
            return self.summary()
        if self._thread is not None:
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                raise TimeoutError('Camera log pipe remained open after owner exit')
        try:
            if not self.full and self.error_type is None and self.tail_size:
                self._file.seek(self.head_limit)
                tail = self._file.read(self.tail_size)
                if self.tail_size == self.tail_limit:
                    tail = tail[self.tail_position:] + tail[:self.tail_position]
                omitted = self.total-self.head_size-len(tail)
                if omitted:
                    # A ring may start midway through a JSON line. Preserve
                    # complete following records, including the final status.
                    newline = tail.find(b'\n')
                    if newline >= 0:
                        tail = tail[newline+1:]
                    omitted = self.total-self.head_size-len(tail)
                    marker = ('\n[shieldsigner: {} bytes omitted; bounded startup/tail log]\n'.format(omitted)).encode()
                else:
                    marker = b''
                self._file.seek(self.head_size)
                self._write(marker)
                self._write(tail)
                self._file.truncate()
        except OSError as exc:
            self.error_type = type(exc).__name__
        finally:
            self._file.close()
            self._finished = True
        return self.summary()

    def summary(self):
        return {'fullLog': self.full, 'bytesReceived': self.total,
                'maxRetainedPayloadBytes': None if self.full else self.head_limit+self.tail_limit,
                'errorType': self.error_type}


def record_finished_session(directory, owner_exit_code, info, keep=3):
    """Retire only explicitly owned, finished bounded-mode sessions in this root."""
    directory = Path(directory)
    record = {'owner': OWNER, 'finished': True, 'ownerExitCode': owner_exit_code, **info}
    try:
        with (directory / MARKER).open('x') as output:
            json.dump(record, output)
    except OSError:
        return  # Logging/retention must not prevent camera shutdown.
    if info['fullLog']:
        return
    candidates = []
    for path in directory.parent.iterdir():
        if path == directory or not path.name.startswith('camera-') or path.is_symlink() or not path.is_dir():
            continue
        try:
            marker = path / MARKER
            previous = json.loads(marker.read_text())
            if previous.get('owner') == OWNER and previous.get('finished') is True and previous.get('fullLog') is False:
                candidates.append((marker.stat().st_mtime_ns, path))
        except (OSError, ValueError):
            continue
    for _, path in sorted(candidates, key=lambda item: item[0], reverse=True)[max(0, keep-1):]:
        try:
            shutil.rmtree(path)
        except OSError:
            pass

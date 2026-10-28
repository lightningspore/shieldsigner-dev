#!/usr/bin/env python3
"""Local real-camera preview: SSRGB001 TCP input, in-memory JPEG HTTP output.

Run with: uv run --python 3.13 --with pillow python server.py --camera-port 8766
Root owns the camera process and adb forwarding; this server starts neither.
"""

import argparse
from collections import deque
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import ipaddress
import json
from pathlib import Path
import socket
import struct
import threading
import time
from urllib.parse import urlsplit

from PIL import Image

HEADER = struct.Struct("<8sIIII")


def receive_exact(connection, count):
    data = bytearray()
    while len(data) < count:
        block = connection.recv(count - len(data))
        if not block:
            raise EOFError("Camera transport closed")
        data.extend(block)
    return bytes(data)


def read_frame(connection):
    magic, width, height, sequence, size = HEADER.unpack(
        receive_exact(connection, HEADER.size)
    )
    if magic != b"SSRGB001" or not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError("Invalid SSRGB001 frame header")
    if size != width * height * 3 or size > 32 * 1024 * 1024:
        raise ValueError("Invalid SSRGB001 RGB payload length")
    return width, height, sequence, receive_exact(connection, size)


class Camera:
    def __init__(self, args):
        self.args = args
        self.condition = threading.Condition()
        self.stop = threading.Event()
        self.jpeg = None
        self.width = self.height = self.sequence = None
        self.received = 0
        self.last_monotonic = None
        self.last_wall = None
        self.times = deque(maxlen=90)
        self.transport = False
        self.error = None
        self.thread = threading.Thread(
            target=self.run, name="camera-reader", daemon=True
        )

    def telemetry(self):
        if not self.args.metadata_file:
            return {"available": False}
        try:
            with self.args.metadata_file.open("rb") as source:
                data = source.read(65537)
            if len(data) > 65536:
                raise ValueError("Metadata exceeds bound")
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError("Metadata must be an object")
            return {**value, "available": True}
        except (OSError, ValueError):
            return {"available": False, "error": "Metadata unavailable"}

    def status(self):
        now = time.monotonic()
        with self.condition:
            age = None if self.last_monotonic is None else now - self.last_monotonic
            connected = (
                self.transport and age is not None and age <= self.args.stale_seconds
            )
            times = [t for t in self.times if now - t <= 5]
            fps = (
                (len(times) - 1) / (times[-1] - times[0])
                if len(times) > 1 and times[-1] > times[0]
                else 0.0
            )
            result = dict(
                connected=connected,
                state="live"
                if connected
                else "connecting"
                if self.transport and age is None
                else "disconnected",
                source="Luckfox / Rust SSRGB001",
                frame_age_ms=None if age is None else round(age * 1000),
                frames_received=self.received,
                sequence=self.sequence,
                width=self.width,
                height=self.height,
                fps=round(fps, 2) if connected else 0.0,
                error=self.error,
                last_frame_at=self.last_wall,
                timestamp_basis="desktop reception",
                images_saved=False,
            )
        result["telemetry"] = self.telemetry()
        if isinstance(result["telemetry"].get("modules"), (dict, list)):
            result["modules"] = result["telemetry"]["modules"]
        return result

    def snapshot(self):
        with self.condition:
            if (
                not self.transport
                or self.last_monotonic is None
                or time.monotonic() - self.last_monotonic > self.args.stale_seconds
            ):
                return None
            return self.received, self.jpeg

    def run(self):
        while not self.stop.is_set():
            try:
                with socket.create_connection(
                    (self.args.camera_host, self.args.camera_port), timeout=2
                ) as connection:
                    connection.settimeout(self.args.stale_seconds)
                    with self.condition:
                        self.transport = True
                    while not self.stop.is_set():
                        width, height, sequence, raw = read_frame(connection)
                        frame = Image.frombytes("RGB", (width, height), raw)
                        if self.args.rotate:
                            frame = frame.transpose(
                                {
                                    90: Image.Transpose.ROTATE_90,
                                    180: Image.Transpose.ROTATE_180,
                                    270: Image.Transpose.ROTATE_270,
                                }[self.args.rotate]
                            )
                        encoded = io.BytesIO()
                        frame.save(
                            encoded,
                            format="JPEG",
                            quality=self.args.jpeg_quality,
                            subsampling=0,
                        )
                        now = time.monotonic()
                        with self.condition:
                            self.jpeg = encoded.getvalue()
                            self.width, self.height = frame.size
                            self.sequence = sequence
                            self.received += 1
                            self.last_monotonic = now
                            self.last_wall = datetime.now(timezone.utc).isoformat()
                            self.times.append(now)
                            self.error = None
                            self.condition.notify_all()
            except (OSError, EOFError, ValueError) as exc:
                with self.condition:
                    self.transport = False
                    self.error = str(exc)[:200]
                    self.condition.notify_all()
                self.stop.wait(0.5)


def make_handler(camera, static_dir):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(static_dir), **kwargs)

        def log_message(self, format, *args):
            pass  # Status polling is intentionally quiet.

        def list_directory(self, path):
            self.send_error(404)
            return None

        def data(self, status, content_type, body):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/status.json":
                self.data(200, "application/json", json.dumps(camera.status()).encode())
            elif path == "/telemetry.json":
                self.data(
                    200, "application/json", json.dumps(camera.telemetry()).encode()
                )
            elif path == "/snapshot.jpg":
                latest = camera.snapshot()
                if latest is None:
                    self.data(
                        503, "application/json", b'{"error":"No fresh camera frame"}'
                    )
                else:
                    self.data(200, "image/jpeg", latest[1])
            elif path == "/stream.mjpg":
                latest = camera.snapshot()
                if latest is None:
                    self.data(
                        503, "application/json", b'{"error":"No fresh camera frame"}'
                    )
                    return
                self.send_response(200)
                self.send_header(
                    "Content-Type", "multipart/x-mixed-replace; boundary=frame"
                )
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                last = -1
                try:
                    while not camera.stop.is_set():
                        latest = camera.snapshot()
                        if latest is None:
                            return
                        number, jpeg = latest
                        if number != last:
                            self.wfile.write(
                                b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                + str(len(jpeg)).encode()
                                + b"\r\n\r\n"
                                + jpeg
                                + b"\r\n"
                            )
                            self.wfile.flush()
                            last = number
                        with camera.condition:
                            camera.condition.wait(timeout=0.5)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            elif path == "/" or Path(path).suffix.lower() in {
                ".html",
                ".css",
                ".js",
                ".svg",
                ".png",
                ".jpg",
                ".ico",
                ".woff2",
            }:
                super().do_GET()
            else:
                self.send_error(404)

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-host", default="127.0.0.1")
    parser.add_argument("--camera-port", type=int, default=8766)
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=8765)
    parser.add_argument(
        "--static-dir", type=Path, default=Path(__file__).resolve().parent
    )
    parser.add_argument("--metadata-file", type=Path)
    parser.add_argument("--stale-seconds", type=float, default=3.0)
    parser.add_argument("--jpeg-quality", type=int, choices=range(30, 96), default=85)
    parser.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0)
    args = parser.parse_args()
    try:
        loopback = (
            args.listen_host == "localhost"
            or ipaddress.ip_address(args.listen_host).is_loopback
        )
    except ValueError:
        loopback = False
    if not loopback:
        parser.error("The demo listens only on localhost")
    if not (0.5 <= args.stale_seconds <= 30) or not all(
        1 <= p <= 65535 for p in [args.listen_port, args.camera_port]
    ):
        parser.error("Invalid staleness limit or port")
    camera = Camera(args)
    server = ThreadingHTTPServer(
        (args.listen_host, args.listen_port), make_handler(camera, args.static_dir)
    )
    server.daemon_threads = True
    camera.thread.start()
    print(
        f"Real camera demo: http://{args.listen_host}:{args.listen_port} (SSRGB001 from {args.camera_host}:{args.camera_port})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        camera.stop.set()
        server.server_close()
        camera.thread.join(timeout=args.stale_seconds + 2)


if __name__ == "__main__":
    main()

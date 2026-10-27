"""Bounded real-board smoke test; run from the directory containing the adapter."""
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time

from shieldsigner_video_stream import PiVideoStream


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--socket", default="/tmp/shieldsigner-camera.sock")
    parser.add_argument("--stall-reader", action="store_true")
    parser.add_argument("--stop-signal", choices=["TERM", "INT"], default="TERM")
    parser.add_argument("--continuous", action="store_true", help="Stop stream-sc3336 gracefully after the reader sessions")
    parser.add_argument("--app-root", help="Exercise the installed Camera wrapper without launching the UI")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    report = {"sessions": [], "success": False}
    environment = dict(os.environ, SHIELDSIGNER_CAMERA_SOCKET=args.socket)
    camera_module = None
    if args.app_root:
        sys.path.insert(0, args.app_root)
        from seedsigner.hardware import camera as camera_module
    report["applicationCameraWrapper"] = bool(camera_module)
    reader = None
    images = []
    with open(args.output + ".log", "xb") as log:
        process = subprocess.Popen(command, env=environment, stdout=log, stderr=log)
        try:
            for index in range(2):
                reader = PiVideoStream(args.socket)
                application = None
                if camera_module:
                    camera_module.PiVideoStream = lambda: reader
                    application = camera_module.Camera.__new__(camera_module.Camera)
                    application._camera_rotation = 0
                    application.start_video_stream_mode()
                else:
                    reader.start()
                start = time.monotonic()
                seen = []
                while time.monotonic() - start < 8:
                    frame = application.read_video_stream(as_image=True) if application else reader.read()
                    if frame is not None and (not seen or seen[-1] != reader.sequence):
                        seen.append(reader.sequence)
                    time.sleep(0.01)
                frame = application.read_video_stream(as_image=True) if application else reader.read()
                report["lastReaderSamples"] = len(seen)
                assert frame is not None and len(seen) >= 20, "Insufficient live frames: {} samples, {} received".format(len(seen), reader.frames_received)
                assert all(a < b for a, b in zip(seen, seen[1:])), "Regressing frame sequence"
                images.append(frame)
                before = time.monotonic()
                if application:
                    application.stop_video_stream_mode()
                else:
                    reader.stop()
                report["sessions"].append({
                    "received": reader.frames_received, "sampled": len(seen),
                    "first": seen[0], "last": seen[-1], "mode": frame.mode,
                    "size": frame.size, "stopped": reader.is_stopped,
                    "stopSeconds": time.monotonic() - before,
                })
                reader = None
                time.sleep(0.4)
                if args.stall_reader and index == 0:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stalled:
                        stalled.connect(args.socket)
                        time.sleep(2.5)
                        stalled.settimeout(1)
                        while stalled.recv(65536):
                            pass
                    report["stalledReaderDisconnected"] = True
            if args.continuous:
                process.send_signal(signal.SIGINT if args.stop_signal == "INT" else signal.SIGTERM)
                report["stopSignal"] = args.stop_signal
            report["exitCode"] = process.wait(timeout=35)
            assert report["exitCode"] == 0, "Camera capture failed"
            assert not os.path.exists(args.socket), "Socket was not cleaned up"
            for index, frame in enumerate(images):
                frame.save(args.output + ".reader-{}.png".format(index))
            report["success"] = True
        except Exception as exc:
            report["error"] = str(exc)
            report["receivedBeforeError"] = reader.frames_received if reader else None
            raise
        finally:
            if reader:
                reader.stop()
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            with open(args.output + ".reader.json", "x") as output:
                json.dump(report, output, indent=2)
    print(json.dumps(report))


if __name__ == "__main__":
    main()

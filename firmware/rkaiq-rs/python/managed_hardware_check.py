"""Test application-owned Rust camera sessions on the real board; no boot edits."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

from shieldsigner_video_stream import PiVideoStream


def main():
    parser = argparse.ArgumentParser()
    for name in ["binary", "plan", "iq", "output-directory", "app-root", "report"]:
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    config = {"binary": args.binary, "plan": args.plan, "iq": args.iq,
              "parameters": "/dev/video20", "image": "/dev/video11",
              "statistics": "/dev/video19", "output_directory": args.output_directory}
    sys.path.insert(0, args.app_root)
    from seedsigner.hardware import camera as camera_module
    report = {"passed": False, "sessions": [], "binarySha256": digest(args.binary),
              "adapterSha256": digest(os.path.join(os.path.dirname(__file__), "shieldsigner_video_stream.py")),
              "iqSha256": digest(args.iq)}
    try:
        missing = dict(config, output_directory=args.report + ".missing/sessions")
        invalid = PiVideoStream(owner_config=missing)
        try:
            invalid.start()
        except FileNotFoundError:
            assert invalid.is_stopped and invalid._owner is None
            report["missingOutputDirectoryRejected"] = True
        else:
            raise AssertionError("Missing output directory was accepted")
        for session_index in range(2):
            reader = PiVideoStream(owner_config=config)
            camera_module.PiVideoStream = lambda: reader
            camera = camera_module.Camera.__new__(camera_module.Camera)
            camera._camera_rotation = 0
            start = time.monotonic()
            camera.start_video_stream_mode()
            seen = []
            first_frame = None
            collision_checked = False
            try:
                while first_frame is None or time.monotonic() - first_frame < 8:
                    frame = camera.read_video_stream(as_image=True)
                    if frame is not None:
                        if first_frame is None:
                            first_frame = time.monotonic()
                        if not seen or seen[-1] != reader.sequence:
                            seen.append(reader.sequence)
                    if session_index == 0 and first_frame and not collision_checked:
                        competing = PiVideoStream(owner_config=config).start()
                        failed = False
                        try:
                            deadline = time.monotonic() + 5
                            while time.monotonic() < deadline:
                                try:
                                    competing.read()
                                except RuntimeError:
                                    failed = True
                                    break
                                time.sleep(.02)
                        finally:
                            try:
                                competing.stop()
                            except RuntimeError:
                                pass
                        assert failed and competing.owner_exit_code != 0
                        with open(os.path.join(competing.session_directory, "owner.log")) as source:
                            assert "Another Rust camera owner is already running" in source.read()
                        report["competingOwner"] = {"rejectedBeforeReconfiguration": True,
                                                    "directory": competing.session_directory,
                                                    "exitCode": competing.owner_exit_code}
                        collision_checked = True
                    if time.monotonic() - start > 20:
                        raise TimeoutError("Managed session exceeded deadline")
                    time.sleep(0.01)
            finally:
                stop = time.monotonic()
                camera.stop_video_stream_mode()
            assert len(seen) >= 20 and all(a < b for a, b in zip(seen, seen[1:]))
            assert reader.owner_exit_code == 0 and reader.is_stopped
            assert not os.path.exists(reader.socket_path)
            report["sessions"].append({"directory": reader.session_directory,
                                       "firstFrameSeconds": first_frame - start,
                                       "samples": len(seen), "received": reader.frames_received,
                                       "first": seen[0], "last": seen[-1],
                                       "stopSeconds": time.monotonic() - stop,
                                       "ownerExitCode": reader.owner_exit_code})
        assert report["sessions"][0]["directory"] != report["sessions"][1]["directory"]
        early = PiVideoStream(owner_config=config).start()
        early_start = time.monotonic()
        early.stop()
        assert early.owner_exit_code == 0 and not os.path.exists(early.socket_path)
        report["earlyStop"] = {"directory": early.session_directory,
                               "ownerExitCode": early.owner_exit_code,
                               "seconds": time.monotonic() - early_start}
        # Exit a separate Python parent without running adapter.stop() or finally.
        child_report = args.report + ".parent-exit.json"
        code = (
            "import json,os,sys,time; from shieldsigner_video_stream import PiVideoStream; "
            "s=PiVideoStream(owner_config=json.loads(sys.argv[1])).start(); "
            "start=time.monotonic()\n"
            "while s.read() is None:\n"
            " if time.monotonic()-start>12: raise TimeoutError('No frame before parent exit')\n"
            " time.sleep(.02)\n"
            "with open(sys.argv[2],'x') as f: json.dump({'directory':s.session_directory,'ownerPid':s._owner.pid},f)\n"
            "os._exit(0)\n"
        )
        child = subprocess.run([sys.executable, "-c", code, json.dumps(config), child_report],
                               cwd=os.path.dirname(os.path.abspath(__file__)), timeout=20)
        assert child.returncode == 0
        with open(child_report) as source:
            parent_exit = json.load(source)
        deadline = time.monotonic() + 8
        while True:
            with open(os.path.join(parent_exit["directory"], "owner.log")) as source:
                events = []
                for line in source:
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        pass
            finished = [event for event in events if isinstance(event, dict) and event.get("event") == "first-frame-finished"]
            if finished:
                assert finished[-1]["success"]
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Rust owner did not finish after Python parent exit")
            time.sleep(.1)
        assert not os.path.exists(os.path.join(parent_exit["directory"], "camera.sock"))
        parent_exit["cleanCameraFinish"] = True
        report["parentExit"] = parent_exit
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        with open(args.report, "x") as output:
            json.dump(report, output, indent=2)
        print(json.dumps(report))


def digest(path):
    with open(path, "rb") as source:
        return hashlib.sha256(source.read()).hexdigest()


if __name__ == "__main__":
    main()

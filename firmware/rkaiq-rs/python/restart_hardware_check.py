"""Exercise repeated real application Camera ownership; no installed app edits."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from shieldsigner_integration import install_camera_backend


def memory():
    result = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in (
            "MemAvailable",
            "CmaFree",
            "CmaTotal",
            "CmaAllocated",
            "CmaReleased",
            "Slab",
        ):
            result[key + "KiB"] = int(value.split()[0])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--cycles", type=int, default=10)
    args = parser.parse_args()
    if not 2 <= args.cycles <= 100:
        parser.error("--cycles must be 2..100")
    config = json.loads(Path(args.config).read_text())
    os.environ["SHIELDSIGNER_CAMERA_CONFIG"] = str(Path(args.config).resolve())
    module = install_camera_backend(args.app_root)
    report = {
        "passed": False,
        "cycles": [],
        "initialMemory": memory(),
        "binarySha256": hashlib.sha256(Path(config["binary"]).read_bytes()).hexdigest(),
        "opticalScanQualified": False,
    }
    try:
        for index in range(args.cycles):
            camera = module.Camera.__new__(module.Camera)
            camera._camera_rotation = (index % 4) * 90
            start = time.monotonic()
            first = None
            seen = []
            camera.start_video_stream_mode()
            reader = camera._video_stream
            owner_pid = reader._owner.pid
            try:
                while len(seen) < 6:
                    preview = camera.read_video_stream(as_image=True)
                    if preview is not None:
                        if first is None:
                            first = time.monotonic()
                        assert preview.size in ((480, 640), (640, 480))
                        if not seen or seen[-1] != reader.sequence:
                            seen.append(reader.sequence)
                    if time.monotonic() - start > 12:
                        raise TimeoutError("Camera restart did not produce six frames")
                    time.sleep(0.01)
            finally:
                stop = time.monotonic()
                camera.stop_video_stream_mode()
            assert reader.owner_exit_code == 0 and reader.is_stopped
            assert not Path(reader.socket_path).exists()
            assert not Path("/proc/" + str(owner_pid)).exists()
            assert all(a < b for a, b in zip(seen, seen[1:]))
            after = memory()
            # This kernel releases CMA to the general allocator, so CmaFree alone
            # can stay zero with no live allocations. Prefer its allocated counter.
            if "CmaAllocatedKiB" in after:
                assert (
                    after["CmaAllocatedKiB"]
                    == report["initialMemory"]["CmaAllocatedKiB"]
                )
            else:
                assert after["CmaFreeKiB"] == report["initialMemory"]["CmaFreeKiB"]
            report["cycles"].append(
                {
                    "index": index,
                    "rotation": camera._camera_rotation,
                    "firstFrameSeconds": first - start,
                    "stopSeconds": time.monotonic() - stop,
                    "sequences": seen,
                    "ownerExitCode": reader.owner_exit_code,
                    "ownerGone": True,
                    "socketRemoved": True,
                    "memoryAfterStop": after,
                    "directory": reader.session_directory,
                }
            )
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()

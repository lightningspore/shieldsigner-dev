"""ARM/Linux startup-order check: READY must precede a rejected code lock.

Run with no active camera owner. Invalid plan/device paths and a64KiB MEMLOCK
hard limit ensure rejection before graph, sensor or V4L2 setup.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Choose a new report filename")
    ready_read, ready_write = os.pipe()
    environment = dict(os.environ, SHIELDSIGNER_CAMERA_LOCK_CODE="1",
                       SHIELDSIGNER_CAMERA_READY_FD=str(ready_write),
                       SHIELDSIGNER_CAMERA_PARENT_PID=str(os.getpid()))
    def limit():
        resource.setrlimit(resource.RLIMIT_MEMLOCK, (65536, 65536))
    started = time.monotonic()
    process = subprocess.Popen([str(args.binary.resolve()), "stream-sc3336",
                                *["/nonexistent-readiness-check"] * 7],
                               env=environment, pass_fds=(ready_write,), preexec_fn=limit,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.close(ready_write)
    try:
        stdout, stderr = process.communicate(timeout=15)
        ready = os.read(ready_read, 1)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(ready_read)
    records = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            records.append(value)
    code_lock = next((r for r in records if r.get("event") == "executable-code-lock"), {})
    passed = (ready == b"1" and process.returncode != 0 and code_lock.get("success") is False
              and code_lock.get("hardLimitBytes") == 65536
              and code_lock.get("requestedBytes", 0) > 65536
              and "hard limit" in code_lock.get("error", "")
              and not any(r.get("event") == "first-frame-starting" for r in records))
    report = dict(passed=passed, binarySha256=hashlib.sha256(args.binary.read_bytes()).hexdigest(),
                  readyAcknowledged=ready == b"1", exitCode=process.returncode,
                  codeLock=code_lock, seconds=time.monotonic() - started,
                  stderr=stderr.decode(errors="replace"),
                  scope="Invalid paths and rejected memory lock; no camera capture or UI qualification.")
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

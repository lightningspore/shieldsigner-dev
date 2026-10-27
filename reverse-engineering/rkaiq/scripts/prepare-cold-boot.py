#!/usr/bin/env python3
"""Prepare a single vendor/UI-skipped boot on the pinned test image.

Does not reboot. Both startup scripts restore their original bytes before
writing a boot-specific marker and returning. Backups remain for host checking.
Refuses other script versions and any existing backup/preparation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

PINNED = {
    "S21appinit": "61dcd3bdb6740771b296611ab83e3238f9bc45b2ca0ec5ae78b542085be592e5",
    "S99seedsigner": "b0b93fc8486d7d54e5d9ac1c5ef439fa86087f52123607a93f48d8292a518573",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adb = ["adb", "-s", args.serial]

    def shell(command):
        return subprocess.check_output(adb + ["shell", command], text=True).strip()

    if args.output.exists():
        raise FileExistsError(args.output)
    originals = {}
    for name, expected in PINNED.items():
        path = "/etc/init.d/" + name
        actual = shell("sha256sum " + path).split()[0]
        if actual != expected:
            raise ValueError("Unexpected startup script: " + path)
        backup = "/etc/init.d/." + name + ".shieldsigner-coldtest-backup"
        if shell("test ! -e " + backup + " && echo absent") != "absent":
            raise ValueError("Pending startup backup: " + backup)
        originals[name] = {"path": path, "backup": backup, "sha256": actual}
    boot_id = shell("cat /proc/sys/kernel/random/boot_id")
    # Copy persistent test assets separately before reboot; /tmp will disappear.
    prepared = []
    try:
        for name, entry in originals.items():
            path, backup = entry["path"], entry["backup"]
            marker = "/tmp/shieldsigner-coldtest-" + name + ".json"
            wrapper = f'''#!/bin/sh
# One observed boot only. Restores the original without executing it this boot.
[ "$1" = start ] || exit 0
backup={shlex.quote(backup)}
expected={entry['sha256']}
actual=$(sha256sum "$backup")
actual=${{actual%% *}}
[ "$actual" = "$expected" ] || exit 1
cp -p "$backup" {shlex.quote(path + '.restore')} || exit 1
mv {shlex.quote(path + '.restore')} {shlex.quote(path)} || exit 1
boot_id=$(cat /proc/sys/kernel/random/boot_id)
printf '{{"bootId":"%s","service":"{name}","skipped":true,"restoredSha256":"%s"}}\\n' "$boot_id" "$expected" > {shlex.quote(marker)}
exit 0
'''
            with tempfile.TemporaryDirectory() as temporary:
                source = Path(temporary) / name
                source.write_text(wrapper)
                temporary_remote = "/etc/init.d/." + name + ".shieldsigner-coldtest-new"
                shell("cp -p " + path + " " + backup)
                prepared.append(entry)
                subprocess.run(adb + ["push", str(source), temporary_remote], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                shell("chmod 755 " + temporary_remote + " && mv " + temporary_remote + " " + path)
                entry["wrapperSha256"] = hashlib.sha256(wrapper.encode()).hexdigest()
                if shell("sha256sum " + path).split()[0] != entry["wrapperSha256"]:
                    raise ValueError("Wrapper verification failed")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"previousBootId": boot_id, "services": originals,
                                         "rebootIssued": False}, indent=2) + "\n")
    except Exception:
        for entry in reversed(prepared):
            shell("cp -p " + entry["backup"] + " " + entry["path"])
            if shell("sha256sum " + entry["path"]).split()[0] == entry["sha256"]:
                shell("rm " + entry["backup"])
        raise
    print(json.dumps({"prepared": True, "previousBootId": boot_id,
                      "restorationEvidence": str(args.output), "rebootIssued": False}))


if __name__ == "__main__":
    main()

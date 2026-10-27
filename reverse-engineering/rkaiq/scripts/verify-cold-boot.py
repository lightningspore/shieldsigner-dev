#!/usr/bin/env python3
"""Verify the pinned one-boot skip/restoration before running Rust capture."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adb = ["adb", "-s", args.serial]

    def shell(command):
        return subprocess.check_output(adb + ["shell", command], text=True).strip()

    if args.output.exists():
        raise FileExistsError(args.output)
    preparation = json.loads(args.preparation.read_text())
    boot_id = shell("cat /proc/sys/kernel/random/boot_id")
    assert boot_id != preparation["previousBootId"], "Boot did not change"
    verified = {}
    for name, entry in preparation["services"].items():
        # Only names emitted by the preparation tool, not arbitrary JSON commands.
        assert name in {"S21appinit", "S99seedsigner"}
        assert entry["path"] == "/etc/init.d/" + name
        assert entry["backup"] == "/etc/init.d/." + name + ".shieldsigner-coldtest-backup"
        marker = json.loads(shell("cat /tmp/shieldsigner-coldtest-" + name + ".json"))
        assert marker["bootId"] == boot_id and marker["skipped"]
        assert marker["restoredSha256"] == entry["sha256"]
        for path in [entry["path"], entry["backup"]]:
            assert shell("sha256sum " + path).split()[0] == entry["sha256"]
        verified[name] = marker
    vendor_pids = shell("pidof rkipc rkaiq_3A_server || true")
    vendor_maps = shell("grep -l -E 'librkaiq|librockit' /proc/[0-9]*/maps || true")
    rockit_absent = shell("test ! -d /sys/module/rockit && echo absent") == "absent"
    assert not vendor_pids and not vendor_maps and rockit_absent
    report = {"kind": "controlled-clean-reboot-pre-capture-check", "passed": True,
              "previousBootId": preparation["previousBootId"], "bootId": boot_id,
              "services": verified, "vendorCameraPids": vendor_pids,
              "vendorLibraryMappings": vendor_maps, "rockitModuleAbsent": rockit_absent,
              "modulesBeforeManagedCapture": shell("cat /proc/modules"),
              "physicalPowerCycle": False, "startupScriptsRestored": True}
    # Backups are removed only after every service and all checks pass.
    for entry in preparation["services"].values():
        shell("rm " + entry["backup"])
    report["matchingTemporaryBackupsRemoved"] = True
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

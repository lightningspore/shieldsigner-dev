#!/usr/bin/env python3
"""Check native result handoff's mirror/flip loops with unique grid entries."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
from differential import OriginalArm, BINARY, HEAP


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    arm = OriginalArm(BINARY)
    name = "_ZN5RkCam18RkAiqAlscHandleInt12genIspResultEPNS_15RkAiqFullParamsES2_"
    assert arm.resolve_symbol(name, 0x7A320) == arm.symbols[name]
    checks = []
    for mirror, flip in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        arm.uc.mem_write(HEAP, bytes(0x10000))
        h, v, out, core, shared, full, prev, proxy, pproxy, data, pdata = [
            HEAP + x
            for x in (
                0,
                0x100,
                0x200,
                0x1000,
                0x2000,
                0x3000,
                0x4000,
                0x5000,
                0x6000,
                0x7000,
                0x8000,
            )
        ]

        def w(a, n):
            arm.uc.mem_write(a, struct.pack("<I", n))

        w(h, v)
        w(v - 12, 0)
        w(h + 0x14, out)
        w(h + 0x28, core)
        w(h + 0x34, shared)
        w(h + 0xA4, 1)
        w(shared + 4, 123)
        w(full + 0x70, proxy)
        w(proxy + 0x6C, data)
        w(prev + 0x70, pproxy)
        w(pproxy + 0x6C, pdata)
        arm.uc.mem_write(core + 0x3D0, bytes([mirror, flip]))
        # Every entry is unique; any nonidentity grid permutation is detectable.
        grid = struct.pack("<1156H", *range(1156)) + bytes(range(128)) + b"\x01\xa5"
        arm.uc.mem_write(pdata + 8, grid)
        assert arm.invoke(name, [h, full, prev]) == 0
        assert bytes(arm.uc.mem_read(data + 8, 2442)) == grid
        assert bytes(arm.uc.mem_read(pdata + 8, 2442)) == grid
        assert bytes(arm.uc.mem_read(data + 4, 1)) == b"\x01"
        assert bytes(arm.uc.mem_read(data + 0x994, 8)) == struct.pack("<II", 123, 1)
        checks.append(dict(mirror=bool(mirror), flip=bool(flip), gridUnchanged=True))
    report = dict(
        passed=True,
        cases=checks,
        resultBytesComparedPerCase=2442,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        scope="Full native genIspResult carry-forward publication branch and common mirror/flip loops. All unique grid entries and geometry/enable/padding preserved; frame/sync/update metadata checked.",
        limitations=[
            "Constructed valid typed C++ pointer graph; fresh-result SmartPtr assignment branch not executed.",
            "Native loops make a full set of pair swaps twice, yielding identity; no corrected orientation behavior is inferred.",
            "Native emulation only; not physical mirror/flip or shading qualification.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

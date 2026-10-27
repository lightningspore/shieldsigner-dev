#!/usr/bin/env python3
"""Compare LSC selected-result packing with the original full ISP32 dispatcher."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid

from differential import ROOT, BINARY, HEAP

OriginalColor = importlib.import_module("isp-color").OriginalColor


class OriginalLsc(OriginalColor):
    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "__dynamic_cast":
            from differential import regs

            uc.reg_write(regs.UC_ARM_REG_R0, HEAP + 0x40000)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run_lsc(self, value):
        context, params, source, smart, proxy, vtable = [
            HEAP + x for x in (0, 0x10000, 0x20000, 0x30000, 0x40000, 0x5000C)
        ]
        self.uc.mem_write(context, bytes([0x77]) * 0x3000)
        self.uc.mem_write(context + 0x68, bytes([value["enabled"]]))
        self.uc.mem_write(context, struct.pack("<I", vtable))
        self.uc.mem_write(vtable - 12, bytes(4))
        self.uc.mem_write(params, bytes.fromhex(value["parameters"]))
        self.uc.mem_write(source, bytes(8) + bytes.fromhex(value["result"]))
        self.uc.mem_write(smart, struct.pack("<II", proxy, 1))
        self.uc.mem_write(proxy, bytes(0x100))
        self.uc.mem_write(proxy + 100, struct.pack("<I", 10))
        self.uc.mem_write(proxy + 0x6C, struct.pack("<I", source))
        before = bytes(self.uc.mem_read(context, 0x3000))
        assert (
            self.invoke(
                "_ZN5RkCam11Isp32Params24convert3aResultsToIspCfgERN4XCam8SmartPtrINS_14SharedItemBaseEEEPvb",
                [context, smart, params, 0],
            )
            == 1
        )
        after = bytearray(self.uc.mem_read(context, 0x3000))
        enabled = bool(after[0x68])
        after[0x68] = before[0x68]
        assert bytes(after) == before
        assert bytes(self.uc.mem_read(source + 8, 2442)).hex() == value["result"]
        return dict(
            parameters=bytes(self.uc.mem_read(params, 11145)).hex(), enabled=enabled
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=1000)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert 4 <= args.cases <= 4096
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x4C5343)
    cases = []
    for index in range(args.cases):
        result = bytearray(rng.randbytes(2442))
        result[0x988] = [0, 1, 255][index % 3]
        parameters = bytearray(rng.randbytes(11145))
        if index < 4:
            parameters[:24] = struct.pack("<QQQ", index & 1, (index >> 1) & 1, 0)
        for channel in range(4):
            for entry, number in enumerate([0, 8190, 8191, 8192, 65535]):
                struct.pack_into("<H", result, channel * 578 + entry * 2, number)
            struct.pack_into(
                "<H",
                parameters,
                0x895 + channel * 580 + 578,
                [0, 8191, 8192, 65535][index % 4],
            )
        cases.append(
            {
                "result": result.hex(),
                "parameters": parameters.hex(),
                "enabled": bool(index % 2),
            }
        )
    arm = OriginalLsc()
    expected = [arm.run_lsc(value) for value in cases]
    lines = "".join(
        "isp-lsc " + json.dumps(value, separators=(",", ":")) + "\n" for value in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = [
        json.loads(line)
        for line in subprocess.check_output(
            [str(binary)], input=lines, text=True
        ).splitlines()
    ]
    assert actual == expected, "Host/native LSC mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/lsc-" + uuid.uuid4().hex + ".txt"
        )
        board = "/shieldsigner-camera-tests/dev-0.0.34/bin/numeric-fixture"
        board_sha = subprocess.check_output(
            adb + ["shell", "sha256sum " + board], text=True
        ).split()[0]
        assert (
            board_sha
            == hashlib.sha256(
                (
                    ROOT
                    / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture"
                ).read_bytes()
            ).hexdigest()
        )
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary) / "input"
            p.write_text(lines)
            subprocess.run(
                adb + ["push", str(p), remote], check=True, capture_output=True
            )
            try:
                output = subprocess.check_output(
                    adb + ["shell", board + " < " + remote], text=True
                ).splitlines()
                assert [json.loads(line) for line in output] == actual, (
                    "Physical ARM/native LSC mismatch"
                )
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "bytesComparedPerCase": 11145,
        "mismatches": 0,
        "seed": "0x4c5343",
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Original full ISP32 dispatcher LSC branch (result type 10); all 11,145 output bytes, 2,449 packed LSC bytes, input preservation and native cached enable byte.",
        "limitations": [
            "Typed C++ dynamic_cast is a controlled oracle boundary; actual LSC branch instructions execute.",
            "Calibration selection, geometry and AlscConfig are separate from this serializer.",
            "Physical ARM replay does not enable LSC on the camera or qualify image quality.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

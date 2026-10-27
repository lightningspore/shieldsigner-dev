#!/usr/bin/env python3
"""Compare DPCC selected-result packing with the original full ISP32 dispatcher."""

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


class OriginalDpcc(OriginalColor):
    def run_dpcc(self, value):
        context, params, source, smart, proxy, vtable = [
            HEAP + x for x in (0, 0x10000, 0x20000, 0x30000, 0x40000, 0x5000C)
        ]
        self.uc.mem_write(context, bytes(0x3000))
        self.uc.mem_write(context, struct.pack("<I", vtable))
        self.uc.mem_write(vtable - 12, bytes(4))
        self.uc.mem_write(params, bytes.fromhex(value["parameters"]))
        self.uc.mem_write(source, bytes(8) + bytes.fromhex(value["result"]))
        self.uc.mem_write(smart, struct.pack("<II", proxy, 0))
        self.uc.mem_write(proxy, bytes(0x100))
        self.uc.mem_write(proxy + 100, struct.pack("<I", 6))
        self.uc.mem_write(proxy + 0x6C, struct.pack("<I", source))
        assert (
            self.invoke(
                "_ZN5RkCam11Isp32Params24convert3aResultsToIspCfgERN4XCam8SmartPtrINS_14SharedItemBaseEEEPvb",
                [context, smart, params, 0],
            )
            == 1
        )
        return bytes(self.uc.mem_read(params, 11145)).hex()


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
    rng = random.Random(0x44504343)
    cases = []
    for index in range(args.cases):
        result = bytearray(rng.randbytes(192))
        result[2] = [0, 1, 255][index % 3]
        parameters = bytearray(rng.randbytes(11145))
        if index < 4:
            parameters[:24] = struct.pack("<QQQ", index & 1, (index >> 1) & 1, 0)
        cases.append({"result": result.hex(), "parameters": parameters.hex()})
    arm = OriginalDpcc()
    expected = [arm.run_dpcc(value) for value in cases]
    lines = "".join(
        "isp-dpcc " + json.dumps(value, separators=(",", ":")) + "\n" for value in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected, "Host/native DPCC mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/dpcc-" + uuid.uuid4().hex + ".txt"
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
                assert output == actual, "Physical ARM/native DPCC mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "bytesComparedPerCase": 11145,
        "mismatches": 0,
        "seed": "0x44504343",
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Original full ISP32 result dispatcher DPCC branch, complete output parameter buffer, all mask bits and all 186 packed DPCC bytes.",
        "limitations": [
            "Typed C++ proxy cast is a controlled oracle boundary.",
            "Calibration selection and AdpccProcess are not implemented by this serializer.",
            "Physical ARM replay does not enable DPCC on the camera or qualify image quality.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Full native ISP32 dispatcher CNR branch versus Rust packed results."""

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

OriginalLsc = importlib.import_module("isp-lsc").OriginalLsc


class OriginalCnr(OriginalLsc):
    def run_cnr(self, value):
        context, params, source, smart, proxy, vtable = [
            HEAP + x for x in (0, 0x10000, 0x20000, 0x30000, 0x40000, 0x5000C)
        ]
        self.uc.mem_write(context, bytes([0x77]) * 0x3000)
        self.uc.mem_write(context, struct.pack("<I", vtable))
        self.uc.mem_write(vtable - 12, bytes(4))
        self.uc.mem_write(params, bytes.fromhex(value["parameters"]))
        original = bytes(8) + bytes.fromhex(value["result"])
        self.uc.mem_write(source, original)
        self.uc.mem_write(smart, struct.pack("<II", proxy, 1))
        self.uc.mem_write(proxy, bytes(0x100))
        self.uc.mem_write(proxy + 100, struct.pack("<I", 34))
        self.uc.mem_write(proxy + 0x6C, struct.pack("<I", source))
        before = bytes(self.uc.mem_read(context, 0x3000))
        assert (
            self.invoke(
                "_ZN5RkCam11Isp32Params24convert3aResultsToIspCfgERN4XCam8SmartPtrINS_14SharedItemBaseEEEPvb",
                [context, smart, params, 0],
            )
            == 1
        )
        assert bytes(self.uc.mem_read(context, 0x3000)) == before
        assert bytes(self.uc.mem_read(source, len(original))) == original
        return bytes(self.uc.mem_read(params, 11145)).hex()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adb")
    args = parser.parse_args()
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    rng = random.Random(0x434E52)
    cases = []
    for i in range(1000):
        result = bytearray(rng.randbytes(66))
        result[0] = [0, 1, 2, 255][i % 4]
        parameters = bytearray(rng.randbytes(11145))
        if i < 16:
            parameters[:24] = struct.pack(
                "<QQQ", i & 1, (i >> 1 & 1) << 39, (i >> 2 & 1) << 39
            )
            # Distinct bytes expose reorderings; poison SDK padding separately.
            for offset in range(1, 65):
                result[offset] = offset
            result[7] = result[23] = result[37] = result[41] = result[45] = result[
                65
            ] = 0xA5
        cases.append(dict(parameters=parameters.hex(), result=result.hex()))
    arm = OriginalCnr()
    expected = [arm.run_cnr(v) for v in cases]
    lines = "".join(
        "isp-cnr " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected, "Host/native CNR mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
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
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/cnr-" + uuid.uuid4().hex + ".txt"
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
                assert output == actual, "Physical ARM/native CNR mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = dict(
        passed=True,
        cases=len(cases),
        parameterBytesComparedPerCase=11145,
        packedCnrBytes=59,
        sdkResultBytes=66,
        mismatches=0,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        hostBinarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        physicalArmBinarySha256=board_sha,
        hostMatchesPhysicalArm=board_sha is not None,
        scope="Full original ISP32 dispatcher result type 34 and complete convertAiqUvnrToIsp32Params. All output parameter bytes compared; original result and all converter context bytes checked unchanged. SDK disable retains module enable but clears global alpha.",
        boundaries=[
            "Controlled valid typed C++ dynamic_cast; original dispatcher/converter instructions execute with no algorithm substitutes.",
            "Random prior masks/bytes, zero/nonzero SDK enable, bypass alpha, SDK padding and packed register reordering covered.",
            "Register serialization only; calibration, tuning, quantization, runtime and live CNR remain separate.",
            "Physical CPU replay makes no ISP writes and loads no vendor library on the board.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

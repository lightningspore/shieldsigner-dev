#!/usr/bin/env python3
"""Compare CCM register conversion with the original ARM conversion routine."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import uuid

from differential import ROOT, BINARY, HEAP, OriginalArm


class OriginalCcm(OriginalArm):
    def run_ccm(self, value):
        context, params, source = [HEAP + x for x in (0, 0x10000, 0x20000)]
        self.uc.mem_write(context, bytes(0x3000))
        self.uc.mem_write(params, bytes.fromhex(value["parameters"]))
        self.uc.mem_write(source, bytes.fromhex(value["result"]))
        self.invoke(
            "_ZN5RkCam11Isp32Params26convertAiqCcmToIsp32ParamsER20isp32_isp_params_cfgRK19rk_aiq_ccm_cfg_v2_s",
            [context, params, source],
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
    rng = random.Random(0x43434D)
    cases = []
    for index in range(args.cases):
        result = bytearray(rng.randbytes(156))
        result[0] = [0, 1, 255][index % 3]
        result[4] = [0, 1, 255][index % 3]
        for offset in list(range(8, 148, 4)) + [152]:
            value = (
                rng.choice([0.0, -0.0, 0.5, -0.5, 1.0, -1.0, 65536.25, -65536.25])
                if index < 100
                else rng.uniform(-1000.0, 1000.0)
            )
            struct.pack_into("<f", result, offset, value)
        if index < 4:
            for row in range(3):
                for col in range(3):
                    struct.pack_into(
                        "<f", result, 8 + (row * 3 + col) * 4, float(row == col)
                    )
        parameters = bytearray(rng.randbytes(11145))
        if index < 4:
            parameters[:24] = struct.pack("<QQQ", index & 1, (index >> 1) & 1, 0)
        cases.append({"result": result.hex(), "parameters": parameters.hex()})
    arm = OriginalCcm(BINARY)
    expected = [arm.run_ccm(value) for value in cases]
    lines = "".join(
        "isp-ccm " + json.dumps(value, separators=(",", ":")) + "\n" for value in cases
    )
    binary = ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture"
    actual = subprocess.check_output([str(binary)], input=lines, text=True).splitlines()
    assert actual == expected, "Host/native CCM mismatch"
    board_sha = None
    if args.adb:
        adb = ["adb", "-s", args.adb]
        remote = (
            "/shieldsigner-camera-tests/dev-0.0.34/ccm-" + uuid.uuid4().hex + ".txt"
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
                assert output == actual, "Physical ARM/native CCM mismatch"
            finally:
                subprocess.run(
                    adb + ["shell", "rm " + remote], check=True, capture_output=True
                )
    report = {
        "passed": True,
        "cases": len(cases),
        "bytesComparedPerCase": 11145,
        "mismatches": 0,
        "seed": "0x43434D",
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "hostBinarySha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "physicalArmBinarySha256": board_sha,
        "hostMatchesPhysicalArm": board_sha is not None,
        "scope": "Original full CCM converter, complete 11,145-byte parameter buffer, all mask bits and all 79 packed CCM bytes. Finite inputs bounded to magnitude 1,000,000.",
        "limitations": [
            "Calibrated matrix selection and the live CCM controller are separate from this serializer.",
            "Physical ARM replay does not enable CCM on the camera or qualify image quality.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
